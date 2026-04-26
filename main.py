from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile

from db import log_event
from face import get_embedding
from faiss_index import add_face, search_face
from phone import reverse_phone_lookup
from social_media import (
    download_profile_picture,
    generate_username_variations,
    list_supported_platforms,
    search_by_name,
    search_username,
    search_username_on_platforms,
    validate_username,
)

app = FastAPI(title="Face Recognition & Social Media Search System")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/add")
async def add_person(
    person_id: str,
    file: UploadFile = File(...),
    username: Optional[str] = None,
):
    image_bytes = await file.read()
    embedding = get_embedding(image_bytes)

    if embedding is None:
        raise HTTPException(status_code=400, detail="No face detected in image.")

    social_profiles = []
    if username:
        try:
            validate_username(username)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        social_profiles = await search_username(username)

    try:
        add_face(embedding, person_id, username=username, social_profiles=social_profiles)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_event("add", person_id)
    return {"status": "added", "social_profiles": social_profiles}


@app.post("/search")
async def search(file: UploadFile = File(...)):
    image_bytes = await file.read()
    embedding = get_embedding(image_bytes)

    if embedding is None:
        raise HTTPException(status_code=400, detail="No face detected in image.")

    results = search_face(embedding)
    log_event("search", "query")
    return {"results": results}


@app.get("/search/social")
async def search_social(
    username: str,
    platforms: Optional[str] = Query(
        default=None,
        description="Comma-separated platform names to search (default: all)",
    ),
    scrape: bool = Query(
        default=False,
        description="When true, scrape profile pictures, bios, and display names",
    ),
):
    try:
        validate_username(username)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_event("social_search", username)

    supported = set(list_supported_platforms())
    if platforms:
        platform_list = [p.strip() for p in platforms.split(",") if p.strip()]
        invalid_platforms = [p for p in platform_list if p not in supported]
        if invalid_platforms:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unsupported platforms requested: "
                    + ", ".join(sorted(invalid_platforms))
                ),
            )

        results = await search_username_on_platforms(
            username, platform_list, scrape=scrape,
        )
        checked_count = len(platform_list)
    else:
        results = await search_username(username, scrape=scrape)
        checked_count = len(supported)

    return {
        "username": username,
        "platforms_checked": checked_count,
        "profiles_found": len(results),
        "results": results,
    }


@app.get("/search/name")
async def search_name(
    name: str = Query(
        ..., description="Real name to search (e.g. 'John Doe')",
    ),
    scrape: bool = Query(
        default=False,
        description="When true, scrape profile pictures, bios, and display names",
    ),
):
    """Search social platforms using username variations generated from a real name."""
    if len(name.strip()) < 2:
        raise HTTPException(
            status_code=400,
            detail="Name must be at least 2 characters.",
        )

    log_event("name_search", name)
    result = await search_by_name(name, scrape=scrape)
    return result


@app.get("/search/name/usernames")
async def preview_name_usernames(
    name: str = Query(
        ..., description="Real name to generate username variations for",
    ),
):
    """Preview the username variations that would be tried for a given name."""
    if len(name.strip()) < 2:
        raise HTTPException(
            status_code=400,
            detail="Name must be at least 2 characters.",
        )
    usernames = generate_username_variations(name)
    return {"name": name, "variations_count": len(usernames), "usernames": usernames}


@app.post("/search/identify")
async def identify_person(
    file: UploadFile = File(...),
    name: Optional[str] = Query(
        default=None,
        description="Person's real name to also search social platforms",
    ),
    username: Optional[str] = Query(
        default=None,
        description="Known username to search social platforms",
    ),
    scrape: bool = Query(
        default=False,
        description="When true, scrape profile pictures, bios, and display names",
    ),
):
    """Upload a face photo and optionally provide a name/username to combine
    face matching with social media discovery in a single request."""
    image_bytes = await file.read()
    embedding = get_embedding(image_bytes)

    face_matches = []
    if embedding is not None:
        face_matches = search_face(embedding)
    else:
        if not name and not username:
            raise HTTPException(
                status_code=400,
                detail="No face detected and no name or username provided.",
            )

    social_results: list[dict] = []
    name_search_info: dict | None = None

    if username:
        try:
            validate_username(username)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        social_results = await search_username(username, scrape=scrape)

    if name:
        name_data = await search_by_name(name, scrape=scrape)
        name_search_info = {
            "name": name,
            "usernames_tried": name_data["usernames_tried"],
        }
        seen_urls = {r["url"] for r in social_results}
        for r in name_data["results"]:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                social_results.append(r)

    log_event("identify", name or username or "photo_only")
    return {
        "face_detected": embedding is not None,
        "face_matches": face_matches,
        "social_profiles_found": len(social_results),
        "social_results": social_results,
        "name_search": name_search_info,
    }


@app.get("/platforms")
async def get_platforms():
    platforms = list_supported_platforms()
    return {"count": len(platforms), "platforms": platforms}


@app.get("/search/phone")
async def search_phone(
    number: str = Query(..., description="Phone number in E.164 or national format"),
    region: Optional[str] = Query(
        default=None,
        description="ISO 3166-1 alpha-2 region code (e.g. US, GB) for national-format numbers",
    ),
    numverify: bool = Query(
        default=False,
        description="If true, also query Numverify (requires NUMVERIFY_API_KEY env var)",
    ),
):
    try:
        result = await reverse_phone_lookup(
            number, default_region=region, use_numverify=numverify
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_event("phone_lookup", result["formats"]["e164"])
    return result
