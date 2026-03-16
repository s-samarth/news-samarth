"""
AI Summarization Module using LangChain and LangGraph

This module provides intelligent news summarization using LangGraph workflows
and OpenRouter as the LLM provider. It processes articles from ChromaDB and
generates comprehensive daily news digests with full source tracking.

Features:
    - LangGraph-based stateful workflow
    - OpenRouter integration (OpenAI-compatible API)
    - Full source tracking (platform → source → article)
    - Daily summary storage in ChromaDB
    - Configurable model selection via environment variables

Example:
    >>> from ai.summarizer import NewsSummarizer
    >>> summarizer = NewsSummarizer()
    >>> summary = summarizer.summarize_last_24h()
    >>> print(summary["summary"])
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, TypedDict, Optional

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from config import config
from db.chroma_db import (
    get_chroma_client,
    get_or_create_collection,
    get_articles_last_24h
)


class SummaryState(TypedDict):
    """
    State dictionary for the LangGraph summarization workflow.
    
    Attributes:
        date: Date string (YYYY-MM-DD) for the summary
        articles: List of article dictionaries from ChromaDB
        categorized: Articles grouped by platform
        sources_tracking: Detailed source information for each article
        key_points: Extracted key points and themes
        summary: Generated summary text
        metadata: Summary metadata (article count, topics, etc.)
    """
    date: str
    articles: List[Dict[str, Any]]
    categorized: Dict[str, List[Dict[str, Any]]]
    sources_tracking: Dict[str, List[Dict[str, Any]]]
    key_points: List[str]
    summary: str
    metadata: Dict[str, Any]


class NewsSummarizer:
    """
    AI-powered news summarizer using LangGraph and OpenRouter.
    
    Processes articles from ChromaDB and generates comprehensive daily
    news digests with full source tracking.
    """
    
    def __init__(self):
        """
        Initialize the NewsSummarizer with OpenRouter LLM.
        
        Requires OPENROUTER_API_KEY to be set in environment.
        Model can be configured via OPENROUTER_MODEL environment variable.
        """
        self.api_key = config.openrouter_api_key
        self.model_name = config.openrouter_model
        
        if not self.api_key:
            print("Warning: OPENROUTER_API_KEY not set. Summarization will fail.")
            self.llm = None
        else:
            self.llm = ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=0.3  # Lower temperature for more focused summaries
            )
        
        # Initialize ChromaDB
        self.client = get_chroma_client()
        self.collection = get_or_create_collection(self.client)
        
        # Build the LangGraph workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph summarization workflow.
        
        Creates a stateful graph with the following nodes:
        1. fetch_articles - Retrieve last 24h articles from ChromaDB
        2. categorize - Group articles by platform
        3. extract_sources - Build detailed source tracking
        4. extract_key_points - Identify main themes
        5. generate_summary - LLM generates the digest
        6. store_summary - Save to ChromaDB
        
        Returns:
            Compiled StateGraph workflow
        """
        workflow = StateGraph(SummaryState)
        
        # Add nodes
        workflow.add_node("fetch_articles", self._fetch_articles)
        workflow.add_node("categorize", self._categorize_articles)
        workflow.add_node("extract_sources", self._extract_sources)
        workflow.add_node("extract_key_points", self._extract_key_points)
        workflow.add_node("generate_summary", self._generate_summary)
        workflow.add_node("store_summary", self._store_summary)
        
        # Define edges (linear workflow)
        workflow.set_entry_point("fetch_articles")
        workflow.add_edge("fetch_articles", "categorize")
        workflow.add_edge("categorize", "extract_sources")
        workflow.add_edge("extract_sources", "extract_key_points")
        workflow.add_edge("extract_key_points", "generate_summary")
        workflow.add_edge("generate_summary", "store_summary")
        workflow.add_edge("store_summary", END)
        
        return workflow.compile()
    
    def _fetch_articles(self, state: SummaryState) -> SummaryState:
        """
        Fetch articles from the last 24 hours from ChromaDB.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with articles fetched
        """
        print(f"Fetching articles for {state['date']}...")
        
        result = get_articles_last_24h(self.collection)
        state["articles"] = result.get("items", [])
        
        print(f"Found {len(state['articles'])} articles from last 24 hours")
        return state
    
    def _categorize_articles(self, state: SummaryState) -> SummaryState:
        """
        Categorize articles by platform.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with categorized articles
        """
        print("Categorizing articles by platform...")
        
        categorized = {}
        for article in state["articles"]:
            platform = article.get("platform", "unknown")
            if platform not in categorized:
                categorized[platform] = []
            categorized[platform].append(article)
        
        state["categorized"] = categorized
        
        for platform, articles in categorized.items():
            print(f"  {platform}: {len(articles)} articles")
        
        return state
    
    def _extract_sources(self, state: SummaryState) -> SummaryState:
        """
        Extract detailed source tracking information.
        
        Builds a structured representation of where each piece of content
        came from: platform → source name → article details.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with source tracking
        """
        print("Extracting source information...")
        
        sources_tracking = {}
        
        for platform, articles in state["categorized"].items():
            sources_tracking[platform] = []
            for article in articles:
                sources_tracking[platform].append({
                    "source_name": article.get("source_name", "Unknown"),
                    "title": article.get("title", "Untitled"),
                    "url": article.get("url", ""),
                    "timestamp": article.get("timestamp", ""),
                    "content_preview": article.get("content_text", "")[:200] + "..."
                    if len(article.get("content_text", "")) > 200
                    else article.get("content_text", "")
                })
        
        state["sources_tracking"] = sources_tracking
        return state
    
    def _extract_key_points(self, state: SummaryState) -> SummaryState:
        """
        Extract key points and themes from articles using LLM.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with key points extracted
        """
        print("Extracting key points and themes...")
        
        if not self.llm:
            state["key_points"] = ["LLM not configured - skipping key point extraction"]
            return state
        
        # Prepare article summaries for LLM
        articles_text = self._prepare_articles_for_llm(state["articles"][:50])  # Limit to 50 articles
        
        prompt = f"""Analyze the following news articles and extract the main key points and themes.
Focus on:
1. Major trends or developments
2. Important announcements
3. Recurring topics across multiple sources
4. Noteworthy opinions or analyses

Articles:
{articles_text}

Return ONLY a JSON list of key points, one per line. Example:
["Key point 1", "Key point 2", "Key point 3"]
"""
        
        try:
            response = self.llm.invoke(prompt)
            # Parse the response
            key_points_text = response.content.strip()
            
            # Try to parse as JSON
            try:
                key_points = json.loads(key_points_text)
                if isinstance(key_points, list):
                    state["key_points"] = key_points[:10]  # Limit to 10 key points
                else:
                    state["key_points"] = [key_points_text]
            except json.JSONDecodeError:
                # Fall back to splitting by newlines
                state["key_points"] = [
                    line.strip("- •").strip()
                    for line in key_points_text.split("\n")
                    if line.strip()
                ][:10]
                
        except Exception as e:
            print(f"Error extracting key points: {e}")
            state["key_points"] = ["Unable to extract key points"]
        
        return state
    
    def _generate_summary(self, state: SummaryState) -> SummaryState:
        """
        Generate comprehensive news summary using LLM.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with generated summary
        """
        print("Generating news summary...")
        
        if not self.llm:
            state["summary"] = "LLM not configured - unable to generate summary"
            state["metadata"] = {
                "article_count": len(state["articles"]),
                "key_topics": [],
                "platforms": list(state["categorized"].keys())
            }
            return state
        
        # Prepare articles for LLM
        articles_text = self._prepare_articles_for_llm(state["articles"][:50])
        key_points_text = "\n".join([f"- {kp}" for kp in state["key_points"]])
        
        prompt = f"""Generate a comprehensive daily news digest for {state['date']}.

Based on {len(state['articles'])} articles from {', '.join(state['categorized'].keys())}.

Key Themes Identified:
{key_points_text}

Articles:
{articles_text}

Create a well-structured news digest with:
1. Executive Summary (2-3 sentences)
2. Top Stories (most important news items)
3. Platform-specific highlights
4. Key Takeaways

Format in Markdown. Be concise but informative.
Include source attribution where relevant (e.g., "According to Fireship...").
"""
        
        try:
            response = self.llm.invoke(prompt)
            state["summary"] = response.content
            
            # Extract key topics from key points
            state["metadata"] = {
                "article_count": len(state["articles"]),
                "key_topics": state["key_points"][:5],  # Top 5 as topics
                "platforms": list(state["categorized"].keys()),
                "generated_at": datetime.now().isoformat(),
                "model_used": self.model_name
            }
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            state["summary"] = f"Error generating summary: {str(e)}"
            state["metadata"] = {"error": str(e)}
        
        return state
    
    def _store_summary(self, state: SummaryState) -> SummaryState:
        """
        Store the generated summary in ChromaDB.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state (unchanged)
        """
        print(f"Storing summary for {state['date']}...")
        
        summary_id = f"summary_{state['date']}"
        
        # Prepare summary document
        summary_doc = {
            "id": summary_id,
            "document": state["summary"],
            "metadata": {
                "type": "summary",
                "date": state["date"],
                "article_count": state["metadata"].get("article_count", 0),
                "key_topics": json.dumps(state["metadata"].get("key_topics", [])),
                "platforms": json.dumps(state["metadata"].get("platforms", [])),
                "sources_json": json.dumps(state["sources_tracking"]),
                "generated_at": state["metadata"].get("generated_at", datetime.now().isoformat()),
                "model_used": state["metadata"].get("model_used", self.model_name)
            }
        }
        
        # Upsert to ChromaDB
        try:
            self.collection.upsert(
                ids=[summary_doc["id"]],
                documents=[summary_doc["document"]],
                metadatas=[summary_doc["metadata"]]
            )
            print(f"Summary stored successfully: {summary_id}")
        except Exception as e:
            print(f"Error storing summary: {e}")
        
        return state
    
    def _prepare_articles_for_llm(self, articles: List[Dict[str, Any]]) -> str:
        """
        Prepare articles text for LLM processing.
        
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
Content: {article.get('content_text', 'No content')[:500]}
---
""")
        return "\n".join(formatted)
    
    def summarize_last_24h(self) -> Dict[str, Any]:
        """
        Generate summary for the last 24 hours.
        
        This is the main entry point for summarization.
        Runs the complete LangGraph workflow.
        
        Returns:
            Dictionary with summary data:
            - id: Summary ID
            - date: Date string
            - summary: Generated summary text
            - metadata: Summary metadata
            - sources: Source tracking data
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Initialize state
        initial_state: SummaryState = {
            "date": today,
            "articles": [],
            "categorized": {},
            "sources_tracking": {},
            "key_points": [],
            "summary": "",
            "metadata": {}
        }
        
        # Run workflow
        print(f"\n{'='*60}")
        print(f"Starting news summarization for {today}")
        print(f"Using model: {self.model_name}")
        print(f"{'='*60}\n")
        
        result = self.workflow.invoke(initial_state)
        
        print(f"\n{'='*60}")
        print(f"Summarization complete!")
        print(f"Articles processed: {result['metadata'].get('article_count', 0)}")
        print(f"{'='*60}\n")
        
        return {
            "id": f"summary_{today}",
            "date": today,
            "summary": result["summary"],
            "metadata": result["metadata"],
            "sources": result["sources_tracking"]
        }


def summarize_last_24h() -> Dict[str, Any]:
    """
    Convenience function to summarize last 24 hours of news.
    
    Returns:
        Dictionary with summary data
        
    Example:
        >>> from ai import summarize_last_24h
        >>> summary = summarize_last_24h()
        >>> print(summary["summary"])
    """
    summarizer = NewsSummarizer()
    return summarizer.summarize_last_24h()