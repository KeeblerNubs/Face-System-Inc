from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile

from db import log_event
from face import get_embedding
from faiss_index import add_face, search_face
from phone import reverse_phone_lookup
from social_media import (
    list_supported_platforms,
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

        results = await search_username_on_platforms(username, platform_list)
        checked_count = len(platform_list)
    else:
        results = await search_username(username)
        checked_count = len(supported)

    return {
        "username": username,
        "platforms_checked": checked_count,
        "profiles_found": len(results),
        "results": results,
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
