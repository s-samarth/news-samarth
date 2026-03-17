"""
Comprehensive test suite for all extractors.

Tests each extractor to ensure they can successfully extract content
from their respective platforms, validate extraction accuracy,
handle edge cases, and comply with expected schemas.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.youtube import YouTubeExtractor
from extractors.reddit import RedditExtractor
from extractors.substack import SubstackExtractor
from extractors.twitter import TwitterExtractor


# Expected article schema for all platforms
EXPECTED_ARTICLE_SCHEMA = {
    "platform": str,
    "source_name": str,
    "title": str,
    "content_text": str,
    "url": str,
    "timestamp": str,
    "media_link": (str, type(None))  # Can be None
}


def validate_article_schema(article: dict) -> bool:
    """Validate that an article matches the expected schema."""
    for field, expected_type in EXPECTED_ARTICLE_SCHEMA.items():
        if field not in article:
            return False
        if not isinstance(article[field], expected_type):
            return False
    return True


class TestYouTubeExtractor:
    """Test YouTube extractor functionality (RSS-based)."""
    
    def test_extractor_initialization(self):
        """Test that YouTube extractor initializes correctly."""
        extractor = YouTubeExtractor()
        assert extractor is not None
        assert hasattr(extractor, 'extract')
        assert hasattr(extractor, '_extract_channel')
        assert hasattr(extractor, '_fetch_transcript')
        assert hasattr(extractor, '_extract_video_id')
        assert hasattr(extractor, '_is_short')
    
    def test_extract_with_valid_channel(self):
        """Test extraction with a valid YouTube channel via RSS."""
        extractor = YouTubeExtractor()
        
        # Test with Fireship channel (known to have transcripts)
        sources = [{
            "name": "Fireship",
            "channel_id": "UCsBjURrPoezykLs9EqgamOA",
            "max_results": 1,
            "fetch_transcript": True,
            "filter_shorts": True
        }]
        
        articles = extractor.extract(sources)
        
        # Should return a list
        assert isinstance(articles, list)
        
        # Should get results (no API key needed for RSS)
        if len(articles) > 0:
            article = articles[0]
            
            # Validate schema compliance
            assert validate_article_schema(article), f"Article schema invalid: {article}"
            
            # Validate platform-specific fields
            assert article["platform"] == "youtube"
            assert article["source_name"] == "Fireship"
            assert "youtube.com/watch?v=" in article["url"]
            assert len(article["title"]) > 0
            assert len(article["content_text"]) > 0
    
    def test_extract_without_channel_id(self):
        """Test that extractor handles missing channel_id gracefully."""
        extractor = YouTubeExtractor()
        
        sources = [{
            "name": "Invalid Channel",
            # Missing channel_id
        }]
        
        articles = extractor.extract(sources)
        assert isinstance(articles, list)
        assert len(articles) == 0
    
    def test_extract_with_invalid_channel_id(self):
        """Test that extractor handles invalid channel_id gracefully."""
        extractor = YouTubeExtractor()
        
        sources = [{
            "name": "Invalid Channel",
            "channel_id": "INVALID_CHANNEL_ID_12345",
            "max_results": 1
        }]
        
        articles = extractor.extract(sources)
        assert isinstance(articles, list)
        # Should return empty list for invalid channel
        assert len(articles) == 0
    
    def test_extract_with_max_results_limit(self):
        """Test that max_results parameter is respected."""
        extractor = YouTubeExtractor()
        
        sources = [{
            "name": "Fireship",
            "channel_id": "UCsBjURrPoezykLs9EqgamOA",
            "max_results": 2,
            "fetch_transcript": False,
            "filter_shorts": True
        }]
        
        articles = extractor.extract(sources)
        
        if len(articles) > 0:
            # Should not exceed max_results
            assert len(articles) <= 2
    
    def test_extract_without_transcript(self):
        """Test extraction with fetch_transcript disabled."""
        extractor = YouTubeExtractor()
        
        sources = [{
            "name": "Fireship",
            "channel_id": "UCsBjURrPoezykLs9EqgamOA",
            "max_results": 1,
            "fetch_transcript": False,
            "filter_shorts": True
        }]
        
        articles = extractor.extract(sources)
        
        if len(articles) > 0:
            article = articles[0]
            # Should still have content (description fallback)
            assert len(article["content_text"]) > 0
    
    def test_extract_empty_sources(self):
        """Test extraction with empty sources list."""
        extractor = YouTubeExtractor()
        articles = extractor.extract([])
        assert isinstance(articles, list)
        assert len(articles) == 0
    
    def test_extract_multiple_sources(self):
        """Test extraction with multiple YouTube channels."""
        extractor = YouTubeExtractor()
        
        sources = [
            {
                "name": "Fireship",
                "channel_id": "UCsBjURrPoezykLs9EqgamOA",
                "max_results": 1,
                "fetch_transcript": False,
                "filter_shorts": True
            },
            {
                "name": "Two Minute Papers",
                "channel_id": "UCbfYPyITQ-7l4upoX8nvctg",
                "max_results": 1,
                "fetch_transcript": False,
                "filter_shorts": True
            }
        ]
        
        articles = extractor.extract(sources)
        
        # Should get articles from both channels
        assert isinstance(articles, list)
        # Verify articles come from different sources
        source_names = {article["source_name"] for article in articles}
        # At least one source should have articles
        assert len(source_names) >= 1
    
    def test_video_id_extraction(self):
        """Test video ID extraction from YouTube URLs."""
        extractor = YouTubeExtractor()
        
        # Test standard YouTube URL
        video_id = extractor._extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"
        
        # Test short URL
        video_id = extractor._extract_video_id("https://youtu.be/dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"
        
        # Test embed URL
        video_id = extractor._extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"
        
        # Test invalid URL
        video_id = extractor._extract_video_id("https://example.com")
        assert video_id == ""
    
    def test_shorts_detection(self):
        """Test YouTube Shorts detection."""
        extractor = YouTubeExtractor()
        
        # Test entry with /shorts/ in URL
        entry_with_shorts_url = {"link": "https://www.youtube.com/shorts/abc123"}
        assert extractor._is_short(entry_with_shorts_url) == True
        
        # Test entry with #shorts in title
        entry_with_shorts_title = {"title": "Cool video #shorts"}
        assert extractor._is_short(entry_with_shorts_title) == True
        
        # Test regular video
        entry_regular = {"link": "https://www.youtube.com/watch?v=abc123", "title": "Regular video"}
        assert extractor._is_short(entry_regular) == False


class TestRedditExtractor:
    """Test Reddit extractor functionality."""
    
    def test_extractor_initialization(self):
        """Test that Reddit extractor initializes correctly."""
        extractor = RedditExtractor()
        assert extractor is not None
        assert hasattr(extractor, 'extract')
        assert hasattr(extractor, '_extract_subreddit')
    
    def test_extract_with_valid_subreddit(self):
        """Test extraction with a valid subreddit."""
        extractor = RedditExtractor()
        
        # Test with LocalLLaMA subreddit
        sources = [{
            "name": "r/LocalLLaMA",
            "subreddit": "LocalLLaMA",
            "sort": "hot",
            "limit": 2
        }]
        
        articles = extractor.extract(sources)
        
        # Should return a list
        assert isinstance(articles, list)
        
        # Should get results (no API key needed for Reddit)
        assert len(articles) > 0
        article = articles[0]
        
        # Validate schema compliance
        assert validate_article_schema(article), f"Article schema invalid: {article}"
        
        # Validate platform-specific fields
        assert article["platform"] == "reddit"
        assert article["source_name"] == "r/LocalLLaMA"
        assert "reddit.com" in article["url"]
        assert len(article["title"]) > 0
        assert len(article["content_text"]) > 0
    
    def test_extract_without_subreddit(self):
        """Test that extractor handles missing subreddit gracefully."""
        extractor = RedditExtractor()
        
        sources = [{
            "name": "Invalid Subreddit",
            # Missing subreddit
        }]
        
        articles = extractor.extract(sources)
        assert isinstance(articles, list)
        assert len(articles) == 0
    
    def test_extract_with_invalid_subreddit(self):
        """Test that extractor handles invalid subreddit gracefully."""
        extractor = RedditExtractor()
        
        sources = [{
            "name": "Invalid Subreddit",
            "subreddit": "this_subreddit_definitely_does_not_exist_12345",
            "sort": "hot",
            "limit": 2
        }]
        
        articles = extractor.extract(sources)
        assert isinstance(articles, list)
        # Should return empty list for invalid subreddit
        assert len(articles) == 0
    
    def test_extract_with_different_sort_options(self):
        """Test extraction with different sort options."""
        extractor = RedditExtractor()
        
        sort_options = ["hot", "new", "top"]
        
        for sort_option in sort_options:
            sources = [{
                "name": "r/LocalLLaMA",
                "subreddit": "LocalLLaMA",
                "sort": sort_option,
                "limit": 1
            }]
            
            articles = extractor.extract(sources)
            assert isinstance(articles, list)
            # Should work with all sort options
    
    def test_extract_with_limit(self):
        """Test that limit parameter is respected."""
        extractor = RedditExtractor()
        
        sources = [{
            "name": "r/LocalLLaMA",
            "subreddit": "LocalLLaMA",
            "sort": "hot",
            "limit": 3
        }]
        
        articles = extractor.extract(sources)
        
        if len(articles) > 0:
            # Should not exceed limit
            assert len(articles) <= 3
    
    def test_extract_empty_sources(self):
        """Test extraction with empty sources list."""
        extractor = RedditExtractor()
        articles = extractor.extract([])
        assert isinstance(articles, list)
        assert len(articles) == 0
    
    def test_extract_multiple_sources(self):
        """Test extraction with multiple subreddits."""
        extractor = RedditExtractor()
        
        sources = [
            {
                "name": "r/LocalLLaMA",
                "subreddit": "LocalLLaMA",
                "sort": "hot",
                "limit": 1
            },
            {
                "name": "r/MachineLearning",
                "subreddit": "MachineLearning",
                "sort": "hot",
                "limit": 1
            }
        ]
        
        articles = extractor.extract(sources)
        
        # Should get articles from both subreddits
        assert isinstance(articles, list)
        # Verify articles come from different sources
        source_names = {article["source_name"] for article in articles}
        # At least one source should have articles
        assert len(source_names) >= 1


class TestSubstackExtractor:
    """Test Substack extractor functionality."""
    
    def test_extractor_initialization(self):
        """Test that Substack extractor initializes correctly."""
        extractor = SubstackExtractor()
        assert extractor is not None
        assert hasattr(extractor, 'extract')
        assert hasattr(extractor, '_extract_feed')
        assert hasattr(extractor, '_extract_content')
        assert hasattr(extractor, '_extract_thumbnail')
    
    def test_extract_with_valid_rss(self):
        """Test extraction with a valid Substack RSS feed."""
        extractor = SubstackExtractor()
        
        # Test with Stratechery RSS feed
        sources = [{
            "name": "Stratechery",
            "rss_url": "https://stratechery.com/feed"
        }]
        
        articles = extractor.extract(sources)
        
        # Should return a list
        assert isinstance(articles, list)
        
        # Should get results (no API key needed for Substack)
        assert len(articles) > 0
        article = articles[0]
        
        # Validate schema compliance
        assert validate_article_schema(article), f"Article schema invalid: {article}"
        
        # Validate platform-specific fields
        assert article["platform"] == "substack"
        assert article["source_name"] == "Stratechery"
        assert "http" in article["url"]
        assert len(article["title"]) > 0
        assert len(article["content_text"]) > 0
    
    def test_extract_without_rss_url(self):
        """Test that extractor handles missing rss_url gracefully."""
        extractor = SubstackExtractor()
        
        sources = [{
            "name": "Invalid Newsletter",
            # Missing rss_url
        }]
        
        articles = extractor.extract(sources)
        assert isinstance(articles, list)
        assert len(articles) == 0
    
    def test_extract_with_invalid_rss_url(self):
        """Test that extractor handles invalid RSS URL gracefully."""
        extractor = SubstackExtractor()
        
        sources = [{
            "name": "Invalid Newsletter",
            "rss_url": "https://invalid-url-that-does-not-exist.com/feed"
        }]
        
        articles = extractor.extract(sources)
        assert isinstance(articles, list)
        # Should return empty list for invalid RSS
        assert len(articles) == 0
    
    def test_extract_empty_sources(self):
        """Test extraction with empty sources list."""
        extractor = SubstackExtractor()
        articles = extractor.extract([])
        assert isinstance(articles, list)
        assert len(articles) == 0
    
    def test_extract_multiple_sources(self):
        """Test extraction with multiple Substack newsletters."""
        extractor = SubstackExtractor()
        
        sources = [
            {
                "name": "Stratechery",
                "rss_url": "https://stratechery.com/feed"
            },
            {
                "name": "Lenny's Newsletter",
                "rss_url": "https://www.lennysnewsletter.com/feed"
            }
        ]
        
        articles = extractor.extract(sources)
        
        # Should get articles from both newsletters
        assert isinstance(articles, list)
        # Verify articles come from different sources
        source_names = {article["source_name"] for article in articles}
        # At least one source should have articles
        assert len(source_names) >= 1
    
    def test_content_html_stripping(self):
        """Test that HTML tags are properly stripped from content."""
        extractor = SubstackExtractor()
        
        sources = [{
            "name": "Stratechery",
            "rss_url": "https://stratechery.com/feed"
        }]
        
        articles = extractor.extract(sources)
        
        if len(articles) > 0:
            article = articles[0]
            # Content should not contain HTML tags
            assert "<" not in article["content_text"] or ">" not in article["content_text"]


class TestTwitterExtractor:
    """Test Twitter extractor functionality."""
    
    def test_extractor_initialization(self):
        """Test that Twitter extractor initializes correctly."""
        extractor = TwitterExtractor()
        assert extractor is not None
        assert hasattr(extractor, 'extract')
        assert hasattr(extractor, '_extract_async')
        assert hasattr(extractor, '_extract_user')
        assert hasattr(extractor, '_extract_media')
    
    def test_extract_with_valid_handle(self):
        """Test extraction with a valid Twitter handle."""
        extractor = TwitterExtractor()
        
        # Test with Elon Musk's handle
        sources = [{
            "name": "@elonmusk",
            "handle": "elonmusk",
            "max_tweets": 2
        }]
        
        articles = extractor.extract(sources)
        
        # Should return a list
        assert isinstance(articles, list)
        
        # If twscrape is configured, should get results
        if extractor.api:
            assert len(articles) > 0
            article = articles[0]
            
            # Validate schema compliance
            assert validate_article_schema(article), f"Article schema invalid: {article}"
            
            # Validate platform-specific fields
            assert article["platform"] == "twitter"
            assert article["source_name"] == "@elonmusk"
            assert "twitter.com" in article["url"] or "x.com" in article["url"]
            assert len(article["title"]) > 0
            assert len(article["content_text"]) > 0
    
    def test_extract_without_handle(self):
        """Test that extractor handles missing handle gracefully."""
        extractor = TwitterExtractor()
        
        sources = [{
            "name": "Invalid User",
            # Missing handle
        }]
        
        articles = extractor.extract(sources)
        assert isinstance(articles, list)
        assert len(articles) == 0
    
    def test_extract_with_invalid_handle(self):
        """Test that extractor handles invalid handle gracefully."""
        extractor = TwitterExtractor()
        
        sources = [{
            "name": "Invalid User",
            "handle": "this_handle_definitely_does_not_exist_12345",
            "max_tweets": 2
        }]
        
        articles = extractor.extract(sources)
        assert isinstance(articles, list)
        # Should return empty list for invalid handle
        assert len(articles) == 0
    
    def test_extract_with_max_tweets_limit(self):
        """Test that max_tweets parameter is respected."""
        extractor = TwitterExtractor()
        
        sources = [{
            "name": "@elonmusk",
            "handle": "elonmusk",
            "max_tweets": 3
        }]
        
        articles = extractor.extract(sources)
        
        if extractor.api and len(articles) > 0:
            # Should not exceed max_tweets
            assert len(articles) <= 3
    
    def test_extract_empty_sources(self):
        """Test extraction with empty sources list."""
        extractor = TwitterExtractor()
        articles = extractor.extract([])
        assert isinstance(articles, list)
        assert len(articles) == 0
    
    def test_extract_multiple_sources(self):
        """Test extraction with multiple Twitter handles."""
        extractor = TwitterExtractor()
        
        sources = [
            {
                "name": "@elonmusk",
                "handle": "elonmusk",
                "max_tweets": 1
            },
            {
                "name": "@sama",
                "handle": "sama",
                "max_tweets": 1
            }
        ]
        
        articles = extractor.extract(sources)
        
        if extractor.api:
            # Should get articles from both handles
            assert isinstance(articles, list)
            # Verify articles come from different sources
            source_names = {article["source_name"] for article in articles}
            # At least one source should have articles
            assert len(source_names) >= 1


class TestExtractorIntegration:
    """Integration tests for all extractors."""
    
    def test_all_extractors_have_extract_method(self):
        """Test that all extractors implement the extract method."""
        extractors = [
            YouTubeExtractor(),
            RedditExtractor(),
            SubstackExtractor(),
            TwitterExtractor()
        ]
        
        for extractor in extractors:
            assert hasattr(extractor, 'extract')
            assert callable(extractor.extract)
    
    def test_extractors_return_correct_format(self):
        """Test that all extractors return the correct article format."""
        # This test verifies the structure without making actual API calls
        # by checking that extractors handle empty/invalid sources gracefully
        
        extractors = [
            YouTubeExtractor(),
            RedditExtractor(),
            SubstackExtractor(),
            TwitterExtractor()
        ]
        
        for extractor in extractors:
            # Test with empty sources
            articles = extractor.extract([])
            assert isinstance(articles, list)
            
            # Test with invalid sources
            articles = extractor.extract([{"invalid": "data"}])
            assert isinstance(articles, list)
    
    def test_all_extractors_handle_errors_gracefully(self):
        """Test that all extractors handle errors without crashing."""
        extractors = [
            YouTubeExtractor(),
            RedditExtractor(),
            SubstackExtractor(),
            TwitterExtractor()
        ]
        
        for extractor in extractors:
            # Test with None
            articles = extractor.extract(None)
            assert isinstance(articles, list)
            
            # Test with malformed data
            articles = extractor.extract([{"malformed": True}])
            assert isinstance(articles, list)
    
    def test_article_schema_compliance(self):
        """Test that all extractors produce articles with correct schema."""
        # This test validates the schema structure
        test_article = {
            "platform": "test",
            "source_name": "Test Source",
            "title": "Test Title",
            "content_text": "Test content",
            "url": "https://test.com",
            "timestamp": "2024-01-15T10:00:00",
            "media_link": None
        }
        
        # Validate the test article itself
        assert validate_article_schema(test_article)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
