"""
Twitter/X Extractor Module

Fetches tweets from Twitter/X user timelines using twscrape library.
Stores full tweet content for AI/analysis purposes.

Features:
    - Fetches recent tweets from configured user handles
    - Stores complete tweet text (no truncation)
    - Extracts media URLs (photos/videos)
    - Uses twscrape for unofficial API access (no official API key needed)
    - Async implementation for efficient fetching

Setup:
    Before using, add Twitter accounts to twscrape:
    $ twscrape add_accounts accounts.txt
    $ twscrape login_accounts

Example:
    >>> from extractors.twitter import TwitterExtractor
    >>> extractor = TwitterExtractor()
    >>> articles = extractor.extract([{"name": "@elonmusk", "handle": "elonmusk", "max_tweets": 5}])
"""

import asyncio
from typing import List, Dict, Any

from .base import BaseExtractor

try:
    from twscrape import API, gather
except ImportError:
    API = None


class TwitterExtractor(BaseExtractor):
    """
    Extractor for Twitter/X content.
    
    Fetches tweets from user timelines using twscrape library.
    Requires twscrape to be installed and configured with accounts.
    """
    
    def __init__(self):
        """
        Initialize the Twitter extractor.
        
        Sets up twscrape API client. If twscrape is not installed,
        extraction will return empty results.
        """
        self.api = None
        if API:
            try:
                self.api = API()  # twscrape uses a local accounts.db by default
            except Exception as e:
                print(f"Failed to initialize Twitter API: {e}")

    def extract(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract tweets from configured user handles.
        
        This is a synchronous wrapper around the async extraction method.
        
        Args:
            sources: List of Twitter configurations with keys:
                - name (str): Display name for the source
                - handle (str): Twitter handle without @ (required)
                - max_tweets (int): Max tweets to fetch (default: 5)
                
        Returns:
            List of article dictionaries with full content:
            - platform: "twitter"
            - source_name: Display name
            - title: "Tweet from @{handle}"
            - content_text: Full tweet text
            - url: Tweet URL
            - timestamp: Publication date (ISO 8601)
            - media_link: Media URL (photo/video thumbnail)
        """
        try:
            return asyncio.run(self._extract_async(sources))
        except Exception as e:
            print(f"Twitter extraction failed: {e}")
            return []

    async def _extract_async(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Async implementation of tweet extraction.
        
        Args:
            sources: List of Twitter configurations
            
        Returns:
            List of article dictionaries
        """
        extracted_articles = []
        
        if not self.api:
            print("twscrape not installed or API initialization failed - skipping Twitter.")
            return []

        for source in sources:
            name = source.get("name")
            handle = source.get("handle")
            max_tweets = source.get("max_tweets", 5)
            
            if not handle:
                print(f"Warning: No handle provided for source '{name}', skipping.")
                continue
                
            try:
                articles = await self._extract_user(name, handle, max_tweets)
                extracted_articles.extend(articles)
            except Exception as e:
                print(f"Error extracting from Twitter @{handle}: {e}")
                
        return extracted_articles
    
    async def _extract_user(
        self,
        name: str,
        handle: str,
        max_tweets: int
    ) -> List[Dict[str, Any]]:
        """
        Extract tweets from a single user.
        
        Args:
            name: Display name for the source
            handle: Twitter handle (without @)
            max_tweets: Maximum tweets to fetch
            
        Returns:
            List of article dictionaries
        """
        articles = []
        
        # Get user ID first
        user = await self.api.user_by_screen_name(handle)
        if not user:
            print(f"Could not find Twitter user: @{handle}")
            return articles
        
        # Fetch tweets
        tweets = await gather(self.api.user_tweets(user.id, limit=max_tweets))
        
        for tweet in tweets:
            # Extract media URL
            media_link = self._extract_media(tweet)
            
            articles.append({
                "platform": "twitter",
                "source_name": name,
                "title": f"Tweet from @{handle}",
                "content_text": tweet.rawContent,  # Full tweet text
                "url": tweet.url,
                "timestamp": tweet.date.isoformat(),
                "media_link": media_link
            })
            
        return articles
    
    def _extract_media(self, tweet) -> str:
        """
        Extract media URL from tweet.
        
        Prioritizes photos over videos.
        
        Args:
            tweet: twscrape tweet object
            
        Returns:
            Media URL or None
        """
        if not tweet.media:
            return None
            
        # Check for photos first
        if tweet.media.photos:
            return tweet.media.photos[0].url
            
        # Fall back to video thumbnail
        if tweet.media.videos:
            return tweet.media.videos[0].thumbnail_url
            
        return None