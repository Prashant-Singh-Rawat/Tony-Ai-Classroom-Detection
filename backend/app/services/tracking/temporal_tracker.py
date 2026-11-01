"""
backend/app/services/tracking/temporal_tracker.py — Temporal Hand-Raising Detection & Tracking
==============================================================================================
Phase 2.2: Temporal Hand-Raising Detection & Anonymous Person Tracking.

Key Capabilities:
1. Anonymous Person Tracking across video frames using IoU & centroid similarity.
2. Hand-Raising Finite State Machine (FSM):
   - NOT_RAISED -> RAISING -> RAISED -> LOWERING -> NOT_RAISED
   - NEEDS_REVIEW for low-confidence or noisy keypoints
3. Temporal Event Detection:
   - One single event per continuous hand raise.
   - Accurate start/end timestamps and duration.
   - Left / Right / Both hands classification.
   - Short detection gap bridging.
   - Cooldown period for duplicate event prevention.
4. Safe SQLite persistence via HandRaiseEventRepository.
5. Strictly anonymous: zero biometric tracking or persistent identity.
"""

from __future__ import annotations

import math
import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from backend.app.schemas.detections import (
    ArmPostureGeometry,
    BoundingBox,
    DetectionSummary,
    Keypoint,
    ObservablePosture,
    PersonDetection,
    PersonPoseDetection,
    PoseDetectionResponse,
    PoseGeometry,
    PoseKeypoint,
)
from backend.app.schemas.tracking import (
    HandRaiseEventSchema,
    HandRaisingState,
    HandSide,
    TrackedPersonState,
    TrackingEventStatisticsResponse,
    TrackingSummaryResponse,
)


def compute_box_iou(box1: List[float], box2: List[float]) -> float:
    """Computes Intersection over Union between two [x1, y1, x2, y2] bounding boxes."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area1 = max(1.0, (box1[2] - box1[0]) * (box1[3] - box1[1]))
    area2 = max(1.0, (box2[2] - box2[0]) * (box2[3] - box2[1]))
    union = area1 + area2 - intersection

    return intersection / max(1.0, union)


class TrackedPerson:
    """Internal state machine and trajectory representation for an active anonymous track."""

    def __init__(
        self,
        track_id: str,
        bbox: PersonDetection,
        keypoints: List[PoseKeypoint],
        geometry: Optional[PoseGeometry] = None,
        timestamp_seconds: float = 0.0,
        frame_index: int = 0,
    ) -> None:
        self.track_id = track_id
        self.bbox = bbox
        self.keypoints = keypoints
        self.geometry = geometry
        self.confidence = bbox.confidence

        # Temporal State Machine
        self.state: HandRaisingState = HandRaisingState.NOT_RAISED
        self.hand_side: HandSide = HandSide.NONE
        self.frames_in_current_state: int = 1
        self.total_frames_tracked: int = 1
        self.missing_frames_count: int = 0
        self.is_occluded: bool = False

        # Event Tracking
        self.active_event: Optional[HandRaiseEventSchema] = None
        self.last_event_end_timestamp: float = -100.0
        self.last_event_end_frame: int = -100

        # Timing
        self.first_seen_timestamp = timestamp_seconds
        self.last_seen_timestamp = timestamp_seconds
        self.last_seen_frame = frame_index

        # History buffer for smoothing
        self.state_history: deque[HandRaisingState] = deque(maxlen=30)
        self.state_history.append(self.state)

    def get_box_coords(self) -> List[float]:
        return [
            float(self.bbox.x1 if self.bbox.x1 is not None else self.bbox.x),
            float(self.bbox.y1 if self.bbox.y1 is not None else self.bbox.y),
            float(self.bbox.x2 if self.bbox.x2 is not None else (self.bbox.x + self.bbox.width)),
            float(self.bbox.y2 if self.bbox.y2 is not None else (self.bbox.y + self.bbox.height)),
        ]

    def get_centroid(self) -> Tuple[float, float]:
        coords = self.get_box_coords()
        return ((coords[0] + coords[2]) / 2.0, (coords[1] + coords[3]) / 2.0)

    def to_schema(self) -> TrackedPersonState:
        return TrackedPersonState(
            trackId=self.track_id,
            state=self.state,
            handSide=self.hand_side,
            confidence=round(self.confidence, 3),
            bbox=self.bbox,
            keypoints=self.keypoints,
            geometry=self.geometry,
            framesInCurrentState=self.frames_in_current_state,
            totalFramesTracked=self.total_frames_tracked,
            missingFramesCount=self.missing_frames_count,
            isOccluded=self.is_occluded,
            activeEventId=self.active_event.eventId if self.active_event else None,
            lastUpdatedTimestamp=round(self.last_seen_timestamp, 3),
        )


class TemporalTracker:
    """
    Manages anonymous track assignment, temporal state machine transitions,
    and event aggregation across consecutive frames.
    """

    def __init__(
        self,
        keypoint_confidence_threshold: float = 0.40,
        elevation_margin_px: float = 15.0,
        min_raised_frames: int = 2,
        max_missing_frames: int = 10,
        cooldown_seconds: float = 1.0,
        iou_match_threshold: float = 0.20,
    ) -> None:
        self.keypoint_conf_thresh = keypoint_confidence_threshold
        self.elevation_margin_px = elevation_margin_px
        self.min_raised_frames = min_raised_frames
        self.max_missing_frames = max_missing_frames
        self.cooldown_seconds = cooldown_seconds
        self.iou_match_thresh = iou_match_threshold

        self.tracks: Dict[str, TrackedPerson] = {}
        self.next_track_idx: int = 1
        self.next_event_idx: int = 1
        self.completed_events: List[HandRaiseEventSchema] = []
        self.all_events_by_id: Dict[str, HandRaiseEventSchema] = {}
        self.current_frame_index: int = 0
        self.current_session_id: str = "sess_live"
        self.instructor_roi_polygon: Optional[List[List[float]]] = None
        self.zone_filtering_enabled: bool = True
        self.video_width: Optional[int] = None
        self.video_height: Optional[int] = None

    def set_zone_config(
        self,
        polygon: Optional[List[List[float]]] = None,
        enabled: bool = True,
        video_width: Optional[int] = None,
        video_height: Optional[int] = None,
    ) -> None:
        """Sets or updates the Teacher Zone Exclusion polygon, activation state, and frame dimensions."""
        self.instructor_roi_polygon = polygon
        self.zone_filtering_enabled = enabled
        if video_width is not None:
            self.video_width = video_width
        if video_height is not None:
            self.video_height = video_height

    def reset_session(self, session_id: str = "sess_live") -> None:
        """Resets the tracker for a new monitoring session."""
        self.tracks.clear()
        self.completed_events.clear()
        self.all_events_by_id.clear()
        self.next_track_idx = 1
        self.next_event_idx = 1
        self.current_frame_index = 0
        self.current_session_id = session_id

    # ---------------------------------------------------------------------------
    # Core Update Cycle
    # ---------------------------------------------------------------------------

    def update(
        self,
        pose_detections: List[PersonPoseDetection],
        timestamp_seconds: Optional[float] = None,
        session_id: Optional[str] = None,
        db_session: Any = None,
        video_width: Optional[int] = None,
        video_height: Optional[int] = None,
    ) -> Tuple[List[TrackedPersonState], List[HandRaiseEventSchema]]:
        """
        Ingests a frame of pose detections, associates tracks, updates state machines,
        and generates completed/active hand-raising events.
        """
        self.current_frame_index += 1
        t_sec = timestamp_seconds if timestamp_seconds is not None else float(self.current_frame_index * 0.033)
        if session_id:
            self.current_session_id = session_id
        if video_width is not None:
            self.video_width = video_width
        if video_height is not None:
            self.video_height = video_height

        # 1. Associate Detections with Active Tracks
        matched_pairs, unmatched_dets, unmatched_tracks = self._associate_detections(pose_detections)

        # 2. Update Matched Tracks
        newly_completed_events: List[HandRaiseEventSchema] = []
        for track_id, det in matched_pairs:
            track = self.tracks[track_id]
            completed_evt = self._update_track_with_detection(
                track, det, t_sec, self.current_frame_index, db_session
            )
            if completed_evt:
                newly_completed_events.append(completed_evt)

        # 3. Handle Unmatched Detections -> Initiate New Tracks
        for det in unmatched_dets:
            track_id = f"track_{self.next_track_idx:03d}"
            self.next_track_idx += 1
            new_track = TrackedPerson(
                track_id=track_id,
                bbox=det.bbox,
                keypoints=det.keypoints,
                geometry=det.geometry,
                timestamp_seconds=t_sec,
                frame_index=self.current_frame_index,
            )
            self._update_track_fsm(new_track, det, t_sec, self.current_frame_index, db_session)
            self.tracks[track_id] = new_track

        # 4. Handle Unmatched Active Tracks -> Occlusion / Missing
        expired_track_ids = []
        for track_id in unmatched_tracks:
            track = self.tracks[track_id]
            track.missing_frames_count += 1
            track.is_occluded = True

            # If track had an active event and is missing for too long, close the event
            if track.missing_frames_count > self.max_missing_frames:
                if track.active_event:
                    closed_evt = self._finalize_event(
                        track,
                        end_timestamp=t_sec,
                        end_frame=self.current_frame_index,
                        final_state="COMPLETED" if track.state == HandRaisingState.RAISED else "NEEDS_REVIEW",
                        db_session=db_session,
                    )
                    if closed_evt:
                        newly_completed_events.append(closed_evt)
                expired_track_ids.append(track_id)
            elif track.missing_frames_count >= 2 and track.state != HandRaisingState.RAISED:
                # Set state to NEEDS_REVIEW when occluded
                track.state = HandRaisingState.NEEDS_REVIEW

        # 5. Prune Expired Tracks
        for track_id in expired_track_ids:
            del self.tracks[track_id]

        active_track_states = [track.to_schema() for track in self.tracks.values()]
        return active_track_states, newly_completed_events

    # ---------------------------------------------------------------------------
    # Track Association (IoU + Centroid Distance)
    # ---------------------------------------------------------------------------

    def _associate_detections(
        self,
        detections: List[PersonPoseDetection],
    ) -> Tuple[List[Tuple[str, PersonPoseDetection]], List[PersonPoseDetection], List[str]]:
        if not self.tracks:
            return [], detections, []
        if not detections:
            return [], [], list(self.tracks.keys())

        track_ids = list(self.tracks.keys())
        cost_matrix = np.zeros((len(track_ids), len(detections)), dtype=np.float32)

        for t_i, t_id in enumerate(track_ids):
            track = self.tracks[t_id]
            t_box = track.get_box_coords()
            t_cx, t_cy = track.get_centroid()
            t_w = max(1.0, t_box[2] - t_box[0])
            t_h = max(1.0, t_box[3] - t_box[1])

            for d_i, det in enumerate(detections):
                d_box = [
                    float(det.bbox.x1 if det.bbox.x1 is not None else det.bbox.x),
                    float(det.bbox.y1 if det.bbox.y1 is not None else det.bbox.y),
                    float(det.bbox.x2 if det.bbox.x2 is not None else (det.bbox.x + det.bbox.width)),
                    float(det.bbox.y2 if det.bbox.y2 is not None else (det.bbox.y + det.bbox.height)),
                ]
                d_cx = (d_box[0] + d_box[2]) / 2.0
                d_cy = (d_box[1] + d_box[3]) / 2.0

                iou = compute_box_iou(t_box, d_box)
                dist_norm = math.hypot(t_cx - d_cx, t_cy - d_cy) / max(t_w, t_h)
                proximity = max(0.0, 1.0 - dist_norm)

                # Similarity score in [0.0, 1.0]
                similarity = 0.7 * iou + 0.3 * proximity
                cost_matrix[t_i, d_i] = similarity

        matched_pairs: List[Tuple[str, PersonPoseDetection]] = []
        unmatched_dets: List[PersonPoseDetection] = list(detections)
        unmatched_tracks: List[str] = list(track_ids)

        # Greedy maximum matching
        while True:
            if cost_matrix.size == 0:
                break
            max_sim = np.max(cost_matrix)
            if max_sim < self.iou_match_thresh:
                break
            t_i, d_i = np.unravel_index(np.argmax(cost_matrix), cost_matrix.shape)
            track_id = track_ids[t_i]
            det = detections[d_i]

            matched_pairs.append((track_id, det))
            if det in unmatched_dets:
                unmatched_dets.remove(det)
            if track_id in unmatched_tracks:
                unmatched_tracks.remove(track_id)

            # Invalidate row and column
            cost_matrix[t_i, :] = -1.0
            cost_matrix[:, d_i] = -1.0

        return matched_pairs, unmatched_dets, unmatched_tracks

    # ---------------------------------------------------------------------------
    # Finite State Machine Update
    # ---------------------------------------------------------------------------

    def _update_track_with_detection(
        self,
        track: TrackedPerson,
        det: PersonPoseDetection,
        t_sec: float,
        frame_idx: int,
        db_session: Any,
    ) -> Optional[HandRaiseEventSchema]:
        track.bbox = det.bbox
        track.keypoints = det.keypoints
        track.geometry = det.geometry
        track.confidence = det.confidence
        track.missing_frames_count = 0
        track.is_occluded = False
        track.total_frames_tracked += 1
        track.last_seen_timestamp = t_sec
        track.last_seen_frame = frame_idx

        return self._update_track_fsm(track, det, t_sec, frame_idx, db_session)

    def _update_track_fsm(
        self,
        track: TrackedPerson,
        det: PersonPoseDetection,
        t_sec: float,
        frame_idx: int,
        db_session: Any,
    ) -> Optional[HandRaiseEventSchema]:
        """
        Evaluates anatomical keypoint geometry and updates FSM state transitions:
        NOT_RAISED -> RAISING -> RAISED -> LOWERING -> NOT_RAISED | NEEDS_REVIEW
        """
        # 1. Analyze instantaneous physical arm status
        instant_status, hand_side, evidence = self._evaluate_instant_geometry(det)

        prev_state = track.state
        completed_event: Optional[HandRaiseEventSchema] = None

        # Check cooldown period (prevent rapid flutter duplicate events)
        in_cooldown = (t_sec - track.last_event_end_timestamp) < self.cooldown_seconds

        # 2. State Machine Transitions
        if instant_status == "AMBIGUOUS" or instant_status == "LOW_CONFIDENCE":
            if track.state == HandRaisingState.RAISED:
                # If currently raised, tolerate brief noise (up to 2 frames) before entering NEEDS_REVIEW
                if track.frames_in_current_state >= 2:
                    track.frames_in_current_state += 1
                else:
                    track.state = HandRaisingState.NEEDS_REVIEW
                    track.frames_in_current_state = 1
            else:
                track.state = HandRaisingState.NEEDS_REVIEW
                track.frames_in_current_state = 1

        elif instant_status == "RAISED":
            if in_cooldown and track.state == HandRaisingState.NOT_RAISED:
                # In cooldown, suppress immediate re-trigger
                track.state = HandRaisingState.NOT_RAISED
                track.frames_in_current_state += 1
            elif track.state == HandRaisingState.NOT_RAISED:
                track.state = HandRaisingState.RAISING
                track.hand_side = hand_side
                track.frames_in_current_state = 1
            elif track.state == HandRaisingState.RAISING:
                track.frames_in_current_state += 1
                if track.frames_in_current_state >= self.min_raised_frames:
                    track.state = HandRaisingState.RAISED
                    track.hand_side = hand_side
                    # Initiate single temporal event
                    self._start_event(track, t_sec, frame_idx, hand_side, evidence)
            elif track.state == HandRaisingState.RAISED:
                track.frames_in_current_state += 1
                track.hand_side = hand_side
                if track.active_event:
                    self._accumulate_event(track.active_event, det, evidence)
            elif track.state == HandRaisingState.LOWERING:
                # Arm aborted lowering and re-raised -> continue existing event
                track.state = HandRaisingState.RAISED
                track.frames_in_current_state += 1
            elif track.state == HandRaisingState.NEEDS_REVIEW:
                track.state = HandRaisingState.RAISED
                track.hand_side = hand_side
                track.frames_in_current_state = 1
                if not track.active_event:
                    self._start_event(track, t_sec, frame_idx, hand_side, evidence)

        elif instant_status == "RAISING_ZONE":
            if track.state == HandRaisingState.NOT_RAISED:
                track.state = HandRaisingState.RAISING
                track.hand_side = hand_side
                track.frames_in_current_state = 1
            elif track.state == HandRaisingState.RAISING:
                track.frames_in_current_state += 1
            elif track.state == HandRaisingState.RAISED:
                track.state = HandRaisingState.LOWERING
                track.frames_in_current_state = 1
            elif track.state == HandRaisingState.LOWERING:
                track.frames_in_current_state += 1

        elif instant_status == "NOT_RAISED":
            if track.state == HandRaisingState.RAISING:
                # Arm lowered before completing min_raised_frames -> false positive aborted
                track.state = HandRaisingState.NOT_RAISED
                track.hand_side = HandSide.NONE
                track.frames_in_current_state = 1
            elif track.state == HandRaisingState.RAISED:
                track.state = HandRaisingState.LOWERING
                track.frames_in_current_state = 1
            elif track.state == HandRaisingState.LOWERING:
                track.frames_in_current_state += 1
                if track.frames_in_current_state >= 2:
                    # Conclude the event!
                    track.state = HandRaisingState.NOT_RAISED
                    track.hand_side = HandSide.NONE
                    completed_event = self._finalize_event(
                        track,
                        end_timestamp=t_sec,
                        end_frame=frame_idx,
                        final_state="COMPLETED",
                        db_session=db_session,
                    )
            elif track.state == HandRaisingState.NOT_RAISED:
                track.frames_in_current_state += 1
                track.hand_side = HandSide.NONE
            elif track.state == HandRaisingState.NEEDS_REVIEW:
                track.state = HandRaisingState.NOT_RAISED
                track.hand_side = HandSide.NONE
                track.frames_in_current_state = 1

        track.state_history.append(track.state)
        return completed_event

    # ---------------------------------------------------------------------------
    # Anatomical Geometry Evaluation
    # ---------------------------------------------------------------------------

    def _evaluate_instant_geometry(
        self,
        det: PersonPoseDetection,
    ) -> Tuple[str, HandSide, Dict[str, Any]]:
        """
        Validates shoulder, elbow, and wrist keypoints, confidence scores, and angles.
        Returns: (instant_status, hand_side, evidence_dict)
        """
        geom = det.geometry
        if not geom:
            return "AMBIGUOUS", HandSide.NONE, {"reason": "missing_geometry"}

        left_arm = geom.leftArm
        right_arm = geom.rightArm

        # Check keypoint existence
        kp_dict = {kp.name: kp for kp in det.keypoints}
        ls = kp_dict.get("left_shoulder")
        rs = kp_dict.get("right_shoulder")
        lw = kp_dict.get("left_wrist")
        rw = kp_dict.get("right_wrist")
        le = kp_dict.get("left_elbow")
        re = kp_dict.get("right_elbow")

        evidence: Dict[str, Any] = {
            "left_wrist_conf": lw.confidence if lw else 0.0,
            "right_wrist_conf": rw.confidence if rw else 0.0,
            "left_elevation": left_arm.elevationPx,
            "right_elevation": right_arm.elevationPx,
            "left_angle": left_arm.elbowAngleDeg,
            "right_angle": right_arm.elbowAngleDeg,
        }

        # Check for noisy/missing keypoints
        left_valid = (
            ls is not None and lw is not None and le is not None
            and ls.confidence >= self.keypoint_conf_thresh
            and lw.confidence >= self.keypoint_conf_thresh
        )
        right_valid = (
            rs is not None and rw is not None and re is not None
            and rs.confidence >= self.keypoint_conf_thresh
            and rw.confidence >= self.keypoint_conf_thresh
        )

        left_noisy = (
            lw is not None and (0.15 <= lw.confidence < self.keypoint_conf_thresh)
        )
        right_noisy = (
            rw is not None and (0.15 <= rw.confidence < self.keypoint_conf_thresh)
        )

        if not left_valid and not right_valid:
            if left_noisy or right_noisy:
                evidence["reason"] = "low_keypoint_confidence"
                return "LOW_CONFIDENCE", HandSide.UNKNOWN, evidence
            evidence["reason"] = "missing_keypoints"
            return "AMBIGUOUS", HandSide.NONE, evidence

        left_raised = False
        right_raised = False
        left_in_zone = False
        right_in_zone = False

        if left_valid and left_arm.elevationPx is not None:
            elev = left_arm.elevationPx
            # Validate elbow angle (anatomical check)
            angle = left_arm.elbowAngleDeg or 90.0
            if elev >= self.elevation_margin_px and (45.0 <= angle <= 185.0):
                left_raised = True
            elif elev >= -10.0:
                left_in_zone = True

        if right_valid and right_arm.elevationPx is not None:
            elev = right_arm.elevationPx
            angle = right_arm.elbowAngleDeg or 90.0
            if elev >= self.elevation_margin_px and (45.0 <= angle <= 185.0):
                right_raised = True
            elif elev >= -10.0:
                right_in_zone = True

        if left_raised and right_raised:
            return "RAISED", HandSide.BOTH_HANDS, evidence
        elif left_raised:
            return "RAISED", HandSide.LEFT_HAND, evidence
        elif right_raised:
            return "RAISED", HandSide.RIGHT_HAND, evidence
        elif left_in_zone or right_in_zone:
            side = HandSide.BOTH_HANDS if (left_in_zone and right_in_zone) else (HandSide.LEFT_HAND if left_in_zone else HandSide.RIGHT_HAND)
            return "RAISING_ZONE", side, evidence
        else:
            return "NOT_RAISED", HandSide.NONE, evidence

    # ---------------------------------------------------------------------------
    # Event Lifecycle Methods
    # ---------------------------------------------------------------------------

    def _start_event(
        self,
        track: TrackedPerson,
        t_sec: float,
        frame_idx: int,
        side: HandSide,
        evidence: Dict[str, Any],
    ) -> HandRaiseEventSchema:
        event_id = f"evt_{self.next_event_idx:04d}"
        self.next_event_idx += 1

        # Evaluate Teacher Zone Exclusion (Spatial ROI)
        from backend.app.services.tracking.zone_filter import classify_detection_zone
        zone_cls, zone_evidence = classify_detection_zone(
            bbox=track.bbox,
            polygon=self.instructor_roi_polygon,
            enabled=self.zone_filtering_enabled,
            video_width=self.video_width,
            video_height=self.video_height,
            confidence=track.confidence,
            is_occluded=track.is_occluded,
        )
        evidence["zone_classification"] = zone_cls.value
        evidence["zone_evidence"] = zone_evidence

        evt = HandRaiseEventSchema(
            eventId=event_id,
            sessionId=self.current_session_id,
            trackId=track.track_id,
            handSide=side,
            state="RAISED",
            zoneClassification=zone_cls.value,
            startTimestampSeconds=round(t_sec, 3),
            endTimestampSeconds=None,
            durationSeconds=0.0,
            startFrame=frame_idx,
            endFrame=None,
            frameCount=1,
            maxConfidence=round(track.confidence, 3),
            avgConfidence=round(track.confidence, 3),
            evidence=evidence,
            dataSource="REAL_PROCESSING",
            createdAt=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        track.active_event = evt
        self.all_events_by_id[event_id] = evt
        return evt

    def _accumulate_event(
        self,
        evt: HandRaiseEventSchema,
        det: PersonPoseDetection,
        evidence: Dict[str, Any],
    ) -> None:
        evt.frameCount += 1
        conf = det.confidence
        evt.maxConfidence = max(evt.maxConfidence, round(conf, 3))
        evt.avgConfidence = round((evt.avgConfidence * (evt.frameCount - 1) + conf) / evt.frameCount, 3)
        evt.evidence.update(evidence)

    def _finalize_event(
        self,
        track: TrackedPerson,
        end_timestamp: float,
        end_frame: int,
        final_state: str = "COMPLETED",
        db_session: Any = None,
    ) -> Optional[HandRaiseEventSchema]:
        evt = track.active_event
        if not evt:
            return None

        evt.endTimestampSeconds = round(end_timestamp, 3)
        evt.endFrame = end_frame
        evt.durationSeconds = max(0.05, round(end_timestamp - evt.startTimestampSeconds, 2))
        evt.state = final_state

        track.last_event_end_timestamp = end_timestamp
        track.last_event_end_frame = end_frame
        track.active_event = None

        self.completed_events.append(evt)

        # Persist to SQLite if db_session is provided
        if db_session is not None:
            try:
                from backend.app.database.repositories import HandRaiseEventRepository
                repo = HandRaiseEventRepository(db_session)
                repo.upsert(
                    event_id=evt.eventId,
                    session_id=evt.sessionId,
                    track_id=evt.trackId,
                    hand_side=evt.handSide.value,
                    state=evt.state,
                    zone_classification=evt.zoneClassification,
                    start_timestamp_seconds=evt.startTimestampSeconds,
                    end_timestamp_seconds=evt.endTimestampSeconds,
                    duration_seconds=evt.durationSeconds,
                    start_frame=evt.startFrame,
                    end_frame=evt.endFrame,
                    frame_count=evt.frameCount,
                    max_confidence=evt.maxConfidence,
                    avg_confidence=evt.avgConfidence,
                    evidence=evt.evidence,
                    data_source=evt.dataSource,
                )
            except Exception:
                pass

        return evt

    # ---------------------------------------------------------------------------
    # Query & Reporting Helpers
    # ---------------------------------------------------------------------------

    def get_summary_response(self) -> TrackingSummaryResponse:
        active_tracks = [t.to_schema() for t in self.tracks.values()]
        active_raises = sum(1 for t in self.tracks.values() if t.state == HandRaisingState.RAISED)

        states_summary = {
            HandRaisingState.NOT_RAISED.value: 0,
            HandRaisingState.RAISING.value: 0,
            HandRaisingState.RAISED.value: 0,
            HandRaisingState.LOWERING.value: 0,
            HandRaisingState.NEEDS_REVIEW.value: 0,
        }
        for t in self.tracks.values():
            states_summary[t.state.value] = states_summary.get(t.state.value, 0) + 1

        active_events = [t.active_event for t in self.tracks.values() if t.active_event]

        return TrackingSummaryResponse(
            sessionId=self.current_session_id,
            timestampSeconds=round(self.current_frame_index * 0.033, 2),
            activeTracksCount=len(active_tracks),
            activeHandRaisesCount=active_raises,
            statesSummary=states_summary,
            tracks=active_tracks,
            activeEvents=active_events,
            dataSource="REAL_PROCESSING",
        )

    def get_statistics_response(self) -> TrackingEventStatisticsResponse:
        all_evts = list(self.all_events_by_id.values())
        completed = [e for e in all_evts if e.state == "COMPLETED"]
        active = [e for e in all_evts if e.state == "RAISED"]
        needs_rev = [e for e in all_evts if e.state == "NEEDS_REVIEW"]

        durations = [e.durationSeconds for e in completed if e.durationSeconds > 0]
        left_count = sum(1 for e in all_evts if e.handSide == HandSide.LEFT_HAND)
        right_count = sum(1 for e in all_evts if e.handSide == HandSide.RIGHT_HAND)
        both_count = sum(1 for e in all_evts if e.handSide == HandSide.BOTH_HANDS)

        student_zone_count = sum(
            1 for e in all_evts
            if getattr(e, "zoneClassification", "STUDENT_ZONE") in ("STUDENT_ZONE", "NOT_CONFIGURED")
        )
        instructor_zone_count = sum(
            1 for e in all_evts
            if getattr(e, "zoneClassification", None) == "INSTRUCTOR_ZONE"
        )
        uncertain_zone_count = sum(
            1 for e in all_evts
            if getattr(e, "zoneClassification", None) == "NEEDS_REVIEW"
        )

        return TrackingEventStatisticsResponse(
            sessionId=self.current_session_id,
            totalEvents=len(all_evts),
            completedEvents=len(completed),
            activeEvents=len(active),
            leftHandCount=left_count,
            rightHandCount=right_count,
            bothHandsCount=both_count,
            avgDurationSeconds=round(sum(durations) / max(1, len(durations)), 2),
            maxDurationSeconds=round(max(durations), 2) if durations else 0.0,
            totalDurationSeconds=round(sum(durations), 2),
            needsReviewCount=len(needs_rev),
            cooldownPeriodSeconds=self.cooldown_seconds,
            studentZoneEvents=student_zone_count,
            instructorZoneEvents=instructor_zone_count,
            uncertainEvents=uncertain_zone_count,
            zoneFilteringEnabled=self.zone_filtering_enabled,
        )


# Singleton TemporalTracker instance
temporal_tracker = TemporalTracker()

