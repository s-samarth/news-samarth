# Running Instructions

Follow this guide to get your Newsfeed Aggregator up and running for the first time.

## 1. Prerequisites
- Python 3.11 or higher.
- `pip` (Python package installer).

## 2. Installation
1.  **Clone the Repository**:
    ```bash
    git clone <your-repo-link>
    cd news-samarth
    ```
2.  **Create a Virtual Environment** (Highly Recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## 3. Configuration

### A. Environment Variables (`.env`)
Copy the template and fill in your keys:
```bash
cp .env.example .env
```
- **Reddit**: Create an app at [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps). Choose **script**.
- **YouTube**: Create a project in [Google Cloud Console](https://console.cloud.google.com/), enable **YouTube Data API v3**, and generate an API API key.

### B. Targets (`sources.json`)
Open `sources.json` and add your favorite creators. 
- Use the correct `channel_id` for YouTube (not the username).
- Substack requires the direct RSS link (usually `yoursite.substack.com/feed`).

## 4. Twitter/X Account Setup
The `twscrape` library uses a pool of accounts rather than an official API.
1. Create `accounts.txt` with this format: `username:password:email:email_password`
2. Run these commands:
   ```bash
   twscrape add_accounts accounts.txt
   twscrape login_accounts
   ```
   *Note: Using a dummy/throwaway account is recommended.*

## 5. Running the System

### Manual Extraction
To run a full sweep across all platforms:
```bash
python scripts/run_all.py
```

To test a single platform (e.g., just Reddit):
```bash
python scripts/run_single.py --platform reddit
```

### Starting the API
Start the server to serve the content to your frontend:
```bash
python api/main.py
```
The API will be available at `http://localhost:8000`. You can test it by visiting `http://localhost:8000/feed` in your browser.

## 6. Troubleshooting
- **Missing Data**: Check `logs/extractor.log` for platform-specific errors.
- **Database Locked**: Ensure only one instance of `run_all.py` is running at a time.
- **Twitter Failures**: Twitter frequently updates its internal API; if `twscrape` fails, check their [official repo](https://github.com/vladkens/twscrape) for updates.
