from abc import ABC, abstractmethod
from typing import List, Dict, Any
from db.models import upsert_articles

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return a list of article dicts matching the DB schema."""
        pass

    def run(self, sources: List[Dict[str, Any]]) -> int:
        """Runs extract + upserts to DB. Returns count of new rows."""
        articles = self.extract(sources)
        return upsert_articles(articles)
