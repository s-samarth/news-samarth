"""
ChromaDB Database Module for Newsfeed Aggregator

This module provides a local, AI-ready NoSQL database for storing and querying
news content from multiple platforms. ChromaDB is chosen for its:
- Local-first architecture (no cloud dependencies)
- Native support for vector embeddings (AI/ML ready)
- Simple document-based storage model
- Excellent integration with LangChain and other AI frameworks

Database Schema:
    Each document in ChromaDB represents a single news item with:
    - id: Unique identifier (URL hash)
    - document: Full content text (transcript, article, tweet, post)
    - metadata: Platform, source, title, URL, timestamp, media link

Example Usage:
    >>> from db.chroma_db import get_chroma_client, get_or_create_collection, upsert_articles
    >>> client = get_chroma_client()
    >>> collection = get_or_create_collection(client)
    >>> articles = [{"url": "...", "title": "...", ...}]
    >>> upsert_articles(collection, articles)
"""

import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.api import Collection

from config import config


def get_chroma_client() -> chromadb.PersistentClient:
    """
    Get or create a persistent ChromaDB client.
    
    The client stores data locally in the configured chroma_path directory.
    Data persists between application restarts.
    
    Returns:
        chromadb.PersistentClient: Configured ChromaDB client instance
        
    Example:
        >>> client = get_chroma_client()
        >>> print(f"Database location: {config.chroma_path}")
    """
    return chromadb.PersistentClient(path=str(config.chroma_path))


def get_or_create_collection(
    client: chromadb.PersistentClient,
    name: str = "newsfeed"
) -> Collection:
    """
    Get or create the main newsfeed collection.
    
    A collection is like a table in SQL databases - it holds all news articles.
    The collection uses metadata indexing for efficient filtering by platform,
    source, and timestamp.
    
    Args:
        client: ChromaDB client instance
        name: Collection name (default: "newsfeed")
        
    Returns:
        Collection: The newsfeed collection
        
    Example:
        >>> client = get_chroma_client()
        >>> collection = get_or_create_collection(client)
        >>> print(f"Collection has {collection.count()} items")
    """
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}  # Enable cosine similarity for future semantic search
    )


def _generate_doc_id(url: str) -> str:
    """
    Generate a unique document ID from URL.
    
    Uses SHA256 hash to create a consistent, unique identifier for each article.
    This ensures the same URL always produces the same ID, enabling deduplication.
    
    Args:
        url: The article URL
        
    Returns:
        str: Hex digest of the URL hash
        
    Example:
        >>> doc_id = _generate_doc_id("https://example.com/article")
        >>> print(doc_id)  # 'a1b2c3d4...'
    """
    return hashlib.sha256(url.encode()).hexdigest()


def upsert_articles(
    collection: Collection,
    articles: List[Dict[str, Any]]
) -> int:
    """
    Insert or update articles in the collection.
    
    Uses upsert semantics: if an article with the same URL exists, it's updated;
    otherwise, it's inserted. This prevents duplicates while allowing content updates.
    
    Args:
        collection: ChromaDB collection instance
        articles: List of article dictionaries with keys:
            - url (str): Unique article URL (required)
            - platform (str): Source platform (required)
            - source_name (str): Creator/source name (required)
            - title (str): Article title
            - content_text (str): Full content (transcript, article text, etc.)
            - timestamp (str): ISO 8601 publication timestamp
            - media_link (str): Image/thumbnail URL
            
    Returns:
        int: Number of new articles added (not updates)
        
    Example:
        >>> articles = [
        ...     {
        ...         "url": "https://youtube.com/watch?v=abc",
        ...         "platform": "youtube",
        ...         "source_name": "Fireship",
        ...         "title": "100 Seconds of AI",
        ...         "content_text": "Full transcript here...",
        ...         "timestamp": "2024-01-15T10:00:00",
        ...         "media_link": "https://img.youtube.com/..."
        ...     }
        ... ]
        >>> count = upsert_articles(collection, articles)
    """
    if not articles:
        return 0
    
    ids = []
    documents = []
    metadatas = []
    
    for article in articles:
        url = article.get("url")
        if not url:
            continue
            
        doc_id = _generate_doc_id(url)
        ids.append(doc_id)
        
        # Full content stored as the document
        documents.append(article.get("content_text") or article.get("title") or "")
        
        # Metadata for filtering and display
        metadatas.append({
            "platform": article.get("platform", "unknown"),
            "source_name": article.get("source_name", "unknown"),
            "title": article.get("title", ""),
            "url": url,
            "timestamp": article.get("timestamp", datetime.now().isoformat()),
            "media_link": article.get("media_link", ""),
            "scraped_at": datetime.now().isoformat()
        })
    
    # Upsert: insert or update if exists
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    
    return len(ids)


def get_articles(
    collection: Collection,
    platform: Optional[str] = None,
    source_name: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Retrieve articles with optional filtering.
    
    Supports filtering by platform and/or source name, with pagination.
    Results are ordered by timestamp (newest first).
    
    Args:
        collection: ChromaDB collection instance
        platform: Filter by platform (e.g., "youtube", "reddit")
        source_name: Filter by source name (e.g., "Fireship")
        limit: Maximum number of results
        offset: Number of results to skip (for pagination)
        
    Returns:
        dict: Response with "total" count and "items" list
        
    Example:
        >>> result = get_articles(collection, platform="youtube", limit=10)
        >>> print(f"Found {result['total']} YouTube articles")
    """
    # Build where clause for filtering
    where = {}
    if platform:
        where["platform"] = platform
    if source_name:
        where["source_name"] = source_name
    
    # Get total count first
    total = collection.count(where=where if where else None)
    
    # Get articles with pagination
    results = collection.get(
        where=where if where else None,
        limit=limit,
        offset=offset,
        include=["documents", "metadatas"]
    )
    
    # Format response
    items = []
    for i, doc_id in enumerate(results["ids"]):
        metadata = results["metadatas"][i] if results["metadatas"] else {}
        items.append({
            "id": doc_id,
            "content_text": results["documents"][i] if results["documents"] else "",
            **metadata
        })
    
    # Sort by timestamp (newest first)
    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {
        "total": total,
        "items": items
    }


def get_articles_last_24h(
    collection: Collection,
    platform: Optional[str] = None,
    source_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get all articles from the last 24 hours.
    
    This is the primary function for retrieving recent content as specified
    in the project requirements. Filters articles by timestamp to only include
    content published in the last 24 hours.
    
    Args:
        collection: ChromaDB collection instance
        platform: Optional platform filter
        source_name: Optional source filter
        
    Returns:
        dict: Response with "total" count and "items" list from last 24h
        
    Example:
        >>> result = get_articles_last_24h(collection)
        >>> print(f"Found {result['total']} articles in last 24 hours")
    """
    # Calculate 24 hours ago in ISO format
    yesterday = (datetime.now() - timedelta(hours=24)).isoformat()
    
    # Build where clause with timestamp filter
    where = {
        "timestamp": {"$gte": yesterday}
    }
    
    # Add optional filters
    if platform:
        where["platform"] = platform
    if source_name:
        where["source_name"] = source_name
    
    # Get all matching articles
    results = collection.get(
        where=where,
        include=["documents", "metadatas"]
    )
    
    # Format response
    items = []
    for i, doc_id in enumerate(results["ids"]):
        metadata = results["metadatas"][i] if results["metadatas"] else {}
        items.append({
            "id": doc_id,
            "content_text": results["documents"][i] if results["documents"] else "",
            **metadata
        })
    
    # Sort by timestamp (newest first)
    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {
        "total": len(items),
        "items": items
    }


def get_platform_stats(collection: Collection) -> List[Dict[str, Any]]:
    """
    Get article counts grouped by platform.
    
    Useful for dashboard displays and understanding content distribution.
    
    Args:
        collection: ChromaDB collection instance
        
    Returns:
        list: List of dicts with "platform" and "count" keys
        
    Example:
        >>> stats = get_platform_stats(collection)
        >>> for stat in stats:
        ...     print(f"{stat['platform']}: {stat['count']} articles")
    """
    # Get all articles to compute stats
    # Note: For large datasets, consider caching this
    all_items = collection.get(include=["metadatas"])
    
    # Count by platform
    platform_counts = {}
    for metadata in (all_items["metadatas"] or []):
        platform = metadata.get("platform", "unknown")
        platform_counts[platform] = platform_counts.get(platform, 0) + 1
    
    return [
        {"platform": platform, "count": count}
        for platform, count in platform_counts.items()
    ]


def search_articles(
    collection: Collection,
    query: str,
    n_results: int = 10
) -> Dict[str, Any]:
    """
    Search articles using semantic similarity (future-ready).
    
    This function uses ChromaDB's built-in semantic search capabilities.
    When combined with embeddings, it enables natural language search
    over your news archive.
    
    Args:
        collection: ChromaDB collection instance
        query: Search query text
        n_results: Number of results to return
        
    Returns:
        dict: Search results with relevance scores
        
    Example:
        >>> results = search_articles(collection, "AI developments")
        >>> for item in results["items"]:
        ...     print(f"{item['title']} (score: {item['distance']})")
    """
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    
    items = []
    for i, doc_id in enumerate(results["ids"][0] if results["ids"] else []):
        metadata = results["metadatas"][0][i] if results["metadatas"] else {}
        items.append({
            "id": doc_id,
            "content_text": results["documents"][0][i] if results["documents"] else "",
            "distance": results["distances"][0][i] if results["distances"] else None,
            **metadata
        })
    
    return {
        "total": len(items),
        "items": items
    }


def delete_old_articles(
    collection: Collection,
    days_old: int = 30
) -> int:
    """
    Delete articles older than specified days.
    
    Useful for managing database size by removing old content.
    
    Args:
        collection: ChromaDB collection instance
        days_old: Delete articles older than this many days
        
    Returns:
        int: Number of articles deleted
        
    Example:
        >>> deleted = delete_old_articles(collection, days_old=30)
        >>> print(f"Deleted {deleted} old articles")
    """
    cutoff = (datetime.now() - timedelta(days=days_old)).isoformat()
    
    # Get old articles
    old_articles = collection.get(
        where={"timestamp": {"$lt": cutoff}},
        include=["metadatas"]
    )
    
    if old_articles["ids"]:
        collection.delete(ids=old_articles["ids"])
        return len(old_articles["ids"])
    
    return 0


# =============================================================================
# Summary Functions (for AI-generated daily digests)
# =============================================================================

def store_summary(
    collection: Collection,
    summary_id: str,
    summary_text: str,
    metadata: Dict[str, Any]
) -> bool:
    """
    Store an AI-generated summary in the collection.
    
    Summaries are stored with a special "type": "summary" metadata field
    to distinguish them from regular articles.
    
    Args:
        collection: ChromaDB collection instance
        summary_id: Unique summary ID (e.g., "summary_2024-01-15")
        summary_text: Generated summary markdown text
        metadata: Summary metadata including:
            - date: Summary date (YYYY-MM-DD)
            - article_count: Number of articles summarized
            - key_topics: List of key topics
            - platforms: List of platforms included
            - sources_json: JSON string of source tracking data
            - generated_at: ISO 8601 timestamp
            - model_used: LLM model name
            
    Returns:
        bool: True if successful
        
    Example:
        >>> store_summary(
        ...     collection,
        ...     "summary_2024-01-15",
        ...     "## Daily Digest\n...",
        ...     {"date": "2024-01-15", "article_count": 25}
        ... )
    """
    try:
        # Add type marker to distinguish from articles
        full_metadata = {"type": "summary", **metadata}
        
        collection.upsert(
            ids=[summary_id],
            documents=[summary_text],
            metadatas=[full_metadata]
        )
        return True
    except Exception as e:
        print(f"Error storing summary: {e}")
        return False


def get_latest_summary(collection: Collection) -> Optional[Dict[str, Any]]:
    """
    Get the most recent AI-generated summary.
    
    Args:
        collection: ChromaDB collection instance
        
    Returns:
        dict or None: Summary data with id, document, and metadata
        
    Example:
        >>> summary = get_latest_summary(collection)
        >>> if summary:
        ...     print(summary["document"])
    """
    try:
        # Get all summaries
        results = collection.get(
            where={"type": "summary"},
            include=["documents", "metadatas"]
        )
        
        if not results["ids"]:
            return None
        
        # Find the latest by date in metadata
        summaries = []
        for i, doc_id in enumerate(results["ids"]):
            metadata = results["metadatas"][i] if results["metadatas"] else {}
            summaries.append({
                "id": doc_id,
                "document": results["documents"][i] if results["documents"] else "",
                "metadata": metadata
            })
        
        # Sort by date (newest first)
        summaries.sort(
            key=lambda x: x["metadata"].get("date", ""),
            reverse=True
        )
        
        return summaries[0] if summaries else None
        
    except Exception as e:
        print(f"Error getting latest summary: {e}")
        return None


def get_summary_by_date(
    collection: Collection,
    date: str
) -> Optional[Dict[str, Any]]:
    """
    Get summary for a specific date.
    
    Args:
        collection: ChromaDB collection instance
        date: Date string in YYYY-MM-DD format
        
    Returns:
        dict or None: Summary data
        
    Example:
        >>> summary = get_summary_by_date(collection, "2024-01-15")
        >>> if summary:
        ...     print(summary["document"])
    """
    summary_id = f"summary_{date}"
    
    try:
        results = collection.get(
            ids=[summary_id],
            include=["documents", "metadatas"]
        )
        
        if not results["ids"]:
            return None
        
        return {
            "id": results["ids"][0],
            "document": results["documents"][0] if results["documents"] else "",
            "metadata": results["metadatas"][0] if results["metadatas"] else {}
        }
        
    except Exception as e:
        print(f"Error getting summary for {date}: {e}")
        return None


def get_summaries_range(
    collection: Collection,
    start_date: str,
    end_date: str
) -> List[Dict[str, Any]]:
    """
    Get summaries for a date range.
    
    Args:
        collection: ChromaDB collection instance
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        list: List of summary dictionaries
        
    Example:
        >>> summaries = get_summaries_range(collection, "2024-01-01", "2024-01-15")
        >>> print(f"Found {len(summaries)} summaries")
    """
    try:
        # Get all summaries
        results = collection.get(
            where={"type": "summary"},
            include=["documents", "metadatas"]
        )
        
        summaries = []
        for i, doc_id in enumerate(results["ids"]):
            metadata = results["metadatas"][i] if results["metadatas"] else {}
            summary_date = metadata.get("date", "")
            
            # Filter by date range
            if start_date <= summary_date <= end_date:
                summaries.append({
                    "id": doc_id,
                    "document": results["documents"][i] if results["documents"] else "",
                    "metadata": metadata
                })
        
        # Sort by date (newest first)
        summaries.sort(
            key=lambda x: x["metadata"].get("date", ""),
            reverse=True
        )
        
        return summaries
        
    except Exception as e:
        print(f"Error getting summaries: {e}")
        return []


def get_summary_sources(
    collection: Collection,
    date: str
) -> Optional[Dict[str, Any]]:
    """
    Get source tracking data for a specific summary.
    
    Returns the detailed breakdown of where each piece of content
    came from: platform → source → article.
    
    Args:
        collection: ChromaDB collection instance
        date: Date string in YYYY-MM-DD format
        
    Returns:
        dict or None: Source tracking data
        
    Example:
        >>> sources = get_summary_sources(collection, "2024-01-15")
        >>> if sources:
        ...     for platform, articles in sources.items():
        ...         print(f"{platform}: {len(articles)} articles")
    """
    summary = get_summary_by_date(collection, date)
    
    if not summary:
        return None
    
    sources_json = summary["metadata"].get("sources_json", "{}")
    
    try:
        return json.loads(sources_json)
    except json.JSONDecodeError:
        return None


# =============================================================================
# Newsletter Functions (for AI agent-generated newsletters)
# =============================================================================

def store_newsletter(
    collection: Collection,
    newsletter_id: str,
    newsletter_text: str,
    metadata: Dict[str, Any]
) -> bool:
    """
    Store an AI-generated newsletter in the collection.
    
    Newsletters are stored with a special "type": "newsletter" metadata field
    to distinguish them from articles and summaries.
    
    Args:
        collection: ChromaDB collection instance
        newsletter_id: Unique newsletter ID (e.g., "newsletter_2024-01-15")
        newsletter_text: Generated newsletter markdown text
        metadata: Newsletter metadata including:
            - date: Newsletter date (YYYY-MM-DD)
            - article_count: Number of articles in newsletter
            - new_stories_count: Count of new stories
            - updates_count: Count of updates
            - platforms: JSON string of platforms included
            - sources_json: JSON string of source tracking data
            - generated_at: ISO 8601 timestamp
            - model_used: LLM model name
            
    Returns:
        bool: True if successful
        
    Example:
        >>> store_newsletter(
        ...     collection,
        ...     "newsletter_2024-01-15",
        ...     "# Daily Newsletter\n...",
        ...     {"date": "2024-01-15", "article_count": 20}
        ... )
    """
    try:
        # Add type marker to distinguish from articles
        full_metadata = {"type": "newsletter", **metadata}
        
        collection.upsert(
            ids=[newsletter_id],
            documents=[newsletter_text],
            metadatas=[full_metadata]
        )
        return True
    except Exception as e:
        print(f"Error storing newsletter: {e}")
        return False


def get_latest_newsletter(collection: Collection) -> Optional[Dict[str, Any]]:
    """
    Get the most recent AI-generated newsletter.
    
    Args:
        collection: ChromaDB collection instance
        
    Returns:
        dict or None: Newsletter data with id, document, and metadata
        
    Example:
        >>> newsletter = get_latest_newsletter(collection)
        >>> if newsletter:
        ...     print(newsletter["document"])
    """
    try:
        # Get all newsletters
        results = collection.get(
            where={"type": "newsletter"},
            include=["documents", "metadatas"]
        )
        
        if not results["ids"]:
            return None
        
        # Find the latest by date in metadata
        newsletters = []
        for i, doc_id in enumerate(results["ids"]):
            metadata = results["metadatas"][i] if results["metadatas"] else {}
            newsletters.append({
                "id": doc_id,
                "document": results["documents"][i] if results["documents"] else "",
                "metadata": metadata
            })
        
        # Sort by date (newest first)
        newsletters.sort(
            key=lambda x: x["metadata"].get("date", ""),
            reverse=True
        )
        
        return newsletters[0] if newsletters else None
        
    except Exception as e:
        print(f"Error getting latest newsletter: {e}")
        return None


def get_newsletter_by_date(
    collection: Collection,
    date: str
) -> Optional[Dict[str, Any]]:
    """
    Get newsletter for a specific date.
    
    Args:
        collection: ChromaDB collection instance
        date: Date string in YYYY-MM-DD format
        
    Returns:
        dict or None: Newsletter data
        
    Example:
        >>> newsletter = get_newsletter_by_date(collection, "2024-01-15")
        >>> if newsletter:
        ...     print(newsletter["document"])
    """
    newsletter_id = f"newsletter_{date}"
    
    try:
        results = collection.get(
            ids=[newsletter_id],
            include=["documents", "metadatas"]
        )
        
        if not results["ids"]:
            return None
        
        return {
            "id": results["ids"][0],
            "document": results["documents"][0] if results["documents"] else "",
            "metadata": results["metadatas"][0] if results["metadatas"] else {}
        }
        
    except Exception as e:
        print(f"Error getting newsletter for {date}: {e}")
        return None


def get_newsletters_range(
    collection: Collection,
    start_date: str,
    end_date: str
) -> List[Dict[str, Any]]:
    """
    Get newsletters for a date range.
    
    Args:
        collection: ChromaDB collection instance
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        list: List of newsletter dictionaries
        
    Example:
        >>> newsletters = get_newsletters_range(collection, "2024-01-01", "2024-01-15")
        >>> print(f"Found {len(newsletters)} newsletters")
    """
    try:
        # Get all newsletters
        results = collection.get(
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
        
        # Sort by date (newest first)
        newsletters.sort(
            key=lambda x: x["metadata"].get("date", ""),
            reverse=True
        )
        
        return newsletters
        
    except Exception as e:
        print(f"Error getting newsletters: {e}")
        return []


def get_newsletter_sources(
    collection: Collection,
    date: str
) -> Optional[Dict[str, Any]]:
    """
    Get source tracking data for a specific newsletter.
    
    Returns the detailed breakdown of where each piece of content
    came from: platform → source → article.
    
    Args:
        collection: ChromaDB collection instance
        date: Date string in YYYY-MM-DD format
        
    Returns:
        dict or None: Source tracking data
        
    Example:
        >>> sources = get_newsletter_sources(collection, "2024-01-15")
        >>> if sources:
        ...     for platform, articles in sources.items():
        ...         print(f"{platform}: {len(articles)} articles")
    """
    newsletter = get_newsletter_by_date(collection, date)
    
    if not newsletter:
        return None
    
    sources_json = newsletter["metadata"].get("sources_json", "{}")
    
    try:
        return json.loads(sources_json)
    except json.JSONDecodeError:
        return None


def get_newsletter_updates(
    collection: Collection,
    date: str
) -> Optional[Dict[str, Any]]:
    """
    Get update tracking data for a specific newsletter.
    
    Returns information about stories that were updates to previous coverage.
    
    Args:
        collection: ChromaDB collection instance
        date: Date string in YYYY-MM-DD format
        
    Returns:
        dict or None: Update tracking data
        
    Example:
        >>> updates = get_newsletter_updates(collection, "2024-01-15")
        >>> if updates:
        ...     print(f"Found {len(updates)} updates")
    """
    newsletter = get_newsletter_by_date(collection, date)
    
    if not newsletter:
        return None
    
    updates_json = newsletter["metadata"].get("updates_json", "{}")
    
    try:
        return json.loads(updates_json)
    except json.JSONDecodeError:
        return None
