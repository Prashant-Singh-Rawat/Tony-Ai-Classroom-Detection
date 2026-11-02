"""
scripts/audit_duplicate_boxes_and_confidence.py
Audits duplicate bounding box pairs, confidence histograms, and NMS suppression
across the 10 real classroom frames (depositphotos_stock_classroom.mp4) at imgsz 640, 960, 1280.
Generates annotated visual diagnostics highlighting overlapping pairs (IoU > 0.3).
"""

import os
import cv2
import numpy as np
import torch
from ultralytics import YOLO

VIDEO_PATH = "data/classroom_test/depositphotos_stock_classroom.mp4"
OUTPUT_DIR = "audit_output/duplicate_box_analysis"
os.makedirs(OUTPUT_DIR, exist_ok=True)

MODEL_PATH = "models/yolov8n-pose.pt"
model = YOLO(MODEL_PATH)

FRAMES = [50, 150, 300, 450, 600, 750, 900, 1050, 1200, 1350]

def compute_iou(box1, box2):
    # box format: [x1, y1, x2, y2]
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    inter_w = max(0.0, x2 - x1)
    inter_h = max(0.0, y2 - y1)
    inter_area = inter_w * inter_h
    
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union_area = area1 + area2 - inter_area
    if union_area <= 0:
        return 0.0
    return inter_area / union_area

def run_duplicate_audit():
    print("==================================================================")
    print("AUDIT: DUPLICATE BOXES & OVERLAP ON REAL CLASSROOM FOOTAGE")
    print("==================================================================")
    cap = cv2.VideoCapture(VIDEO_PATH)
    
    results = {}
    
    for f_idx in FRAMES:
        cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
        ret, frame = cap.read()
        if not ret:
            print(f"Error reading frame {f_idx}")
            continue
            
        h, w = frame.shape[:2]
        
        # Run YOLOv8n-pose at imgsz=640, conf=0.15 (raw model output)
        pred = model(frame, imgsz=640, conf=0.15, verbose=False)[0]
        boxes_xyxy = pred.boxes.xyxy.cpu().numpy()
        confs = pred.boxes.conf.cpu().numpy()
        
        num_raw = len(boxes_xyxy)
        
        # Find overlapping pairs with IoU > 0.3
        overlapping_pairs = []
        suppressed_indices = set()
        
        # Sort by confidence descending
        order = np.argsort(-confs)
        
        for i_idx in range(len(order)):
            i = order[i_idx]
            if i in suppressed_indices:
                continue
            for j_idx in range(i_idx + 1, len(order)):
                j = order[j_idx]
                if j in suppressed_indices:
                    continue
                iou = compute_iou(boxes_xyxy[i], boxes_xyxy[j])
                if iou > 0.30:
                    overlapping_pairs.append((i, j, iou, confs[i], confs[j]))
                    suppressed_indices.add(j)
                    
        num_survived = num_raw - len(suppressed_indices)
        
        results[f_idx] = {
            "raw_boxes": num_raw,
            "overlapping_pairs": len(overlapping_pairs),
            "suppressed_duplicates": len(suppressed_indices),
            "survived_after_iou30": num_survived,
            "conf_mean": float(np.mean(confs)) if len(confs) > 0 else 0.0,
            "pairs_detail": overlapping_pairs
        }
        
        print(f"Frame {f_idx:4d}: {num_raw:2d} raw boxes | {len(overlapping_pairs):2d} pairs overlap (IoU>0.3) | {len(suppressed_indices):2d} duplicates | {num_survived:2d} survived")

        # Generate annotated diagnostic image highlighting overlapping pairs
        diag_img = frame.copy()
        
        # Draw all non-duplicate boxes in emerald green
        for idx in range(num_raw):
            if idx not in suppressed_indices:
                x1, y1, x2, y2 = [int(v) for v in boxes_xyxy[idx]]
                cv2.rectangle(diag_img, (x1, y1), (x2, y2), (0, 200, 100), 1)
                cv2.putText(diag_img, f"{confs[idx]:.2f}", (x1, max(12, y1 - 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 200, 100), 1)
                
        # Draw duplicate boxes in bright magenta/red with connecting line
        for (i, j, iou, ci, cj) in overlapping_pairs:
            x1_i, y1_i, x2_i, y2_i = [int(v) for v in boxes_xyxy[i]]
            x1_j, y1_j, x2_j, y2_j = [int(v) for v in boxes_xyxy[j]]
            cv2.rectangle(diag_img, (x1_j, y1_j), (x2_j, y2_j), (0, 0, 255), 2)
            cv2.putText(diag_img, f"DUP {cj:.2f} (IoU:{iou:.2f})", (x1_j, min(h - 5, y2_j + 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
            # Line between centers
            ci_x = (x1_i + x2_i) // 2
            ci_y = (y1_i + y2_i) // 2
            cj_x = (x1_j + x2_j) // 2
            cj_y = (y1_j + y2_j) // 2
            cv2.line(diag_img, (ci_x, ci_y), (cj_x, cj_y), (255, 0, 255), 1)
            
        out_path = os.path.join(OUTPUT_DIR, f"frame_{f_idx:04d}_duplicates.jpg")
        cv2.imwrite(out_path, diag_img)

    cap.release()
    return results

def run_confidence_histograms_imgsz():
    print("\n==================================================================")
    print("AUDIT: PER-BOX CONFIDENCE HISTOGRAMS AT 640 / 960 / 1280 (FRAME 450)")
    print("==================================================================")
    cap = cv2.VideoCapture(VIDEO_PATH)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 450)
    ret, frame = cap.read()
    cap.release()
    assert ret, "Could not read frame 450"
    
    for sz in [640, 960, 1280]:
        pred = model(frame, imgsz=sz, conf=0.05, verbose=False)[0] # conf=0.05 to capture all candidates
        confs = pred.boxes.conf.cpu().numpy()
        
        # Binned confidence counts
        bins = [(0.05, 0.15), (0.15, 0.25), (0.25, 0.50), (0.50, 0.75), (0.75, 1.00)]
        bin_counts = [int(np.sum((confs >= b[0]) & (confs < b[1]))) for b in bins]
        
        at_conf_15 = int(np.sum(confs >= 0.15))
        at_conf_25 = int(np.sum(confs >= 0.25))
        
        print(f"\n--- imgsz = {sz} ---")
        print(f"Total candidates (conf >= 0.05): {len(confs)}")
        print(f"Boxes at conf >= 0.15: {at_conf_15}")
        print(f"Boxes at conf >= 0.25: {at_conf_25}")
        print(f"Mean confidence (for conf >= 0.15): {float(np.mean(confs[confs >= 0.15])):.3f}" if at_conf_15 > 0 else "N/A")
        print("Confidence histogram distribution:")
        for b, count in zip(bins, bin_counts):
            pct = (count / max(1, len(confs))) * 100
            bar = '#' * int(pct // 4)
            print(f"  [{b[0]:.2f} - {b[1]:.2f}): {count:2d} ({pct:5.1f}%) | {bar}")

if __name__ == "__main__":
    run_duplicate_audit()
    run_confidence_histograms_imgsz()

