# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personalized daily newsfeed aggregator that scrapes content from Substack, Reddit, YouTube, and Twitter/X into ChromaDB, served via FastAPI. Includes AI-powered summarization and newsletter generation using LangChain/LangGraph with OpenRouter.

## Common Commands

```bash
# Install dependencies (use conda env with Python 3.11+)
pip install -r requirements.txt

# Install Playwright browser (required for Twitter extraction)
playwright install chromium

# Run all extractors (scrape all platforms)
python scripts/run_all.py

# Run a single platform extractor
python scripts/run_single.py --platform youtube  # choices: substack, reddit, youtube, twitter

# Start the API server (serves API + frontend at http://localhost:8000)
python api/main.py

# Run tests
pytest
pytest path/to/test_file.py          # single test file
pytest path/to/test_file.py::test_fn # single test function
```

## Architecture

**Data flow:** `sources.json` → Extractors → ChromaDB → FastAPI → Frontend

### Key Components

- **config.py** — Global `Config` singleton. Loads `sources.json`, env vars (Reddit creds, YouTube API key, OpenRouter key/model). All paths resolve relative to `BASE_DIR`. Includes timezone and cleanup configuration.

- **extractors/** — Platform-specific scrapers inheriting from `BaseExtractor`. Each implements `extract(sources)` returning article dicts with keys: `platform`, `source_name`, `title`, `content_text`, `url`, `timestamp`, `media_link`. The `run()` convenience method extracts and stores to DB. Twitter uses `TwitterPlaywrightExtractor` with Playwright for browser-based extraction with isolated session.

- **db/chroma_db.py** — Primary database layer. Single `"newsfeed"` collection stores articles, summaries, and newsletters, differentiated by `metadata.type` (`"summary"`, `"newsletter"`, or absent for articles). Document IDs are SHA256 of URLs. Uses upsert semantics for deduplication. Uses timezone-aware datetime functions.

- **db/health.py** — Database health check module. Provides `check_database_integrity()`, `scan_for_issues()`, `get_database_stats()`, and `validate_article()` functions for monitoring database quality.

- **db/cleanup.py** — Database cleanup and backup module. Provides `run_cleanup()` (with dry-run mode), `create_backup()`, `list_backups()`, `restore_backup()`, and surgical deletion functions (`delete_article_by_url()`, `delete_articles_by_platform()`).

- **db/timezone_utils.py** — Timezone utilities module. Provides `get_now()`, `get_today()`, `get_24h_ago()`, `normalize_timestamp()`, and other timezone-aware datetime functions. Uses `TIMEZONE` env var (default: 'local').

- **api/main.py** — FastAPI app. Serves REST endpoints and static frontend files from `frontend/`. Initializes ChromaDB client at module level. API docs at `/docs`. Supports date-based newsletter generation with `POST /newsletter/fetch` and `POST /newsletter/generate` endpoints. Includes admin endpoints for database management (`/admin/health`, `/admin/cleanup`, `/admin/backup`, etc.).

- **api/orchestrator.py** — Newsletter orchestration module. Coordinates two-phase date-based newsletter flow: `validate_date()` (30-day check using configured timezone), `fetch_for_date()` (runs all extractors with date filtering), `generate_for_date()` (check-first logic with force option).

- **ai/summarizer.py** — LangGraph workflow (6-node linear graph): fetch → categorize → extract sources → extract key points → generate summary → store. Uses `NewsSummarizer` class with OpenRouter via `ChatOpenAI`.

- **ai/newsletter.py** — 4-agent LangGraph workflow: Fetcher → Ranker → Deduplicator → Generator. Includes RAG-based deduplication against previous newsletters and AI-powered article ranking.

### Database Design

ChromaDB stores everything in one collection. Record types are distinguished by `metadata.type`:
- Articles: no type field, ID = SHA256(url)
- Summaries: `type="summary"`, ID = `summary_YYYY-MM-DD`
- Newsletters: `type="newsletter"`, ID = `newsletter_YYYY-MM-DD`

Complex metadata (lists, nested objects) is stored as JSON strings in metadata fields (`sources_json`, `key_topics`, `platforms`, `updates_json`).

### Environment Variables

Required in `.env` (see `.env.example`):
- `YOUTUBE_API_KEY`
- `TWITTER_USERNAME`, `TWITTER_PASSWORD`, `TWITTER_EMAIL` (for Playwright-based Twitter extraction)
- `OPENROUTER_API_KEY` (for AI features)
- `OPENROUTER_MODEL` (default: `anthropic/claude-3.5-sonnet`)

Optional in `.env`:
- `TIMEZONE` (default: `local`) — Timezone for date calculations (e.g., `UTC`, `America/New_York`)
- `AUTO_CLEANUP_ENABLED` (default: `false`) — Enable automatic cleanup of old articles
- `AUTO_CLEANUP_DAYS` (default: `30`) — Number of days to keep articles
- `AUTO_CLEANUP_ON_STARTUP` (default: `false`) — Run cleanup on server startup

### Note on Legacy Code

`db/models.py` and `extractors/base.py` reference a legacy SQLite backend. The active database layer is `db/chroma_db.py`. `run_single.py` still uses the legacy `init_db`/`run()` path while `run_all.py` uses ChromaDB directly.
