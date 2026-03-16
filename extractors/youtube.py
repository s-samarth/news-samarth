from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from typing import List, Dict, Any
from .base import BaseExtractor
from config import config

class YouTubeExtractor(BaseExtractor):
    def __init__(self):
        self.api_key = config.youtube_api_key
        self.youtube = None
        if self.api_key:
            try:
                self.youtube = build("youtube", "v3", developerKey=self.api_key)
            except Exception as e:
                print(f"Failed to initialize YouTube API: {e}")

    def extract(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
                continue
                
            try:
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
                    
                    content_text = snippet.get("description", "")
                    
                    if fetch_transcript:
                        try:
                            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                            transcript_text = " ".join([t["text"] for t in transcript_list])
                            content_text = transcript_text if transcript_text else content_text
                        except Exception:
                            # Silently fail transcript and keep description
                            pass
                    
                    extracted_articles.append({
                        "platform": "youtube",
                        "source_name": name,
                        "title": snippet.get("title"),
                        "content_text": content_text,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "timestamp": snippet.get("publishedAt"),
                        "media_link": snippet.get("thumbnails", {}).get("high", {}).get("url")
                    })
            except Exception as e:
                print(f"Error extracting from YouTube channel {channel_id}: {e}")
                
        return extracted_articles
