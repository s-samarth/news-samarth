import sqlite3
from typing import List, Dict, Any
from .config import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    platform        TEXT    NOT NULL,              -- 'substack' | 'reddit' | 'youtube' | 'twitter'
    source_name     TEXT    NOT NULL,              -- e.g. 'Stratechery', 'r/LocalLLaMA', '@elonmusk'
    title           TEXT,
    content_text    TEXT,
    url             TEXT    NOT NULL UNIQUE,        -- Upsert dedup key
    timestamp       TEXT    NOT NULL,               -- ISO 8601
    media_link      TEXT,                           -- Thumbnail / image URL
    scraped_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_platform      ON articles(platform);
CREATE INDEX IF NOT EXISTS idx_source_name   ON articles(source_name);
CREATE INDEX IF NOT EXISTS idx_timestamp     ON articles(timestamp);
"""

def init_db():
    with sqlite3.connect(config.db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()

def upsert_articles(articles: List[Dict[str, Any]]) -> int:
    """Inserts articles or ignores if URL already exists. Returns count of new items."""
    if not articles:
        return 0
    
    new_count = 0
    with sqlite3.connect(config.db_path) as conn:
        cursor = conn.cursor()
        for art in articles:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO articles 
                    (platform, source_name, title, content_text, url, timestamp, media_link)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        art.get("platform"),
                        art.get("source_name"),
                        art.get("title"),
                        art.get("content_text"),
                        art.get("url"),
                        art.get("timestamp"),
                        art.get("media_link"),
                    )
                )
                if cursor.rowcount > 0:
                    new_count += 1
            except sqlite3.Error as e:
                # Log error elsewhere or just skip
                pass
        conn.commit()
    return new_count

def get_latest_articles(
    platform: str = None, 
    source_name: str = None, 
    limit: int = 50, 
    offset: int = 0
) -> Dict[str, Any]:
    query = "SELECT * FROM articles WHERE 1=1"
    params = []
    
    if platform:
        query += " AND platform = ?"
        params.append(platform)
    if source_name:
        query += " AND source_name = ?"
        params.append(source_name)
        
    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    with sqlite3.connect(config.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        # Get total count for pagination
        count_query = "SELECT COUNT(*) FROM articles WHERE 1=1"
        count_params = []
        if platform:
            count_query += " AND platform = ?"
            count_params.append(platform)
        if source_name:
            count_query += " AND source_name = ?"
            count_params.append(source_name)
            
        cursor.execute(count_query, tuple(count_params))
        total = cursor.fetchone()[0]
        
    return {
        "total": total,
        "items": [dict(row) for row in rows]
    }
