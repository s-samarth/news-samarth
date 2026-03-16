# System Design Documentation

## 1. Architecture Overview
The system follows a classic **ETL (Extract, Transform, Load)** pattern decoupled from a **REST API** serving layer.

### High-Level Flow
1. **Config**: Master `sources.json` is read by the `config.py` module.
2. **Extraction (E)**: Platform-specific classes in `extractors/` fetch raw data.
3. **Transformation (T)**: Data is normalized into a standard Python `dict` matching the database schema.
4. **Loading (L)**: `db/models.py` performs an `INSERT OR IGNORE` into the SQLite database.
5. **Serving**: The FastAPI app in `api/main.py` queries the database and serves JSON to the client.

## 2. Component Hiearchy

### **A. Configuration Manager (`config.py`)**
- Centralized `Config` class.
- Handles `.env` loading using `python-dotenv`.
- Ensures required directories (`db/`, `logs/`) exist on startup.

### **B. Data Layer (`db/models.py`)**
- **SQLite**: Optimal for low-volume, local storage.
- **Schema**: Unique index on `url` column enforces global deduplication.
- **Concurrency**: SQLite's write-locking is managed by the sequential nature of the `run_all.py` script.

### **C. Extractor Suite (`extractors/`)**
- **Modular Design**: Every platform inherits from `BaseExtractor`.
- **Resilience**: 
    - Substack uses `feedparser` which handles malformed RSS gracefully.
    - Reddit uses `PRAW` with a dedicated `User-Agent`.
    - YouTube uses `google-api-python-client` with a fallback from transcripts to descriptions.
    - Twitter uses `twscrape` (async) wrapped in a synchronous bridge for architectural consistency.

### **D. API Layer (`api/main.py`)**
- **Framework**: FastAPI (Pydantic models for future strict typing).
- **CORS**: Configured to allow cross-origin requests from modern frontend generators (Lovable/Vite).

## 3. Data Schema (Articles Table)

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | PK Auto-increment |
| `platform` | TEXT | Source platform (reddit, substack, etc.) |
| `source_name` | TEXT | Human-readable name (e.g. '@elonmusk') |
| `title` | TEXT | Heading or Tweet summary |
| `content_text`| TEXT | Full body (newsletter text, transcript, or selftext) |
| `url` | TEXT | **Unique Identifier** (Deduplication key) |
| `timestamp` | TEXT | Original publication date (ISO 8601) |
| `media_link` | TEXT | Image url for cards |
| `scraped_at` | TEXT | Internal audit-log of when item was added |

## 4. Error Handling & Recovery
- **Granular Exception Handling**: If a single Subreddit fails, the script captures the error and moves to the next Subreddit in the list.
- **Platform Isolation**: If an entire platform (e.g. Twitter) fails, the `run_all.py` script logs the error and proceeds to the next platform.
- **Log Rotation**: Logs are written to `logs/extractor.log` for debugging failed runs.
