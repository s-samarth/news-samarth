import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

class Config:
    """
    Centralized configuration manager for the Newsfeed Aggregator.
    
    Handles environment variables, file paths, and application settings.
    Supports both legacy SQLite and new ChromaDB database backends.
    """
    
    def __init__(self):
        self.sources_path = BASE_DIR / "sources.json"
        # Legacy SQLite path (kept for backward compatibility)
        self.db_path = BASE_DIR / "db" / "newsfeed.db"
        # ChromaDB path (new NoSQL AI-ready database)
        self.chroma_path = BASE_DIR / "db" / "chroma_db"
        self.log_dir = BASE_DIR / "logs"
        self._ensure_paths()
        self.sources = self._load_sources()

    def _ensure_paths(self):
        """Create required directories if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _load_sources(self):
        """
        Load sources from sources.json with platform-specific schema support.
        
        The sources.json file uses a platform-specific schema where each platform
        has its own configuration structure tailored to its data format:
        
        - youtube: Requires channel_id, max_results, fetch_transcript
        - reddit: Requires subreddit, sort, limit
        - substack: Requires rss_url
        - twitter: Requires handle, max_tweets
        
        Returns:
            dict: Platform-specific source configurations
        """
        if not self.sources_path.exists():
            return {}
        
        with open(self.sources_path, "r") as f:
            raw_sources = json.load(f)
        
        # Extract sources from platform-specific schema
        # Each platform has a "sources" key containing the list of sources
        sources = {}
        for platform in ["youtube", "reddit", "substack", "twitter"]:
            if platform in raw_sources and "sources" in raw_sources[platform]:
                sources[platform] = raw_sources[platform]["sources"]
            else:
                sources[platform] = []
        
        return sources

    @property
    def youtube_api_key(self) -> str:
        """YouTube Data API v3 key from environment variables."""
        return os.getenv("YOUTUBE_API_KEY")

    @property
    def openrouter_api_key(self) -> str:
        """OpenRouter API key for AI summarization."""
        return os.getenv("OPENROUTER_API_KEY")

    @property
    def openrouter_model(self) -> str:
        """
        OpenRouter model name for AI summarization.
        
        Default: anthropic/claude-3.5-sonnet
        Other options: openai/gpt-4o, meta-llama/llama-3.1-70b-instruct
        See https://openrouter.ai/models for full list
        """
        return os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

    @property
    def twitter_username(self) -> str:
        """Twitter/X username for Playwright-based extraction."""
        return os.getenv("TWITTER_USERNAME")

    @property
    def twitter_password(self) -> str:
        """Twitter/X password for Playwright-based extraction."""
        return os.getenv("TWITTER_PASSWORD")

    @property
    def twitter_email(self) -> str:
        """Twitter/X email for verification (optional)."""
        return os.getenv("TWITTER_EMAIL")

    @property
    def playwright_profile_dir(self) -> Path:
        """
        Playwright browser profile directory for Twitter extraction.
        
        This directory stores the isolated browser session data,
        ensuring no cross-contamination with the main browser.
        """
        return BASE_DIR / ".playwright_twitter_profile"

    # =========================================================================
    # Timezone Configuration
    # =========================================================================
    
    @property
    def timezone(self) -> str:
        """
        Timezone for date calculations.
        
        Default: 'local' (uses system timezone)
        Can be set to any valid timezone string (e.g., 'UTC', 'America/New_York')
        """
        return os.getenv("TIMEZONE", "local")

    # =========================================================================
    # Cleanup Configuration
    # =========================================================================
    
    @property
    def auto_cleanup_enabled(self) -> bool:
        """
        Enable automatic cleanup of old articles.
        
        Default: False (opt-in for safety)
        """
        return os.getenv("AUTO_CLEANUP_ENABLED", "false").lower() == "true"

    @property
    def auto_cleanup_days(self) -> int:
        """
        Number of days to keep articles.
        
        Default: 30
        Articles older than this will be deleted during cleanup.
        """
        return int(os.getenv("AUTO_CLEANUP_DAYS", "30"))

    @property
    def auto_cleanup_on_startup(self) -> bool:
        """
        Run cleanup on server startup.
        
        Default: False (manual cleanup recommended)
        """
        return os.getenv("AUTO_CLEANUP_ON_STARTUP", "false").lower() == "true"

    @property
    def backup_dir(self) -> Path:
        """
        Directory for database backups.
        
        Default: db/backups/
        """
        return self.chroma_path.parent / "backups"

# Global configuration instance
config = Config()
