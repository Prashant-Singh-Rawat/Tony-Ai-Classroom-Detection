import os
import sys
import json
import time
import cv2
import numpy as np
from ultralytics import YOLO

GT_JSON = "datasets/evaluation/cv/real_classroom_ground_truth/annotations.json"
FRAMES_DIR = "datasets/evaluation/cv/real_classroom_ground_truth/frames"
VERIFIED_FRAMES = ["10", "52", "700"]
FRAME_FILES = {
    "10": "frame_0010.jpg",
    "52": "frame_0052.jpg",
    "700": "frame_0700.jpg",
}

def box_iou(b1, b2):
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
            xywh = a["coordinates_xywh"]
            x1 = xywh[0]
            y1 = xywh[1]
            x2 = x1 + xywh[2]
            y2 = y1 + xywh[3]
            h = xywh[3]
            if h < 45.0:
                h_bucket = "<45px"
            elif h < 75.0:
                h_bucket = "45-74px"
            else:
                h_bucket = ">=75px"
            gt_boxes.append({
                "person_id": a["person_id"],
                "box": [x1, y1, x2, y2],
                "height": h,
                "h_bucket": h_bucket,
                "row_position": a.get("row_position", "unknown"),
            })
        gt_by_frame[f_idx] = gt_boxes
    return gt_by_frame

def evaluate_run(model, model_name, imgsz, conf, nms_iou, max_det, gt_by_frame):
    results_iou50 = {"tp": 0, "fp": 0, "fn": 0}
    results_iou30 = {"tp": 0, "fp": 0, "fn": 0}
    row_stats = {
        "row_1_front": {"total": 0, "det30": 0, "det50": 0},
        "row_2_mid_front": {"total": 0, "det30": 0, "det50": 0},
        "row_3_mid_back": {"total": 0, "det30": 0, "det50": 0},
        "row_4_rear": {"total": 0, "det30": 0, "det50": 0},
    }
    bucket_stats = {
        "<45px": {"total": 0, "det30": 0, "det50": 0},
        "45-74px": {"total": 0, "det30": 0, "det50": 0},
        ">=75px": {"total": 0, "det30": 0, "det50": 0},
    }
    
    latencies = []
    total_det_boxes = 0
    duplicate_boxes = 0

    for f_idx in VERIFIED_FRAMES:
        img_path = os.path.join(FRAMES_DIR, FRAME_FILES[f_idx])
        img = cv2.imread(img_path)
        
        # Measure warm latency (median of 3 runs per frame)
        frame_lats = []
        for _ in range(3):
            t0 = time.perf_counter()
            pred = model(
                img,
                classes=[0],
                conf=conf,
                iou=nms_iou,
                imgsz=imgsz,
                max_det=max_det,
                device="cpu",
                verbose=False,
            )
            frame_lats.append((time.perf_counter() - t0) * 1000.0)
        frame_lats.sort()
        latencies.append(frame_lats[1]) # median
        
        gt_boxes = gt_by_frame[f_idx]
        for gt in gt_boxes:
            row_stats[gt["row_position"]]["total"] += 1
            bucket_stats[gt["h_bucket"]]["total"] += 1
            
        pred_boxes = []
        if pred and len(pred) > 0 and pred[0].boxes:
            for b in pred[0].boxes:
                coords = b.xyxy[0].cpu().numpy().tolist()
                pred_boxes.append(coords)
                total_det_boxes += 1
                
        # Matching IoU 0.50
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
                row_stats[gt_boxes[best_g]["row_position"]]["det50"] += 1
                bucket_stats[gt_boxes[best_g]["h_bucket"]]["det50"] += 1
                
        results_iou50["tp"] += len(matched_gt_50)
        results_iou50["fp"] += len(pred_boxes) - len(matched_pred_50)
        results_iou50["fn"] += len(gt_boxes) - len(matched_gt_50)

        # Matching IoU 0.30
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
                row_stats[gt_boxes[best_g]["row_position"]]["det30"] += 1
                bucket_stats[gt_boxes[best_g]["h_bucket"]]["det30"] += 1
                
        results_iou30["tp"] += len(matched_gt_30)
        results_iou30["fp"] += len(pred_boxes) - len(matched_pred_30)
        results_iou30["fn"] += len(gt_boxes) - len(matched_gt_30)

        # Count duplicate prediction pairs (IoU > 0.30 between predictions)
        for i in range(len(pred_boxes)):
            for j in range(i + 1, len(pred_boxes)):
                if box_iou(pred_boxes[i], pred_boxes[j]) > 0.30:
                    duplicate_boxes += 1

    # Aggregate metrics
    tp50, fp50, fn50 = results_iou50["tp"], results_iou50["fp"], results_iou50["fn"]
    prec50 = tp50 / max(1, tp50 + fp50)
    rec50 = tp50 / max(1, tp50 + fn50)
    f1_50 = 2 * (prec50 * rec50) / max(1e-6, prec50 + rec50)

    tp30, fp30, fn30 = results_iou30["tp"], results_iou30["fp"], results_iou30["fn"]
    prec30 = tp30 / max(1, tp30 + fp30)
    rec30 = tp30 / max(1, tp30 + fn30)
    f1_30 = 2 * (prec30 * rec30) / max(1e-6, prec30 + rec30)

    latencies.sort()
    med_latency = latencies[len(latencies) // 2]

    return {
        "model": model_name,
        "imgsz": imgsz,
        "conf": conf,
        "prec50": round(prec50 * 100, 1),
        "rec50": round(rec50 * 100, 1),
        "f1_50": round(f1_50 * 100, 1),
        "prec30": round(prec30 * 100, 1),
        "rec30": round(rec30 * 100, 1),
        "f1_30": round(f1_30 * 100, 1),
        "tp30": tp30, "fp30": fp30, "fn30": fn30,
        "duplicates": duplicate_boxes,
        "total_pred": total_det_boxes,
        "med_latency_ms": round(med_latency, 1),
        "fps": round(1000.0 / max(1.0, med_latency), 1),
        "row_recall_30": {
            "r1": f"{row_stats['row_1_front']['det30']}/{row_stats['row_1_front']['total']}",
            "r2": f"{row_stats['row_2_mid_front']['det30']}/{row_stats['row_2_mid_front']['total']}",
            "r3": f"{row_stats['row_3_mid_back']['det30']}/{row_stats['row_3_mid_back']['total']}",
            "r4": f"{row_stats['row_4_rear']['det30']}/{row_stats['row_4_rear']['total']}",
        },
        "row4_pct": round(row_stats['row_4_rear']['det30'] / max(1, row_stats['row_4_rear']['total']) * 100, 1),
        "height_recall_30": {
            "<45px": f"{bucket_stats['<45px']['det30']}/{bucket_stats['<45px']['total']}",
            "45-74px": f"{bucket_stats['45-74px']['det30']}/{bucket_stats['45-74px']['total']}",
            ">=75px": f"{bucket_stats['>=75px']['det30']}/{bucket_stats['>=75px']['total']}",
        },
        "h_lt45_pct": round(bucket_stats['<45px']['det30'] / max(1, bucket_stats['<45px']['total']) * 100, 1),
        "h_45_74_pct": round(bucket_stats['45-74px']['det30'] / max(1, bucket_stats['45-74px']['total']) * 100, 1),
        "h_ge75_pct": round(bucket_stats['>=75px']['det30'] / max(1, bucket_stats['>=75px']['total']) * 100, 1),
    }

def main():
    gt = load_ground_truth()
    models = ["yolov8n.pt", "yolov8s.pt", "yolo11n.pt"]
    resolutions = [640, 960, 1280]
    confs = [0.10, 0.15, 0.25, 0.35]
    
    all_runs = []
    
    for m_name in models:
        print(f"\n==================== Loading Model: {m_name} ====================")
        m = YOLO(m_name)
        for imgsz in resolutions:
            for conf in confs:
                res = evaluate_run(
                    model=m,
                    model_name=m_name,
                    imgsz=imgsz,
                    conf=conf,
                    nms_iou=0.45,
                    max_det=300,
                    gt_by_frame=gt,
                )
                all_runs.append(res)
                print(f"[{m_name} imgsz={imgsz} conf={conf}] Rec@0.3={res['rec30']}% (R4: {res['row_recall_30']['r4']}, <45px: {res['height_recall_30']['<45px']}) | Prec@0.3={res['prec30']}% | Dups={res['duplicates']} | Lat={res['med_latency_ms']}ms ({res['fps']} FPS)")

    with open("docs/stage1b_grid_results.json", "w", encoding="utf-8") as f:
        json.dump(all_runs, f, indent=2)
    print("\n[VERIFIED] Successfully saved stage1b_grid_results.json")

if __name__ == "__main__":
    main()

