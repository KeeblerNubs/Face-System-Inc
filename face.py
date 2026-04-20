from insightface.app import FaceAnalysis
import numpy as np
import cv2

app = FaceAnalysis()
app.prepare(ctx_id=0)

def get_embedding(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    faces = app.get(img)
    if not faces:
        return None

    return faces[0].embedding