import cv2
import numpy as np
from ultralytics import YOLO

# Evaluate class 67 detection across models down to conf=0.01
models = {
    "yolov8n": YOLO("yolov8n.pt"),
    "yolov8s": YOLO("yolov8s.pt"),
    "yolo11n": YOLO("yolo11n.pt"),
}

print("=== STAGE 1B PHONE POSITIVE CONTROL TEST (CONF DOWN TO 0.01) ===")

# Test 1: Real classroom frames where students have hands/objects on desks
frames = [
    ("Frame 10", "datasets/evaluation/cv/real_classroom_ground_truth/frames/frame_0010.jpg"),
    ("Frame 52", "datasets/evaluation/cv/real_classroom_ground_truth/frames/frame_0052.jpg"),
    ("Frame 700", "datasets/evaluation/cv/real_classroom_ground_truth/frames/frame_0700.jpg"),
]

for label, fpath in frames:
    img = cv2.imread(fpath)
    print(f"\nEvaluating {label} ({img.shape[1]}x{img.shape[0]}):")
    for name, m in models.items():
        res = m(img, classes=[67], conf=0.01, imgsz=640, device="cpu", verbose=False)[0].boxes
        dets = []
        if res:
            for b in res:
                c = float(b.conf[0].cpu().numpy())
                xy = [round(float(x), 1) for x in b.xyxy[0].cpu().numpy()]
                dets.append((round(c, 4), xy))
        print(f"  {name:8s}: {len(dets)} detections down to conf=0.01 | Detections: {dets}")

# Test 2: Live webcam DirectShow staged test (In-memory, zero face/frame disk writes)
print("\n--- Live Webcam Inference (Logging class 67 down to conf=0.01) ---")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if cap.isOpened():
    ret, frame = cap.read()
    cap.release()
    if ret:
        print(f"Live webcam captured frame ({frame.shape[1]}x{frame.shape[0]}). Evaluating...")
        for name, m in models.items():
            res = m(frame, classes=[67], conf=0.01, imgsz=640, device="cpu", verbose=False)[0].boxes
            dets = []
            if res:
                for b in res:
                    c = float(b.conf[0].cpu().numpy())
                    xy = [round(float(x), 1) for x in b.xyxy[0].cpu().numpy()]
                    dets.append((round(c, 4), xy))
            print(f"  {name:8s}: {len(dets)} detections down to conf=0.01 | Detections: {dets}")
    else:
        print("Webcam frame read returned False.")
else:
    print("Webcam not openable.")

