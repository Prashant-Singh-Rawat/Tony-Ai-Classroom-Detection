import time
import cv2
import numpy as np
from ultralytics import YOLO

models = ["yolov8n.pt", "yolov8s.pt", "yolov8m.pt", "yolo11n.pt"]

print("=== OFF-THE-SHELF PRETRAINED PHONE DETECTION BENCHMARK ===")

# Test 1: Real-footage classroom frames (evaluating whether phone class 67 fires on classroom desks/students)
frames = [
    "datasets/evaluation/cv/real_classroom_ground_truth/frames/frame_0010.jpg",
    "datasets/evaluation/cv/real_classroom_ground_truth/frames/frame_0052.jpg",
    "datasets/evaluation/cv/real_classroom_ground_truth/frames/frame_0700.jpg",
]

for m_name in models:
    m = YOLO(m_name)
    phones_detected_in_classroom = 0
    max_phone_conf = 0.0
    
    t0 = time.perf_counter()
    for fp in frames:
        img = cv2.imread(fp)
        res = m(img, classes=[67], conf=0.10, imgsz=640, device="cpu", verbose=False)
        if res and len(res) > 0 and res[0].boxes:
            for b in res[0].boxes:
                c = float(b.conf[0].cpu().numpy())
                phones_detected_in_classroom += 1
                if c > max_phone_conf:
                    max_phone_conf = c
    lat = (time.perf_counter() - t0) * 1000.0 / len(frames)
    print(f"Model: {m_name:12s} | Phones on 3 real classroom frames: {phones_detected_in_classroom} | Max conf: {max_phone_conf:.3f} | Latency: {lat:.1f}ms")

# Test 2: Live webcam phone test (DirectShow capture, in memory, numbers only, zero disk writes)
print("\n--- Live Webcam Staged Phone Test (Numbers Only, Zero Disk Writes) ---")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("[UNKNOWN] Webcam cannot be opened (busy or absent).")
else:
    frames_grabbed = []
    for _ in range(5):
        ret, frame = cap.read()
        if ret:
            frames_grabbed.append(frame)
        time.sleep(0.05)
    cap.release()
    
    if not frames_grabbed:
        print("[UNKNOWN] Failed to read webcam frames.")
    else:
        print(f"[VERIFIED] Read {len(frames_grabbed)} live frames ({frames_grabbed[0].shape[1]}x{frames_grabbed[0].shape[0]}). Running inference...")
        for m_name in models:
            m = YOLO(m_name)
            confs = []
            for frame in frames_grabbed:
                res = m(frame, classes=[67], conf=0.01, imgsz=640, device="cpu", verbose=False)
                if res and len(res) > 0 and res[0].boxes:
                    for b in res[0].boxes:
                        confs.append(float(b.conf[0].cpu().numpy()))
            max_c = max(confs) if confs else 0.0
            detected_fraction = len(confs) / len(frames_grabbed)
            print(f"Model: {m_name:12s} | Phone Detections (conf>=0.01): {len(confs)}/{len(frames_grabbed)} | Max conf: {max_c:.3f} | Avg conf: {sum(confs)/max(1, len(confs)):.3f}")

