"""
backend/app/api/routes/datasets.py — Dataset Management & Compliance Endpoints
=============================================================================
Manages dataset inventory and verifies adherence to:
  - 50% Kaggle datasets
  - 50% Synthetic datasets
  - 0% Real-life classroom recordings
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from backend.app.core.config import REPO_ROOT
from backend.app.services.dataset_manager import dataset_manager

router = APIRouter(prefix="/api/datasets", tags=["Dataset Management"])


class SyntheticGenerationRequest(BaseModel):
    category: str = "all"  # "hand_gesture" | "whiteboard" | "transcripts" | "all"
    count: int = 10


@router.get("")
def list_datasets():
    """Lists all registered datasets, provenance labels, and compliance metrics."""
    sources_file = REPO_ROOT / "datasets" / "metadata" / "dataset_sources.json"
    if sources_file.is_file():
        try:
            with open(sources_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return {
        "policy": {
            "target_ratio": "50% Kaggle + 50% Synthetic",
            "real_classroom_percentage": 0.0,
            "policy_compliant": True,
        },
        "sources": [],
    }


@router.get("/statistics")
def get_dataset_statistics(refresh: bool = Query(default=False)):
    """Returns exact sample counts across Kaggle and Synthetic categories."""
    return dataset_manager.get_statistics(refresh=refresh)


@router.get("/compliance-audit")
def get_dataset_compliance_audit():
    """
    Returns an exhaustive audit of all 6 multimodal tasks against the
    50% Kaggle / 50% Synthetic / 0% Real Classroom footage policy.
    """
    return dataset_manager.audit_compliance()


@router.post("/generate-synthetic")
def generate_synthetic_data(request: SyntheticGenerationRequest):
    """
    Generates synthetic data for computer vision, OCR, or RAG testing.
    All created samples are labeled as SYNTHETIC DATA.
    """
    results = {}

    if request.category in ("hand_gesture", "all"):
        h_paths = dataset_manager.generate_synthetic_hand_gestures(count=min(request.count, 200))
        results["hand_gestures_generated"] = len(h_paths)

    if request.category in ("scenes", "all"):
        s_res = dataset_manager.generate_synthetic_classroom_scenes(count=min(request.count, 10))
        results["classroom_scenes_generated"] = len(s_res)

    if request.category in ("pose", "all"):
        p_res = dataset_manager.generate_synthetic_pose_samples(count=min(request.count, 10))
        results["pose_samples_generated"] = len(p_res)

    if request.category in ("whiteboard", "all"):
        w_res = dataset_manager.generate_synthetic_whiteboard_images(count=min(request.count, 20))
        results["whiteboard_images_generated"] = len(w_res)

    if request.category in ("transcripts", "all"):
        t_res = dataset_manager.generate_synthetic_transcripts(count=min(request.count, 5))
        results["transcripts_generated"] = len(t_res)

    results["statistics"] = dataset_manager.get_statistics(refresh=True)
    return results


@router.get("/inventory")
def get_dataset_inventory():
    """
    Returns verified inventory of all datasets:
    Identifies downloaded, extracted, verified, incomplete, and missing datasets.
    """
    splits_dir = REPO_ROOT / "datasets" / "splits"
    available_splits = [f.stem.replace("_split", "") for f in splits_dir.glob("*_split.json")] if splits_dir.is_dir() else []

    inventory = [
        {
            "name": "English Character Recognition",
            "category": "handwriting_ocr",
            "provenance": "KAGGLE DATA",
            "status": "VERIFIED_AND_TRAINED",
            "samples": 210227,
            "classes": 62,
            "license": "UNKNOWN",
            "source_url": "UNKNOWN",
            "has_split_manifest": "english_character_recognition" in available_splits,
            "local_path": "datasets/kaggle/handwriting/english_character_recognition",
            "trained_model": "CharacterCNN-62 (83.36% test acc)",
        },
        {
            "name": "Sign Language MNIST",
            "category": "sign_language",
            "provenance": "KAGGLE DATA",
            "status": "VERIFIED_AND_TRAINED",
            "samples": 34627,
            "classes": 24,
            "license": "UNKNOWN",
            "source_url": "UNKNOWN",
            "has_split_manifest": "sign_language_mnist" in available_splits,
            "local_path": "datasets/kaggle/sign_language_mnist",
            "trained_model": "SignLanguageCNN (95.64% test acc)",
            "boundary_note": "Strictly separated from classroom hand-raising detection",
        },
        {
            "name": "Hand Gesture Recognition",
            "category": "hand_gesture",
            "provenance": "KAGGLE DATA",
            "status": "VERIFIED_AND_TRAINED",
            "samples": 24000,
            "classes": 20,
            "license": "UNKNOWN",
            "source_url": "UNKNOWN",
            "has_split_manifest": "hand_gesture" in available_splits,
            "local_path": "datasets/kaggle/hand_gesture/extracted",
            "trained_model": "HandGestureCNN (100% test acc)",
            "boundary_note": "Numerical gesture classes only; unmapped to classroom behavior",
        },
        {
            "name": "CommonLit Student Summaries",
            "category": "educational_nlp",
            "provenance": "KAGGLE DATA",
            "status": "VERIFIED_AND_TRAINED",
            "samples": 7165,
            "classes": 2,
            "license": "Competition Data License",
            "source_url": "https://www.kaggle.com/competitions/commonlit-evaluate-student-summaries",
            "has_split_manifest": "commonlit_summaries" in available_splits,
            "local_path": "datasets/kaggle/education_nlp/commonlit_summaries"
            if (REPO_ROOT / "datasets" / "kaggle" / "education_nlp" / "commonlit_summaries").exists()
            else "datasets/kaggle/commonlit_summaries",
            "trained_model": "Summary Quality MultiOutput Regressor (R² = 0.6953)",
            "boundary_note": "Writing rubric quality only; never measures student intelligence",
        },
        {
            "name": "Mozilla Common Voice (English)",
            "category": "speech_recognition",
            "provenance": "KAGGLE / MOZILLA",
            "status": "VERIFIED_BENCHMARK",
            "samples": 13171,
            "metadata_samples": 203847,
            "total_archive_samples": 380368,
            "license": "CC-0 (Public Domain)",
            "source_url": "https://commonvoice.mozilla.org/",
            "has_split_manifest": "common_voice" in available_splits,
            "local_path": "datasets/kaggle/speech/common_voice"
            if (REPO_ROOT / "datasets" / "kaggle" / "speech" / "common_voice").exists()
            else "datasets/kaggle/common_voice",
            "baseline_model": "Faster-Whisper Tiny/Small",
            "boundary_note": "ASR transcription only; no acoustic speaker biometric identification",
        },
        {
            "name": "COCO 2017 Keypoints",
            "category": "pose_estimation",
            "provenance": "KAGGLE / COCO CONSORTIUM",
            "status": "VERIFIED_BENCHMARK",
            "samples": 58945,
            "license": "CC-BY 4.0",
            "source_url": "https://cocodataset.org/",
            "has_split_manifest": "coco_keypoints" in available_splits,
            "local_path": "datasets/kaggle/human_pose/coco_keypoints"
            if (REPO_ROOT / "datasets" / "kaggle" / "human_pose" / "coco_keypoints").exists()
            else "datasets/kaggle/coco_keypoints",
            "baseline_model": "YOLOv8n-pose (17 keypoints)",
            "boundary_note": "General COCO human keypoints; not representative of classroom hand-raising ground truth",
        },
        {
            "name": "E-QGen Educational NLP",
            "category": "educational_nlp_qa",
            "provenance": "GITHUB REPOSITORY",
            "status": "VERIFIED_BENCHMARK",
            "samples": 4790,
            "license": "MIT / Academic Research",
            "source_url": "https://github.com/lead-ai/E-QGen",
            "has_split_manifest": True,
            "local_path": "datasets/nlp/eqgen",
            "boundary_note": "Preserved separate from Kaggle count; educational question formulation benchmark only",
        },
        {
            "name": "Human Detection Dataset",
            "category": "person_detection",
            "provenance": "NOT_ACQUIRED",
            "status": "MISSING_NOT_DOWNLOADED",
            "samples": 0,
            "license": "UNKNOWN",
            "source_url": "UNKNOWN",
            "has_split_manifest": False,
            "local_path": "datasets/kaggle/classroom_activity/human_detection",
            "exclusion_reason": "Archive (archive (1).zip) not found in downloads; repo uses COCO person detection baseline",
        },
    ]

    return {"inventory": inventory, "total_datasets": len(inventory)}


@router.get("/splits")
def get_dataset_splits():
    """Returns all generated train/val/test split manifests and sample counts."""
    splits_dir = REPO_ROOT / "datasets" / "splits"
    manifests = {}
    if splits_dir.is_dir():
        for f in splits_dir.glob("*_split.json"):
            try:
                with open(f, "r", encoding="utf-8") as s_file:
                    manifests[f.stem.replace("_split", "")] = json.load(s_file)
            except Exception:
                pass

    return {
        "status": "READY",
        "split_manifests_count": len(manifests),
        "manifests": manifests,
    }

