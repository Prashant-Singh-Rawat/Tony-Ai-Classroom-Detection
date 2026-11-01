"""
backend/app/services/sign_language.py — Sign Language MNIST Inference Service
==============================================================================
Inference for 24 static ASL alphabet gesture classes (0-25, excluding J and Z).
Strict boundary: Isolated from live classroom hand-raising detection.
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


class SignLanguageCNN(nn.Module):
    def __init__(self, num_classes: int = 24):
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
            nn.Linear(64 * 7 * 7, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x))


class SignLanguageService:
    def __init__(self):
        self.checkpoint_dir = REPO_ROOT / "models" / "checkpoints" / "sign_language"
        self.checkpoint_path = self.checkpoint_dir / "best_sign_language_cnn.pth"
        self.mapping_path = self.checkpoint_dir / "class_mapping.json"
        self.metrics_path = self.checkpoint_dir / "evaluation_results.json"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self._model: Optional[SignLanguageCNN] = None
        self._mappings: Optional[dict] = None

    def _get_mappings(self) -> dict:
        if self._mappings is None:
            if self.mapping_path.is_file():
                with open(self.mapping_path, "r", encoding="utf-8") as f:
                    self._mappings = json.load(f)
            else:
                raw_classes = [i for i in range(25) if i not in (9, 25)]
                self._mappings = {
                    "raw_classes": raw_classes,
                    "idx_to_letter": {str(idx): chr(ord('A') + c) for idx, c in enumerate(raw_classes)},
                }
        return self._mappings

    def _get_model(self) -> SignLanguageCNN:
        if self._model is None:
            if not self.checkpoint_path.is_file():
                raise FileNotFoundError(f"Sign Language checkpoint not found at: {self.checkpoint_path}")
            mappings = self._get_mappings()
            num_classes = len(mappings.get("raw_classes", [])) or 24
            model = SignLanguageCNN(num_classes=num_classes)
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

        img = img.convert("L").resize((28, 28))
        arr = np.array(img, dtype=np.float32) / 255.0
        tensor = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0)  # (1, 1, 28, 28)
        tensor = ((tensor - 0.5) / 0.5).to(self.device)

        model = self._get_model()
        mappings = self._get_mappings()
        idx_to_letter = mappings.get("idx_to_letter", {})

        t0 = time.perf_counter()
        with torch.no_grad():
            logits = model(tensor)
            probs = F.softmax(logits, dim=1).squeeze(0)
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        top3 = torch.topk(probs, k=min(3, len(probs))).indices.cpu().numpy()
        top3_list = []
        for idx in top3:
            conf = float(probs[idx].item())
            letter = idx_to_letter.get(str(idx), str(idx))
            top3_list.append({"letter": letter, "classIndex": int(idx), "confidence": round(conf, 4)})

        best = top3_list[0]
        return {
            "predictedLetter": best["letter"],
            "classIndex": best["classIndex"],
            "confidence": best["confidence"],
            "top3Predictions": top3_list,
            "inferenceTimeMs": latency_ms,
            "device": str(self.device),
            "modelName": "SignLanguageCNN",
            "provenance": "TRAINED MODEL",
            "status": "SUCCESS",
            "boundaryIsolation": "Isolated static ASL alphabet classifier; strictly NOT connected to classroom hand-raising detection",
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
            "module": "sign_language_mnist",
            "status": "READY" if self.checkpoint_path.is_file() else "CHECKPOINT_NOT_FOUND",
            "checkpointPath": str(self.checkpoint_path),
            "numClasses": 24,
            "device": str(self.device),
            "provenance": "TRAINED MODEL",
            "trainingDataset": "Sign Language MNIST (24 ASL Alphabet Classes)",
            "evaluationMetrics": metrics,
            "boundaryIsolation": "Strictly separate from classroom hand-raising detection",
        }


sign_language_service = SignLanguageService()

