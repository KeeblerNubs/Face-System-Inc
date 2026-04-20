# Face Recognition & Social Media Search System (Consent-Based)

A FastAPI service that:
- stores facial embeddings for known people,
- searches for similar faces,
- and looks up username presence across many social platforms.

> ⚠️ This project should only be used with explicit consent and authorized datasets.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Server URL: `http://127.0.0.1:8000`

## API endpoints

- `GET /health` — service health check.
- `POST /add` (`person_id`, `file`, optional `username`) — adds a person and optionally discovers social profiles.
- `POST /search` (`file`) — searches for top face matches.
- `GET /search/social?username=X` — checks all supported social platforms.
- `GET /search/social?username=X&platforms=Instagram,Twitter` — checks specific platforms.
- `GET /platforms` — lists supported social platforms.

## Behavioral notes

- Input validation now returns HTTP 400 responses for:
  - invalid usernames,
  - unsupported platform filters,
  - missing/no-face images,
  - embedding dimension mismatch.
- Face analysis attempts GPU first, then falls back to CPU automatically.
- FAISS index dimension is initialized from the first embedding and validated on future inserts/searches.

## Example requests

### Add a person

```bash
curl -X POST "http://127.0.0.1:8000/add?person_id=user-001&username=test_user" \
  -F "file=@/path/to/face.jpg"
```

### Search by face

```bash
curl -X POST "http://127.0.0.1:8000/search" \
  -F "file=@/path/to/query.jpg"
```

### Search username on selected platforms

```bash
curl "http://127.0.0.1:8000/search/social?username=test_user&platforms=GitHub,Instagram"
```

## Supported platforms

This project includes 70+ platforms, including:
Facebook, Instagram, Twitter/X, LinkedIn, TikTok, Snapchat, Threads, YouTube,
Reddit, Discord, Telegram, GitHub, GitLab, Steam, Twitch, Spotify, Medium,
Hugging Face, ProductHunt, and many more.

Use `GET /platforms` for the exact live list.
