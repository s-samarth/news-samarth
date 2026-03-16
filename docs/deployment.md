# Deployment & Scheduling Guide

This guide covers how to keep your newsfeed updated automatically and how to host the API.

## 1. Local Scheduling (Recommended)
Since this is a low-volume scraper (20-30 items/day), running it on your local machine or a home server (like a Raspberry Pi or always-on Mac) is the most efficient choice.

### Using Crontab (macOS / Linux)
1. Open your crontab editor:
   ```bash
   crontab -e
   ```
2. Add a line to run the script every morning at 7:00 AM:
   ```bash
   0 7 * * * cd /path/to/news-samarth && /path/to/venv/bin/python scripts/run_all.py >> logs/cron.log 2>&1
   ```
   *Note: Use absolute paths for both the project directory and the python executable inside your venv.*

## 2. Server Deployment (Cloud)
If you wish to host this in the cloud, follow these recommendations:

### A. Scraper (Background Jobs)
- **GitHub Actions**: You can schedule `run_all.py` as a GitHub Action. However, notice that **SQLite is a local file**. You would need to commit the updated `newsfeed.db` back to the repo (not recommended) or use a hosted database like **ElephantSQL (PostgreSQL)** by modifying `db/models.py`.
- **VPS (DigitalOcean/Linode)**: A simple $5/mo VPS is ideal. Set up your cron job there as described in Section 1.

### B. API Layer
To keep the FastAPI server running 24/7 on a server:
1. Install `gunicorn`:
   ```bash
   pip install gunicorn
   ```
2. Run with worker management:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.main:app --bind 0.0.0.0:8000
   ```

## 3. Persistent Sessions
- **Twitter**: The `accounts.db` created by `twscrape` must persist. If you are using Docker or a transient cloud environment, ensure this file is mapped to a persistent volume.
- **SQLite**: Ensure `db/newsfeed.db` is backed up or stored on persistent storage. It contains your entire historical news stash.

## 4. Frontend Deployment
Since the frontend spec is designed for React:
- **Vercel / Netlify**: Ideal for hosting the static React build.
- **CORS Configuration**: In `api/main.py`, ensure the `allow_origins` list includes your production frontend URL (e.g., `https://my-newsfeed.vercel.app`).
