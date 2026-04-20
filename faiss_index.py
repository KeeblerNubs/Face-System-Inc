from __future__ import annotations

from typing import Any, Optional

import faiss
import numpy as np

index: Optional[faiss.IndexFlatL2] = None
embedding_dimension: Optional[int] = None
metadata: list[dict[str, Any]] = []


def _ensure_index(dimension: int) -> None:
    global index, embedding_dimension
    if index is None:
        index = faiss.IndexFlatL2(dimension)
        embedding_dimension = dimension


def add_face(
    embedding: np.ndarray,
    person_id: str,
    username: Optional[str] = None,
    social_profiles: Optional[list] = None,
) -> None:
    global index, metadata, embedding_dimension

    vector = np.asarray(embedding, dtype="float32").reshape(1, -1)
    dimension = vector.shape[1]

    _ensure_index(dimension)
    if embedding_dimension != dimension:
        raise ValueError(
            f"Embedding dimension mismatch: expected {embedding_dimension}, got {dimension}."
        )

    index.add(vector)
    metadata.append(
        {
            "person_id": person_id,
            "username": username,
            "social_profiles": social_profiles or [],
        }
    )


def search_face(embedding: np.ndarray, k: int = 5) -> list[dict[str, Any]]:
    if index is None or not metadata:
        return []

    vector = np.asarray(embedding, dtype="float32").reshape(1, -1)
    if embedding_dimension is not None and vector.shape[1] != embedding_dimension:
        return []

    result_count = min(k, len(metadata))
    distances, indices = index.search(vector, result_count)

    results = []
    for i, idx in enumerate(indices[0]):
        if idx == -1:
            continue
        entry = metadata[idx]
        results.append(
            {
                "person_id": entry["person_id"],
                "distance": float(distances[0][i]),
                "username": entry.get("username"),
                "social_profiles": entry.get("social_profiles", []),
            }
        )

    return results
