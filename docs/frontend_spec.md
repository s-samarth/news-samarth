# React Frontend Specification

Use this specification in a UI generator (like Lovable, v0.dev, or Bolt.new) to build the frontend for the Newsfeed Aggregator.

## 1. Goal
Build a personalized daily newsfeed dashboard that consumes a unified JSON API from a FastAPI backend. It should feel premium, responsive, and prominently show the origin of every piece of content.

## 2. API Data Contract
The frontend will call `GET http://localhost:8000/feed`.

### **Sample JSON Item:**
```json
{
  "id": 1,
  "platform": "substack",
  "source_name": "Stratechery",
  "title": "The AI Unbundling",
  "content_text": "Sample content...",
  "url": "https://stratechery.com/...",
  "timestamp": "2026-03-16T10:00:00Z",
  "media_link": "https://..."
}
```

## 3. Component Specs

### **A. Platform Badge System**
- **Substack**: Orange (#FF6719)
- **Reddit**: Blue (#FF4500)
- **YouTube**: Red (#FF0000)
- **Twitter/X**: Sky Blue (#1DA1F2)

### **B. Feed Card**
- **Top Bar**: Display the `platform` badge and `source_name` side-by-side. Use capitalized source names.
- **Image**: If `media_link` exists, show it as a top-flush cover image or a small square thumbnail.
- **Body**: 
    - `title`: Bold, linked to `url`.
    - `content_text`: Truncated preview (280 chars) with a "Read More" that expands the text or opens the original URL.
- **Footer**: Relative timestamp (e.g., "3 hours ago").

### **C. Sidebar/Filter Nav**
- **Platform Selector**: Toggle buttons to filter feed by one or more platforms.
- **Health Widget**: Small section at bottom showing backend stats from `/health` (article count, DB size).

## 4. UI prompt to paste into generator:

> "Create a premium, dark-themed newsfeed dashboard in React. 
> 1. Use a sidebar for navigation and a main content area for a card-based feed. 
> 2. The feed consumes a JSON from `http://localhost:8000/feed`. 
> 3. Each card represents a news article with a title, platform badge (colors: Substack: orange, Reddit: orange-red, YouTube: red, Twitter: blue), source name (e.g. @username), a content preview, and a relative timestamp. 
> 4. If a 'media_link' is present, display it as a thumbnail. 
> 5. Implement filtering by platform using the sidebar buttons. 
> 6. Use Inter font and high-contrast typography. Add smooth hover effects on cards."
