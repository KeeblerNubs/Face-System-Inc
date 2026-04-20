from __future__ import annotations

import cv2
import numpy as np
from insightface.app import FaceAnalysis


def _build_face_app() -> FaceAnalysis:
    """Initialize InsightFace with GPU first and CPU fallback."""
    analyzer = FaceAnalysis()
    try:
        analyzer.prepare(ctx_id=0)
    except Exception:
        analyzer.prepare(ctx_id=-1)
    return analyzer


app = _build_face_app()


def get_embedding(image_bytes: bytes) -> np.ndarray | None:
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return None

    faces = app.get(img)
    if not faces:
        return None

    return faces[0].embedding
