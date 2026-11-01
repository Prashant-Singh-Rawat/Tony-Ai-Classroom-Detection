"""
backend/app/services/summary_scoring.py — CommonLit Student Summary Scoring Service
===================================================================================
Predicts content and wording quality continuous scores for student summaries.
Strict boundary: Rubric assessment only; never measures student intelligence.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib
import numpy as np

from backend.app.core.config import REPO_ROOT

logger = logging.getLogger(__name__)


def extract_text_stats(texts: list[str]) -> np.ndarray:
    features = []
    for t in texts:
        words = t.split()
        n_words = len(words)
        n_chars = len(t)
        n_sentences = max(1, t.count(".") + t.count("!") + t.count("?"))
        avg_word_len = n_chars / max(1, n_words)
        avg_sent_len = n_words / n_sentences
        features.append([n_words, n_chars, n_sentences, avg_word_len, avg_sent_len])
    return np.array(features, dtype=np.float32)


class SummaryScoringService:
    def __init__(self):
        self.checkpoint_dir = REPO_ROOT / "models" / "checkpoints" / "summary_scoring"
        self.model_path = self.checkpoint_dir / "summary_regressor.joblib"
        self.metrics_path = self.checkpoint_dir / "evaluation_results.json"
        self._bundle: Optional[dict] = None

    def _get_bundle(self) -> dict:
        if self._bundle is None:
            if not self.model_path.is_file():
                raise FileNotFoundError(f"Summary scoring model not found at {self.model_path}")
            self._bundle = joblib.load(self.model_path)
        return self._bundle

    def predict(self, summary_text: str) -> Dict[str, Any]:
        text = summary_text.strip()
        if not text:
            raise ValueError("Summary text is empty.")

        bundle = self._get_bundle()
        tfidf = bundle["tfidf"]
        scaler = bundle["scaler"]
        regressor = bundle["regressor"]

        from scipy.sparse import hstack
        t0 = time.perf_counter()
        X_text = tfidf.transform([text])
        X_stats = scaler.transform(extract_text_stats([text]))
        X_feat = hstack([X_text, X_stats]).tocsr()

        preds = regressor.predict(X_feat)[0]
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 3)

        content_score = round(float(preds[0]), 4)
        wording_score = round(float(preds[1]), 4)
        overall_quality = round((content_score + wording_score) / 2.0, 4)

        return {
            "contentScore": content_score,
            "wordingScore": wording_score,
            "overallQualityScore": overall_quality,
            "inferenceTimeMs": latency_ms,
            "modelName": "MultiOutputRidge-TFIDF",
            "provenance": "TRAINED MODEL",
            "status": "SUCCESS",
            "ethicalBoundary": "Scores reflect educational writing rubric only; NEVER student intelligence or cognitive ability",
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
            "module": "student_summary_scoring",
            "status": "READY" if self.model_path.is_file() else "MODEL_NOT_FOUND",
            "modelPath": str(self.model_path),
            "targetMetrics": ["content", "wording"],
            "provenance": "TRAINED MODEL",
            "trainingDataset": "CommonLit Student Summaries (7,165 samples)",
            "evaluationMetrics": metrics,
            "ethicalBoundary": "Educational writing rubric assessment only; never measures student intelligence",
        }


summary_scoring_service = SummaryScoringService()

