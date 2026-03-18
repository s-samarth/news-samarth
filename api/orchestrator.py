"""
Newsletter Orchestration Module

Coordinates the two-phase newsletter generation flow:
1. Fetch phase: Run extractors for a target date, store in ChromaDB, report per-platform status
2. Generate phase: Check for existing newsletter, generate if missing

This module sits between the API endpoints and the extractors/AI pipeline.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple

from config import config
from db.timezone_utils import get_today, get_now
from db.chroma_db import (
    get_chroma_client,
    get_or_create_collection,
    upsert_articles,
    get_newsletter_by_date,
    get_articles_by_fetch_date,
)
from extractors import (
    SubstackExtractor,
    RedditExtractor,
    YouTubeExtractor,
    TwitterPlaywrightExtractor,
)

logger = logging.getLogger(__name__)


def validate_date(date_str: str) -> Tuple[bool, str]:
    """
    Validate that date_str is YYYY-MM-DD format and within the last 30 days (inclusive of today).

    Uses configured timezone for "today" calculation.

    Returns:
        (is_valid, error_message) — error_message is empty when valid.
    """
    try:
        target = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return False, f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD."

    today = get_today()
    oldest_allowed = today - timedelta(days=30)

    if target > today:
        return False, f"Date {date_str} is in the future."
    if target < oldest_allowed:
        return False, f"Date {date_str} is older than 30 days. Only the last 30 days are supported."

    return True, ""


def fetch_for_date(target_date: str) -> Dict[str, Any]:
    """
    Run all extractors for *target_date*, store results in ChromaDB, and
    return per-platform fetch status.

    Returns a dict shaped like:
        {
            "date": "2026-03-18",
            "overall_status": "success" | "partial" | "failed",
            "platforms": {
                "youtube":  {"status": "success", "count": 12},
                "reddit":   {"status": "failed",  "count": 0, "error": "..."},
                ...
            },
            "total_articles": 25
        }
    """
    # Validate first
    valid, err = validate_date(target_date)
    if not valid:
        return {"date": target_date, "overall_status": "failed", "error": err, "platforms": {}, "total_articles": 0}

    client = get_chroma_client()
    collection = get_or_create_collection(client)
    sources = config.sources

    platform_extractors = {
        "youtube": YouTubeExtractor(),
        "reddit": RedditExtractor(),
        "substack": SubstackExtractor(),
    }

    # Twitter extractor may fail to initialise if credentials are missing
    try:
        platform_extractors["twitter"] = TwitterPlaywrightExtractor()
    except Exception as e:
        logger.warning(f"Twitter extractor init failed: {e}")

    platform_status: Dict[str, Dict[str, Any]] = {}
    total_articles = 0

    for platform, extractor in platform_extractors.items():
        platform_sources = sources.get(platform, [])
        if not platform_sources:
            platform_status[platform] = {"status": "success", "count": 0, "note": "No sources configured"}
            continue

        try:
            articles = extractor.extract(platform_sources, target_date=target_date)
            count = 0
            if articles:
                count = upsert_articles(collection, articles, fetch_date=target_date)
            platform_status[platform] = {"status": "success", "count": count}
            total_articles += count
        except Exception as e:
            logger.error(f"Platform {platform} failed: {e}")
            platform_status[platform] = {"status": "failed", "count": 0, "error": str(e)}

    # Handle twitter separately if it wasn't initialised
    if "twitter" not in platform_extractors:
        platform_status["twitter"] = {
            "status": "failed",
            "count": 0,
            "error": "Twitter credentials not configured",
        }

    # Determine overall status
    statuses = [p["status"] for p in platform_status.values()]
    if all(s == "success" for s in statuses):
        overall = "success"
    elif all(s == "failed" for s in statuses):
        overall = "failed"
    else:
        overall = "partial"

    return {
        "date": target_date,
        "overall_status": overall,
        "platforms": platform_status,
        "total_articles": total_articles,
    }


def generate_for_date(target_date: str, force: bool = False) -> Dict[str, Any]:
    """
    Generate a newsletter for *target_date*.

    If a newsletter already exists and *force* is False, returns the cached version.
    Otherwise runs the AI pipeline.

    Returns:
        Dict with keys: success, id, date, newsletter, metadata, sources, cached
    """
    valid, err = validate_date(target_date)
    if not valid:
        return {"success": False, "error": err}

    client = get_chroma_client()
    collection = get_or_create_collection(client)

    # Check for existing newsletter
    if not force:
        existing = get_newsletter_by_date(collection, target_date)
        if existing:
            import json
            sources_json = existing["metadata"].get("sources_json", "{}")
            try:
                sources = json.loads(sources_json)
            except json.JSONDecodeError:
                sources = {}

            return {
                "success": True,
                "cached": True,
                "id": existing["id"],
                "date": target_date,
                "newsletter": existing["document"],
                "metadata": {
                    "date": existing["metadata"].get("date"),
                    "article_count": existing["metadata"].get("article_count", 0),
                    "new_stories_count": existing["metadata"].get("new_stories_count", 0),
                    "updates_count": existing["metadata"].get("updates_count", 0),
                    "platforms": json.loads(existing["metadata"].get("platforms", "[]")),
                    "generated_at": existing["metadata"].get("generated_at"),
                    "model_used": existing["metadata"].get("model_used"),
                },
                "sources": sources,
            }

    # Generate new newsletter
    try:
        from ai.newsletter import generate_newsletter

        result = generate_newsletter(target_date=target_date)
        return {
            "success": True,
            "cached": False,
            "id": result["id"],
            "date": result["date"],
            "newsletter": result["newsletter"],
            "metadata": result["metadata"],
            "sources": result["sources"],
        }
    except Exception as e:
        logger.error(f"Newsletter generation failed: {e}")
        return {"success": False, "error": str(e)}
