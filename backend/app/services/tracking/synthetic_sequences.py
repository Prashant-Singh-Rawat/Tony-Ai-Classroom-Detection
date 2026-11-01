"""
backend/app/services/tracking/synthetic_sequences.py — Synthetic Temporal Sequences (Phase 2.2)
================================================================================================
Programmatic generation of ground-truth annotated temporal frame sequences for:
- One person raising left hand
- One person raising right hand
- One person raising both hands
- Multiple people with simultaneous and staggered hand raises
- Hand lowering
- Temporary occlusion and missed detection bridging
- Missing / low-confidence keypoints -> NEEDS_REVIEW
- Repeated hand raises separated by cooldown periods
Strictly 0% real classroom footage.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
from backend.app.schemas.detections import (
    ArmPostureGeometry,
    PersonDetection,
    PersonPoseDetection,
    PoseGeometry,
    PoseKeypoint,
)
from backend.app.schemas.tracking import HandRaisingState, HandSide


COCO_NAMES = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
]


def make_synthetic_pose_frame(
    person_id: str,
    cx: float = 320.0,
    cy: float = 240.0,
    left_hand_raised: bool = False,
    right_hand_raised: bool = False,
    left_hand_raising: bool = False,
    right_hand_raising: bool = False,
    confidence: float = 0.90,
    wrist_conf: float = 0.90,
    omit_keypoints: bool = False,
) -> PersonPoseDetection:
    """Builds a single synthetic PersonPoseDetection with exact geometry."""
    w, h = 120.0, 180.0
    x1, y1 = cx - w / 2.0, cy - h / 2.0
    x2, y2 = cx + w / 2.0, cy + h / 2.0

    bbox = PersonDetection(
        id=person_id,
        className="person",
        confidence=confidence,
        x=round(x1, 1),
        y=round(y1, 1),
        width=round(w, 1),
        height=round(h, 1),
        x1=round(x1, 1),
        y1=round(y1, 1),
        x2=round(x2, 1),
        y2=round(y2, 1),
    )

    if omit_keypoints:
        geom = PoseGeometry(
            leftArm=ArmPostureGeometry(elbowAngleDeg=None, elevationPx=None, wristAboveShoulder=False, armRaised=False, confidence=0.0),
            rightArm=ArmPostureGeometry(elbowAngleDeg=None, elevationPx=None, wristAboveShoulder=False, armRaised=False, confidence=0.0),
            shoulderDistancePx=None,
            upperBodyVisible=False,
            occludedKeypoints=COCO_NAMES,
        )
        return PersonPoseDetection(
            id=person_id,
            confidence=confidence,
            bbox=bbox,
            keypoints=[],
            geometry=geom,
        )

    # Keypoint positions
    sh_y = cy - 40.0
    ls_x, rs_x = cx - 35.0, cx + 35.0

    # Left arm elevation
    if left_hand_raised:
        lw_y = sh_y - 30.0  # Above shoulder by 30px
        le_y = sh_y - 10.0
        le_angle = 120.0
        l_elev = 30.0
    elif left_hand_raising:
        lw_y = sh_y - 5.0   # In transition zone
        le_y = sh_y + 10.0
        le_angle = 90.0
        l_elev = 5.0
    else:
        lw_y = sh_y + 45.0  # Below shoulder
        le_y = sh_y + 20.0
        le_angle = 75.0
        l_elev = -45.0

    # Right arm elevation
    if right_hand_raised:
        rw_y = sh_y - 30.0
        re_y = sh_y - 10.0
        re_angle = 120.0
        r_elev = 30.0
    elif right_hand_raising:
        rw_y = sh_y - 5.0
        re_y = sh_y + 10.0
        re_angle = 90.0
        r_elev = 5.0
    else:
        rw_y = sh_y + 45.0
        re_y = sh_y + 20.0
        re_angle = 75.0
        r_elev = -45.0

    kps: List[PoseKeypoint] = [
        PoseKeypoint(index=0, name="nose", x=cx, y=cy - 70.0, confidence=confidence, visible=True),
        PoseKeypoint(index=1, name="left_eye", x=cx - 10.0, y=cy - 75.0, confidence=confidence, visible=True),
        PoseKeypoint(index=2, name="right_eye", x=cx + 10.0, y=cy - 75.0, confidence=confidence, visible=True),
        PoseKeypoint(index=3, name="left_ear", x=cx - 20.0, y=cy - 70.0, confidence=confidence, visible=True),
        PoseKeypoint(index=4, name="right_ear", x=cx + 20.0, y=cy - 70.0, confidence=confidence, visible=True),
        PoseKeypoint(index=5, name="left_shoulder", x=ls_x, y=sh_y, confidence=confidence, visible=True),
        PoseKeypoint(index=6, name="right_shoulder", x=rs_x, y=sh_y, confidence=confidence, visible=True),
        PoseKeypoint(index=7, name="left_elbow", x=ls_x - 15.0, y=le_y, confidence=confidence, visible=True),
        PoseKeypoint(index=8, name="right_elbow", x=rs_x + 15.0, y=re_y, confidence=confidence, visible=True),
        PoseKeypoint(index=9, name="left_wrist", x=ls_x - 20.0, y=lw_y, confidence=wrist_conf, visible=True),
        PoseKeypoint(index=10, name="right_wrist", x=rs_x + 20.0, y=rw_y, confidence=wrist_conf, visible=True),
        PoseKeypoint(index=11, name="left_hip", x=cx - 25.0, y=cy + 40.0, confidence=confidence, visible=True),
        PoseKeypoint(index=12, name="right_hip", x=cx + 25.0, y=cy + 40.0, confidence=confidence, visible=True),
        PoseKeypoint(index=13, name="left_knee", x=cx - 25.0, y=cy + 80.0, confidence=confidence, visible=True),
        PoseKeypoint(index=14, name="right_knee", x=cx + 25.0, y=cy + 80.0, confidence=confidence, visible=True),
        PoseKeypoint(index=15, name="left_ankle", x=cx - 25.0, y=cy + 120.0, confidence=confidence, visible=True),
        PoseKeypoint(index=16, name="right_ankle", x=cx + 25.0, y=cy + 120.0, confidence=confidence, visible=True),
    ]

    geom = PoseGeometry(
        leftArm=ArmPostureGeometry(
            elbowAngleDeg=le_angle,
            elevationPx=l_elev,
            wristAboveShoulder=(l_elev > 0.0),
            armRaised=left_hand_raised,
            confidence=round((confidence + wrist_conf) / 2.0, 3),
        ),
        rightArm=ArmPostureGeometry(
            elbowAngleDeg=re_angle,
            elevationPx=r_elev,
            wristAboveShoulder=(r_elev > 0.0),
            armRaised=right_hand_raised,
            confidence=round((confidence + wrist_conf) / 2.0, 3),
        ),
        shoulderDistancePx=70.0,
        upperBodyVisible=True,
        occludedKeypoints=[],
    )

    return PersonPoseDetection(
        id=person_id,
        confidence=confidence,
        bbox=bbox,
        keypoints=kps,
        geometry=geom,
    )


def generate_single_person_sequence(
    num_frames: int = 20,
    hand_to_raise: str = "LEFT",  # "LEFT" | "RIGHT" | "BOTH"
    raise_start_frame: int = 5,
    raise_end_frame: int = 15,
) -> List[List[PersonPoseDetection]]:
    """Generates a sequence where a person starts seated, raises hand, and lowers it."""
    frames: List[List[PersonPoseDetection]] = []
    for f in range(num_frames):
        if f < raise_start_frame:
            # NOT_RAISED
            det = make_synthetic_pose_frame("anon_001", 320.0, 240.0)
        elif raise_start_frame <= f < (raise_start_frame + 2):
            # RAISING
            l_rg = (hand_to_raise in ("LEFT", "BOTH"))
            r_rg = (hand_to_raise in ("RIGHT", "BOTH"))
            det = make_synthetic_pose_frame("anon_001", 320.0, 240.0, left_hand_raising=l_rg, right_hand_raising=r_rg)
        elif (raise_start_frame + 2) <= f <= raise_end_frame:
            # RAISED
            l_rd = (hand_to_raise in ("LEFT", "BOTH"))
            r_rd = (hand_to_raise in ("RIGHT", "BOTH"))
            det = make_synthetic_pose_frame("anon_001", 320.0, 240.0, left_hand_raised=l_rd, right_hand_raised=r_rd)
        elif raise_end_frame < f <= (raise_end_frame + 2):
            # LOWERING
            l_rg = (hand_to_raise in ("LEFT", "BOTH"))
            r_rg = (hand_to_raise in ("RIGHT", "BOTH"))
            det = make_synthetic_pose_frame("anon_001", 320.0, 240.0, left_hand_raising=l_rg, right_hand_raising=r_rg)
        else:
            # NOT_RAISED
            det = make_synthetic_pose_frame("anon_001", 320.0, 240.0)
        frames.append([det])
    return frames


def generate_multi_person_staggered_sequence(
    num_frames: int = 30,
) -> List[List[PersonPoseDetection]]:
    """Two people at distinct desk positions raising hands at staggered times."""
    frames: List[List[PersonPoseDetection]] = []
    for f in range(num_frames):
        p1_raised = (6 <= f <= 16)
        p1_raising = (4 <= f < 6)
        p2_raised = (14 <= f <= 24)
        p2_raising = (12 <= f < 14)

        det1 = make_synthetic_pose_frame(
            "anon_001",
            cx=180.0,
            cy=240.0,
            left_hand_raised=p1_raised,
            left_hand_raising=p1_raising,
        )
        det2 = make_synthetic_pose_frame(
            "anon_002",
            cx=460.0,
            cy=240.0,
            right_hand_raised=p2_raised,
            right_hand_raising=p2_raising,
        )
        frames.append([det1, det2])
    return frames


def generate_temporary_occlusion_sequence(
    num_frames: int = 20,
    occlusion_frames: Tuple[int, int] = (9, 11),  # frames 9-11 missing
) -> List[List[PersonPoseDetection]]:
    """Person raises hand, drops out of frame for 2 frames, returns still raised."""
    frames: List[List[PersonPoseDetection]] = []
    for f in range(num_frames):
        if occlusion_frames[0] <= f <= occlusion_frames[1]:
            # Occluded (no detections in frame)
            frames.append([])
            continue

        raised = (5 <= f <= 16)
        raising = (3 <= f < 5)
        det = make_synthetic_pose_frame(
            "anon_001",
            cx=320.0,
            cy=240.0,
            left_hand_raised=raised,
            left_hand_raising=raising,
        )
        frames.append([det])
    return frames


def generate_noisy_keypoint_sequence(
    num_frames: int = 15,
) -> List[List[PersonPoseDetection]]:
    """Wrist confidence is low (0.20), triggering NEEDS_REVIEW instead of false raise."""
    frames: List[List[PersonPoseDetection]] = []
    for f in range(num_frames):
        det = make_synthetic_pose_frame(
            "anon_001",
            cx=320.0,
            cy=240.0,
            left_hand_raised=(f >= 4),
            wrist_conf=0.22,  # Sub-threshold noisy confidence
        )
        frames.append([det])
    return frames


def generate_repeated_raise_cooldown_sequence(
    num_frames: int = 35,
) -> List[List[PersonPoseDetection]]:
    """Two raises separated by a short cooldown."""
    frames: List[List[PersonPoseDetection]] = []
    for f in range(num_frames):
        # Raise 1: frames 4-10
        # Lowered: frames 11-13
        # Jitter at frame 14 (should be suppressed by cooldown)
        # Raise 2: frames 24-30
        r1 = (4 <= f <= 10)
        r2 = (24 <= f <= 30)
        jitter = (f == 14)

        det = make_synthetic_pose_frame(
            "anon_001",
            cx=320.0,
            cy=240.0,
            left_hand_raised=(r1 or r2 or jitter),
        )
        frames.append([det])
    return frames

