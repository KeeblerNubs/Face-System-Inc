import faiss
import numpy as np

dimension = 512
index = faiss.IndexFlatL2(dimension)

metadata = []

def add_face(embedding, person_id):
    global index, metadata

    vec = np.array([embedding]).astype("float32")
    index.add(vec)

    metadata.append({
        "person_id": person_id
    })

def search_face(embedding, k=5):
    vec = np.array([embedding]).astype("float32")
    D, I = index.search(vec, k)

    results = []
    for i, idx in enumerate(I[0]):
        if idx == -1:
            continue
        results.append({
            "person_id": metadata[idx]["person_id"],
            "distance": float(D[0][i])
        })

    return results