"""Profile data extraction from social media pages.

Parses HTML responses to pull structured profile information including
profile pictures, display names, bios, and other metadata using
OpenGraph tags, meta elements, and platform-specific selectors.
"""

from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup


def extract_profile_data(
    platform: str,
    url: str,
    html: str,
) -> dict:
    """Return structured profile data scraped from *html*.

    Fields returned (all optional):
        profile_picture, display_name, bio, extra (dict of platform-specific
        metadata such as follower counts).
    """
    soup = BeautifulSoup(html[:50_000], "lxml")

    picture = _extract_profile_picture(soup, url)
    display_name = _extract_display_name(soup, platform)
    bio = _extract_bio(soup, platform)
    extra = _extract_extra(soup, platform)

    return {
        "profile_picture": picture,
        "display_name": display_name,
        "bio": bio,
        **extra,
    }


# -- profile picture --------------------------------------------------------

_OG_IMAGE_ATTRS = [
    {"property": "og:image"},
    {"name": "og:image"},
    {"property": "og:image:secure_url"},
]

_TWITTER_IMAGE_ATTRS = [
    {"name": "twitter:image"},
    {"name": "twitter:image:src"},
    {"property": "twitter:image"},
]

_ICON_LINK_RELS = [
    "apple-touch-icon",
    "icon",
    "shortcut icon",
]


def _extract_profile_picture(soup: BeautifulSoup, page_url: str) -> Optional[str]:
    for attrs in _OG_IMAGE_ATTRS:
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            return _abs(tag["content"], page_url)

    for attrs in _TWITTER_IMAGE_ATTRS:
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            return _abs(tag["content"], page_url)

    img = soup.select_one(
        "img.avatar, img.profile-pic, img.user-avatar, "
        "img[class*='avatar'], img[class*='profile'], "
        "img[alt*='avatar'], img[alt*='profile']"
    )
    if img and img.get("src"):
        return _abs(img["src"], page_url)

    for rel in _ICON_LINK_RELS:
        link = soup.find("link", rel=rel)
        if link and link.get("href"):
            return _abs(link["href"], page_url)

    return None


# -- display name ------------------------------------------------------------

_NAME_META_ATTRS = [
    {"property": "og:title"},
    {"name": "og:title"},
    {"property": "profile:first_name"},
    {"name": "twitter:title"},
]


def _extract_display_name(soup: BeautifulSoup, platform: str) -> Optional[str]:
    for attrs in _NAME_META_ATTRS:
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            raw = tag["content"].strip()
            cleaned = _clean_title(raw, platform)
            if cleaned:
                return cleaned

    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        cleaned = _clean_title(title_tag.string.strip(), platform)
        if cleaned:
            return cleaned

    return None


_TITLE_STRIP_PATTERNS = [
    re.compile(r"\s*[|\-\u2013\u2014]\s*.{2,}$"),
    re.compile(r"\s*on\s+(GitHub|Instagram|Twitter|LinkedIn|Medium)\s*$", re.I),
    re.compile(r"\(@\w+\)"),
]


def _clean_title(raw: str, platform: str) -> Optional[str]:
    text = raw
    for pat in _TITLE_STRIP_PATTERNS:
        text = pat.sub("", text)
    text = text.strip(" -\u2013\u2014|")
    if len(text) < 2 or text.lower() in {"home", "login", "sign up", platform.lower()}:
        return None
    return text


# -- bio / description -------------------------------------------------------

_BIO_META_ATTRS = [
    {"property": "og:description"},
    {"name": "og:description"},
    {"name": "description"},
    {"name": "twitter:description"},
]


def _extract_bio(soup: BeautifulSoup, platform: str) -> Optional[str]:
    for attrs in _BIO_META_ATTRS:
        tag = soup.find("meta", attrs=attrs)
        if tag and tag.get("content"):
            text = tag["content"].strip()
            if len(text) > 10:
                return text[:1000]

    bio_el = soup.select_one(
        "[class*='bio'], [class*='description'], "
        "[class*='about'], [class*='summary']"
    )
    if bio_el:
        text = bio_el.get_text(separator=" ", strip=True)
        if len(text) > 10:
            return text[:1000]

    return None


# -- extra metadata ----------------------------------------------------------

_FOLLOWER_PATTERN = re.compile(
    r"([\d,.]+[KkMm]?)\s*(?:followers?|following|subscribers?|connections?)",
    re.I,
)

_STAT_PATTERNS = {
    "followers": re.compile(r"([\d,.]+[KkMm]?)\s*followers?", re.I),
    "following": re.compile(r"([\d,.]+[KkMm]?)\s*following", re.I),
    "posts": re.compile(r"([\d,.]+[KkMm]?)\s*(?:posts?|tweets?|repos?|gists?)", re.I),
}


def _extract_extra(soup: BeautifulSoup, platform: str) -> dict:
    text_block = soup.get_text(separator=" ", strip=True)[:10_000]
    stats: dict[str, str] = {}
    for key, pat in _STAT_PATTERNS.items():
        m = pat.search(text_block)
        if m:
            stats[key] = m.group(1)
    if stats:
        return {"stats": stats}
    return {}


# -- helpers -----------------------------------------------------------------

def _abs(url: str, base: str) -> str:
    if url.startswith(("http://", "https://", "//")):
        return url if not url.startswith("//") else "https:" + url
    return urljoin(base, url)
