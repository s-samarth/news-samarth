"""
Tests for Backup and Restore Functions
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import tarfile

from db.cleanup import create_backup, list_backups, restore_backup


class TestCreateBackup:
    """Tests for backup creation."""
    
    @patch('db.cleanup.tarfile.open')
    @patch('db.cleanup.config')
    def test_create_backup(self, mock_config, mock_tarfile):
        """Test creating a backup."""
        mock_config.chroma_path = Path("/fake/chroma_db")
        mock_config.backup_dir = Path("/fake/backups")
        
        with patch.object(Path, 'mkdir'):
            with patch.object(Path, 'exists', return_value=True):
                result = create_backup()
        
        assert result.name.startswith("chroma_backup_")
        assert result.name.endswith(".tar.gz")
        mock_tarfile.assert_called_once()
    
    @patch('db.cleanup.config')
    def test_create_backup_creates_directory(self, mock_config):
        """Test that backup creates directory if it doesn't exist."""
        mock_config.chroma_path = Path("/fake/chroma_db")
        mock_config.backup_dir = Path("/fake/backups")
        
        with patch.object(Path, 'mkdir') as mock_mkdir:
            with patch('db.cleanup.tarfile.open'):
                create_backup()
        
        mock_mkdir.assert_called_with(parents=True, exist_ok=True)


class TestListBackups:
    """Tests for listing backups."""
    
    @patch('db.cleanup.config')
    def test_list_empty_backups(self, mock_config):
        """Test listing when no backups exist."""
        mock_config.backup_dir = Path("/fake/backups")
        
        with patch.object(Path, 'exists', return_value=False):
            result = list_backups()
        
        assert result == []
    
    @patch('db.cleanup.config')
    def test_list_backups(self, mock_config):
        """Test listing existing backups."""
        mock_config.backup_dir = Path("/fake/backups")
        
        mock_backup1 = MagicMock()
        mock_backup1.name = "chroma_backup_20240115_100000.tar.gz"
        mock_backup1.stat.return_value = MagicMock(
            st_size=1024 * 1024,  # 1 MB
            st_ctime=datetime(2024, 1, 15, 10, 0, 0).timestamp(),
            st_mtime=datetime(2024, 1, 15, 10, 0, 0).timestamp()
        )
        
        mock_backup2 = MagicMock()
        mock_backup2.name = "chroma_backup_20240116_100000.tar.gz"
        mock_backup2.stat.return_value = MagicMock(
            st_size=2 * 1024 * 1024,  # 2 MB
            st_ctime=datetime(2024, 1, 16, 10, 0, 0).timestamp(),
            st_mtime=datetime(2024, 1, 16, 10, 0, 0).timestamp()
        )
        
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'glob', return_value=[mock_backup2, mock_backup1]):
                result = list_backups()
        
        assert len(result) == 2
        assert result[0]["filename"] == "chroma_backup_20240116_100000.tar.gz"
        assert result[0]["size_mb"] == 2.0
        assert result[1]["filename"] == "chroma_backup_20240115_100000.tar.gz"
        assert result[1]["size_mb"] == 1.0


class TestRestoreBackup:
    """Tests for backup restoration."""
    
    @patch('db.cleanup.config')
    def test_restore_requires_confirm(self, mock_config):
        """Test that restore requires confirmation."""
        mock_config.backup_dir = Path("/fake/backups")
        
        result = restore_backup(Path("/fake/backup.tar.gz"), confirm=False)
        
        assert result["success"] is False
        assert "confirm" in result["message"].lower()
    
    @patch('db.cleanup.config')
    def test_restore_nonexistent_backup(self, mock_config):
        """Test restoring from non-existent backup."""
        mock_config.backup_dir = Path("/fake/backups")
        
        with patch.object(Path, 'exists', return_value=False):
            result = restore_backup(Path("/fake/nonexistent.tar.gz"), confirm=True)
        
        assert result["success"] is False
        assert "not found" in result["message"].lower()
    
    @patch('db.cleanup.tarfile.open')
    @patch('db.cleanup.shutil.rmtree')
    @patch('db.cleanup.create_backup')
    @patch('db.cleanup.config')
    def test_restore_backup(self, mock_config, mock_create_backup, mock_rmtree, mock_tarfile):
        """Test successful backup restoration."""
        mock_config.chroma_path = Path("/fake/chroma_db")
        mock_config.backup_dir = Path("/fake/backups")
        
        mock_create_backup.return_value = Path("/fake/pre_restore_backup.tar.gz")
        
        with patch.object(Path, 'exists', return_value=True):
            result = restore_backup(Path("/fake/backup.tar.gz"), confirm=True)
        
        assert result["success"] is True
        assert "restored" in result["message"].lower()
        mock_rmtree.assert_called_once()
        mock_tarfile.assert_called_once()