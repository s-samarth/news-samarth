# Newsfeed Aggregator

A highly reliable, personalized daily newsfeed aggregator that scrapes content from Substack, Reddit, YouTube, and Twitter/X into a unified **ChromaDB** (NoSQL) database, served via a FastAPI layer.

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
| [🗄️ ChromaDB Schema](docs/chromadb_schema.md) | Database schema and AI-ready features. |
| [🤖 AI Summarization](docs/ai_summarization.md) | LangChain/LangGraph daily digest generation. |
| [📰 Newsletter System](docs/newsletter_system.md) | AI agent-based newsletter with ranking & RAG. |

## 🛠️ Tech Stack

- **Backend:** Python 3.11+
- **Framework:** FastAPI
- **Database:** ChromaDB (NoSQL, AI-ready, local-first)
- **Extractors:** PRAW (Reddit), feedparser (Substack), Google API v3 (YouTube), twscrape (Twitter)
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

```bash
# Generate newsletter
curl -X POST http://localhost:8000/newsletter/generate

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
| `/newsletter/generate` | POST | Generate newsletter with 4-agent workflow |
| `/newsletter/latest` | GET | Get latest newsletter |
| `/newsletter/{date}` | GET | Get newsletter by date |
| `/newsletter/{date}/sources` | GET | Get source tracking with rankings |
| `/newsletter/{date}/updates` | GET | Get update tracking |
| `/newsletter/history` | GET | List past newsletters (1-90 days) |

---
*Created with ⚡ by Anti-Gravity.*