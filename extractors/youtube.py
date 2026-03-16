"""
YouTube Extractor Module

Fetches video metadata and full transcripts from YouTube channels.
Uses the YouTube Data API v3 for video listings and youtube-transcript-api
for transcript extraction.

Features:
    - Fetches latest videos from configured channels
    - Extracts full video transcripts when available
    - Falls back to video description if transcript unavailable
    - Stores complete content for AI/analysis purposes

Example:
    >>> from extractors.youtube import YouTubeExtractor
    >>> extractor = YouTubeExtractor()
    >>> articles = extractor.extract([{"name": "Fireship", "channel_id": "UCsBjURrPoezykLs9EqgamOA"}])
"""

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from typing import List, Dict, Any

from .base import BaseExtractor
from config import config


class YouTubeExtractor(BaseExtractor):
    """
    Extractor for YouTube video content.
    
    Fetches video metadata and transcripts from YouTube channels.
    Requires a valid YouTube Data API v3 key.
    """
    
    def __init__(self):
        """
        Initialize the YouTube extractor with API credentials.
        
        Sets up the YouTube API client using the API key from config.
        If no API key is configured, extraction will return empty results.
        """
        self.api_key = config.youtube_api_key
        self.youtube = None
        if self.api_key:
            try:
                self.youtube = build("youtube", "v3", developerKey=self.api_key)
            except Exception as e:
                print(f"Failed to initialize YouTube API: {e}")

    def extract(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract videos and transcripts from YouTube channels.
        
        For each configured channel, fetches the latest videos and attempts
        to retrieve full transcripts. Falls back to video description if
        transcript is unavailable.
        
        Args:
            sources: List of channel configurations with keys:
                - name (str): Display name for the channel
                - channel_id (str): YouTube channel ID (required)
                - max_results (int): Max videos to fetch (default: 3)
                - fetch_transcript (bool): Whether to fetch transcripts (default: True)
                
        Returns:
            List of article dictionaries with full content:
            - platform: "youtube"
            - source_name: Channel display name
            - title: Video title
            - content_text: Full transcript or description
            - url: Video URL
            - timestamp: Publication date (ISO 8601)
            - media_link: Thumbnail URL
        """
        extracted_articles = []
        
        if not self.youtube:
            print("YouTube API key missing - skipping YouTube extraction.")
            return []
            
        for source in sources:
            name = source.get("name")
            channel_id = source.get("channel_id")
            max_results = source.get("max_results", 3)
            fetch_transcript = source.get("fetch_transcript", True)
            
            if not channel_id:
                print(f"Warning: No channel_id provided for source '{name}', skipping.")
                continue
                
            try:
                articles = self._extract_channel(name, channel_id, max_results, fetch_transcript)
                extracted_articles.extend(articles)
            except Exception as e:
                print(f"Error extracting from YouTube channel {channel_id}: {e}")
                
        return extracted_articles
    
    def _extract_channel(
        self,
        name: str,
        channel_id: str,
        max_results: int,
        fetch_transcript: bool
    ) -> List[Dict[str, Any]]:
        """
        Extract videos from a single YouTube channel.
        
        Args:
            name: Display name for the channel
            channel_id: YouTube channel ID
            max_results: Maximum number of videos to fetch
            fetch_transcript: Whether to attempt transcript extraction
            
        Returns:
            List of article dictionaries
        """
        articles = []
        
        # Get latest videos from channel
        request = self.youtube.search().list(
            part="snippet",
            channelId=channel_id,
            maxResults=max_results,
            order="date",
            type="video"
        )
        response = request.execute()
        
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]
            
            # Start with video description as fallback
            content_text = snippet.get("description", "")
            
            # Attempt to fetch full transcript
            if fetch_transcript:
                transcript = self._fetch_transcript(video_id)
                if transcript:
                    content_text = transcript
            
            articles.append({
                "platform": "youtube",
                "source_name": name,
                "title": snippet.get("title"),
                "content_text": content_text,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "timestamp": snippet.get("publishedAt"),
                "media_link": snippet.get("thumbnails", {}).get("high", {}).get("url")
            })
            
        return articles
    
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
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            # Join all transcript segments into a single string
            transcript_text = " ".join([t["text"] for t in transcript_list])
            return transcript_text if transcript_text else ""
        except Exception:
            # Transcript not available (disabled, language not supported, etc.)
            return ""