import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

class Config:
    def __init__(self):
        self.sources_path = BASE_DIR / "sources.json"
        self.db_path = BASE_DIR / "db" / "newsfeed.db"
        self.log_dir = BASE_DIR / "logs"
        self._ensure_paths()
        self.sources = self._load_sources()

    def _ensure_paths(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _load_sources(self):
        if not self.sources_path.exists():
            return {}
        with open(self.sources_path, "r") as f:
            return json.load(f)

    @property
    def reddit_creds(self):
        return {
            "client_id": os.getenv("REDDIT_CLIENT_ID"),
            "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
            "user_agent": os.getenv("REDDIT_USER_AGENT", "newsfeed-aggregator/1.0"),
            "username": os.getenv("REDDIT_USERNAME"),
            "password": os.getenv("REDDIT_PASSWORD"),
        }

    @property
    def youtube_api_key(self):
        return os.getenv("YOUTUBE_API_KEY")

config = Config()
