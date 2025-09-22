from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from PIL import Image

@dataclass(frozen=True)
class OcrRequest:
    images: List[Image.Image]
    # optional flags that Surya supports
    language_hints: Optional[List[str]] = None  # you can add hints; Surya supports 90+ langs
    extra: Dict[str, Any] | None = None

@dataclass(frozen=True)
class OcrResponse:
    raw: Any               # Surya’s native dict/list payload
    meta: Dict[str, Any]   # timings, counts, device, batch sizes

class OcrEngine:
    async def health_check(self) -> bool: raise NotImplementedError
    async def ocr(self, req: OcrRequest) -> OcrResponse: raise NotImplementedError