# Face Recognition & Social Media Search System (Consent-Based)

A FastAPI service that:
- stores facial embeddings for known people,
- searches for similar faces,
- looks up username presence across many social platforms,
- and performs reverse phone number lookup (country, region, carrier, line type, timezones).

> ⚠️ This project should only be used with explicit consent and authorized datasets.

## Quick start (local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Server URL: `http://127.0.0.1:8000`

## Run with Docker + Telegram bot

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy your token.
2. Set the token as an environment variable.
3. Start both API and bot in Docker.

```bash
export TELEGRAM_BOT_TOKEN="<your_bot_token>"
docker compose up --build
```

### Services

- API: `http://127.0.0.1:8000`
- Telegram bot service: runs `bot.py` and talks to the API over Docker network (`http://api:8000`)

### Telegram commands

- `/start` — help and command list.
- `/health` — checks API health endpoint.
- `/platforms` — returns supported social platforms.
- `/social <username>` — searches username across platforms.
- `/phone <number> [region]` — reverse phone number lookup.

## API endpoints

- `GET /health` — service health check.
- `POST /add` (`person_id`, `file`, optional `username`) — adds a person and optionally discovers social profiles.
- `POST /search` (`file`) — searches for top face matches.
- `GET /search/social?username=X` — checks all supported social platforms.
- `GET /search/social?username=X&platforms=Instagram,Twitter` — checks specific platforms.
- `GET /platforms` — lists supported social platforms.
- `GET /search/phone?number=+14155552671` — reverse phone number lookup (country, region, carrier, line type, timezones).
- `GET /search/phone?number=4155552671&region=US` — national-format numbers with an ISO region hint.
- `GET /search/phone?number=+14155552671&numverify=true` — also query Numverify (requires `NUMVERIFY_API_KEY` env var).

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

### Reverse phone number lookup

```bash
# E.164 format (preferred)
curl "http://127.0.0.1:8000/search/phone?number=%2B14155552671"

# National format with a region hint
curl "http://127.0.0.1:8000/search/phone?number=4155552671&region=US"

# Optional Numverify enrichment (requires NUMVERIFY_API_KEY env var)
curl "http://127.0.0.1:8000/search/phone?number=%2B14155552671&numverify=true"
```

The response includes validity, country/region code, rough geographic location,
carrier (when known), line type (mobile/fixed/voip/...), timezones, and formatted
strings (E.164, international, national, RFC 3966). All enrichment other than
Numverify is fully offline via Google's libphonenumber. Owner/name lookup
requires a paid third-party API (e.g. Numverify, Twilio Lookup, Truecaller) —
this service ships with optional Numverify support only.

## Supported platforms

This project includes 70+ platforms, including:
Facebook, Instagram, Twitter/X, LinkedIn, TikTok, Snapchat, Threads, YouTube,
Reddit, Discord, Telegram, GitHub, GitLab, Steam, Twitch, Spotify, Medium,
Hugging Face, ProductHunt, and many more.

Use `GET /platforms` for the exact live list.
