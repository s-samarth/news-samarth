"""
Base Extractor Module

Abstract base class for all platform extractors.
Defines the interface that all extractors must implement.

All extractors inherit from BaseExtractor and implement:
    - extract(): Fetch and transform content from a platform
    - run(): Extract and store to database (convenience method)

Example:
    >>> from extractors.base import BaseExtractor
    >>> class MyExtractor(BaseExtractor):
    ...     def extract(self, sources):
    ...         return [{"url": "...", "title": "...", ...}]
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from db.models import upsert_articles


class BaseExtractor(ABC):
    """
    Abstract base class for content extractors.
    
    All platform-specific extractors (YouTube, Reddit, etc.) inherit from this
    class and implement the extract() method.
    """
    
    @abstractmethod
    def extract(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract content from configured sources.
        
        This method must be implemented by all subclasses.
        Should return a list of article dictionaries with the following keys:
            - platform (str): Source platform name
            - source_name (str): Display name for the source
            - title (str): Article/post title
            - content_text (str): Full content (transcript, article, tweet, etc.)
            - url (str): Unique URL for the content
            - timestamp (str): Publication date in ISO 8601 format
            - media_link (str, optional): Image/thumbnail URL
            
        Args:
            sources: List of source configurations from sources.json
            
        Returns:
            List of article dictionaries
        """
        pass

    def run(self, sources: List[Dict[str, Any]]) -> int:
        """
        Extract content and store to database.
        
        Convenience method that calls extract() and then stores results
        to the database using upsert_articles.
        
        Args:
            sources: List of source configurations
            
        Returns:
            int: Number of new articles added to database
            
        Example:
            >>> extractor = YouTubeExtractor()
            >>> new_count = extractor.run(youtube_sources)
            >>> print(f"Added {new_count} new articles")
        """
        articles = self.extract(sources)
        return upsert_articles(articles)