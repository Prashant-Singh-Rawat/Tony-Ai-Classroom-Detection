"""
backend/app/services/ocr/service.py — Whiteboard & Slide OCR Service via EasyOCR
================================================================================
Integrates EasyOCR for extracting handwritten and typed lecture board content.
All outputs are labeled as PRETRAINED MODEL / REAL_PROCESSING.
Does not claim handwritten text recognition is perfect; outputs confidence metrics.
"""

from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
from PIL import Image

from backend.app.schemas.common import DataStatus


class OcrService:
    """Manages EasyOCR whiteboard and slide text extraction."""

    def __init__(self) -> None:
        self.status: DataStatus = DataStatus.READY
        self.engine: str = "EasyOCR"
        self._reader = None

    def is_available(self) -> bool:
        """Returns True since EasyOCR is installed."""
        return True

    def get_status_info(self) -> dict:
        return {
            "module": "whiteboard_ocr",
            "status": "READY",
            "engine": self.engine,
            "device": "cpu",
            "ready_for_ocr": True,
            "provenance": "PRETRAINED MODEL",
            "limitations": "Handwritten blackboard formulas may have lower confidence than printed slides.",
        }

    def _get_reader(self):
        """Lazy loader for EasyOCR reader."""
        if self._reader is None:
            import easyocr
            # CPU mode for HP Victus compatibility
            self._reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        return self._reader

    def extract_text(self, image_source: str | bytes) -> Dict[str, Any]:
        """
        Extracts text from an image path or raw bytes.
        Returns extracted lines, bounding boxes, and confidence scores.
        """
        temp_path: Optional[str] = None
        if isinstance(image_source, bytes):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(image_source)
                temp_path = tmp.name
            img_target = temp_path
        else:
            img_target = image_source

        if not os.path.isfile(img_target):
            raise FileNotFoundError(f"Image not found for OCR: {img_target}")

        try:
            reader = self._get_reader()
            raw_results = reader.readtext(img_target)

            text_blocks = []
            extracted_lines = []
            confidences = []

            for bbox, text, conf in raw_results:
                clean_text = text.strip()
                if clean_text:
                    conf_float = round(float(conf), 3)
                    confidences.append(conf_float)
                    extracted_lines.append(clean_text)
                    text_blocks.append({
                        "text": clean_text,
                        "confidence": conf_float,
                        "bbox": [[int(pt[0]), int(pt[1])] for pt in bbox],
                    })

            full_text = "\n".join(extracted_lines)
            avg_conf = round(sum(confidences) / len(confidences), 3) if confidences else 0.0

            return {
                "engine": self.engine,
                "full_text": full_text,
                "text_blocks": text_blocks,
                "overall_confidence": avg_conf,
                "block_count": len(text_blocks),
                "data_source": "REAL_PROCESSING",
                "provenance": "PRETRAINED MODEL",
            }
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass


ocr_service = OcrService()
