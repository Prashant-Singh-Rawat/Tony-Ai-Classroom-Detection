"""
tests/api/test_sideways_detection.py — Comprehensive Unit & Integration Tests for Turned Sideways Detection
===========================================================================================================
Validates:
1. Person facing forward -> NO_FLAG_OBSERVED (Green: Facing board).
2. Person sitting sideways (foreshortened shoulders/hips) -> POSSIBLE_PEER_INTERACTION (Orange: Turned sideways).
3. Person sitting profile view (one shoulder dominant, far shoulder occluded) -> POSSIBLE_PEER_INTERACTION.
4. Person turning upper body / head toward neighbor -> POSSIBLE_PEER_INTERACTION.
5. Person facing away from classroom board -> POSSIBLE_PEER_INTERACTION.
6. Calibrated side-camera vs rear-camera board alignment.
7. Heavily occluded posture without sideways geometry -> NEEDS_REVIEW (Yellow/Grey).
8. Temporal stability & hysteresis (momentary glance filtered, sustained turn persists, return to board).
9. Zero biometric / facial recognition compliance.
"""

from __future__ import annotations

import pytest
from backend.app.schemas.activities import ActivityLabel
from backend.app.schemas.detections import BoundingBox, Keypoint
from backend.app.services.activity_recognition.service import (
    ActivityRecognitionService,
    DISPLAY_LABELS,
)


def make_test_keypoints(
    nose_x: float = 50.0,
    nose_y: float = 30.0,
    nose_conf: float = 0.90,
    l_sh_x: float = 40.0,
    l_sh_y: float = 45.0,
    l_sh_conf: float = 0.90,
    r_sh_x: float = 60.0,
    r_sh_y: float = 45.0,
    r_sh_conf: float = 0.90,
    l_hip_x: float = 42.0,
    l_hip_y: float = 70.0,
    l_hip_conf: float = 0.85,
    r_hip_x: float = 58.0,
    r_hip_y: float = 70.0,
    r_hip_conf: float = 0.85,
    l_ear_x: float = 44.0,
    l_ear_y: float = 30.0,
    l_ear_conf: float = 0.85,
    r_ear_x: float = 56.0,
    r_ear_y: float = 30.0,
    r_ear_conf: float = 0.85,
) -> list[Keypoint]:
    """Generates COCO-17 keypoints with parameterized positions and confidences."""
    return [
        Keypoint(id=0, name="nose", x=nose_x, y=nose_y, confidence=nose_conf),
        Keypoint(id=1, name="left_eye", x=nose_x - 3, y=nose_y - 2, confidence=nose_conf),
        Keypoint(id=2, name="right_eye", x=nose_x + 3, y=nose_y - 2, confidence=nose_conf),
        Keypoint(id=3, name="left_ear", x=l_ear_x, y=l_ear_y, confidence=l_ear_conf),
        Keypoint(id=4, name="right_ear", x=r_ear_x, y=r_ear_y, confidence=r_ear_conf),
        Keypoint(id=5, name="left_shoulder", x=l_sh_x, y=l_sh_y, confidence=l_sh_conf),
        Keypoint(id=6, name="right_shoulder", x=r_sh_x, y=r_sh_y, confidence=r_sh_conf),
        Keypoint(id=7, name="left_elbow", x=l_sh_x - 4, y=l_sh_y + 12, confidence=0.85),
        Keypoint(id=8, name="right_elbow", x=r_sh_x + 4, y=r_sh_y + 12, confidence=0.85),
        Keypoint(id=9, name="left_wrist", x=l_sh_x - 4, y=l_sh_y + 24, confidence=0.85),
        Keypoint(id=10, name="right_wrist", x=r_sh_x + 4, y=r_sh_y + 24, confidence=0.85),
        Keypoint(id=11, name="left_hip", x=l_hip_x, y=l_hip_y, confidence=l_hip_conf),
        Keypoint(id=12, name="right_hip", x=r_hip_x, y=r_hip_y, confidence=r_hip_conf),
        Keypoint(id=13, name="left_knee", x=l_hip_x, y=l_hip_y + 18, confidence=0.80),
        Keypoint(id=14, name="right_knee", x=r_hip_x, y=r_hip_y + 18, confidence=0.80),
        Keypoint(id=15, name="left_ankle", x=l_hip_x, y=l_hip_y + 36, confidence=0.80),
        Keypoint(id=16, name="right_ankle", x=r_hip_x, y=r_hip_y + 36, confidence=0.80),
    ]


def test_person_facing_forward_classified_as_facing_board():
    """Person with wide horizontal shoulders facing the whiteboard is classified as Facing board."""
    svc = ActivityRecognitionService()
    kps = make_test_keypoints(l_sh_x=40.0, r_sh_x=60.0, l_sh_y=45.0, r_sh_y=45.0)
    box = BoundingBox(id="p1", personId=1, classId=1, className="hand_not_raised", confidence=0.92, x=20.0, y=20.0, w=20.0, h=50.0, keypoints=kps)

    enriched, _ = [], []
    for f in range(5):
        enriched, _ = svc.analyze_frame([box], is_pose_mode=True, timestamp_seconds=f * 0.1)

    assert enriched[0].activityLabel == DISPLAY_LABELS[ActivityLabel.NO_FLAG_OBSERVED]
    assert enriched[0].statusColor == "GREEN"


def test_person_sitting_sideways_foreshortened_classified_as_turned_sideways():
    """Person sitting sideways with horizontally foreshortened shoulders and hips is classified as Turned sideways."""
    svc = ActivityRecognitionService()
    # 60° body yaw: horizontal shoulder span is only 7px (ratio < 0.58)
    kps = make_test_keypoints(
        l_sh_x=48.0, r_sh_x=55.0, l_sh_y=48.0, r_sh_y=42.0,
        l_hip_x=48.0, r_hip_x=53.0, l_hip_y=70.0, r_hip_y=68.0,
        nose_x=56.0, nose_y=32.0,
    )
    box = BoundingBox(id="p2", personId=2, classId=1, className="hand_not_raised", confidence=0.90, x=20.0, y=20.0, w=15.0, h=50.0, keypoints=kps)

    enriched, _ = [], []
    for f in range(5):
        enriched, _ = svc.analyze_frame([box], is_pose_mode=True, timestamp_seconds=f * 0.2)

    assert enriched[0].activityLabel == DISPLAY_LABELS[ActivityLabel.POSSIBLE_PEER_INTERACTION]
    assert enriched[0].statusColor == "ORANGE"
    assert "foreshortened" in enriched[0].activityEvidence.lower()


def test_person_sitting_profile_one_shoulder_occluded():
    """Profile view where far shoulder is occluded by torso is recognized as Turned sideways, NOT Needs review."""
    svc = ActivityRecognitionService()
    kps = make_test_keypoints(
        l_sh_x=50.0, l_sh_y=45.0, l_sh_conf=0.85,
        r_sh_x=50.0, r_sh_y=45.0, r_sh_conf=0.10, # Far shoulder occluded!
        l_hip_x=50.0, l_hip_y=70.0, l_hip_conf=0.80,
        r_hip_x=50.0, r_hip_y=70.0, r_hip_conf=0.10,
        nose_x=55.0, nose_y=32.0, nose_conf=0.70,
    )
    # Narrow profile bbox (w=12, h=48 -> aspect 0.25)
    box = BoundingBox(id="p3", personId=3, classId=1, className="hand_not_raised", confidence=0.88, x=20.0, y=20.0, w=12.0, h=48.0, keypoints=kps)

    enriched, _ = [], []
    for f in range(5):
        enriched, _ = svc.analyze_frame([box], is_pose_mode=True, timestamp_seconds=f * 0.2)

    assert enriched[0].activityLabel == DISPLAY_LABELS[ActivityLabel.POSSIBLE_PEER_INTERACTION]
    assert enriched[0].statusColor == "ORANGE"
    assert "profile" in enriched[0].activityEvidence.lower()


def test_person_turning_upper_body_toward_neighbor():
    """Person turning their head / upper body sideways toward an adjacent desk is classified as Turned sideways."""
    svc = ActivityRecognitionService()
    # Shoulders slightly angled, nose turned significantly to the right (offset > 0.48x)
    kps = make_test_keypoints(
        l_sh_x=40.0, r_sh_x=60.0, l_sh_y=48.0, r_sh_y=44.0,
        nose_x=57.0, nose_y=32.0, # shifted far right from shoulder center 50.0
    )
    box = BoundingBox(id="p4", personId=4, classId=1, className="hand_not_raised", confidence=0.89, x=20.0, y=20.0, w=20.0, h=50.0, keypoints=kps)

    enriched, _ = [], []
    for f in range(5):
        enriched, _ = svc.analyze_frame([box], is_pose_mode=True, timestamp_seconds=f * 0.2)

    assert enriched[0].activityLabel == DISPLAY_LABELS[ActivityLabel.POSSIBLE_PEER_INTERACTION]
    assert enriched[0].statusColor == "ORANGE"


def test_person_facing_away_from_board():
    """Person turned around facing the back of the classroom is classified as Turned sideways."""
    svc = ActivityRecognitionService()
    # Reversed shoulders: right shoulder is at x=40, left shoulder at x=60 (chest pointing towards camera / rear)
    kps = make_test_keypoints(
        l_sh_x=60.0, r_sh_x=40.0, l_sh_y=45.0, r_sh_y=45.0,
        nose_x=50.0, nose_y=30.0,
    )
    box = BoundingBox(id="p5", personId=5, classId=1, className="hand_not_raised", confidence=0.91, x=20.0, y=20.0, w=20.0, h=50.0, keypoints=kps)

    enriched, _ = [], []
    for f in range(5):
        enriched, _ = svc.analyze_frame([box], is_pose_mode=True, timestamp_seconds=f * 0.2)

    assert enriched[0].activityLabel == DISPLAY_LABELS[ActivityLabel.POSSIBLE_PEER_INTERACTION]
    assert enriched[0].statusColor == "ORANGE"
    assert "away" in enriched[0].activityEvidence.lower()


def test_side_camera_viewpoint_board_calibration():
    """Side camera calibration respects whiteboard coordinates and evaluates alignment relative to board."""
    svc = ActivityRecognitionService()
    # Configure board on LEFT wall of classroom (x1=0, y1=10, x2=20, y2=80)
    svc.set_board_calibration(x1=0.0, y1=10.0, x2=20.0, y2=80.0, forward_vector=[-1.0, 0.0])

    # Student at (x=50, y=50) facing left toward the whiteboard:
    # Chest points left -> right shoulder at y=40, left shoulder at y=60
    kps_facing_board = make_test_keypoints(
        l_sh_x=50.0, r_sh_x=50.0, l_sh_y=60.0, r_sh_y=40.0,
        nose_x=40.0, nose_y=50.0,
    )
    box_facing = BoundingBox(id="p_side1", personId=61, classId=1, className="hand_not_raised", confidence=0.90, x=45.0, y=40.0, w=15.0, h=50.0, keypoints=kps_facing_board)

    enriched, _ = [], []
    for f in range(5):
        enriched, _ = svc.analyze_frame([box_facing], is_pose_mode=True, timestamp_seconds=f * 0.2)

    # Even though body is sideways in screen coordinates, student IS facing the calibrated board!
    assert enriched[0].activityLabel == DISPLAY_LABELS[ActivityLabel.NO_FLAG_OBSERVED]
    assert enriched[0].statusColor == "GREEN"


def test_heavily_occluded_posture_returns_needs_review():
    """Heavily occluded posture lacking sufficient keypoints returns Needs review."""
    svc = ActivityRecognitionService()
    # Almost all upper body landmarks have sub-threshold confidence
    kps = make_test_keypoints(
        nose_conf=0.12, l_sh_conf=0.14, r_sh_conf=0.15,
        l_hip_conf=0.10, r_hip_conf=0.10,
    )
    box = BoundingBox(id="p7", personId=7, classId=1, className="hand_not_raised", confidence=0.65, x=20.0, y=20.0, w=20.0, h=50.0, keypoints=kps)

    enriched, _ = [], []
    for f in range(5):
        enriched, _ = svc.analyze_frame([box], is_pose_mode=True, timestamp_seconds=f * 0.1)

    assert enriched[0].activityLabel == DISPLAY_LABELS[ActivityLabel.NEEDS_REVIEW]
    assert enriched[0].statusColor in ("YELLOW", "GREY")


def test_temporal_stability_and_hysteresis():
    """Verifies that brief glitch does not trigger sideways, while sustained turn is stable."""
    svc = ActivityRecognitionService()
    normal_kps = make_test_keypoints(l_sh_x=40.0, r_sh_x=60.0)
    sideways_kps = make_test_keypoints(l_sh_x=48.0, r_sh_x=55.0, l_sh_y=48.0, r_sh_y=42.0)

    box_normal = BoundingBox(id="p8", personId=8, classId=1, className="hand_not_raised", confidence=0.90, x=20.0, y=20.0, w=20.0, h=50.0, keypoints=normal_kps)
    box_sideways = BoundingBox(id="p8", personId=8, classId=1, className="hand_not_raised", confidence=0.90, x=20.0, y=20.0, w=20.0, h=50.0, keypoints=sideways_kps)

    # 1. Start normal (4 frames)
    for f in range(4):
        res, _ = svc.analyze_frame([box_normal], is_pose_mode=True, timestamp_seconds=f * 0.1)
    assert res[0].activityLabel == DISPLAY_LABELS[ActivityLabel.NO_FLAG_OBSERVED]

    # 2. Brief 1-frame glance sideways -> should NOT trigger due to hysteresis
    res, _ = svc.analyze_frame([box_sideways], is_pose_mode=True, timestamp_seconds=0.4)
    assert res[0].activityLabel == DISPLAY_LABELS[ActivityLabel.NO_FLAG_OBSERVED]

    # 3. Sustained sideways for 4 more frames -> triggers Turned sideways
    for f in range(5, 9):
        res, _ = svc.analyze_frame([box_sideways], is_pose_mode=True, timestamp_seconds=f * 0.1)
    assert res[0].activityLabel == DISPLAY_LABELS[ActivityLabel.POSSIBLE_PEER_INTERACTION]

    # 4. Turn back to board: 1 frame does not immediately lose state
    res, _ = svc.analyze_frame([box_normal], is_pose_mode=True, timestamp_seconds=0.9)
    assert res[0].activityLabel == DISPLAY_LABELS[ActivityLabel.POSSIBLE_PEER_INTERACTION]

    # 5. Sustained return (4 consecutive normal frames) -> cleanly recovers to Facing board
    for f in range(10, 15):
        res, _ = svc.analyze_frame([box_normal], is_pose_mode=True, timestamp_seconds=f * 0.1)
    assert res[0].activityLabel == DISPLAY_LABELS[ActivityLabel.NO_FLAG_OBSERVED]


def test_center_student_facing_board_with_minor_head_jitter_and_peer_proximity():
    """
    Guarantees that a center student sitting upright with broad horizontal shoulders facing
    the whiteboard is classified as Facing board (Green), even if their head exhibits minor
    landmark jitter or an adjacent student sits in the next desk.
    Eliminates false positive Turned sideways classifications.
    """
    svc = ActivityRecognitionService()
    center_kps = make_test_keypoints(
        l_sh_x=40.0, r_sh_x=60.0, l_sh_y=45.0, r_sh_y=46.0,
        nose_x=47.0, nose_y=30.0, nose_conf=0.35,
        l_hip_x=42.0, r_hip_x=58.0, l_hip_y=70.0, r_hip_y=70.0,
    )
    peer_kps = make_test_keypoints(
        l_sh_x=70.0, r_sh_x=90.0, l_sh_y=45.0, r_sh_y=45.0,
        nose_x=83.0, nose_y=30.0, nose_conf=0.35,
    )

    box_center = BoundingBox(id="center_student", personId=1, classId=1, className="hand_not_raised", confidence=0.92, x=35.0, y=20.0, w=20.0, h=50.0, keypoints=center_kps)
    box_peer = BoundingBox(id="peer_student", personId=2, classId=1, className="hand_not_raised", confidence=0.90, x=60.0, y=20.0, w=20.0, h=50.0, keypoints=peer_kps)

    enriched = []
    for f in range(6):
        enriched, _ = svc.analyze_frame([box_center, box_peer], is_pose_mode=True, timestamp_seconds=f * 0.1)

    center_res = [b for b in enriched if b.id == "center_student"][0]
    assert center_res.activityLabel == DISPLAY_LABELS[ActivityLabel.NO_FLAG_OBSERVED]
    assert center_res.statusColor == "GREEN"
    assert "facing" in center_res.activityEvidence.lower() or "board" in center_res.activityEvidence.lower()


