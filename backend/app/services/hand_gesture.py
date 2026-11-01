"""
backend/app/services/hand_gesture.py — 20-Class Hand Gesture Inference Service
==============================================================================
Inference for 20 numerical hand gesture classes (0-19).
Strict boundary: Unmapped semantics; NOT treated as classroom hand-raising ground truth.
"""

from __future__ import annotations

import io
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F

from backend.app.core.config import REPO_ROOT

logger = logging.getLogger(__name__)


class HandGestureCNN(nn.Module):
    def __init__(self, num_classes: int = 20):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            nn.Dropout2d(0.1),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            nn.Dropout2d(0.2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 12 * 12, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x))


class HandGestureService:
    def __init__(self):
        self.checkpoint_dir = REPO_ROOT / "models" / "checkpoints" / "hand_gesture"
        self.checkpoint_path = self.checkpoint_dir / "best_gesture_cnn.pth"
        self.mapping_path = self.checkpoint_dir / "class_mapping.json"
        self.metrics_path = self.checkpoint_dir / "evaluation_results.json"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self._model: Optional[HandGestureCNN] = None
        self._mappings: Optional[dict] = None

    def _get_mappings(self) -> dict:
        if self._mappings is None:
            if self.mapping_path.is_file():
                with open(self.mapping_path, "r", encoding="utf-8") as f:
                    self._mappings = json.load(f)
            else:
                self._mappings = {"classes": [str(i) for i in range(20)]}
        return self._mappings

    def _get_model(self) -> HandGestureCNN:
        if self._model is None:
            if not self.checkpoint_path.is_file():
                raise FileNotFoundError(f"Hand gesture checkpoint not found at: {self.checkpoint_path}")
            mappings = self._get_mappings()
            classes = mappings.get("classes", [str(i) for i in range(20)])
            model = HandGestureCNN(num_classes=len(classes))
            checkpoint = torch.load(self.checkpoint_path, map_location=self.device)
            state_dict = checkpoint["model_state_dict"] if "model_state_dict" in checkpoint else checkpoint
            model.load_state_dict(state_dict)
            model.to(self.device)
            model.eval()
            self._model = model
        return self._model

    def predict(self, image_input: Union[bytes, Image.Image, np.ndarray]) -> Dict[str, Any]:
        if isinstance(image_input, bytes):
            if len(image_input) == 0:
                raise ValueError("Uploaded image buffer is empty.")
            img = Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, np.ndarray):
            img = Image.fromarray(image_input)
        elif isinstance(image_input, Image.Image):
            img = image_input
        else:
            raise TypeError("Unsupported image input type.")

        img = img.convert("L").resize((50, 50))
        arr = np.array(img, dtype=np.float32) / 255.0
        tensor = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0)  # (1, 1, 50, 50)
        tensor = ((tensor - 0.5) / 0.5).to(self.device)

        model = self._get_model()
        mappings = self._get_mappings()
        classes = mappings.get("classes", [str(i) for i in range(20)])

        t0 = time.perf_counter()
        with torch.no_grad():
            logits = model(tensor)
            probs = F.softmax(logits, dim=1).squeeze(0)
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        top3 = torch.topk(probs, k=min(3, len(probs))).indices.cpu().numpy()
        top3_list = []
        for idx in top3:
            conf = float(probs[idx].item())
            cls_name = str(classes[idx]) if idx < len(classes) else str(idx)
            top3_list.append({"classId": int(idx), "className": cls_name, "confidence": round(conf, 4)})

        best = top3_list[0]
        return {
            "predictedClass": best["className"],
            "classId": best["classId"],
            "confidence": best["confidence"],
            "top3Predictions": top3_list,
            "inferenceTimeMs": latency_ms,
            "device": str(self.device),
            "modelName": "HandGestureCNN-20",
            "provenance": "TRAINED MODEL",
            "status": "SUCCESS",
            "boundaryIsolation": "Numerical classes 0-19 only; NOT mapped to classroom hand-raising without verified ground truth",
        }

    def get_status_info(self) -> Dict[str, Any]:
        metrics = None
        if self.metrics_path.is_file():
            try:
                with open(self.metrics_path, "r", encoding="utf-8") as f:
                    metrics = json.load(f)
            except Exception:
                pass

        return {
            "module": "hand_gesture_recognition",
            "status": "READY" if self.checkpoint_path.is_file() else "CHECKPOINT_NOT_FOUND",
            "checkpointPath": str(self.checkpoint_path),
            "numClasses": 20,
            "device": str(self.device),
            "provenance": "TRAINED MODEL",
            "trainingDataset": "Kaggle Hand Gesture Recognition (20 classes: 0-19)",
            "evaluationMetrics": metrics,
            "boundaryIsolation": "Classes 0-19 remain numerical; unmapped to classroom behavior",
        }


hand_gesture_service = HandGestureService()

