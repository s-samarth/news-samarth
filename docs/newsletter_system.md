# AI Agent Newsletter System Documentation

This document provides comprehensive documentation for the AI agent-based newsletter generation system, including architecture details, agent descriptions, RAG implementation, and usage examples.

===============================================================================
TABLE OF CONTENTS
===============================================================================

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Agent Descriptions](#3-agent-descriptions)
4. [RAG Implementation](#4-rag-implementation)
5. [Newsletter Format](#5-newsletter-format)
6. [API Endpoints](#6-api-endpoints)
7. [Configuration](#7-configuration)
8. [Usage Examples](#8-usage-examples)
9. [Customization](#9-customization)
10. [Troubleshooting](#10-troubleshooting)

===============================================================================
1. OVERVIEW
===============================================================================

The AI Agent Newsletter System is a sophisticated newsletter generation pipeline
that uses LangGraph with multiple AI agents to create professional, ranked
newsletters from collected news articles.

### Key Features

- **4-Agent Workflow**: Specialized agents for fetching, ranking, deduplication, and generation
- **AI-Powered Ranking**: Articles ranked by impact, uniqueness, credibility, and depth
- **RAG-Based Deduplication**: Uses vector similarity to identify duplicates and updates
- **Update Tracking**: Identifies and tracks story updates across newsletters
- **Source Attribution**: Every story includes full source tracking
- **Newsletter History**: All newsletters stored in ChromaDB for retrieval
- **Configurable Models**: Use any OpenRouter model via environment variables

### Use Cases

1. **Daily Newsletters**: Generate professional newsletters for teams or audiences
2. **Content Curation**: Rank and filter news for decision-makers
3. **Story Tracking**: Track how stories evolve over time
4. **Source Verification**: Full attribution for fact-checking

===============================================================================
2. ARCHITECTURE
===============================================================================

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LangGraph Newsletter Workflow                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │   Agent 1   │───▶│   Agent 2   │───▶│   Agent 3   │───▶│   Agent 4   │ │
│  │   Fetcher   │    │   Ranker    │    │Deduplicator │    │  Generator  │ │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘ │
│         │                  │                  │                  │          │
│         ▼                  ▼                  ▼                  ▼          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      ChromaDB Collections                            │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │  newsfeed   │  │ newsletters │  │  (RAG via   │                  │   │
│  │  │ (articles)  │  │ (history)   │  │  embeddings)│                  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Fetch**: Retrieve articles from last 24 hours + previous newsletters for RAG
2. **Rank**: AI evaluates and ranks articles by importance (top 20)
3. **Deduplicate**: RAG compares against previous newsletters to find duplicates/updates
4. **Generate**: Create professional newsletter with source attribution
5. **Store**: Save newsletter to ChromaDB for future retrieval and RAG

### State Management

The workflow uses a TypedDict (`NewsletterState`) to pass data between agents:

```python
class NewsletterState(TypedDict):
    date: str                           # Newsletter date
    articles: List[Dict]                # Raw articles from ChromaDB
    ranked_articles: List[Dict]         # After ranking
    new_stories: List[Dict]             # Genuinely new stories
    updates: List[Dict]                 # Updates to previous stories
    duplicates: List[Dict]              # Duplicate articles (excluded)
    newsletter: str                     # Final newsletter markdown
    metadata: Dict                      # Newsletter metadata
    sources_tracking: Dict              # Source attribution data
    previous_newsletters: List[Dict]    # For RAG context
```

===============================================================================
3. AGENT DESCRIPTIONS
===============================================================================

### Agent 1: Fetcher

**Purpose**: Retrieve and prepare articles from the last 24 hours.

**System Prompt**:
```
You are a content fetcher AI agent.

Your role is to:
1. Retrieve articles from the last 24 hours
2. Filter out low-quality or incomplete articles
3. Prepare articles for ranking by extracting key information
4. Organize articles by platform for easier processing

Focus on articles with:
- Complete content (not just titles)
- Valid timestamps
- Credible sources
```

**Processing Steps**:
1. Query ChromaDB for articles from last 24h
2. Filter out articles with <50 characters content
3. Fetch previous newsletters (last 7 days) for RAG context
4. Update state with prepared articles

**Output**: State with `articles` and `previous_newsletters` populated

---

### Agent 2: Ranker

**Purpose**: Rank articles by importance using AI evaluation.

**System Prompt**:
```
You are an expert news editor AI agent.

RANKING CRITERIA (in order of priority):

1. IMPACT (40%): How significant is this news?
   - Does it affect many people or industries?
   - Is it a major announcement or breakthrough?

2. UNIQUENESS (25%): Is this a unique story?
   - Is it being covered by multiple sources?
   - Does it provide new information?

3. SOURCE CREDIBILITY (20%): How credible is the source?
   - Is the source known for accurate reporting?
   - Does the source have expertise?

4. CONTENT DEPTH (15%): How substantial is the content?
   - Does the article provide detailed information?
   - Are there facts, data, or evidence?
```

**Processing Steps**:
1. Prepare articles for LLM (limit 50 for context window)
2. Send to LLM with ranking system prompt
3. Parse JSON response with ranked articles
4. Update state with top 20 ranked articles

**Output**: State with `ranked_articles` (top 20 with scores)

---

### Agent 3: Deduplicator

**Purpose**: Identify duplicates and track story updates using RAG.

**System Prompt**:
```
You are a fact-checker and deduplication AI agent.

DEDUPLICATION RULES:

1. EXACT DUPLICATES: Same URL or identical content
   - Action: EXCLUDE from new stories

2. SEMANTIC DUPLICATES: Same story, different source
   - Action: EXCLUDE from new stories

3. UPDATES: Same topic but new information
   - Action: INCLUDE in updates section

4. NEW STORIES: Genuinely new information
   - Action: INCLUDE in new stories

An article is an "update" if:
- It covers the same event/topic as a previous article
- It provides new information, data, or developments
```

**Processing Steps**:
1. For each ranked article, check URL against previous newsletters
2. Use vector similarity search to find similar content
3. Use LLM to categorize as "new" or "update"
4. Build update tracking with previous version info
5. Update state with categorized articles

**Output**: State with `new_stories`, `updates`, and `duplicates`

---

### Agent 4: Generator

**Purpose**: Create the final professional newsletter.

**System Prompt**:
```
You are a professional newsletter writer AI agent.

NEWSLETTER STRUCTURE:

1. HEADER
   - Title: "📰 Daily AI Newsletter - [DATE]"
   - Subtitle: Brief tagline

2. EXECUTIVE SUMMARY (2-3 sentences)
   - Capture the essence of today's news
   - Highlight the most important development

3. 🔥 TOP STORIES (Numbered 1-20)
   For each story:
   - Rank number and title
   - Source badge (platform + source_name)
   - Relative timestamp
   - Content summary (2-3 paragraphs)
   - Source link (URL)
   - Relevance score

4. 📱 PLATFORM HIGHLIGHTS
   Group stories by platform

5. 🔄 UPDATES ON PREVIOUS STORIES
   - Story title
   - Previous version summary
   - What's new today

6. 📊 STATISTICS
   - Total articles analyzed
   - Articles selected
   - Source breakdown

FORMATTING GUIDELINES:
- Use Markdown for formatting
- Platform colors: Substack (orange), Reddit (orange-red), YouTube (red), Twitter (blue)
- Make it scannable with clear sections
- Include source links for every story
```

**Processing Steps**:
1. Build source tracking data organized by platform
2. Prepare articles and updates for LLM
3. Send to LLM with generation prompt
4. Store newsletter in ChromaDB
5. Update state with final newsletter and metadata

**Output**: State with `newsletter`, `metadata`, and `sources_tracking`

===============================================================================
4. RAG IMPLEMENTATION
===============================================================================

### Overview

RAG (Retrieval-Augmented Generation) is used for intelligent deduplication
and update detection. The system compares new articles against previous
newsletters to identify:

1. **Exact Duplicates**: Same URL already covered
2. **Semantic Duplicates**: Same story from different source
3. **Updates**: Same topic with new information

### Vector Store Setup

```python
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# Create vector store using existing newsfeed collection
vectorstore = Chroma(
    client=get_chroma_client(),
    collection_name="newsfeed",
    embedding_function=OpenAIEmbeddings(
        openai_api_key=config.openrouter_api_key
    )
)
```

### Similarity Search

```python
def _find_similar_articles(article, n_results=3):
    """Find semantically similar articles using vector search."""
    query_text = f"{article['title']} {article['content_text'][:200]}"
    
    results = vectorstore.similarity_search_with_score(
        query_text,
        k=n_results
    )
    
    similar = []
    for doc, score in results:
        similarity = 1.0 - score  # Convert distance to similarity
        
        if similarity > 0.7:  # Only >70% similarity
            similar.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "similarity": similarity
            })
    
    return similar
```

### Update Detection Logic

1. **URL Check**: If URL exists in previous newsletter → duplicate
2. **Vector Search**: Find semantically similar articles
3. **LLM Analysis**: Determine if "new" or "update" based on:
   - Same topic coverage
   - New information provided
   - Evolution of story

### RAG Context

Previous newsletters (last 7 days) are fetched and used as context:
- Enables comparison across multiple days
- Tracks story evolution over time
- Identifies when coverage is redundant

===============================================================================
5. NEWSLETTER FORMAT
===============================================================================

### Structure

```markdown
# 📰 Daily AI Newsletter - January 15, 2024

## Executive Summary
[2-3 sentence overview]

## 🔥 Top Stories

### 1. [Title] - Ranked #1
**Source:** Fireship (YouTube) | **Posted:** 3 hours ago
[Content summary - 2-3 paragraphs]
🔗 [Read Original](url)
📊 **Relevance Score:** 95/100

### 2. [Title] - Ranked #2
...

---

## 📱 Platform Highlights

### YouTube (5 stories)
- [Story 1] - Fireship
- [Story 2] - Two Minute Papers

### Reddit (8 stories)
- [Story 1] - r/LocalLLaMA
...

### Substack (4 stories)
...

### Twitter (3 stories)
...

---

## 🔄 Updates on Previous Stories

- **[Story Title]**: Updated with new information
  - Previous: [summary from yesterday]
  - Today: [new development]

---

## 📊 Today's Statistics

- **Total Articles Analyzed:** 150
- **Articles Selected:** 20
- **Updates on Previous Stories:** 3
- **Sources:** YouTube (5), Reddit (8), Substack (4), Twitter (3)

---

## 🔗 Source Attribution
All stories include direct links to original sources for verification.
```

### Platform Badge Colors

| Platform | Color | Hex Code |
|----------|-------|----------|
| Substack | Orange | #FF6719 |
| Reddit | Orange-Red | #FF4500 |
| YouTube | Red | #FF0000 |
| Twitter | Sky Blue | #1DA1F2 |

### Frontend Compatibility

The newsletter format is designed to be compatible with the React frontend
specification in `docs/frontend_spec.md`:

- Cards with platform badges
- Source attribution
- Relative timestamps
- Media thumbnails
- Expandable content

===============================================================================
6. API ENDPOINTS
===============================================================================

### Newsletter Generation

#### POST /newsletter/generate
Trigger AI agent-based newsletter generation for the last 24 hours.

**Response:**
```json
{
  "success": true,
  "id": "newsletter_2024-01-15",
  "date": "2024-01-15",
  "newsletter": "# 📰 Daily Newsletter...\n...",
  "metadata": {
    "date": "2024-01-15",
    "article_count": 20,
    "new_stories_count": 17,
    "updates_count": 3,
    "platforms": ["youtube", "reddit", "substack", "twitter"],
    "generated_at": "2024-01-15T08:00:00",
    "model_used": "anthropic/claude-3.5-sonnet"
  },
  "sources": {
    "youtube": [...],
    "reddit": [...],
    ...
  }
}
```

---

#### GET /newsletter/latest
Get the most recent AI-generated newsletter.

**Response:** Same as POST /newsletter/generate

---

#### GET /newsletter/{date}
Get newsletter for a specific date (YYYY-MM-DD).

**Example:** `GET /newsletter/2024-01-15`

---

#### GET /newsletter/{date}/sources
Get source tracking data for a specific newsletter.

**Response:**
```json
{
  "success": true,
  "date": "2024-01-15",
  "sources": {
    "youtube": [
      {
        "source_name": "Fireship",
        "title": "100 Seconds of AI",
        "url": "https://...",
        "rank": 1,
        "score": 95
      }
    ],
    ...
  },
  "platforms": ["youtube", "reddit", "substack", "twitter"],
  "total_articles": 20
}
```

---

#### GET /newsletter/{date}/updates
Get update tracking data for a specific newsletter.

**Response:**
```json
{
  "success": true,
  "date": "2024-01-15",
  "updates": [
    {
      "article": {...},
      "update_info": {
        "previous_topic": "Company X announces new AI model",
        "what_changed": "Model now available for public use",
        "significance": "Major milestone for accessibility"
      }
    }
  ],
  "update_count": 3
}
```

---

#### GET /newsletter/history?limit=30
Get list of past newsletters (summary info only).

**Parameters:**
- `limit`: Number of days to look back (1-90, default: 30)

**Response:**
```json
{
  "success": true,
  "total": 15,
  "newsletters": [
    {
      "id": "newsletter_2024-01-15",
      "date": "2024-01-15",
      "article_count": 20,
      "new_stories_count": 17,
      "updates_count": 3,
      "platforms": ["youtube", "reddit"],
      "generated_at": "2024-01-15T08:00:00"
    },
    ...
  ]
}
```

===============================================================================
7. CONFIGURATION
===============================================================================

### Environment Variables

```env
# OpenRouter Configuration
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Newsletter-Specific Configuration
NEWSLETTER_MODEL=anthropic/claude-3.5-sonnet  # Can differ from summarization
NEWSLETTER_TOP_N=20                            # Number of articles in newsletter
```

### Model Selection

Different models can be used for different tasks:

| Task | Config Variable | Recommended Model |
|------|-----------------|-------------------|
| Summarization | `OPENROUTER_MODEL` | anthropic/claude-3.5-sonnet |
| Newsletter | `NEWSLETTER_MODEL` | anthropic/claude-3.5-sonnet |

### ChromaDB Collections

| Collection | Purpose | Document Type |
|------------|---------|---------------|
| `newsfeed` | Article storage | Articles from all platforms |
| `newsletters` | Newsletter history | Generated newsletters |

===============================================================================
8. USAGE EXAMPLES
===============================================================================

### Python API

```python
from ai.newsletter import (
    NewsletterGenerator,
    generate_newsletter,
    get_latest_newsletter,
    get_newsletter_by_date
)

# Method 1: Convenience function
result = generate_newsletter()
print(result["newsletter"])

# Method 2: Using class directly
generator = NewsletterGenerator()
result = generator.generate_newsletter()

# Access source tracking
for platform, articles in result["sources"].items():
    print(f"\n{platform.upper()}:")
    for article in articles:
        print(f"  #{article['rank']} {article['source_name']}: {article['title']}")

# Get previous newsletter
latest = get_latest_newsletter()
if latest:
    print(latest["document"])

# Get specific date
newsletter = get_newsletter_by_date("2024-01-15")
```

### REST API

```bash
# Generate newsletter
curl -X POST http://localhost:8000/newsletter/generate

# Get latest newsletter
curl http://localhost:8000/newsletter/latest

# Get newsletter by date
curl http://localhost:8000/newsletter/2024-01-15

# Get source tracking
curl http://localhost:8000/newsletter/2024-01-15/sources

# Get update tracking
curl http://localhost:8000/newsletter/2024-01-15/updates

# Get newsletter history
curl http://localhost:8000/newsletter/history?limit=7
```

### Scheduling Daily Newsletters

#### Using Crontab (macOS/Linux)

```bash
# Edit crontab
crontab -e

# Add: Generate newsletter daily at 8 AM
0 8 * * * cd /path/to/news-samarth && /path/to/venv/bin/python -c "from ai.newsletter import generate_newsletter; generate_newsletter()"
```

#### Using API + Cron

```bash
# Add to crontab
0 8 * * * curl -X POST http://localhost:8000/newsletter/generate
```

===============================================================================
9. CUSTOMIZATION
===============================================================================

### Modifying Agent Behavior

Each agent has a system prompt that can be customized:

```python
# In ai/newsletter.py, modify the system prompts:

RANKER_SYSTEM_PROMPT = """Your custom ranking criteria...

1. YOUR_CRITERIA (X%): Description
2. ...
"""

DEDUPLICATOR_SYSTEM_PROMPT = """Your custom deduplication rules...

1. YOUR_RULE: Description
2. ...
"""

GENERATOR_SYSTEM_PROMPT = """Your custom newsletter format...

1. YOUR_SECTION: Description
2. ...
"""
```

### Adjusting Ranking Criteria

Modify the ranking weights in the Ranker system prompt:

```python
RANKER_SYSTEM_PROMPT = """
RANKING CRITERIA:
1. YOUR_PRIORITY (50%): Your description
2. SECONDARY (30%): Your description
3. TERTIARY (20%): Your description
"""
```

### Custom Newsletter Format

Modify the Generator system prompt to change the newsletter structure:

```python
GENERATOR_SYSTEM_PROMPT = """
Your custom structure:
1. CUSTOM_HEADER
2. CUSTOM_SECTIONS
3. ...
"""
```

### Adding New Agents

To add additional agents to the workflow:

```python
def _build_workflow(self) -> StateGraph:
    workflow = StateGraph(NewsletterState)
    
    # Add new agent node
    workflow.add_node("custom_agent", self._custom_agent)
    
    # Modify edges
    workflow.add_edge("rank_articles", "custom_agent")
    workflow.add_edge("custom_agent", "deduplicate")
    
    return workflow.compile()
```

===============================================================================
10. TROUBLESHOOTING
===============================================================================

### Common Issues

#### "OPENROUTER_API_KEY not set"
- **Cause**: API key not configured
- **Solution**: Add `OPENROUTER_API_KEY` to `.env` file

#### "No articles found"
- **Cause**: No articles in database for last 24 hours
- **Solution**: Run extraction first: `python scripts/run_all.py`

#### Newsletter generation fails
- **Possible causes**:
  - Invalid model name in `NEWSLETTER_MODEL`
  - OpenRouter API rate limits
  - Insufficient articles for meaningful newsletter
- **Solutions**:
  - Check model name at https://openrouter.ai/models
  - Wait and retry (rate limits)
  - Run extraction to get more articles

#### RAG similarity search fails
- **Cause**: Embeddings not configured properly
- **Solution**: Ensure `OPENROUTER_API_KEY` is set (used for embeddings)

#### Duplicates not detected
- **Cause**: Similarity threshold too high
- **Solution**: Adjust threshold in `_find_similar_articles()`:
  ```python
  if similarity > 0.6:  # Lower threshold = more aggressive dedup
  ```

### Logging

The system provides detailed logging:

```
############################################################
# NEWSLETTER GENERATION STARTING
# Date: 2024-01-15
# Model: anthropic/claude-3.5-sonnet
############################################################

============================================================
AGENT 1: Fetcher - Retrieving articles for 2024-01-15
============================================================
  Fetched 150 articles
  After filtering: 120 articles
  Retrieved 7 previous newsletters for RAG

============================================================
AGENT 2: Ranker - Ranking 120 articles
============================================================
  Successfully ranked 20 articles

============================================================
AGENT 3: Deduplicator - Analyzing 20 articles
============================================================
  [NEW] Article title 1...
  [UPDATE] Article title 2...
  [DUPLICATE] Article title 3...
  
  Summary:
    New stories: 15
    Updates: 3
    Duplicates: 2

============================================================
AGENT 4: Generator - Creating newsletter for 2024-01-15
============================================================
  Successfully generated newsletter
  Newsletter stored: newsletter_2024-01-15

############################################################
# NEWSLETTER GENERATION COMPLETE
############################################################
```

### Performance Optimization

1. **Reduce article limit**: Modify `articles[:50]` in ranker to process fewer articles
2. **Use faster model**: Switch to `openai/gpt-4o-mini` for quicker generation
3. **Cache embeddings**: Pre-compute embeddings for frequently accessed articles
4. **Parallel processing**: Process multiple articles simultaneously (advanced)

### Cost Optimization

| Model | ~Cost per Newsletter |
|-------|---------------------|
| Claude 3.5 Sonnet | $0.10-0.30 |
| GPT-4o | $0.10-0.30 |
| GPT-4o-mini | $0.01-0.03 |
| Llama 3.1 70B | $0.01-0.02 |

**Tips:**
- Use cheaper models for testing
- Run once daily, not on-demand
- Limit articles processed (currently 20)
- Cache intermediate results

===============================================================================
APPENDIX: TECHNICAL DETAILS
===============================================================================

### LangGraph Workflow Implementation

```python
def _build_workflow(self) -> StateGraph:
    workflow = StateGraph(NewsletterState)
    
    # Add nodes (agents)
    workflow.add_node("fetch_articles", self._fetch_articles)
    workflow.add_node("rank_articles", self._rank_articles)
    workflow.add_node("deduplicate", self._deduplicate)
    workflow.add_node("generate_newsletter", self._generate_newsletter)
    
    # Define edges (linear workflow)
    workflow.set_entry_point("fetch_articles")
    workflow.add_edge("fetch_articles", "rank_articles")
    workflow.add_edge("rank_articles", "deduplicate")
    workflow.add_edge("deduplicate", "generate_newsletter")
    workflow.add_edge("generate_newsletter", END)
    
    return workflow.compile()
```

### Document Schema

**Newsletter Document:**
```json
{
    "id": "newsletter_2024-01-15",
    "document": "Full newsletter markdown...",
    "metadata": {
        "type": "newsletter",
        "date": "2024-01-15",
        "article_count": 20,
        "new_stories_count": 17,
        "updates_count": 3,
        "platforms": "[\"youtube\", \"reddit\", ...]",
        "sources_json": "{...}",
        "generated_at": "2024-01-15T08:00:00",
        "model_used": "anthropic/claude-3.5-sonnet"
    }
}
```

### Source Tracking Structure

```json
{
  "youtube": [
    {
      "source_name": "Fireship",
      "title": "100 Seconds of AI",
      "url": "https://youtube.com/watch?v=abc",
      "timestamp": "2024-01-15T10:00:00",
      "rank": 1,
      "score": 95,
      "content_preview": "First 200 chars..."
    }
  ],
  "reddit": [...],
  "substack": [...],
  "twitter": [...]
}
```

### Update Tracking Structure

```json
{
  "article": {
    "title": "Company X Releases New AI Model",
    "url": "https://...",
    ...
  },
  "update_info": {
    "previous_topic": "Company X announced new AI model last week",
    "what_changed": "Model now publicly available with API access",
    "significance": "Major step toward democratizing AI access"
  }
}
```

===============================================================================
END OF DOCUMENTATION
===============================================================================