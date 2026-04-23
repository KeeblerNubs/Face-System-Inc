"""Asynchronous OSINT engine for checking username presence and scraping
profile data across 100+ social media platforms.

Supports:
- Username search across all or selected platforms.
- Real-name-to-username variation generation.
- Optional profile scraping (picture, display name, bio, stats).
"""

from __future__ import annotations

import asyncio
import re
from typing import Optional

import httpx

from scraper import extract_profile_data

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")


def validate_username(username: str) -> str:
    if not USERNAME_PATTERN.match(username):
        raise ValueError(
            "Username contains invalid characters. "
            "Only alphanumeric, dots, underscores, and hyphens are allowed."
        )
    return username


# ---------------------------------------------------------------------------
# Platform registry  (100+ entries)
# ---------------------------------------------------------------------------

PLATFORMS = {
    # Major social networks
    "Facebook": "https://www.facebook.com/{}",
    "Instagram": "https://www.instagram.com/{}",
    "Twitter": "https://x.com/{}",
    "LinkedIn": "https://www.linkedin.com/in/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "Snapchat": "https://www.snapchat.com/add/{}",
    "Threads": "https://www.threads.net/@{}",
    "Pinterest": "https://www.pinterest.com/{}",

    # Video platforms
    "YouTube": "https://www.youtube.com/@{}",
    "Twitch": "https://www.twitch.tv/{}",
    "Vimeo": "https://vimeo.com/{}",
    "Dailymotion": "https://www.dailymotion.com/{}",
    "Rumble": "https://rumble.com/user/{}",
    "Kick": "https://kick.com/{}",
    "Odysee": "https://odysee.com/@{}",
    "BitChute": "https://www.bitchute.com/channel/{}",

    # Messaging / community
    "Reddit": "https://www.reddit.com/user/{}",
    "Discord": "https://discord.com/users/{}",
    "Telegram": "https://t.me/{}",
    "Mastodon": "https://mastodon.social/@{}",
    "Tumblr": "https://{}.tumblr.com",
    "Bluesky": "https://bsky.app/profile/{}.bsky.social",

    # Music / audio
    "Spotify": "https://open.spotify.com/user/{}",
    "SoundCloud": "https://soundcloud.com/{}",
    "Bandcamp": "https://{}.bandcamp.com",
    "Last.fm": "https://www.last.fm/user/{}",
    "Mixcloud": "https://www.mixcloud.com/{}",
    "Deezer": "https://www.deezer.com/profile/{}",

    # Professional / creative
    "GitHub": "https://github.com/{}",
    "GitLab": "https://gitlab.com/{}",
    "Bitbucket": "https://bitbucket.org/{}",
    "DeviantArt": "https://www.deviantart.com/{}",
    "Behance": "https://www.behance.net/{}",
    "Dribbble": "https://dribbble.com/{}",
    "ArtStation": "https://www.artstation.com/{}",
    "Medium": "https://medium.com/@{}",
    "Substack": "https://{}.substack.com",
    "Hashnode": "https://hashnode.com/@{}",
    "DEV Community": "https://dev.to/{}",
    "Stack Overflow": "https://stackoverflow.com/users/{}",
    "HackerNews": "https://news.ycombinator.com/user?id={}",
    "Kaggle": "https://www.kaggle.com/{}",
    "Hugging Face": "https://huggingface.co/{}",
    "CodePen": "https://codepen.io/{}",
    "Replit": "https://replit.com/@{}",
    "Glitch": "https://glitch.com/@{}",
    "HackerRank": "https://www.hackerrank.com/{}",
    "LeetCode": "https://leetcode.com/{}",
    "Codeforces": "https://codeforces.com/profile/{}",
    "NPM": "https://www.npmjs.com/~{}",
    "PyPI": "https://pypi.org/user/{}",

    # Photography
    "Flickr": "https://www.flickr.com/people/{}",
    "500px": "https://500px.com/p/{}",
    "VSCO": "https://vsco.co/{}",
    "Unsplash": "https://unsplash.com/@{}",
    "SmugMug": "https://{}.smugmug.com",
    "EyeEm": "https://www.eyeem.com/u/{}",

    # Gaming
    "Steam": "https://steamcommunity.com/id/{}",
    "Xbox": "https://www.xbox.com/en-US/play/user/{}",
    "Epic Games": "https://store.epicgames.com/u/{}",
    "Roblox": "https://www.roblox.com/user.aspx?username={}",
    "Chess.com": "https://www.chess.com/member/{}",
    "Lichess": "https://lichess.org/@/{}",
    "Speedrun.com": "https://www.speedrun.com/user/{}",
    "Itch.io": "https://{}.itch.io",
    "Newgrounds": "https://{}.newgrounds.com",

    # Forums / Q&A
    "Quora": "https://www.quora.com/profile/{}",
    "Ask.fm": "https://ask.fm/{}",

    # E-commerce / other
    "Etsy": "https://www.etsy.com/shop/{}",
    "Redbubble": "https://www.redbubble.com/people/{}",
    "Patreon": "https://www.patreon.com/{}",
    "Ko-fi": "https://ko-fi.com/{}",
    "Buy Me a Coffee": "https://buymeacoffee.com/{}",
    "Gumroad": "https://gumroad.com/{}",
    "Linktree": "https://linktr.ee/{}",
    "Carrd": "https://{}.carrd.co",
    "Fiverr": "https://www.fiverr.com/{}",
    "Freelancer": "https://www.freelancer.com/u/{}",

    # Reviews / media tracking
    "Goodreads": "https://www.goodreads.com/{}",
    "Letterboxd": "https://letterboxd.com/{}",
    "MyAnimeList": "https://myanimelist.net/profile/{}",
    "Trakt": "https://trakt.tv/users/{}",
    "Rate Your Music": "https://rateyourmusic.com/~{}",
    "AniList": "https://anilist.co/user/{}",

    # Regional platforms
    "VK": "https://vk.com/{}",
    "OK.ru": "https://ok.ru/profile/{}",
    "Weibo": "https://weibo.com/{}",
    "Pixiv": "https://www.pixiv.net/users/{}",
    "Niconico": "https://www.nicovideo.jp/user/{}",

    # Fitness / health
    "Strava": "https://www.strava.com/athletes/{}",

    # Miscellaneous
    "Gravatar": "https://gravatar.com/{}",
    "About.me": "https://about.me/{}",
    "Keybase": "https://keybase.io/{}",
    "ProductHunt": "https://www.producthunt.com/@{}",
    "Instructables": "https://www.instructables.com/member/{}",
    "Giphy": "https://giphy.com/{}",
    "Imgur": "https://imgur.com/user/{}",
    "Slack": "https://{}.slack.com",
    "Clubhouse": "https://www.clubhouse.com/@{}",
    "Pexels": "https://www.pexels.com/@{}",
    "Trello": "https://trello.com/{}",
    "Venmo": "https://account.venmo.com/u/{}",
    "CashApp": "https://cash.app/${}",
    "Twitch Tracker": "https://twitchtracker.com/{}",
    "Wattpad": "https://www.wattpad.com/user/{}",
    "Thingiverse": "https://www.thingiverse.com/{}",
    "Disqus": "https://disqus.com/by/{}",
    "Blogger": "https://{}.blogspot.com",
    "WordPress": "https://{}.wordpress.com",
    "Coub": "https://coub.com/{}",
    "Lobsters": "https://lobste.rs/u/{}",
    "Hacker.one": "https://hackerone.com/{}",
    "BugCrowd": "https://bugcrowd.com/{}",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

TIMEOUT = 10.0
MAX_CONCURRENT = 20


# ---------------------------------------------------------------------------
# Platform checking
# ---------------------------------------------------------------------------

async def _check_platform(
    client: httpx.AsyncClient,
    platform: str,
    url: str,
    scrape: bool = False,
) -> Optional[dict]:
    """Check if a profile exists and optionally scrape its data."""
    try:
        resp = await client.get(url, follow_redirects=True, timeout=TIMEOUT)
        if resp.status_code == 200:
            final_url = str(resp.url)
            body = resp.text
            if _looks_like_valid_profile(platform, final_url, body):
                result: dict = {
                    "platform": platform,
                    "url": url,
                    "status": "found",
                }
                if scrape:
                    result["profile"] = extract_profile_data(
                        platform, url, body
                    )
                return result
    except (httpx.RequestError, httpx.HTTPStatusError):
        pass
    return None


def _looks_like_valid_profile(platform: str, final_url: str, body: str) -> bool:
    not_found_signals = [
        "page not found",
        "this page isn't available",
        "user not found",
        "profile not found",
        "nothing here",
        "doesn't exist",
        "does not exist",
        "error 404",
        "sorry, this page",
        "account suspended",
        "this account doesn't exist",
        "no user found",
        "the page you were looking for",
    ]
    lower_body = body[:5000].lower()
    for signal in not_found_signals:
        if signal in lower_body:
            return False

    if "/login" in final_url or "/signup" in final_url:
        return False

    return True


# ---------------------------------------------------------------------------
# Username search
# ---------------------------------------------------------------------------

async def search_username(
    username: str, *, scrape: bool = False,
) -> list[dict]:
    """Search *username* across every registered platform."""
    validate_username(username)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    results: list[dict] = []

    async def _bounded_check(
        client: httpx.AsyncClient, platform: str, url: str,
    ) -> None:
        async with semaphore:
            result = await _check_platform(client, platform, url, scrape=scrape)
            if result is not None:
                results.append(result)

    async with httpx.AsyncClient(headers=HEADERS) as client:
        tasks = [
            _bounded_check(client, platform, url_template.format(username))
            for platform, url_template in PLATFORMS.items()
        ]
        await asyncio.gather(*tasks)

    results.sort(key=lambda r: r["platform"])
    return results


async def search_username_on_platforms(
    username: str,
    platforms: list[str],
    *,
    scrape: bool = False,
) -> list[dict]:
    """Search *username* on a specific subset of platforms."""
    validate_username(username)
    selected = {p: PLATFORMS[p] for p in platforms if p in PLATFORMS}
    if not selected:
        return []

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    results: list[dict] = []

    async def _bounded_check(
        client: httpx.AsyncClient, platform: str, url: str,
    ) -> None:
        async with semaphore:
            result = await _check_platform(client, platform, url, scrape=scrape)
            if result is not None:
                results.append(result)

    async with httpx.AsyncClient(headers=HEADERS) as client:
        tasks = [
            _bounded_check(client, platform, url_template.format(username))
            for platform, url_template in selected.items()
        ]
        await asyncio.gather(*tasks)

    results.sort(key=lambda r: r["platform"])
    return results


# ---------------------------------------------------------------------------
# Name-based search  (generate username variations from a real name)
# ---------------------------------------------------------------------------

def generate_username_variations(name: str) -> list[str]:
    """Generate plausible username variations from a real name.

    Examples for "John Doe":
        johndoe, john.doe, john_doe, john-doe, johnd, jdoe, doejohn, ...
    """
    parts = re.split(r"[\s\-]+", name.strip().lower())
    parts = [re.sub(r"[^a-z0-9]", "", p) for p in parts if p]
    if not parts:
        return []

    variations: list[str] = []

    joined = "".join(parts)
    if joined:
        variations.append(joined)

    if len(parts) >= 2:
        first, last = parts[0], parts[-1]
        variations.extend([
            f"{first}.{last}",
            f"{first}_{last}",
            f"{first}-{last}",
            f"{first}{last}",
            f"{last}{first}",
            f"{last}.{first}",
            f"{last}_{first}",
            f"{first}{last[0]}",
            f"{first[0]}{last}",
            f"{last}{first[0]}",
            f"{first[0]}.{last}",
            f"{first[0]}_{last}",
            f"{first[0]}{last[0]}",
        ])
        for sep in ["", ".", "_", "-"]:
            for yr in ["99", "00", "01", "23", "24"]:
                variations.append(f"{first}{sep}{last}{yr}")

    if len(parts) == 1:
        w = parts[0]
        variations.extend([w, f"{w}1", f"{w}123", f"the{w}", f"{w}_official"])

    seen: set[str] = set()
    unique: list[str] = []
    for v in variations:
        if v and v not in seen and USERNAME_PATTERN.match(v):
            seen.add(v)
            unique.append(v)

    return unique


async def search_by_name(
    name: str, *, scrape: bool = False,
) -> dict:
    """Search social platforms using username variations generated from *name*.

    Returns a dict with the generated usernames tried and all found profiles.
    """
    usernames = generate_username_variations(name)
    if not usernames:
        return {"name": name, "usernames_tried": [], "results": []}

    all_results: list[dict] = []
    seen_urls: set[str] = set()

    for username in usernames:
        results = await search_username(username, scrape=scrape)
        for r in results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                r["matched_username"] = username
                all_results.append(r)

    all_results.sort(key=lambda r: r["platform"])
    return {
        "name": name,
        "usernames_tried": usernames,
        "profiles_found": len(all_results),
        "results": all_results,
    }


# ---------------------------------------------------------------------------
# Profile picture download helper
# ---------------------------------------------------------------------------

async def download_profile_picture(url: str) -> Optional[bytes]:
    """Download a profile picture from *url* and return raw bytes."""
    try:
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
            resp = await client.get(url, timeout=TIMEOUT)
            if resp.status_code == 200 and resp.headers.get(
                "content-type", ""
            ).startswith("image/"):
                return resp.content
    except (httpx.RequestError, httpx.HTTPStatusError):
        pass
    return None


def list_supported_platforms() -> list[str]:
    return sorted(PLATFORMS.keys())
