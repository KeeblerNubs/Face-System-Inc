import httpx
import asyncio
from typing import Optional

PLATFORMS = {
    # Major social networks
    "Facebook": "https://www.facebook.com/{}",
    "Instagram": "https://www.instagram.com/{}",
    "Twitter": "https://x.com/{}",
    "LinkedIn": "https://www.linkedin.com/in/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "Snapchat": "https://www.snapchat.com/add/{}",
    "Threads": "https://www.threads.net/@{}",

    # Video platforms
    "YouTube": "https://www.youtube.com/@{}",
    "Twitch": "https://www.twitch.tv/{}",
    "Vimeo": "https://vimeo.com/{}",
    "Dailymotion": "https://www.dailymotion.com/{}",
    "Rumble": "https://rumble.com/user/{}",
    "Kick": "https://kick.com/{}",

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

    # Photography
    "Flickr": "https://www.flickr.com/people/{}",
    "500px": "https://500px.com/p/{}",
    "VSCO": "https://vsco.co/{}",
    "Unsplash": "https://unsplash.com/@{}",

    # Gaming
    "Steam": "https://steamcommunity.com/id/{}",
    "Xbox": "https://www.xbox.com/en-US/play/user/{}",
    "Epic Games": "https://store.epicgames.com/u/{}",
    "Roblox": "https://www.roblox.com/user.aspx?username={}",
    "Chess.com": "https://www.chess.com/member/{}",

    # Forums / Q&A
    "Quora": "https://www.quora.com/profile/{}",

    # E-commerce / other
    "Etsy": "https://www.etsy.com/shop/{}",
    "Redbubble": "https://www.redbubble.com/people/{}",
    "Patreon": "https://www.patreon.com/{}",
    "Ko-fi": "https://ko-fi.com/{}",
    "Buy Me a Coffee": "https://buymeacoffee.com/{}",
    "Gumroad": "https://gumroad.com/{}",
    "Linktree": "https://linktr.ee/{}",

    # Reviews / media tracking
    "Goodreads": "https://www.goodreads.com/{}",
    "Letterboxd": "https://letterboxd.com/{}",
    "MyAnimeList": "https://myanimelist.net/profile/{}",
    "Trakt": "https://trakt.tv/users/{}",

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


async def _check_platform(
    client: httpx.AsyncClient,
    platform: str,
    url: str,
) -> Optional[dict]:
    try:
        resp = await client.get(url, follow_redirects=True, timeout=TIMEOUT)
        if resp.status_code == 200:
            final_url = str(resp.url)
            if _looks_like_valid_profile(platform, final_url, resp.text):
                return {"platform": platform, "url": url, "status": "found"}
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
        "404",
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


async def search_username(username: str) -> list[dict]:
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    results: list[dict] = []

    async def _bounded_check(
        client: httpx.AsyncClient, platform: str, url: str
    ) -> None:
        async with semaphore:
            result = await _check_platform(client, platform, url)
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
    username: str, platforms: list[str]
) -> list[dict]:
    selected = {
        p: PLATFORMS[p] for p in platforms if p in PLATFORMS
    }
    if not selected:
        return []

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    results: list[dict] = []

    async def _bounded_check(
        client: httpx.AsyncClient, platform: str, url: str
    ) -> None:
        async with semaphore:
            result = await _check_platform(client, platform, url)
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


def list_supported_platforms() -> list[str]:
    return sorted(PLATFORMS.keys())
