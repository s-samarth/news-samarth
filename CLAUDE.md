# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personalized daily newsfeed aggregator that scrapes content from Substack, Reddit, YouTube, and Twitter/X into ChromaDB, served via FastAPI. Includes AI-powered summarization and newsletter generation using LangChain/LangGraph with OpenRouter.

## Common Commands

```bash
# Install dependencies (use conda env with Python 3.11+)
pip install -r requirements.txt

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

- **config.py** — Global `Config` singleton. Loads `sources.json`, env vars (Reddit creds, YouTube API key, OpenRouter key/model). All paths resolve relative to `BASE_DIR`.

- **extractors/** — Platform-specific scrapers inheriting from `BaseExtractor`. Each implements `extract(sources)` returning article dicts with keys: `platform`, `source_name`, `title`, `content_text`, `url`, `timestamp`, `media_link`. The `run()` convenience method extracts and stores to DB.

- **db/chroma_db.py** — Primary database layer. Single `"newsfeed"` collection stores articles, summaries, and newsletters, differentiated by `metadata.type` (`"summary"`, `"newsletter"`, or absent for articles). Document IDs are SHA256 of URLs. Uses upsert semantics for deduplication.

- **api/main.py** — FastAPI app. Serves REST endpoints and static frontend files from `frontend/`. Initializes ChromaDB client at module level. API docs at `/docs`.

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
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USERNAME`, `REDDIT_PASSWORD`
- `YOUTUBE_API_KEY`
- `OPENROUTER_API_KEY` (for AI features)
- `OPENROUTER_MODEL` (default: `anthropic/claude-3.5-sonnet`)

### Note on Legacy Code

`db/models.py` and `extractors/base.py` reference a legacy SQLite backend. The active database layer is `db/chroma_db.py`. `run_single.py` still uses the legacy `init_db`/`run()` path while `run_all.py` uses ChromaDB directly.
