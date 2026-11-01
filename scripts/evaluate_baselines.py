"""
scripts/evaluate_baselines.py — Benchmark Pretrained Baselines on Acquired Datasets
==================================================================================
1. Faster-Whisper ASR on Mozilla Common Voice test samples -> Computes WER & CER.
2. YOLOv8n-pose on COCO 2017 Keypoint validation samples -> Computes Keypoint Accuracy & Latency.
Outputs empirical benchmarks to models/evaluation/.
"""

from __future__ import annotations

import json
import logging
import re
import time
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

EVAL_DIR = REPO_ROOT / "models" / "evaluation"
EVAL_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Metric Helpers: WER and CER (Levenshtein Distance)
# ---------------------------------------------------------------------------
def levenshtein_distance(ref: list[str] | str, hyp: list[str] | str) -> int:
    d = np.zeros((len(ref) + 1, len(hyp) + 1), dtype=np.uint32)
    for i in range(len(ref) + 1):
        d[i, 0] = i
    for j in range(len(hyp) + 1):
        d[0, j] = j
    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            if ref[i - 1] == hyp[j - 1]:
                d[i, j] = d[i - 1, j - 1]
            else:
                d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + 1)
    return int(d[len(ref), len(hyp)])


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def compute_wer(ref: str, hyp: str) -> float:
    ref_words = normalize_text(ref).split()
    hyp_words = normalize_text(hyp).split()
    if len(ref_words) == 0:
        return 0.0 if len(hyp_words) == 0 else 1.0
    dist = levenshtein_distance(ref_words, hyp_words)
    return min(1.0, dist / len(ref_words))


def compute_cer(ref: str, hyp: str) -> float:
    ref_chars = list(normalize_text(ref))
    hyp_chars = list(normalize_text(hyp))
    if len(ref_chars) == 0:
        return 0.0 if len(hyp_chars) == 0 else 1.0
    dist = levenshtein_distance(ref_chars, hyp_chars)
    return min(1.0, dist / len(ref_chars))


# ---------------------------------------------------------------------------
# 1. Faster-Whisper on Common Voice
# ---------------------------------------------------------------------------
def evaluate_common_voice_speech():
    logger.info("Evaluating Faster-Whisper on Common Voice...")
    cv_dir = REPO_ROOT / "datasets" / "kaggle" / "common_voice"
    samples_dir = cv_dir / "samples"
    test_csv = cv_dir / "cv-valid-test.csv"

    if not test_csv.is_file() or not samples_dir.is_dir():
        logger.warning("Common Voice test assets not found. Skipping.")
        return

    df_test = pd.read_csv(test_csv)
    # Map filename -> ground truth sentence
    ground_truth = {}
    for _, row in df_test.iterrows():
        fname = Path(str(row["filename"])).name
        ground_truth[fname] = str(row["text"])

    audio_files = sorted(list(samples_dir.glob("*.mp3")))[:15]  # Evaluate on first 15 test files
    if len(audio_files) == 0:
        logger.warning("No audio files in %s", samples_dir)
        return

    from backend.app.services.speech import speech_service

    wers = []
    cers = []
    latencies = []
    results = []

    for af in audio_files:
        ref_text = ground_truth.get(af.name, "")
        if not ref_text:
            continue

        try:
            with open(af, "rb") as f:
                audio_bytes = f.read()

            t0 = time.perf_counter()
            asr_res = speech_service.transcribe(audio_bytes, filename_hint=af.name)
            latency = time.perf_counter() - t0

            hyp_text = asr_res.get("full_text", asr_res.get("full_transcript", ""))
            wer = compute_wer(ref_text, hyp_text)
            cer = compute_cer(ref_text, hyp_text)

            wers.append(wer)
            cers.append(cer)
            latencies.append(latency)

            results.append({
                "audio_file": af.name,
                "reference": ref_text,
                "hypothesis": hyp_text,
                "wer": round(wer, 4),
                "cer": round(cer, 4),
                "latency_seconds": round(latency, 2),
            })
            logger.info("Sample: %s | WER: %.2f%% | CER: %.2f%%", af.name, wer * 100.0, cer * 100.0)
        except Exception as e:
            logger.warning("Failed to transcribe %s: %s", af.name, e)

    if len(wers) > 0:
        avg_wer = float(np.mean(wers))
        avg_cer = float(np.mean(cers))
        avg_latency = float(np.mean(latencies))

        payload = {
            "dataset": "Mozilla Common Voice (English Test Split)",
            "model": "Faster-Whisper (base / small)",
            "total_evaluated_samples": len(wers),
            "word_error_rate_mean": round(avg_wer, 4),
            "character_error_rate_mean": round(avg_cer, 4),
            "accuracy_word_level": round(1.0 - avg_wer, 4),
            "avg_inference_latency_seconds": round(avg_latency, 3),
            "provenance": "KAGGLE / MOZILLA",
            "speaker_profiling": "EXCLUDED — No acoustic speaker biometric identification permitted",
            "samples": results[:5],
        }
        out_path = EVAL_DIR / "speech_evaluation_results.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        logger.info("Saved Common Voice ASR evaluation: Mean WER = %.2f%% | Mean CER = %.2f%%", avg_wer * 100, avg_cer * 100)


# ---------------------------------------------------------------------------
# 2. YOLOv8n-pose on COCO Keypoints
# ---------------------------------------------------------------------------
def evaluate_coco_pose():
    logger.info("Evaluating YOLOv8n-pose baseline on official COCO Keypoints...")
    coco_dir = REPO_ROOT / "datasets" / "kaggle" / "coco_keypoints"
    val_images_dir = coco_dir / "val2017"
    annot_path = coco_dir / "annotations" / "person_keypoints_val2017.json"

    if not annot_path.is_file() or not val_images_dir.is_dir():
        logger.warning("COCO Keypoints assets not found. Skipping.")
        return

    with open(annot_path, "r", encoding="utf-8") as f:
        coco_data = json.load(f)

    # Build image_id -> list of person annotations
    img_id_to_anns = {}
    for ann in coco_data.get("annotations", []):
        if ann.get("num_keypoints", 0) > 0:
            iid = ann["image_id"]
            img_id_to_anns.setdefault(iid, []).append(ann)

    # Build filename -> image_id
    fname_to_iid = {img["file_name"]: img["id"] for img in coco_data.get("images", [])}

    test_imgs = sorted(list(val_images_dir.glob("*.jpg")))[:20]  # Evaluate on first 20 COCO validation crops
    if len(test_imgs) == 0:
        logger.warning("No images in %s", val_images_dir)
        return

    from backend.app.services.computer_vision import cv_service

    detected_persons = 0
    gt_persons = 0
    keypoint_confidences = []
    latencies = []

    for img_path in test_imgs:
        iid = fname_to_iid.get(img_path.name)
        if iid is None:
            continue

        gt_anns = img_id_to_anns.get(iid, [])
        gt_persons += len(gt_anns)

        try:
            with open(img_path, "rb") as f:
                img_bytes = f.read()

            t0 = time.perf_counter()
            summary = cv_service.detect_with_pose(img_bytes)
            latency_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(latency_ms)

            detected_persons += summary.totalPersons

            # Extract pose keypoints from detections
            for box in summary.boxes:
                if box.keypoints:
                    for kp in box.keypoints:
                        keypoint_confidences.append(kp.confidence)

        except Exception as e:
            logger.warning("Pose inference failed on %s: %s", img_path.name, e)

    detection_recall = round(min(1.0, detected_persons / max(1, gt_persons)), 4)
    avg_kp_conf = round(float(np.mean(keypoint_confidences)) if keypoint_confidences else 0.0, 4)
    avg_latency = round(float(np.mean(latencies)) if latencies else 0.0, 2)

    payload = {
        "dataset": "COCO 2017 Keypoints (Validation Split)",
        "model": "YOLOv8n-pose (official checkpoint)",
        "total_evaluated_images": len(test_imgs),
        "ground_truth_persons": gt_persons,
        "detected_persons": detected_persons,
        "person_detection_recall": detection_recall,
        "mean_keypoint_confidence": avg_kp_conf,
        "total_extracted_keypoints": len(keypoint_confidences),
        "avg_inference_latency_ms": avg_latency,
        "device": str(cv_service.get_device()),
        "boundary_isolation": "Evaluates general COCO human keypoints; not representative of classroom hand-raising ground truth",
    }
    out_path = EVAL_DIR / "pose_evaluation_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    logger.info("Saved COCO Keypoints baseline evaluation: Recall = %.2f%% | Avg KP Conf = %.4f | Latency = %.2f ms",
                detection_recall * 100, avg_kp_conf, avg_latency)


if __name__ == "__main__":
    evaluate_common_voice_speech()
    evaluate_coco_pose()
    print("Baseline evaluations successfully completed!")
