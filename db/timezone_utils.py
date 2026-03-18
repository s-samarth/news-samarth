"""
Timezone Utilities Module

Provides timezone-aware datetime functions for consistent date handling
across the application. Uses the configured timezone from environment.
"""

import os
from datetime import datetime, date, timedelta
from typing import Optional

# Try to import pytz, fall back to basic datetime if not available
try:
    import pytz
    HAS_PYTZ = True
except ImportError:
    HAS_PYTZ = False
    pytz = None


def get_configured_timezone():
    """
    Get the configured timezone from environment.
    
    Returns:
        Timezone string or 'local' for system timezone
    """
    return os.getenv("TIMEZONE", "local")


def get_timezone_obj():
    """
    Get timezone object for datetime operations.
    
    Returns:
        pytz timezone object or None for local timezone
    """
    if not HAS_PYTZ:
        return None
    
    tz_name = get_configured_timezone()
    
    if tz_name == "local":
        return None  # Use system local timezone
    
    try:
        return pytz.timezone(tz_name)
    except pytz.exceptions.UnknownTimeZoneError:
        # Fall back to local if invalid timezone
        return None


def get_now() -> datetime:
    """
    Get current time in configured timezone.
    
    Returns:
        Timezone-aware datetime object
    """
    tz = get_timezone_obj()
    
    if tz is None:
        # Use local timezone
        return datetime.now()
    
    # Use configured timezone
    return datetime.now(tz)


def get_today() -> date:
    """
    Get today's date in configured timezone.
    
    Returns:
        Date object for today
    """
    return get_now().date()


def get_yesterday() -> date:
    """
    Get yesterday's date in configured timezone.
    
    Returns:
        Date object for yesterday
    """
    return get_today() - timedelta(days=1)


def get_24h_ago() -> datetime:
    """
    Get datetime 24 hours ago in configured timezone.
    
    Returns:
        Timezone-aware datetime object
    """
    return get_now() - timedelta(hours=24)


def normalize_timestamp(timestamp: str) -> str:
    """
    Normalize timestamp to ISO 8601 format.
    
    Handles various input formats:
    - ISO 8601 with timezone
    - ISO 8601 without timezone (assumes UTC)
    - Date only (YYYY-MM-DD)
    
    Args:
        timestamp: Input timestamp string
        
    Returns:
        Normalized ISO 8601 timestamp string
    """
    if not timestamp:
        return get_now().isoformat()
    
    try:
        # Try parsing as ISO 8601
        if "T" in timestamp:
            # Has time component
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            
            # If no timezone info, assume UTC
            if dt.tzinfo is None:
                if HAS_PYTZ:
                    dt = pytz.utc.localize(dt)
            
            return dt.isoformat()
        else:
            # Date only - add midnight time
            dt = datetime.strptime(timestamp, "%Y-%m-%d")
            return dt.isoformat()
            
    except (ValueError, TypeError):
        # Return current time if parsing fails
        return get_now().isoformat()


def date_to_iso_range(target_date: str) -> tuple:
    """
    Convert a date string to ISO 8601 range (start, end of day).
    
    Args:
        target_date: Date string in YYYY-MM-DD format
        
    Returns:
        Tuple of (start_iso, end_iso) strings
    """
    try:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        end = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        return (start.isoformat(), end.isoformat())
    except ValueError:
        # Return today's range if parsing fails
        today = get_today()
        start = datetime.combine(today, datetime.min.time())
        end = datetime.combine(today, datetime.max.time())
        return (start.isoformat(), end.isoformat())


def is_within_last_n_days(timestamp: str, days: int) -> bool:
    """
    Check if a timestamp is within the last N days.
    
    Args:
        timestamp: ISO 8601 timestamp string
        days: Number of days to check
        
    Returns:
        True if within last N days, False otherwise
    """
    if not timestamp:
        return False
    
    try:
        # Parse timestamp
        if "T" in timestamp:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        else:
            dt = datetime.strptime(timestamp, "%Y-%m-%d")
        
        # Remove timezone for comparison
        if dt.tzinfo:
            dt = dt.replace(tzinfo=None)
        
        # Calculate cutoff
        cutoff = datetime.now() - timedelta(days=days)
        
        return dt >= cutoff
        
    except (ValueError, TypeError):
        return False


def get_date_from_timestamp(timestamp: str) -> Optional[str]:
    """
    Extract date string (YYYY-MM-DD) from timestamp.
    
    Args:
        timestamp: ISO 8601 timestamp string
        
    Returns:
        Date string or None if invalid
    """
    if not timestamp:
        return None
    
    try:
        if "T" in timestamp:
            return timestamp[:10]
        else:
            # Already a date string
            datetime.strptime(timestamp, "%Y-%m-%d")
            return timestamp
    except (ValueError, TypeError):
        return None


def format_for_display(timestamp: str, format_str: str = "%Y-%m-%d %H:%M") -> str:
    """
    Format timestamp for display.
    
    Args:
        timestamp: ISO 8601 timestamp string
        format_str: strftime format string
        
    Returns:
        Formatted date/time string
    """
    if not timestamp:
        return "Unknown"
    
    try:
        if "T" in timestamp:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        else:
            dt = datetime.strptime(timestamp, "%Y-%m-%d")
        
        return dt.strftime(format_str)
        
    except (ValueError, TypeError):
        return timestamp


def get_timezone_info() -> dict:
    """
    Get information about the current timezone configuration.
    
    Returns:
        Dict with timezone information
    """
    tz_name = get_configured_timezone()
    now = get_now()
    
    info = {
        "configured_timezone": tz_name,
        "has_pytz": HAS_PYTZ,
        "current_time": now.isoformat(),
        "current_date": str(get_today()),
        "utc_offset": None
    }
    
    if now.tzinfo:
        info["utc_offset"] = str(now.utcoffset())
        info["timezone_name"] = str(now.tzinfo)
    
    return info