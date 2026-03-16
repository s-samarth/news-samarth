from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from db import get_latest_articles
from config import config

app = FastAPI(title="Newsfeed Aggregator API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev / generic specification
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/feed")
async def read_feed(
    platform: Optional[str] = None,
    source_name: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Unified feed with optional filtering and pagination."""
    return get_latest_articles(
        platform=platform,
        source_name=source_name,
        limit=limit,
        offset=offset
    )

@app.get("/sources")
async def read_sources():
    """Returns the raw sources configuration."""
    return config.sources

@app.get("/platforms")
async def list_platforms():
    """Returns distinct platforms with article counts."""
    import sqlite3
    with sqlite3.connect(config.db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT platform, COUNT(*) as count FROM articles GROUP BY platform")
        rows = cursor.fetchall()
    return [dict(row) for row in rows]

@app.get("/health")
async def health_check():
    """Basic health status of the API and database."""
    import os
    db_size = 0
    if os.path.exists(config.db_path):
        db_size = os.path.getsize(config.db_path) / (1024 * 1024) # MB
        
    return {
        "status": "ok",
        "db_path": str(config.db_path),
        "db_size_mb": round(db_size, 2)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
