"""
Database Health Check Module

Provides functions to check ChromaDB integrity, validate articles,
and scan for common issues. All functions are read-only and safe to run.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def validate_article(article: Dict[str, Any]) -> List[str]:
    """
    Validate a single article's data.
    
    Checks for:
    - Missing required fields
    - Invalid timestamp format
    - Empty content
    - Invalid URL format
    
    Args:
        article: Article dictionary with metadata
        
    Returns:
        List of issue descriptions (empty if valid)
    """
    issues = []
    
    # Check required fields
    required_fields = ["url", "platform", "source_name"]
    for field in required_fields:
        if not article.get(field):
            issues.append(f"Missing required field: {field}")
    
    # Check URL format
    url = article.get("url", "")
    if url and not (url.startswith("http://") or url.startswith("https://")):
        issues.append(f"Invalid URL format: {url}")
    
    # Check timestamp format
    timestamp = article.get("timestamp", "")
    if timestamp:
        try:
            # Try to parse ISO 8601 format
            if "T" in timestamp:
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            else:
                datetime.strptime(timestamp, "%Y-%m-%d")
        except (ValueError, TypeError):
            issues.append(f"Invalid timestamp format: {timestamp}")
    
    # Check for future timestamps (more than 1 day in future)
    if timestamp:
        try:
            if "T" in timestamp:
                ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            else:
                ts = datetime.strptime(timestamp, "%Y-%m-%d")
            
            # Remove timezone info for comparison
            if ts.tzinfo:
                ts = ts.replace(tzinfo=None)
            
            now = datetime.now()
            if ts > now + timedelta(days=1):
                issues.append(f"Timestamp is in the future: {timestamp}")
        except (ValueError, TypeError):
            pass  # Already caught above
    
    # Check content
    content = article.get("content_text", "")
    title = article.get("title", "")
    if not content and not title:
        issues.append("Both content_text and title are empty")
    
    # Check platform validity
    valid_platforms = ["youtube", "reddit", "substack", "twitter"]
    platform = article.get("platform", "")
    if platform and platform not in valid_platforms:
        issues.append(f"Unknown platform: {platform}")
    
    return issues


def check_database_integrity(collection) -> Dict[str, Any]:
    """
    Check ChromaDB integrity.
    
    Performs comprehensive checks:
    - Total article count
    - Articles by platform
    - Date range of articles
    - Duplicate detection
    - Metadata completeness
    
    Args:
        collection: ChromaDB collection instance
        
    Returns:
        Dict with: status, article_count, platforms, date_range, issues, warnings
    """
    result = {
        "status": "healthy",
        "article_count": 0,
        "platforms": {},
        "date_range": {"earliest": None, "latest": None},
        "issues": [],
        "warnings": [],
        "checked_at": datetime.now().isoformat()
    }
    
    try:
        # Get all articles
        all_items = collection.get(include=["metadatas"])
        
        if not all_items["ids"]:
            result["status"] = "empty"
            result["warnings"].append("Database is empty - no articles found")
            return result
        
        result["article_count"] = len(all_items["ids"])
        
        # Analyze metadata
        platforms = {}
        timestamps = []
        urls = set()
        duplicates = []
        
        for i, doc_id in enumerate(all_items["ids"]):
            metadata = all_items["metadatas"][i] if all_items["metadatas"] else {}
            
            # Count by platform
            platform = metadata.get("platform", "unknown")
            platforms[platform] = platforms.get(platform, 0) + 1
            
            # Collect timestamps
            timestamp = metadata.get("timestamp")
            if timestamp:
                timestamps.append(timestamp)
            
            # Check for duplicates (by URL)
            url = metadata.get("url")
            if url:
                if url in urls:
                    duplicates.append(url)
                urls.add(url)
        
        result["platforms"] = platforms
        
        # Date range
        if timestamps:
            timestamps.sort()
            result["date_range"]["earliest"] = timestamps[0]
            result["date_range"]["latest"] = timestamps[-1]
        
        # Report duplicates
        if duplicates:
            result["warnings"].append(f"Found {len(duplicates)} duplicate URLs")
            result["duplicate_urls"] = duplicates[:10]  # First 10
        
        # Check for articles older than 30 days
        cutoff = (datetime.now() - timedelta(days=30)).isoformat()
        old_count = sum(1 for ts in timestamps if ts < cutoff)
        if old_count > 0:
            result["warnings"].append(f"{old_count} articles are older than 30 days")
        
        # Check for future articles
        now = datetime.now().isoformat()
        future_count = sum(1 for ts in timestamps if ts > now)
        if future_count > 0:
            result["issues"].append(f"{future_count} articles have future timestamps")
            result["status"] = "warning"
        
        # Set overall status
        if result["issues"]:
            result["status"] = "unhealthy"
        elif result["warnings"]:
            result["status"] = "warning"
        
    except Exception as e:
        result["status"] = "error"
        result["issues"].append(f"Error checking database: {str(e)}")
        logger.error(f"Database integrity check failed: {e}")
    
    return result


def scan_for_issues(collection, sample_size: int = 100) -> Dict[str, Any]:
    """
    Scan articles for common issues.
    
    Validates a sample of articles and reports issues found.
    
    Args:
        collection: ChromaDB collection instance
        sample_size: Number of articles to sample (default: 100)
        
    Returns:
        Dict with: total_scanned, valid_count, invalid_count, issues_by_type, sample_issues
    """
    result = {
        "total_scanned": 0,
        "valid_count": 0,
        "invalid_count": 0,
        "issues_by_type": {},
        "sample_issues": [],
        "scanned_at": datetime.now().isoformat()
    }
    
    try:
        # Get sample of articles
        all_items = collection.get(
            limit=sample_size,
            include=["documents", "metadatas"]
        )
        
        if not all_items["ids"]:
            return result
        
        result["total_scanned"] = len(all_items["ids"])
        
        for i, doc_id in enumerate(all_items["ids"]):
            metadata = all_items["metadatas"][i] if all_items["metadatas"] else {}
            document = all_items["documents"][i] if all_items["documents"] else ""
            
            # Combine metadata and document for validation
            article = {
                **metadata,
                "content_text": document
            }
            
            issues = validate_article(article)
            
            if issues:
                result["invalid_count"] += 1
                
                # Count issues by type
                for issue in issues:
                    issue_type = issue.split(":")[0] if ":" in issue else issue
                    result["issues_by_type"][issue_type] = result["issues_by_type"].get(issue_type, 0) + 1
                
                # Store sample issues (limit to 20)
                if len(result["sample_issues"]) < 20:
                    result["sample_issues"].append({
                        "id": doc_id,
                        "url": metadata.get("url", "unknown"),
                        "issues": issues
                    })
            else:
                result["valid_count"] += 1
        
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Issue scan failed: {e}")
    
    return result


def get_database_stats(collection) -> Dict[str, Any]:
    """
    Get comprehensive database statistics.
    
    Args:
        collection: ChromaDB collection instance
        
    Returns:
        Dict with various statistics
    """
    stats = {
        "total_articles": 0,
        "by_platform": {},
        "by_type": {"article": 0, "summary": 0, "newsletter": 0},
        "date_range": {},
        "content_stats": {
            "avg_content_length": 0,
            "empty_content_count": 0
        }
    }
    
    try:
        all_items = collection.get(include=["documents", "metadatas"])
        
        if not all_items["ids"]:
            return stats
        
        stats["total_articles"] = len(all_items["ids"])
        
        content_lengths = []
        timestamps = []
        
        for i, doc_id in enumerate(all_items["ids"]):
            metadata = all_items["metadatas"][i] if all_items["metadatas"] else {}
            document = all_items["documents"][i] if all_items["documents"] else ""
            
            # Count by platform
            platform = metadata.get("platform", "unknown")
            stats["by_platform"][platform] = stats["by_platform"].get(platform, 0) + 1
            
            # Count by type
            doc_type = metadata.get("type", "article")
            if doc_type in stats["by_type"]:
                stats["by_type"][doc_type] += 1
            
            # Content stats
            if document:
                content_lengths.append(len(document))
            else:
                stats["content_stats"]["empty_content_count"] += 1
            
            # Timestamps
            timestamp = metadata.get("timestamp")
            if timestamp:
                timestamps.append(timestamp)
        
        # Average content length
        if content_lengths:
            stats["content_stats"]["avg_content_length"] = sum(content_lengths) // len(content_lengths)
        
        # Date range
        if timestamps:
            timestamps.sort()
            stats["date_range"] = {
                "earliest": timestamps[0],
                "latest": timestamps[-1],
                "span_days": (datetime.fromisoformat(timestamps[-1].replace("Z", "+00:00").split("T")[0]) - 
                             datetime.fromisoformat(timestamps[0].replace("Z", "+00:00").split("T")[0])).days
            }
        
    except Exception as e:
        stats["error"] = str(e)
        logger.error(f"Failed to get database stats: {e}")
    
    return stats