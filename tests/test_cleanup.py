"""
Tests for Database Cleanup Module
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call
from pathlib import Path

from db.cleanup import (
    run_cleanup,
    create_backup,
    list_backups,
    restore_backup,
    delete_article_by_url,
    delete_articles_by_urls,
    delete_articles_by_platform,
    get_cleanup_preview
)


class TestRunCleanup:
    """Tests for cleanup function."""
    
    def test_dry_run(self):
        """Test dry run mode doesn't delete anything."""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 100
        mock_collection.get.return_value = {
            "ids": ["id1", "id2"],
            "metadatas": [
                {"url": "https://example.com/1", "platform": "youtube", "timestamp": "2024-01-01T10:00:00", "title": "Old Article 1"},
                {"url": "https://example.com/2", "platform": "reddit", "timestamp": "2024-01-01T11:00:00", "title": "Old Article 2"}
            ]
        }
        
        result = run_cleanup(mock_collection, days_old=30, dry_run=True, backup=False)
        
        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["deleted_count"] == 2
        assert result["total_before"] == 100
        assert result["total_after"] == 100  # No actual deletion
        mock_collection.delete.assert_not_called()
    
    def test_actual_cleanup(self):
        """Test actual cleanup deletes articles."""
        mock_collection = MagicMock()
        mock_collection.count.side_effect = [100, 98]  # Before and after
        mock_collection.get.return_value = {
            "ids": ["id1", "id2"],
            "metadatas": [
                {"url": "https://example.com/1", "platform": "youtube", "timestamp": "2024-01-01T10:00:00", "title": "Old Article 1"},
                {"url": "https://example.com/2", "platform": "reddit", "timestamp": "2024-01-01T11:00:00", "title": "Old Article 2"}
            ]
        }
        
        with patch('db.cleanup.create_backup'):
            result = run_cleanup(mock_collection, days_old=30, dry_run=False, backup=True)
        
        assert result["success"] is True
        assert result["dry_run"] is False
        assert result["deleted_count"] == 2
        assert result["total_before"] == 100
        assert result["total_after"] == 98
        mock_collection.delete.assert_called_once()
    
    def test_no_old_articles(self):
        """Test cleanup when no old articles exist."""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 100
        mock_collection.get.return_value = {"ids": [], "metadatas": []}
        
        result = run_cleanup(mock_collection, days_old=30, dry_run=True, backup=False)
        
        assert result["success"] is True
        assert result["deleted_count"] == 0
        assert "No articles older" in result["message"]


class TestDeleteByUrl:
    """Tests for URL-based deletion functions."""
    
    def test_delete_single_article(self):
        """Test deleting a single article by URL."""
        mock_collection = MagicMock()
        mock_collection.get.return_value = {"ids": ["doc_id"]}
        
        result = delete_article_by_url(mock_collection, "https://example.com/article")
        
        assert result is True
        mock_collection.delete.assert_called_once()
    
    def test_delete_nonexistent_article(self):
        """Test deleting a non-existent article."""
        mock_collection = MagicMock()
        mock_collection.get.return_value = {"ids": []}
        
        result = delete_article_by_url(mock_collection, "https://example.com/nonexistent")
        
        assert result is False
        mock_collection.delete.assert_not_called()
    
    def test_delete_multiple_articles(self):
        """Test deleting multiple articles by URL."""
        mock_collection = MagicMock()
        mock_collection.get.return_value = {"ids": ["id1", "id2"]}
        
        urls = ["https://example.com/1", "https://example.com/2", "https://example.com/3"]
        result = delete_articles_by_urls(mock_collection, urls)
        
        assert result["https://example.com/1"] is True
        assert result["https://example.com/2"] is True
        assert result["https://example.com/3"] is False  # Not in existing_ids


class TestDeleteByPlatform:
    """Tests for platform-based deletion."""
    
    def test_delete_platform_articles(self):
        """Test deleting all articles from a platform."""
        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["id1", "id2", "id3"],
            "metadatas": [
                {"platform": "youtube"},
                {"platform": "youtube"},
                {"platform": "youtube"}
            ]
        }
        
        count = delete_articles_by_platform(mock_collection, "youtube")
        
        assert count == 3
        mock_collection.delete.assert_called_once_with(ids=["id1", "id2", "id3"])
    
    def test_delete_empty_platform(self):
        """Test deleting from platform with no articles."""
        mock_collection = MagicMock()
        mock_collection.get.return_value = {"ids": [], "metadatas": []}
        
        count = delete_articles_by_platform(mock_collection, "nonexistent")
        
        assert count == 0
        mock_collection.delete.assert_not_called()


class TestGetCleanupPreview:
    """Tests for cleanup preview function."""
    
    def test_preview(self):
        """Test cleanup preview."""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 100
        mock_collection.get.return_value = {
            "ids": ["id1"],
            "metadatas": [
                {"url": "https://example.com/1", "platform": "youtube", "timestamp": "2024-01-01T10:00:00", "title": "Old Article"}
            ]
        }
        
        result = get_cleanup_preview(mock_collection, days_old=30)
        
        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["deleted_count"] == 1