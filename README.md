# Newsfeed Aggregator

A highly reliable, personalized daily newsfeed aggregator that scrapes content from Substack, Reddit, YouTube, and Twitter/X into a unified **ChromaDB** (NoSQL) database, served via a FastAPI layer.

## 🚀 Quick Start

1. **Install Dependencies:** `pip install -r requirements.txt`
2. **Install Playwright Browser:** `playwright install chromium`
3. **Setup Env:** Copy `.env.example` to `.env` and add your API keys and Twitter credentials.
4. **Configure Sources:** Add your URLs/handles to `sources.json` using platform-specific schemas.
5. **Run Extraction:** `python scripts/run_all.py`.
6. **Start API:** `python api/main.py`.

### Twitter/X Setup (First Time)
1. Add your burner account credentials to `.env`:
   ```
   TWITTER_USERNAME=your_burner_username
   TWITTER_PASSWORD=your_burner_password
   TWITTER_EMAIL=your_email_for_verification
   ```
2. Run with `headless=False` for initial login debugging:
   ```python
   # In scripts/run_all.py or run_single.py, modify:
   "twitter": TwitterPlaywrightExtractor(headless=False)
   ```
3. After successful login, session persists in `.playwright_twitter_profile/`

## 📚 Detailed Documentation

| Document | Description |
|----------|-------------|
| [📖 Product Overview](docs/product_overview.md) | The "Why" behind the project, features, and target user. |
| [🏗️ System Design](docs/system_design.md) | Technical architecture, data flow, and component breakdown. |
| [👤 User Actions Guide](docs/user_actions.md) | **Complete step-by-step setup guide** - every action needed to run the system. |
| [🛠️ Running Instructions](docs/instructions.md) | Comprehensive guide on setup, configuration, and execution. |
| [🧪 Testing Guide](docs/testing_guide.md) | Complete testing and running guide with step-by-step instructions. |
| [🔄 Reddit RSS Migration](docs/reddit_rss_migration_plan.md) | **Plan to migrate from PRAW to RSS feeds** - eliminates Reddit API credential issues. |
| [🚢 Deployment Guide](docs/deployment.md) | How to schedule runs and host the API. |
| [🎨 Frontend Specs](docs/frontend_spec.md) | Data contracts and prompts for UI generation. |
| [🗄️ ChromaDB Schema](docs/chromadb_schema.md) | Database schema and AI-ready features. |
| [🤖 AI Summarization](docs/ai_summarization.md) | LangChain/LangGraph daily digest generation. |
| [📰 Newsletter System](docs/newsletter_system.md) | AI agent-based newsletter with ranking & RAG. |
| [📡 API Documentation](docs/api_documentation.md) | **Complete REST API reference** - all endpoints, parameters, and examples. |

## 🛠️ Tech Stack

- **Backend:** Python 3.11+
- **Framework:** FastAPI
- **Database:** ChromaDB (NoSQL, AI-ready, local-first)
- **Extractors:** feedparser (Reddit, Substack, YouTube RSS), youtube-transcript-api (YouTube transcripts), Playwright (Twitter/X)
- **AI/LLM:** LangChain, LangGraph, OpenRouter
- **Scheduling:** Crontab (macOS/Linux)

## 🎨 Frontend

A premium dark-themed web interface is included for browsing your newsfeed.

### Features
- **Platform Filtering**: Filter by Substack, Reddit, YouTube, or Twitter/X
- **Search**: Search articles by keywords
- **AI Newsletter**: Generate and view AI-curated newsletters
- **Responsive Design**: Works on desktop and mobile
- **Real-time Updates**: Health status and article counts

### Access
Once the API server is running, open your browser to:
```
http://localhost:8000
```

### Frontend Files
```
frontend/
├── index.html      # Main HTML structure
├── styles.css      # Dark theme styling
└── app.js          # JavaScript functionality
```

## 📁 Directory Structure

```text
.
├── api/                 # FastAPI server and routes
├── db/                  # Database modules (ChromaDB + legacy SQLite)
│   ├── chroma_db.py     # ChromaDB module (primary)
│   └── models.py        # Legacy SQLite models
├── docs/                # Detailed documentation
├── extractors/          # Platform-specific scraping logic
├── frontend/            # Web interface
│   ├── index.html       # Main HTML
│   ├── styles.css       # Styling
│   └── app.js           # JavaScript
├── scripts/             # Orchestration and utility scripts
├── sources.json         # Primary configuration file
├── requirements.txt     # Python dependencies
└── .env.example         # Template for secrets
```

## 🗄️ Database

This project uses **ChromaDB** as the primary database:

- **NoSQL**: Document-based storage, no rigid schema
- **Local-first**: All data stays on your machine
- **AI-ready**: Built-in support for vector embeddings and semantic search
- **Full content storage**: Stores complete transcripts, articles, tweets, and posts

### Database Location
```
db/chroma_db/  # ChromaDB persistent storage
```

## 🤖 AI Features

### Semantic Search
ChromaDB enables powerful AI capabilities:

- **Semantic Search**: Search articles by meaning, not just keywords
- **Vector Embeddings**: Ready for embedding models (OpenAI, Sentence Transformers)
- **LangChain Integration**: Easy integration with AI frameworks

```python
# Example: Semantic search
GET /feed/search?q=artificial+intelligence+developments
```

### AI Summarization (NEW)
Generate daily news digests using LangChain/LangGraph with OpenRouter:

- **Daily Digests**: Automatic summarization of last 24h content
- **Source Tracking**: Full provenance (platform → source → article)
- **Configurable Models**: Use any OpenRouter model (Claude, GPT-4, Llama, etc.)
- **Stored Summaries**: Daily digests saved to ChromaDB

```bash
# Trigger summarization
curl -X POST http://localhost:8000/summarize

# Get latest summary
curl http://localhost:8000/summary/latest
```

### AI Newsletter System (NEW)
Generate professional newsletters using 4-agent LangGraph workflow:

- **AI-Powered Ranking**: Articles ranked by impact, uniqueness, credibility
- **RAG Deduplication**: Identifies duplicates and tracks story updates
- **Source Attribution**: Every story includes full source tracking
- **Newsletter History**: All newsletters stored for retrieval
- **Date-Based Generation**: Generate newsletters for any date in the last 30 days

```bash
# Generate newsletter for today
curl -X POST http://localhost:8000/newsletter/generate

# Two-phase date-based generation
# Phase 1: Fetch articles for specific date
curl -X POST http://localhost:8000/newsletter/fetch \
  -H "Content-Type: application/json" \
  -d '{"date": "2024-01-15"}'

# Phase 2: Generate newsletter (with force option)
curl -X POST http://localhost:8000/newsletter/generate \
  -H "Content-Type: application/json" \
  -d '{"date": "2024-01-15", "force": false}'

# Get latest newsletter
curl http://localhost:8000/newsletter/latest

# Get newsletter with sources
curl http://localhost:8000/newsletter/2024-01-15/sources

# Get update tracking
curl http://localhost:8000/newsletter/2024-01-15/updates
```

See [AI Summarization Docs](docs/ai_summarization.md) and [Newsletter System Docs](docs/newsletter_system.md) for details.

## 📊 API Endpoints

### Feed Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /feed` | Main feed with filtering and pagination |
| `GET /feed/recent` | Last 24 hours content |
| `GET /feed/search` | Semantic search (AI-ready) |
| `GET /sources` | Raw sources configuration |
| `GET /platforms` | Platform statistics |
| `GET /health` | Health check with DB stats |

### AI Summarization Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/summarize` | POST | Trigger AI summarization for last 24h |
| `/summary/latest` | GET | Get latest generated summary |
| `/summary/{date}` | GET | Get summary for specific date (YYYY-MM-DD) |
| `/summary/{date}/sources` | GET | Get source breakdown for date |

### Newsletter Endpoints (AI Agents)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/newsletter/fetch` | POST | Fetch articles for specific date (Phase 1) |
| `/newsletter/generate` | POST | Generate newsletter with date/force support (Phase 2) |
| `/newsletter/latest` | GET | Get latest newsletter |
| `/newsletter/{date}` | GET | Get newsletter by date |
| `/newsletter/{date}/sources` | GET | Get source tracking with rankings |
| `/newsletter/{date}/updates` | GET | Get update tracking |
| `/newsletter/history` | GET | List past newsletters (1-90 days) |

### Admin Endpoints (Database Management)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/health` | GET | Comprehensive database health check with integrity validation |
| `/admin/scan` | GET | Scan articles for data quality issues |
| `/admin/cleanup` | POST | Clean up old articles (dry-run by default for safety) |
| `/admin/cleanup/preview` | GET | Preview what would be deleted without deleting |
| `/admin/articles` | DELETE | Surgically remove specific articles by URL or platform |
| `/admin/backup` | POST | Create timestamped database backup |
| `/admin/backups` | GET | List available backups with metadata |
| `/admin/restore` | POST | Restore database from backup (with pre-restore backup) |
| `/admin/timezone` | GET | Get timezone configuration and current time |

### Environment Variables (New)
| Variable | Default | Description |
|----------|---------|-------------|
| `TIMEZONE` | `local` | Timezone for date calculations (e.g., `UTC`, `America/New_York`) |
| `AUTO_CLEANUP_ENABLED` | `false` | Enable automatic cleanup of old articles |
| `AUTO_CLEANUP_DAYS` | `30` | Number of days to keep articles |
| `AUTO_CLEANUP_ON_STARTUP` | `false` | Run cleanup on server startup |

---
*Created with ⚡ by Anti-Gravity.*
