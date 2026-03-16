# AI Summarization Documentation

This document describes the LangChain/LangGraph-based AI summarization system that generates daily news digests from collected articles.

## 1. Overview

The AI summarization system uses:
- **LangChain**: Framework for building LLM applications
- **LangGraph**: Stateful workflow orchestration
- **OpenRouter**: OpenAI-compatible API for accessing various LLM models

### Key Features
- Daily news digest generation
- Full source tracking (platform → source → article)
- Configurable LLM model selection
- Automatic storage in ChromaDB
- REST API endpoints for triggering and retrieving summaries

---

## 2. Architecture

### LangGraph Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  fetch_articles │────▶│   categorize    │────▶│ extract_sources │
│  (Last 24h)     │     │  (By Platform)  │     │  (Tracking)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ store_summary   │◀────│generate_summary │◀────│extract_key_points│
│  (ChromaDB)     │     │    (LLM)        │     │   (Themes)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Workflow States

```python
class SummaryState(TypedDict):
    date: str                           # YYYY-MM-DD
    articles: List[Dict]                # Raw articles from ChromaDB
    categorized: Dict[str, List[Dict]]  # Articles grouped by platform
    sources_tracking: Dict[str, List]   # Detailed source information
    key_points: List[str]               # Extracted themes
    summary: str                        # Generated summary
    metadata: Dict                      # Summary metadata
```

---

## 3. Configuration

### Environment Variables

Add to `.env`:

```env
# AI Summarization (OpenRouter)
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

### Available Models

OpenRouter provides access to many models. Popular options:

| Model | ID | Best For |
|-------|-----|----------|
| Claude 3.5 Sonnet | `anthropic/claude-3.5-sonnet` | High quality summaries |
| GPT-4o | `openai/gpt-4o` | Fast, reliable |
| Llama 3.1 70B | `meta-llama/llama-3.1-70b-instruct` | Open source, cost-effective |
| Mixtral 8x7B | `mistralai/mixtral-8x7b-instruct` | Fast inference |

See [OpenRouter Models](https://openrouter.ai/models) for full list.

---

## 4. Usage

### Python API

```python
from ai.summarizer import NewsSummarizer, summarize_last_24h

# Method 1: Using convenience function
summary = summarize_last_24h()
print(summary["summary"])

# Method 2: Using class directly
summarizer = NewsSummarizer()
summary = summarizer.summarize_last_24h()

# Access source tracking
for platform, articles in summary["sources"].items():
    print(f"\n{platform.upper()}:")
    for article in articles:
        print(f"  - {article['source_name']}: {article['title']}")
```

### REST API

#### Trigger Summarization

```bash
curl -X POST http://localhost:8000/summarize
```

Response:
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

#### Get Latest Summary

```bash
curl http://localhost:8000/summary/latest
```

#### Get Summary by Date

```bash
curl http://localhost:8000/summary/2024-01-15
```

#### Get Source Tracking

```bash
curl http://localhost:8000/summary/2024-01-15/sources
```

Response:
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
        "content_preview": "Full transcript preview..."
      }
    ],
    "reddit": [...],
    "substack": [...],
    "twitter": [...]
  },
  "platforms": ["youtube", "reddit", "substack", "twitter"],
  "total_articles": 25
}
```

---

## 5. Source Tracking

Every summary includes detailed source tracking showing exactly where each piece of content came from.

### Structure

```json
{
  "sources": {
    "youtube": [
      {
        "source_name": "Fireship",
        "title": "Video Title",
        "url": "https://youtube.com/watch?v=...",
        "timestamp": "2024-01-15T10:00:00",
        "content_preview": "First 200 chars of content..."
      }
    ],
    "reddit": [...],
    "substack": [...],
    "twitter": [...]
  }
}
```

### Use Cases
- **Attribution**: Know exactly which sources contributed to the summary
- **Verification**: Click through to original articles
- **Analysis**: Understand content distribution across platforms
- **Debugging**: Trace issues back to specific sources

---

## 6. Summary Storage

Summaries are stored in ChromaDB with special metadata:

```python
{
    "id": "summary_2024-01-15",
    "document": "Full markdown summary...",
    "metadata": {
        "type": "summary",  # Distinguishes from articles
        "date": "2024-01-15",
        "article_count": 25,
        "key_topics": '["AI", "ML", ...]',  # JSON string
        "platforms": '["youtube", "reddit", ...]',
        "sources_json": "{...}",  # Full source tracking
        "generated_at": "2024-01-15T08:00:00",
        "model_used": "anthropic/claude-3.5-sonnet"
    }
}
```

---

## 7. Scheduling Daily Summaries

### Using Crontab (macOS/Linux)

Run summarization daily at 8 AM:

```bash
crontab -e
# Add this line:
0 8 * * * cd /path/to/news-samarth && /path/to/venv/bin/python -c "from ai import summarize_last_24h; summarize_last_24h()"
```

### Using API + Cron

```bash
# Add to crontab
0 8 * * * curl -X POST http://localhost:8000/summarize
```

---

## 8. Customization

### Modifying the Prompt

Edit `ai/summarizer.py` to customize the summary generation:

```python
# In _generate_summary method
prompt = f"""Your custom prompt here...

Articles:
{articles_text}

Your instructions...
"""
```

### Adjusting Workflow

Add or modify nodes in `_build_workflow()`:

```python
def _build_workflow(self) -> StateGraph:
    workflow = StateGraph(SummaryState)
    
    # Add custom node
    workflow.add_node("custom_filter", self._custom_filter)
    
    # Modify edges
    workflow.add_edge("categorize", "custom_filter")
    workflow.add_edge("custom_filter", "extract_sources")
    
    return workflow.compile()
```

---

## 9. Troubleshooting

### "OPENROUTER_API_KEY not set"
- Ensure `.env` file exists with valid API key
- Restart the API server after changing `.env`

### "No articles found"
- Run extraction first: `python scripts/run_all.py`
- Check articles exist: `GET /feed/recent`

### Summary generation fails
- Check OpenRouter API status
- Verify model name is correct
- Check API rate limits

### Slow summarization
- Reduce article limit in `_prepare_articles_for_llm()`
- Use a faster model (e.g., `openai/gpt-4o-mini`)
- Consider caching intermediate results

---

## 10. Cost Considerations

OpenRouter charges per token. Approximate costs:

| Model | Cost per 1M tokens | ~Cost per summary |
|-------|-------------------|-------------------|
| Claude 3.5 Sonnet | $3-15 | $0.05-0.15 |
| GPT-4o | $5-15 | $0.05-0.15 |
| Llama 3.1 70B | $0.40-0.60 | $0.005-0.01 |

**Tips to reduce costs:**
- Use smaller models for testing
- Limit articles processed (currently 50)
- Run summarization once daily, not on-demand