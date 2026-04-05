"""人脸特征与比对；InsightFace 不可用时使用占位逻辑（开发环境）。"""
import logging

import numpy as np
from django.conf import settings

logger = logging.getLogger('photos')


class FaceRecognizer:
    def __init__(self):
        self._app = None
        try:
            from insightface.app import FaceAnalysis

            self._app = FaceAnalysis(name=settings.INSIGHTFACE_MODEL, providers=['CPUExecutionProvider'])
            self._app.prepare(ctx_id=0, det_size=(640, 640))
            logger.info('InsightFace 已加载')
        except Exception as e:
            logger.warning('InsightFace 未加载，使用占位比对: %s', e)

    def get_face_embedding(self, image_bytes: bytes):
        if self._app is None:
            return np.ones(512, dtype=np.float32)
        import cv2
        import numpy as np

        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if bgr is None:
            return None
        faces = self._app.get(bgr)
        if not faces:
            return None
        return faces[0].embedding

    def compare(self, emb_new, emb_old):
        thr = float(settings.FACE_SIMILARITY_THRESHOLD)
        if emb_new is None or emb_old is None:
            return False, 0.0
        a = np.asarray(emb_new, dtype=np.float32).flatten()
        b = np.asarray(emb_old, dtype=np.float32).flatten()
        denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
        sim = float(np.dot(a, b) / denom)
        return sim >= thr, sim


face_recognizer = FaceRecognizer()
