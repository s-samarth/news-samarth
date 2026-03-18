import argparse
import sys
from pathlib import Path

# Add root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import config
from db import init_db
from extractors import SubstackExtractor, RedditExtractor, YouTubeExtractor, TwitterPlaywrightExtractor

def main():
    parser = argparse.ArgumentParser(description="Run a single newsfeed extractor.")
    parser.add_argument("--platform", required=True, choices=["substack", "reddit", "youtube", "twitter"],
                        help="Platform to scrape")
    args = parser.parse_args()
    
    init_db()
    
    platform_map = {
        "substack": SubstackExtractor(),
        "reddit": RedditExtractor(),
        "youtube": YouTubeExtractor(),
        "twitter": TwitterPlaywrightExtractor()
    }
    
    extractor = platform_map[args.platform]
    sources = config.sources.get(args.platform, [])
    
    if not sources:
        print(f"No sources for {args.platform}")
        return
        
    print(f"Running {args.platform} extractor...")
    new_count = extractor.run(sources)
    print(f"Done. Added {new_count} new articles.")

if __name__ == "__main__":
    main()
