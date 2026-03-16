import feedparser
import re
from typing import List, Dict, Any
from .base import BaseExtractor

class SubstackExtractor(BaseExtractor):
    def extract(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        extracted_articles = []
        
        for source in sources:
            name = source.get("name")
            url = source.get("rss_url")
            
            if not url:
                continue
                
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    content = ""
                    if hasattr(entry, "content"):
                        content = entry.content[0].value
                    elif hasattr(entry, "summary"):
                        content = entry.summary
                    
                    # Basic HTML stripping
                    content_clean = re.sub('<[^<]+?>', '', content)
                    
                    # Try to find a thumbnail
                    media_link = None
                    if "media_thumbnail" in entry and len(entry.media_thumbnail) > 0:
                        media_link = entry.media_thumbnail[0]["url"]
                    elif "links" in entry:
                        # Sometimes image is in enclosure links
                        for link in entry.links:
                            if "image" in link.get("type", ""):
                                media_link = link.get("href")
                                break

                    extracted_articles.append({
                        "platform": "substack",
                        "source_name": name,
                        "title": entry.get("title"),
                        "content_text": content_clean,
                        "url": entry.get("link"),
                        "timestamp": entry.get("published", ""),
                        "media_link": media_link
                    })
            except Exception as e:
                # Log error here in a real scenario
                print(f"Error extracting from Substack {name}: {e}")
                
        return extracted_articles
