# Product Overview: Newsfeed Aggregator

## 1. The Vision
In an era of algorithmic noise and platform fragmentation, the **Newsfeed Aggregator** is designed for "intentional consumption." It allows users to follow a strictly curated list of creators and communities across diverse platforms without visiting 4+ different apps or being distracted by "recommended" content.

## 2. Key Objectives
- **Zero-Noise**: Only see content from the accounts *you* explicitly add to `sources.json`.
- **Unified Interface**: One feed for videos, newsletters, reddit threads, and tweets.
- **Extreme Reliability**: Built with robust error handling; a failure on one platform (e.g. Twitter API change) never stops other platforms from loading.
- **Low Cost / Zero Cost**: Utilizes free-tiers and open-source scraping tools.
- **Privacy & Ownership**: All data stays in a local ChromaDB database on your machine.
- **AI-Ready**: NoSQL document storage enables semantic search, embeddings, and AI integrations.
- **Platform-Specific Schemas**: Each platform has its own configuration structure tailored to its data format.

## 3. Core Features

### Multi-Platform Support
Targeted extraction for:
- **Substack** (RSS): Full newsletter text
- **Reddit** (RSS): Complete post body (no API credentials required)
- **YouTube** (API + Transcripts): Full video transcripts
- **Twitter/X** (twscrape): Complete tweet content

### Rich Content Extraction
Goes beyond links—extracts:
- Full text from newsletters
- Complete transcripts from YouTube videos
- Full Reddit post bodies
- Entire tweet content

This enables searchable local archives for research and analysis.

### Smart Deduping
Uses URL-based upsert logic so you never see the same post twice, no matter how many times you run the script.

### Unified API
A standard JSON structure for all platform content, making it trivial to build or generate a modern frontend.

### 24-Hour Content Retrieval
New `/feed/recent` endpoint provides all content from the last 24 hours, perfect for daily digests.

## 4. AI-Ready Architecture

### Why ChromaDB?
We use ChromaDB as our NoSQL database because it's:
- **Local-first**: All data stays on your machine
- **Document-based**: Flexible schema for varied content types
- **Vector-ready**: Built-in support for semantic search
- **AI-native**: Seamless integration with LangChain, LlamaIndex, and other AI frameworks

### Semantic Search
Search articles by meaning, not just keywords:
```
GET /feed/search?q=artificial+intelligence+developments
```

### AI Features (Implemented)
- **AI Summarization**: Daily news digests using LangChain/LangGraph with OpenRouter
- **AI Newsletter**: 4-agent workflow with ranking, deduplication, and source tracking
- **RAG Deduplication**: Vector similarity search for identifying duplicate stories
- **Update Tracking**: Tracks evolving stories and shows what changed
- **Source Attribution**: Full provenance tracking (platform → source → article)

### Future AI Features
- **Custom Embeddings**: Add OpenAI/Sentence Transformer embeddings
- **Content Classification**: Auto-categorize articles by topic
- **RAG Applications**: Use as vector store for retrieval-augmented generation

## 5. Target Audience
- **Information workers** needing to track specific niche experts.
- **Content curators** looking for a source-of-truth dashboard.
- **Researchers** building knowledge bases from diverse sources.
- **AI/ML practitioners** wanting structured data for model training.
- **Users seeking to escape** "infinite scroll" algorithms.

## 6. Data Storage

### What Gets Stored
| Platform | Content Stored |
|----------|----------------|
| YouTube | Full video transcripts (when available) |
| Reddit | Complete post body + optional top comments |
| Substack | Full newsletter text (HTML stripped) |
| Twitter | Complete tweet content (no truncation) |

### Database Location
```
db/chroma_db/  # ChromaDB persistent storage
```

### Storage Efficiency
- ~1-5 KB per article (text only)
- Automatic deduplication
- Grows with each extraction run

## 7. Current Status & Roadmap

### Implemented Features
- ✅ **Frontend Dashboard**: Dark-themed web UI with platform filtering and search
- ✅ **AI Summarization**: Daily news digests using LangChain/LangGraph
- ✅ **AI Newsletter**: 4-agent workflow with ranking and RAG deduplication
- ✅ **Semantic Search**: ChromaDB-powered search capabilities
- ✅ **Source Attribution**: Full provenance tracking for all content

### Future Roadmap

#### Short Term
- **Mobile App**: Native iOS/Android apps
- **Email Digests**: Daily/weekly email summaries
- **Custom Embeddings**: Add OpenAI/Sentence Transformer embeddings

#### Medium Term
- **Content Recommendations**: AI-powered suggestions based on reading history
- **Content Classification**: Auto-categorize articles by topic
- **Collaborative Curation**: Share feeds with team members

#### Long Term
- **Multi-language Support**: Auto-translate content from any language
- **Voice Integration**: "Hey AI, what's new in AI research today?"
- **Export to PDF/JSON**: One-click summary generation

### Long Term
- **Multi-language Support**: Auto-translate content from any language
- **Voice Integration**: "Hey AI, what's new in AI research today?"
- **Collaborative Curation**: Share feeds with team members
- **Export to PDF/JSON**: One-click summary generation

## 8. Competitive Advantages

| Feature | Newsfeed Aggregator | Traditional RSS | Social Media |
|---------|---------------------|-----------------|--------------|
| Full content storage | ✅ | ❌ | ❌ |
| AI-ready database | ✅ | ❌ | ❌ |
| Semantic search | ✅ | ❌ | ❌ |
| No algorithm | ✅ | ✅ | ❌ |
| Local privacy | ✅ | ✅ | ❌ |
| Multi-platform | ✅ | ✅ | ❌ |
| Transcript extraction | ✅ | ❌ | ❌ |

## 9. Technical Highlights

- **Modular Architecture**: Easy to add new platforms
- **Resilient Design**: Platform isolation prevents cascading failures
- **Well-Documented**: Comprehensive docs for every component
- **Type-Safe**: Python type hints throughout
- **Async Support**: Efficient Twitter extraction with async/await