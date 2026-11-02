"""
scripts/reproduce_phone_detection_telemetry.py
Strictly adheres to privacy rules:
- NEVER saves images or faces to disk or repo.
- In-memory processing only.
- Logs text metrics and confidence numbers only.
"""

import time
import cv2
import numpy as np
from ultralytics import YOLO

MODEL_POSE = "models/yolov8n-pose.pt"
MODEL_YOLO = "models/yolov8n.pt"

print("Loading models into memory...")
pose_model = YOLO(MODEL_POSE)
yolo_model = YOLO(MODEL_YOLO)

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("ERROR: Could not open webcam via CAP_DSHOW.")
    exit(1)

print("Webcam successfully opened. Running 10-second diagnostic session...")
print("Please hold phone at chest height in front of camera...")

frames_total = 0
subpass_executed_count = 0
frames_with_class67 = 0
frames_with_class67_above_025 = 0
frames_associated_old_rule = 0
frames_associated_fixed_rule = 0
max_phone_conf = 0.0

start_time = time.time()
while time.time() - start_time < 10.0:
    ret, frame = cap.read()
    if not ret or frame is None:
        continue

    frames_total += 1
    h, w = frame.shape[:2]

    # 1. Pose pass
    pose_res = pose_model(frame, classes=[0], conf=0.25, imgsz=640, verbose=False)
    persons = []
    if pose_res and len(pose_res) > 0 and pose_res[0].boxes:
        for idx, b in enumerate(pose_res[0].boxes):
            coords = b.xyxy[0].cpu().numpy()
            conf = float(b.conf[0].cpu().numpy())
            # Keypoints
            kps = {}
            if pose_res[0].keypoints is not None:
                kp_data = pose_res[0].keypoints.data[idx].cpu().numpy()
                # 9: left_wrist, 10: right_wrist
                if len(kp_data) > 10:
                    kps["left_wrist"] = {"x": float(kp_data[9][0]), "y": float(kp_data[9][1]), "conf": float(kp_data[9][2])}
                    kps["right_wrist"] = {"x": float(kp_data[10][0]), "y": float(kp_data[10][1]), "conf": float(kp_data[10][2])}
            persons.append({
                "id": f"person_{idx+1}",
                "bbox_xyxy": [float(coords[0]), float(coords[1]), float(coords[2]), float(coords[3])],
                # Percentage bbox as created in detect_with_pose:
                "pct_box": {
                    "x": (float(coords[0]) / w) * 100,
                    "y": (float(coords[1]) / h) * 100,
                    "w": (float(coords[2] - coords[0]) / w) * 100,
                    "h": (float(coords[3] - coords[1]) / h) * 100,
                },
                "keypoints": kps
            })

    # 2. Phone pass (COCO class 67 down to conf 0.01)
    subpass_executed_count += 1
    phone_res = yolo_model(frame, classes=[67], conf=0.01, imgsz=640, verbose=False)
    phones = []
    if phone_res and len(phone_res) > 0 and phone_res[0].boxes:
        for b in phone_res[0].boxes:
            p_coords = b.xyxy[0].cpu().numpy()
            p_conf = float(b.conf[0].cpu().numpy())
            phones.append({
                "bbox": [float(p_coords[0]), float(p_coords[1]), float(p_coords[2]), float(p_coords[3])],
                "confidence": p_conf
            })
            if p_conf > max_phone_conf:
                max_phone_conf = p_conf

    if phones:
        frames_with_class67 += 1
        if any(p["confidence"] >= 0.25 for p in phones):
            frames_with_class67_above_025 += 1

    # Test Old Association Rule
    old_assoc = False
    for phone in phones:
        if phone["confidence"] < 0.25:
            continue
        px_c = (phone["bbox"][0] + phone["bbox"][2]) / 2.0
        py_c = (phone["bbox"][1] + phone["bbox"][3]) / 2.0
        for p in persons:
            bx1 = p["pct_box"]["x"]
            by1 = p["pct_box"]["y"]
            bx2 = p["pct_box"]["x"] + p["pct_box"]["w"]
            by2 = p["pct_box"]["y"] + p["pct_box"]["h"]
            margin_x = p["pct_box"]["w"] * 0.15
            margin_y = p["pct_box"]["h"] * 0.10
            if (bx1 - margin_x <= px_c <= bx2 + margin_x) and (by1 <= py_c <= by2 + margin_y):
                old_assoc = True
                break

    if old_assoc:
        frames_associated_old_rule += 1

    # Test Fixed Association Rule (comparing pixel coordinates to pixel coordinates or wrist proximity)
    fixed_assoc = False
    for phone in phones:
        if phone["confidence"] < 0.25:
            continue
        p_box = phone["bbox"]
        px_c = (p_box[0] + p_box[2]) / 2.0
        py_c = (p_box[1] + p_box[3]) / 2.0
        for p in persons:
            pb = p["bbox_xyxy"]
            # Overlap with person body (in pixel space)
            margin_x = (pb[2] - pb[0]) * 0.20
            margin_y = (pb[3] - pb[1]) * 0.20
            in_body = (pb[0] - margin_x <= px_c <= pb[2] + margin_x) and (pb[1] - margin_y <= py_c <= pb[3] + margin_y)

            # Proximity to wrists
            near_wrist = False
            for w_name in ["left_wrist", "right_wrist"]:
                if w_name in p["keypoints"] and p["keypoints"][w_name]["conf"] >= 0.20:
                    wx = p["keypoints"][w_name]["x"]
                    wy = p["keypoints"][w_name]["y"]
                    # Wrist inside phone box or within 50px
                    if (p_box[0] - 40 <= wx <= p_box[2] + 40) and (p_box[1] - 40 <= wy <= p_box[3] + 40):
                        near_wrist = True
                        break

            if in_body or near_wrist:
                fixed_assoc = True
                break

    if fixed_assoc:
        frames_associated_fixed_rule += 1

    # Print log sample every 10 frames
    if frames_total % 10 == 0:
        print(f"Frame {frames_total:>3}: Persons={len(persons)} | Phones(any)={len(phones)} | MaxConf={max_phone_conf:.3f} | OldAssoc={old_assoc} | FixedAssoc={fixed_assoc}")

cap.release()
del frame

print("\n" + "="*70)
print("DIAGNOSTIC TELEMETRY SUMMARY")
print("="*70)
print(f"Total Frames Processed:                {frames_total}")
print(f"Phone Sub-pass Execution Counter:       {subpass_executed_count} / {frames_total} (100%)")
print(f"Frames with ANY Class-67 (>=0.01):     {frames_with_class67} ({frames_with_class67/max(1,frames_total):.1%})")
print(f"Frames with Class-67 >= 0.25:          {frames_with_class67_above_025} ({frames_with_class67_above_025/max(1,frames_total):.1%})")
print(f"Max Phone Confidence Reached:          {max_phone_conf:.3f}")
print(f"Frames Passed OLD Association Rule:    {frames_associated_old_rule} ({frames_associated_old_rule/max(1,frames_total):.1%})")
print(f"Frames Passed FIXED Association Rule:  {frames_associated_fixed_rule} ({frames_associated_fixed_rule/max(1,frames_total):.1%})")
print("="*70)

