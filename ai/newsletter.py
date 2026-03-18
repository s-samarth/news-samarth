"""
AI Agent-Based Newsletter Generation System

This module implements a sophisticated newsletter generation system using LangGraph
with multiple AI agents, RAG (Retrieval-Augmented Generation), and intelligent
ranking/deduplication capabilities.

===============================================================================
ARCHITECTURE OVERVIEW
===============================================================================

The system uses a 4-agent LangGraph workflow:

1. Fetcher Agent: Retrieves and prepares articles from ChromaDB
2. Ranker Agent: Ranks articles by importance using AI
3. Deduplicator Agent: Checks for duplicates and identifies updates using RAG
4. Generator Agent: Creates the final newsletter with proper formatting

Each agent has a specific system prompt that guides its behavior, ensuring
consistent and high-quality output.

===============================================================================
KEY FEATURES
===============================================================================

- AI-powered ranking based on impact, uniqueness, and source credibility
- RAG-based deduplication using vector similarity search
- Update tracking for evolving stories
- Full source attribution for every news item
- Newsletter history stored in ChromaDB
- Configurable via environment variables
- Extensive logging and error handling

===============================================================================
USAGE EXAMPLE
===============================================================================

    >>> from ai.newsletter import generate_newsletter
    >>> newsletter = generate_newsletter()
    >>> print(newsletter["newsletter"])
    # 📰 Daily AI Newsletter - January 15, 2024
    ...

===============================================================================
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, TypedDict, Optional, Tuple

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langgraph.graph import StateGraph, END

from config import config
from db.chroma_db import (
    get_chroma_client,
    get_or_create_collection,
    get_articles_last_24h,
    get_articles_by_fetch_date,
    get_articles_by_date
)


# =============================================================================
# STATE DEFINITIONS
# =============================================================================

class NewsletterState(TypedDict):
    """
    State dictionary for the LangGraph newsletter workflow.
    
    This TypedDict defines all the state variables that flow through
    the workflow nodes. Each agent reads from and writes to this state.
    
    Attributes:
        date: Newsletter date in YYYY-MM-DD format
        articles: Raw articles fetched from ChromaDB
        ranked_articles: Articles after ranking (with scores)
        new_stories: Articles identified as genuinely new
        updates: Articles identified as updates to previous stories
        duplicates: Articles identified as duplicates (excluded)
        newsletter: Final generated newsletter markdown text
        metadata: Newsletter metadata (counts, sources, etc.)
        sources_tracking: Detailed source information for each article
        previous_newsletters: Retrieved previous newsletters for RAG
    """
    date: str
    articles: List[Dict[str, Any]]
    ranked_articles: List[Dict[str, Any]]
    new_stories: List[Dict[str, Any]]
    updates: List[Dict[str, Any]]
    duplicates: List[Dict[str, Any]]
    newsletter: str
    metadata: Dict[str, Any]
    sources_tracking: Dict[str, List[Dict[str, Any]]]
    previous_newsletters: List[Dict[str, Any]]


# =============================================================================
# SYSTEM PROMPTS FOR AGENTS
# =============================================================================

# Fetcher Agent System Prompt
# This agent is responsible for retrieving and preparing articles
FETCHER_SYSTEM_PROMPT = """You are a content fetcher AI agent.

Your role is to:
1. Retrieve articles from the last 24 hours
2. Filter out low-quality or incomplete articles
3. Prepare articles for ranking by extracting key information
4. Organize articles by platform for easier processing

Focus on articles with:
- Complete content (not just titles)
- Valid timestamps
- Credible sources

Return a well-organized list of articles ready for ranking.
"""

# Ranker Agent System Prompt
# This agent ranks articles by importance using multiple criteria
RANKER_SYSTEM_PROMPT = """You are an expert news editor AI agent.

Your job is to rank news articles by importance and relevance.

===============================================================================
RANKING CRITERIA (in order of priority)
===============================================================================

1. **IMPACT (40%)**: How significant is this news?
   - Does it affect many people or industries?
   - Is it a major announcement or breakthrough?
   - Does it have long-term implications?

2. **UNIQUENESS (25%)**: Is this a unique story?
   - Is it being covered by multiple sources? (more coverage = more important)
   - Is it a original analysis or just re reporting?
   - Does it provide new information not available elsewhere?

3. **SOURCE CREDIBILITY (20%)**: How credible is the source?
   - Is the source known for accurate reporting?
   - Does the source have expertise in this area?
   - Is this a primary source or secondary reporting?

4. **CONTENT DEPTH (15%)**: How substantial is the content?
   - Does the article provide detailed information?
   - Are there facts, data, or evidence provided?
   - Is it actionable or merely informational?

===============================================================================
OUTPUT FORMAT
===============================================================================

For each article, provide:
- rank: Position in the list (1-20)
- score: Overall score (0-100)
- rationale: Brief explanation of ranking

Return the top 20 articles sorted by rank.
"""

# Deduplicator Agent System Prompt
# This agent identifies duplicates and updates using RAG
DEDUPLICATOR_SYSTEM_PROMPT = """You are a fact-checker and deduplication AI agent.

Your job is to identify duplicate articles and track story updates using
the provided context from previous newsletters.

===============================================================================
DEDUPLICATION RULES
===============================================================================

1. **EXACT DUPLICATES**: Same URL or identical content
   - Action: EXCLUDE from new stories
   - Reason: Already covered

2. **SEMANTIC DUPLICATES**: Same story, different source
   - Action: EXCLUDE from new stories (keep best source)
   - Reason: Redundant coverage

3. **UPDATES**: Same topic but new information
   - Action: INCLUDE in updates section
   - Reason: New developments matter

4. **NEW STORIES**: Genuinely new information
   - Action: INCLUDE in new stories
   - Reason: Fresh content

===============================================================================
UPDATE DETECTION
===============================================================================

An article is an "update" if:
- It covers the same event/topic as a previous article
- It provides new information, data, or developments
- The core subject matter is the same but details have evolved

Example:
- Previous: "Company X announces new AI model"
- Update: "Company X releases new AI model, now available publicly"

===============================================================================
OUTPUT FORMAT
===============================================================================

Return a JSON object with:
{
    "new_stories": [list of new articles],
    "updates": [
        {
            "article": {...},
            "previous_version": {...},
            "what_changed": "description of new information"
        }
    ],
    "duplicates": [list of duplicate articles]
}
"""

# Generator Agent System Prompt
# This agent creates the final newsletter
GENERATOR_SYSTEM_PROMPT = """You are a professional newsletter writer AI agent.

Your job is to create an engaging, well-structured newsletter from the
ranked and deduplicated articles.

===============================================================================
NEWSLETTER STRUCTURE
===============================================================================

1. **HEADER**
   - Title: "📰 Daily AI Newsletter - [DATE]"
   - Subtitle: Brief tagline

2. **EXECUTIVE SUMMARY** (2-3 sentences)
   - Capture the essence of today's news
   - Highlight the most important development

3. **🔥 TOP STORIES** (Numbered 1-20)
   For each story:
   - Rank number and title
   - Source badge (platform + source_name)
   - Relative timestamp (e.g., "3 hours ago")
   - Content summary (2-3 paragraphs)
   - Source link (URL)
   - Relevance score (for transparency)

4. **📱 PLATFORM HIGHLIGHTS**
   Group stories by platform:
   - YouTube (with channel names)
   - Reddit (with subreddit names)
   - Substack (with publication names)
   - Twitter (with handles)

5. **🔄 UPDATES ON PREVIOUS STORIES**
   For each update:
   - Story title
   - Previous version summary
   - What's new today
   - Why it matters

6. **📊 STATISTICS**
   - Total articles analyzed
   - Articles selected
   - Updates on previous stories
   - Source breakdown by platform

7. **🔗 SOURCE ATTRIBUTION**
   - Note that all stories include direct links
   - Encourage readers to verify information

===============================================================================
FORMATTING GUIDELINES
===============================================================================

- Use Markdown for formatting
- Use emojis sparingly for visual appeal (headers only)
- Include platform colors in badges:
  * Substack: Orange (#FF6719)
  * Reddit: Orange-Red (#FF4500)
  * YouTube: Red (#FF0000)
  * Twitter: Sky Blue (#1DA1F2)
- Make it scannable with clear sections
- Keep paragraphs concise (2-3 sentences max)
- Include source links for every story

===============================================================================
TONE AND STYLE
===============================================================================

- Professional but engaging
- Authoritative yet accessible
- Factual and objective
- Concise and informative
- Avoid sensationalism

Create a newsletter that readers will look forward to receiving daily.
"""


# =============================================================================
# NEWSLETTER GENERATOR CLASS
# =============================================================================

class NewsletterGenerator:
    """
    AI agent-based newsletter generator using LangGraph.
    
    This class implements a sophisticated 4-agent workflow for generating
    professional newsletters from collected news articles. Each agent has
    a specific role and system prompt to ensure high-quality output.
    
    The workflow:
    1. Fetcher Agent: Retrieves and prepares articles
    2. Ranker Agent: Ranks articles by importance
    3. Deduplicator Agent: Identifies duplicates and updates using RAG
    4. Generator Agent: Creates the final newsletter
    
    Attributes:
        api_key: OpenRouter API key for LLM access
        model_name: LLM model name (configurable via env)
        client: ChromaDB client instance
        collection: Main newsfeed collection
        newsletter_collection: Newsletter history collection
        vectorstore: Vector store for RAG operations
        llm: ChatOpenAI instance configured for OpenRouter
        workflow: Compiled LangGraph workflow
    
    Example:
        >>> generator = NewsletterGenerator()
        >>> result = generator.generate_newsletter()
        >>> print(result["newsletter"])
    """
    
    def __init__(self):
        """
        Initialize the NewsletterGenerator with OpenRouter LLM and ChromaDB.
        
        Sets up:
        - OpenRouter LLM connection (configurable model)
        - ChromaDB connections for articles and newsletters
        - Vector store for RAG operations
        - LangGraph workflow with 4 agents
        
        Raises:
            Warning: If OPENROUTER_API_KEY is not set
        """
        # =====================================================================
        # LLM CONFIGURATION
        # =====================================================================
        # Get API key and model name from config (environment variables)
        self.api_key = config.openrouter_api_key
        # Allow different models for summarization vs newsletter generation
        self.model_name = os.getenv("NEWSLETTER_MODEL", config.openrouter_model)
        
        if not self.api_key:
            print("Warning: OPENROUTER_API_KEY not set. Newsletter generation will fail.")
            self.llm = None
        else:
            # Configure LLM with OpenRouter (OpenAI-compatible API)
            # Temperature 0.4 balances creativity with factual accuracy
            self.llm = ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=0.4  # Moderate temperature for balanced output
            )
        
        # =====================================================================
        # CHROMADB CONNECTIONS
        # =====================================================================
        # Initialize ChromaDB client for local storage
        self.client = get_chroma_client()
        
        # Main collection containing all news articles
        self.collection = get_or_create_collection(self.client)
        
        # Separate collection for newsletter history (used for RAG)
        # This allows us to compare new articles against previous newsletters
        self.newsletter_collection = get_or_create_collection(
            self.client,
            name="newsletters"
        )
        
        # =====================================================================
        # RAG VECTOR STORE SETUP
        # =====================================================================
        # Vector store for semantic similarity search
        # Used by deduplicator agent to find similar articles
        if self.api_key:
            self.vectorstore = Chroma(
                client=self.client,
                collection_name="newsfeed",
                embedding_function=OpenAIEmbeddings(
                    openai_api_key=self.api_key
                )
            )
        else:
            self.vectorstore = None
        
        # =====================================================================
        # BUILD LANGGRAPH WORKFLOW
        # =====================================================================
        # Construct the 4-agent workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow with 4 agents.
        
        Creates a stateful graph where each node represents an agent:
        1. fetch_articles - Retrieve articles from last 24h
        2. rank_articles - AI-powered ranking by importance
        3. deduplicate - RAG-based deduplication and update detection
        4. generate_newsletter - Create final newsletter
        
        The workflow is linear: each agent processes the state and passes
        it to the next agent in the chain.
        
        Returns:
            Compiled StateGraph ready for execution
        """
        # Create state graph with NewsletterState as the state type
        workflow = StateGraph(NewsletterState)
        
        # =====================================================================
        # ADD AGENT NODES
        # =====================================================================
        # Each node is a method that processes the state
        workflow.add_node("fetch_articles", self._fetch_articles)
        workflow.add_node("rank_articles", self._rank_articles)
        workflow.add_node("deduplicate", self._deduplicate)
        workflow.add_node("generate_newsletter", self._generate_newsletter)
        
        # =====================================================================
        # DEFINE WORKFLOW EDGES
        # =====================================================================
        # Linear workflow: fetch → rank → deduplicate → generate
        workflow.set_entry_point("fetch_articles")
        workflow.add_edge("fetch_articles", "rank_articles")
        workflow.add_edge("rank_articles", "deduplicate")
        workflow.add_edge("deduplicate", "generate_newsletter")
        workflow.add_edge("generate_newsletter", END)
        
        # Compile the workflow for execution
        return workflow.compile()
    
    # =========================================================================
    # AGENT 1: FETCHER
    # =========================================================================
    
    def _fetch_articles(self, state: NewsletterState) -> NewsletterState:
        """
        Agent 1: Fetch and prepare articles from the last 24 hours.
        
        This agent retrieves all articles collected in the last 24 hours
        from ChromaDB and prepares them for ranking. It also fetches
        previous newsletters for RAG-based deduplication.
        
        Processing steps:
        1. Query ChromaDB for articles from last 24h
        2. Filter out articles with minimal content
        3. Fetch previous newsletters for RAG context
        4. Update state with prepared articles
        
        Args:
            state: Current workflow state with date
            
        Returns:
            Updated state with articles and previous newsletters
        """
        print(f"\n{'='*60}")
        print(f"AGENT 1: Fetcher - Retrieving articles for {state['date']}")
        print(f"{'='*60}")
        
        # =====================================================================
        # FETCH ARTICLES FOR TARGET DATE
        # =====================================================================
        # Try fetch_date first (set by orchestrator), fall back to timestamp-based,
        # then fall back to last 24h for backward compatibility
        target_date = state["date"]
        result = get_articles_by_fetch_date(self.collection, target_date)
        if result["total"] == 0:
            result = get_articles_by_date(self.collection, target_date)
        if result["total"] == 0:
            result = get_articles_last_24h(self.collection)
        articles = result.get("items", [])
        
        # =====================================================================
        # FILTER LOW-QUALITY ARTICLES
        # =====================================================================
        # Remove articles with insufficient content
        # Minimum 50 characters ensures we have actual content, not just titles
        filtered_articles = [
            article for article in articles
            if len(article.get("content_text", "")) >= 50
        ]
        
        print(f"  Fetched {len(articles)} articles")
        print(f"  After filtering: {len(filtered_articles)} articles")
        
        # =====================================================================
        # FETCH PREVIOUS NEWSLETTERS FOR RAG
        # =====================================================================
        # Retrieve last 7 days of newsletters for comparison
        # This helps identify duplicates and track story updates
        previous_newsletters = self._fetch_previous_newsletters(days=7)
        print(f"  Retrieved {len(previous_newsletters)} previous newsletters for RAG")
        
        # =====================================================================
        # UPDATE STATE
        # =====================================================================
        state["articles"] = filtered_articles
        state["previous_newsletters"] = previous_newsletters
        state["ranked_articles"] = []
        state["new_stories"] = []
        state["updates"] = []
        state["duplicates"] = []
        state["sources_tracking"] = {}
        
        return state
    
    def _fetch_previous_newsletters(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch previous newsletters for RAG context.
        
        Retrieves newsletters from the last N days to use as context
        for deduplication and update detection.
        
        Args:
            days: Number of days to look back (default: 7)
            
        Returns:
            List of previous newsletter documents with metadata
        """
        try:
            # Calculate date range
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            # Query newsletter collection
            results = self.newsletter_collection.get(
                where={"type": "newsletter"},
                include=["documents", "metadatas"]
            )
            
            newsletters = []
            for i, doc_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i] if results["metadatas"] else {}
                newsletter_date = metadata.get("date", "")
                
                # Filter by date range
                if start_date <= newsletter_date <= end_date:
                    newsletters.append({
                        "id": doc_id,
                        "document": results["documents"][i] if results["documents"] else "",
                        "metadata": metadata
                    })
            
            return newsletters
            
        except Exception as e:
            print(f"  Warning: Could not fetch previous newsletters: {e}")
            return []
    
    # =========================================================================
    # AGENT 2: RANKER
    # =========================================================================
    
    def _rank_articles(self, state: NewsletterState) -> NewsletterState:
        """
        Agent 2: Rank articles by importance using AI.
        
        This agent uses the LLM with the RANKER_SYSTEM_PROMPT to evaluate
        and rank articles based on multiple criteria:
        - Impact (40%): Significance and reach
        - Uniqueness (25%): Original vs. re-reported
        - Source Credibility (20%): Trustworthiness
        - Content Depth (15%): Substantial vs. superficial
        
        Processing steps:
        1. Prepare articles for LLM (limit to 50 for context window)
        2. Send to LLM with ranking system prompt
        3. Parse response and extract ranked articles
        4. Update state with ranked articles
        
        Args:
            state: Current workflow state with fetched articles
            
        Returns:
            Updated state with ranked articles (top 20)
        """
        print(f"\n{'='*60}")
        print(f"AGENT 2: Ranker - Ranking {len(state['articles'])} articles")
        print(f"{'='*60}")
        
        # =====================================================================
        # CHECK LLM AVAILABILITY
        # =====================================================================
        if not self.llm:
            print("  Warning: LLM not configured. Using simple ranking by timestamp.")
            # Fallback: sort by timestamp (newest first) and take top 20
            sorted_articles = sorted(
                state["articles"],
                key=lambda x: x.get("timestamp", ""),
                reverse=True
            )[:20]
            
            # Add simple ranking scores
            for i, article in enumerate(sorted_articles, 1):
                article["rank"] = i
                article["score"] = 100 - (i * 2)  # Simple descending score
                article["rationale"] = "Ranked by recency (LLM not configured)"
            
            state["ranked_articles"] = sorted_articles
            return state
        
        # =====================================================================
        # PREPARE ARTICLES FOR LLM
        # =====================================================================
        # Limit to 50 articles to fit within context window
        # Focus on articles with substantial content
        articles_for_ranking = state["articles"][:50]
        articles_text = self._prepare_articles_for_llm(articles_for_ranking)
        
        # =====================================================================
        # CONSTRUCT RANKING PROMPT
        # =====================================================================
        prompt = f"""{RANKER_SYSTEM_PROMPT}

===============================================================================
ARTICLES TO RANK
===============================================================================

Today's Date: {state['date']}

{articles_text}

===============================================================================
INSTRUCTIONS
===============================================================================

Rank these articles and return the top 20 in the following JSON format:

```json
{{
    "ranked_articles": [
        {{
            "rank": 1,
            "score": 95,
            "platform": "youtube",
            "source_name": "Fireship",
            "title": "Article Title",
            "url": "https://...",
            "content_text": "First 200 chars...",
            "timestamp": "2024-01-15T10:00:00",
            "rationale": "Brief explanation of ranking"
        }}
    ]
}}
```

Return ONLY the JSON object, no additional text.
"""
        
        # =====================================================================
        # CALL LLM FOR RANKING
        # =====================================================================
        try:
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # Parse JSON response
            # Handle potential markdown code blocks
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            ranking_data = json.loads(response_text)
            ranked_articles = ranking_data.get("ranked_articles", [])
            
            print(f"  Successfully ranked {len(ranked_articles)} articles")
            
            # =================================================================
            # UPDATE STATE WITH RANKED ARTICLES
            # =================================================================
            state["ranked_articles"] = ranked_articles[:20]  # Ensure top 20 only
            
        except json.JSONDecodeError as e:
            print(f"  Error parsing ranking response: {e}")
            # Fallback: use original order
            state["ranked_articles"] = articles_for_ranking[:20]
            
        except Exception as e:
            print(f"  Error during ranking: {e}")
            # Fallback: use original order
            state["ranked_articles"] = articles_for_ranking[:20]
        
        return state
    
    # =========================================================================
    # AGENT 3: DEDUPLICATOR
    # =========================================================================
    
    def _deduplicate(self, state: NewsletterState) -> NewsletterState:
        """
        Agent 3: Identify duplicates and track updates using RAG.
        
        This agent uses RAG (Retrieval-Augmented Generation) to compare
        new articles against previous newsletters and identify:
        - Exact duplicates (same URL)
        - Semantic duplicates (same story, different source)
        - Updates (same topic, new information)
        - Genuinely new stories
        
        Processing steps:
        1. For each ranked article, search vector store for similar content
        2. Use LLM to analyze similarity and determine category
        3. Build update tracking for evolving stories
        4. Update state with categorized articles
        
        Args:
            state: Current workflow state with ranked articles
            
        Returns:
            Updated state with new_stories, updates, and duplicates
        """
        print(f"\n{'='*60}")
        print(f"AGENT 3: Deduplicator - Analyzing {len(state['ranked_articles'])} articles")
        print(f"{'='*60}")
        
        # =====================================================================
        # INITIALIZE CATEGORIZATION LISTS
        # =====================================================================
        new_stories = []
        updates = []
        duplicates = []
        
        # =====================================================================
        # PROCESS EACH ARTICLE
        # =====================================================================
        for article in state["ranked_articles"]:
            # -------------------------------------------------------------
            # Step 1: Check for exact URL duplicates
            # -------------------------------------------------------------
            is_duplicate = self._check_url_duplicate(article, state["previous_newsletters"])
            
            if is_duplicate:
                duplicates.append(article)
                print(f"  [DUPLICATE] {article.get('title', 'Untitled')[:50]}...")
                continue
            
            # -------------------------------------------------------------
            # Step 2: Semantic similarity search using RAG
            # -------------------------------------------------------------
            similar_articles = self._find_similar_articles(article, n_results=3)
            
            # -------------------------------------------------------------
            # Step 3: Use LLM to determine if update or new
            # -------------------------------------------------------------
            if similar_articles and self.llm:
                category, update_info = self._categorize_with_llm(
                    article, 
                    similar_articles,
                    state["previous_newsletters"]
                )
                
                if category == "update":
                    updates.append({
                        "article": article,
                        "update_info": update_info
                    })
                    print(f"  [UPDATE] {article.get('title', 'Untitled')[:50]}...")
                else:
                    new_stories.append(article)
                    print(f"  [NEW] {article.get('title', 'Untitled')[:50]}...")
            else:
                # No similar articles found or LLM not available
                new_stories.append(article)
                print(f"  [NEW] {article.get('title', 'Untitled')[:50]}...")
        
        # =====================================================================
        # UPDATE STATE WITH CATEGORIZED ARTICLES
        # =====================================================================
        state["new_stories"] = new_stories
        state["updates"] = updates
        state["duplicates"] = duplicates
        
        print(f"\n  Summary:")
        print(f"    New stories: {len(new_stories)}")
        print(f"    Updates: {len(updates)}")
        print(f"    Duplicates: {len(duplicates)}")
        
        return state
    
    def _check_url_duplicate(
        self, 
        article: Dict[str, Any], 
        previous_newsletters: List[Dict[str, Any]]
    ) -> bool:
        """
        Check if article URL appears in previous newsletters.
        
        Uses URL matching to identify exact duplicates.
        
        Args:
            article: Article to check
            previous_newsletters: List of previous newsletter documents
            
        Returns:
            True if URL found in previous newsletters
        """
        article_url = article.get("url", "")
        if not article_url:
            return False
        
        # Check each previous newsletter for the URL
        for newsletter in previous_newsletters:
            content = newsletter.get("document", "")
            if article_url in content:
                return True
        
        return False
    
    def _find_similar_articles(
        self, 
        article: Dict[str, Any], 
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find semantically similar articles using vector search.
        
        Uses ChromaDB's vector search to find articles with similar
        content, which may indicate the same story from different sources.
        
        Args:
            article: Article to find similarities for
            n_results: Number of similar articles to return
            
        Returns:
            List of similar articles with similarity scores
        """
        if not self.vectorstore:
            return []
        
        try:
            # Use article title + content snippet for search
            query_text = f"{article.get('title', '')} {article.get('content_text', '')[:200]}"
            
            # Perform vector similarity search
            results = self.vectorstore.similarity_search_with_score(
                query_text,
                k=n_results
            )
            
            similar = []
            for doc, score in results:
                # Convert distance to similarity (lower distance = higher similarity)
                similarity = 1.0 - score
                
                # Only consider articles with >70% similarity
                if similarity > 0.7:
                    similar.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity": similarity
                    })
            
            return similar
            
        except Exception as e:
            print(f"    Warning: Similarity search failed: {e}")
            return []
    
    def _categorize_with_llm(
        self,
        article: Dict[str, Any],
        similar_articles: List[Dict[str, Any]],
        previous_newsletters: List[Dict[str, Any]]
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Use LLM to categorize article as new or update.
        
        Analyzes the article against similar articles to determine if it's
        a genuinely new story or an update to a previous story.
        
        Args:
            article: Article to categorize
            similar_articles: List of similar articles from vector search
            previous_newsletters: Previous newsletter context
            
        Returns:
            Tuple of (category, update_info) where category is "new" or "update"
        """
        if not self.llm:
            return "new", None
        
        # Prepare similar articles text
        similar_text = "\n".join([
            f"- Similar article (similarity: {s['similarity']:.2f}): {s['metadata'].get('title', 'Untitled')}"
            for s in similar_articles
        ])
        
        prompt = f"""Analyze this article and determine if it's a NEW story or an UPDATE to a previous story.

===============================================================================
NEW ARTICLE
===============================================================================
Title: {article.get('title', 'Untitled')}
Source: {article.get('source_name', 'Unknown')} ({article.get('platform', 'unknown')})
Content: {article.get('content_text', '')[:300]}

===============================================================================
SIMILAR ARTICLES FOUND
===============================================================================
{similar_text if similar_articles else "No similar articles found"}

===============================================================================
INSTRUCTIONS
===============================================================================

Determine if this is:
1. **NEW**: Genuinely new story not covered before
2. **UPDATE**: Same topic as a previous story but with new information

Return JSON:
```json
{{
    "category": "new" or "update",
    "confidence": 0.0 to 1.0,
    "update_info": {{
        "previous_topic": "description of previous coverage",
        "what_changed": "what's new in this version",
        "significance": "why this update matters"
    }} (only if category is "update")
}}
```

Return ONLY the JSON.
"""
        
        try:
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # Parse JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            result = json.loads(response_text)
            category = result.get("category", "new")
            update_info = result.get("update_info") if category == "update" else None
            
            return category, update_info
            
        except Exception as e:
            print(f"    Warning: Categorization failed: {e}")
            return "new", None
    
    # =========================================================================
    # AGENT 4: GENERATOR
    # =========================================================================
    
    def _generate_newsletter(self, state: NewsletterState) -> NewsletterState:
        """
        Agent 4: Generate the final newsletter.
        
        This agent creates a professional, well-structured newsletter from
        the categorized articles. It uses the GENERATOR_SYSTEM_PROMPT to
        ensure consistent formatting and quality.
        
        Processing steps:
        1. Prepare categorized articles for LLM
        2. Build source tracking data
        3. Send to LLM with generation prompt
        4. Parse and format the newsletter
        5. Store newsletter in ChromaDB
        6. Update state with final newsletter
        
        Args:
            state: Current workflow state with categorized articles
            
        Returns:
            Updated state with generated newsletter and metadata
        """
        print(f"\n{'='*60}")
        print(f"AGENT 4: Generator - Creating newsletter for {state['date']}")
        print(f"{'='*60}")
        
        # =====================================================================
        # BUILD SOURCE TRACKING DATA
        # =====================================================================
        # Organize all articles by platform for source attribution
        sources_tracking = self._build_sources_tracking(state)
        state["sources_tracking"] = sources_tracking
        
        # =====================================================================
        # PREPARE ARTICLES FOR LLM
        # =====================================================================
        # Combine new stories and updates for newsletter generation
        all_articles = state["new_stories"] + [u["article"] for u in state["updates"]]
        articles_text = self._prepare_articles_for_llm(all_articles[:20])
        
        # Prepare updates text
        updates_text = ""
        if state["updates"]:
            updates_text = "\n\n".join([
                f"**{u['article'].get('title', 'Untitled')}**\n"
                f"Previous: {u.get('update_info', {}).get('previous_topic', 'N/A')}\n"
                f"Update: {u.get('update_info', {}).get('what_changed', 'N/A')}"
                for u in state["updates"][:5]  # Limit to 5 updates
            ])
        
        # =====================================================================
        # CONSTRUCT GENERATION PROMPT
        # =====================================================================
        prompt = f"""{GENERATOR_SYSTEM_PROMPT}

===============================================================================
ARTICLES FOR NEWSLETTER
===============================================================================

Date: {state['date']}
Total Articles Analyzed: {len(state['articles'])}
New Stories: {len(state['new_stories'])}
Updates: {len(state['updates'])}
Duplicates Excluded: {len(state['duplicates'])}

-------------------------------------------------------------------------------
NEW STORIES (Top {len(all_articles[:20])})
-------------------------------------------------------------------------------

{articles_text}

-------------------------------------------------------------------------------
UPDATES ON PREVIOUS STORIES
-------------------------------------------------------------------------------

{updates_text if updates_text else "No updates on previous stories."}

-------------------------------------------------------------------------------
SOURCE BREAKDOWN
-------------------------------------------------------------------------------

{json.dumps(sources_tracking, indent=2)}

===============================================================================
INSTRUCTIONS
===============================================================================

Create a complete newsletter following the structure and guidelines in your
system prompt. Ensure every story includes:
- Source attribution (platform + source_name)
- Direct link to original content
- Brief but informative summary

Make it engaging, professional, and easy to scan.
"""
        
        # =====================================================================
        # CALL LLM FOR GENERATION
        # =====================================================================
        if not self.llm:
            print("  Warning: LLM not configured. Creating basic newsletter.")
            newsletter = self._create_basic_newsletter(state)
        else:
            try:
                response = self.llm.invoke(prompt)
                newsletter = response.content
                print("  Successfully generated newsletter")
                
            except Exception as e:
                print(f"  Error generating newsletter: {e}")
                newsletter = self._create_basic_newsletter(state)
        
        # =====================================================================
        # UPDATE STATE WITH NEWSLETTER
        # =====================================================================
        state["newsletter"] = newsletter
        
        # =====================================================================
        # BUILD METADATA
        # =====================================================================
        state["metadata"] = {
            "date": state["date"],
            "article_count": len(all_articles[:20]),
            "new_stories_count": len(state["new_stories"]),
            "updates_count": len(state["updates"]),
            "duplicates_count": len(state["duplicates"]),
            "platforms": list(sources_tracking.keys()),
            "generated_at": datetime.now().isoformat(),
            "model_used": self.model_name
        }
        
        # =====================================================================
        # STORE NEWSLETTER IN CHROMADB
        # =====================================================================
        self._store_newsletter(state)
        
        return state
    
    def _build_sources_tracking(self, state: NewsletterState) -> Dict[str, List[Dict[str, Any]]]:
        """
        Build detailed source tracking data organized by platform.
        
        Creates a structured representation of where each piece of content
        came from: platform → source name → article details.
        
        Args:
            state: Current workflow state with articles
            
        Returns:
            Dictionary organized by platform with article details
        """
        sources_tracking = {}
        
        # Process all articles (new stories + updates)
        all_articles = state["new_stories"] + [u["article"] for u in state["updates"]]
        
        for article in all_articles:
            platform = article.get("platform", "unknown")
            
            if platform not in sources_tracking:
                sources_tracking[platform] = []
            
            sources_tracking[platform].append({
                "source_name": article.get("source_name", "Unknown"),
                "title": article.get("title", "Untitled"),
                "url": article.get("url", ""),
                "timestamp": article.get("timestamp", ""),
                "rank": article.get("rank", 0),
                "score": article.get("score", 0),
                "content_preview": article.get("content_text", "")[:200] + "..."
                if len(article.get("content_text", "")) > 200
                else article.get("content_text", "")
            })
        
        return sources_tracking
    
    def _create_basic_newsletter(self, state: NewsletterState) -> str:
        """
        Create a basic newsletter without LLM (fallback method).
        
        Generates a simple markdown newsletter when LLM is not available.
        Used as fallback to ensure newsletter generation always succeeds.
        
        Args:
            state: Current workflow state
            
        Returns:
            Basic newsletter in markdown format
        """
        lines = [
            f"# 📰 Daily Newsletter - {state['date']}\n",
            f"## Executive Summary\n",
            f"Today's newsletter covers {len(state['new_stories'])} new stories "
            f"and {len(state['updates'])} updates.\n",
            "---\n",
            "## 🔥 Top Stories\n"
        ]
        
        # Add new stories
        for i, article in enumerate(state["new_stories"][:20], 1):
            lines.append(f"### {i}. {article.get('title', 'Untitled')}")
            lines.append(f"**Source:** {article.get('source_name', 'Unknown')} "
                        f"({article.get('platform', 'unknown')})")
            lines.append(f"**Link:** {article.get('url', 'N/A')}\n")
            lines.append(f"{article.get('content_text', 'No content')[:300]}...\n")
        
        # Add updates section if any
        if state["updates"]:
            lines.append("---\n")
            lines.append("## 🔄 Updates on Previous Stories\n")
            for update in state["updates"][:5]:
                article = update["article"]
                info = update.get("update_info", {})
                lines.append(f"### {article.get('title', 'Untitled')}")
                lines.append(f"**Previous:** {info.get('previous_topic', 'N/A')}")
                lines.append(f"**Update:** {info.get('what_changed', 'N/A')}\n")
        
        # Add statistics
        lines.append("---\n")
        lines.append("## 📊 Statistics\n")
        lines.append(f"- **Total Articles Analyzed:** {len(state['articles'])}")
        lines.append(f"- **Articles Selected:** {len(state['new_stories'])}")
        lines.append(f"- **Updates:** {len(state['updates'])}")
        lines.append(f"- **Duplicates Excluded:** {len(state['duplicates'])}")
        
        return "\n".join(lines)
    
    def _store_newsletter(self, state: NewsletterState) -> bool:
        """
        Store the generated newsletter in ChromaDB.
        
        Saves the newsletter with metadata for future retrieval and
        RAG-based deduplication.
        
        Args:
            state: Current workflow state with newsletter
            
        Returns:
            True if successful, False otherwise
        """
        try:
            newsletter_id = f"newsletter_{state['date']}"
            
            # Prepare metadata
            metadata = {
                "type": "newsletter",
                "date": state["date"],
                "article_count": state["metadata"].get("article_count", 0),
                "new_stories_count": state["metadata"].get("new_stories_count", 0),
                "updates_count": state["metadata"].get("updates_count", 0),
                "platforms": json.dumps(state["metadata"].get("platforms", [])),
                "sources_json": json.dumps(state["sources_tracking"]),
                "generated_at": state["metadata"].get("generated_at", ""),
                "model_used": state["metadata"].get("model_used", "")
            }
            
            # Upsert to newsletter collection
            self.newsletter_collection.upsert(
                ids=[newsletter_id],
                documents=[state["newsletter"]],
                metadatas=[metadata]
            )
            
            print(f"  Newsletter stored: {newsletter_id}")
            return True
            
        except Exception as e:
            print(f"  Error storing newsletter: {e}")
            return False
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _prepare_articles_for_llm(self, articles: List[Dict[str, Any]]) -> str:
        """
        Prepare articles text for LLM processing.
        
        Formats articles into a structured text format suitable for
        LLM consumption, including all relevant metadata.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Formatted string of articles
        """
        formatted = []
        for i, article in enumerate(articles, 1):
            formatted.append(f"""
---
Article {i}
Platform: {article.get('platform', 'unknown')}
Source: {article.get('source_name', 'Unknown')}
Title: {article.get('title', 'Untitled')}
Rank: {article.get('rank', 'N/A')}
Score: {article.get('score', 'N/A')}
URL: {article.get('url', 'N/A')}
Timestamp: {article.get('timestamp', 'N/A')}
Content: {article.get('content_text', 'No content')[:500]}
---
""")
        return "\n".join(formatted)
    
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    def generate_newsletter(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a newsletter for a specific date (defaults to today).

        This is the main entry point for newsletter generation.
        Runs the complete 4-agent LangGraph workflow.

        Args:
            target_date: Date in YYYY-MM-DD format. Defaults to today.

        Returns:
            Dictionary containing:
            - id: Newsletter ID
            - date: Newsletter date
            - newsletter: Full newsletter markdown
            - metadata: Newsletter metadata
            - sources: Source tracking data
        """
        target = target_date or datetime.now().strftime("%Y-%m-%d")

        # Initialize state
        initial_state: NewsletterState = {
            "date": target,
            "articles": [],
            "ranked_articles": [],
            "new_stories": [],
            "updates": [],
            "duplicates": [],
            "newsletter": "",
            "metadata": {},
            "sources_tracking": {},
            "previous_newsletters": []
        }
        
        # Run workflow
        print(f"\n{'#'*60}")
        print(f"# NEWSLETTER GENERATION STARTING")
        print(f"# Date: {target}")
        print(f"# Model: {self.model_name}")
        print(f"{'#'*60}")

        result = self.workflow.invoke(initial_state)

        print(f"\n{'#'*60}")
        print(f"# NEWSLETTER GENERATION COMPLETE")
        print(f"{'#'*60}\n")

        return {
            "id": f"newsletter_{target}",
            "date": target,
            "newsletter": result["newsletter"],
            "metadata": result["metadata"],
            "sources": result["sources_tracking"]
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_newsletter(target_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to generate a newsletter.

    Creates a NewsletterGenerator instance and runs the complete workflow.

    Args:
        target_date: Date in YYYY-MM-DD format. Defaults to today.

    Returns:
        Dictionary with newsletter data
    """
    generator = NewsletterGenerator()
    return generator.generate_newsletter(target_date=target_date)


def get_latest_newsletter() -> Optional[Dict[str, Any]]:
    """
    Get the most recent newsletter from storage.
    
    Returns:
        Newsletter data or None if no newsletters exist
        
    Example:
        >>> from ai.newsletter import get_latest_newsletter
        >>> newsletter = get_latest_newsletter()
        >>> if newsletter:
        ...     print(newsletter["document"])
    """
    from db.chroma_db import get_latest_newsletter as db_get_latest
    
    client = get_chroma_client()
    collection = get_or_create_collection(client, name="newsletters")
    return db_get_latest(collection)


def get_newsletter_by_date(date: str) -> Optional[Dict[str, Any]]:
    """
    Get newsletter for a specific date.
    
    Args:
        date: Date string in YYYY-MM-DD format
        
    Returns:
        Newsletter data or None if not found
        
    Example:
        >>> from ai.newsletter import get_newsletter_by_date
        >>> newsletter = get_newsletter_by_date("2024-01-15")
    """
    from db.chroma_db import get_newsletter_by_date as db_get_by_date
    
    client = get_chroma_client()
    collection = get_or_create_collection(client, name="newsletters")
    return db_get_by_date(collection, date)