"""
scripts/generate_coco_metadata.py — Generate dataset_info and manifests for COCO Keypoints
========================================================================================
Creates:
- datasets/kaggle/human_pose/coco_keypoints/dataset_info.json
- datasets/splits/coco_keypoints_split.json
- datasets/splits/coco_keypoints_manifest.json
"""

import json
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
COCO_DIR = REPO_ROOT / "datasets" / "kaggle" / "human_pose" / "coco_keypoints"
SPLITS_DIR = REPO_ROOT / "datasets" / "splits"
SPLITS_DIR.mkdir(parents=True, exist_ok=True)

dataset_info = {
    "dataset_name": "COCO 2017 Keypoints (Human Pose)",
    "task": "2D Human Pose Estimation (17 Keypoints)",
    "provenance": "KAGGLE / COCO CONSORTIUM",
    "source_url": "https://cocodataset.org/",
    "license": "CC BY 4.0",
    "created_at": datetime.now().isoformat(),
    "archive_source": r"C:\Users\prash\Downloads\COCO_Keypoints.zip",
    "local_path": "datasets/kaggle/human_pose/coco_keypoints",
    "keypoints": [
        "nose", "left_eye", "right_eye", "left_ear", "right_ear",
        "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
        "left_wrist", "right_wrist", "left_hip", "right_hip",
        "left_knee", "right_knee", "left_ankle", "right_ankle"
    ],
    "skeleton": [
        [16, 14], [14, 12], [17, 15], [15, 13], [12, 13],
        [6, 12], [7, 13], [6, 7], [6, 8], [7, 9],
        [8, 10], [9, 11], [2, 3], [1, 2], [1, 3],
        [2, 4], [3, 5], [4, 6], [5, 7]
    ],
    "counts": {
        "train": {
            "images_in_archive_and_disk": 56599,
            "images_in_json": 118287,
            "images_with_person_annots": 64115,
            "images_with_keypoints": 56599,
            "total_annotations": 262465,
            "annotations_with_keypoints": 149813,
            "crowd_annotations": 5212,
            "invalid_bboxes": 1,
            "visibility_distribution": {
                "v0_not_labeled": 2819622,
                "v0_percent": 63.19,
                "v1_occluded": 185442,
                "v1_percent": 4.16,
                "v2_visible": 1456841,
                "v2_percent": 32.65
            }
        },
        "val": {
            "images_in_archive_and_disk": 2346,
            "images_in_json": 5000,
            "images_with_keypoints": 2346,
            "total_annotations": 11004,
            "annotations_with_keypoints": 6352,
            "crowd_annotations": 227,
            "invalid_bboxes": 0,
            "visibility_distribution": {
                "v0_not_labeled": 118853,
                "v0_percent": 63.53,
                "v1_occluded": 8365,
                "v1_percent": 4.47,
                "v2_visible": 59850,
                "v2_percent": 31.99
            }
        },
        "total_images_on_disk": 58945,
        "total_annotations": 273469
    },
    "integrity": {
        "corrupted_images": 0,
        "annotation_json_valid": True,
        "keypoint_count_per_ann": 17,
        "keypoint_channels": 3
    },
    "ethical_and_operational_boundary": {
        "classroom_hand_raising": "COCO keypoints represent general body posture; they do NOT represent classroom hand-raising semantic ground truth.",
        "biometrics": "No facial recognition, emotion analysis, or identity persistence is derived from COCO keypoints.",
        "tracking": "Keypoints feed into anonymous session-scoped Euclidean/IOU person tracking only."
    }
}

with open(COCO_DIR / "dataset_info.json", "w", encoding="utf-8") as f:
    json.dump(dataset_info, f, indent=2)
print("Saved dataset_info.json")

# Update datasets/splits/coco_keypoints_split.json
split_info = {
    "dataset": "COCO 2017 Keypoints (Human Pose)",
    "official_split_preserved": True,
    "random_seed": 42,
    "strategy": "Official COCO 2017 Benchmark Partition (Train2017 / Val2017)",
    "counts": {
        "train_images": 56599,
        "val_images": 2346,
        "train_annotations": 262465,
        "val_annotations": 11004,
        "total_images_on_disk": 58945
    },
    "split_manifest": {
        "train": "datasets/kaggle/human_pose/coco_keypoints/train2017",
        "val": "datasets/kaggle/human_pose/coco_keypoints/val2017",
        "train_annotations": "datasets/kaggle/human_pose/coco_keypoints/annotations/person_keypoints_train2017.json",
        "val_annotations": "datasets/kaggle/human_pose/coco_keypoints/annotations/person_keypoints_val2017.json"
    },
    "license": "CC BY 4.0",
    "updated_at": datetime.now().isoformat()
}

with open(SPLITS_DIR / "coco_keypoints_split.json", "w", encoding="utf-8") as f:
    json.dump(split_info, f, indent=2)
print("Saved coco_keypoints_split.json")

# Also write coco_keypoints_manifest.json with sample filenames
manifest_info = {
    "dataset": "coco_keypoints",
    "total_val_images": 2346,
    "total_train_images": 56599,
    "val_sample_files": [f.name for f in list((COCO_DIR / "val2017").glob("*.jpg"))[:50]],
    "train_sample_files": [f.name for f in list((COCO_DIR / "train2017").glob("*.jpg"))[:50]],
    "source_archive": r"C:\Users\prash\Downloads\COCO_Keypoints.zip",
    "updated_at": datetime.now().isoformat()
}

with open(SPLITS_DIR / "coco_keypoints_manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest_info, f, indent=2)
print("Saved coco_keypoints_manifest.json")

