#!/usr/bin/env python3
"""
scripts/evaluate_common_voice_wer.py
====================================
Evaluates Faster-Whisper on Mozilla Common Voice (English Test Split)
using strictly verified, correctly matched audio-transcript pairs.
Computes Word Error Rate (WER), Character Error Rate (CER), and inference latency.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.speech.service import speech_service


def normalize_text(text: str) -> str:
    """Normalizes text for standardized WER/CER calculation."""
    text = text.lower()
    text = re.sub(r"['\",.\?!:;\-\(\)\[\]]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compute_levenshtein(seq1: List[str], seq2: List[str]) -> int:
    """Computes Levenshtein edit distance between two token sequences."""
    n1, n2 = len(seq1), len(seq2)
    dp = [[0] * (n2 + 1) for _ in range(n1 + 1)]
    for i in range(n1 + 1):
        dp[i][0] = i
    for j in range(n2 + 1):
        dp[0][j] = j

    for i in range(1, n1 + 1):
        for j in range(1, n2 + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(
                    dp[i - 1][j] + 1,      # deletion
                    dp[i][j - 1] + 1,      # insertion
                    dp[i - 1][j - 1] + 1,  # substitution
                )
    return dp[n1][n2]


def calculate_wer_and_cer(reference: str, hypothesis: str) -> Tuple[float, float]:
    """Calculates Word Error Rate (WER) and Character Error Rate (CER)."""
    norm_ref = normalize_text(reference)
    norm_hyp = normalize_text(hypothesis)

    ref_words = norm_ref.split()
    hyp_words = norm_hyp.split()

    if not ref_words:
        wer = 0.0 if not hyp_words else 1.0
    else:
        dist_words = compute_levenshtein(ref_words, hyp_words)
        wer = min(1.0, dist_words / len(ref_words))

    ref_chars = list(norm_ref.replace(" ", ""))
    hyp_chars = list(norm_hyp.replace(" ", ""))

    if not ref_chars:
        cer = 0.0 if not hyp_chars else 1.0
    else:
        dist_chars = compute_levenshtein(ref_chars, hyp_chars)
        cer = min(1.0, dist_chars / len(ref_chars))

    return wer, cer


def run_evaluation(num_samples: int = 25) -> Dict[str, Any]:
    csv_path = REPO_ROOT / "datasets" / "kaggle" / "speech" / "common_voice" / "cv-valid-test.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(f"Missing Common Voice metadata: {csv_path}")

    df = pd.read_csv(csv_path)
    base_dir = REPO_ROOT / "datasets" / "kaggle" / "speech" / "common_voice"

    print(f"[EVALUATION] Starting Common Voice WER benchmark on {num_samples} matched samples...")
    sample_records = []
    wers = []
    cers = []
    latencies = []

    tested_count = 0
    for idx, row in df.iterrows():
        if tested_count >= num_samples:
            break

        audio_rel = str(row["filename"]).replace("\\", "/")
        audio_abs = base_dir / audio_rel
        if not audio_abs.is_file():
            continue

        reference_text = str(row["text"])
        t0 = time.perf_counter()
        res = speech_service.transcribe(str(audio_abs))
        t1 = time.perf_counter()

        latency = round(t1 - t0, 3)
        hypothesis_text = res.get("full_text", "")

        wer, cer = calculate_wer_and_cer(reference_text, hypothesis_text)
        wers.append(wer)
        cers.append(cer)
        latencies.append(latency)

        sample_records.append({
            "audio_file": os.path.basename(audio_rel),
            "reference": reference_text,
            "hypothesis": hypothesis_text,
            "detected_language": res.get("language"),
            "language_confidence": res.get("language_probability"),
            "duration_seconds": res.get("duration"),
            "wer": round(wer, 4),
            "cer": round(cer, 4),
            "latency_seconds": latency,
        })
        tested_count += 1
        print(f"  [{tested_count:02d}/{num_samples}] {os.path.basename(audio_rel)} | WER: {wer:.4f} | Latency: {latency:.2f}s")

    mean_wer = round(sum(wers) / len(wers), 4) if wers else 0.0
    mean_cer = round(sum(cers) / len(cers), 4) if cers else 0.0
    mean_latency = round(sum(latencies) / len(latencies), 3) if latencies else 0.0
    word_accuracy = round(1.0 - mean_wer, 4)

    results = {
        "dataset": "Mozilla Common Voice (English Test Split)",
        "model": "Faster-Whisper (tiny, CPU int8)",
        "total_evaluated_samples": len(sample_records),
        "word_error_rate_mean": mean_wer,
        "character_error_rate_mean": mean_cer,
        "accuracy_word_level": word_accuracy,
        "avg_inference_latency_seconds": mean_latency,
        "provenance": "KAGGLE / MOZILLA",
        "speaker_profiling": "EXCLUDED — No acoustic speaker biometric identification permitted",
        "evaluation_mode": "STRICTLY_MATCHED_PAIRS",
        "samples": sample_records,
    }

    out_path = REPO_ROOT / "models" / "evaluation" / "speech_evaluation_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n[DONE] Evaluation written to {out_path}")
    print(f"  Evaluated Samples: {len(sample_records)}")
    print(f"  Mean WER: {mean_wer:.4f} (Accuracy: {word_accuracy*100:.2f}%)")
    print(f"  Mean CER: {mean_cer:.4f}")
    print(f"  Avg Latency: {mean_latency:.3f} s")
    return results


if __name__ == "__main__":
    run_evaluation(num_samples=25)

