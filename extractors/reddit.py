import praw
from datetime import datetime
from typing import List, Dict, Any
from .base import BaseExtractor
from config import config

class RedditExtractor(BaseExtractor):
    def __init__(self):
        creds = config.reddit_creds
        # Check if creds are provided; if not, extract will return empty or skip
        self.reddit = None
        if all(creds.values()):
            try:
                self.reddit = praw.Reddit(
                    client_id=creds["client_id"],
                    client_secret=creds["client_secret"],
                    user_agent=creds["user_agent"],
                    username=creds["username"],
                    password=creds["password"]
                )
            except Exception as e:
                print(f"Failed to initialize Reddit PRAW: {e}")

    def extract(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        extracted_articles = []
        if not self.reddit:
            print("Reddit credentials missing - skipping Reddit extraction.")
            return []
            
        for source in sources:
            name = source.get("name")
            subreddit_name = source.get("subreddit")
            limit = source.get("limit", 5)
            sort = source.get("sort", "hot")
            
            if not subreddit_name:
                continue
                
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Dynamic call based on sort
                submissions = []
                if sort == "hot":
                    submissions = subreddit.hot(limit=limit)
                elif sort == "new":
                    submissions = subreddit.new(limit=limit)
                elif sort == "top":
                    submissions = subreddit.top(time_filter="day", limit=limit)
                
                for submission in submissions:
                    if submission.stickied:
                        continue
                        
                    # Extract timestamp
                    dt = datetime.fromtimestamp(submission.created_utc)
                    
                    extracted_articles.append({
                        "platform": "reddit",
                        "source_name": name,
                        "title": submission.title,
                        "content_text": submission.selftext[:5000], # Cap length
                        "url": f"https://www.reddit.com{submission.permalink}",
                        "timestamp": dt.isoformat(),
                        "media_link": submission.thumbnail if submission.thumbnail.startswith("http") else None
                    })
            except Exception as e:
                print(f"Error extracting from Reddit {subreddit_name}: {e}")
                
        return extracted_articles
