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
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
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
from db.health import check_database_integrity, scan_for_issues, get_database_stats
from db.cleanup import (
    run_cleanup,
    create_backup,
    list_backups,
    restore_backup,
    delete_article_by_url,
    delete_articles_by_urls,
    delete_articles_by_platform,
    get_cleanup_preview
)
from db.timezone_utils import get_timezone_info
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

# Request models for date-based endpoints
class FetchRequest(BaseModel):
    date: str  # YYYY-MM-DD

class GenerateRequest(BaseModel):
    date: str  # YYYY-MM-DD
    force: bool = False

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

@app.post("/newsletter/fetch")
async def fetch_news_for_date(request: FetchRequest):
    """
    Fetch raw news articles for a specific date from all platforms.

    Runs all configured extractors with date filtering, stores results in
    ChromaDB, and returns per-platform fetch status so the frontend can
    decide whether to proceed, retry, or cancel.

    Request body:
        date (str): Target date in YYYY-MM-DD format (within last 30 days)

    Returns:
        Per-platform status with article counts and overall status.
    """
    from api.orchestrator import fetch_for_date
    return fetch_for_date(request.date)


@app.post("/newsletter/generate")
async def trigger_newsletter_generation(request: GenerateRequest = GenerateRequest(date=datetime.now().strftime("%Y-%m-%d"))):
    """
    Generate a newsletter for a specific date.

    If a newsletter already exists for the date and force=False, returns the
    cached version. Otherwise runs the 4-agent AI pipeline.

    Request body:
        date (str): Target date in YYYY-MM-DD format (within last 30 days)
        force (bool): If True, regenerate even if newsletter exists

    Returns:
        Generated or cached newsletter with metadata and sources.
    """
    from api.orchestrator import generate_for_date
    return generate_for_date(request.date, force=request.force)


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


# =============================================================================
# Admin Endpoints (Database Management)
# =============================================================================

@app.get("/admin/health")
async def admin_health_check():
    """
    Comprehensive database health check.
    
    Returns detailed information about database integrity,
    including article counts, platform distribution, and any issues found.
    """
    integrity = check_database_integrity(collection)
    stats = get_database_stats(collection)
    
    return {
        "success": True,
        "integrity": integrity,
        "stats": stats,
        "timezone": get_timezone_info()
    }


@app.get("/admin/scan")
async def admin_scan_issues(sample_size: int = Query(100, ge=1, le=1000)):
    """
    Scan articles for data quality issues.
    
    Validates a sample of articles and reports any issues found.
    
    Args:
        sample_size: Number of articles to sample (1-1000)
    """
    result = scan_for_issues(collection, sample_size=sample_size)
    return {
        "success": True,
        **result
    }


@app.post("/admin/cleanup")
async def admin_cleanup(
    days_old: Optional[int] = Query(None, description="Days to keep (default: config value)"),
    dry_run: bool = Query(True, description="Preview without deleting"),
    backup: bool = Query(True, description="Create backup before deletion")
):
    """
    Clean up old articles from the database.
    
    By default, runs in dry-run mode to preview what would be deleted.
    Set dry_run=false to actually perform the cleanup.
    
    Args:
        days_old: Delete articles older than this many days
        dry_run: If True, only preview (default: True for safety)
        backup: Create backup before deletion (default: True)
    """
    result = run_cleanup(
        collection,
        days_old=days_old,
        dry_run=dry_run,
        backup=backup
    )
    return result


@app.get("/admin/cleanup/preview")
async def admin_cleanup_preview(days_old: Optional[int] = Query(None)):
    """
    Preview what would be deleted by cleanup.
    
    Always runs in dry-run mode - no data is actually deleted.
    
    Args:
        days_old: Delete articles older than this many days
    """
    result = get_cleanup_preview(collection, days_old=days_old)
    return {
        "success": True,
        **result
    }


@app.delete("/admin/articles")
async def admin_delete_articles(
    url: Optional[str] = Query(None, description="Single URL to delete"),
    urls: Optional[str] = Query(None, description="Comma-separated URLs to delete"),
    platform: Optional[str] = Query(None, description="Delete all from platform"),
    confirm: bool = Query(False, description="Confirm deletion")
):
    """
    Surgically remove specific articles from the database.
    
    Must provide at least one of: url, urls, platform
    Must set confirm=true to actually delete.
    
    Args:
        url: Single URL to delete
        urls: Comma-separated list of URLs to delete
        platform: Delete all articles from this platform
        confirm: Must be True to actually delete
    """
    if not confirm:
        return {
            "success": False,
            "message": "Deletion cancelled - confirm=true required",
            "hint": "Add ?confirm=true to actually delete"
        }
    
    if not url and not urls and not platform:
        return {
            "success": False,
            "message": "Must provide at least one of: url, urls, platform"
        }
    
    results = {}
    
    if url:
        deleted = delete_article_by_url(collection, url)
        results["single_url"] = {"url": url, "deleted": deleted}
    
    if urls:
        url_list = [u.strip() for u in urls.split(",") if u.strip()]
        deleted_map = delete_articles_by_urls(collection, url_list)
        results["multiple_urls"] = {
            "requested": len(url_list),
            "deleted": sum(1 for v in deleted_map.values() if v),
            "details": deleted_map
        }
    
    if platform:
        count = delete_articles_by_platform(collection, platform)
        results["platform"] = {"platform": platform, "deleted": count}
    
    return {
        "success": True,
        "results": results
    }


@app.post("/admin/backup")
async def admin_create_backup():
    """
    Create a backup of the database.
    
    Creates a timestamped tar.gz archive of the ChromaDB directory.
    """
    try:
        backup_path = create_backup()
        return {
            "success": True,
            "message": "Backup created successfully",
            "backup_path": str(backup_path),
            "backup_name": backup_path.name
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Backup failed: {str(e)}"
        }


@app.get("/admin/backups")
async def admin_list_backups():
    """
    List available database backups.
    
    Returns list of backups with metadata (filename, size, dates).
    """
    backups = list_backups()
    return {
        "success": True,
        "total": len(backups),
        "backups": backups
    }


@app.post("/admin/restore")
async def admin_restore_backup(
    backup_name: str = Query(..., description="Backup filename to restore"),
    confirm: bool = Query(False, description="Confirm restore")
):
    """
    Restore database from a backup.
    
    WARNING: This will replace the current database!
    A pre-restore backup is automatically created.
    
    Args:
        backup_name: Name of the backup file to restore
        confirm: Must be True to actually restore
    """
    from pathlib import Path
    
    backup_path = config.backup_dir / backup_name
    
    result = restore_backup(backup_path, confirm=confirm)
    return result


@app.get("/admin/timezone")
async def admin_timezone_info():
    """
    Get timezone configuration information.
    
    Returns current timezone settings and time information.
    """
    return {
        "success": True,
        **get_timezone_info()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
