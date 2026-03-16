"""
Database module for Newsfeed Aggregator.

This module provides both legacy SQLite and new ChromaDB database backends.
ChromaDB is the recommended backend for AI-ready, NoSQL document storage.

Exports:
    # Legacy SQLite functions
    init_db: Initialize SQLite database schema
    upsert_articles: Insert/update articles in SQLite
    get_latest_articles: Query articles from SQLite
    
    # ChromaDB functions (recommended)
    get_chroma_client: Get ChromaDB client instance
    get_or_create_collection: Get/create newsfeed collection
    upsert_articles_chroma: Insert/update articles in ChromaDB
    get_articles: Query articles with filtering
    get_articles_last_24h: Get articles from last 24 hours
    get_platform_stats: Get article counts by platform
    search_articles: Semantic search (AI-ready)
    delete_old_articles: Cleanup old articles
"""

# Legacy SQLite exports (backward compatibility)
from .models import init_db, upsert_articles, get_latest_articles

# ChromaDB exports (new NoSQL backend)
from .chroma_db import (
    get_chroma_client,
    get_or_create_collection,
    upsert_articles as upsert_articles_chroma,
    get_articles,
    get_articles_last_24h,
    get_platform_stats,
    search_articles,
    delete_old_articles,
    # Summary functions
    store_summary,
    get_latest_summary,
    get_summary_by_date,
    get_summaries_range,
    get_summary_sources,
    # Newsletter functions
    store_newsletter,
    get_latest_newsletter,
    get_newsletter_by_date,
    get_newsletters_range,
    get_newsletter_sources,
    get_newsletter_updates
)

__all__ = [
    # Legacy SQLite
    "init_db",
    "upsert_articles",
    "get_latest_articles",
    # ChromaDB
    "get_chroma_client",
    "get_or_create_collection",
    "upsert_articles_chroma",
    "get_articles",
    "get_articles_last_24h",
    "get_platform_stats",
    "search_articles",
    "delete_old_articles",
    # Summary functions
    "store_summary",
    "get_latest_summary",
    "get_summary_by_date",
    "get_summaries_range",
    "get_summary_sources",
    # Newsletter functions
    "store_newsletter",
    "get_latest_newsletter",
    "get_newsletter_by_date",
    "get_newsletters_range",
    "get_newsletter_sources",
    "get_newsletter_updates"
]
