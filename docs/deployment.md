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

### Configuration Note
The `sources.json` file uses platform-specific schemas. Each platform (YouTube, Reddit, Substack, Twitter) has its own configuration structure tailored to its data format. See the [Testing Guide](testing_guide.md#13-platform-specific-schema-reference) for detailed schema documentation.

## 2. Server Deployment (Cloud)
If you wish to host this in the cloud, follow these recommendations:

### A. Scraper (Background Jobs)
- **GitHub Actions**: You can schedule `run_all.py` as a GitHub Action. ChromaDB stores data locally, so you would need to commit the `db/chroma_db/` directory back to the repo or use a hosted vector database.
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

### C. Frontend (Included)
The frontend is now served directly by FastAPI:
- No separate frontend build step required
- Static files served from `frontend/` directory
- Access at `http://localhost:8000`

## 3. Persistent Sessions
- **Twitter**: The `accounts.db` created by `twscrape` must persist. If you are using Docker or a transient cloud environment, ensure this file is mapped to a persistent volume.
- **ChromaDB**: Ensure `db/chroma_db/` is backed up or stored on persistent storage. It contains your entire historical news stash.

## 4. Docker Deployment (Optional)
Create a `Dockerfile` for easy deployment:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "api/main.py"]
```

Build and run:
```bash
docker build -t news-samarth .
docker run -p 8000:8000 -v $(pwd)/db:/app/db news-samarth
```
