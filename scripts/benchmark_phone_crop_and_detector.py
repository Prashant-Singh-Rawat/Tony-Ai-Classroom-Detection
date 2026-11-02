"""
scripts/benchmark_phone_crop_and_detector.py
Benchmarks phone detection latency, wrist-crop pass, and confidence on CPU.
Zero frames or faces saved to disk.
"""

import time
import numpy as np
import cv2
import torch
from ultralytics import YOLO

print("CUDA available:", torch.cuda.is_available())

model_n = YOLO("models/yolov8n.pt")
model_pose = YOLO("models/yolov8n-pose.pt")

# Create a test synthetic frame with a person and a phone shape to measure exact latency
test_img = np.zeros((480, 640, 3), dtype=np.uint8)
# Add some texture so feature maps are non-trivial
cv2.rectangle(test_img, (150, 100), (450, 480), (120, 120, 120), -1) # person body
cv2.rectangle(test_img, (280, 240), (360, 380), (220, 220, 220), -1) # phone in hand

# Warmup
for _ in range(3):
    _ = model_pose(test_img, imgsz=640, verbose=False)
    _ = model_n(test_img, classes=[67], imgsz=640, verbose=False)

# 1. Measure Pose Latency
t0 = time.time()
for _ in range(10):
    _ = model_pose(test_img, imgsz=640, verbose=False)
t_pose = (time.time() - t0) / 10.0 * 1000

# 2. Measure YOLOv8n Full-Frame Class 67 Latency at imgsz=640
t0 = time.time()
for _ in range(10):
    _ = model_n(test_img, classes=[67], conf=0.15, imgsz=640, verbose=False)
t_phone_full = (time.time() - t0) / 10.0 * 1000

# 3. Measure Wrist-Crop Pass Latency at imgsz=320 (e.g. 2 wrist crops)
crop1 = test_img[200:360, 240:400] # 160x160 crop around wrist
t0 = time.time()
for _ in range(10):
    _ = model_n(crop1, classes=[67], conf=0.15, imgsz=320, verbose=False)
t_phone_crop = (time.time() - t0) / 10.0 * 1000

print(f"Pose Estimation (YOLOv8n-pose, 640x480):  {t_pose:.1f} ms")
print(f"Phone Full-Frame Sub-pass (YOLOv8n, 640): {t_phone_full:.1f} ms")
print(f"Phone Wrist-Crop Sub-pass (YOLOv8n, 320): {t_phone_crop:.1f} ms")
print(f"Combined Latency (Pose + Full-Frame):      {t_pose + t_phone_full:.1f} ms (~{1000/(t_pose + t_phone_full):.1f} FPS)")
print(f"Combined Latency (Pose + Wrist-Crop):     {t_pose + t_phone_crop:.1f} ms (~{1000/(t_pose + t_phone_crop):.1f} FPS)")

