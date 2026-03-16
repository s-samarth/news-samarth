# System Design Documentation

## 1. Architecture Overview
The system follows a classic **ETL (Extract, Transform, Load)** pattern decoupled from a **REST API** serving layer, with **ChromaDB** as the primary NoSQL database.

### High-Level Flow
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  sources.json│────▶│  Extractors │────▶│  ChromaDB   │────▶│  FastAPI    │
│  (Config)    │     │  (E + T)    │     │  (Storage)  │     │  (Serving)  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

1. **Config**: Master `sources.json` is read by the `config.py` module.
2. **Extraction (E)**: Platform-specific classes in `extractors/` fetch raw data.
3. **Transformation (T)**: Data is normalized into a standard Python `dict` with full content.
4. **Loading (L)**: `chroma_db.py` performs upserts into the ChromaDB database.
5. **Serving**: The FastAPI app in `api/main.py` queries ChromaDB and serves JSON.

---

## 2. Component Hierarchy

### **A. Configuration Manager (`config.py`)**
- Centralized `Config` class.
- Handles `.env` loading using `python-dotenv`.
- Manages paths for both ChromaDB and legacy SQLite.
- Ensures required directories (`db/`, `logs/`) exist on startup.

### **B. Data Layer (`db/chroma_db.py`)**
- **ChromaDB**: Local-first NoSQL document database.
- **Schema**: Document-based with metadata indexing.
- **Deduplication**: URL-based hashing ensures no duplicates.
- **AI-Ready**: Supports vector embeddings for semantic search.

### **C. Extractor Suite (`extractors/`)**
- **Modular Design**: Every platform inherits from `BaseExtractor`.
- **Full Content Storage**: 
  - YouTube: Complete video transcripts
  - Reddit: Full post body + optional comments
  - Substack: Complete newsletter text (HTML stripped)
  - Twitter: Full tweet content (no truncation)
- **Resilience**: Platform isolation ensures failures don't cascade.

### **D. API Layer (`api/main.py`)**
- **Framework**: FastAPI with automatic OpenAPI docs.
- **CORS**: Configured for frontend access.
- **Static File Serving**: Serves frontend from `/frontend/` directory
- **New Endpoints**:
  - `/feed/recent`: Last 24 hours content
  - `/feed/search`: Semantic search (AI-ready)

### **E. Frontend Layer (`frontend/`)**
- **Technology**: Vanilla HTML/CSS/JavaScript (no framework dependencies)
- **Design**: Premium dark theme with Inter font
- **Features**:
  - Platform filtering (Substack, Reddit, YouTube, Twitter/X)
  - Search functionality
  - AI Newsletter generation and viewing
  - Real-time health status
  - Responsive design for mobile
- **Files**:
  - `index.html`: Main HTML structure
  - `styles.css`: Dark theme styling with CSS variables
  - `app.js`: JavaScript for API integration and UI logic

---

## 3. ChromaDB Database Schema

### Collection: `newsfeed`

Each document in ChromaDB represents a single news item:

```python
{
    "id": "sha256_hash_of_url",  # Unique identifier
    "document": "Full content text (transcript/article/tweet/post)",
    "metadata": {
        "platform": "youtube|reddit|substack|twitter",
        "source_name": "Fireship",
        "title": "100 Seconds of AI",
        "url": "https://youtube.com/watch?v=abc123",
        "timestamp": "2024-01-15T10:30:00",
        "media_link": "https://img.youtube.com/...",
        "scraped_at": "2024-01-15T12:00:00"
    }
}
```

### Key Features
- **Full Content**: Complete transcripts, articles, posts stored in `document` field
- **Metadata Indexing**: Efficient filtering by platform, source, timestamp
- **Vector Ready**: Cosine similarity enabled for future semantic search
- **Deduplication**: URL-based hashing prevents duplicates

---

## 4. Data Schema Comparison

### Legacy SQLite (`db/models.py`)
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | PK Auto-increment |
| `platform` | TEXT | Source platform |
| `source_name` | TEXT | Human-readable name |
| `title` | TEXT | Heading |
| `content_text`| TEXT | Full body |
| `url` | TEXT | Unique identifier |
| `timestamp` | TEXT | ISO 8601 |
| `media_link` | TEXT | Image URL |
| `scraped_at` | TEXT | Audit timestamp |

### ChromaDB (`db/chroma_db.py`)
| Field | Location | Description |
|-------|----------|-------------|
| `id` | Document ID | SHA256 hash of URL |
| `document` | Main content | Full content text |
| `platform` | metadata | Source platform |
| `source_name` | metadata | Human-readable name |
| `title` | metadata | Heading |
| `url` | metadata | Original URL |
| `timestamp` | metadata | ISO 8601 |
| `media_link` | metadata | Image URL |
| `scraped_at` | metadata | Audit timestamp |

---

## 5. Error Handling & Recovery

- **Granular Exception Handling**: If a single source fails, the script captures the error and moves to the next.
- **Platform Isolation**: If an entire platform fails, `run_all.py` logs the error and proceeds.
- **Graceful Degradation**: Missing API keys result in skipped platforms, not crashes.
- **Log Rotation**: Logs are written to `logs/extractor.log` for debugging.

---

## 6. AI-Ready Features

### Semantic Search
ChromaDB's built-in vector search enables:
```python
# Search by meaning, not just keywords
GET /feed/search?q=artificial+intelligence+developments
```

### AI Summarization (Implemented)
The system now includes full AI summarization using LangChain/LangGraph:

**Components:**
- `ai/summarizer.py`: LangGraph workflow for daily digest generation
- OpenRouter integration for LLM access
- Full source tracking (platform → source → article)
- Daily summary storage in ChromaDB

**Workflow:**
1. Fetch last 24h articles from ChromaDB
2. Categorize by platform
3. Extract source tracking information
4. Identify key points/themes using LLM
5. Generate comprehensive summary using LLM
6. Store summary with metadata

**API Endpoints:**
- `POST /summarize`: Trigger summarization
- `GET /summary/latest`: Get latest summary
- `GET /summary/{date}`: Get summary by date
- `GET /summary/{date}/sources`: Get source breakdown

### AI Newsletter System (Implemented)
The system now includes a sophisticated 4-agent newsletter generation system:

**Components:**
- `ai/newsletter.py`: LangGraph workflow with 4 specialized agents
- RAG-based deduplication using vector similarity
- AI-powered article ranking (impact, uniqueness, credibility, depth)
- Update tracking for evolving stories
- Full source attribution with ranking scores

**4-Agent Workflow:**
1. **Fetcher Agent**: Retrieves articles and previous newsletters for RAG
2. **Ranker Agent**: Ranks articles by importance using AI criteria
3. **Deduplicator Agent**: Identifies duplicates and updates using RAG
4. **Generator Agent**: Creates professional newsletter with formatting

**API Endpoints:**
- `POST /newsletter/generate`: Trigger newsletter generation
- `GET /newsletter/latest`: Get latest newsletter
- `GET /newsletter/{date}`: Get newsletter by date
- `GET /newsletter/{date}/sources`: Get source tracking with rankings
- `GET /newsletter/{date}/updates`: Get update tracking
- `GET /newsletter/history`: List past newsletters

### Future Enhancements
- **Custom Embeddings**: Add OpenAI/Sentence Transformer embeddings
- **Classification**: Auto-categorize articles by topic
- **Multi-language**: Auto-translate newsletters
- **Email Delivery**: Send newsletters via email

---

## 7. Data Flow Diagram

```
                    ┌─────────────────────────────────────────────────────┐
                    │                   sources.json                      │
                    │  {                                                  │
                    │    "youtube": [{"name": "Fireship", ...}],          │
                    │    "reddit": [{"name": "r/LocalLLaMA", ...}],       │
                    │    ...                                              │
                    │  }                                                  │
                    └─────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Extractors Layer                                    │
├─────────────────┬─────────────────┬─────────────────┬─────────────────────────┤
│ YouTube         │ Reddit          │ Substack        │ Twitter                 │
│ - Full          │ - Full post     │ - Full          │ - Full tweet            │
│   transcripts   │   body          │   newsletter    │   text                  │
│ - API v3        │ - PRAW          │ - RSS feed      │ - twscrape              │
└─────────────────┴─────────────────┴─────────────────┴─────────────────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────────────────────┐
                    │                    ChromaDB                         │
                    │  db/chroma_db/                                     │
                    │  - Document-based storage                          │
                    │  - Full content in "document" field                │
                    │  - Metadata for filtering                          │
                    │  - Vector embeddings ready                         │
                    └─────────────────────────────────────────────────────┘
                                          │
                                          ▼
                    ┌─────────────────────────────────────────────────────┐
                    │                    FastAPI                          │
                    │  - /feed (paginated)                               │
                    │  - /feed/recent (last 24h)                         │
                    │  - /feed/search (semantic)                         │
                    │  - /platforms (stats)                              │
                    └─────────────────────────────────────────────────────┘