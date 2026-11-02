"""
scripts/test_phone_association_unit.py
Unit tests for phone association rule:
1. Synthetic normalized coordinates [0-100] (legacy fixture compatibility)
2. Real-world raw pixel coordinates (640x480 frame, phone in hand at chest)
3. Wrist proximity matching (phone held in hand near right wrist)
4. Negative control: phone far away (not associated with person)
"""

import sys
sys.path.insert(0, ".")

from backend.app.schemas.detections import BoundingBox, Keypoint
from backend.app.services.activity_recognition.service import ActivityRecognitionService, ActivityLabel

svc = ActivityRecognitionService()

# 1. Synthetic percentage test
box_pct = BoundingBox(
    id="anon_001", personId=1, classId=1, className="hand_not_raised",
    confidence=0.85, x=15.0, y=15.0, w=30.0, h=60.0
)
phone_pct = {"bbox": [20.0, 30.0, 26.0, 42.0], "confidence": 0.75}

# 2. Real-world pixel coordinates on 640x480 frame
# Person: x=100, y=80, w=200, h=350 (normalized: x=15.6%, y=16.7%, w=31.2%, h=72.9%)
# Phone: x=180, y=200, w=50, h=90 (in chest region)
kps = [
    Keypoint(name="right_wrist", x=210.0, y=240.0, confidence=0.88),
    Keypoint(name="left_wrist", x=120.0, y=360.0, confidence=0.75),
]
box_px = BoundingBox(
    id="anon_002", personId=2, classId=1, className="hand_not_raised",
    confidence=0.90,
    x=15.62, y=16.67, w=31.25, h=72.92,
    width=200.0, height=350.0,
    keypoints=kps
)
phone_px = {
    "bbox": [180.0, 200.0, 230.0, 290.0],
    "bbox_normalized": [28.12, 41.67, 35.94, 60.42],
    "confidence": 0.82
}

# 3. Negative control: phone far away on background wall/table
phone_far = {
    "bbox": [550.0, 400.0, 600.0, 460.0],
    "bbox_normalized": [85.94, 83.33, 93.75, 95.83],
    "confidence": 0.80
}

print("Running Unit Tests for Phone Association...")

# Test 1: Synthetic
m1 = svc._associate_phones_to_persons([box_pct], [phone_pct])
print("Test 1 (Synthetic):", m1)

# Test 2: Pixel + Normalized
m2 = svc._associate_phones_to_persons([box_px], [phone_px])
print("Test 2 (Pixel + Wrist):", m2)

# Test 3: Negative Control
m3 = svc._associate_phones_to_persons([box_px], [phone_far])
print("Test 3 (Negative Control):", m3)
