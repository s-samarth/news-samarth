# Newsfeed Aggregator

A highly reliable, personalized daily newsfeed aggregator that scrapes content from Substack, Reddit, YouTube, and Twitter/X into a unified local SQLite database, served via a FastAPI layer.

## 🚀 Quick Start

1. **Install Dependencies:** `pip install -r requirements.txt`
2. **Setup Env:** Copy `.env.example` to `.env` and add your API keys.
3. **Configure Sources:** Add your URLs/handles to `sources.json`.
4. **Initialize Twitter:** `twscrape add_accounts accounts.txt && twscrape login_accounts`.
5. **Run Extraction:** `python scripts/run_all.py`.
6. **Start API:** `python api/main.py`.

## 📚 Detailed Documentation

| Document | Description |
|----------|-------------|
| [📖 Product Overview](docs/product_overview.md) | The "Why" behind the project, features, and target user. |
| [🏗️ System Design](docs/system_design.md) | Technical architecture, data flow, and component breakdown. |
| [🛠️ Running Instructions](docs/instructions.md) | Comprehensive guide on setup, configuration, and execution. |
| [🚢 Deployment Guide](docs/deployment.md) | How to schedule runs and host the API. |
| [🎨 Frontend Specs](docs/frontend_spec.md) | Data contracts and prompts for UI generation. |

## 🛠️ Tech Stack

- **Backend:** Python 3.11+
- **Framework:** FastAPI
- **Database:** SQLite
- **Extractors:** PRAW (Reddit), feedparser (Substack), Google API v3 (YouTube), twscrape (Twitter)
- **Scheduling:** Crontab (macOS/Linux)

## 📁 Directory Structure

```text
.
├── api/                 # FastAPI server and routes
├── db/                  # Database models and SQLite file
├── docs/                # Detailed documentation
├── extractors/          # Platform-specific scraping logic
├── scripts/             # Orchestration and utility scripts
├── sources.json         # Primary configuration file
├── requirements.txt     # Python dependencies
└── .env.example         # Template for secrets
```

---
*Created with ⚡ by Anti-Gravity.*
