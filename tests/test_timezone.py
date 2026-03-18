"""
Tests for Timezone Utilities Module
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock
import os

from db.timezone_utils import (
    get_configured_timezone,
    get_timezone_obj,
    get_now,
    get_today,
    get_yesterday,
    get_24h_ago,
    normalize_timestamp,
    date_to_iso_range,
    is_within_last_n_days,
    get_date_from_timestamp,
    format_for_display,
    get_timezone_info
)


class TestGetConfiguredTimezone:
    """Tests for timezone configuration."""
    
    def test_default_timezone(self):
        """Test default timezone is 'local'."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove TIMEZONE if it exists
            os.environ.pop('TIMEZONE', None)
            tz = get_configured_timezone()
            assert tz == "local"
    
    def test_custom_timezone(self):
        """Test custom timezone from environment."""
        with patch.dict(os.environ, {'TIMEZONE': 'UTC'}):
            tz = get_configured_timezone()
            assert tz == "UTC"


class TestGetNow:
    """Tests for get_now function."""
    
    def test_returns_datetime(self):
        """Test that get_now returns a datetime object."""
        now = get_now()
        assert isinstance(now, datetime)
    
    def test_returns_current_time(self):
        """Test that get_now returns approximately current time."""
        before = datetime.now()
        now = get_now()
        after = datetime.now()
        
        # Should be within a few seconds
        assert before <= now.replace(tzinfo=None) <= after + timedelta(seconds=5)


class TestGetToday:
    """Tests for get_today function."""
    
    def test_returns_date(self):
        """Test that get_today returns a date object."""
        today = get_today()
        assert isinstance(today, date)
    
    def test_returns_current_date(self):
        """Test that get_today returns current date."""
        today = get_today()
        expected = datetime.now().date()
        assert today == expected


class TestGetYesterday:
    """Tests for get_yesterday function."""
    
    def test_returns_yesterday(self):
        """Test that get_yesterday returns yesterday's date."""
        yesterday = get_yesterday()
        expected = datetime.now().date() - timedelta(days=1)
        assert yesterday == expected


class TestGet24hAgo:
    """Tests for get_24h_ago function."""
    
    def test_returns_24_hours_ago(self):
        """Test that get_24h_ago returns datetime 24 hours ago."""
        ago = get_24h_ago()
        now = get_now()
        
        # Should be approximately 24 hours ago (within a few seconds)
        diff = now - ago
        assert timedelta(hours=23, minutes=59, seconds=55) <= diff <= timedelta(hours=24, minutes=0, seconds=5)


class TestNormalizeTimestamp:
    """Tests for timestamp normalization."""
    
    def test_iso_with_timezone(self):
        """Test normalizing ISO timestamp with timezone."""
        result = normalize_timestamp("2024-01-15T10:00:00+00:00")
        assert "2024-01-15" in result
    
    def test_iso_without_timezone(self):
        """Test normalizing ISO timestamp without timezone."""
        result = normalize_timestamp("2024-01-15T10:00:00")
        assert "2024-01-15" in result
    
    def test_date_only(self):
        """Test normalizing date-only string."""
        result = normalize_timestamp("2024-01-15")
        assert "2024-01-15" in result
    
    def test_empty_timestamp(self):
        """Test normalizing empty timestamp returns current time."""
        result = normalize_timestamp("")
        assert result  # Should return something
    
    def test_invalid_timestamp(self):
        """Test normalizing invalid timestamp returns current time."""
        result = normalize_timestamp("not-a-date")
        assert result  # Should return something


class TestDateToIsoRange:
    """Tests for date to ISO range conversion."""
    
    def test_valid_date(self):
        """Test converting valid date to range."""
        start, end = date_to_iso_range("2024-01-15")
        assert start == "2024-01-15T00:00:00"
        assert end == "2024-01-15T23:59:59.999999"
    
    def test_invalid_date(self):
        """Test converting invalid date returns today's range."""
        start, end = date_to_iso_range("invalid")
        today = datetime.now().strftime("%Y-%m-%d")
        assert today in start
        assert today in end


class TestIsWithinLastNDays:
    """Tests for date range checking."""
    
    def test_recent_timestamp(self):
        """Test that recent timestamp is within range."""
        recent = datetime.now().isoformat()
        assert is_within_last_n_days(recent, 7) is True
    
    def test_old_timestamp(self):
        """Test that old timestamp is not within range."""
        old = (datetime.now() - timedelta(days=100)).isoformat()
        assert is_within_last_n_days(old, 7) is False
    
    def test_empty_timestamp(self):
        """Test that empty timestamp returns False."""
        assert is_within_last_n_days("", 7) is False


class TestGetDateFromTimestamp:
    """Tests for date extraction from timestamp."""
    
    def test_iso_timestamp(self):
        """Test extracting date from ISO timestamp."""
        result = get_date_from_timestamp("2024-01-15T10:00:00")
        assert result == "2024-01-15"
    
    def test_date_only(self):
        """Test extracting date from date-only string."""
        result = get_date_from_timestamp("2024-01-15")
        assert result == "2024-01-15"
    
    def test_empty_timestamp(self):
        """Test extracting date from empty timestamp."""
        result = get_date_from_timestamp("")
        assert result is None
    
    def test_invalid_timestamp(self):
        """Test extracting date from invalid timestamp."""
        result = get_date_from_timestamp("invalid")
        assert result is None


class TestFormatForDisplay:
    """Tests for display formatting."""
    
    def test_iso_timestamp(self):
        """Test formatting ISO timestamp."""
        result = format_for_display("2024-01-15T10:30:00")
        assert "2024-01-15" in result
        assert "10:30" in result
    
    def test_custom_format(self):
        """Test formatting with custom format string."""
        result = format_for_display("2024-01-15T10:30:00", "%Y/%m/%d")
        assert result == "2024/01/15"
    
    def test_empty_timestamp(self):
        """Test formatting empty timestamp."""
        result = format_for_display("")
        assert result == "Unknown"


class TestGetTimezoneInfo:
    """Tests for timezone info function."""
    
    def test_returns_dict(self):
        """Test that get_timezone_info returns a dict."""
        info = get_timezone_info()
        assert isinstance(info, dict)
    
    def test_has_required_keys(self):
        """Test that info has required keys."""
        info = get_timezone_info()
        assert "configured_timezone" in info
        assert "has_pytz" in info
        assert "current_time" in info
        assert "current_date" in info