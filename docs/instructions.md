# Running Instructions

Follow this guide to get your Newsfeed Aggregator up and running for the first time.

## 1. Prerequisites
- Python 3.11 or higher.
- `pip` (Python package installer).

## 2. Installation
1.  **Clone the Repository**:
    ```bash
    git clone <your-repo-link>
    cd news-samarth
    ```
2.  **Create a Virtual Environment** (Highly Recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    
    This installs all required packages including:
    - `chromadb` - NoSQL database for AI-ready content storage
    - `fastapi` & `uvicorn` - API server
    - `feedparser`, `google-api-python-client`, `twscrape` - Platform extractors

## 3. Configuration

### A. Environment Variables (`.env`)
Copy the template and fill in your keys:
```bash
cp .env.example .env
```

Required API keys:
- **YouTube**: Create a project in [Google Cloud Console](https://console.cloud.google.com/), enable **YouTube Data API v3**, and generate an API key.
- **OpenRouter** (Optional): For AI summarization and newsletter features. Get an API key at [openrouter.ai](https://openrouter.ai).

**Note**: Reddit content is accessed via RSS feeds (no API credentials required).

### B. Targets (`sources.json`)
Open `sources.json` and add your favorite creators using platform-specific schemas. Each platform has its own configuration structure:

```json
{
  "youtube": {
    "_schema": "YouTube channels require channel_id (not username), max_results limit, and transcript fetching option",
    "_required_fields": ["name", "channel_id"],
    "_optional_fields": ["max_results", "fetch_transcript"],
    "sources": [
      {
        "name": "Fireship",
        "channel_id": "UCsBjURrPoezykLs9EqgamOA",
        "max_results": 3,
        "fetch_transcript": true
      }
    ]
  },
  "reddit": {
    "_schema": "Reddit subreddits use RSS feeds (no API credentials required). Supports sort options via different RSS endpoints.",
    "_required_fields": ["name", "subreddit"],
    "_optional_fields": ["sort", "limit"],
    "sources": [
      {
        "name": "r/LocalLLaMA",
        "subreddit": "LocalLLaMA",
        "sort": "hot",
        "limit": 10
      }
    ]
  },
  "substack": {
    "_schema": "Substack newsletters use RSS feeds. URL must end with /feed",
    "_required_fields": ["name", "rss_url"],
    "sources": [
      {
        "name": "Stratechery",
        "rss_url": "https://stratechery.com/feed"
      }
    ]
  },
  "twitter": {
    "_schema": "Twitter/X accounts use twscrape library (no official API). Requires account setup via twscrape CLI.",
    "_required_fields": ["name", "handle"],
    "_optional_fields": ["max_tweets"],
    "sources": [
      {
        "name": "@elonmusk",
        "handle": "elonmusk",
        "max_tweets": 10
      }
    ]
  }
}
```

**Important**:
- Each platform has its own schema with required and optional fields
- Use the correct `channel_id` for YouTube (not the username)
- Substack requires the direct RSS link (usually `yoursite.substack.com/feed`)
- Reddit uses RSS feeds (no API credentials required). Use `https://www.reddit.com/r/{subreddit}/.rss` format
- Set `fetch_transcript: true` for YouTube to get full video transcripts
- See the [Testing Guide](testing_guide.md#13-platform-specific-schema-reference) for detailed schema documentation

## 4. Twitter/X Account Setup
The `twscrape` library uses a pool of accounts rather than an official API.
1. Create `accounts.txt` with this format: `username:password:email:email_password`
2. Run these commands:
   ```bash
   twscrape add_accounts accounts.txt
   twscrape login_accounts
   ```
   *Note: Using a dummy/throwaway account is recommended.*

## 5. Running the System

### Manual Extraction
To run a full sweep across all platforms:
```bash
python scripts/run_all.py
```

This will:
1. Initialize ChromaDB connection
2. Fetch content from all configured platforms
3. Store full content (transcripts, articles, posts) in `db/chroma_db/`
4. Log summary statistics

To test a single platform (e.g., just Reddit):
```bash
python scripts/run_single.py --platform reddit
```

### Starting the API & Frontend
Start the server to serve the content and frontend:
```bash
python api/main.py
```

The API will be available at `http://localhost:8000`. 
- **Frontend**: Open `http://localhost:8000` in your browser
- **API Docs**: Interactive docs at `http://localhost:8000/docs`

## 6. API Endpoints

### Feed Endpoints
| Endpoint | Description | Example |
|----------|-------------|---------|
| `GET /feed` | Main feed with pagination | `/feed?platform=youtube&limit=10` |
| `GET /feed/recent` | Last 24 hours content | `/feed/recent` |
| `GET /feed/search` | Semantic search | `/feed/search?q=AI+developments` |
| `GET /sources` | Raw configuration | `/sources` |
| `GET /platforms` | Platform statistics | `/platforms` |
| `GET /health` | Health check | `/health` |

### AI Summarization Endpoints (Requires OpenRouter)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/summarize` | POST | Generate daily news digest |
| `/summary/latest` | GET | Get latest summary |
| `/summary/{date}` | GET | Get summary by date |
| `/summary/{date}/sources` | GET | Get source breakdown |

### Newsletter Endpoints (Requires OpenRouter)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/newsletter/generate` | POST | Generate AI newsletter |
| `/newsletter/latest` | GET | Get latest newsletter |
| `/newsletter/{date}` | GET | Get newsletter by date |
| `/newsletter/{date}/sources` | GET | Get source tracking |
| `/newsletter/{date}/updates` | GET | Get update tracking |
| `/newsletter/history` | GET | List past newsletters |

## 7. Database

### ChromaDB Location
```
db/chroma_db/  # All data stored here
```

### What Gets Stored
- **YouTube**: Full video transcripts (when available)
- **Reddit**: Complete post body + optional comments
- **Substack**: Full newsletter text (HTML stripped)
- **Twitter**: Complete tweet content

### Database Size
ChromaDB stores data efficiently. Expect:
- ~1-5 KB per article (text only)
- Database grows with each extraction run
- No duplicates (URL-based deduplication)

## 8. Troubleshooting

### Missing Data
Check `logs/extractor.log` for platform-specific errors.

### Database Locked
ChromaDB handles concurrency better than SQLite, but ensure only one `run_all.py` runs at a time.

### Twitter Failures
Twitter frequently updates its internal API; if `twscrape` fails, check their [official repo](https://github.com/vladkens/twscrape) for updates.

### YouTube Transcripts Not Available
Some videos have transcripts disabled. The extractor falls back to video description.

### ChromaDB Import Error
Ensure you've installed chromadb:
```bash
pip install chromadb>=0.4.0
```

## 9. Scheduling (Optional)

### Using Crontab (macOS/Linux)
Run extraction daily at 8 AM:
```bash
crontab -e
# Add this line:
0 8 * * * cd /path/to/news-samarth && /path/to/venv/bin/python scripts/run_all.py
```

### Using Task Scheduler (Windows)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily, 8 AM)
4. Set action: Start program → `python.exe` with argument `scripts/run_all.py`