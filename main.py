from fastapi import FastAPI, UploadFile, File, Query
from typing import Optional
import numpy as np
from face import get_embedding
from faiss_index import search_face, add_face
from db import log_event
from social_media import (
    search_username,
    search_username_on_platforms,
    list_supported_platforms,
)

app = FastAPI(title="Face Recognition & Social Media Search System")


@app.post("/add")
async def add_person(
    person_id: str,
    file: UploadFile = File(...),
    username: Optional[str] = None,
):
    image_bytes = await file.read()
    embedding = get_embedding(image_bytes)

    if embedding is None:
        return {"error": "No face detected"}

    social_profiles = []
    if username:
        social_profiles = await search_username(username)

    add_face(embedding, person_id, username=username, social_profiles=social_profiles)
    log_event("add", person_id)

    return {"status": "added", "social_profiles": social_profiles}


@app.post("/search")
async def search(file: UploadFile = File(...)):
    image_bytes = await file.read()
    embedding = get_embedding(image_bytes)

    if embedding is None:
        return {"error": "No face detected"}

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
    log_event("social_search", username)

    if platforms:
        platform_list = [p.strip() for p in platforms.split(",")]
        results = await search_username_on_platforms(username, platform_list)
    else:
        results = await search_username(username)

    return {
        "username": username,
        "platforms_checked": len(list_supported_platforms()) if not platforms else len(platform_list),
        "profiles_found": len(results),
        "results": results,
    }


@app.get("/platforms")
async def get_platforms():
    platforms = list_supported_platforms()
    return {"count": len(platforms), "platforms": platforms}