# API Documentation

Complete reference for all REST API endpoints provided by the Newsfeed Aggregator.

## Base URL

```
http://localhost:8000
```

## Interactive Documentation

Swagger UI is available at: `http://localhost:8000/docs`
ReDoc is available at: `http://localhost:8000/redoc`

---

## Table of Contents

1. [Feed Endpoints](#feed-endpoints)
2. [AI Summarization Endpoints](#ai-summarization-endpoints)
3. [Newsletter Endpoints](#newsletter-endpoints)
4. [Admin Endpoints](#admin-endpoints)
5. [Frontend Endpoints](#frontend-endpoints)

---

## Feed Endpoints

### GET /feed

Get unified feed with optional filtering and pagination.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `platform` | string | No | - | Filter by platform: `youtube`, `reddit`, `substack`, `twitter` |
| `source_name` | string | No | - | Filter by source name (e.g., "Fireship") |
| `limit` | integer | No | 50 | Number of results (1-200) |
| `offset` | integer | No | 0 | Results offset for pagination |

**Example Request:**
```bash
curl "http://localhost:8000/feed?platform=youtube&limit=10"
```

**Example Response:**
```json
{
  "total": 45,
  "items": [
    {
      "id": "abc123...",
      "platform": "youtube",
      "source_name": "Fireship",
      "title": "100 Seconds of AI",
      "content_text": "Full transcript...",
      "url": "https://youtube.com/watch?v=abc123",
      "timestamp": "2024-01-15T10:30:00",
      "media_link": "https://img.youtube.com/...",
      "scraped_at": "2024-01-15T12:00:00"
    }
  ]
}
```

---

### GET /feed/recent

Get all articles from the last 24 hours.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `platform` | string | No | - | Filter by platform |
| `source_name` | string | No | - | Filter by source name |

**Example Request:**
```bash
curl http://localhost:8000/feed/recent
curl "http://localhost:8000/feed/recent?platform=reddit"
```

**Example Response:**
```json
{
  "total": 25,
  "items": [
    {
      "id": "def456...",
      "platform": "reddit",
      "source_name": "r/LocalLLaMA",
      "title": "New LLM breakthrough",
      "content_text": "Full post content...",
      "url": "https://reddit.com/r/LocalLLaMA/...",
      "timestamp": "2024-01-15T08:00:00",
      "media_link": "",
      "scraped_at": "2024-01-15T12:00:00"
    }
  ]
}
```

---

### GET /feed/search

Search articles using semantic similarity.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `q` | string | Yes | - | Search query |
| `n_results` | integer | No | 10 | Number of results (1-50) |

**Example Request:**
```bash
curl "http://localhost:8000/feed/search?q=artificial+intelligence&n_results=5"
```

**Example Response:**
```json
{
  "total": 5,
  "items": [
    {
      "id": "ghi789...",
      "platform": "youtube",
      "source_name": "Two Minute Papers",
      "title": "AI Research Update",
      "content_text": "Full content...",
      "url": "https://youtube.com/watch?v=ghi789",
      "timestamp": "2024-01-15T09:00:00",
      "distance": 0.23
    }
  ]
}
```

---

### GET /sources

Get raw sources configuration.

**Example Request:**
```bash
curl http://localhost:8000/sources
```

**Example Response:**
```json
{
  "youtube": [
    {
      "name": "Fireship",
      "channel_id": "UCsBjURrPoezykLs9EqgamOA",
      "max_results": 15,
      "fetch_transcript": true
    }
  ],
  "reddit": [...],
  "substack": [...],
  "twitter": [...]
}
```

---

### GET /platforms

Get platform statistics.

**Example Request:**
```bash
curl http://localhost:8000/platforms
```

**Example Response:**
```json
[
  {"platform": "youtube", "count": 45},
  {"platform": "reddit", "count": 120},
  {"platform": "substack", "count": 30},
  {"platform": "twitter", "count": 15}
]
```

---

### GET /health

Health check endpoint.

**Example Request:**
```bash
curl http://localhost:8000/health
```

**Example Response:**
```json
{
  "status": "ok",
  "database": "chromadb",
  "db_path": "db/chroma_db",
  "db_size_mb": 15.5,
  "article_count": 210
}
```

---

## AI Summarization Endpoints

### POST /summarize

Trigger AI summarization for the last 24 hours.

**Request Body:** None

**Example Request:**
```bash
curl -X POST http://localhost:8000/summarize
```

**Example Response:**
```json
{
  "success": true,
  "id": "summary_2024-01-15",
  "date": "2024-01-15",
  "summary": "## Daily News Digest\n\n### Executive Summary\n...",
  "metadata": {
    "date": "2024-01-15",
    "article_count": 25,
    "key_topics": ["AI", "Machine Learning", "LLMs"],
    "platforms": ["youtube", "reddit", "substack", "twitter"],
    "generated_at": "2024-01-15T08:00:00",
    "model_used": "anthropic/claude-3.5-sonnet"
  },
  "sources": {
    "youtube": [...],
    "reddit": [...]
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "OPENROUTER_API_KEY not set"
}
```

---

### GET /summary/latest

Get the most recent AI-generated summary.

**Example Request:**
```bash
curl http://localhost:8000/summary/latest
```

**Example Response:**
```json
{
  "success": true,
  "id": "summary_2024-01-15",
  "summary": "## Daily News Digest\n...",
  "metadata": {
    "date": "2024-01-15",
    "article_count": 25,
    "key_topics": ["AI", "ML"],
    "platforms": ["youtube", "reddit"],
    "generated_at": "2024-01-15T08:00:00",
    "model_used": "anthropic/claude-3.5-sonnet"
  },
  "sources": {...}
}
```

---

### GET /summary/{date}

Get summary for a specific date.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date` | string | Yes | Date in YYYY-MM-DD format |

**Example Request:**
```bash
curl http://localhost:8000/summary/2024-01-15
```

**Example Response:**
```json
{
  "success": true,
  "id": "summary_2024-01-15",
  "summary": "## Daily News Digest\n...",
  "metadata": {...},
  "sources": {...}
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "No summary found for 2024-01-15"
}
```

---

### GET /summary/{date}/sources

Get source tracking data for a specific summary.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date` | string | Yes | Date in YYYY-MM-DD format |

**Example Request:**
```bash
curl http://localhost:8000/summary/2024-01-15/sources
```

**Example Response:**
```json
{
  "success": true,
  "date": "2024-01-15",
  "sources": {
    "youtube": [
      {
        "source_name": "Fireship",
        "title": "100 Seconds of AI",
        "url": "https://youtube.com/watch?v=abc",
        "timestamp": "2024-01-15T10:00:00"
      }
    ],
    "reddit": [...]
  },
  "platforms": ["youtube", "reddit"],
  "total_articles": 25
}
```

---

## Newsletter Endpoints

### POST /newsletter/fetch

Fetch raw news articles for a specific date from all platforms (Phase 1 of date-based generation).

**Request Body:**
```json
{
  "date": "2024-01-15"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `date` | string | Yes | Target date in YYYY-MM-DD format (within last 30 days) |

**Example Request:**
```bash
curl -X POST http://localhost:8000/newsletter/fetch \
  -H "Content-Type: application/json" \
  -d '{"date": "2024-01-15"}'
```

**Example Response:**
```json
{
  "date": "2024-01-15",
  "overall_status": "success",
  "platforms": {
    "youtube": {"status": "success", "count": 12},
    "reddit": {"status": "success", "count": 8},
    "substack": {"status": "success", "count": 5},
    "twitter": {"status": "failed", "count": 0, "error": "Twitter credentials not configured"}
  },
  "total_articles": 25
}
```

**Status Values:**
- `success`: All platforms fetched successfully
- `partial`: Some platforms failed
- `failed`: All platforms failed

**Error Response:**
```json
{
  "date": "2024-01-15",
  "overall_status": "failed",
  "error": "Date 2024-01-15 is older than 30 days. Only the last 30 days are supported.",
  "platforms": {},
  "total_articles": 0
}
```

---

### POST /newsletter/generate

Generate a newsletter for a specific date (Phase 2 of date-based generation).

**Request Body:**
```json
{
  "date": "2024-01-15",
  "force": false
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `date` | string | No | Today | Target date in YYYY-MM-DD format (within last 30 days) |
| `force` | boolean | No | false | If true, regenerate even if newsletter exists |

**Example Request:**
```bash
# Generate for today
curl -X POST http://localhost:8000/newsletter/generate

# Generate for specific date
curl -X POST http://localhost:8000/newsletter/generate \
  -H "Content-Type: application/json" \
  -d '{"date": "2024-01-15"}'

# Force regenerate
curl -X POST http://localhost:8000/newsletter/generate \
  -H "Content-Type: application/json" \
  -d '{"date": "2024-01-15", "force": true}'
```

**Example Response:**
```json
{
  "success": true,
  "cached": false,
  "id": "newsletter_2024-01-15",
  "date": "2024-01-15",
  "newsletter": "# 📰 Daily AI Newsletter - January 15, 2024\n\n## Executive Summary\n...",
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
    "reddit": [...]
  }
}
```

**Cached Response (when force=false and newsletter exists):**
```json
{
  "success": true,
  "cached": true,
  "id": "newsletter_2024-01-15",
  "date": "2024-01-15",
  "newsletter": "# 📰 Daily AI Newsletter...",
  "metadata": {...},
  "sources": {...}
}
```

---

### GET /newsletter/latest

Get the most recent AI-generated newsletter.

**Example Request:**
```bash
curl http://localhost:8000/newsletter/latest
```

**Example Response:**
```json
{
  "success": true,
  "id": "newsletter_2024-01-15",
  "newsletter": "# 📰 Daily AI Newsletter...",
  "metadata": {
    "date": "2024-01-15",
    "article_count": 20,
    "new_stories_count": 17,
    "updates_count": 3,
    "platforms": ["youtube", "reddit"],
    "generated_at": "2024-01-15T08:00:00",
    "model_used": "anthropic/claude-3.5-sonnet"
  },
  "sources": {...}
}
```

---

### GET /newsletter/{date}

Get newsletter for a specific date.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date` | string | Yes | Date in YYYY-MM-DD format |

**Example Request:**
```bash
curl http://localhost:8000/newsletter/2024-01-15
```

**Example Response:**
```json
{
  "success": true,
  "id": "newsletter_2024-01-15",
  "newsletter": "# 📰 Daily AI Newsletter...",
  "metadata": {...},
  "sources": {...}
}
```

---

### GET /newsletter/{date}/sources

Get source tracking data for a specific newsletter.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date` | string | Yes | Date in YYYY-MM-DD format |

**Example Request:**
```bash
curl http://localhost:8000/newsletter/2024-01-15/sources
```

**Example Response:**
```json
{
  "success": true,
  "date": "2024-01-15",
  "sources": {
    "youtube": [
      {
        "source_name": "Fireship",
        "title": "100 Seconds of AI",
        "url": "https://youtube.com/watch?v=abc",
        "timestamp": "2024-01-15T10:00:00",
        "rank": 1,
        "score": 95
      }
    ],
    "reddit": [...]
  },
  "platforms": ["youtube", "reddit"],
  "total_articles": 20
}
```

---

### GET /newsletter/{date}/updates

Get update tracking data for a specific newsletter.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date` | string | Yes | Date in YYYY-MM-DD format |

**Example Request:**
```bash
curl http://localhost:8000/newsletter/2024-01-15/updates
```

**Example Response:**
```json
{
  "success": true,
  "date": "2024-01-15",
  "updates": [
    {
      "article": {
        "title": "Company X Releases New AI Model",
        "url": "https://..."
      },
      "update_info": {
        "previous_topic": "Company X announced new AI model",
        "what_changed": "Model now publicly available",
        "significance": "Major milestone for accessibility"
      }
    }
  ],
  "update_count": 3
}
```

---

### GET /newsletter/history

Get list of past newsletters.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 30 | Number of days to look back (1-90) |

**Example Request:**
```bash
curl "http://localhost:8000/newsletter/history?limit=7"
```

**Example Response:**
```json
{
  "success": true,
  "total": 7,
  "newsletters": [
    {
      "id": "newsletter_2024-01-15",
      "date": "2024-01-15",
      "article_count": 20,
      "new_stories_count": 17,
      "updates_count": 3,
      "platforms": ["youtube", "reddit"],
      "generated_at": "2024-01-15T08:00:00"
    }
  ]
}
```

---

## Admin Endpoints

### GET /admin/health

Comprehensive database health check with integrity validation.

**Example Request:**
```bash
curl http://localhost:8000/admin/health
```

**Example Response:**
```json
{
  "success": true,
  "integrity": {
    "status": "healthy",
    "article_count": 210,
    "platforms": {
      "youtube": 50,
      "reddit": 80,
      "substack": 50,
      "twitter": 30
    },
    "date_range": {
      "earliest": "2024-01-01T10:00:00",
      "latest": "2024-01-15T18:00:00"
    },
    "issues": [],
    "warnings": ["15 articles are older than 30 days"],
    "checked_at": "2024-01-15T18:30:00"
  },
  "stats": {
    "total_articles": 210,
    "by_platform": {
      "youtube": 50,
      "reddit": 80,
      "substack": 50,
      "twitter": 30
    },
    "by_type": {
      "article": 200,
      "summary": 5,
      "newsletter": 5
    },
    "content_stats": {
      "avg_content_length": 2500,
      "empty_content_count": 0
    }
  },
  "timezone": {
    "configured_timezone": "local",
    "has_pytz": true,
    "current_time": "2024-01-15T18:30:00+05:30",
    "current_date": "2024-01-15",
    "utc_offset": "5:30:00"
  }
}
```

**Status Values:**
- `healthy`: No issues found
- `warning`: Non-critical issues (e.g., old articles)
- `unhealthy`: Critical issues found
- `empty`: Database is empty
- `error`: Error during check

---

### GET /admin/scan

Scan articles for data quality issues.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `sample_size` | integer | No | 100 | Number of articles to sample (1-1000) |

**Example Request:**
```bash
curl "http://localhost:8000/admin/scan?sample_size=50"
```

**Example Response:**
```json
{
  "success": true,
  "total_scanned": 50,
  "valid_count": 47,
  "invalid_count": 3,
  "issues_by_type": {
    "Missing required field": 2,
    "Invalid timestamp format": 1
  },
  "sample_issues": [
    {
      "id": "abc123...",
      "url": "https://example.com/article",
      "issues": ["Missing required field: source_name"]
    }
  ],
  "scanned_at": "2024-01-15T18:30:00"
}
```

---

### POST /admin/cleanup

Clean up old articles from the database.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `days_old` | integer | No | 30 | Delete articles older than this many days |
| `dry_run` | boolean | No | true | Preview without deleting |
| `backup` | boolean | No | true | Create backup before deletion |

**Example Request:**
```bash
# Preview cleanup (dry run)
curl -X POST "http://localhost:8000/admin/cleanup?days_old=30"

# Execute cleanup
curl -X POST "http://localhost:8000/admin/cleanup?days_old=30&dry_run=false"

# Cleanup without backup
curl -X POST "http://localhost:8000/admin/cleanup?days_old=30&dry_run=false&backup=false"
```

**Example Response (Dry Run):**
```json
{
  "success": true,
  "deleted_count": 25,
  "total_before": 210,
  "total_after": 210,
  "days_old": 30,
  "dry_run": true,
  "backup_path": null,
  "cutoff_date": "2023-12-16T18:30:00",
  "articles_to_delete": [
    {
      "id": "abc123...",
      "url": "https://example.com/old-article",
      "platform": "youtube",
      "timestamp": "2023-12-15T10:00:00",
      "title": "Old Article Title"
    }
  ],
  "message": "Dry run: Would delete 25 articles",
  "executed_at": "2024-01-15T18:30:00"
}
```

**Example Response (Actual Cleanup):**
```json
{
  "success": true,
  "deleted_count": 25,
  "total_before": 210,
  "total_after": 185,
  "days_old": 30,
  "dry_run": false,
  "backup_path": "/path/to/db/backups/chroma_backup_20240115_183000.tar.gz",
  "cutoff_date": "2023-12-16T18:30:00",
  "articles_to_delete": [...],
  "message": "Successfully deleted 25 articles",
  "executed_at": "2024-01-15T18:30:00"
}
```

---

### GET /admin/cleanup/preview

Preview what would be deleted by cleanup (always dry-run).

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `days_old` | integer | No | 30 | Delete articles older than this many days |

**Example Request:**
```bash
curl "http://localhost:8000/admin/cleanup/preview?days_old=30"
```

**Example Response:**
```json
{
  "success": true,
  "deleted_count": 25,
  "total_before": 210,
  "total_after": 210,
  "days_old": 30,
  "dry_run": true,
  "cutoff_date": "2023-12-16T18:30:00",
  "articles_to_delete": [...],
  "message": "Dry run: Would delete 25 articles"
}
```

---

### DELETE /admin/articles

Surgically remove specific articles from the database.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | No | Single URL to delete |
| `urls` | string | No | Comma-separated URLs to delete |
| `platform` | string | No | Delete all articles from this platform |
| `confirm` | boolean | Yes | Must be true to actually delete |

**Example Request:**
```bash
# Delete single article
curl -X DELETE "http://localhost:8000/admin/articles?url=https://example.com/bad-article&confirm=true"

# Delete multiple articles
curl -X DELETE "http://localhost:8000/admin/articles?urls=https://example.com/1,https://example.com/2&confirm=true"

# Delete all from platform
curl -X DELETE "http://localhost:8000/admin/articles?platform=twitter&confirm=true"
```

**Example Response:**
```json
{
  "success": true,
  "results": {
    "single_url": {
      "url": "https://example.com/bad-article",
      "deleted": true
    }
  }
}
```

**Error Response (no confirm):**
```json
{
  "success": false,
  "message": "Deletion cancelled - confirm=true required",
  "hint": "Add ?confirm=true to actually delete"
}
```

---

### POST /admin/backup

Create a timestamped backup of the database.

**Example Request:**
```bash
curl -X POST http://localhost:8000/admin/backup
```

**Example Response:**
```json
{
  "success": true,
  "message": "Backup created successfully",
  "backup_path": "/path/to/db/backups/chroma_backup_20240115_183000.tar.gz",
  "backup_name": "chroma_backup_20240115_183000.tar.gz"
}
```

---

### GET /admin/backups

List available database backups.

**Example Request:**
```bash
curl http://localhost:8000/admin/backups
```

**Example Response:**
```json
{
  "success": true,
  "total": 3,
  "backups": [
    {
      "filename": "chroma_backup_20240115_183000.tar.gz",
      "path": "/path/to/db/backups/chroma_backup_20240115_183000.tar.gz",
      "size_mb": 15.5,
      "created_at": "2024-01-15T18:30:00",
      "modified_at": "2024-01-15T18:30:00"
    },
    {
      "filename": "chroma_backup_20240114_183000.tar.gz",
      "path": "/path/to/db/backups/chroma_backup_20240114_183000.tar.gz",
      "size_mb": 14.2,
      "created_at": "2024-01-14T18:30:00",
      "modified_at": "2024-01-14T18:30:00"
    }
  ]
}
```

---

### POST /admin/restore

Restore database from a backup.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `backup_name` | string | Yes | Backup filename to restore |
| `confirm` | boolean | Yes | Must be true to actually restore |

**Example Request:**
```bash
curl -X POST "http://localhost:8000/admin/restore?backup_name=chroma_backup_20240115_183000.tar.gz&confirm=true"
```

**Example Response:**
```json
{
  "success": true,
  "message": "Database restored from chroma_backup_20240115_183000.tar.gz",
  "restored_from": "/path/to/db/backups/chroma_backup_20240115_183000.tar.gz",
  "pre_restore_backup": "/path/to/db/backups/chroma_backup_20240115_190000.tar.gz",
  "executed_at": "2024-01-15T19:00:00"
}
```

**Error Response (no confirm):**
```json
{
  "success": false,
  "message": "Restore cancelled - confirm=True required"
}
```

---

### GET /admin/timezone

Get timezone configuration information.

**Example Request:**
```bash
curl http://localhost:8000/admin/timezone
```

**Example Response:**
```json
{
  "success": true,
  "configured_timezone": "local",
  "has_pytz": true,
  "current_time": "2024-01-15T18:30:00+05:30",
  "current_date": "2024-01-15",
  "utc_offset": "5:30:00",
  "timezone_name": "IST"
}
```

---

## Frontend Endpoints

### GET /

Serve the main frontend page.

**Example Request:**
```bash
curl http://localhost:8000/
```

**Response:** HTML page

---

### GET /static/*

Serve static frontend assets (CSS, JS).

**Example Request:**
```bash
curl http://localhost:8000/static/styles.css
curl http://localhost:8000/static/app.js
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid date format: 'invalid-date'. Expected YYYY-MM-DD."
}
```

### 404 Not Found
```json
{
  "detail": "Not Found"
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

---

## Rate Limiting

Currently, there is no rate limiting implemented. However, be aware of:
- OpenRouter API rate limits for AI features
- YouTube/Reddit RSS feed rate limits for extraction

---

## Authentication

Currently, there is no authentication implemented. All endpoints are publicly accessible when the server is running.

For production deployment, consider adding:
- API key authentication
- Rate limiting
- CORS restrictions

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `YOUTUBE_API_KEY` | No | - | YouTube Data API key (not required for RSS) |
| `TWITTER_USERNAME` | No | - | Twitter/X username for extraction |
| `TWITTER_PASSWORD` | No | - | Twitter/X password for extraction |
| `TWITTER_EMAIL` | No | - | Twitter/X email for verification |
| `OPENROUTER_API_KEY` | Yes (for AI) | - | OpenRouter API key |
| `OPENROUTER_MODEL` | No | `anthropic/claude-3.5-sonnet` | LLM model for summarization |
| `NEWSLETTER_MODEL` | No | `anthropic/claude-3.5-sonnet` | LLM model for newsletter |
| `NEWSLETTER_TOP_N` | No | `20` | Number of articles in newsletter |
| `TIMEZONE` | No | `local` | Timezone for date calculations |
| `AUTO_CLEANUP_ENABLED` | No | `false` | Enable automatic cleanup |
| `AUTO_CLEANUP_DAYS` | No | `30` | Days to keep articles |
| `AUTO_CLEANUP_ON_STARTUP` | No | `false` | Run cleanup on startup |

---

*Created with ⚡ by Anti-Gravity.*