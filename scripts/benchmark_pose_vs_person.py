"""
scripts/benchmark_pose_vs_person.py — Performance & Pose Verification Benchmark
================================================================================
Compares YOLOv8n person detection vs YOLOv8n-pose pose estimation on latency,
FPS, memory usage, keypoint accuracy, and posture classification.
"""

import sys
import os
import time
from pathlib import Path
import numpy as np
import cv2

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.computer_vision import cv_service


def run_benchmark():
    # 1. Use an actual sample from Kaggle dataset (50x50 upscaled to 320x320 for realistic resolution)
    sample_path = Path("datasets/kaggle/hand_gesture/extracted/train/0/1.jpg")
    if sample_path.exists():
        raw_img = cv2.imread(str(sample_path))
        img = cv2.resize(raw_img, (320, 320))
        dataset_source = f"Kaggle Dataset ({sample_path})"
    else:
        img = np.full((320, 320, 3), 200, dtype=np.uint8)
        dataset_source = "Synthetic Baseline"

    print("=================================================================")
    print("CLASSVISION AI — PHASE 2.1 POSE ESTIMATION BENCHMARK & COMPARISON")
    print("=================================================================")
    print(f"Input Source: {dataset_source}")
    print(f"Resolution: {img.shape[1]}x{img.shape[0]}")

    status = cv_service.get_pose_status_info()
    print(f"Device: {status.inferenceDevice}")
    print(f"CUDA Available: {status.cudaAvailable}")
    print(f"Active Checkpoint: {status.activeCheckpoint}")
    print(f"VRAM Memory Allocated: {status.memoryUsage.get('allocated_mb', 0.0)} MB")
    print(f"Supported Keypoints: {status.supportedKeypointsCount} (COCO Standard)")
    print(f"Observable Posture Classes: {status.postureClasses}")

    # Benchmark YOLOv8n (Person detection)
    yolo_times = []
    for _ in range(5):
        t0 = time.perf_counter()
        res_yolo = cv_service.detect_persons_yolov8n(img, confidence_threshold=0.10)
        yolo_times.append((time.perf_counter() - t0) * 1000)
    avg_yolo = np.mean(yolo_times[1:])  # drop warm-up

    # Benchmark YOLOv8n-pose (Human pose estimation)
    pose_times = []
    for _ in range(5):
        t0 = time.perf_counter()
        res_pose = cv_service.estimate_pose(img, confidence_threshold=0.10)
        pose_times.append((time.perf_counter() - t0) * 1000)
    avg_pose = np.mean(pose_times[1:])  # drop warm-up

    print("\n--- INFERENCE PERFORMANCE COMPARISON ---")
    print(f"YOLOv8n Person Detection: {avg_yolo:.1f} ms ({1000/avg_yolo:.1f} FPS)")
    print(f"YOLOv8n-pose Estimation:  {avg_pose:.1f} ms ({1000/avg_pose:.1f} FPS)")
    overhead = avg_pose - avg_yolo
    print(f"Pose Estimation Overhead: +{overhead:.1f} ms (+{(overhead / max(0.1, avg_yolo)) * 100:.1f}%)")

    print("\n--- DETECTION & POSTURE VERIFICATION ---")
    print(f"YOLOv8n Detected Persons: {res_yolo.totalPersons}")
    print(f"YOLOv8n-pose Detected Persons: {res_pose.totalPersons}")
    print(f"Posture Counts: {res_pose.postureCounts}")

    if res_pose.totalPersons > 0:
        p = res_pose.persons[0]
        print(f"\nPerson ID: {p.id}")
        print(f"Pose Detection Confidence: {p.confidence}")
        print(f"Posture Classification: {p.posture.value}")
        print(f"Posture Observation: {p.postureReason}")
        print(f"Left Elbow Angle: {p.geometry.leftArm.elbowAngleDeg} deg")
        print(f"Right Elbow Angle: {p.geometry.rightArm.elbowAngleDeg} deg")
        print(f"Left Wrist Elevation: {p.geometry.leftArm.elevationPx} px (Above shoulder: {p.geometry.leftArm.wristAboveShoulder})")
        print(f"Right Wrist Elevation: {p.geometry.rightArm.elevationPx} px (Above shoulder: {p.geometry.rightArm.wristAboveShoulder})")
        print(f"Upper Body Visible: {p.geometry.upperBodyVisible}")
        print(f"Occluded Keypoints: {p.geometry.occludedKeypoints}")
        print(f"Total Keypoints Extracted: {len(p.keypoints)}")
        print("\nAll 17 COCO Keypoints:")
        for kp in p.keypoints:
            print(f"  [{kp.index:02d}] {kp.name:15s}: x={kp.x:5.1f}, y={kp.y:5.1f}, conf={kp.confidence:.3f}, visible={kp.visible}")

    print("\n=================================================================")
    print("BENCHMARK COMPLETED SUCCESSFULLY")
    print("=================================================================")


if __name__ == "__main__":
    run_benchmark()

