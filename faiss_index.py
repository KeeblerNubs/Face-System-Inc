import faiss
import numpy as np
from typing import Optional

dimension = 512
index = faiss.IndexFlatL2(dimension)

metadata = []


def add_face(
    embedding,
    person_id: str,
    username: Optional[str] = None,
    social_profiles: Optional[list] = None,
):
    global index, metadata

    vec = np.array([embedding]).astype("float32")
    index.add(vec)

    metadata.append({
        "person_id": person_id,
        "username": username,
        "social_profiles": social_profiles or [],
    })


def search_face(embedding, k=5):
    vec = np.array([embedding]).astype("float32")
    D, I = index.search(vec, k)

    results = []
    for i, idx in enumerate(I[0]):
        if idx == -1:
            continue
        entry = metadata[idx]
        results.append({
            "person_id": entry["person_id"],
            "distance": float(D[0][i]),
            "username": entry.get("username"),
            "social_profiles": entry.get("social_profiles", []),
        })

    return results