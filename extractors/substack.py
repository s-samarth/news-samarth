"""
Substack Extractor Module

Fetches newsletter content from Substack publications via RSS feeds.
Uses feedparser to parse RSS/Atom feeds and extracts full article content.

Features:
    - Fetches articles from Substack RSS feeds
    - Extracts full newsletter HTML/text content
    - Strips HTML tags for clean text storage
    - Extracts thumbnail images when available
    - Handles both content and summary fields

Example:
    >>> from extractors.substack import SubstackExtractor
    >>> extractor = SubstackExtractor()
    >>> articles = extractor.extract([{"name": "Stratechery", "rss_url": "https://stratechery.com/feed"}])
"""

import feedparser
import re
from typing import List, Dict, Any

from .base import BaseExtractor


class SubstackExtractor(BaseExtractor):
    """
    Extractor for Substack newsletter content.
    
    Fetches articles from Substack RSS feeds without requiring API keys.
    Extracts full article content for storage and analysis.
    """
    
    def extract(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract articles from Substack RSS feeds.
        
        For each configured Substack publication, fetches the RSS feed
        and extracts full article content.
        
        Args:
            sources: List of Substack configurations with keys:
                - name (str): Display name for the publication
                - rss_url (str): RSS feed URL (required)
                
        Returns:
            List of article dictionaries with full content:
            - platform: "substack"
            - source_name: Publication name
            - title: Article title
            - content_text: Full article text (HTML stripped)
            - url: Article URL
            - timestamp: Publication date
            - media_link: Thumbnail image URL (if available)
        """
        extracted_articles = []
        
        for source in sources:
            name = source.get("name")
            url = source.get("rss_url")
            
            if not url:
                print(f"Warning: No RSS URL provided for source '{name}', skipping.")
                continue
                
            try:
                articles = self._extract_feed(name, url)
                extracted_articles.extend(articles)
            except Exception as e:
                print(f"Error extracting from Substack {name}: {e}")
                
        return extracted_articles
    
    def _extract_feed(self, name: str, rss_url: str) -> List[Dict[str, Any]]:
        """
        Extract articles from a single RSS feed.
        
        Args:
            name: Publication display name
            rss_url: RSS feed URL
            
        Returns:
            List of article dictionaries
        """
        articles = []
        feed = feedparser.parse(rss_url)
        
        for entry in feed.entries:
            # Extract full content
            content = self._extract_content(entry)
            
            # Extract thumbnail
            media_link = self._extract_thumbnail(entry)
            
            articles.append({
                "platform": "substack",
                "source_name": name,
                "title": entry.get("title"),
                "content_text": content,
                "url": entry.get("link"),
                "timestamp": entry.get("published", ""),
                "media_link": media_link
            })
            
        return articles
    
    def _extract_content(self, entry) -> str:
        """
        Extract full article content from RSS entry.
        
        Tries content field first (full article), then falls back to summary.
        Strips HTML tags for clean text storage.
        
        Args:
            entry: feedparser entry object
            
        Returns:
            Clean article text
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
        
        return content
    
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