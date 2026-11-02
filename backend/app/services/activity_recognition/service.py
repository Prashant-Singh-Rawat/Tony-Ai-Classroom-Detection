"""
backend/app/services/activity_recognition/service.py — Explainable Classroom Activity Recognition
================================================================================================
Phase 2.9: Temporal Activity Recognition based strictly on visible physical geometry,
body keypoints, and detected objects without subjective attention/disciplinary scoring.

Activities:
- NO_FLAG_OBSERVED (Green)
- PHONE_VISIBLE (Red)
- HEAD_DOWN_POSTURE (Red)
- POSSIBLE_PEER_INTERACTION (Orange)
- POSSIBLE_SPEAKING (Orange / Needs Review)
- LEFT_HAND_RAISED, RIGHT_HAND_RAISED, BOTH_HANDS_RAISED (Blue)
- NEEDS_REVIEW (Yellow)
"""

from __future__ import annotations

import math
import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from backend.app.schemas.activities import (
    ActivityEvidence,
    ActivityLabel,
    TrackedActivityState,
    ActivityEventSchema,
    ActivityDistributionSummary,
)
from backend.app.schemas.detections import BoundingBox, Keypoint, PersonDetection


from backend.app.core.activity_config import (
    TAG_FACING_BOARD,
    TAG_HAND_RAISED,
    TAG_HAND_RAISED_LEFT,
    TAG_HAND_RAISED_RIGHT,
    TAG_HAND_RAISED_BOTH,
    TAG_PHONE_VISIBLE,
    TAG_HEAD_DOWN,
    TAG_TURNED_SIDEWAYS,
    TAG_NEEDS_REVIEW,
    COLOR_GREEN,
    COLOR_BLUE,
    COLOR_RED,
    COLOR_ORANGE,
    COLOR_YELLOW,
    HEAD_DOWN_DURATION_THRESHOLD_SEC,
    PHONE_CONSECUTIVE_FRAMES,
    SIDEWAYS_SUSTAINED_SECONDS,
    SIDEWAYS_SUSTAINED_FRAMES,
    WHITEBOARD_DEFAULT_CALIBRATION,
)

# Observable Tag Color Mapping strictly adhering to product requirements:
# Green: Facing board
# Blue: Hand raised (Left / Right / Both)
# Red: Phone visible
# Orange: Head down (N s)
# Orange: Turned sideways (possible interaction)
# Yellow: Needs review
ACTIVITY_COLORS: Dict[ActivityLabel, str] = {
    ActivityLabel.NO_FLAG_OBSERVED: COLOR_GREEN,
    ActivityLabel.HEAD_DOWN_POSTURE: COLOR_ORANGE,
    ActivityLabel.PHONE_VISIBLE: COLOR_RED,
    ActivityLabel.POSSIBLE_PEER_INTERACTION: COLOR_ORANGE,
    ActivityLabel.POSSIBLE_SPEAKING: COLOR_ORANGE,
    ActivityLabel.HAND_RAISED: COLOR_BLUE,
    ActivityLabel.LEFT_HAND_RAISED: COLOR_BLUE,
    ActivityLabel.RIGHT_HAND_RAISED: COLOR_BLUE,
    ActivityLabel.BOTH_HANDS_RAISED: COLOR_BLUE,
    ActivityLabel.NEEDS_REVIEW: COLOR_YELLOW,
}

DISPLAY_LABELS: Dict[ActivityLabel, str] = {
    ActivityLabel.NO_FLAG_OBSERVED: TAG_FACING_BOARD,
    ActivityLabel.HEAD_DOWN_POSTURE: TAG_HEAD_DOWN,
    ActivityLabel.PHONE_VISIBLE: TAG_PHONE_VISIBLE,
    ActivityLabel.POSSIBLE_PEER_INTERACTION: TAG_TURNED_SIDEWAYS,
    ActivityLabel.POSSIBLE_SPEAKING: TAG_TURNED_SIDEWAYS,
    ActivityLabel.HAND_RAISED: TAG_HAND_RAISED,
    ActivityLabel.LEFT_HAND_RAISED: TAG_HAND_RAISED_LEFT,
    ActivityLabel.RIGHT_HAND_RAISED: TAG_HAND_RAISED_RIGHT,
    ActivityLabel.BOTH_HANDS_RAISED: TAG_HAND_RAISED_BOTH,
    ActivityLabel.NEEDS_REVIEW: TAG_NEEDS_REVIEW,
}


class TrackTemporalBuffer:
    """Rolling observation window and hysteresis tracking for a single anonymous track."""

    def __init__(self, track_id: str, window_size: int = 25) -> None:
        self.track_id = track_id
        self.window_size = window_size

        # Current stable state
        self.current_label: ActivityLabel = ActivityLabel.NO_FLAG_OBSERVED
        self.current_confidence: float = 0.85
        self.current_duration_seconds: float = 0.0
        self.state_start_time: float = time.time()
        self.state_start_frame: int = 0
        self.frames_in_state: int = 1

        # Frame observation history (candidate per frame)
        self.raw_observations: deque[Tuple[ActivityLabel, float, Dict[str, Any]]] = deque(maxlen=window_size)
        self.active_event_id: Optional[str] = None
        self.candidate_peer_start_time: Optional[float] = None


class ActivityRecognitionService:
    """
    Explainable temporal activity recognition service.
    Analyzes body keypoints, geometry, orientation, and object detections.
    """

    def __init__(
        self,
        head_down_min_duration_s: float = 1.5,
        peer_interaction_min_duration_s: float = 1.0,
        phone_min_frames: int = 2,
        keypoint_confidence_threshold: float = 0.35,
        board_calibration: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.head_down_min_duration_s = head_down_min_duration_s
        self.peer_interaction_min_duration_s = peer_interaction_min_duration_s
        self.phone_min_frames = phone_min_frames
        self.keypoint_conf_thresh = keypoint_confidence_threshold
        self.board_calibration = board_calibration or WHITEBOARD_DEFAULT_CALIBRATION.copy()

        self.track_buffers: Dict[str, TrackTemporalBuffer] = {}
        self.completed_activity_events: List[ActivityEventSchema] = []
        self.next_event_idx: int = 1
        self.current_frame_index: int = 0

    def reset_session(self) -> None:
        """Resets all track buffers for a new classroom session."""
        self.track_buffers.clear()
        self.completed_activity_events.clear()
        self.next_event_idx = 1
        self.current_frame_index = 0

    def set_board_calibration(
        self,
        x1: float = 20.0,
        y1: float = 5.0,
        x2: float = 80.0,
        y2: float = 35.0,
        forward_vector: Optional[List[float]] = None,
        min_facing_alignment: float = 0.35,
    ) -> None:
        """Configures per-camera whiteboard region and forward direction calibration."""
        self.board_calibration = {
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "forward_vector": forward_vector or [0.0, -1.0],
            "min_facing_alignment": min_facing_alignment,
        }

    def _evaluate_facing_board(
        self,
        box: BoundingBox,
        kp_map: Dict[str, Keypoint],
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Evaluates student facing alignment against the calibrated whiteboard region.
        In elevated rear-camera positions, student orientation is derived from the shoulder vector.
        """
        calib = self.board_calibration or WHITEBOARD_DEFAULT_CALIBRATION
        board_cx = (calib.get("x1", 20.0) + calib.get("x2", 80.0)) / 2.0
        board_cy = (calib.get("y1", 5.0) + calib.get("y2", 35.0)) / 2.0

        student_cx = box.x + box.w / 2.0
        student_cy = box.y + box.h / 2.0

        # Vector pointing from student toward whiteboard center
        target_vec = np.array([board_cx - student_cx, board_cy - student_cy], dtype=float)
        norm_t = np.linalg.norm(target_vec)
        if norm_t > 0:
            target_vec /= norm_t
        else:
            target_vec = np.array([0.0, -1.0])

        l_sh = kp_map.get("left_shoulder")
        r_sh = kp_map.get("right_shoulder")
        if l_sh and r_sh and l_sh.confidence >= 0.25 and r_sh.confidence >= 0.25:
            # Body forward vector orthogonal to shoulder axis (pointing toward front of person)
            # Body forward vector orthogonal to shoulder axis (pointing toward front of person, away from camera)
            # In screen coordinates (+X right, +Y down), right shoulder is at greater X than left shoulder (sh_dx > 0).
            # Vector pointing forward into classroom toward board (negative Y) is (sh_dy, -sh_dx).
            sh_dx = r_sh.x - l_sh.x
            sh_dy = r_sh.y - l_sh.y
            body_vec = np.array([sh_dy, -sh_dx], dtype=float)
            norm_b = np.linalg.norm(body_vec)
            if norm_b > 0:
                body_vec /= norm_b
            else:
                body_vec = np.array([0.0, -1.0])

            alignment = float(np.dot(body_vec, target_vec))
            min_align = calib.get("min_facing_alignment", 0.35)
            is_facing = alignment >= min_align
            return is_facing, round(alignment, 3), {
                "alignmentScore": round(alignment, 3),
                "boardCenterX": float(board_cx),
                "boardCenterY": float(board_cy),
                "minAlignmentThreshold": float(min_align),
            }

        return False, 0.0, {
            "alignmentScore": 0.0,
            "boardCenterX": float(board_cx),
            "boardCenterY": float(board_cy),
            "shouldersAvailable": 0.0,
        }

    # ---------------------------------------------------------------------------
    # Core Evaluation Pipeline
    # ---------------------------------------------------------------------------

    def analyze_frame(
        self,
        person_boxes: List[BoundingBox],
        detected_phones: Optional[List[Dict[str, Any]]] = None,
        timestamp_seconds: Optional[float] = None,
        session_id: str = "sess_live",
        is_pose_mode: bool = True,
        db_session: Any = None,
    ) -> Tuple[List[BoundingBox], List[ActivityEventSchema]]:
        """
        Processes a single video frame with tracked people and detected objects.
        Returns enriched bounding boxes with explainable activity labels, confidence,
        duration, and status color.
        """
        self.current_frame_index += 1
        t_sec = timestamp_seconds if timestamp_seconds is not None else float(self.current_frame_index * 0.20)
        phones = detected_phones or []
        newly_completed_events: List[ActivityEventSchema] = []

        # 1. Map phone detections to spatial person boxes
        person_phone_map = self._associate_phones_to_persons(person_boxes, phones)

        # 2. Extract pairwise proximity and orientation cues (for peer interaction)
        peer_candidates = self._detect_peer_orientations(person_boxes) if is_pose_mode else {}

        # 3. Analyze each individual person
        for idx, box in enumerate(person_boxes):
            track_id = box.id or f"anon_{idx + 1:03d}"
            buffer = self._get_or_create_buffer(track_id, t_sec)

            # Check if this person has an associated detected cell phone
            has_phone = track_id in person_phone_map
            phone_conf = person_phone_map.get(track_id, {}).get("confidence", 0.0)

            # Evaluate posture candidates
            raw_label, conf, evidence = self._evaluate_single_person_activity(
                box=box,
                has_phone=has_phone,
                phone_conf=phone_conf,
                is_peer_candidate=peer_candidates.get(track_id, False),
                peer_evidence=peer_candidates.get(track_id),
                is_pose_mode=is_pose_mode,
            )

            # Add to temporal buffer
            buffer.raw_observations.append((raw_label, conf, evidence))

            # Apply temporal classification & hysteresis
            final_label, final_conf, final_evidence, completed_event = self._apply_temporal_rules(
                buffer=buffer,
                current_time=t_sec,
                current_frame=self.current_frame_index,
                session_id=session_id,
            )

            if completed_event:
                newly_completed_events.append(completed_event)
                if db_session:
                    self._persist_activity_event(completed_event, db_session)

            # Enrich bounding box with single-source-of-truth tags and duration
            color = ACTIVITY_COLORS.get(final_label, COLOR_GREEN)
            base_label = DISPLAY_LABELS.get(final_label, TAG_FACING_BOARD)

            if final_label == ActivityLabel.HEAD_DOWN_POSTURE and buffer.current_duration_seconds > 0:
                disp_label = f"{base_label} ({int(buffer.current_duration_seconds)}s)"
            else:
                disp_label = base_label

            box.activityLabel = disp_label
            box.activityConfidence = round(final_conf, 2)
            box.activityDurationSeconds = round(buffer.current_duration_seconds, 1)
            box.activityEvidence = final_evidence.rationale
            box.statusColor = color
            if has_phone:
                box.detectedObjects = ["cell phone"]

        # 4. Prune missing tracks
        active_ids = set(box.id for box in person_boxes if box.id)
        stale_ids = [tid for tid in self.track_buffers if tid not in active_ids]
        for tid in stale_ids:
            buf = self.track_buffers[tid]
            if buf.active_event_id and buf.current_label != ActivityLabel.NO_FLAG_OBSERVED:
                # Close active event
                closed_evt = self._create_event(
                    buffer=buf,
                    end_time=t_sec,
                    end_frame=self.current_frame_index,
                    session_id=session_id,
                )
                newly_completed_events.append(closed_evt)
                if db_session:
                    self._persist_activity_event(closed_evt, db_session)
            del self.track_buffers[tid]

        return person_boxes, newly_completed_events

    # ---------------------------------------------------------------------------
    # Spatial Phone Association
    # ---------------------------------------------------------------------------

    def _associate_phones_to_persons(
        self,
        person_boxes: List[BoundingBox],
        phones: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Associates detected COCO cell phones to nearby tracked people based on:
        1. Bounding-box containment / upper-body & desk overlap.
        2. Wrist keypoint proximity (left/right wrist within reach of phone).
        Robust to both raw pixel coordinates and normalized [0-100] coordinates.
        """
        assignments: Dict[str, Dict[str, Any]] = {}
        if not phones or not person_boxes:
            return assignments

        for phone in phones:
            p_bbox = phone.get("bbox", []) # [x1, y1, x2, y2]
            p_conf = float(phone.get("confidence", 0.0))
            if len(p_bbox) < 4 or p_conf < 0.20:
                continue

            best_match: Optional[str] = None
            min_dist = float("inf")

            for p in person_boxes:
                # Determine image dimensions from person box if available
                img_w = None
                img_h = None
                if p.w and p.w > 0 and p.width and p.width > 0:
                    img_w = (p.width / p.w) * 100.0
                if p.h and p.h > 0 and p.height and p.height > 0:
                    img_h = (p.height / p.h) * 100.0

                # Derive phone coordinates in normalized percentage [0-100] space
                phone_norm = phone.get("bbox_normalized")
                if phone_norm and len(phone_norm) >= 4:
                    ph_nx1, ph_ny1, ph_nx2, ph_ny2 = phone_norm[:4]
                elif max(p_bbox) > 100.0:
                    # Raw pixel coordinates (e.g. [220, 230, 260, 290])
                    ref_w = img_w or 640.0
                    ref_h = img_h or 480.0
                    ph_nx1 = (p_bbox[0] / ref_w) * 100.0
                    ph_ny1 = (p_bbox[1] / ref_h) * 100.0
                    ph_nx2 = (p_bbox[2] / ref_w) * 100.0
                    ph_ny2 = (p_bbox[3] / ref_h) * 100.0
                else:
                    # Already in percentage space [0-100] (e.g. test fixtures)
                    ph_nx1, ph_ny1, ph_nx2, ph_ny2 = p_bbox[:4]

                ph_ncx = (ph_nx1 + ph_nx2) / 2.0
                ph_ncy = (ph_ny1 + ph_ny2) / 2.0

                # Person box in percentage space [0-100]
                bx1 = p.x
                by1 = p.y
                bx2 = p.x + p.w
                by2 = p.y + p.h

                # Expanded upper-body margin (hands holding phone near lap, chest, or desk surface)
                margin_x = p.w * 0.25
                margin_y_top = p.h * 0.10
                margin_y_bottom = p.h * 0.35  # covers phone resting on desk just below torso box

                overlap_match = (
                    (bx1 - margin_x <= ph_ncx <= bx2 + margin_x) and
                    (by1 - margin_y_top <= ph_ncy <= by2 + margin_y_bottom)
                )

                # Wrist proximity check (using pose keypoints if available)
                wrist_match = False
                if p.keypoints:
                    ph_px_cx = (p_bbox[0] + p_bbox[2]) / 2.0
                    ph_px_cy = (p_bbox[1] + p_bbox[3]) / 2.0
                    max_wrist_dist_px = max(50.0, (p.height or 150.0) * 0.35)
                    max_wrist_dist_norm = max(10.0, p.h * 0.35)

                    for kp in p.keypoints:
                        if kp.name in ("left_wrist", "right_wrist") and kp.confidence >= 0.20:
                            dist_px = ((kp.x - ph_px_cx) ** 2 + (kp.y - ph_px_cy) ** 2) ** 0.5
                            if dist_px <= max_wrist_dist_px:
                                wrist_match = True
                                break
                            dist_norm = ((kp.x - ph_ncx) ** 2 + (kp.y - ph_ncy) ** 2) ** 0.5
                            if dist_norm <= max_wrist_dist_norm:
                                wrist_match = True
                                break

                if overlap_match or wrist_match:
                    dist = abs(ph_ncx - (bx1 + bx2) / 2.0)
                    if dist < min_dist:
                        min_dist = dist
                        best_match = p.id

            if best_match:
                assignments[best_match] = {
                    "phone_bbox": p_bbox,
                    "confidence": p_conf,
                }

        return assignments

    # ---------------------------------------------------------------------------
    # Geometric Evaluation (Pose Keypoints)
    # ---------------------------------------------------------------------------

    def _evaluate_single_person_activity(
        self,
        box: BoundingBox,
        has_phone: bool,
        phone_conf: float,
        is_peer_candidate: bool,
        peer_evidence: Optional[Dict[str, Any]],
        is_pose_mode: bool,
    ) -> Tuple[ActivityLabel, float, ActivityEvidence]:
        """Evaluates instantaneous activity candidates for an individual person."""
        # 1. Priority A: Phone Visible (Requires actual phone object detection)
        if has_phone and phone_conf >= 0.20:
            evidence = ActivityEvidence(
                detectorUsed="YOLOv8n (COCO Class 67)",
                observedFeatures=["Spatial proximity of detected cell phone to tracked person body/hands"],
                geometryMetrics={"phoneConfidence": phone_conf},
                detectedObjects=["cell phone"],
                rationale=f"COCO cell phone detected in hand/torso region (confidence: {phone_conf:.0%}).",
            )
            return ActivityLabel.PHONE_VISIBLE, phone_conf, evidence

        # In Person Mode without pose keypoints, only phone detection or normal presence can be evaluated
        if not is_pose_mode or not box.keypoints:
            evidence = ActivityEvidence(
                detectorUsed="YOLOv8n (Person Mode)",
                observedFeatures=["Person bounding box tracked"],
                rationale="Person mode active. No supported physical activity flag observed.",
            )
            return ActivityLabel.NO_FLAG_OBSERVED, box.confidence, evidence

        # Map keypoints to dictionary for fast O(1) access
        kp_map: Dict[str, Keypoint] = {kp.name: kp for kp in box.keypoints}

        # 2. Priority B: Hand-Raising Posture (Left, Right, Both)
        hand_status, hand_conf, hand_ev = self._evaluate_hand_raise(kp_map)
        if hand_status in (ActivityLabel.BOTH_HANDS_RAISED, ActivityLabel.LEFT_HAND_RAISED, ActivityLabel.RIGHT_HAND_RAISED, ActivityLabel.HAND_RAISED):
            return hand_status, hand_conf, hand_ev

        # 3. Priority C: Head-Down Posture
        is_head_down, hd_conf, hd_ev = self._evaluate_head_down_posture(kp_map)
        if is_head_down:
            return ActivityLabel.HEAD_DOWN_POSTURE, hd_conf, hd_ev

        # 4. Priority D: Possible Peer Interaction
        if is_peer_candidate and peer_evidence:
            peer_ev = ActivityEvidence(
                detectorUsed="YOLOv8n-pose Keypoint Geometry",
                observedFeatures=["Mutual upper-body orientation", "Centroid proximity to adjacent peer"],
                geometryMetrics=peer_evidence.get("metrics", {}),
                rationale="Upper body and head oriented toward adjacent peer within interaction distance.",
            )
            return ActivityLabel.POSSIBLE_PEER_INTERACTION, 0.78, peer_ev

        # 5. Check for ambiguous / low confidence keypoints
        nose = kp_map.get("nose")
        l_sh = kp_map.get("left_shoulder")
        r_sh = kp_map.get("right_shoulder")
        if (nose and 0.15 < nose.confidence <= 0.35) or (l_sh and 0.15 < l_sh.confidence <= 0.35):
            evidence = ActivityEvidence(
                detectorUsed="YOLOv8n-pose",
                observedFeatures=["Low confidence or partially occluded keypoints"],
                rationale="Keypoints partially occluded or below confidence threshold.",
            )
            return ActivityLabel.NEEDS_REVIEW, 0.50, evidence

        # 6. Facing Board (Calibrated forward direction)
        is_facing, align_score, align_meta = self._evaluate_facing_board(box, kp_map)
        features = ["Upright posture", "Arms lowered"]
        if is_facing:
            features.append(f"Oriented toward calibrated board (score: {align_score:.2f})")
            rationale = f"Seated upright facing calibrated whiteboard region (alignment {align_score:.0%}). No supported physical activity flag observed."
        else:
            features.append(f"Angle deviated from board (score: {align_score:.2f})")
            rationale = f"Seated posture. Angle slightly deviated from whiteboard axis. No supported physical activity flag observed."

        evidence = ActivityEvidence(
            detectorUsed="YOLOv8n-pose + Board Calibration",
            observedFeatures=features,
            geometryMetrics=align_meta,
            rationale=rationale,
        )
        return ActivityLabel.NO_FLAG_OBSERVED, box.confidence, evidence

    # ---------------------------------------------------------------------------
    # Posture Geometric Analyzers
    # ---------------------------------------------------------------------------

    def _evaluate_hand_raise(
        self,
        kp_map: Dict[str, Keypoint],
    ) -> Tuple[ActivityLabel, float, ActivityEvidence]:
        """Evaluates hand-raising elevation relative to shoulder level."""
        l_sh = kp_map.get("left_shoulder")
        r_sh = kp_map.get("right_shoulder")
        l_wr = kp_map.get("left_wrist")
        r_wr = kp_map.get("right_wrist")

        margin_px = 15.0
        left_raised = False
        right_raised = False
        l_elev = 0.0
        r_elev = 0.0

        if l_sh and l_wr and l_sh.confidence >= self.keypoint_conf_thresh and l_wr.confidence >= self.keypoint_conf_thresh:
            l_elev = l_sh.y - l_wr.y
            if l_wr.y < (l_sh.y - margin_px):
                left_raised = True

        if r_sh and r_wr and r_sh.confidence >= self.keypoint_conf_thresh and r_wr.confidence >= self.keypoint_conf_thresh:
            r_elev = r_sh.y - r_wr.y
            if r_wr.y < (r_sh.y - margin_px):
                right_raised = True

        if left_raised and right_raised:
            conf = min(l_wr.confidence, r_wr.confidence)
            ev = ActivityEvidence(
                detectorUsed="YOLOv8n-pose Arm Geometry",
                observedFeatures=["Both wrists elevated above shoulder level"],
                geometryMetrics={"leftElevationPx": l_elev, "rightElevationPx": r_elev},
                rationale="Both wrists elevated significantly above shoulder height.",
            )
            return ActivityLabel.BOTH_HANDS_RAISED, conf, ev
        elif left_raised:
            conf = l_wr.confidence
            ev = ActivityEvidence(
                detectorUsed="YOLOv8n-pose Arm Geometry",
                observedFeatures=["Left wrist elevated above left shoulder"],
                geometryMetrics={"leftElevationPx": l_elev},
                rationale="Left wrist elevated above shoulder line.",
            )
            return ActivityLabel.LEFT_HAND_RAISED, conf, ev
        elif right_raised:
            conf = r_wr.confidence
            ev = ActivityEvidence(
                detectorUsed="YOLOv8n-pose Arm Geometry",
                observedFeatures=["Right wrist elevated above right shoulder"],
                geometryMetrics={"rightElevationPx": r_elev},
                rationale="Right wrist elevated above shoulder line.",
            )
            return ActivityLabel.RIGHT_HAND_RAISED, conf, ev

        return ActivityLabel.NO_FLAG_OBSERVED, 0.0, ActivityEvidence()

    def _evaluate_head_down_posture(
        self,
        kp_map: Dict[str, Keypoint],
    ) -> Tuple[bool, float, ActivityEvidence]:
        """
        Evaluates head-down posture from nose and shoulder keypoints.
        Triggers when nose drops significantly towards or below the shoulder line.
        """
        nose = kp_map.get("nose")
        l_sh = kp_map.get("left_shoulder")
        r_sh = kp_map.get("right_shoulder")

        if not nose or nose.confidence < self.keypoint_conf_thresh:
            return False, 0.0, ActivityEvidence()

        shoulders = [s for s in (l_sh, r_sh) if s and s.confidence >= self.keypoint_conf_thresh]
        if not shoulders:
            return False, 0.0, ActivityEvidence()

        s_y = sum(s.y for s in shoulders) / len(shoulders)
        s_dist = abs(l_sh.x - r_sh.x) if (l_sh and r_sh and l_sh.confidence >= 0.3 and r_sh.confidence >= 0.3) else 40.0

        # Elevation of nose above shoulders (negative when nose drops below shoulders)
        elevation = s_y - nose.y

        # When head is resting on desk or dropped downwards:
        # Nose is near or below the shoulder line (elevation <= 0.05 * shoulder_dist)
        is_head_down = elevation < (0.10 * max(20.0, s_dist))

        if is_head_down:
            ev = ActivityEvidence(
                detectorUsed="YOLOv8n-pose Keypoints",
                observedFeatures=["Nose position depressed below standard sitting posture", "Head-to-shoulder compression"],
                geometryMetrics={"noseElevationPx": elevation, "shoulderDistancePx": s_dist},
                rationale=f"Nose elevation ({elevation:.1f}px) dropped near/below shoulder line ({s_y:.1f}px).",
            )
            return True, nose.confidence, ev

        return False, 0.0, ActivityEvidence()

    def _detect_peer_orientations(
        self,
        person_boxes: List[BoundingBox],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Identifies pairs of tracked persons who are:
        1. In spatial proximity (adjacent desks/benches).
        2. Mutually oriented towards each other (converging head/shoulder angles).
        """
        candidates: Dict[str, Dict[str, Any]] = {}
        if len(person_boxes) < 2:
            return candidates

        for i in range(len(person_boxes)):
            for j in range(i + 1, len(person_boxes)):
                b1 = person_boxes[i]
                b2 = person_boxes[j]
                if not b1.id or not b2.id or not b1.keypoints or not b2.keypoints:
                    continue

                c1_x = b1.x + b1.w / 2.0
                c1_y = b1.y + b1.h / 2.0
                c2_x = b2.x + b2.w / 2.0
                c2_y = b2.y + b2.h / 2.0

                # Check horizontal interaction distance (e.g. within 2x bbox width)
                dx = abs(c1_x - c2_x)
                dy = abs(c1_y - c2_y)
                max_interaction_dx = (b1.w + b2.w) * 1.35
                max_interaction_dy = (b1.h + b2.h) * 0.40

                if dx > max_interaction_dx or dy > max_interaction_dy:
                    continue

                # Determine which person is on the left vs right
                left_person = b1 if c1_x < c2_x else b2
                right_person = b2 if c1_x < c2_x else b1

                # Check head/shoulder orientation convergence
                left_facing_right = self._is_facing_right(left_person)
                right_facing_left = self._is_facing_left(right_person)

                if left_facing_right and right_facing_left:
                    # Mutual convergence
                    metrics = {"peerDistanceDx": round(dx, 1), "peerDistanceDy": round(dy, 1)}
                    candidates[left_person.id] = {"peerId": right_person.id, "metrics": metrics}
                    candidates[right_person.id] = {"peerId": left_person.id, "metrics": metrics}

        return candidates

    def _is_facing_right(self, box: BoundingBox) -> bool:
        """Determines if a person's upper body / head is oriented to the right."""
        if not box.keypoints:
            return False
        kp_map = {kp.name: kp for kp in box.keypoints}
        nose = kp_map.get("nose")
        l_sh = kp_map.get("left_shoulder")
        r_sh = kp_map.get("right_shoulder")
        if nose and l_sh and r_sh and l_sh.confidence >= 0.25 and r_sh.confidence >= 0.25:
            mid_x = (l_sh.x + r_sh.x) / 2.0
            return nose.x > (mid_x + 3.0)
        return False

    def _is_facing_left(self, box: BoundingBox) -> bool:
        """Determines if a person's upper body / head is oriented to the left."""
        if not box.keypoints:
            return False
        kp_map = {kp.name: kp for kp in box.keypoints}
        nose = kp_map.get("nose")
        l_sh = kp_map.get("left_shoulder")
        r_sh = kp_map.get("right_shoulder")
        if nose and l_sh and r_sh and l_sh.confidence >= 0.25 and r_sh.confidence >= 0.25:
            mid_x = (l_sh.x + r_sh.x) / 2.0
            return nose.x < (mid_x - 3.0)
        return False

    # ---------------------------------------------------------------------------
    # Temporal Rules, Hysteresis & Event Finalization
    # ---------------------------------------------------------------------------

    def _apply_temporal_rules(
        self,
        buffer: TrackTemporalBuffer,
        current_time: float,
        current_frame: int,
        session_id: str,
    ) -> Tuple[ActivityLabel, float, ActivityEvidence, Optional[ActivityEventSchema]]:
        """
        Applies minimum persistence duration, temporal smoothing, and hysteresis.
        Prevents flickering labels across consecutive frames.
        """
        if not buffer.raw_observations:
            return buffer.current_label, buffer.current_confidence, ActivityEvidence(), None

        latest_cand, latest_conf, latest_ev = buffer.raw_observations[-1]
        completed_event: Optional[ActivityEventSchema] = None

        # Check recent window observations (last 8 frames)
        recent = list(buffer.raw_observations)[-8:]
        cand_counts: Dict[ActivityLabel, int] = {}
        for c, _, _ in recent:
            cand_counts[c] = cand_counts.get(c, 0) + 1

        # Persistence thresholds
        # HEAD_DOWN_POSTURE: requires at least 6 out of 8 frames
        # PHONE_VISIBLE: requires at least 2 frames
        # POSSIBLE_PEER_INTERACTION: requires at least 6 out of 8 frames
        # HAND_RAISED variants: requires at least 2 frames

        target_label = ActivityLabel.NO_FLAG_OBSERVED
        target_conf = latest_conf

        if cand_counts.get(ActivityLabel.PHONE_VISIBLE, 0) >= self.phone_min_frames:
            target_label = ActivityLabel.PHONE_VISIBLE
        elif any(c in (ActivityLabel.BOTH_HANDS_RAISED, ActivityLabel.LEFT_HAND_RAISED, ActivityLabel.RIGHT_HAND_RAISED, ActivityLabel.HAND_RAISED) and cand_counts.get(c, 0) >= 2 for c in cand_counts):
            # Pick dominant hand raise label
            for hr in (ActivityLabel.BOTH_HANDS_RAISED, ActivityLabel.LEFT_HAND_RAISED, ActivityLabel.RIGHT_HAND_RAISED, ActivityLabel.HAND_RAISED):
                if cand_counts.get(hr, 0) >= 2:
                    target_label = hr
                    break
        elif cand_counts.get(ActivityLabel.HEAD_DOWN_POSTURE, 0) >= 6:
            target_label = ActivityLabel.HEAD_DOWN_POSTURE
        elif cand_counts.get(ActivityLabel.POSSIBLE_PEER_INTERACTION, 0) >= 4:
            # Check sustained seconds-based duration threshold
            if buffer.candidate_peer_start_time is None:
                # If first time reaching 4 observations, backdate to start of recent window (4 frames * dt)
                buffer.candidate_peer_start_time = max(0.0, current_time - 0.8)
            peer_elapsed = max(0.0, current_time - buffer.candidate_peer_start_time)

            if peer_elapsed >= self.peer_interaction_min_duration_s or buffer.current_label == ActivityLabel.POSSIBLE_PEER_INTERACTION:
                target_label = ActivityLabel.POSSIBLE_PEER_INTERACTION
            else:
                # Brief glance or turn under duration threshold: keep current label to prevent false accusations
                target_label = buffer.current_label
        elif cand_counts.get(ActivityLabel.NEEDS_REVIEW, 0) >= 4:
            buffer.candidate_peer_start_time = None
            target_label = ActivityLabel.NEEDS_REVIEW
        else:
            buffer.candidate_peer_start_time = None
            # Hysteresis: If current state was an alert, require at least 4 consecutive frames of NO_FLAG to exit
            if buffer.current_label != ActivityLabel.NO_FLAG_OBSERVED:
                normal_count = cand_counts.get(ActivityLabel.NO_FLAG_OBSERVED, 0)
                if normal_count >= 4:
                    target_label = ActivityLabel.NO_FLAG_OBSERVED
                else:
                    target_label = buffer.current_label
            else:
                target_label = ActivityLabel.NO_FLAG_OBSERVED

        # State transition handling
        if target_label != buffer.current_label:
            # If leaving an active flag state, complete the previous event
            if buffer.current_label != ActivityLabel.NO_FLAG_OBSERVED and buffer.current_duration_seconds >= 0.5:
                completed_event = self._create_event(
                    buffer=buffer,
                    end_time=current_time,
                    end_frame=current_frame,
                    session_id=session_id,
                )

            buffer.current_label = target_label
            buffer.current_confidence = target_conf
            buffer.state_start_time = current_time
            buffer.state_start_frame = current_frame
            buffer.frames_in_state = 1
            buffer.current_duration_seconds = 0.0
            buffer.active_event_id = f"act_{self.next_event_idx:04d}"
            self.next_event_idx += 1
        else:
            buffer.frames_in_state += 1
            buffer.current_duration_seconds = max(0.0, current_time - buffer.state_start_time)
            buffer.current_confidence = round(latest_conf * 0.3 + buffer.current_confidence * 0.7, 3)

        latest_ev.durationSeconds = buffer.current_duration_seconds
        latest_ev.persistenceFrames = buffer.frames_in_state

        return buffer.current_label, buffer.current_confidence, latest_ev, completed_event

    def _get_or_create_buffer(self, track_id: str, current_time: float) -> TrackTemporalBuffer:
        if track_id not in self.track_buffers:
            buf = TrackTemporalBuffer(track_id=track_id)
            buf.state_start_time = current_time
            self.track_buffers[track_id] = buf
        return self.track_buffers[track_id]

    def _create_event(
        self,
        buffer: TrackTemporalBuffer,
        end_time: float,
        end_frame: int,
        session_id: str,
    ) -> ActivityEventSchema:
        """Constructs a completed ActivityEventSchema."""
        duration = max(0.1, round(end_time - buffer.state_start_time, 2))
        evt = ActivityEventSchema(
            eventId=buffer.active_event_id or f"act_{self.next_event_idx:04d}",
            sessionId=session_id,
            trackId=buffer.track_id,
            activityLabel=buffer.current_label,
            displayLabel=DISPLAY_LABELS.get(buffer.current_label, "NO FLAG OBSERVED"),
            startTimestampSeconds=round(buffer.state_start_time, 2),
            endTimestampSeconds=round(end_time, 2),
            durationSeconds=duration,
            startFrame=buffer.state_start_frame,
            endFrame=end_frame,
            frameCount=buffer.frames_in_state,
            confidence=round(buffer.current_confidence, 2),
            evidenceSource="YOLOv8n-pose" if "HAND" in buffer.current_label.value or "HEAD" in buffer.current_label.value else "YOLOv8n",
            status="COMPLETED",
        )
        self.completed_activity_events.append(evt)
        return evt

    def _persist_activity_event(self, event: ActivityEventSchema, db_session: Any) -> None:
        """Safely persists completed activity events into SQLite."""
        try:
            from backend.app.database.repositories import ActivityEventRepository
            repo = ActivityEventRepository(db_session)
            repo.upsert(
                event_id=event.eventId,
                session_id=event.sessionId,
                track_id=event.trackId,
                activity_label=event.activityLabel.value,
                display_label=event.displayLabel,
                status_color=ACTIVITY_COLORS.get(event.activityLabel, "GREEN"),
                status=event.status,
                start_timestamp_seconds=event.startTimestampSeconds,
                end_timestamp_seconds=event.endTimestampSeconds or 0.0,
                duration_seconds=event.durationSeconds,
                start_frame=event.startFrame,
                end_frame=event.endFrame or 0,
                frame_count=event.frameCount,
                confidence=event.confidence,
                evidence_source=event.evidenceSource,
                evidence_details=event.evidenceDetails,
                data_source="REAL_PROCESSING",
            )
        except Exception:
            db_session.rollback()

    def get_session_distribution(self, session_id: str = "sess_live") -> ActivityDistributionSummary:
        """Computes aggregate activity distribution for analytics."""
        events = [e for e in self.completed_activity_events if e.sessionId == session_id]
        counts: Dict[str, int] = {}
        durations: Dict[str, List[float]] = {}

        for e in events:
            lbl = e.activityLabel.value
            counts[lbl] = counts.get(lbl, 0) + 1
            durations.setdefault(lbl, []).append(e.durationSeconds)

        # Include current active states
        for buf in self.track_buffers.values():
            lbl = buf.current_label.value
            counts[lbl] = counts.get(lbl, 0) + 1
            durations.setdefault(lbl, []).append(buf.current_duration_seconds)

        total = sum(counts.values())
        percentages = {k: round((v / max(1, total)) * 100, 1) for k, v in counts.items()}
        avg_dur = {k: round(sum(d) / max(1, len(d)), 2) for k, d in durations.items()}

        return ActivityDistributionSummary(
            sessionId=session_id,
            totalTrackedPersons=len(self.track_buffers),
            totalActivityEvents=total,
            activityCounts=counts,
            activityPercentages=percentages,
            avgDurations=avg_dur,
        )


# Global singleton instance
activity_service = ActivityRecognitionService()

