Face Recognition & Social Media Search System (Consent-Based)

Run:
uvicorn main:app --reload

Endpoints:
- POST /add (person_id + image + optional username) — adds a person and auto-discovers their social media profiles
- POST /search (image) — searches for matching faces and returns linked social media profiles
- GET /search/social?username=X — searches every social media platform for a username
- GET /search/social?username=X&platforms=Instagram,Twitter — searches specific platforms only
- GET /platforms — lists all supported social media platforms

Supported Platforms (100+):
Facebook, Instagram, Twitter/X, LinkedIn, TikTok, Snapchat, Threads,
YouTube, Twitch, Vimeo, Dailymotion, Rumble, Kick,
Reddit, Discord, Telegram, Mastodon, Tumblr, Bluesky,
Spotify, SoundCloud, Bandcamp, Last.fm,
GitHub, GitLab, Bitbucket, DeviantArt, Behance, Dribbble, ArtStation,
Medium, Substack, Hashnode, DEV Community, Stack Overflow, HackerNews,
Kaggle, Hugging Face, Flickr, 500px, VSCO, Unsplash,
Steam, Xbox, Epic Games, Roblox, Chess.com,
Quora, Etsy, Redbubble, Patreon, Ko-fi, Buy Me a Coffee, Gumroad,
Linktree, Goodreads, Letterboxd, MyAnimeList, Trakt,
VK, OK.ru, Weibo, Pixiv, Niconico, Strava,
Gravatar, About.me, Keybase, ProductHunt, Instructables,
Giphy, Imgur, Slack, Clubhouse, Pexels, and more.

Note:
This system assumes consent-based datasets only.
Do not use on unauthorized or public scraping sources.