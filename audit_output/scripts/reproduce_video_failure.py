"""
Script: audit_output/scripts/reproduce_video_failure.py
Phase A4: Reproduce video processing end-to-end and capture raw payload.
"""

import json
import os
import sys
import time
import requests

VIDEO_PATH = r"data\classroom_test\ClassVision_Sample_Classroom_Test_Compatible.mp4"
OUTPUT_PAYLOAD_PATH = r"audit_output\video_process_raw_payload.json"
API_URL = "http://127.0.0.1:8000/api/vision/video/process"

if not os.path.exists(VIDEO_PATH):
    print(f"Error: Video not found at {VIDEO_PATH}")
    sys.exit(1)

print(f"Testing video: {VIDEO_PATH}")
print(f"File size: {os.path.getsize(VIDEO_PATH)} bytes")

# Test 1: Calling backend endpoint via HTTP multipart upload (exact frontend behavior)
with open(VIDEO_PATH, "rb") as f:
    files = {"file": ("ClassVision_Sample_Classroom_Test_Compatible.mp4", f, "video/mp4")}
    data = {
        "frame_skip": 5,
        "confidence_threshold": 0.35,
        "imgsz": 640,
        "detect_pose": "false",
        "session_id": "sess_audit_a4",
        "enable_tracking": "true",
        "zone_filtering_enabled": "true",
    }
    print(f"Posting request to {API_URL} (detect_pose=false, conf=0.35)...")
    t0 = time.time()
    try:
        resp = requests.post(API_URL, files=files, data=data, timeout=60)
        elapsed = time.time() - t0
        print(f"Status Code: {resp.status_code} in {elapsed:.2f}s")
        if resp.status_code == 200:
            payload = resp.json()
            with open(OUTPUT_PAYLOAD_PATH, "w", encoding="utf-8") as out_f:
                json.dump(payload, out_f, indent=2)
            print(f"Saved raw payload to {OUTPUT_PAYLOAD_PATH}")
            
            # Summarize payload
            total_frames = payload.get("totalFrames")
            processed_frames = payload.get("processedFrames")
            max_persons = payload.get("maxPersonsInFrame")
            avg_persons = payload.get("avgPersonsPerFrame")
            timeline = payload.get("timeline", [])
            print(f"\n--- Payload Summary ---")
            print(f"Total Frames: {total_frames}")
            print(f"Processed Frames: {processed_frames}")
            print(f"Max Persons in Frame: {max_persons}")
            print(f"Avg Persons per Frame: {avg_persons}")
            
            non_empty_frames = [f for f in timeline if f.get("personCount", 0) > 0]
            print(f"Sampled frames with >= 1 detection: {len(non_empty_frames)} / {len(timeline)}")
            if non_empty_frames:
                sample_frame = non_empty_frames[0]
                print(f"Sample detection in frame {sample_frame.get('frameIndex')}:")
                print(f"  Boxes count: {len(sample_frame.get('boxes', []))}")
                for b in sample_frame.get("boxes", []):
                    print(f"    Box: id={b.get('id')}, conf={b.get('confidence')}, coords=(x={b.get('x')}%, y={b.get('y')}%, w={b.get('w')}%, h={b.get('h')}%)")
            else:
                print("  WARNING: 0 detections across all sampled frames at conf=0.35!")
        else:
            print(f"Request failed: {resp.text}")
    except Exception as e:
        print(f"Request error: {e}")

# Test 2: Also test with detect_pose=True
OUTPUT_POSE_PAYLOAD_PATH = r"audit_output\video_process_pose_raw_payload.json"
with open(VIDEO_PATH, "rb") as f:
    files = {"file": ("ClassVision_Sample_Classroom_Test_Compatible.mp4", f, "video/mp4")}
    data = {
        "frame_skip": 5,
        "confidence_threshold": 0.35,
        "imgsz": 640,
        "detect_pose": "true",
        "session_id": "sess_audit_a4_pose",
        "enable_tracking": "true",
        "zone_filtering_enabled": "true",
    }
    print(f"\nPosting request to {API_URL} (detect_pose=true, conf=0.35)...")
    t0 = time.time()
    try:
        resp = requests.post(API_URL, files=files, data=data, timeout=60)
        elapsed = time.time() - t0
        print(f"Status Code: {resp.status_code} in {elapsed:.2f}s")
        if resp.status_code == 200:
            payload = resp.json()
            with open(OUTPUT_POSE_PAYLOAD_PATH, "w", encoding="utf-8") as out_f:
                json.dump(payload, out_f, indent=2)
            print(f"Saved pose payload to {OUTPUT_POSE_PAYLOAD_PATH}")
            max_persons = payload.get("maxPersonsInFrame")
            timeline = payload.get("timeline", [])
            non_empty_frames = [f for f in timeline if f.get("personCount", 0) > 0]
            print(f"Max Persons in Frame: {max_persons}")
            print(f"Sampled frames with >= 1 detection: {len(non_empty_frames)} / {len(timeline)}")
            if non_empty_frames:
                sample_frame = non_empty_frames[0]
                for b in sample_frame.get("boxes", []):
                    print(f"    Pose Box: id={b.get('id')}, conf={b.get('confidence')}, coords=(x={b.get('x')}%, y={b.get('y')}%, w={b.get('w')}%, h={b.get('h')}%)")
    except Exception as e:
        print(f"Request error: {e}")

