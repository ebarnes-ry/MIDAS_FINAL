#generates an ocr output for an input image with surya ocr
from typing import Any
from PIL import Image
import time

from .ocr_base import OcrEngine, OcrRequest, OcrResponse


class SuryaOCRProvider(OcrEngine):
    def __init__(self):
        self.det_predictor = None
        self.rec_predictor = None

    async def _lazy_load(self) -> Any:
        if self.det_predictor is None or self.rec_predictor is None:
            from surya.foundation import FoundationPredictor
            from surya.detection import DetectionPredictor
            from surya.recognition import RecognitionPredictor

            foundation = FoundationPredictor()
            self.det_predictor = DetectionPredictor()
            self.rec_predictor = RecognitionPredictor(foundation)
        
        return {"det_predictor": self.det_predictor, "rec_predictor": self.rec_predictor}

    async def ocr(self, req: OcrRequest) -> OcrResponse:
        await self._lazy_load()

        t0 = time.perf_counter()
        results = self.rec_predictor(req.images, det_predictor=self.det_predictor)
        latency = time.perf_counter() - t0

        # Return all results, not just the first one
        raw_result = results if results else []
        meta = {"latency": latency, "image_count": len(req.images)}
        return OcrResponse(raw=raw_result, meta=meta)

    async def health_check(self) -> bool:
        try:
            await self._lazy_load()
            return True
        except Exception:
            return False