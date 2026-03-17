# Testing and Running Guide

This guide provides comprehensive instructions for testing and running the Newsfeed Aggregator system, from initial setup to full integration testing.

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Environment Setup](#2-environment-setup)
3. [Configuration Testing](#3-configuration-testing)
4. [Database Testing](#4-database-testing)
5. [Extractor Testing](#5-extractor-testing)
6. [API Testing](#6-api-testing)
7. [Frontend Testing](#7-frontend-testing)
8. [AI Feature Testing](#8-ai-feature-testing)
9. [Integration Testing](#9-integration-testing)
10. [Automated Test Script](#10-automated-test-script)
11. [Manual Testing Checklist](#11-manual-testing-checklist)
12. [Troubleshooting](#12-troubleshooting)
13. [Platform-Specific Schema Reference](#13-platform-specific-schema-reference)

---

## 1. Prerequisites

Before testing, ensure you have:

- **Python 3.11** installed (recommended via Anaconda)
- **API Keys** (optional for full testing):
  - YouTube Data API v3 key
  - OpenRouter API key (for AI features)
- **Git** for cloning the repository

**Note**: Reddit content is accessed via RSS feeds (no API credentials required).

---

## 2. Environment Setup

### Step 1: Create Conda Environment

```bash
# Create environment with Python 3.11
conda create -n newsfeed python=3.11

# Activate environment
conda activate newsfeed
```

### Step 2: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

This installs:
- `chromadb` - NoSQL database for AI-ready content storage
- `fastapi` & `uvicorn` - API server
- `feedparser`, `google-api-python-client`, `twscrape` - Platform extractors
- `langchain`, `langgraph` - AI/LLM frameworks

### Step 3: Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your API keys
# Required for full functionality:
# - YOUTUBE_API_KEY
# - OPENROUTER_API_KEY (for AI features)
```

**Note**: Reddit content is accessed via RSS feeds (no API credentials required).

### Step 4: Configure Sources

Edit `sources.json` to add your favorite creators:

```json
{
  "youtube": [
    {
      "name": "Fireship",
      "channel_id": "UCsBjURrPoezykLs9EqgamOA",
      "max_results": 3,
      "fetch_transcript": true
    }
  ],
  "reddit": [
    {
      "name": "r/LocalLLaMA",
      "rss_url": "https://www.reddit.com/r/LocalLLaMA/.rss",
      "limit": 10
    }
  ],
  "substack": [
    {
      "name": "Example Newsletter",
      "rss_url": "https://example.substack.com/feed"
    }
  ]
}
```

---

## 3. Configuration Testing

### Test 1: Verify Configuration Loads

```bash
python -c "from config import config; print('Config loaded successfully'); print(f'Sources: {config.sources}')"
```

**Expected Output:**
```
Config loaded successfully
Sources: {'youtube': [...], 'reddit': [...], ...}
```

### Test 2: Check Environment Variables

```bash
python -c "
from config import config
print('YouTube API key:', bool(config.youtube_api_key))
print('OpenRouter API key:', bool(config.openrouter_api_key))
"
```

**Expected Output:**
```
YouTube API key: True/False
OpenRouter API key: True/False
```

### Test 3: Verify Directory Structure

```bash
python -c "
from config import config
print('Sources path:', config.sources_path.exists())
print('ChromaDB path:', config.chroma_path.exists())
print('Log directory:', config.log_dir.exists())
"
```

**Expected Output:**
```
Sources path: True
ChromaDB path: True
Log directory: True
```

---

## 4. Database Testing

### Test 4: Initialize ChromaDB

```bash
python -c "
from db.chroma_db import get_chroma_client, get_or_create_collection
client = get_chroma_client()
collection = get_or_create_collection(client)
print(f'ChromaDB initialized: {collection.count()} articles')
"
```

**Expected Output:**
```
ChromaDB initialized: 0 articles
```

### Test 5: Test Database Operations

```bash
python -c "
from db.chroma_db import get_chroma_client, get_or_create_collection, upsert_articles
client = get_chroma_client()
collection = get_or_create_collection(client)

# Test article insertion
test_article = [{
    'id': 'test_123',
    'document': 'Test article content',
    'metadata': {
        'platform': 'test',
        'source_name': 'Test Source',
        'title': 'Test Title',
        'url': 'https://test.com/123',
        'timestamp': '2024-01-15T10:00:00',
        'scraped_at': '2024-01-15T12:00:00'
    }
}]

count = upsert_articles(collection, test_article)
print(f'Inserted {count} test article')

# Verify retrieval
result = collection.get(ids=['test_123'])
print(f'Retrieved: {result[\"documents\"][0][:50]}...')
"
```

**Expected Output:**
```
Inserted 1 test article
Retrieved: Test article content...
```

### Test 6: Test Database Queries

```bash
python -c "
from db.chroma_db import get_chroma_client, get_or_create_collection, get_articles
client = get_chroma_client()
collection = get_or_create_collection(client)

# Test query
result = get_articles(collection, limit=5)
print(f'Query returned {len(result.get(\"articles\", []))} articles')
"
```

---

## 5. Extractor Testing

### Test 7: Test Extractor Imports

```bash
python -c "
from extractors import SubstackExtractor, RedditExtractor, YouTubeExtractor, TwitterExtractor
print('✓ SubstackExtractor imported')
print('✓ RedditExtractor imported')
print('✓ YouTubeExtractor imported')
print('✓ TwitterExtractor imported')
"
```

**Expected Output:**
```
✓ SubstackExtractor imported
✓ RedditExtractor imported
✓ YouTubeExtractor imported
✓ TwitterExtractor imported
```

### Test 8: Test Base Extractor

```bash
python -c "
from extractors.base import BaseExtractor
print('✓ BaseExtractor class available')
print(f'Methods: {[m for m in dir(BaseExtractor) if not m.startswith(\"_\")]}')
"
```

### Test 9: Run Single Platform Extraction

```bash
# Test with Substack (uses RSS, no API key needed)
python scripts/run_single.py --platform substack
```

**Expected Output:**
```
Running substack extractor...
Done. Added X new articles.
```

**Note:** This will only work if you have Substack sources configured in `sources.json` with valid RSS feeds.

### Test 10: Run All Extractors

```bash
python scripts/run_all.py
```

**Expected Output:**
```
============================================================
Starting master newsfeed extraction...
Database location: db/chroma_db
============================================================
Current database contains 0 articles
Running substack extractor...
Finished substack: X fetched, Y new articles added.
Running reddit extractor...
Finished reddit: X fetched, Y new articles added.
Running youtube extractor...
Finished youtube: X fetched, Y new articles added.
Running twitter extractor...
Finished twitter: X fetched, Y new articles added.
============================================================
EXTRACTION SUMMARY
============================================================
Starting articles: 0
Ending articles: Z
New articles added: Z

Platform breakdown:
  substack: X fetched, Y new
  reddit: X fetched, Y new
  youtube: X fetched, Y new
  twitter: X fetched, Y new
============================================================
```

---

## 6. API Testing

### Test 11: Start the API Server

```bash
python api/main.py
```

**Expected Output:**
```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Note:** Keep this terminal running. Open a new terminal for the following tests.

### Test 12: Test Health Endpoint

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "ok",
  "database": "chromadb",
  "db_path": "db/chroma_db",
  "db_size_mb": 0.0,
  "article_count": 0
}
```

### Test 13: Test Feed Endpoints

```bash
# Get main feed
curl http://localhost:8000/feed

# Get feed with pagination
curl "http://localhost:8000/feed?limit=10&offset=0"

# Get feed filtered by platform
curl "http://localhost:8000/feed?platform=youtube"

# Get recent feed (last 24 hours)
curl http://localhost:8000/feed/recent

# Get recent feed filtered by platform
curl "http://localhost:8000/feed/recent?platform=reddit"
```

### Test 14: Test Search Endpoint

```bash
# Semantic search
curl "http://localhost:8000/feed/search?q=artificial+intelligence"

# Search with result limit
curl "http://localhost:8000/feed/search?q=machine+learning&n_results=5"
```

### Test 15: Test Configuration Endpoints

```bash
# Get sources configuration
curl http://localhost:8000/sources

# Get platform statistics
curl http://localhost:8000/platforms
```

**Expected Response for `/platforms`:**
```json
[
  {"platform": "youtube", "count": 45},
  {"platform": "reddit", "count": 120},
  {"platform": "substack", "count": 30},
  {"platform": "twitter", "count": 85}
]
```

### Test 16: Test API Documentation

Open browser to: `http://localhost:8000/docs`

This provides interactive Swagger UI documentation for all endpoints.

---

## 7. Frontend Testing

### Test 17: Access the Web Interface

1. Ensure API server is running
2. Open browser to: `http://localhost:8000`

**Expected Features:**
- Dark-themed interface with Inter font
- Platform filter buttons (All, Substack, Reddit, YouTube, Twitter)
- Search functionality with real-time results
- Article cards with platform badges and timestamps
- AI Newsletter section (if configured)
- Health status indicator showing database stats

### Test 18: Test Frontend Functionality

**Platform Filtering:**
1. Click "YouTube" button
2. Verify only YouTube articles are displayed
3. Click "All" to reset

**Search:**
1. Enter "AI" in search box
2. Press Enter or click search
3. Verify relevant articles are displayed

**Article Display:**
1. Verify article cards show:
   - Platform badge (colored)
   - Source name
   - Title
   - Timestamp (relative)
   - Content preview
   - Link to original

### Test 19: Test Frontend API Integration

Open browser console (F12) and run:

```javascript
// Test API connectivity
fetch('/health')
  .then(r => r.json())
  .then(data => console.log('Health:', data))

// Test feed
fetch('/feed?limit=5')
  .then(r => r.json())
  .then(data => console.log('Feed:', data))

// Test search
fetch('/feed/search?q=test')
  .then(r => r.json())
  .then(data => console.log('Search:', data))
```

---

## 8. AI Feature Testing

**Note:** AI features require an OpenRouter API key configured in `.env`.

### Test 20: Test AI Summarization

```bash
# Trigger summarization
curl -X POST http://localhost:8000/summarize

# Get latest summary
curl http://localhost:8000/summary/latest

# Get summary by date
curl http://localhost:8000/summary/2024-01-15

# Get summary sources
curl http://localhost:8000/summary/2024-01-15/sources
```

**Expected Response for `/summarize`:**
```json
{
  "success": true,
  "id": "summary_2024-01-15",
  "date": "2024-01-15",
  "summary": "## Daily News Digest\n\n### Executive Summary\n...",
  "metadata": {
    "article_count": 25,
    "key_topics": ["AI", "Machine Learning", ...],
    "platforms": ["youtube", "reddit", "substack", "twitter"],
    "generated_at": "2024-01-15T08:00:00",
    "model_used": "anthropic/claude-3.5-sonnet"
  },
  "sources": {
    "youtube": [...],
    "reddit": [...],
    ...
  }
}
```

### Test 21: Test Newsletter Generation

```bash
# Generate newsletter
curl -X POST http://localhost:8000/newsletter/generate

# Get latest newsletter
curl http://localhost:8000/newsletter/latest

# Get newsletter by date
curl http://localhost:8000/newsletter/2024-01-15

# Get newsletter sources
curl http://localhost:8000/newsletter/2024-01-15/sources

# Get newsletter updates
curl http://localhost:8000/newsletter/2024-01-15/updates

# Get newsletter history
curl http://localhost:8000/newsletter/history
```

**Expected Response for `/newsletter/generate`:**
```json
{
  "success": true,
  "id": "newsletter_2024-01-15",
  "date": "2024-01-15",
  "newsletter": "# 📰 Daily AI Newsletter - January 15, 2024\n...",
  "metadata": {
    "date": "2024-01-15",
    "article_count": 20,
    "new_stories_count": 17,
    "updates_count": 3,
    "platforms": ["youtube", "reddit", "substack", "twitter"],
    "generated_at": "2024-01-15T08:00:00",
    "model_used": "anthropic/claude-3.5-sonnet"
  },
  "sources": {
    "youtube": [...],
    "reddit": [...],
    ...
  }
}
```

### Test 22: Test AI Features via Frontend

1. Open browser to `http://localhost:8000`
2. Scroll to "AI Newsletter" section
3. Click "Generate Newsletter" button
4. Verify newsletter is generated and displayed
5. Click "View Latest" to see most recent newsletter

---

## 9. Integration Testing

### Test 23: Full Pipeline Test

```bash
# 1. Clear database (optional)
rm -rf db/chroma_db/

# 2. Run extraction
python scripts/run_all.py

# 3. Start API in background
python api/main.py &
API_PID=$!

# 4. Wait for API to start
sleep 3

# 5. Test endpoints
echo "Testing health endpoint..."
curl http://localhost:8000/health

echo "Testing feed endpoint..."
curl http://localhost:8000/feed/recent

echo "Testing search endpoint..."
curl "http://localhost:8000/feed/search?q=test"

# 6. Test AI features (if API key set)
if [ -n "$OPENROUTER_API_KEY" ]; then
  echo "Testing AI summarization..."
  curl -X POST http://localhost:8000/summarize
  
  echo "Testing newsletter generation..."
  curl -X POST http://localhost:8000/newsletter/generate
fi

# 7. Stop API
kill $API_PID

echo "Integration test complete!"
```

### Test 24: End-to-End Test Script

Create `test_e2e.py`:

```python
#!/usr/bin/env python3
"""
End-to-end test for Newsfeed Aggregator
"""

import sys
import time
import requests
from pathlib import Path

# Add root to path
sys.path.append(str(Path(__file__).resolve().parent))

BASE_URL = "http://localhost:8000"

def test_api_running():
    """Test if API is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_feed_endpoints():
    """Test feed endpoints"""
    print("Testing feed endpoints...")
    
    # Test main feed
    response = requests.get(f"{BASE_URL}/feed")
    assert response.status_code == 200
    print("✓ /feed endpoint works")
    
    # Test recent feed
    response = requests.get(f"{BASE_URL}/feed/recent")
    assert response.status_code == 200
    print("✓ /feed/recent endpoint works")
    
    # Test search
    response = requests.get(f"{BASE_URL}/feed/search?q=test")
    assert response.status_code == 200
    print("✓ /feed/search endpoint works")

def test_config_endpoints():
    """Test configuration endpoints"""
    print("Testing configuration endpoints...")
    
    # Test sources
    response = requests.get(f"{BASE_URL}/sources")
    assert response.status_code == 200
    print("✓ /sources endpoint works")
    
    # Test platforms
    response = requests.get(f"{BASE_URL}/platforms")
    assert response.status_code == 200
    print("✓ /platforms endpoint works")

def test_frontend():
    """Test frontend serving"""
    print("Testing frontend...")
    
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert "Newsfeed" in response.text
    print("✓ Frontend loads correctly")

if __name__ == "__main__":
    print("=" * 60)
    print("Newsfeed Aggregator - End-to-End Test")
    print("=" * 60)
    
    # Check if API is running
    if not test_api_running():
        print("✗ API is not running. Start it with: python api/main.py")
        sys.exit(1)
    
    print("✓ API is running")
    
    try:
        test_feed_endpoints()
        test_config_endpoints()
        test_frontend()
        
        print("=" * 60)
        print("✓ All end-to-end tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
```

Run it:
```bash
# Start API first
python api/main.py &

# Run test
python test_e2e.py

# Stop API
pkill -f "python api/main.py"
```

---

## 10. Automated Test Script

Create `test_system.py` for comprehensive system validation:

```python
#!/usr/bin/env python3
"""
Comprehensive system test for Newsfeed Aggregator
"""

import sys
import json
from pathlib import Path

# Add root to path
sys.path.append(str(Path(__file__).resolve().parent))

def test_config():
    """Test configuration loading"""
    print("Testing configuration...")
    from config import config
    assert config.sources is not None
    assert config.chroma_path.exists()
    assert config.log_dir.exists()
    print("✓ Configuration loaded")

def test_database():
    """Test database initialization"""
    print("Testing database...")
    from db.chroma_db import get_chroma_client, get_or_create_collection
    client = get_chroma_client()
    collection = get_or_create_collection(client)
    print(f"✓ Database initialized with {collection.count()} articles")

def test_extractors():
    """Test extractor initialization"""
    print("Testing extractors...")
    from extractors import SubstackExtractor, RedditExtractor, YouTubeExtractor, TwitterExtractor
    
    extractors = {
        'substack': SubstackExtractor(),
        'reddit': RedditExtractor(),
        'youtube': YouTubeExtractor(),
        'twitter': TwitterExtractor()
    }
    
    for name, extractor in extractors.items():
        assert extractor is not None
        print(f"✓ {name.capitalize()} extractor initialized")

def test_api_imports():
    """Test API module imports"""
    print("Testing API imports...")
    from api.main import app
    assert app is not None
    print("✓ FastAPI app imported")

def test_ai_imports():
    """Test AI module imports"""
    print("Testing AI imports...")
    try:
        from ai.summarizer import NewsSummarizer
        from ai.newsletter import NewsletterGenerator
        print("✓ AI modules imported")
    except ImportError as e:
        print(f"⚠ AI modules not available: {e}")

def test_scripts():
    """Test script imports"""
    print("Testing scripts...")
    from scripts.run_all import run_all
    from scripts.run_single import main
    print("✓ Scripts imported")

if __name__ == "__main__":
    print("=" * 60)
    print("Newsfeed Aggregator - System Test")
    print("=" * 60)
    
    try:
        test_config()
        test_database()
        test_extractors()
        test_api_imports()
        test_ai_imports()
        test_scripts()
        
        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

Run it:
```bash
python test_system.py
```

---

## 11. Manual Testing Checklist

### Core Functionality
- [ ] Configuration loads from `sources.json`
- [ ] Environment variables load from `.env`
- [ ] ChromaDB initializes successfully
- [ ] Each extractor can be imported
- [ ] `run_all.py` executes without errors
- [ ] API server starts on port 8000
- [ ] Frontend loads at `http://localhost:8000`

### API Endpoints
- [ ] `GET /health` returns status
- [ ] `GET /feed` returns articles
- [ ] `GET /feed/recent` returns last 24h content
- [ ] `GET /feed/search` performs semantic search
- [ ] `GET /sources` returns configuration
- [ ] `GET /platforms` returns statistics
- [ ] `POST /summarize` generates summary (requires API key)
- [ ] `GET /summary/latest` returns latest summary
- [ ] `POST /newsletter/generate` generates newsletter (requires API key)
- [ ] `GET /newsletter/latest` returns latest newsletter

### Frontend
- [ ] Dark theme displays correctly
- [ ] Platform filters work
- [ ] Search functionality works
- [ ] Article cards display properly
- [ ] AI Newsletter section visible
- [ ] Health status updates

### AI Features (Requires OpenRouter API Key)
- [ ] Summarization generates daily digest
- [ ] Newsletter generation creates ranked content
- [ ] Source tracking works correctly
- [ ] Update tracking identifies story evolution

---

## 12. Troubleshooting

### Issue: "No module named 'chromadb'"

**Solution:**
```bash
pip install chromadb>=0.4.0
```

### Issue: "OPENROUTER_API_KEY not set"

**Solution:**
- Add to `.env` file: `OPENROUTER_API_KEY=your_key_here`
- Or skip AI feature tests

### Issue: "No articles found"

**Solution:**
- Run extraction first: `python scripts/run_all.py`
- Check `sources.json` has valid sources
- Verify API keys are configured

### Issue: API server won't start

**Solution:**
- Check if port 8000 is already in use: `lsof -i :8000`
- Try different port: `python api/main.py --port 8001`
- Check for import errors in terminal output

### Issue: Twitter extraction fails

**Solution:**
- Twitter API is unstable; this is expected
- Other platforms should still work
- Check `twscrape` repository for updates

### Issue: YouTube transcripts not available

**Solution:**
- Some videos have transcripts disabled
- Extractor falls back to video description
- Check `fetch_transcript: true` in `sources.json`

### Issue: Database locked

**Solution:**
- Ensure only one `run_all.py` runs at a time
- ChromaDB handles concurrency better than SQLite
- Check for zombie processes: `ps aux | grep python`

### Issue: Frontend not loading

**Solution:**
- Verify API server is running
- Check browser console for errors (F12)
- Try hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)

### Issue: CORS errors

**Solution:**
- CORS is configured to allow all origins for local dev
- Check `api/main.py` CORS middleware configuration
- Restart API server after changes

---

## Quick Reference Commands

### Setup
```bash
conda create -n newsfeed python=3.11
conda activate newsfeed
pip install -r requirements.txt
cp .env.example .env
```

### Run Extraction
```bash
python scripts/run_all.py
```

### Start API
```bash
python api/main.py
```

### Test API
```bash
curl http://localhost:8000/health
curl http://localhost:8000/feed
curl http://localhost:8000/feed/recent
```

### Test AI Features
```bash
curl -X POST http://localhost:8000/summarize
curl http://localhost:8000/summary/latest
curl -X POST http://localhost:8000/newsletter/generate
curl http://localhost:8000/newsletter/latest
```

### Access Frontend
```
http://localhost:8000
```

### View API Docs
```
http://localhost:8000/docs
```

---

## Testing Workflow Summary

1. **Setup Environment** → Create conda env, install dependencies
2. **Configure** → Add API keys to `.env`, sources to `sources.json`
3. **Test Components** → Run individual tests for config, database, extractors
4. **Run Extraction** → `python scripts/run_all.py`
5. **Start API** → `python api/main.py`
6. **Test Endpoints** → Use curl or browser to test API
7. **Test Frontend** → Open `http://localhost:8000`
8. **Test AI Features** → Generate summaries and newsletters
9. **Integration Test** → Run full pipeline test
10. **Validate** → Check manual testing checklist

---

*Created with ⚡ by Anti-Gravity.*
