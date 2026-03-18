"""
Master Extraction Script

Orchestrates content extraction from all configured platforms and stores
results in the ChromaDB database. This is the main entry point for
running the newsfeed aggregation pipeline.

Usage:
    python scripts/run_all.py
    
    Or with specific platform:
    python scripts/run_single.py --platform youtube

Features:
    - Runs all platform extractors (Substack, Reddit, YouTube, Twitter)
    - Stores full content in ChromaDB (NoSQL, AI-ready)
    - Continues on individual platform failures
    - Logs all activity to logs/extractor.log
    - Provides summary of new articles added

Architecture:
    sources.json → Extractors → ChromaDB (db/chroma_db/)
"""

import logging
import sys
from pathlib import Path

# Add root to path so we can import from extractors and db
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import config
from db.chroma_db import get_chroma_client, get_or_create_collection, upsert_articles
from extractors import SubstackExtractor, RedditExtractor, YouTubeExtractor, TwitterPlaywrightExtractor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(config.log_dir / "extractor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_all():
    """
    Run extraction for all configured platforms.
    
    This is the main orchestration function that:
    1. Initializes ChromaDB connection
    2. Loads sources from sources.json
    3. Runs each platform extractor
    4. Stores results in ChromaDB
    5. Logs summary statistics
    
    Returns:
        int: Total number of new articles added across all platforms
    """
    logger.info("=" * 60)
    logger.info("Starting master newsfeed extraction...")
    logger.info(f"Database location: {config.chroma_path}")
    logger.info("=" * 60)
    
    # Initialize ChromaDB
    client = get_chroma_client()
    collection = get_or_create_collection(client)
    
    initial_count = collection.count()
    logger.info(f"Current database contains {initial_count} articles")
    
    sources = config.sources
    
    # Map platforms to extractors
    platform_map = {
        "substack": SubstackExtractor(),
        "reddit": RedditExtractor(),
        "youtube": YouTubeExtractor(),
        "twitter": TwitterPlaywrightExtractor()
    }
    
    total_new = 0
    platform_stats = {}
    
    for platform, extractor in platform_map.items():
        platform_sources = sources.get(platform, [])
        if not platform_sources:
            logger.info(f"No sources configured for {platform}. Skipping.")
            continue
            
        try:
            logger.info(f"Running {platform} extractor...")
            articles = extractor.extract(platform_sources)
            
            if articles:
                new_count = upsert_articles(collection, articles)
                logger.info(f"Finished {platform}: {len(articles)} fetched, {new_count} new articles added.")
                total_new += new_count
                platform_stats[platform] = {"fetched": len(articles), "new": new_count}
            else:
                logger.info(f"Finished {platform}: No articles fetched.")
                platform_stats[platform] = {"fetched": 0, "new": 0}
                
        except Exception as e:
            logger.error(f"Platform {platform} failed with error: {e}")
            platform_stats[platform] = {"error": str(e)}
            # Continue to next platform instead of crashing entire script
            continue
    
    # Final summary
    final_count = collection.count()
    logger.info("=" * 60)
    logger.info("EXTRACTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Starting articles: {initial_count}")
    logger.info(f"Ending articles: {final_count}")
    logger.info(f"New articles added: {total_new}")
    logger.info("")
    logger.info("Platform breakdown:")
    for platform, stats in platform_stats.items():
        if "error" in stats:
            logger.info(f"  {platform}: FAILED - {stats['error']}")
        else:
            logger.info(f"  {platform}: {stats['fetched']} fetched, {stats['new']} new")
    logger.info("=" * 60)
    
    return total_new


if __name__ == "__main__":
    run_all()