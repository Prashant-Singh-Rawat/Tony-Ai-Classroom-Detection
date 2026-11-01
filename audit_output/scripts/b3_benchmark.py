"""
Script: audit_output/scripts/b3_benchmark.py
Phase B3: Multi-Resolution & Confidence Comparison Benchmark.
Evaluates imgsz in [640, 960, 1280] at conf in [0.35, 0.25, 0.15] on CPU across 10 diagnostic frames.
Measures: Total persons detected, Average persons per frame, Inference latency per frame (ms),
CPU usage %, RAM footprint (MB).
"""

import json
import os
import time
import cv2
import psutil
from ultralytics import YOLO

VIDEO_PATH = r"data\classroom_test\ClassVision_Sample_Classroom_Test_Compatible.mp4"
BENCHMARK_OUT = r"audit_output\benchmark_results.json"
MODEL_POSE = r"models\yolov8n-pose.pt"
MODEL_YOLO = r"models\yolov8n.pt"

cap = cv2.VideoCapture(VIDEO_PATH)
fps = cap.get(cv2.CAP_PROP_FPS) or 20.0
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
selected_indices = [10, 35, 60, 85, 110, 135, 160, 185, 210, 235]
frames = {}

for idx in range(total_frames):
    ret, frame = cap.read()
    if not ret:
        break
    if idx in selected_indices:
        frames[idx] = frame

cap.release()

process = psutil.Process(os.getpid())

resolutions = [640, 960, 1280]
confidences = [0.35, 0.25, 0.15]
models_to_test = [("yolov8n", MODEL_YOLO), ("yolov8n-pose", MODEL_POSE)]

results = []

for model_name, model_path in models_to_test:
    model = YOLO(model_path)
    for imgsz in resolutions:
        for conf in confidences:
            latencies = []
            detection_counts = []
            
            # Warm up
            _ = model.predict(frames[selected_indices[0]], conf=conf, imgsz=imgsz, device="cpu", verbose=False)
            
            cpu_before = psutil.cpu_percent(interval=0.1)
            t_start = time.perf_counter()
            for idx in selected_indices:
                img = frames[idx]
                t0 = time.perf_counter()
                kwargs = {"classes": [0]} if model_name == "yolov8n" else {}
                pred = model.predict(img, conf=conf, imgsz=imgsz, device="cpu", verbose=False, **kwargs)[0]
                t1 = time.perf_counter()
                latencies.append((t1 - t0) * 1000.0)
                n_boxes = len(pred.boxes) if pred.boxes is not None else 0
                detection_counts.append(n_boxes)
            t_end = time.perf_counter()
            cpu_after = psutil.cpu_percent(interval=0.1)
            
            ram_mb = process.memory_info().rss / (1024 * 1024)
            avg_latency = sum(latencies) / len(latencies)
            total_detected = sum(detection_counts)
            avg_detected = total_detected / len(detection_counts)
            
            entry = {
                "model": model_name,
                "imgsz": imgsz,
                "confidence": conf,
                "total_persons_detected": total_detected,
                "avg_persons_per_frame": round(avg_detected, 2),
                "avg_latency_ms": round(avg_latency, 1),
                "fps": round(1000.0 / avg_latency, 1) if avg_latency > 0 else 0,
                "ram_mb": round(ram_mb, 1),
                "cpu_percent": round((cpu_before + cpu_after) / 2.0, 1),
            }
            results.append(entry)
            print(f"[{model_name}] imgsz={imgsz} conf={conf:.2f} -> detected={total_detected} (avg {avg_detected:.2f}/fr), latency={avg_latency:.1f}ms, RAM={ram_mb:.1f}MB")

with open(BENCHMARK_OUT, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"\nSaved benchmark results to {BENCHMARK_OUT}")

