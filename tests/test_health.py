"""
Tests for Database Health Check Module
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from db.health import validate_article, check_database_integrity, scan_for_issues, get_database_stats


class TestValidateArticle:
    """Tests for article validation function."""
    
    def test_valid_article(self):
        """Test that a valid article passes validation."""
        article = {
            "url": "https://example.com/article",
            "platform": "youtube",
            "source_name": "TestChannel",
            "title": "Test Article",
            "content_text": "Some content",
            "timestamp": "2024-01-15T10:00:00"
        }
        issues = validate_article(article)
        assert issues == []
    
    def test_missing_url(self):
        """Test that missing URL is detected."""
        article = {
            "platform": "youtube",
            "source_name": "TestChannel",
            "title": "Test Article"
        }
        issues = validate_article(article)
        assert any("url" in issue.lower() for issue in issues)
    
    def test_missing_platform(self):
        """Test that missing platform is detected."""
        article = {
            "url": "https://example.com/article",
            "source_name": "TestChannel",
            "title": "Test Article"
        }
        issues = validate_article(article)
        assert any("platform" in issue.lower() for issue in issues)
    
    def test_invalid_url_format(self):
        """Test that invalid URL format is detected."""
        article = {
            "url": "not-a-valid-url",
            "platform": "youtube",
            "source_name": "TestChannel",
            "title": "Test Article"
        }
        issues = validate_article(article)
        assert any("url" in issue.lower() for issue in issues)
    
    def test_invalid_timestamp(self):
        """Test that invalid timestamp is detected."""
        article = {
            "url": "https://example.com/article",
            "platform": "youtube",
            "source_name": "TestChannel",
            "title": "Test Article",
            "timestamp": "not-a-date"
        }
        issues = validate_article(article)
        assert any("timestamp" in issue.lower() for issue in issues)
    
    def test_future_timestamp(self):
        """Test that future timestamp is detected."""
        future_date = (datetime.now() + timedelta(days=30)).isoformat()
        article = {
            "url": "https://example.com/article",
            "platform": "youtube",
            "source_name": "TestChannel",
            "title": "Test Article",
            "timestamp": future_date
        }
        issues = validate_article(article)
        assert any("future" in issue.lower() for issue in issues)
    
    def test_empty_content_and_title(self):
        """Test that empty content and title is detected."""
        article = {
            "url": "https://example.com/article",
            "platform": "youtube",
            "source_name": "TestChannel",
            "title": "",
            "content_text": ""
        }
        issues = validate_article(article)
        assert any("empty" in issue.lower() for issue in issues)
    
    def test_unknown_platform(self):
        """Test that unknown platform is detected."""
        article = {
            "url": "https://example.com/article",
            "platform": "unknown_platform",
            "source_name": "TestChannel",
            "title": "Test Article"
        }
        issues = validate_article(article)
        assert any("platform" in issue.lower() for issue in issues)


class TestCheckDatabaseIntegrity:
    """Tests for database integrity check function."""
    
    def test_empty_database(self):
        """Test integrity check on empty database."""
        mock_collection = MagicMock()
        mock_collection.get.return_value = {"ids": [], "metadatas": []}
        
        result = check_database_integrity(mock_collection)
        
        assert result["status"] == "empty"
        assert result["article_count"] == 0
    
    def test_healthy_database(self):
        """Test integrity check on healthy database."""
        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["id1", "id2"],
            "metadatas": [
                {"platform": "youtube", "url": "https://example.com/1", "timestamp": "2024-01-15T10:00:00"},
                {"platform": "reddit", "url": "https://example.com/2", "timestamp": "2024-01-15T11:00:00"}
            ]
        }
        
        result = check_database_integrity(mock_collection)
        
        assert result["status"] == "healthy"
        assert result["article_count"] == 2
        assert result["platforms"]["youtube"] == 1
        assert result["platforms"]["reddit"] == 1
    
    def test_duplicate_detection(self):
        """Test that duplicate URLs are detected."""
        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["id1", "id2"],
            "metadatas": [
                {"platform": "youtube", "url": "https://example.com/same", "timestamp": "2024-01-15T10:00:00"},
                {"platform": "youtube", "url": "https://example.com/same", "timestamp": "2024-01-15T11:00:00"}
            ]
        }
        
        result = check_database_integrity(mock_collection)
        
        assert result["status"] == "warning"
        assert "duplicate" in result["warnings"][0].lower()


class TestScanForIssues:
    """Tests for issue scanning function."""
    
    def test_scan_valid_articles(self):
        """Test scanning valid articles."""
        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["id1"],
            "documents": ["Some content"],
            "metadatas": [
                {"platform": "youtube", "url": "https://example.com/1", "source_name": "Test", "timestamp": "2024-01-15T10:00:00"}
            ]
        }
        
        result = scan_for_issues(mock_collection, sample_size=10)
        
        assert result["total_scanned"] == 1
        assert result["valid_count"] == 1
        assert result["invalid_count"] == 0
    
    def test_scan_invalid_articles(self):
        """Test scanning invalid articles."""
        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["id1"],
            "documents": [""],
            "metadatas": [
                {"platform": "youtube", "url": "", "source_name": "Test", "timestamp": "invalid"}
            ]
        }
        
        result = scan_for_issues(mock_collection, sample_size=10)
        
        assert result["total_scanned"] == 1
        assert result["valid_count"] == 0
        assert result["invalid_count"] == 1


class TestGetDatabaseStats:
    """Tests for database statistics function."""
    
    def test_get_stats(self):
        """Test getting database statistics."""
        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["id1", "id2", "id3"],
            "documents": ["Content 1", "Content 2", ""],
            "metadatas": [
                {"platform": "youtube", "type": "article", "timestamp": "2024-01-15T10:00:00"},
                {"platform": "reddit", "type": "article", "timestamp": "2024-01-15T11:00:00"},
                {"platform": "youtube", "type": "summary", "timestamp": "2024-01-15T12:00:00"}
            ]
        }
        
        stats = get_database_stats(mock_collection)
        
        assert stats["total_articles"] == 3
        assert stats["by_platform"]["youtube"] == 2
        assert stats["by_platform"]["reddit"] == 1
        assert stats["by_type"]["article"] == 2
        assert stats["by_type"]["summary"] == 1
        assert stats["content_stats"]["empty_content_count"] == 1