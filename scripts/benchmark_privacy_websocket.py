"""
scripts/benchmark_privacy_websocket.py — Phase 2.8 Real-Time Latency Benchmark
=============================================================================
Measures exact CPU wall-clock inference latencies across the 5 processing configurations:
1. Baseline YOLOv8n (No Privacy Blur)
2. YOLOv8n + Server-Side In-Memory Privacy Blur
3. YOLOv8n-pose (No Privacy Blur)
4. YOLOv8n-pose + Server-Side In-Memory Privacy Blur
5. Full End-to-End Pipeline: YOLOv8n-pose + Privacy Blur + Temporal Tracking + SQLite Upsert
Reports: Mean, Median, P95, Min, Max, and estimated FPS on local HP Victus hardware.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import base64
import io
import json
import statistics
import time
from typing import List
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

from backend.app.database.db import SessionLocal
from backend.app.database.repositories import HandRaiseEventRepository
from backend.app.main import app
from backend.app.services.computer_vision import cv_service
from backend.app.services.tracking.synthetic_sequences import generate_single_person_sequence
from backend.app.services.tracking.temporal_tracker import temporal_tracker


def make_test_frame_b64(width: int = 640, height: int = 480) -> str:
    """Creates a synthetic classroom frame in base64 format."""
    img = Image.new("RGB", (width, height), color=(140, 150, 160))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def benchmark_pipeline(num_iterations: int = 30) -> dict:
    client = TestClient(app)
    b64_frame = make_test_frame_b64()

    # Pre-warm models so first-load initialization doesn't skew stats
    with client.websocket_connect("/api/ws/detections") as ws:
        _ = ws.receive_json()
        ws.send_json({
            "type": "frame",
            "frame": b64_frame,
            "detectPose": True,
            "serverSideBlur": True,
            "sessionId": "warmup",
        })
        _ = ws.receive_json()

    results = {}

    configs = [
        {
            "name": "1. Person Detection (YOLOv8n, No Blur)",
            "payload": {
                "type": "frame",
                "frame": b64_frame,
                "detectPose": False,
                "serverSideBlur": False,
                "sessionId": "bench_p1",
            },
        },
        {
            "name": "2. Person Detection + Server Privacy Blur",
            "payload": {
                "type": "frame",
                "frame": b64_frame,
                "detectPose": False,
                "serverSideBlur": True,
                "sessionId": "bench_p2",
            },
        },
        {
            "name": "3. Pose Estimation (YOLOv8n-pose, No Blur)",
            "payload": {
                "type": "frame",
                "frame": b64_frame,
                "detectPose": True,
                "serverSideBlur": False,
                "sessionId": "bench_p3",
            },
        },
        {
            "name": "4. Pose Estimation + Server Privacy Blur",
            "payload": {
                "type": "frame",
                "frame": b64_frame,
                "detectPose": True,
                "serverSideBlur": True,
                "sessionId": "bench_p4",
            },
        },
        {
            "name": "5. Full Pipeline (Pose + Blur + Tracking + SQLite)",
            "payload": {
                "type": "frame",
                "frame": b64_frame,
                "detectPose": True,
                "serverSideBlur": True,
                "clientSideBlur": True,
                "sessionId": "bench_p5",
            },
        },
    ]

    with client.websocket_connect("/api/ws/detections") as ws:
        _ = ws.receive_json()

        for cfg in configs:
            durations_ms: List[float] = []
            for _ in range(num_iterations):
                t0 = time.perf_counter()
                ws.send_json(cfg["payload"])
                resp = ws.receive_json()
                t1 = time.perf_counter()
                durations_ms.append((t1 - t0) * 1000.0)

            durations_ms.sort()
            mean_ms = statistics.mean(durations_ms)
            median_ms = statistics.median(durations_ms)
            p95_ms = np.percentile(durations_ms, 95)
            min_ms = min(durations_ms)
            max_ms = max(durations_ms)
            fps = 1000.0 / mean_ms if mean_ms > 0 else 0.0

            results[cfg["name"]] = {
                "samples": num_iterations,
                "mean_ms": round(float(mean_ms), 2),
                "median_ms": round(float(median_ms), 2),
                "p95_ms": round(float(p95_ms), 2),
                "min_ms": round(float(min_ms), 2),
                "max_ms": round(float(max_ms), 2),
                "estimated_fps": round(float(fps), 1),
            }

    return results


if __name__ == "__main__":
    print("=" * 70)
    print("CLASSVISION AI — PHASE 2.8 WEBSOCKET PRIVACY & PERSISTENCE BENCHMARK")
    print("Hardware Profile: HP Victus Laptop (PyTorch CPU Inference Fallback)")
    print("=" * 70)
    bench_results = benchmark_pipeline(num_iterations=25)
    print(json.dumps(bench_results, indent=2))
