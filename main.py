from fastapi import FastAPI, UploadFile, File
import numpy as np
from face import get_embedding
from faiss_index import search_face, add_face
from db import log_event

app = FastAPI()

@app.post("/add")
async def add_person(person_id: str, file: UploadFile = File(...)):
    image_bytes = await file.read()
    embedding = get_embedding(image_bytes)

    if embedding is None:
        return {"error": "No face detected"}

    add_face(embedding, person_id)
    log_event("add", person_id)

    return {"status": "added"}

@app.post("/search")
async def search(file: UploadFile = File(...)):
    image_bytes = await file.read()
    embedding = get_embedding(image_bytes)

    if embedding is None:
        return {"error": "No face detected"}

    results = search_face(embedding)
    log_event("search", "query")

    return {"results": results}