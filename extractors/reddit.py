"""
Reddit Extractor Module (RSS-based)

Fetches posts from Reddit subreddits using RSS feeds.
Uses feedparser to parse RSS feeds and extracts full post content.

Features:
    - Fetches posts from configured subreddit RSS feeds
    - No API credentials required
    - Stores complete post body text
    - Handles both www.reddit.com and old.reddit.com URLs
    - Automatic fallback to old.reddit.com if blocked

Example:
    >>> from extractors.reddit import RedditExtractor
    >>> extractor = RedditExtractor()
    >>> articles = extractor.extract([{
    ...     "name": "r/LocalLLaMA",
    ...     "rss_url": "https://www.reddit.com/r/LocalLLaMA/.rss",
    ...     "limit": 5
    ... }])
"""

import feedparser
import re
from typing import List, Dict, Any, Optional

from .base import BaseExtractor


class RedditExtractor(BaseExtractor):
    """
    Extractor for Reddit subreddit content via RSS feeds.
    
    Fetches posts from Reddit using RSS feeds without requiring API credentials.
    Uses feedparser (same as Substack extractor) for consistency.
    """
    
    # Sort option to RSS URL path mapping
    SORT_URL_MAP = {
        "hot": "",
        "new": "new/",
        "top": "top/.rss?t=day",
        "rising": "rising/",
    }

    def _build_rss_url(self, source: Dict[str, Any]) -> Optional[str]:
        """
        Build RSS URL from source config, supporting both rss_url and subreddit+sort fields.

        Args:
            source: Source configuration dict

        Returns:
            RSS URL string, or None if insufficient config
        """
        rss_url = source.get("rss_url")
        if rss_url:
            return rss_url

        subreddit = source.get("subreddit")
        if not subreddit:
            return None

        sort = source.get("sort", "hot")
        sort_path = self.SORT_URL_MAP.get(sort, "")

        if sort == "top":
            return f"https://www.reddit.com/r/{subreddit}/{sort_path}"
        else:
            return f"https://www.reddit.com/r/{subreddit}/{sort_path}.rss"

    def extract(self, sources: List[Dict[str, Any]], target_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extract posts from configured subreddit RSS feeds.

        For each configured subreddit, fetches posts and stores the full post content.

        Args:
            sources: List of subreddit configurations with keys:
                - name (str): Display name for the source
                - rss_url (str): RSS feed URL (option 1)
                - subreddit (str): Subreddit name (option 2, used with sort)
                - sort (str): Sort order - hot/new/top/rising (default: hot)
                - limit (int): Max posts to fetch (default: 10)
            target_date: Optional date string (YYYY-MM-DD) to filter posts by publication date

        Returns:
            List of article dictionaries with full content
        """
        extracted_articles = []

        for source in sources:
            name = source.get("name")
            rss_url = self._build_rss_url(source)
            # Fetch more when targeting a specific date
            default_limit = 25 if target_date else 10
            limit = source.get("limit", default_limit) if not target_date else max(source.get("limit", 10), 25)

            if not rss_url:
                print(f"Warning: No RSS URL or subreddit provided for source '{name}', skipping.")
                continue

            try:
                articles = self._extract_feed(name, rss_url, limit)
                extracted_articles.extend(articles)
            except Exception as e:
                print(f"Error extracting from Reddit {name}: {e}")
                # Try fallback to old.reddit.com
                if "www.reddit.com" in rss_url:
                    fallback_url = rss_url.replace("www.reddit.com", "old.reddit.com")
                    print(f"Trying fallback: {fallback_url}")
                    try:
                        articles = self._extract_feed(name, fallback_url, limit)
                        extracted_articles.extend(articles)
                    except Exception as e2:
                        print(f"Fallback also failed: {e2}")

        return self._filter_by_date(extracted_articles, target_date)
    
    def _extract_feed(self, name: str, rss_url: str, limit: int) -> List[Dict[str, Any]]:
        """
        Extract posts from a single RSS feed.
        
        Args:
            name: Display name for the source
            rss_url: RSS feed URL
            limit: Maximum posts to fetch
            
        Returns:
            List of article dictionaries
        """
        articles = []
        feed = feedparser.parse(rss_url)
        
        # Limit entries
        entries = feed.entries[:limit]
        
        for entry in entries:
            # Extract full content
            content = self._extract_content(entry)
            
            # Extract thumbnail
            media_link = self._extract_thumbnail(entry)
            
            # Extract timestamp
            timestamp = entry.get("published", "")
            
            articles.append({
                "platform": "reddit",
                "source_name": name,
                "title": entry.get("title"),
                "content_text": content,
                "url": entry.get("link"),
                "timestamp": timestamp,
                "media_link": media_link
            })
            
        return articles
    
    def _extract_content(self, entry) -> str:
        """
        Extract full post content from RSS entry.
        
        Tries content field first (full post), then falls back to summary.
        Strips HTML tags for clean text storage.
        
        Args:
            entry: feedparser entry object
            
        Returns:
            Clean post text
        """
        content = ""
        
        # Try full content first
        if hasattr(entry, "content") and entry.content:
            content = entry.content[0].value
        # Fall back to summary
        elif hasattr(entry, "summary"):
            content = entry.summary
        
        # Strip HTML tags for clean text
        if content:
            content = re.sub(r'<[^<]+?>', '', content)
            # Clean up extra whitespace
            content = re.sub(r'\n\s*\n', '\n\n', content)
            content = content.strip()
        
        return content if content else entry.get("title", "")
    
    def _extract_thumbnail(self, entry) -> str:
        """
        Extract thumbnail image URL from RSS entry.
        
        Checks multiple possible locations for thumbnail:
        - media_thumbnail field
        - enclosure links with image type
        
        Args:
            entry: feedparser entry object
            
        Returns:
            Thumbnail URL or None
        """
        # Check media_thumbnail field
        if "media_thumbnail" in entry and entry.media_thumbnail:
            return entry.media_thumbnail[0].get("url")
        
        # Check enclosure links
        if "links" in entry:
            for link in entry.links:
                if "image" in link.get("type", ""):
                    return link.get("href")
        
        return None
