"""
verify_phase_c_detection.py
Rigorous verification of Phase C according to exact evaluation rules:
1. Calls live FastAPI /api/vision/video/process with conf=0.20 and conf=0.15 (detect_pose=True).
2. Verifies actual API response fields (timeline, timestampSeconds, boxes, keypoints, etc.).
3. Evaluates detection counts against human-verified headcounts on the 10 diagnostic frames.
4. Reports detection counts and raw predictions. Does NOT fabricate precision/recall/F1 without manual ground-truth bounding boxes.
5. Inspects track ID persistence across timeline frames. Reports temporal IoU as UNAVAILABLE without ground-truth trajectory annotations.
"""

import os
import json
import time
import requests

VIDEO_PATH = r"data\classroom_test\ClassVision_Sample_Classroom_Test_Compatible.mp4"
API_URL = "http://127.0.0.1:8000/api/vision/video/process"
OUTPUT_JSON = r"audit_output\phase_c_verified_metrics.json"

DIAGNOSTIC_FRAMES = [10, 35, 60, 85, 110, 135, 160, 185, 210, 235]
FPS = 20.0
DIAGNOSTIC_TIMESTAMPS = [round(f / FPS, 2) for f in DIAGNOSTIC_FRAMES]
HUMAN_VERIFIED_STUDENT_COUNT = 7  # 7 visible students seated in this classroom view

def run_api_video_process(conf: float, detect_pose: bool = True):
    print(f"\n[API TEST] Calling {API_URL} (conf={conf:.2f}, detect_pose={detect_pose})...")
    t0 = time.time()
    with open(VIDEO_PATH, "rb") as f:
        files = {"file": (os.path.basename(VIDEO_PATH), f, "video/mp4")}
        data = {
            "frame_skip": 5,
            "confidence_threshold": conf,
            "imgsz": 640,
            "detect_pose": str(detect_pose).lower(),
            "apply_zone_filter": "false",
        }
        resp = requests.post(API_URL, files=files, data=data, timeout=180)
    elapsed = time.time() - t0
    print(f"[API TEST] HTTP {resp.status_code} in {elapsed:.2f}s")
    if resp.status_code != 200:
        print(f"Error: {resp.text[:500]}")
        resp.raise_for_status()
    return resp.json(), elapsed

def evaluate_run(payload, conf_value):
    timeline = payload.get("timeline", [])
    total_frames = payload.get("totalFrames", 0)
    processed_frames = payload.get("processedFrames", 0)
    avg_persons = payload.get("avgPersonsPerFrame", 0.0)
    max_persons = payload.get("maxPersonsInFrame", 0)

    print(f"--- Payload Summary for conf={conf_value:.2f} ---")
    print(f"Total Frames: {total_frames}, Processed Frames: {processed_frames}")
    print(f"Avg Persons: {avg_persons}, Max Persons: {max_persons}")
    print(f"Timeline Length: {len(timeline)}")

    diagnostic_evaluations = []
    
    for d_frame, d_time in zip(DIAGNOSTIC_FRAMES, DIAGNOSTIC_TIMESTAMPS):
        # Match using actual schema field timestampSeconds
        best_frame = None
        min_dt = float("inf")
        for fr in timeline:
            ts = fr.get("timestampSeconds", -1.0)
            dt = abs(ts - d_time)
            if dt < min_dt:
                min_dt = dt
                best_frame = fr

        boxes = best_frame.get("boxes", []) if best_frame else []
        detected_count = len(boxes)
        
        # Check keypoints attachment
        keypoint_counts = [len(b.get("keypoints") or []) for b in boxes]
        all_17 = all(k == 17 for k in keypoint_counts) if boxes else True
        
        # Check teacher zone classification if any
        teacher_count = sum(1 for b in boxes if b.get("zoneClassification") == "INSTRUCTOR_ZONE")
        student_count = detected_count - teacher_count
        
        diagnostic_evaluations.append({
            "diagnostic_frame_index": d_frame,
            "target_timestamp_sec": d_time,
            "matched_timestamp_sec": best_frame.get("timestampSeconds") if best_frame else None,
            "time_delta_sec": round(min_dt, 3),
            "human_verified_student_count": HUMAN_VERIFIED_STUDENT_COUNT,
            "total_detected_count": detected_count,
            "student_detected_count": student_count,
            "instructor_detected_count": teacher_count,
            "all_boxes_have_17_keypoints": all_17,
            "keypoint_counts": keypoint_counts,
            "detected_boxes": [
                {
                    "id": b.get("id"),
                    "confidence": round(b.get("confidence", 0.0), 3),
                    "x_pct": b.get("x"),
                    "y_pct": b.get("y"),
                    "w_pct": b.get("w"),
                    "h_pct": b.get("h"),
                    "handRaised": b.get("handRaised"),
                    "status": b.get("status"),
                    "activityLabel": b.get("activityLabel"),
                }
                for b in boxes
            ],
        })

    # Track ID continuity analysis across timeline
    all_seen_ids = set()
    frame_ids = []
    for fr in timeline:
        ids_in_fr = set(b.get("id") for b in fr.get("boxes", []) if b.get("id"))
        frame_ids.append(ids_in_fr)
        all_seen_ids.update(ids_in_fr)

    id_occurrences = {tid: sum(1 for f_set in frame_ids if tid in f_set) for tid in all_seen_ids}

    return {
        "confidence_threshold": conf_value,
        "processed_frames": processed_frames,
        "avg_persons_per_frame": avg_persons,
        "max_persons_in_frame": max_persons,
        "precision_recall_f1_note": "UNAVAILABLE: Ground-truth bounding box coordinate annotations are not present in this dataset. Per Phase C guidelines, metrics are not fabricated from heuristics.",
        "temporal_tracking_iou_note": "UNAVAILABLE: Ground-truth identity trajectories are not available in dataset. Heuristic adjacent overlap is omitted.",
        "track_id_continuity": {
            "unique_ids_detected": len(all_seen_ids),
            "id_frame_counts": id_occurrences,
        },
        "diagnostic_frames": diagnostic_evaluations,
    }

def main():
    print("=====================================================================")
    print("PHASE C: RIGOROUS EMPIRICAL VERIFICATION (ACCURATE API SCHEMA)")
    print("=====================================================================")
    
    # 1. Run inference at default conf=0.20
    payload_20, time_20 = run_api_video_process(0.20, detect_pose=True)
    summary_20 = evaluate_run(payload_20, 0.20)
    summary_20["api_wall_time_seconds"] = round(time_20, 2)
    
    # 2. Run inference at conf=0.15
    payload_15, time_15 = run_api_video_process(0.15, detect_pose=True)
    summary_15 = evaluate_run(payload_15, 0.15)
    summary_15["api_wall_time_seconds"] = round(time_15, 2)

    # Sample box verification
    sample_box = None
    if payload_20.get("timeline"):
        for fr in payload_20["timeline"]:
            if fr.get("boxes"):
                sample_box = fr["boxes"][0]
                break

    output_data = {
        "video": VIDEO_PATH,
        "model": "yolov8n-pose.pt",
        "human_verified_seated_students": HUMAN_VERIFIED_STUDENT_COUNT,
        "api_schema_verification": {
            "endpoint": API_URL,
            "timestamp_field": "timestampSeconds",
            "boxes_field": "boxes",
            "keypoints_attached": bool(sample_box and sample_box.get("keypoints")),
            "keypoints_count": len(sample_box.get("keypoints", [])) if sample_box and sample_box.get("keypoints") else 0,
            "sample_box_fields": list(sample_box.keys()) if sample_box else [],
        },
        "conf_0_20": summary_20,
        "conf_0_15": summary_15,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nWrote verified results to {OUTPUT_JSON}")
    print("\n================== DIAGNOSTIC DETECTION COUNTS ==================")
    print(f"{'Frame':<8}{'Time(s)':<10}{'Human Truth':<14}{'Conf=0.20':<12}{'Conf=0.15':<12}{'17 Kpts?':<10}")
    print("-" * 66)
    for d20, d15 in zip(summary_20["diagnostic_frames"], summary_15["diagnostic_frames"]):
        print(f"{d20['diagnostic_frame_index']:<8}{d20['target_timestamp_sec']:<10.2f}{d20['human_verified_student_count']:<14}{d20['total_detected_count']:<12}{d15['total_detected_count']:<12}{str(d20['all_boxes_have_17_keypoints']):<10}")
    print("=================================================================")
    print(f"Conf=0.20: Avg={summary_20['avg_persons_per_frame']:.2f}/fr, Max={summary_20['max_persons_in_frame']}, Time={summary_20['api_wall_time_seconds']}s")
    print(f"Conf=0.15: Avg={summary_15['avg_persons_per_frame']:.2f}/fr, Max={summary_15['max_persons_in_frame']}, Time={summary_15['api_wall_time_seconds']}s")
    print("Precision/Recall/F1: Reported as UNAVAILABLE (no manual ground-truth bounding-box annotations).")
    print("Tracking IoU: Reported as UNAVAILABLE (no ground-truth trajectory annotations).")

if __name__ == "__main__":
    main()
