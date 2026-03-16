import logging
import sys
import os
from pathlib import Path

# Add root to path so we can import from extractors and db
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import config
from db import init_db
from extractors import SubstackExtractor, RedditExtractor, YouTubeExtractor, TwitterExtractor

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
    logger.info("Starting master newsfeed extraction...")
    
    # Ensure DB is initialized
    init_db()
    
    sources = config.sources
    
    # Map platforms to extractors
    platform_map = {
        "substack": SubstackExtractor(),
        "reddit": RedditExtractor(),
        "youtube": YouTubeExtractor(),
        "twitter": TwitterExtractor()
    }
    
    total_new = 0
    
    for platform, extractor in platform_map.items():
        platform_sources = sources.get(platform, [])
        if not platform_sources:
            logger.info(f"No sources configured for {platform}. Skipping.")
            continue
            
        try:
            logger.info(f"Running {platform} extractor...")
            new_count = extractor.run(platform_sources)
            logger.info(f"Finished {platform}: {new_count} new articles added.")
            total_new += new_count
        except Exception as e:
            logger.error(f"Platform {platform} failed with error: {e}")
            # Continue to next platform instead of crashing entire script
            continue
            
    logger.info(f"Master extraction complete. Total new articles: {total_new}")

if __name__ == "__main__":
    run_all()
