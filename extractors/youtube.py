"""
YouTube Extractor Module (RSS-based)

Fetches video metadata and full transcripts from YouTube channels using RSS feeds.
Uses feedparser to parse YouTube RSS feeds and youtube-transcript-api for transcripts.

Features:
    - Fetches latest videos from configured channels via RSS feeds
    - Extracts full video transcripts when available
    - Falls back to video description if transcript unavailable
    - No API key required - uses native YouTube RSS feeds
    - Filters out YouTube Shorts (optional)

Example:
    >>> from extractors.youtube import YouTubeExtractor
    >>> extractor = YouTubeExtractor()
    >>> articles = extractor.extract([{"name": "Fireship", "channel_id": "UCsBjURrPoezykLs9EqgamOA"}])
"""

import feedparser
import re
from typing import List, Dict, Any, Optional

from .base import BaseExtractor


class YouTubeExtractor(BaseExtractor):
    """
    Extractor for YouTube video content via RSS feeds.
    
    Fetches video metadata and transcripts from YouTube channels using RSS feeds.
    No API key required - uses native YouTube RSS feeds.
    """
    
    def extract(self, sources: List[Dict[str, Any]], target_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extract videos and transcripts from YouTube channels via RSS feeds.

        For each configured channel, fetches the RSS feed and extracts
        video metadata and transcripts.

        Args:
            sources: List of channel configurations with keys:
                - name (str): Display name for the channel
                - channel_id (str): YouTube channel ID (required)
                - max_results (int): Max videos to fetch (default: 15)
                - fetch_transcript (bool): Whether to fetch transcripts (default: True)
                - filter_shorts (bool): Whether to filter out YouTube Shorts (default: True)
            target_date: Optional date string (YYYY-MM-DD) to filter videos by publication date

        Returns:
            List of article dictionaries with full content
        """
        extracted_articles = []

        for source in sources:
            name = source.get("name")
            channel_id = source.get("channel_id")
            # Fetch more when targeting a specific date to increase chances of finding matches
            default_max = 50 if target_date else 15
            max_results = source.get("max_results", default_max) if not target_date else max(source.get("max_results", 15), 50)
            fetch_transcript = source.get("fetch_transcript", True)
            filter_shorts = source.get("filter_shorts", True)

            if not channel_id:
                print(f"Warning: No channel_id provided for source '{name}', skipping.")
                continue

            try:
                articles = self._extract_channel(name, channel_id, max_results, fetch_transcript, filter_shorts)
                extracted_articles.extend(articles)
            except Exception as e:
                print(f"Error extracting from YouTube channel {channel_id}: {e}")

        return self._filter_by_date(extracted_articles, target_date)
    
    def _extract_channel(
        self,
        name: str,
        channel_id: str,
        max_results: int,
        fetch_transcript: bool,
        filter_shorts: bool
    ) -> List[Dict[str, Any]]:
        """
        Extract videos from a single YouTube channel via RSS feed.
        
        Args:
            name: Display name for the channel
            channel_id: YouTube channel ID
            max_results: Maximum number of videos to fetch
            fetch_transcript: Whether to attempt transcript extraction
            filter_shorts: Whether to filter out YouTube Shorts
            
        Returns:
            List of article dictionaries
        """
        articles = []
        
        # Build RSS feed URL
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        
        # Parse RSS feed
        feed = feedparser.parse(rss_url)
        
        if not feed.entries:
            print(f"No videos found for channel {name} ({channel_id})")
            return articles
        
        # Limit entries
        entries = feed.entries[:max_results]
        
        for entry in entries:
            # Extract video ID from link
            video_id = self._extract_video_id(entry.get("link", ""))
            
            if not video_id:
                continue
            
            # Filter out YouTube Shorts if requested
            if filter_shorts and self._is_short(entry):
                continue
            
            # Start with video description as fallback
            content_text = entry.get("summary", "")
            
            # Attempt to fetch full transcript
            if fetch_transcript:
                transcript = self._fetch_transcript(video_id)
                if transcript:
                    content_text = transcript
            
            # Extract thumbnail
            media_link = self._extract_thumbnail(entry)
            
            articles.append({
                "platform": "youtube",
                "source_name": name,
                "title": entry.get("title", ""),
                "content_text": content_text,
                "url": entry.get("link", ""),
                "timestamp": entry.get("published", ""),
                "media_link": media_link
            })
            
        return articles
    
    def _extract_video_id(self, url: str) -> str:
        """
        Extract video ID from YouTube URL.
        
        Args:
            url: YouTube video URL
            
        Returns:
            Video ID or empty string if not found
        """
        # Match patterns like: https://www.youtube.com/watch?v=VIDEO_ID
        # or: https://youtu.be/VIDEO_ID
        patterns = [
            r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'youtu\.be/([a-zA-Z0-9_-]+)',
            r'youtube\.com/embed/([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return ""
    
    def _is_short(self, entry) -> bool:
        """
        Check if a video is a YouTube Short.
        
        YouTube Shorts are typically under 60 seconds and have specific URL patterns.
        
        Args:
            entry: feedparser entry object
            
        Returns:
            True if the video is a Short, False otherwise
        """
        # Check URL for /shorts/ pattern
        link = entry.get("link", "")
        if "/shorts/" in link:
            return True
        
        # Check title for common Short indicators
        title = entry.get("title", "").lower()
        short_indicators = ["#shorts", "#short", "shorts"]
        for indicator in short_indicators:
            if indicator in title:
                return True
        
        return False
    
    def _fetch_transcript(self, video_id: str) -> str:
        """
        Fetch the full transcript for a YouTube video.
        
        Uses youtube-transcript-api to retrieve the complete transcript.
        Returns empty string if transcript is unavailable.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Full transcript text, or empty string if unavailable
        """
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            # Join all transcript segments into a single string
            transcript_text = " ".join([t["text"] for t in transcript_list])
            return transcript_text if transcript_text else ""
        except Exception:
            # Transcript not available (disabled, language not supported, etc.)
            return ""
    
    def _extract_thumbnail(self, entry) -> str:
        """
        Extract thumbnail image URL from RSS entry.
        
        Checks multiple possible locations for thumbnail:
        - media_thumbnail field
        - media_content field
        
        Args:
            entry: feedparser entry object
            
        Returns:
            Thumbnail URL or None
        """
        # Check media_thumbnail field
        if "media_thumbnail" in entry and entry.media_thumbnail:
            return entry.media_thumbnail[0].get("url")
        
        # Check media_content field
        if "media_content" in entry and entry.media_content:
            for media in entry.media_content:
                if "image" in media.get("type", ""):
                    return media.get("url")
        
        return None
