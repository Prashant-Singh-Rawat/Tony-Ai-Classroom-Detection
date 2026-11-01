#!/usr/bin/env python3
"""
scripts/benchmark_inference_performance.py — Comprehensive Inference Benchmark (Phase 2.6)
==========================================================================================
Benchmarks YOLOv8n, YOLOv8n-pose, and Combined Sequential Inference across:
- Cold start load latency
- Warm latency (Mean, Median, P95 across 25 iterations)
- Throughput (Processing FPS)
- Multi-resolution analysis (320x320 vs 640x640)
- Frame skipping factors (skip=1, skip=5, skip=10)
- System resources (Process RAM, CPU %, GPU VRAM)
Outputs structured results to docs/inference_benchmark_results.json and prints markdown summary.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

import cv2
import numpy as np
import psutil
import torch

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.computer_vision import cv_service


def get_process_memory_mb() -> float:
    process = psutil.Process(os.getpid())
    return round(process.memory_info().rss / (1024 * 1024), 2)


def run_benchmark() -> Dict[str, Any]:
    print("=" * 70)
    print("CLASSVISION AI — PHASE 2.6 MULTIMODAL INFERENCE BENCHMARK")
    print("=" * 70)

    # 1. Environment & Hardware Detection
    device_name = cv_service.get_device()
    cuda_available = torch.cuda.is_available()
    cuda_device = torch.cuda.get_device_name(0) if cuda_available else "N/A (CPU Fallback Active)"
    py_version = sys.version.split()[0]
    torch_version = torch.__version__

    print(f"Python: {py_version} | PyTorch: {torch_version}")
    print(f"Device: {device_name.upper()} | CUDA: {cuda_available} | GPU: {cuda_device}")
    print(f"Initial Memory: {get_process_memory_mb()} MB")

    # 2. Prepare Sample Inputs (from Kaggle dataset or synthetic)
    sample_path = REPO_ROOT / "datasets" / "kaggle" / "hand_gesture" / "extracted" / "train" / "0" / "1.jpg"
    if sample_path.exists():
        raw_bgr = cv2.imread(str(sample_path))
        data_source = "Kaggle Dataset Sample (train/0/1.jpg)"
    else:
        raw_bgr = np.full((320, 320, 3), 200, dtype=np.uint8)
        data_source = "Synthetic Baseline Image"

    img_320 = cv2.resize(raw_bgr, (320, 320))
    img_640 = cv2.resize(raw_bgr, (640, 640))

    benchmark_data: Dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "hardware": {
            "device": device_name,
            "cuda_available": cuda_available,
            "gpu_name": cuda_device,
            "torch_version": torch_version,
            "input_source": data_source,
        },
        "cold_start": {},
        "warm_benchmarks": {},
        "frame_skipping": {},
    }

    # 3. Cold Start Measurement
    print("\n--- MEASURING COLD START LATENCY ---")
    # Fresh YOLOv8n load
    t0 = time.perf_counter()
    res_cold_yolo = cv_service.detect_persons_yolov8n(img_640, confidence_threshold=0.25)
    cold_yolo_ms = round((time.perf_counter() - t0) * 1000, 2)
    benchmark_data["cold_start"]["yolov8n_ms"] = cold_yolo_ms
    print(f"YOLOv8n Person Cold Start: {cold_yolo_ms} ms")

    # Fresh YOLOv8n-pose load
    t0 = time.perf_counter()
    res_cold_pose = cv_service.estimate_pose(img_640, confidence_threshold=0.25)
    cold_pose_ms = round((time.perf_counter() - t0) * 1000, 2)
    benchmark_data["cold_start"]["yolov8n_pose_ms"] = cold_pose_ms
    print(f"YOLOv8n-pose Cold Start:   {cold_pose_ms} ms")

    # 4. Warm Latency Benchmarks across Configurations (25 iterations each)
    configurations = [
        ("yolov8n_320", "YOLOv8n Person Detection", img_320, 320, "yolo"),
        ("yolov8n_640", "YOLOv8n Person Detection", img_640, 640, "yolo"),
        ("yolov8n_pose_320", "YOLOv8n-pose Estimation", img_320, 320, "pose"),
        ("yolov8n_pose_640", "YOLOv8n-pose Estimation", img_640, 640, "pose"),
        ("combined_sequential_320", "Combined Sequential (YOLO + Pose)", img_320, 320, "combined"),
        ("combined_sequential_640", "Combined Sequential (YOLO + Pose)", img_640, 640, "combined"),
    ]

    print("\n--- EXECUTING WARM INFERENCE BENCHMARKS (25 iterations each) ---")
    for key, label, img, res, mode in configurations:
        latencies = []
        cpu_readings = []

        # Warmup 3 iterations
        for _ in range(3):
            if mode == "yolo":
                cv_service.detect_persons_yolov8n(img, confidence_threshold=0.25)
            elif mode == "pose":
                cv_service.estimate_pose(img, confidence_threshold=0.25)
            elif mode == "combined":
                cv_service.detect_persons_yolov8n(img, confidence_threshold=0.25)
                cv_service.estimate_pose(img, confidence_threshold=0.25)

        # 25 measured iterations
        for _ in range(25):
            cpu_before = psutil.cpu_percent(interval=None)
            t_start = time.perf_counter()

            if mode == "yolo":
                cv_service.detect_persons_yolov8n(img, confidence_threshold=0.25)
            elif mode == "pose":
                cv_service.estimate_pose(img, confidence_threshold=0.25)
            elif mode == "combined":
                cv_service.detect_persons_yolov8n(img, confidence_threshold=0.25)
                cv_service.estimate_pose(img, confidence_threshold=0.25)

            lat_ms = (time.perf_counter() - t_start) * 1000
            latencies.append(lat_ms)
            cpu_readings.append(psutil.cpu_percent(interval=None))

        mean_ms = round(float(np.mean(latencies)), 2)
        median_ms = round(float(np.median(latencies)), 2)
        p95_ms = round(float(np.percentile(latencies, 95)), 2)
        fps = round(1000.0 / mean_ms, 2)
        ram_mb = get_process_memory_mb()
        avg_cpu = round(float(np.mean(cpu_readings)), 1)

        benchmark_data["warm_benchmarks"][key] = {
            "name": label,
            "resolution": f"{res}x{res}",
            "iterations": 25,
            "mean_ms": mean_ms,
            "median_ms": median_ms,
            "p95_ms": p95_ms,
            "fps": fps,
            "process_ram_mb": ram_mb,
            "avg_cpu_percent": avg_cpu,
        }
        print(f"[{res}x{res}] {label:32s} -> Mean: {mean_ms:6.2f} ms | Median: {median_ms:6.2f} ms | P95: {p95_ms:6.2f} ms | {fps:5.1f} FPS | RAM: {ram_mb} MB")

    # 5. Frame Skipping Factor Benchmark
    print("\n--- MEASURING FRAME SKIPPING EFFICIENCY (30-frame simulated video) ---")
    total_sim_frames = 30
    for skip in [1, 5, 10]:
        t0 = time.perf_counter()
        processed_count = 0
        for f_idx in range(total_sim_frames):
            if f_idx % skip == 0:
                cv_service.detect_persons_yolov8n(img_320, confidence_threshold=0.25)
                processed_count += 1
        elapsed = time.perf_counter() - t0
        effective_stream_fps = round(total_sim_frames / max(0.001, elapsed), 2)
        inference_fps = round(processed_count / max(0.001, elapsed), 2)

        benchmark_data["frame_skipping"][f"skip_{skip}"] = {
            "frame_skip": skip,
            "total_stream_frames": total_sim_frames,
            "processed_frames": processed_count,
            "elapsed_seconds": round(elapsed, 3),
            "effective_stream_fps": effective_stream_fps,
            "inference_throughput_fps": inference_fps,
        }
        print(f"Skip Factor {skip:2d}: {processed_count:2d}/{total_sim_frames} frames processed in {elapsed:.3f}s -> Stream throughput: {effective_stream_fps:5.1f} FPS")

    # 6. Save results to JSON
    out_path = REPO_ROOT / "docs" / "inference_benchmark_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_data, f, indent=2)
    print(f"\nSaved structured benchmark results to: {out_path}")

    return benchmark_data


if __name__ == "__main__":
    run_benchmark()

