"""
Reddit Extractor Module

Fetches posts and content from Reddit subreddits using PRAW (Python Reddit API Wrapper).
Stores full post content including self-text for AI/analysis purposes.

Features:
    - Fetches posts from configured subreddits
    - Supports multiple sort options (hot, new, top)
    - Stores complete post body text
    - Optionally includes top comments
    - Skips stickied posts

Example:
    >>> from extractors.reddit import RedditExtractor
    >>> extractor = RedditExtractor()
    >>> articles = extractor.extract([{"name": "r/LocalLLaMA", "subreddit": "LocalLLaMA", "limit": 5}])
"""

import praw
from datetime import datetime
from typing import List, Dict, Any

from .base import BaseExtractor
from config import config


class RedditExtractor(BaseExtractor):
    """
    Extractor for Reddit subreddit content.
    
    Fetches posts from Reddit using PRAW with authenticated access.
    Requires Reddit API credentials configured in .env file.
    """
    
    def __init__(self):
        """
        Initialize the Reddit extractor with API credentials.
        
        Sets up PRAW client using credentials from config.
        If credentials are missing, extraction will return empty results.
        """
        creds = config.reddit_creds
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
        """
        Extract posts from configured subreddits.
        
        For each configured subreddit, fetches posts based on sort order
        and stores the full post content.
        
        Args:
            sources: List of subreddit configurations with keys:
                - name (str): Display name for the source
                - subreddit (str): Subreddit name (required)
                - limit (int): Max posts to fetch (default: 5)
                - sort (str): Sort order - "hot", "new", "top" (default: "hot")
                - include_comments (bool): Include top comments (default: False)
                
        Returns:
            List of article dictionaries with full content:
            - platform: "reddit"
            - source_name: Display name
            - title: Post title
            - content_text: Full post body + optional comments
            - url: Reddit permalink
            - timestamp: Publication date (ISO 8601)
            - media_link: Thumbnail URL (if valid)
        """
        extracted_articles = []
        
        if not self.reddit:
            print("Reddit credentials missing - skipping Reddit extraction.")
            return []
            
        for source in sources:
            name = source.get("name")
            subreddit_name = source.get("subreddit")
            limit = source.get("limit", 5)
            sort = source.get("sort", "hot")
            include_comments = source.get("include_comments", False)
            
            if not subreddit_name:
                print(f"Warning: No subreddit provided for source '{name}', skipping.")
                continue
                
            try:
                articles = self._extract_subreddit(
                    name, subreddit_name, limit, sort, include_comments
                )
                extracted_articles.extend(articles)
            except Exception as e:
                print(f"Error extracting from Reddit r/{subreddit_name}: {e}")
                
        return extracted_articles
    
    def _extract_subreddit(
        self,
        name: str,
        subreddit_name: str,
        limit: int,
        sort: str,
        include_comments: bool
    ) -> List[Dict[str, Any]]:
        """
        Extract posts from a single subreddit.
        
        Args:
            name: Display name for the source
            subreddit_name: Subreddit name
            limit: Maximum posts to fetch
            sort: Sort order
            include_comments: Whether to include top comments
            
        Returns:
            List of article dictionaries
        """
        articles = []
        subreddit = self.reddit.subreddit(subreddit_name)
        
        # Get submissions based on sort order
        submissions = self._get_submissions(subreddit, sort, limit)
        
        for submission in submissions:
            # Skip stickied posts (usually announcements)
            if submission.stickied:
                continue
            
            # Build full content text
            content_text = self._build_content(submission, include_comments)
            
            # Extract timestamp
            dt = datetime.fromtimestamp(submission.created_utc)
            
            # Validate thumbnail URL
            thumbnail = submission.thumbnail
            media_link = thumbnail if thumbnail and thumbnail.startswith("http") else None
            
            articles.append({
                "platform": "reddit",
                "source_name": name,
                "title": submission.title,
                "content_text": content_text,
                "url": f"https://www.reddit.com{submission.permalink}",
                "timestamp": dt.isoformat(),
                "media_link": media_link
            })
            
        return articles
    
    def _get_submissions(self, subreddit, sort: str, limit: int):
        """
        Get submissions from subreddit based on sort order.
        
        Args:
            subreddit: PRAW subreddit object
            sort: Sort order ("hot", "new", "top")
            limit: Maximum number of submissions
            
        Returns:
            List of PRAW submission objects
        """
        if sort == "hot":
            return subreddit.hot(limit=limit)
        elif sort == "new":
            return subreddit.new(limit=limit)
        elif sort == "top":
            return subreddit.top(time_filter="day", limit=limit)
        else:
            # Default to hot
            return subreddit.hot(limit=limit)
    
    def _build_content(self, submission, include_comments: bool) -> str:
        """
        Build full content text from submission.
        
        Combines post body (selftext) with optional top comments
        for comprehensive content storage.
        
        Args:
            submission: PRAW submission object
            include_comments: Whether to include top comments
            
        Returns:
            Full content text
        """
        parts = []
        
        # Add post body (selftext)
        if submission.selftext:
            # Cap at 10000 chars to prevent excessive storage
            parts.append(submission.selftext[:10000])
        
        # Optionally add top comments
        if include_comments:
            submission.comments.replace_more(limit=0)  # Flatten comment tree
            top_comments = submission.comments[:5]  # Top 5 comments
            
            if top_comments:
                parts.append("\n\n--- Top Comments ---\n")
                for i, comment in enumerate(top_comments, 1):
                    if hasattr(comment, 'body'):
                        parts.append(f"\n{i}. {comment.body[:500]}")
        
        return "\n".join(parts) if parts else submission.title