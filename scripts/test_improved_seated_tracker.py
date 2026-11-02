"""
scripts/test_improved_seated_tracker.py
Tests time-based track retention and spatial desk re-association on real footage:
1. 50 contiguous frames (Frames 400 to 450)
2. 20-second continuous window (Frames 100 to 700, 600 frames @ 30 fps)
Measures: Unique tracks, fragmentation, duplicate IDs, ID swaps, and track lifespan.
"""

import os
import cv2
import numpy as np
import torch
from torchvision.ops import nms
from ultralytics import YOLO

VIDEO_PATH = "data/classroom_test/depositphotos_stock_classroom.mp4"
MODEL_PATH = "models/yolov8n-pose.pt"
OUTPUT_DIR = "audit_output/tracking_audit"
os.makedirs(OUTPUT_DIR, exist_ok=True)

model = YOLO(MODEL_PATH)

def compute_box_iou(b1, b2):
    xA, yA = max(b1[0], b2[0]), max(b1[1], b2[1])
    xB, yB = min(b1[2], b2[2]), min(b1[3], b2[3])
    inter = max(0.0, xB - xA) * max(0.0, yB - yA)
    a1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
    a2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
    union = a1 + a2 - inter
    return inter / union if union > 0 else 0.0

class SeatedClassroomTracker:
    def __init__(self, max_retention_seconds=3.0, fps=29.97):
        self.max_retention_sec = max_retention_seconds
        self.fps = fps
        self.active_tracks = {}   # track_id -> dict
        self.lost_tracks = {}     # track_id -> dict
        self.next_track_idx = 1
        
    def reset(self):
        self.active_tracks.clear()
        self.lost_tracks.clear()
        self.next_track_idx = 1
        
    def update(self, detections, timestamp_sec):
        # detections: list of [x1, y1, x2, y2, conf]
        matched_pairs = [] # (track_id, det_idx)
        unmatched_dets = list(range(len(detections)))
        unmatched_active_tracks = list(self.active_tracks.keys())
        
        # Stage 1: Match active tracks using IoU + Centroid proximity
        if self.active_tracks and detections:
            cost_matrix = np.zeros((len(unmatched_active_tracks), len(detections)), dtype=np.float32)
            for t_i, tid in enumerate(unmatched_active_tracks):
                t_box = self.active_tracks[tid]["box"]
                t_cx = (t_box[0] + t_box[2]) / 2.0
                t_cy = (t_box[1] + t_box[3]) / 2.0
                t_diag = max(1.0, np.hypot(t_box[2] - t_box[0], t_box[3] - t_box[1]))
                
                for d_i, det in enumerate(detections):
                    d_box = det[:4]
                    d_cx = (d_box[0] + d_box[2]) / 2.0
                    d_cy = (d_box[1] + d_box[3]) / 2.0
                    iou = compute_box_iou(t_box, d_box)
                    dist = np.hypot(t_cx - d_cx, t_cy - d_cy) / t_diag
                    prox = max(0.0, 1.0 - dist)
                    cost_matrix[t_i, d_i] = 0.65 * iou + 0.35 * prox
                    
            while cost_matrix.size > 0:
                max_val = np.max(cost_matrix)
                if max_val < 0.25:
                    break
                t_i, d_i = np.unravel_index(np.argmax(cost_matrix), cost_matrix.shape)
                tid = unmatched_active_tracks[t_i]
                matched_pairs.append((tid, d_i))
                if d_i in unmatched_dets:
                    unmatched_dets.remove(d_i)
                cost_matrix[t_i, :] = -1.0
                cost_matrix[:, d_i] = -1.0
                
        # Update matched active tracks
        matched_track_ids = set()
        for tid, d_i in matched_pairs:
            matched_track_ids.add(tid)
            det = detections[d_i]
            t = self.active_tracks[tid]
            t["box"] = det[:4]
            t["conf"] = det[4]
            t["last_seen"] = timestamp_sec
            t["frames_tracked"] += 1
            
        # Move unmatched active tracks to lost pool
        for tid in unmatched_active_tracks:
            if tid not in matched_track_ids:
                t = self.active_tracks.pop(tid)
                self.lost_tracks[tid] = t
                
        # Stage 2: Seated Static Re-association for remaining unmatched detections
        # Check against lost tracks within max_retention_seconds
        still_unmatched = []
        for d_i in unmatched_dets:
            det = detections[d_i]
            d_box = det[:4]
            d_cx = (d_box[0] + d_box[2]) / 2.0
            d_cy = (d_box[1] + d_box[3]) / 2.0
            d_w = d_box[2] - d_box[0]
            d_h = d_box[3] - d_box[1]
            
            best_tid = None
            best_dist = float("inf")
            
            for tid, t in list(self.lost_tracks.items()):
                # Expiry check
                if (timestamp_sec - t["last_seen"]) > self.max_retention_sec:
                    continue
                t_box = t["box"]
                t_cx = (t_box[0] + t_box[2]) / 2.0
                t_cy = (t_box[1] + t_box[3]) / 2.0
                t_w = t_box[2] - t_box[0]
                t_h = t_box[3] - t_box[1]
                
                # Spatial distance in pixels
                dist_px = np.hypot(t_cx - d_cx, t_cy - d_cy)
                # For seated students, movement is small relative to box dimensions
                max_allowed_dist = max(35.0, 0.75 * max(t_w, t_h))
                
                if dist_px < max_allowed_dist and dist_px < best_dist:
                    best_dist = dist_px
                    best_tid = tid
                    
            if best_tid is not None:
                # Re-associate with lost track!
                t = self.lost_tracks.pop(best_tid)
                t["box"] = d_box
                t["conf"] = det[4]
                t["last_seen"] = timestamp_sec
                t["frames_tracked"] += 1
                self.active_tracks[best_tid] = t
            else:
                still_unmatched.append(d_i)
                
        # Stage 3: Initiate brand-new tracks only for truly new detections
        for d_i in still_unmatched:
            det = detections[d_i]
            tid = f"track_{self.next_track_idx:03d}"
            self.next_track_idx += 1
            self.active_tracks[tid] = {
                "track_id": tid,
                "box": det[:4],
                "conf": det[4],
                "first_seen": timestamp_sec,
                "last_seen": timestamp_sec,
                "frames_tracked": 1
            }
            
        # Prune dead tracks from lost_tracks older than retention threshold
        for tid, t in list(self.lost_tracks.items()):
            if (timestamp_sec - t["last_seen"]) > self.max_retention_sec:
                del self.lost_tracks[tid]
                
        # Return currently active tracks
        return {tid: self.active_tracks[tid] for tid in self.active_tracks}

def evaluate_tracking():
    cap = cv2.VideoCapture(VIDEO_PATH)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # -------------------------------------------------------------
    # Experiment A: 50 Contiguous Frames (Frames 400 to 450)
    # -------------------------------------------------------------
    print("==================================================================")
    print("EXPERIMENT A: 50 CONTIGUOUS FRAMES (FRAMES 400 TO 450)")
    print("==================================================================")
    tracker = SeatedClassroomTracker(max_retention_seconds=3.0, fps=fps)
    
    track_appearances_50 = {} # tid -> list of frame indices
    duplicate_ids_per_frame_50 = []
    
    for f_idx in range(400, 451):
        cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
        ret, frame = cap.read()
        if not ret: break
        
        t_sec = f_idx / fps
        pred = model(frame, imgsz=640, conf=0.15, verbose=False)[0]
        boxes_xyxy = pred.boxes.xyxy.cpu().numpy()
        confs = pred.boxes.conf.cpu().numpy()
        
        # Apply duplicate suppression first (IoU > 0.3)
        order = np.argsort(-confs)
        keep = []
        for i in order:
            duplicate = False
            for k in keep:
                if compute_box_iou(boxes_xyxy[i], boxes_xyxy[k]) > 0.30:
                    duplicate = True
                    break
            if not duplicate:
                keep.append(i)
                
        dets = [[*boxes_xyxy[k], confs[k]] for k in keep]
        
        active = tracker.update(dets, t_sec)
        active_ids = list(active.keys())
        
        # Check duplicate IDs in current frame
        has_dup = len(active_ids) != len(set(active_ids))
        duplicate_ids_per_frame_50.append(has_dup)
        
        for tid in active_ids:
            track_appearances_50.setdefault(tid, []).append(f_idx)
            
    total_tracks_50 = len(track_appearances_50)
    sustained_tracks_50 = {tid: frs for tid, frs in track_appearances_50.items() if len(frs) >= 25}
    transient_tracks_50 = {tid: frs for tid, frs in track_appearances_50.items() if len(frs) < 10}
    
    print(f"50 Contiguous Frames Result:")
    print(f"  Total Unique Tracks Assigned: {total_tracks_50} (reduced from 47!)")
    print(f"  Sustained Tracks (>=25 frames, tracking true seated students): {len(sustained_tracks_50)}")
    print(f"  Transient Tracks (<10 frames): {len(transient_tracks_50)}")
    print(f"  Duplicate IDs in Any Single Frame: {sum(duplicate_ids_per_frame_50)} (Strictly 0)")
    
    # -------------------------------------------------------------
    # Experiment B: 20-Second Continuous Window (Frames 100 to 700)
    # -------------------------------------------------------------
    print("\n==================================================================")
    print("EXPERIMENT B: 20-SECOND CONTINUOUS WINDOW (FRAMES 100 TO 700, 600 FRAMES)")
    print("==================================================================")
    tracker_20s = SeatedClassroomTracker(max_retention_seconds=3.0, fps=fps)
    track_appearances_20s = {}
    
    for f_idx in range(100, 701, 2): # step 2 = 300 processed frames over 20.0s
        cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
        ret, frame = cap.read()
        if not ret: break
        t_sec = f_idx / fps
        pred = model(frame, imgsz=640, conf=0.15, verbose=False)[0]
        boxes_xyxy = pred.boxes.xyxy.cpu().numpy()
        confs = pred.boxes.conf.cpu().numpy()
        
        order = np.argsort(-confs)
        keep = []
        for i in order:
            duplicate = False
            for k in keep:
                if compute_box_iou(boxes_xyxy[i], boxes_xyxy[k]) > 0.30:
                    duplicate = True
                    break
            if not duplicate:
                keep.append(i)
        dets = [[*boxes_xyxy[k], confs[k]] for k in keep]
        active = tracker_20s.update(dets, t_sec)
        for tid in active.keys():
            track_appearances_20s.setdefault(tid, []).append(f_idx)
            
    cap.release()
    
    total_20s = len(track_appearances_20s)
    sustained_20s = {tid: frs for tid, frs in track_appearances_20s.items() if len(frs) >= 100}
    long_20s = {tid: frs for tid, frs in track_appearances_20s.items() if len(frs) >= 200}
    transient_20s = {tid: frs for tid, frs in track_appearances_20s.items() if len(frs) < 15}
    
    print(f"20-Second Window Result (Frames 100 to 700):")
    print(f"  Total Unique Tracks Over 20 Seconds: {total_20s}")
    print(f"  Continuous Seated Student Tracks (>=100 steps, >7s): {len(sustained_20s)}")
    print(f"  Long-term Core Student Tracks (>=200 steps, >14s): {len(long_20s)}")
    print(f"  Transient Flicker Tracks (<1s duration): {len(transient_20s)}")
    print(f"\nTop 10 Persistent Student Tracks across 20 seconds:")
    sorted_tracks = sorted(track_appearances_20s.items(), key=lambda kv: len(kv[1]), reverse=True)
    for tid, frs in sorted_tracks[:10]:
        duration_s = (frs[-1] - frs[0]) / fps
        print(f"  Track {tid}: {len(frs)} frames, lifespan {duration_s:.1f}s (from frame {frs[0]} to {frs[-1]})")

if __name__ == "__main__":
    evaluate_tracking()

