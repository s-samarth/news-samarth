# User Actions Guide

This guide provides **every single step** you need to perform to set up and run the Newsfeed Aggregator. Follow these steps in order—do not skip any.

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Install Python 3.11](#2-install-python-311)
3. [Clone the Repository](#3-clone-the-repository)
4. [Create Conda Environment](#4-create-conda-environment)
5. [Install Dependencies](#5-install-dependencies)
6. [Get OpenRouter API Key](#6-get-openrouter-api-key)
7. [Configure Environment Variables](#7-configure-environment-variables)
8. [Configure Sources](#8-configure-sources)
9. [Set Up Twitter/X Accounts](#9-set-up-twitterx-accounts)
10. [Run Content Extraction](#10-run-content-extraction)
11. [Start the API Server](#11-start-the-api-server)
12. [Access the Frontend](#12-access-the-frontend)
13. [Test AI Features](#13-test-ai-features)
14. [Schedule Automatic Runs](#14-schedule-automatic-runs)
15. [Troubleshooting](#15-troubleshooting)
16. [Platform-Specific Schema Reference](#16-platform-specific-schema-reference)

---

## 1. Prerequisites

Before you begin, ensure you have:

- **Computer**: macOS, Linux, or Windows
- **Internet Connection**: Required for API calls and content extraction
- **Terminal/Command Line**: Basic familiarity with terminal commands
- **Text Editor**: To edit configuration files (VS Code, Sublime Text, Notepad++, etc.)
- **Web Browser**: Chrome, Firefox, Safari, or Edge

---

## 2. Install Python 3.11

### macOS

1. Install Homebrew (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. Install Python 3.11:
   ```bash
   brew install python@3.11
   ```

3. Verify installation:
   ```bash
   python3.11 --version
   ```
   Expected output: `Python 3.11.x`

### Linux (Ubuntu/Debian)

1. Update package list:
   ```bash
   sudo apt update
   ```

2. Install Python 3.11:
   ```bash
   sudo apt install python3.11 python3.11-venv python3.11-dev
   ```

3. Verify installation:
   ```bash
   python3.11 --version
   ```

### Windows

1. Download Python 3.11 from [python.org](https://www.python.org/downloads/release/python-3110/)
2. Run the installer
3. **Important**: Check "Add Python 3.11 to PATH" during installation
4. Click "Install Now"
5. Verify installation (open Command Prompt):
   ```cmd
   python --version
   ```

---

## 3. Clone the Repository

1. Open terminal/command prompt

2. Navigate to where you want to store the project:
   ```bash
   cd ~/Codebases
   ```

3. Clone the repository:
   ```bash
   git clone https://github.com/your-username/news-samarth.git
   ```

4. Enter the project directory:
   ```bash
   cd news-samarth
   ```

5. Verify you're in the correct directory:
   ```bash
   ls
   ```
   You should see: `README.md`, `requirements.txt`, `sources.json`, etc.

---

## 4. Create Conda Environment

### Install Anaconda (if not already installed)

1. Download Anaconda from [anaconda.com](https://www.anaconda.com/download)
2. Run the installer and follow prompts
3. Restart your terminal after installation

### Create Environment

1. Create a new conda environment with Python 3.11:
   ```bash
   conda create -n newsfeed python=3.11
   ```

2. When prompted, type `y` and press Enter to proceed

3. Activate the environment:
   ```bash
   conda activate newsfeed
   ```

4. Verify Python version:
   ```bash
   python --version
   ```
   Expected output: `Python 3.11.x`

**Note**: You must activate this environment every time you work with the project:
```bash
conda activate newsfeed
```

---

## 5. Install Dependencies

1. Ensure you're in the project directory and conda environment is activated:
   ```bash
   conda activate newsfeed
   cd ~/Codebases/news-samarth
   ```

2. Install all required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Playwright browser (required for Twitter extraction):
   ```bash
   playwright install chromium
   ```

4. Wait for installation to complete (may take 2-5 minutes)

5. Verify installation:
   ```bash
   pip list | grep -E "chromadb|fastapi|langchain|playwright"
   ```
   You should see these packages listed.

---

## 6. Get OpenRouter API Key

OpenRouter provides access to AI models (Claude, GPT-4, etc.) for summarization and newsletter generation.

### Step 1: Create an OpenRouter Account

1. Go to [openrouter.ai](https://openrouter.ai)
2. Click "Sign Up"
3. Create an account (email or Google/GitHub sign-in)

### Step 2: Add Credits (Optional but Recommended)

1. Go to [openrouter.ai/credits](https://openrouter.ai/credits)
2. Click "Add Credits"
3. Add $5-10 (enough for hundreds of summaries/newsletters)
4. Complete payment

**Note**: You can use OpenRouter without credits, but you'll hit rate limits quickly.

### Step 3: Get Your API Key

1. Go to [openrouter.ai/keys](https://openrouter.ai/keys)
2. Click "Create Key"
3. Enter a name: `Newsfeed Aggregator`
4. Click "Create"
5. **Copy the API key** (starts with `sk-or-...`)

**Important**: This key is shown only once. Copy it immediately.

---

## 7. Configure Environment Variables

### Step 1: Create .env File

1. In the project directory, copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` in your text editor:
   ```bash
   # macOS/Linux
   open .env
   
   # Windows
   notepad .env
   ```

### Step 2: Fill in Your API Keys

Replace the placeholder values with your actual keys:

```env
# Twitter/X (Playwright-based extraction)
# Use a burner account - credentials stored in isolated browser profile
TWITTER_USERNAME=your_burner_username
TWITTER_PASSWORD=your_burner_password
TWITTER_EMAIL=your_email_for_verification  # Optional, for verification screens

# OpenRouter API Key (for AI features)
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

**Important Notes**:
- Replace `sk-or-...` with your OpenRouter API key
- Keep `OPENROUTER_MODEL` as is (or change to another model)
- **Note**: YouTube now uses RSS feeds (no API key required)
- **Twitter**: Uses Playwright with isolated browser session - use a burner account

### Step 3: Save the File

Save the `.env` file and close your text editor.

### Step 4: Verify Configuration

Run this command to verify your keys are loaded:
```bash
python -c "
from config import config
print('OpenRouter API Key:', bool(config.openrouter_api_key))
"
```

Expected output:
```
OpenRouter API Key: True/False
```

If it shows `False`, double-check your `.env` file.

---

## 8. Configure Sources

The `sources.json` file tells the system which creators to follow.

### Step 1: Open sources.json

```bash
# macOS/Linux
open sources.json

# Windows
notepad sources.json
```

### Step 2: Understand the Structure

The file has four sections:
- `youtube`: YouTube channels to follow
- `reddit`: Subreddits to monitor (via RSS feeds)
- `substack`: Newsletters to subscribe to
- `twitter`: Twitter/X accounts to track

### Step 3: Add YouTube Channels (via RSS Feeds)

YouTube content is accessed via RSS feeds (no API credentials required).

To find a YouTube channel ID:

1. Go to the YouTube channel page
2. Look at the URL:
   - If it's `youtube.com/channel/UC...`, the part after `/channel/` is the ID
   - If it's `youtube.com/@username`, you need to find the channel ID:
     - Go to the channel
     - Right-click → "View Page Source"
     - Search for `"channelId"`—the value is the ID

**RSS Feed URL Format**: `https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}`

Example configuration:
```json
"youtube": [
  {
    "name": "Fireship",
    "channel_id": "UCsBjURrPoezykLs9EqgamOA",
    "max_results": 15,
    "fetch_transcript": true,
    "filter_shorts": true
  },
  {
    "name": "Two Minute Papers",
    "channel_id": "UCbfYPyITQ-7l4upoX8nvctg",
    "max_results": 15,
    "fetch_transcript": true,
    "filter_shorts": true
  }
]
```

**Fields**:
- `name`: Display name (can be anything)
- `channel_id`: The YouTube channel ID (required)
- `max_results`: Number of recent videos to fetch (default: 15)
- `fetch_transcript`: Set to `true` to get full video transcripts using youtube-transcript-api
- `filter_shorts`: Set to `true` to filter out YouTube Shorts (default: true)

**Note**: YouTube RSS feeds return the 15 most recent videos by default. The `filter_shorts` option helps remove short-form content from your feed.

### Step 4: Add Subreddits (via RSS Feeds)

Reddit content is accessed via RSS feeds (no API credentials required).

To find a subreddit RSS feed URL:

1. Go to the subreddit (e.g., `reddit.com/r/LocalLLaMA`)
2. Add `/.rss` to the end: `reddit.com/r/LocalLLaMA/.rss`
3. Test it in your browser—you should see XML

**Pro Tip**: If `www.reddit.com` blocks your requests, use `old.reddit.com` instead.

Example configuration:
```json
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
```

**Fields**:
- `name`: Display name (can be anything)
- `rss_url`: Full RSS feed URL (required)
- `limit`: Number of posts to fetch (1-100)

**Note**: The `sort` option is not available with RSS feeds. Use different RSS endpoints for different sorts:
- Hot: `https://www.reddit.com/r/{subreddit}/.rss`
- New: `https://www.reddit.com/r/{subreddit}/new/.rss`
- Top: `https://www.reddit.com/r/{subreddit}/top/.rss?t=day`

### Step 5: Add Substack Newsletters

To find a Substack RSS feed URL:

1. Go to the Substack newsletter (e.g., `example.substack.com`)
2. Add `/feed` to the end: `example.substack.com/feed`
3. Test it in your browser—you should see XML

Example configuration:
```json
"substack": [
  {
    "name": "The Pragmatic Engineer",
    "rss_url": "https://newsletter.pragmaticengineer.com/feed"
  },
  {
    "name": "Lenny's Newsletter",
    "rss_url": "https://www.lennysnewsletter.com/feed"
  }
]
```

**Fields**:
- `name`: Display name (can be anything)
- `rss_url`: Full RSS feed URL (must end with `/feed`)

### Step 6: Add Twitter/X Accounts

Example configuration:
```json
"twitter": [
  {
    "name": "Elon Musk",
    "handle": "elonmusk",
    "max_results": 10
  },
  {
    "name": "Sam Altman",
    "handle": "sama",
    "max_results": 5
  }
]
```

**Fields**:
- `name`: Display name (can be anything)
- `handle`: Twitter username (without @)
- `max_results`: Number of tweets to fetch (1-100)

### Step 7: Save the File

Save `sources.json` and close your text editor.

### Step 8: Verify Configuration

```bash
python -c "
from config import config
import json
print(json.dumps(config.sources, indent=2))
"
```

You should see your configured sources printed.

---

## 11. Set Up Twitter/X Accounts

Twitter uses Playwright for browser-based extraction with strict session isolation.

### Step 1: Create a Burner Twitter Account

**Important**: Use a throwaway/dummy account, not your main account.

1. Create a Twitter account:
   - Go to [twitter.com](https://twitter.com)
   - Click "Create account"
   - Use a temporary email address (e.g., from [temp-mail.org](https://temp-mail.org))
   - Complete phone verification if required

2. Note down:
   - Username (without @)
   - Password
   - Email address (for verification screens)

### Step 2: Add Credentials to .env

Add your burner account credentials to the `.env` file:

```env
TWITTER_USERNAME=your_burner_username
TWITTER_PASSWORD=your_burner_password
TWITTER_EMAIL=your_email_for_verification
```

### Step 3: First Run (Login)

The first time you run the Twitter extractor, it will:
1. Open a browser (isolated from your main browser)
2. Navigate to Twitter login page
3. Log in with your credentials
4. Handle email verification if prompted
5. Save session to `.playwright_twitter_profile/`

**For debugging**, you can run with visible browser:
```python
# In scripts/run_all.py or run_single.py, modify:
"twitter": TwitterPlaywrightExtractor(headless=False)
```

### Step 4: Verify Session Persistence

After successful login:
1. Session is saved in `.playwright_twitter_profile/`
2. Future runs will reuse the session (no login needed)
3. Session persists until Twitter invalidates it

**Note**: If Twitter detects unusual activity, it may require re-login. Just run with `headless=False` to debug.

---

## 12. Run Content Extraction

Now that everything is configured, let's extract content.

### Step 1: Run All Extractors

```bash
python scripts/run_all.py
```

**What happens**:
1. Connects to ChromaDB database
2. Reads your `sources.json` configuration
3. For each platform (Substack, Reddit, YouTube, Twitter):
   - Fetches content from configured sources
   - Stores full content in database
   - Logs progress
4. Shows summary of what was added

**Expected output**:
```
============================================================
Starting master newsfeed extraction...
Database location: db/chroma_db
============================================================
Current database contains 0 articles
Running substack extractor...
Finished substack: 5 fetched, 5 new articles added.
Running reddit extractor...
Finished reddit: 10 fetched, 10 new articles added.
Running youtube extractor...
Finished youtube: 8 fetched, 8 new articles added.
Running twitter extractor...
Finished twitter: 15 fetched, 15 new articles added.
============================================================
EXTRACTION SUMMARY
============================================================
Starting articles: 0
Ending articles: 38
New articles added: 38

Platform breakdown:
  substack: 5 fetched, 5 new
  reddit: 10 fetched, 10 new
  youtube: 8 fetched, 8 new
  twitter: 15 fetched, 15 new
============================================================
```

### Step 2: Run Single Platform (Optional)

To test just one platform:
```bash
python scripts/run_single.py --platform youtube
```

Available platforms: `substack`, `reddit`, `youtube`, `twitter`

### Step 3: Check Logs

If something goes wrong, check the log file:
```bash
cat logs/extractor.log
```

---

## 13. Start the API Server

### Step 1: Start the Server

```bash
python api/main.py
```

**Expected output**:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Important**: Keep this terminal window open. The server must stay running.

### Step 2: Verify Server is Running

Open a **new terminal window** (keep the server running in the first one):

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "database": "chromadb",
  "db_path": "db/chroma_db",
  "db_size_mb": 0.5,
  "article_count": 38
}
```

### Step 3: Test Other Endpoints

```bash
# Get recent articles
curl http://localhost:8000/feed/recent

# Get platform statistics
curl http://localhost:8000/platforms

# Search articles
curl "http://localhost:8000/feed/search?q=AI"
```

---

## 14. Access the Frontend

### Step 1: Open Your Browser

1. Open Chrome, Firefox, Safari, or Edge
2. Go to: `http://localhost:8000`

### Step 2: Explore the Interface

You should see:
- **Header**: "Newsfeed Aggregator" title
- **Platform Filters**: Buttons for All, Substack, Reddit, YouTube, Twitter
- **Search Bar**: Search articles by keywords
- **Article Cards**: Each showing:
  - Platform badge (colored)
  - Source name
  - Title
  - Timestamp
  - Content preview
  - Link to original
- **AI Newsletter Section**: Generate and view newsletters
- **Health Status**: Database statistics

### Step 3: Test Features

1. **Filter by Platform**: Click "YouTube" to see only YouTube articles
2. **Search**: Type "AI" in search box and press Enter
3. **View Article**: Click an article card to expand it
4. **Check Health**: Look at the health status indicator

---

## 15. Test AI Features

AI features require an OpenRouter API key.

### Step 1: Generate a Summary

In a new terminal (server must be running):
```bash
curl -X POST http://localhost:8000/summarize
```

**What happens**:
1. Fetches articles from last 24 hours
2. Sends them to AI model (Claude 3.5 Sonnet by default)
3. Generates a comprehensive summary
4. Stores summary in database
5. Returns the summary

**Expected response**:
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
  }
}
```

### Step 2: Get Latest Summary

```bash
curl http://localhost:8000/summary/latest
```

### Step 3: Generate a Newsletter (Today)

```bash
curl -X POST http://localhost:8000/newsletter/generate
```

**What happens**:
1. Fetches articles from last 24 hours
2. Fetches previous newsletters for context
3. **Agent 1 (Fetcher)**: Prepares articles
4. **Agent 2 (Ranker)**: Ranks articles by importance
5. **Agent 3 (Deduplicator)**: Identifies duplicates/updates
6. **Agent 4 (Generator)**: Creates professional newsletter
7. Stores newsletter in database
8. Returns the newsletter

**Expected response**:
```json
{
  "success": true,
  "cached": false,
  "id": "newsletter_2024-01-15",
  "date": "2024-01-15",
  "newsletter": "# 📰 Daily AI Newsletter - January 15, 2024\n...",
  "metadata": {
    "article_count": 20,
    "new_stories_count": 17,
    "updates_count": 3,
    "platforms": ["youtube", "reddit", "substack", "twitter"],
    "generated_at": "2024-01-15T08:00:00",
    "model_used": "anthropic/claude-3.5-sonnet"
  }
}
```

### Step 4: Generate Newsletter for Specific Date

The system supports generating newsletters for any date within the last 30 days.

**Phase 1: Fetch articles for the date**
```bash
curl -X POST http://localhost:8000/newsletter/fetch \
  -H "Content-Type: application/json" \
  -d '{"date": "2024-01-15"}'
```

**Response shows per-platform status:**
```json
{
  "date": "2024-01-15",
  "overall_status": "success",
  "platforms": {
    "youtube": {"status": "success", "count": 12},
    "reddit": {"status": "success", "count": 8},
    "substack": {"status": "success", "count": 5},
    "twitter": {"status": "failed", "count": 0, "error": "Credentials not configured"}
  },
  "total_articles": 25
}
```

**Phase 2: Generate newsletter**
```bash
curl -X POST http://localhost:8000/newsletter/generate \
  -H "Content-Type: application/json" \
  -d '{"date": "2024-01-15", "force": false}'
```

**Force regenerate (skip cache):**
```bash
curl -X POST http://localhost:8000/newsletter/generate \
  -H "Content-Type: application/json" \
  -d '{"date": "2024-01-15", "force": true}'
```

### Step 5: Get Latest Newsletter

```bash
curl http://localhost:8000/newsletter/latest
```

### Step 6: View in Frontend

1. Open browser to `http://localhost:8000`
2. Scroll to "AI Newsletter" section
3. Use the **date picker** to select a specific date (last 30 days)
4. Click "Generate Newsletter" button
5. If fetching is needed, a **fetch status modal** appears showing per-platform results
6. Choose **Continue** (proceed with available), **Retry** (refetch failed), or **Cancel**
7. Wait for generation (may take 30-60 seconds)
8. View the generated newsletter

---

## 16. Database Management (Admin)

The system includes admin endpoints for database management. These are useful for maintaining database health and cleaning up old data.

### Check Database Health

```bash
curl http://localhost:8000/admin/health
```

**Response shows:**
- Database integrity status
- Article counts by platform
- Date range of articles
- Any issues or warnings
- Timezone configuration

### Scan for Data Quality Issues

```bash
curl "http://localhost:8000/admin/scan?sample_size=100"
```

**Response shows:**
- Number of valid/invalid articles
- Issues by type (missing fields, invalid timestamps, etc.)
- Sample of problematic articles

### Preview Cleanup (Dry Run)

Before deleting old articles, preview what would be removed:

```bash
curl "http://localhost:8000/admin/cleanup/preview?days_old=30"
```

**Response shows:**
- Number of articles that would be deleted
- Cutoff date
- List of articles to be deleted (with URLs and titles)

### Execute Cleanup

**Important:** Always run preview first!

```bash
curl -X POST "http://localhost:8000/admin/cleanup?days_old=30&dry_run=false&backup=true"
```

**Parameters:**
- `days_old`: Delete articles older than this many days (default: 30)
- `dry_run`: Set to `false` to actually delete (default: `true` for safety)
- `backup`: Create backup before deletion (default: `true`)

### Surgically Delete Articles

Delete specific articles by URL:

```bash
# Delete single article
curl -X DELETE "http://localhost:8000/admin/articles?url=https://example.com/bad-article&confirm=true"

# Delete multiple articles
curl -X DELETE "http://localhost:8000/admin/articles?urls=https://example.com/1,https://example.com/2&confirm=true"

# Delete all articles from a platform
curl -X DELETE "http://localhost:8000/admin/articles?platform=twitter&confirm=true"
```

**Important:** Must include `confirm=true` to actually delete.

### Backup and Restore

**Create backup:**
```bash
curl -X POST http://localhost:8000/admin/backup
```

**List backups:**
```bash
curl http://localhost:8000/admin/backups
```

**Restore from backup:**
```bash
curl -X POST "http://localhost:8000/admin/restore?backup_name=chroma_backup_20240115_183000.tar.gz&confirm=true"
```

**Note:** Restore creates a pre-restore backup automatically.

### Check Timezone Configuration

```bash
curl http://localhost:8000/admin/timezone
```

**Response shows:**
- Configured timezone
- Current time in that timezone
- UTC offset

---

## 17. Schedule Automatic Runs

To run extraction automatically every day:

### macOS/Linux (using crontab)

1. Open crontab editor:
   ```bash
   crontab -e
   ```

2. Add this line (runs daily at 8 AM):
   ```
   0 8 * * * cd /Users/samarthsaraswat/Codebases/news-samarth && /Users/samarthsaraswat/anaconda3/envs/newsfeed/bin/python scripts/run_all.py
   ```

   **Important**: Replace paths with your actual paths:
   - First path: Your project directory
   - Second path: Your conda environment Python path

3. Find your conda Python path:
   ```bash
   which python
   ```
   Use this path in the crontab entry.

4. Save and exit (in vim: press `Esc`, type `:wq`, press `Enter`)

5. Verify crontab:
   ```bash
   crontab -l
   ```

### Windows (using Task Scheduler)

1. Open Task Scheduler (search in Start menu)
2. Click "Create Basic Task"
3. Name: `Newsfeed Aggregator Daily Run`
4. Trigger: "Daily"
5. Set time: 8:00 AM
6. Action: "Start a program"
7. Program/script: `C:\Users\YourName\anaconda3\envs\newsfeed\python.exe`
   (Find your actual path with `where python` in conda environment)
8. Add arguments: `scripts/run_all.py`
9. Start in: `C:\Users\YourName\Codebases\news-samarth`
10. Click "Finish"

### Schedule AI Summarization (Optional)

To generate daily summaries automatically:

**macOS/Linux crontab**:
```
0 9 * * * cd /Users/samarthsaraswat/Codebases/news-samarth && /Users/samarthsaraswat/anaconda3/envs/newsfeed/bin/python -c "from ai.summarizer import summarize_last_24h; summarize_last_24h()"
```

**Or use the API** (if server is always running):
```
0 9 * * * curl -X POST http://localhost:8000/summarize
```

---

## 17. Troubleshooting

### Issue: "conda: command not found"

**Solution**: Anaconda is not in your PATH.
```bash
# macOS/Linux - add to ~/.bashrc or ~/.zshrc:
export PATH="$HOME/anaconda3/bin:$PATH"

# Then reload:
source ~/.bashrc  # or source ~/.zshrc
```

### Issue: "No module named 'chromadb'"

**Solution**: Dependencies not installed.
```bash
conda activate newsfeed
pip install -r requirements.txt
```

### Issue: "OPENROUTER_API_KEY not set"

**Solution**: Check your `.env` file.
```bash
cat .env | grep OPENROUTER_API_KEY
```
If empty, add your key to `.env`.

### Issue: "No articles found"

**Solution**: Run extraction first.
```bash
python scripts/run_all.py
```

### Issue: API server won't start

**Solution**: Check if port 8000 is in use.
```bash
# macOS/Linux
lsof -i :8000

# Windows
netstat -ano | findstr :8000
```

If in use, kill the process or use a different port:
```bash
python api/main.py --port 8001
```

### Issue: Twitter extraction fails

**Solution**: Playwright session may have expired.
1. Run with `headless=False` to debug:
   ```python
   # In scripts/run_all.py or run_single.py:
   "twitter": TwitterPlaywrightExtractor(headless=False)
   ```
2. Check if login is required
3. Verify credentials in `.env` file
4. Delete `.playwright_twitter_profile/` to force fresh login

### Issue: YouTube transcripts not available

**Solution**: Some videos have transcripts disabled.
- The extractor falls back to video description
- Check `fetch_transcript: true` in `sources.json`

### Issue: Frontend not loading

**Solution**: 
1. Verify API is running: `curl http://localhost:8000/health`
2. Check browser console for errors (F12)
3. Try hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)

### Issue: "Database locked"

**Solution**: Only one extraction can run at a time.
```bash
# Kill any running extractions
pkill -f "python scripts/run_all.py"

# Wait a moment, then try again
python scripts/run_all.py
```

### Issue: Rate limit errors

**Solution**: You're making too many API calls.
- **Reddit**: Wait a few minutes
- **YouTube**: Check quota at [console.cloud.google.com](https://console.cloud.google.com)
- **OpenRouter**: Add more credits or wait

---

## Quick Reference

### Daily Workflow

```bash
# 1. Activate environment
conda activate newsfeed

# 2. Navigate to project
cd ~/Codebases/news-samarth

# 3. Run extraction
python scripts/run_all.py

# 4. Start API server
python api/main.py

# 5. Open browser
# Go to http://localhost:8000
```

### Useful Commands

```bash
# Check configuration
python -c "from config import config; print(config.sources)"

# Check database
python -c "from db.chroma_db import get_chroma_client, get_or_create_collection; print(get_or_create_collection(get_chroma_client()).count())"

# View logs
cat logs/extractor.log

# Test API
curl http://localhost:8000/health

# Generate summary
curl -X POST http://localhost:8000/summarize

# Generate newsletter
curl -X POST http://localhost:8000/newsletter/generate
```

### File Locations

- **Configuration**: `sources.json`
- **Environment Variables**: `.env`
- **Database**: `db/chroma_db/`
- **Logs**: `logs/extractor.log`
- **Frontend**: `frontend/`

---

## Summary

You've now completed all user actions:

1. ✅ Installed Python 3.11
2. ✅ Cloned the repository
3. ✅ Created conda environment
4. ✅ Installed dependencies
5. ✅ Got Reddit API credentials
6. ✅ Got YouTube API key
7. ✅ Got OpenRouter API key
8. ✅ Configured environment variables
9. ✅ Configured sources
10. ✅ Set up Twitter accounts
11. ✅ Ran content extraction
12. ✅ Started API server
13. ✅ Accessed frontend
14. ✅ Tested AI features
15. ✅ Scheduled automatic runs

Your Newsfeed Aggregator is now fully operational!

---

*Created with ⚡ by Anti-Gravity.*
