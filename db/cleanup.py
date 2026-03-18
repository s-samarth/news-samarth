"""
Database Cleanup Module

Provides functions to safely clean up old articles from ChromaDB.
Includes dry-run mode, backup creation, and detailed reporting.
"""

import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

from config import config

logger = logging.getLogger(__name__)


def run_cleanup(
    collection,
    days_old: int = None,
    dry_run: bool = True,
    backup: bool = True
) -> Dict[str, Any]:
    """
    Run cleanup of old articles with safety checks.
    
    Args:
        collection: ChromaDB collection instance
        days_old: Delete articles older than this many days (default: config value)
        dry_run: If True, return what would be deleted without deleting
        backup: If True, create backup before deletion (ignored if dry_run=True)
        
    Returns:
        Dict with: deleted_count, total_before, total_after, errors, backup_path
    """
    if days_old is None:
        days_old = getattr(config, 'auto_cleanup_days', 30)
    
    result = {
        "success": False,
        "deleted_count": 0,
        "total_before": 0,
        "total_after": 0,
        "days_old": days_old,
        "dry_run": dry_run,
        "errors": [],
        "backup_path": None,
        "cutoff_date": None,
        "articles_to_delete": [],
        "executed_at": datetime.now().isoformat()
    }
    
    try:
        # Get total count before
        result["total_before"] = collection.count()
        
        # Calculate cutoff date
        cutoff = (datetime.now() - timedelta(days=days_old)).isoformat()
        result["cutoff_date"] = cutoff
        
        # Get old articles
        old_articles = collection.get(
            where={"timestamp": {"$lt": cutoff}},
            include=["metadatas"]
        )
        
        if not old_articles["ids"]:
            result["success"] = True
            result["total_after"] = result["total_before"]
            result["message"] = "No articles older than cutoff date found"
            return result
        
        result["deleted_count"] = len(old_articles["ids"])
        
        # Collect info about articles to delete
        for i, doc_id in enumerate(old_articles["ids"]):
            metadata = old_articles["metadatas"][i] if old_articles["metadatas"] else {}
            result["articles_to_delete"].append({
                "id": doc_id,
                "url": metadata.get("url", "unknown"),
                "platform": metadata.get("platform", "unknown"),
                "timestamp": metadata.get("timestamp", "unknown"),
                "title": metadata.get("title", "")[:50]  # Truncate for readability
            })
        
        if dry_run:
            result["success"] = True
            result["total_after"] = result["total_before"]
            result["message"] = f"Dry run: Would delete {result['deleted_count']} articles"
            return result
        
        # Create backup if requested
        if backup:
            try:
                backup_path = create_backup()
                result["backup_path"] = str(backup_path)
                logger.info(f"Backup created at: {backup_path}")
            except Exception as e:
                result["errors"].append(f"Backup failed: {str(e)}")
                logger.error(f"Backup failed: {e}")
                # Continue with deletion even if backup fails
        
        # Perform deletion
        collection.delete(ids=old_articles["ids"])
        
        # Get total count after
        result["total_after"] = collection.count()
        result["success"] = True
        result["message"] = f"Successfully deleted {result['deleted_count']} articles"
        
        logger.info(f"Cleanup completed: deleted {result['deleted_count']} articles")
        
    except Exception as e:
        result["errors"].append(f"Cleanup failed: {str(e)}")
        result["success"] = False
        logger.error(f"Cleanup failed: {e}")
    
    return result


def create_backup(backup_dir: Path = None) -> Path:
    """
    Create timestamped backup of ChromaDB directory.
    
    Args:
        backup_dir: Directory to store backups (default: db/backups/)
        
    Returns:
        Path to created backup file
    """
    if backup_dir is None:
        backup_dir = config.chroma_path.parent / "backups"
    
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Create timestamped backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"chroma_backup_{timestamp}.tar.gz"
    backup_path = backup_dir / backup_name
    
    # Create tar.gz archive of ChromaDB directory
    import tarfile
    with tarfile.open(backup_path, "w:gz") as tar:
        tar.add(config.chroma_path, arcname="chroma_db")
    
    logger.info(f"Backup created: {backup_path}")
    return backup_path


def list_backups(backup_dir: Path = None) -> list:
    """
    List available backups with metadata.
    
    Args:
        backup_dir: Directory containing backups (default: db/backups/)
        
    Returns:
        List of backup info dicts
    """
    if backup_dir is None:
        backup_dir = config.chroma_path.parent / "backups"
    
    if not backup_dir.exists():
        return []
    
    backups = []
    for backup_file in sorted(backup_dir.glob("chroma_backup_*.tar.gz"), reverse=True):
        stat = backup_file.stat()
        backups.append({
            "filename": backup_file.name,
            "path": str(backup_file),
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })
    
    return backups


def restore_backup(backup_path: Path, confirm: bool = False) -> Dict[str, Any]:
    """
    Restore database from backup.
    
    WARNING: This will replace the current database!
    
    Args:
        backup_path: Path to backup file
        confirm: Must be True to actually restore
        
    Returns:
        Dict with: success, message, restored_from
    """
    result = {
        "success": False,
        "message": "",
        "restored_from": str(backup_path),
        "executed_at": datetime.now().isoformat()
    }
    
    if not confirm:
        result["message"] = "Restore cancelled - confirm=True required"
        return result
    
    if not backup_path.exists():
        result["message"] = f"Backup file not found: {backup_path}"
        return result
    
    try:
        # Create backup of current database before restore
        pre_restore_backup = create_backup()
        logger.info(f"Pre-restore backup created: {pre_restore_backup}")
        
        # Remove current database
        if config.chroma_path.exists():
            shutil.rmtree(config.chroma_path)
        
        # Extract backup
        import tarfile
        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(path=config.chroma_path.parent)
        
        result["success"] = True
        result["message"] = f"Database restored from {backup_path.name}"
        result["pre_restore_backup"] = str(pre_restore_backup)
        
        logger.info(f"Database restored from: {backup_path}")
        
    except Exception as e:
        result["message"] = f"Restore failed: {str(e)}"
        result["success"] = False
        logger.error(f"Restore failed: {e}")
    
    return result


def delete_article_by_url(collection, url: str) -> bool:
    """
    Delete a single article by URL.
    
    Args:
        collection: ChromaDB collection instance
        url: URL of article to delete
        
    Returns:
        True if found and deleted, False otherwise
    """
    import hashlib
    doc_id = hashlib.sha256(url.encode()).hexdigest()
    
    try:
        # Check if article exists
        existing = collection.get(ids=[doc_id])
        if not existing["ids"]:
            return False
        
        collection.delete(ids=[doc_id])
        logger.info(f"Deleted article: {url}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete article {url}: {e}")
        return False


def delete_articles_by_urls(collection, urls: list) -> Dict[str, bool]:
    """
    Delete multiple articles by URL.
    
    Args:
        collection: ChromaDB collection instance
        urls: List of URLs to delete
        
    Returns:
        Dict mapping URL to deletion status
    """
    import hashlib
    
    results = {}
    ids_to_delete = []
    
    for url in urls:
        doc_id = hashlib.sha256(url.encode()).hexdigest()
        ids_to_delete.append(doc_id)
    
    try:
        # Check which articles exist
        existing = collection.get(ids=ids_to_delete)
        existing_ids = set(existing["ids"])
        
        # Delete existing articles
        if existing_ids:
            collection.delete(ids=list(existing_ids))
        
        # Build results
        for url, doc_id in zip(urls, ids_to_delete):
            results[url] = doc_id in existing_ids
        
        logger.info(f"Deleted {len(existing_ids)} of {len(urls)} articles")
        
    except Exception as e:
        logger.error(f"Batch delete failed: {e}")
        for url in urls:
            results[url] = False
    
    return results


def delete_articles_by_platform(collection, platform: str) -> int:
    """
    Delete all articles from a specific platform.
    
    Args:
        collection: ChromaDB collection instance
        platform: Platform name (e.g., "youtube", "reddit")
        
    Returns:
        Number of articles deleted
    """
    try:
        # Get all articles from platform
        articles = collection.get(
            where={"platform": platform},
            include=["metadatas"]
        )
        
        if not articles["ids"]:
            return 0
        
        # Delete them
        collection.delete(ids=articles["ids"])
        
        deleted_count = len(articles["ids"])
        logger.info(f"Deleted {deleted_count} articles from platform: {platform}")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Failed to delete articles from platform {platform}: {e}")
        return 0


def get_cleanup_preview(collection, days_old: int = None) -> Dict[str, Any]:
    """
    Preview what would be deleted without actually deleting.
    
    Args:
        collection: ChromaDB collection instance
        days_old: Delete articles older than this many days
        
    Returns:
        Dict with preview information
    """
    return run_cleanup(collection, days_old=days_old, dry_run=True, backup=False)