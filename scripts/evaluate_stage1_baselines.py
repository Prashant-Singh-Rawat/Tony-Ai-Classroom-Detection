import os
import sys
import json
import time
import psutil
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO

# Ground truth path
GT_JSON = "datasets/evaluation/cv/real_classroom_ground_truth/annotations.json"
FRAMES_DIR = "datasets/evaluation/cv/real_classroom_ground_truth/frames"
VERIFIED_FRAMES = ["10", "52", "700"]
FRAME_FILES = {
    "10": "frame_0010.jpg",
    "52": "frame_0052.jpg",
    "700": "frame_0700.jpg",
}

def box_iou(b1, b2):
    """
    b1, b2: [x1, y1, x2, y2]
    """
    xA = max(b1[0], b2[0])
    yA = max(b1[1], b2[1])
    xB = min(b1[2], b2[2])
    yB = min(b1[3], b2[3])

    inter = max(0.0, xB - xA) * max(0.0, yB - yA)
    area1 = max(1.0, (b1[2] - b1[0]) * (b1[3] - b1[1]))
    area2 = max(1.0, (b2[2] - b2[0]) * (b2[3] - b2[1]))
    union = area1 + area2 - inter
    return inter / union if union > 0 else 0.0

def load_ground_truth():
    with open(GT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    gt_by_frame = {}
    for f_idx in VERIFIED_FRAMES:
        anns = data.get("annotations_by_frame", {}).get(f_idx, [])
        gt_boxes = []
        for a in anns:
            # [x, y, w, h] -> [x1, y1, x2, y2]
            xywh = a["coordinates_xywh"]
            x1 = xywh[0]
            y1 = xywh[1]
            x2 = x1 + xywh[2]
            y2 = y1 + xywh[3]
            gt_boxes.append({
                "person_id": a["person_id"],
                "box": [x1, y1, x2, y2],
                "row_position": a.get("row_position", "unknown"),
                "visibility": a.get("visibility", "unknown"),
            })
        gt_by_frame[f_idx] = gt_boxes
    return gt_by_frame

def evaluate_model(model_name, gt_by_frame, conf_thresh=0.35, nms_iou=0.45):
    print(f"\n--- Evaluating Model: {model_name} (conf={conf_thresh}, nms={nms_iou}) ---")
    model = YOLO(model_name)
    
    results_iou50 = {"tp": 0, "fp": 0, "fn": 0}
    results_iou30 = {"tp": 0, "fp": 0, "fn": 0}
    row_stats = {
        "row_1_front": {"total": 0, "detected_50": 0, "detected_30": 0},
        "row_2_mid_front": {"total": 0, "detected_50": 0, "detected_30": 0},
        "row_3_mid_back": {"total": 0, "detected_50": 0, "detected_30": 0},
        "row_4_rear": {"total": 0, "detected_50": 0, "detected_30": 0},
    }
    
    latencies = []
    total_det_boxes = 0
    duplicate_or_desk_boxes = 0
    
    process = psutil.Process(os.getpid())
    ram_before_mb = process.memory_info().rss / (1024 * 1024)

    for f_idx in VERIFIED_FRAMES:
        img_path = os.path.join(FRAMES_DIR, FRAME_FILES[f_idx])
        img = cv2.imread(img_path)
        h, w = img.shape[:2]
        
        # Warmup and timed inference
        t0 = time.perf_counter()
        pred = model(
            img,
            classes=[0],
            conf=conf_thresh,
            iou=nms_iou,
            imgsz=640,
            device="cpu",
            verbose=False,
        )
        lat = (time.perf_counter() - t0) * 1000.0
        latencies.append(lat)
        
        gt_boxes = gt_by_frame[f_idx]
        for gt in gt_boxes:
            row_stats[gt["row_position"]]["total"] += 1
            
        pred_boxes = []
        if pred and len(pred) > 0 and pred[0].boxes:
            for b in pred[0].boxes:
                coords = b.xyxy[0].cpu().numpy().tolist()
                c = float(b.conf[0].cpu().numpy())
                pred_boxes.append(coords)
                total_det_boxes += 1
                
        # Matching for IoU 0.50
        matched_gt_50 = set()
        matched_pred_50 = set()
        for p_i, pb in enumerate(pred_boxes):
            best_iou = 0.0
            best_g = -1
            for g_i, gt in enumerate(gt_boxes):
                if g_i in matched_gt_50:
                    continue
                iou = box_iou(pb, gt["box"])
                if iou > best_iou:
                    best_iou = iou
                    best_g = g_i
            if best_iou >= 0.50:
                matched_gt_50.add(best_g)
                matched_pred_50.add(p_i)
                row_stats[gt_boxes[best_g]["row_position"]]["detected_50"] += 1
                
        tp_50 = len(matched_gt_50)
        fp_50 = len(pred_boxes) - len(matched_pred_50)
        fn_50 = len(gt_boxes) - tp_50
        results_iou50["tp"] += tp_50
        results_iou50["fp"] += fp_50
        results_iou50["fn"] += fn_50

        # Matching for IoU 0.30
        matched_gt_30 = set()
        matched_pred_30 = set()
        for p_i, pb in enumerate(pred_boxes):
            best_iou = 0.0
            best_g = -1
            for g_i, gt in enumerate(gt_boxes):
                if g_i in matched_gt_30:
                    continue
                iou = box_iou(pb, gt["box"])
                if iou > best_iou:
                    best_iou = iou
                    best_g = g_i
            if best_iou >= 0.30:
                matched_gt_30.add(best_g)
                matched_pred_30.add(p_i)
                row_stats[gt_boxes[best_g]["row_position"]]["detected_30"] += 1
                
        tp_30 = len(matched_gt_30)
        fp_30 = len(pred_boxes) - len(matched_pred_30)
        fn_30 = len(gt_boxes) - tp_30
        results_iou30["tp"] += tp_30
        results_iou30["fp"] += fp_30
        results_iou30["fn"] += fn_30
        
        # Check for duplicate predictions (IoU between predictions > 0.45)
        for i in range(len(pred_boxes)):
            for j in range(i + 1, len(pred_boxes)):
                if box_iou(pred_boxes[i], pred_boxes[j]) > 0.40:
                    duplicate_or_desk_boxes += 1

    ram_after_mb = process.memory_info().rss / (1024 * 1024)
    avg_latency = sum(latencies) / len(latencies)
    
    # Compute metrics at 0.50
    tp50, fp50, fn50 = results_iou50["tp"], results_iou50["fp"], results_iou50["fn"]
    prec50 = tp50 / max(1, tp50 + fp50)
    rec50 = tp50 / max(1, tp50 + fn50)
    f1_50 = 2 * (prec50 * rec50) / max(1e-6, prec50 + rec50)

    # Compute metrics at 0.30
    tp30, fp30, fn30 = results_iou30["tp"], results_iou30["fp"], results_iou30["fn"]
    prec30 = tp30 / max(1, tp30 + fp30)
    rec30 = tp30 / max(1, tp30 + fn30)
    f1_30 = 2 * (prec30 * rec30) / max(1e-6, prec30 + rec30)

    out = {
        "model": model_name,
        "conf_threshold": conf_thresh,
        "total_gt": tp50 + fn50,
        "total_pred": total_det_boxes,
        "avg_latency_ms": round(avg_latency, 1),
        "fps": round(1000.0 / avg_latency, 1),
        "ram_mb": round(ram_after_mb, 1),
        "iou50": {
            "tp": tp50, "fp": fp50, "fn": fn50,
            "precision": round(prec50 * 100, 1),
            "recall": round(rec50 * 100, 1),
            "f1": round(f1_50 * 100, 1),
        },
        "iou30": {
            "tp": tp30, "fp": fp30, "fn": fn30,
            "precision": round(prec30 * 100, 1),
            "recall": round(rec30 * 100, 1),
            "f1": round(f1_30 * 100, 1),
        },
        "row_recall_iou30": {
            k: f"{v['detected_30']}/{v['total']} ({v['detected_30']/max(1, v['total'])*100:.1f}%)"
            for k, v in row_stats.items()
        },
        "duplicate_predictions": duplicate_or_desk_boxes,
    }
    return out

def main():
    gt = load_ground_truth()
    models = [
        "yolov8n.pt",
        "yolov8s.pt",
        "yolov8m.pt",
        "yolov8n-pose.pt",
        "yolov8s-pose.pt",
        "yolov8m-pose.pt",
        "yolo11n.pt",
    ]
    
    all_results = []
    for m in models:
        res = evaluate_model(m, gt, conf_thresh=0.35, nms_iou=0.45)
        all_results.append(res)
        print(json.dumps(res, indent=2))
        
    # Also evaluate yolov8n at conf=0.25 to see if lower threshold helps back row
    res_n_25 = evaluate_model("yolov8n.pt", gt, conf_thresh=0.25, nms_iou=0.45)
    all_results.append(res_n_25)
    print(json.dumps(res_n_25, indent=2))

    with open("docs/stage1_baseline_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print("\n[VERIFIED] Successfully saved stage1_baseline_results.json")

if __name__ == "__main__":
    main()

