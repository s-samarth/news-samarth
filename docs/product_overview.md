# Product Overview: Newsfeed Aggregator

## 1. The Vision
In an era of algorithmic noise and platform fragmentation, the **Newsfeed Aggregator** is designed for "intentional consumption." It allows users to follow a strictly curated list of creators and communities across diverse platforms without visiting 4+ different apps or being distracted by "recommended" content.

## 2. Key Objectives
- **Zero-Noise**: Only see content from the accounts *you* explicitly add to `sources.json`.
- **Unified Interface**: One feed for videos, newsletters, reddit threads, and tweets.
- **Extreme Reliability**: Built with robust error handling; a failure on one platform (e.g. Twitter API change) never stops other platforms from loading.
- **Low Cost / Zero Cost**: Utilizes free-tiers and open-source scraping tools.
- **Privacy & Ownership**: All data stays in a local SQLite database on your machine.

## 3. Core Features
- **Multi-Platform Support**: Targeted extraction for Substack (RSS), Reddit (API), YouTube (API + Transcripts), and Twitter/X (twscrape).
- **Rich Content Extraction**: Goes beyond links—extracts full text from newsletters and complete transcripts from YouTube videos to enable searchable local archives.
- **Smart Deduping**: Uses URL-based upsert logic so you never see the same post twice, no matter how many times you run the script.
- **Unified API**: A standard JSON structure for all platform content, making it trivial to build or generate a modern frontend.

## 4. Target Audience
- Information workers needing to track specific niche experts.
- Content curators looking for a source-of-truth dashboard.
- Users seeking to escape "infinite scroll" algorithms.

## 5. Future Roadmap
- **Natural Language Search**: Indexing the SQLite `content_text` in a vector DB (like ChromaDB) for semantic search.
- **AI Summarization**: Using local LLMs to summarize long YouTube transcripts or Reddit threads before displaying them.
- **Export to PDF/JSON**: One-click summary generation of the last 24 hours of news.
