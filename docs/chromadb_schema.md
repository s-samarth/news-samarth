# ChromaDB Schema Documentation

This document describes the ChromaDB database schema used by the Newsfeed Aggregator.

## 1. Overview

ChromaDB is a local-first, AI-ready NoSQL document database. Unlike traditional SQL databases, ChromaDB stores data as documents with flexible metadata, making it ideal for varied content types and AI/ML workflows.

### Key Characteristics
- **Document-based**: No rigid schema, flexible field storage
- **Local-first**: All data stored on your machine at `db/chroma_db/`
- **Vector-ready**: Built-in support for semantic search
- **AI-native**: Seamless integration with LangChain, LlamaIndex

---

## 2. Collection: `newsfeed`

The main collection stores all news articles from all platforms.

### Document Structure

```python
{
    # Document ID (required)
    "id": "a1b2c3d4e5f6...",  # SHA256 hash of URL
    
    # Main content (stored in document field)
    "document": "Full transcript/article/tweet/post text...",
    
    # Metadata for filtering and display
    "metadata": {
        "platform": "youtube",           # Source platform
        "source_name": "Fireship",       # Creator/source name
        "title": "100 Seconds of AI",    # Article title
        "url": "https://youtube.com/...",# Original URL
        "timestamp": "2024-01-15T10:30:00",  # ISO 8601
        "media_link": "https://...",     # Image/thumbnail URL
        "scraped_at": "2024-01-15T12:00:00"  # When extracted
    }
}
```

---

## 3. Field Definitions

### 3.1 Document ID (`id`)

| Property | Value |
|----------|-------|
| Type | String |
| Format | SHA256 hex digest (64 chars) |
| Source | Hash of the article URL |
| Purpose | Unique identifier, deduplication |

**Example:**
```python
import hashlib
url = "https://youtube.com/watch?v=abc123"
doc_id = hashlib.sha256(url.encode()).hexdigest()
# "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
```

### 3.2 Document Content (`document`)

| Property | Value |
|----------|-------|
| Type | String |
| Source | Full content from extractor |
| Purpose | Main searchable content |

**Content by Platform:**

| Platform | Content Stored |
|----------|----------------|
| YouTube | Full video transcript (or description if unavailable) |
| Reddit | Post body (selftext) + optional top comments |
| Substack | Full newsletter text (HTML stripped) |
| Twitter | Complete tweet text |

### 3.3 Metadata Fields

#### `platform`
| Property | Value |
|----------|-------|
| Type | String |
| Values | `"youtube"`, `"reddit"`, `"substack"`, `"twitter"` |
| Indexed | Yes |
| Purpose | Filter by source platform |

#### `source_name`
| Property | Value |
|----------|-------|
| Type | String |
| Example | `"Fireship"`, `"r/LocalLLaMA"`, `"@elonmusk"` |
| Indexed | Yes |
| Purpose | Filter by creator/source |

#### `title`
| Property | Value |
|----------|-------|
| Type | String |
| Example | `"100 Seconds of AI"` |
| Purpose | Display heading |

#### `url`
| Property | Value |
|----------|-------|
| Type | String |
| Format | Valid URL |
| Purpose | Original source link, deduplication reference |

#### `timestamp`
| Property | Value |
|----------|-------|
| Type | String |
| Format | ISO 8601 (`YYYY-MM-DDTHH:MM:SS`) |
| Indexed | Yes |
| Purpose | Sort by date, 24-hour filtering |

#### `media_link`
| Property | Value |
|----------|-------|
| Type | String or null |
| Format | Valid URL |
| Purpose | Thumbnail/image for display |

#### `scraped_at`
| Property | Value |
|----------|-------|
| Type | String |
| Format | ISO 8601 |
| Purpose | Audit trail, when article was extracted |

---

## 4. Indexing

ChromaDB automatically indexes:
- **Document embeddings**: For semantic search (when enabled)
- **Metadata fields**: For efficient filtering

### Collection Configuration
```python
collection = client.get_or_create_collection(
    name="newsfeed",
    metadata={"hnsw:space": "cosine"}  # Cosine similarity for vectors
)
```

---

## 5. Querying

### 5.1 Filter by Platform
```python
results = collection.get(
    where={"platform": "youtube"},
    limit=10
)
```

### 5.2 Filter by Date Range
```python
results = collection.get(
    where={"timestamp": {"$gte": "2024-01-15T00:00:00"}},
    limit=50
)
```

### 5.3 Combined Filters
```python
results = collection.get(
    where={
        "$and": [
            {"platform": "youtube"},
            {"timestamp": {"$gte": "2024-01-15T00:00:00"}}
        ]
    }
)
```

### 5.4 Semantic Search
```python
results = collection.query(
    query_texts=["artificial intelligence developments"],
    n_results=10
)
```

---

## 6. Operations

### 6.1 Insert/Upsert
```python
collection.upsert(
    ids=["doc_id_1"],
    documents=["Full content text"],
    metadata=[{
        "platform": "youtube",
        "source_name": "Fireship",
        "title": "Video Title",
        "url": "https://...",
        "timestamp": "2024-01-15T10:00:00"
    }]
)
```

### 6.2 Delete
```python
collection.delete(ids=["doc_id_1"])
```

### 6.3 Count
```python
total = collection.count()
```

---

## 7. Storage Location

```
db/
└── chroma_db/           # ChromaDB persistent storage
    ├── chroma.sqlite3   # Metadata and index
    ├── index/           # Vector index files
    └── embeddings/      # Embedding data (if enabled)
```

---

## 8. Migration from SQLite

The legacy SQLite database (`db/newsfeed.db`) is still supported for backward compatibility. To migrate:

1. Run extraction with new ChromaDB code
2. Data will be stored in `db/chroma_db/`
3. SQLite data remains for reference
4. Eventually phase out SQLite

---

## 9. AI Integration Examples

### 9.1 LangChain Integration
```python
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

# Connect to existing collection
vectorstore = Chroma(
    client=get_chroma_client(),
    collection_name="newsfeed",
    embedding_function=OpenAIEmbeddings()
)

# Semantic search
results = vectorstore.similarity_search("AI developments", k=10)
```

### 9.2 Custom Embeddings
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

# Add embeddings to documents
embeddings = model.encode(documents)
collection.add(
    ids=ids,
    documents=documents,
    embeddings=embeddings,
    metadatas=metadatas
)
```

---

## 10. Summary Documents

In addition to regular articles, the collection stores AI-generated daily summaries.

### Summary Document Structure

```python
{
    "id": "summary_2024-01-15",  # Date-based ID
    "document": "## Daily News Digest\n\n### Executive Summary\n...",
    "metadata": {
        "type": "summary",  # Distinguishes from articles
        "date": "2024-01-15",
        "article_count": 25,
        "key_topics": '["AI", "Machine Learning", ...]',  # JSON string
        "platforms": '["youtube", "reddit", "substack", "twitter"]',
        "sources_json": "{...}",  # Full source tracking data
        "generated_at": "2024-01-15T08:00:00",
        "model_used": "anthropic/claude-3.5-sonnet"
    }
}
```

### Querying Summaries

```python
# Get all summaries
summaries = collection.get(
    where={"type": "summary"},
    include=["documents", "metadatas"]
)

# Get specific date
summary = collection.get(
    ids=["summary_2024-01-15"],
    include=["documents", "metadatas"]
)
```

### Source Tracking Data

The `sources_json` field contains detailed provenance:

```json
{
  "youtube": [
    {
      "source_name": "Fireship",
      "title": "100 Seconds of AI",
      "url": "https://youtube.com/watch?v=abc",
      "timestamp": "2024-01-15T10:00:00",
      "content_preview": "First 200 chars..."
    }
  ],
  "reddit": [...],
  "substack": [...],
  "twitter": [...]
}
```

---

## 12. Newsletter Documents

In addition to articles and summaries, the collection stores AI-generated newsletters.

### Newsletter Document Structure

```python
{
    "id": "newsletter_2024-01-15",  # Date-based ID
    "document": "# Daily Newsletter\n\n## Top Stories\n...",
    "metadata": {
        "type": "newsletter",  # Distinguishes from articles/summaries
        "date": "2024-01-15",
        "article_count": 50,      # Total articles analyzed
        "new_stories_count": 12,  # New stories selected
        "updates_count": 3,       # Updates to previous stories
        "platforms": '["youtube", "reddit", "substack", "twitter"]',
        "sources_json": "{...}",  # Full source tracking with rankings
        "updates_json": "{...}",  # Update tracking data
        "generated_at": "2024-01-15T08:00:00",
        "model_used": "anthropic/claude-3.5-sonnet"
    }
}
```

### Querying Newsletters

```python
# Get all newsletters
newsletters = collection.get(
    where={"type": "newsletter"},
    include=["documents", "metadatas"]
)

# Get specific date
newsletter = collection.get(
    ids=["newsletter_2024-01-15"],
    include=["documents", "metadatas"]
)
```

### Newsletter Source Tracking

The `sources_json` field includes ranking scores:

```json
{
  "youtube": [
    {
      "source_name": "Fireship",
      "title": "100 Seconds of AI",
      "url": "https://youtube.com/watch?v=abc",
      "timestamp": "2024-01-15T10:00:00",
      "ranking_score": 0.92,
      "ranking_reasons": ["High impact", "Unique angle"]
    }
  ]
}
```

### Update Tracking

The `updates_json` field tracks evolving stories:

```json
{
  "story_key": "ai-regulation-eu",
  "previous_date": "2024-01-14",
  "update_type": "significant_development",
  "changes": "New legislation passed",
  "sources": [...]
}
```

---

## 11. Best Practices

1. **Regular Backups**: Copy `db/chroma_db/` directory periodically
2. **Monitor Size**: Check database size via `/health` endpoint
3. **Clean Old Data**: Use `delete_old_articles()` for maintenance
4. **Test Queries**: Use `/feed/search` endpoint to test semantic search
5. **Summary Storage**: Summaries are stored with `type: "summary"` metadata
