# Face Recognition & Social Media Search System (Consent-Based)

A FastAPI service that:
- stores facial embeddings for known people,
- searches for similar faces,
- looks up username presence across 100+ social platforms,
- scrapes profile pictures, display names, and bios from found profiles,
- generates username variations from a real name and searches them all.

> This project should only be used with explicit consent and authorized datasets.

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
- `/name <full name>` — searches by real name using generated username variations.
- `/scrape <username>` — searches username with profile scraping (pictures, bios, names).

## API endpoints

- `GET /health` — service health check.
- `POST /add` (`person_id`, `file`, optional `username`) — adds a person and optionally discovers social profiles.
- `POST /search` (`file`) — searches for top face matches.
- `GET /search/social?username=X` — checks all supported social platforms.
- `GET /search/social?username=X&platforms=Instagram,Twitter` — checks specific platforms.
- `GET /search/social?username=X&scrape=true` — checks platforms **and** scrapes profile data (picture, display name, bio, stats).
- `GET /search/name?name=John+Doe` — generates username variations from a real name and searches all platforms.
- `GET /search/name?name=John+Doe&scrape=true` — name search with profile scraping.
- `GET /search/name/usernames?name=John+Doe` — preview the username variations that would be generated for a name.
- `POST /search/identify` (`file`, optional `name`, optional `username`, `scrape`) — combines face matching with social media discovery in one request.
- `GET /platforms` — lists supported social platforms.
- `GET /search/phone?number=+14155552671` — reverse phone number lookup (country, region, carrier, line type, timezones).
- `GET /search/phone?number=4155552671&region=US` — national-format numbers with an ISO region hint.
- `GET /search/phone?number=+14155552671&numverify=true` — also query Numverify (requires `NUMVERIFY_API_KEY` env var).

## Profile scraping

When `scrape=true` is passed to any search endpoint, each found profile is enriched with:

| Field             | Description                                         |
|-------------------|-----------------------------------------------------|
| `profile_picture` | URL to the profile avatar (from OG/meta/img tags)   |
| `display_name`    | Display name extracted from page title or meta tags  |
| `bio`             | Bio or description text (up to 1000 characters)     |
| `stats`           | Follower / following / post counts when available    |

## Name-based search

The `/search/name` endpoint generates plausible username variations from a real name and checks each one. For example, "John Doe" generates variations like:

`johndoe`, `john.doe`, `john_doe`, `doejohn`, `johnd`, `jdoe`, `john.doe23`, etc.

Use `/search/name/usernames?name=John+Doe` to preview the exact variations before running a full search.

## Behavioral notes

- Input validation now returns HTTP 400 responses for:
  - invalid usernames,
  - unsupported platform filters,
  - missing/no-face images,
  - embedding dimension mismatch.
- Face analysis attempts GPU first, then falls back to CPU automatically.
- FAISS index dimension is initialized from the first embedding and validated on future inserts/searches.
- Profile scraping uses BeautifulSoup + lxml for fast HTML parsing.
- Concurrency is throttled to 20 simultaneous outbound requests.

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

### Search username with profile scraping

```bash
curl "http://127.0.0.1:8000/search/social?username=torvalds&scrape=true"
```

### Search by real name

```bash
curl "http://127.0.0.1:8000/search/name?name=John+Doe"
```

### Identify: face + name + social in one request

```bash
curl -X POST "http://127.0.0.1:8000/search/identify?name=John+Doe&scrape=true" \
  -F "file=@/path/to/face.jpg"
```

## Supported platforms

This project includes 100+ platforms, including:
Facebook, Instagram, Twitter/X, LinkedIn, TikTok, Snapchat, Threads, YouTube,
Reddit, Discord, Telegram, GitHub, GitLab, Steam, Twitch, Spotify, Medium,
Hugging Face, ProductHunt, Pinterest, LeetCode, HackerRank, CodePen, Wattpad,
and many more.

Use `GET /platforms` for the exact live list.
