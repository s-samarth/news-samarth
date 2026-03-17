# Reddit RSS Migration Plan

## Overview

This document outlines the plan to migrate from PRAW (Reddit API) to RSS feeds for Reddit content extraction. This change eliminates the need for Reddit API credentials, which are now difficult to obtain for new projects.

## Why Migrate?

### Current Issues with PRAW
- Reddit's developer portal is deprecated/outdated
- New API credentials are nearly impossible to obtain
- Requires manual approval that may never come
- Adds unnecessary complexity for personal projects

### Benefits of RSS Approach
- **Zero authentication required** - No API keys needed
- **Uses existing infrastructure** - Already using `feedparser` for Substack
- **Simpler codebase** - Remove PRAW dependency and credential management
- **More reliable** - No API rate limits or authentication issues
- **Free forever** - No costs or quotas

---

## Migration Plan

### Phase 1: Code Changes

#### 1.1 Update `requirements.txt`

**Remove:**
```
praw>=7.7.0
```

**Keep:**
```
feedparser>=6.0.0  # Already exists for Substack
```

#### 1.2 Rewrite `extractors/reddit.py`

**Current:** Uses PRAW with authenticated API access
**New:** Uses feedparser with RSS feeds (similar to Substack extractor)

**Key Changes:**
- Remove `import praw`
- Remove Reddit credentials initialization
- Add `import feedparser` (already in project)
- Change `sources.json` format from subreddit names to RSS URLs
- Parse RSS feed entries instead of PRAW submission objects
- Extract content from RSS `content` or `summary` fields
- Handle Reddit-specific RSS quirks (old.reddit.com fallback)

**New `sources.json` Format:**
```json
{
  "reddit": [
    {
      "name": "r/LocalLLaMA",
      "rss_url": "https://www.reddit.com/r/LocalLLaMA/.rss",
      "limit": 10
    },
    {
      "name": "r/MachineLearning",
      "rss_url": "https://old.reddit.com/r/MachineLearning/.rss",
      "limit": 5
    }
  ]
}
```

**Note:** `sort` and `include_comments` options will be removed as RSS feeds don't support them.

#### 1.3 Update `config.py`

**Remove:**
- `reddit_creds` property
- Reddit environment variable references

**Keep:**
- All other configuration

#### 1.4 Update `.env.example`

**Remove:**
```env
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=
REDDIT_USERNAME=
REDDIT_PASSWORD=
```

#### 1.5 Update `scripts/run_all.py`

**No changes needed** - Already uses generic extractor pattern

#### 1.6 Update `scripts/run_single.py`

**No changes needed** - Already uses generic extractor pattern

---

### Phase 2: Documentation Updates

#### 2.1 Update `README.md`

**Changes:**
- Remove Reddit API credentials from prerequisites
- Update tech stack to remove PRAW
- Update sources.json examples
- Remove Reddit API setup instructions

#### 2.2 Update `docs/user_actions.md`

**Remove:**
- Section 6: "Get Reddit API Credentials" (entire section)
- Reddit credential configuration in Section 9
- Reddit account setup in Section 11

**Update:**
- Section 10: Configure Sources - Update Reddit format
- Section 12: Run Content Extraction - Update examples

#### 2.3 Update `docs/instructions.md`

**Changes:**
- Remove Reddit API setup instructions
- Update sources.json examples
- Remove Reddit credential environment variables

#### 2.4 Update `docs/system_design.md`

**Changes:**
- Update extractor description to mention RSS for Reddit
- Remove PRAW from tech stack
- Update data flow diagrams

#### 2.5 Update `docs/product_overview.md`

**Changes:**
- Update platform support description
- Remove Reddit API references

---

### Phase 3: Testing

#### 3.1 Test RSS Feed Parsing

```bash
# Test individual RSS feeds
python -c "
import feedparser
feed = feedparser.parse('https://www.reddit.com/r/LocalLLaMA/.rss')
print(f'Found {len(feed.entries)} entries')
for entry in feed.entries[:3]:
    print(f'- {entry.title}')
"
```

#### 3.2 Test Reddit Extractor

```bash
# Test new Reddit extractor
python -c "
from extractors.reddit import RedditExtractor
extractor = RedditExtractor()
articles = extractor.extract([{
    'name': 'r/LocalLLaMA',
    'rss_url': 'https://www.reddit.com/r/LocalLLaMA/.rss',
    'limit': 5
}])
print(f'Extracted {len(articles)} articles')
for article in articles[:3]:
    print(f'- {article[\"title\"]}')
"
```

#### 3.3 Test Full Extraction

```bash
# Run full extraction
python scripts/run_all.py
```

#### 3.4 Test API Endpoints

```bash
# Start API
python api/main.py &

# Test endpoints
curl http://localhost:8000/feed?platform=reddit
curl http://localhost:8000/feed/recent?platform=reddit
```

---

## Implementation Details

### New Reddit Extractor Structure

```python
"""
Reddit Extractor Module (RSS-based)

Fetches posts from Reddit subreddits using RSS feeds.
Uses feedparser to parse RSS feeds and extracts full post content.

Features:
    - Fetches posts from configured subreddit RSS feeds
    - No API credentials required
    - Stores complete post body text
    - Handles both www.reddit.com and old.reddit.com URLs
    - Automatic fallback to old.reddit.com if blocked

Example:
    >>> from extractors.reddit import RedditExtractor
    >>> extractor = RedditExtractor()
    >>> articles = extractor.extract([{
    ...     "name": "r/LocalLLaMA",
    ...     "rss_url": "https://www.reddit.com/r/LocalLLaMA/.rss",
    ...     "limit": 5
    ... }])
"""

import feedparser
import re
from typing import List, Dict, Any

from .base import BaseExtractor


class RedditExtractor(BaseExtractor):
    """
    Extractor for Reddit subreddit content via RSS feeds.
    
    Fetches posts from Reddit using RSS feeds without requiring API credentials.
    Uses feedparser (same as Substack extractor) for consistency.
    """
    
    def extract(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract posts from configured subreddit RSS feeds.
        
        For each configured subreddit RSS feed, fetches posts and stores
        the full post content.
        
        Args:
            sources: List of subreddit configurations with keys:
                - name (str): Display name for the source
                - rss_url (str): RSS feed URL (required)
                - limit (int): Max posts to fetch (default: 10)
                
        Returns:
            List of article dictionaries with full content:
            - platform: "reddit"
            - source_name: Display name
            - title: Post title
            - content_text: Full post body
            - url: Reddit permalink
            - timestamp: Publication date (ISO 8601)
            - media_link: Thumbnail URL (if available)
        """
        extracted_articles = []
        
        for source in sources:
            name = source.get("name")
            rss_url = source.get("rss_url")
            limit = source.get("limit", 10)
            
            if not rss_url:
                print(f"Warning: No RSS URL provided for source '{name}', skipping.")
                continue
                
            try:
                articles = self._extract_feed(name, rss_url, limit)
                extracted_articles.extend(articles)
            except Exception as e:
                print(f"Error extracting from Reddit {name}: {e}")
                # Try fallback to old.reddit.com
                if "www.reddit.com" in rss_url:
                    fallback_url = rss_url.replace("www.reddit.com", "old.reddit.com")
                    print(f"Trying fallback: {fallback_url}")
                    try:
                        articles = self._extract_feed(name, fallback_url, limit)
                        extracted_articles.extend(articles)
                    except Exception as e2:
                        print(f"Fallback also failed: {e2}")
                
        return extracted_articles
    
    def _extract_feed(self, name: str, rss_url: str, limit: int) -> List[Dict[str, Any]]:
        """
        Extract posts from a single RSS feed.
        
        Args:
            name: Display name for the source
            rss_url: RSS feed URL
            limit: Maximum posts to fetch
            
        Returns:
            List of article dictionaries
        """
        articles = []
        feed = feedparser.parse(rss_url)
        
        # Limit entries
        entries = feed.entries[:limit]
        
        for entry in entries:
            # Extract full content
            content = self._extract_content(entry)
            
            # Extract thumbnail
            media_link = self._extract_thumbnail(entry)
            
            # Extract timestamp
            timestamp = entry.get("published", "")
            
            articles.append({
                "platform": "reddit",
                "source_name": name,
                "title": entry.get("title"),
                "content_text": content,
                "url": entry.get("link"),
                "timestamp": timestamp,
                "media_link": media_link
            })
            
        return articles
    
    def _extract_content(self, entry) -> str:
        """
        Extract full post content from RSS entry.
        
        Tries content field first (full post), then falls back to summary.
        Strips HTML tags for clean text storage.
        
        Args:
            entry: feedparser entry object
            
        Returns:
            Clean post text
        """
        content = ""
        
        # Try full content first
        if hasattr(entry, "content") and entry.content:
            content = entry.content[0].value
        # Fall back to summary
        elif hasattr(entry, "summary"):
            content = entry.summary
        
        # Strip HTML tags for clean text
        if content:
            content = re.sub(r'<[^<]+?>', '', content)
            # Clean up extra whitespace
            content = re.sub(r'\n\s*\n', '\n\n', content)
            content = content.strip()
        
        return content if content else entry.get("title", "")
    
    def _extract_thumbnail(self, entry) -> str:
        """
        Extract thumbnail image URL from RSS entry.
        
        Checks multiple possible locations for thumbnail:
        - media_thumbnail field
        - enclosure links with image type
        
        Args:
            entry: feedparser entry object
            
        Returns:
            Thumbnail URL or None
        """
        # Check media_thumbnail field
        if "media_thumbnail" in entry and entry.media_thumbnail:
            return entry.media_thumbnail[0].get("url")
        
        # Check enclosure links
        if "links" in entry:
            for link in entry.links:
                if "image" in link.get("type", ""):
                    return link.get("href")
        
        return None
```

---

## RSS Feed URL Formats

### Standard Format
```
https://www.reddit.com/r/{subreddit}/.rss
```

### Examples
- Hot posts: `https://www.reddit.com/r/LocalLLaMA/.rss`
- New posts: `https://www.reddit.com/r/LocalLLaMA/new/.rss`
- Top posts: `https://www.reddit.com/r/LocalLLaMA/top/.rss?t=day`

### Fallback Format (if blocked)
```
https://old.reddit.com/r/{subreddit}/.rss
```

### User Feeds
```
https://www.reddit.com/user/{username}/.rss
```

---

## Limitations of RSS Approach

### What We Lose
1. **Sort options** - RSS feeds don't support custom sorting
2. **Comment inclusion** - RSS doesn't include comments
3. **Vote counts** - No upvote/downvote data
4. **Rich metadata** - Less metadata than PRAW API

### What We Gain
1. **No authentication** - Zero setup required
2. **No rate limits** - No API quotas
3. **Simpler code** - Less complexity
4. **More reliable** - No API changes to worry about
5. **Free forever** - No costs

### Workarounds
- **Sorting**: Use different RSS endpoints (hot, new, top)
- **Comments**: Could add separate comment fetching if needed
- **Metadata**: RSS provides sufficient data for news aggregation

---

## Migration Checklist

### Code Changes
- [ ] Update `requirements.txt` - Remove `praw`
- [ ] Rewrite `extractors/reddit.py` - Use feedparser
- [ ] Update `config.py` - Remove Reddit credentials
- [ ] Update `.env.example` - Remove Reddit variables
- [ ] Update `extractors/__init__.py` - No changes needed

### Documentation Updates
- [ ] Update `README.md` - Remove Reddit API setup
- [ ] Update `docs/user_actions.md` - Remove Reddit credential steps
- [ ] Update `docs/instructions.md` - Update sources.json examples
- [ ] Update `docs/system_design.md` - Update architecture
- [ ] Update `docs/product_overview.md` - Update platform description
- [ ] Update `docs/testing_guide.md` - Update test examples

### Testing
- [ ] Test RSS feed parsing
- [ ] Test Reddit extractor with new format
- [ ] Test full extraction pipeline
- [ ] Test API endpoints with Reddit content
- [ ] Test frontend with Reddit articles

### Configuration Updates
- [ ] Update `sources.json` - Change Reddit format to RSS URLs
- [ ] Remove Reddit credentials from `.env`

---

## Timeline

### Immediate (Today)
1. Rewrite `extractors/reddit.py`
2. Update `requirements.txt`
3. Update `config.py`
4. Update `.env.example`

### Short Term (This Week)
1. Update all documentation
2. Test thoroughly
3. Update `sources.json` examples

### Long Term (Optional)
1. Add comment fetching capability
2. Add more RSS feed options
3. Add feed validation

---

## Rollback Plan

If RSS approach doesn't work:

1. Keep PRAW code in a separate branch
2. Revert `requirements.txt` changes
3. Restore Reddit credentials in config
4. Switch back to PRAW extractor

---

## Success Criteria

### Must Have
- [ ] Reddit content extraction works without API keys
- [ ] Full post content is captured
- [ ] RSS feeds parse correctly
- [ ] Fallback to old.reddit.com works
- [ ] All existing functionality preserved

### Nice to Have
- [ ] Comment inclusion (if needed)
- [ ] Multiple sort options
- [ ] Better error handling

---

## Conclusion

Migrating from PRAW to RSS feeds is a **necessary and beneficial change** that:

1. **Eliminates** the Reddit API credential problem
2. **Simplifies** the codebase
3. **Uses existing** feedparser infrastructure
4. **Provides** reliable, free access to Reddit content
5. **Maintains** all core functionality

The migration is straightforward and low-risk, as we're already using the same approach for Substack.

---

*Created with ⚡ by Anti-Gravity.*
