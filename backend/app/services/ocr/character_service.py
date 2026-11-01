"""
backend/app/services/ocr/character_service.py — Character Recognition Service
=============================================================================
Provides real-time single-character inference using the trained CharacterCNN model.
Classifies alphanumeric characters across 62 classes (0-9, A-Z, a-z).
"""

from __future__ import annotations

import io
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from backend.app.core.config import REPO_ROOT
from backend.app.services.ocr.character_cnn import (
    CharacterCNN,
    build_class_mappings,
    class_name_to_character,
    get_default_class_names,
)

logger = logging.getLogger(__name__)


class CharacterRecognitionService:
    """
    Dedicated inference service for handwritten & printed alphanumeric character recognition.
    Utilizes a custom 3-block CNN trained on the Kaggle English Character Recognition dataset.
    """

    def __init__(
        self,
        checkpoint_dir: Optional[Union[str, Path]] = None,
        device: Optional[str] = None,
    ) -> None:
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else (
            REPO_ROOT / "models" / "checkpoints" / "character_recognition"
        )
        self.checkpoint_path = self.checkpoint_dir / "best_character_cnn.pth"
        self.mapping_path = self.checkpoint_dir / "class_mapping.json"
        self.metrics_path = self.checkpoint_dir / "evaluation_results.json"

        # Hardware profiling
        if device is not None:
            self.device = torch.device(device)
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self._model: Optional[CharacterCNN] = None
        self._class_mappings: Optional[Dict[str, Any]] = None

        # Preprocessing transform
        self._transform = transforms.Compose([
            transforms.Resize((32, 32)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5], std=[0.5]),
        ])

    def _get_mappings(self) -> Dict[str, Any]:
        """Loads or builds class mappings for 62 alphanumeric classes."""
        if self._class_mappings is None:
            if self.mapping_path.is_file():
                try:
                    with open(self.mapping_path, "r", encoding="utf-8") as f:
                        self._class_mappings = json.load(f)
                except Exception as e:
                    logger.warning("Failed to load class_mapping.json: %s. Using default mappings.", e)
                    self._class_mappings = build_class_mappings(get_default_class_names())
            else:
                self._class_mappings = build_class_mappings(get_default_class_names())
        return self._class_mappings

    def _get_model(self) -> CharacterCNN:
        """Lazy-loads model weights from checkpoint into volatile RAM."""
        if self._model is None:
            if not self.checkpoint_path.is_file():
                raise FileNotFoundError(
                    f"Character recognition checkpoint not found at: {self.checkpoint_path}. "
                    "Run scripts/train_character_recognition.py first."
                )

            mappings = self._get_mappings()
            num_classes = len(mappings["classes"])

            model = CharacterCNN(num_classes=num_classes)
            checkpoint = torch.load(self.checkpoint_path, map_location=self.device)

            if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                model.load_state_dict(checkpoint["model_state_dict"])
            else:
                model.load_state_dict(checkpoint)

            model.to(self.device)
            model.eval()
            self._model = model
            logger.info("Loaded CharacterCNN checkpoint successfully on %s", self.device)

        return self._model

    def preprocess_image(self, image_input: Union[bytes, Image.Image, np.ndarray]) -> torch.Tensor:
        """
        Preprocesses an image for CharacterCNN inference:
        - Validates input format
        - Converts to single-channel Grayscale ('L')
        - Resizes to (32, 32)
        - Normalizes to [-1.0, 1.0]
        - Returns (1, 1, 32, 32) batch tensor
        """
        try:
            if isinstance(image_input, bytes):
                if len(image_input) == 0:
                    raise ValueError("Image input buffer is empty.")
                pil_img = Image.open(io.BytesIO(image_input))
            elif isinstance(image_input, np.ndarray):
                if image_input.size == 0:
                    raise ValueError("Image numpy array is empty.")
                pil_img = Image.fromarray(image_input)
            elif isinstance(image_input, Image.Image):
                pil_img = image_input
            else:
                raise TypeError(f"Unsupported image type: {type(image_input)}")

            # Convert to Grayscale
            gray_img = pil_img.convert("L")
            tensor_img = self._transform(gray_img)  # Shape: (1, 32, 32)
            batch_tensor = tensor_img.unsqueeze(0)  # Shape: (1, 1, 32, 32)
            return batch_tensor.to(self.device)

        except Exception as e:
            if isinstance(e, (ValueError, TypeError)):
                raise
            raise ValueError(f"Failed to process character image: {str(e)}") from e

    def predict(self, image_input: Union[bytes, Image.Image, np.ndarray]) -> Dict[str, Any]:
        """
        Predicts alphanumeric character class from image.
        Returns predicted character, confidence, top-3 candidates, and inference latency.
        """
        tensor = self.preprocess_image(image_input)
        model = self._get_model()
        mappings = self._get_mappings()
        classes = mappings["classes"]

        t0 = time.perf_counter()
        with torch.no_grad():
            logits = model(tensor)
            probs = F.softmax(logits, dim=1).squeeze(0)  # Shape: (62,)
        t1 = time.perf_counter()

        latency_ms = round((t1 - t0) * 1000.0, 2)

        # Extract top-3 predictions
        top3_indices = torch.topk(probs, k=min(3, len(classes))).indices.cpu().numpy()

        top3_predictions = []
        for idx in top3_indices:
            cls_name = classes[idx]
            conf = float(probs[idx].item())
            char_glyph = class_name_to_character(cls_name)
            top3_predictions.append({
                "character": char_glyph,
                "class_name": cls_name,
                "confidence": round(conf, 4),
            })

        best = top3_predictions[0]

        return {
            "predicted_character": best["character"],
            "class_name": best["class_name"],
            "confidence": best["confidence"],
            "top3_predictions": top3_predictions,
            "inference_time_ms": latency_ms,
            "device": str(self.device),
            "model_name": "CharacterCNN-62",
            "provenance": "TRAINED MODEL",
            "status": "SUCCESS",
        }

    def get_status_info(self) -> Dict[str, Any]:
        """Returns health status, device profile, and evaluation metadata."""
        eval_metrics = None
        if self.metrics_path.is_file():
            try:
                with open(self.metrics_path, "r", encoding="utf-8") as f:
                    eval_metrics = json.load(f).get("metrics")
            except Exception:
                pass

        mappings = self._get_mappings()

        return {
            "module": "character_recognition",
            "status": "READY" if self.checkpoint_path.is_file() else "CHECKPOINT_NOT_FOUND",
            "model_name": "CharacterCNN-62",
            "model_loaded": self._model is not None,
            "checkpoint_available": self.checkpoint_path.is_file(),
            "checkpoint_path": str(self.checkpoint_path),
            "num_classes": len(mappings["classes"]),
            "device": str(self.device),
            "provenance": "TRAINED MODEL",
            "training_dataset": "Kaggle English Character Recognition (62 classes)",
            "evaluation_metrics": eval_metrics,
        }


# Global singleton instance
character_service = CharacterRecognitionService()

