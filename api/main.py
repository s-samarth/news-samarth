"""
FastAPI Server for Newsfeed Aggregator

Provides REST API endpoints for querying news content stored in ChromaDB.
Supports filtering, pagination, and the new 24-hour content retrieval feature.

Endpoints:
    GET /feed - Main feed with filtering and pagination
    GET /feed/recent - Last 24 hours content (NEW)
    GET /feed/search - Semantic search (AI-ready)
    GET /sources - Raw sources configuration
    GET /platforms - Platform statistics
    GET /health - Health check

Usage:
    python api/main.py
    
    API available at: http://localhost:8000
    Docs at: http://localhost:8000/docs
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional
import os

from db.chroma_db import (
    get_chroma_client,
    get_or_create_collection,
    get_articles,
    get_articles_last_24h,
    get_platform_stats,
    search_articles,
    get_latest_summary,
    get_summary_by_date,
    get_summary_sources,
    get_latest_newsletter,
    get_newsletter_by_date,
    get_newsletter_sources,
    get_newsletter_updates
)
from config import config

app = FastAPI(
    title="Newsfeed Aggregator API",
    description="REST API for querying news content from multiple platforms",
    version="2.0.0"
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ChromaDB connection
client = get_chroma_client()
collection = get_or_create_collection(client)

# Get the frontend directory path
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")


# =============================================================================
# Frontend Serving
# =============================================================================

@app.get("/")
async def serve_frontend():
    """Serve the main frontend page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# Mount static files for frontend assets
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/feed")
async def read_feed(
    platform: Optional[str] = Query(None, description="Filter by platform (youtube, reddit, substack, twitter)"),
    source_name: Optional[str] = Query(None, description="Filter by source name"),
    limit: int = Query(50, ge=1, le=200, description="Number of results"),
    offset: int = Query(0, ge=0, description="Results offset for pagination")
):
    """
    Get unified feed with optional filtering and pagination.
    
    Returns articles from all platforms sorted by timestamp (newest first).
    Supports filtering by platform and/or source name.
    
    Example:
        GET /feed?platform=youtube&limit=10
    """
    return get_articles(
        collection=collection,
        platform=platform,
        source_name=source_name,
        limit=limit,
        offset=offset
    )


@app.get("/feed/recent")
async def read_recent_feed(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    source_name: Optional[str] = Query(None, description="Filter by source name")
):
    """
    Get all articles from the last 24 hours.
    
    This is the primary endpoint for retrieving recent content as specified
    in the project requirements. Returns full content including:
    - YouTube transcripts
    - Reddit post bodies
    - Substack newsletter text
    - Tweet content
    
    Example:
        GET /feed/recent
        GET /feed/recent?platform=youtube
    """
    return get_articles_last_24h(
        collection=collection,
        platform=platform,
        source_name=source_name
    )


@app.get("/feed/search")
async def search_feed(
    q: str = Query(..., description="Search query"),
    n_results: int = Query(10, ge=1, le=50, description="Number of results")
):
    """
    Search articles using semantic similarity.
    
    Uses ChromaDB's built-in semantic search for AI-powered content discovery.
    Returns articles ranked by relevance to the query.
    
    Note: For best results with semantic search, consider adding embeddings
    to the ChromaDB collection.
    
    Example:
        GET /feed/search?q=artificial+intelligence
    """
    return search_articles(
        collection=collection,
        query=q,
        n_results=n_results
    )


@app.get("/sources")
async def read_sources():
    """
    Get raw sources configuration.
    
    Returns the contents of sources.json showing all configured
    channels, subreddits, newsletters, and Twitter handles.
    """
    return config.sources


@app.get("/platforms")
async def list_platforms():
    """
    Get platform statistics.
    
    Returns list of platforms with article counts.
    Useful for dashboard displays.
    
    Example response:
        [
            {"platform": "youtube", "count": 45},
            {"platform": "reddit", "count": 120},
            ...
        ]
    """
    return get_platform_stats(collection)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns API status and database statistics.
    """
    import os
    
    db_size = 0
    chroma_path = config.chroma_path
    if chroma_path.exists():
        # Calculate total size of ChromaDB directory
        for file in chroma_path.rglob("*"):
            if file.is_file():
                db_size += file.stat().st_size
        db_size = db_size / (1024 * 1024)  # Convert to MB
    
    article_count = collection.count()
    
    return {
        "status": "ok",
        "database": "chromadb",
        "db_path": str(chroma_path),
        "db_size_mb": round(db_size, 2),
        "article_count": article_count
    }


# =============================================================================
# AI Summarization Endpoints
# =============================================================================

@app.post("/summarize")
async def trigger_summarization():
    """
    Trigger AI summarization for the last 24 hours.
    
    Uses LangChain/LangGraph with OpenRouter to generate a comprehensive
    news digest from all articles collected in the last 24 hours.
    
    Returns:
        - summary: Generated markdown summary
        - metadata: Summary metadata (article count, topics, etc.)
        - sources: Full source tracking data
        
    Requires:
        - OPENROUTER_API_KEY environment variable to be set
        - Articles in the database from the last 24 hours
    """
    try:
        from ai.summarizer import summarize_last_24h
        
        result = summarize_last_24h()
        
        return {
            "success": True,
            "summary": result["summary"],
            "metadata": result["metadata"],
            "sources": result["sources"],
            "date": result["date"],
            "id": result["id"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/summary/latest")
async def read_latest_summary():
    """
    Get the most recent AI-generated summary.
    
    Returns the latest daily news digest with full source tracking.
    """
    summary = get_latest_summary(collection)
    
    if not summary:
        return {
            "success": False,
            "error": "No summaries found"
        }
    
    # Parse sources from JSON string
    import json
    sources_json = summary["metadata"].get("sources_json", "{}")
    try:
        sources = json.loads(sources_json)
    except json.JSONDecodeError:
        sources = {}
    
    return {
        "success": True,
        "id": summary["id"],
        "summary": summary["document"],
        "metadata": {
            "date": summary["metadata"].get("date"),
            "article_count": summary["metadata"].get("article_count", 0),
            "key_topics": json.loads(summary["metadata"].get("key_topics", "[]")),
            "platforms": json.loads(summary["metadata"].get("platforms", "[]")),
            "generated_at": summary["metadata"].get("generated_at"),
            "model_used": summary["metadata"].get("model_used")
        },
        "sources": sources
    }


@app.get("/summary/{date}")
async def read_summary_by_date(date: str):
    """
    Get summary for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format
        
    Returns:
        Summary with full source tracking for the specified date.
    """
    summary = get_summary_by_date(collection, date)
    
    if not summary:
        return {
            "success": False,
            "error": f"No summary found for {date}"
        }
    
    # Parse sources from JSON string
    import json
    sources_json = summary["metadata"].get("sources_json", "{}")
    try:
        sources = json.loads(sources_json)
    except json.JSONDecodeError:
        sources = {}
    
    return {
        "success": True,
        "id": summary["id"],
        "summary": summary["document"],
        "metadata": {
            "date": summary["metadata"].get("date"),
            "article_count": summary["metadata"].get("article_count", 0),
            "key_topics": json.loads(summary["metadata"].get("key_topics", "[]")),
            "platforms": json.loads(summary["metadata"].get("platforms", "[]")),
            "generated_at": summary["metadata"].get("generated_at"),
            "model_used": summary["metadata"].get("model_used")
        },
        "sources": sources
    }


@app.get("/summary/{date}/sources")
async def read_summary_sources(date: str):
    """
    Get source tracking data for a specific summary.
    
    Returns the detailed breakdown of where each piece of content
    came from: platform → source → article.
    
    Args:
        date: Date in YYYY-MM-DD format
        
    Returns:
        Source tracking data organized by platform.
    """
    sources = get_summary_sources(collection, date)
    
    if not sources:
        return {
            "success": False,
            "error": f"No source data found for {date}"
        }
    
    return {
        "success": True,
        "date": date,
        "sources": sources,
        "platforms": list(sources.keys()),
        "total_articles": sum(len(articles) for articles in sources.values())
    }


# =============================================================================
# Newsletter Endpoints (AI Agent-based)
# =============================================================================

@app.post("/newsletter/generate")
async def trigger_newsletter_generation():
    """
    Trigger AI agent-based newsletter generation for the last 24 hours.
    
    Uses a 4-agent LangGraph workflow:
    1. Fetcher Agent: Retrieves articles from ChromaDB
    2. Ranker Agent: Ranks articles by importance using AI
    3. Deduplicator Agent: Identifies duplicates and updates using RAG
    4. Generator Agent: Creates the final newsletter
    
    Returns:
        - newsletter: Generated newsletter markdown
        - metadata: Newsletter metadata (article counts, platforms, etc.)
        - sources: Full source tracking data
        - updates: Update tracking for previous stories
        
    Requires:
        - OPENROUTER_API_KEY environment variable to be set
        - Articles in the database from the last 24 hours
    """
    try:
        from ai.newsletter import generate_newsletter
        
        result = generate_newsletter()
        
        return {
            "success": True,
            "id": result["id"],
            "date": result["date"],
            "newsletter": result["newsletter"],
            "metadata": result["metadata"],
            "sources": result["sources"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/newsletter/latest")
async def read_latest_newsletter():
    """
    Get the most recent AI-generated newsletter.
    
    Returns the latest daily newsletter with full source tracking
    and update information.
    """
    newsletter = get_latest_newsletter(collection)
    
    if not newsletter:
        return {
            "success": False,
            "error": "No newsletters found"
        }
    
    # Parse sources from JSON string
    import json
    sources_json = newsletter["metadata"].get("sources_json", "{}")
    try:
        sources = json.loads(sources_json)
    except json.JSONDecodeError:
        sources = {}
    
    return {
        "success": True,
        "id": newsletter["id"],
        "newsletter": newsletter["document"],
        "metadata": {
            "date": newsletter["metadata"].get("date"),
            "article_count": newsletter["metadata"].get("article_count", 0),
            "new_stories_count": newsletter["metadata"].get("new_stories_count", 0),
            "updates_count": newsletter["metadata"].get("updates_count", 0),
            "platforms": json.loads(newsletter["metadata"].get("platforms", "[]")),
            "generated_at": newsletter["metadata"].get("generated_at"),
            "model_used": newsletter["metadata"].get("model_used")
        },
        "sources": sources
    }


@app.get("/newsletter/{date}")
async def read_newsletter_by_date(date: str):
    """
    Get newsletter for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format
        
    Returns:
        Newsletter with full source tracking and update information.
    """
    newsletter = get_newsletter_by_date(collection, date)
    
    if not newsletter:
        return {
            "success": False,
            "error": f"No newsletter found for {date}"
        }
    
    # Parse sources from JSON string
    import json
    sources_json = newsletter["metadata"].get("sources_json", "{}")
    try:
        sources = json.loads(sources_json)
    except json.JSONDecodeError:
        sources = {}
    
    return {
        "success": True,
        "id": newsletter["id"],
        "newsletter": newsletter["document"],
        "metadata": {
            "date": newsletter["metadata"].get("date"),
            "article_count": newsletter["metadata"].get("article_count", 0),
            "new_stories_count": newsletter["metadata"].get("new_stories_count", 0),
            "updates_count": newsletter["metadata"].get("updates_count", 0),
            "platforms": json.loads(newsletter["metadata"].get("platforms", "[]")),
            "generated_at": newsletter["metadata"].get("generated_at"),
            "model_used": newsletter["metadata"].get("model_used")
        },
        "sources": sources
    }


@app.get("/newsletter/{date}/sources")
async def read_newsletter_sources(date: str):
    """
    Get source tracking data for a specific newsletter.
    
    Returns the detailed breakdown of where each piece of content
    came from: platform → source → article, with ranking scores.
    
    Args:
        date: Date in YYYY-MM-DD format
        
    Returns:
        Source tracking data organized by platform with rankings.
    """
    sources = get_newsletter_sources(collection, date)
    
    if not sources:
        return {
            "success": False,
            "error": f"No source data found for {date}"
        }
    
    return {
        "success": True,
        "date": date,
        "sources": sources,
        "platforms": list(sources.keys()),
        "total_articles": sum(len(articles) for articles in sources.values())
    }


@app.get("/newsletter/{date}/updates")
async def read_newsletter_updates(date: str):
    """
    Get update tracking data for a specific newsletter.
    
    Returns information about stories that were updates to previous coverage,
    showing what changed and why it matters.
    
    Args:
        date: Date in YYYY-MM-DD format
        
    Returns:
        Update tracking data with previous versions and changes.
    """
    updates = get_newsletter_updates(collection, date)
    
    if not updates:
        return {
            "success": False,
            "error": f"No update data found for {date}"
        }
    
    return {
        "success": True,
        "date": date,
        "updates": updates,
        "update_count": len(updates) if isinstance(updates, list) else 0
    }


@app.get("/newsletter/history")
async def read_newsletter_history(limit: int = Query(30, ge=1, le=90)):
    """
    Get list of past newsletters.
    
    Args:
        limit: Maximum number of newsletters to return (1-90 days)
        
    Returns:
        List of newsletter summaries with dates and metadata.
    """
    from db.chroma_db import get_newsletters_range
    from datetime import datetime, timedelta
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=limit)).strftime("%Y-%m-%d")
    
    newsletters = get_newsletters_range(collection, start_date, end_date)
    
    # Return summary info only (not full newsletter content)
    history = []
    for nl in newsletters:
        metadata = nl.get("metadata", {})
        history.append({
            "id": nl["id"],
            "date": metadata.get("date"),
            "article_count": metadata.get("article_count", 0),
            "new_stories_count": metadata.get("new_stories_count", 0),
            "updates_count": metadata.get("updates_count", 0),
            "platforms": json.loads(metadata.get("platforms", "[]")),
            "generated_at": metadata.get("generated_at")
        })
    
    return {
        "success": True,
        "total": len(history),
        "newsletters": history
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
