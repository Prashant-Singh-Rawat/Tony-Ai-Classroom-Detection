"""
Script: audit_output/scripts/b4_coordinate_check.py
Phase B4: Coordinate-Mapping Numeric Check.
Traces one real detection through:
1. Native frame pixel space (W=960, H=540)
2. Letterboxed tensor space (imgsz=640)
3. Post-inference un-letterboxing
4. Serialized payload space ([0, 100] percentage vs raw pixels)
5. Keypoint coordinate space
6. Frontend rendering math
"""

import sys
import json
import cv2
import numpy as np
from ultralytics import YOLO

from backend.app.services.computer_vision.letterbox import (
    letterbox_image,
    scale_boxes_to_original,
    scale_keypoints_to_original,
)

VIDEO_PATH = r"data\classroom_test\ClassVision_Sample_Classroom_Test_Compatible.mp4"
MODEL_POSE = r"models\yolov8n-pose.pt"

cap = cv2.VideoCapture(VIDEO_PATH)
ret, frame = cap.read()
cap.release()

img_h, img_w = frame.shape[:2]
print(f"--- Stage 1: Native Frame Dimensions ---")
print(f"Native Resolution: width={img_w}, height={img_h}, aspect={img_w/img_h:.4f}")

# Stage 2: Letterboxing
imgsz = 640
lb_img, ratio, (pad_w, pad_h) = letterbox_image(frame, target_shape=(imgsz, imgsz), auto=False)
lb_h, lb_w = lb_img.shape[:2]
print(f"\n--- Stage 2: Letterboxing ---")
print(f"Target size: {imgsz}x{imgsz}")
print(f"Letterbox output: {lb_w}x{lb_h}")
print(f"Scale ratio: {ratio:.4f}")
print(f"Padding: pad_w={pad_w:.1f}, pad_h={pad_h:.1f}")

# Run inference with YOLOv8n-pose
pose = YOLO(MODEL_POSE)
results = pose.predict(frame, conf=0.15, imgsz=imgsz, device="cpu", verbose=False)[0]

print(f"\n--- Stage 3: Raw YOLO Model Output ---")
boxes = results.boxes
kpts = results.keypoints
print(f"Total detections at conf=0.15: {len(boxes)}")

if len(boxes) > 0:
    box0 = boxes[0]
    raw_xyxy = box0.xyxy[0].cpu().numpy()
    conf0 = float(box0.conf[0].cpu().numpy())
    x1, y1, x2, y2 = raw_xyxy
    w_px = x2 - x1
    h_px = y2 - y1
    print(f"Sample Person 1 Raw BBox (in original frame coords directly scaled back by Ultralytics):")
    print(f"  x1={x1:.2f}, y1={y1:.2f}, x2={x2:.2f}, y2={y2:.2f}")
    print(f"  width={w_px:.2f}px, height={h_px:.2f}px")

    # Stage 4: Backend serialization in service.py
    x_pct = max(0.0, min(100.0, (x1 / img_w) * 100))
    y_pct = max(0.0, min(100.0, (y1 / img_h) * 100))
    w_pct = max(0.0, min(100.0, (w_px / img_w) * 100))
    h_pct = max(0.0, min(100.0, (h_px / img_h) * 100))

    print(f"\n--- Stage 4: Backend Serialized BBox ([0, 100] percentage) ---")
    print(f"  x={x_pct:.2f}%, y={y_pct:.2f}%, w={w_pct:.2f}%, h={h_pct:.2f}%")

    # Stage 5: Keypoint coordinate check
    kp_data = kpts[0].data[0].cpu().numpy()
    nose = kp_data[0]
    l_shoulder = kp_data[5]
    r_shoulder = kp_data[6]
    print(f"\n--- Stage 5: Keypoint Coordinate Space ---")
    print(f"  Nose: x={nose[0]:.2f}px, y={nose[1]:.2f}px, conf={nose[2]:.2f}")
    print(f"  L Shoulder: x={l_shoulder[0]:.2f}px, y={l_shoulder[1]:.2f}px, conf={l_shoulder[2]:.2f}")
    print(f"  R Shoulder: x={r_shoulder[0]:.2f}px, y={r_shoulder[1]:.2f}px, conf={r_shoulder[2]:.2f}")
    print(f"  OBSERVATION: Keypoints are returned by Ultralytics in RAW PIXELS of original image (0 to {img_w}, 0 to {img_h})!")

    # Stage 6: Frontend interpretation in MonitoringPage.tsx
    frontend_kp_x = (l_shoulder[0] / img_w) * 100
    frontend_kp_y = (l_shoulder[1] / img_h) * 100
    print(f"\n--- Stage 6: Frontend Interpretation ---")
    print(f"  Frontend BBox style: left: {x_pct:.2f}%, top: {y_pct:.2f}%, width: {w_pct:.2f}%, height: {h_pct:.2f}%")
    print(f"  Frontend L-Shoulder SVG: cx: {frontend_kp_x:.2f}%, cy: {frontend_kp_y:.2f}%")
    inside_x = x_pct <= frontend_kp_x <= (x_pct + w_pct)
    inside_y = y_pct <= frontend_kp_y <= (y_pct + h_pct)
    print(f"  Match result: inside_x={inside_x}, inside_y={inside_y}")

    # Check for potential failure in fallback dimensions:
    distorted_kp_x = (l_shoulder[0] / 640.0) * 100
    distorted_kp_y = (l_shoulder[1] / 480.0) * 100
    print(f"\n  CRITICAL RISK CHECK: If imageWidth/imageHeight fall back to 640/480:")
    print(f"  Distorted cx={distorted_kp_x:.2f}%, cy={distorted_kp_y:.2f}% (Shift of {abs(distorted_kp_x - frontend_kp_x):.2f}% in X, {abs(distorted_kp_y - frontend_kp_y):.2f}% in Y!)")
