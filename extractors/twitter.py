import asyncio
from typing import List, Dict, Any
from .base import BaseExtractor

try:
    from twscrape import API, gather
except ImportError:
    API = None

class TwitterExtractor(BaseExtractor):
    def __init__(self):
        self.api = None
        if API:
            self.api = API() # twscrape uses a local accounts.db by default

    async def _extract_async(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        extracted_articles = []
        if not self.api:
            print("twscrape not installed or API initialization failed - skipping Twitter.")
            return []

        for source in sources:
            name = source.get("name")
            handle = source.get("handle")
            max_tweets = source.get("max_tweets", 5)
            
            if not handle:
                continue
                
            try:
                # Get user ID first
                user = await self.api.user_by_screen_name(handle)
                if not user:
                    print(f"Could not find Twitter user: {handle}")
                    continue
                
                # Fetch tweets
                tweets = await gather(self.api.user_tweets(user.id, limit=max_tweets))
                
                for tweet in tweets:
                    media_link = None
                    if tweet.media and tweet.media.photos:
                        media_link = tweet.media.photos[0].url
                    elif tweet.media and tweet.media.videos:
                        media_link = tweet.media.videos[0].thumbnail_url

                    extracted_articles.append({
                        "platform": "twitter",
                        "source_name": name,
                        "title": f"Tweet from {handle}",
                        "content_text": tweet.rawContent,
                        "url": tweet.url,
                        "timestamp": tweet.date.isoformat(),
                        "media_link": media_link
                    })
            except Exception as e:
                print(f"Error extracting from Twitter {handle}: {e}")
                
        return extracted_articles

    def extract(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Wrapper for async extraction."""
        try:
            return asyncio.run(self._extract_async(sources))
        except Exception as e:
            print(f"Twitter extraction loop failed: {e}")
            return []
