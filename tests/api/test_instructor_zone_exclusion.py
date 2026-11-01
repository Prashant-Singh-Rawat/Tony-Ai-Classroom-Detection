"""
tests/api/test_instructor_zone_exclusion.py — Teacher Zone Exclusion & Spatial Filtering Test Suite
====================================================================================================
Tests the optional Teacher Zone Exclusion (Instructor ROI) capabilities:
1. Invalid polygon coordinate rejection (bounds outside [0, 1], <3 vertices, non-numeric).
2. Teacher raises hand inside zone -> marked INSTRUCTOR_ZONE and excluded from student participation totals.
3. Student raises hand outside zone -> marked STUDENT_ZONE and included in student participation totals.
4. Teacher moves outside zone -> classified as STUDENT_ZONE based on spatial origin (proves no biometric tagging).
5. Student enters instructor zone -> marked INSTRUCTOR_ZONE based on physical blackboard location.
6. Boundary straddling & uncertain bounding boxes -> marked NEEDS_REVIEW.
7. Polygon disabled -> normal processing without exclusion.
8. Multi-resolution & aspect ratio compatibility (320x240, 640x360, 1280x720, 1920x1080, portrait 1080x1920).
9. Session zone configuration REST endpoints (GET, PUT).
10. Analytics comparison (filtered vs unfiltered raw totals).
"""

import json
import pytest
from fastapi.testclient import TestClient

from backend.app.database.db import SessionLocal, init_db
from backend.app.database.models import HandRaiseEventRecord, Session as SessionModel
from backend.app.database.repositories import HandRaiseEventRepository, SessionRepository
from backend.app.main import app
from backend.app.schemas.detections import ObservablePosture, PersonDetection, PersonPoseDetection, PoseGeometry
from backend.app.services.tracking.synthetic_sequences import make_synthetic_pose_frame
from backend.app.services.tracking.temporal_tracker import TemporalTracker
from backend.app.services.tracking.zone_filter import (
    ZoneClassification,
    classify_detection_zone,
    min_distance_to_polygon_boundary,
    point_in_polygon,
    validate_polygon,
)

client = TestClient(app)

# Standard Left Blackboard Polygon
LEFT_BOARD_POLYGON = [
    [0.0, 0.0],
    [0.38, 0.0],
    [0.38, 0.85],
    [0.0, 0.85],
]


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()


# ---------------------------------------------------------------------------
# Test 1: Polygon Validation & Invalid Coordinate Rejection
# ---------------------------------------------------------------------------

def test_invalid_polygon_coordinates():
    """Validates that coordinates outside [0.0, 1.0], <3 vertices, or non-numeric values are rejected."""
    # Out-of-bounds coordinates
    valid, err = validate_polygon([[ -0.1, 0.2 ], [ 0.4, 0.0 ], [ 0.4, 0.8 ]])
    assert not valid
    assert "out of normalized bounds" in err

    valid, err = validate_polygon([[ 0.0, 0.0 ], [ 1.25, 0.0 ], [ 0.4, 0.8 ]])
    assert not valid
    assert "out of normalized bounds" in err

    # Fewer than 3 vertices
    valid, err = validate_polygon([[ 0.1, 0.1 ], [ 0.5, 0.5 ]])
    assert not valid
    assert "at least 3 vertices" in err

    # Degenerate collinear vertices (zero area)
    valid, err = validate_polygon([[ 0.1, 0.1 ], [ 0.2, 0.2 ], [ 0.3, 0.3 ]])
    assert not valid
    assert "degenerate" in err

    # Valid polygon
    valid, err = validate_polygon(LEFT_BOARD_POLYGON)
    assert valid
    assert err is None


def test_put_zone_config_rejects_invalid_polygon():
    """Tests that PUT /api/sessions/{session_id}/zone-config returns HTTP 400 on invalid coordinates."""
    bad_poly = [[0.0, 0.0], [1.5, 0.5], [0.5, 0.5]]
    response = client.put(
        "/api/sessions/test_sess_invalid/zone-config",
        json={"instructorRoiPolygon": bad_poly, "zoneFilteringEnabled": True},
    )
    assert response.status_code == 400
    assert "out of normalized bounds" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Test 2: Teacher Raises Hand Inside Zone
# ---------------------------------------------------------------------------

def test_teacher_raises_hand_inside_zone():
    """
    Simulates a teacher raising hand while standing in front of the blackboard (inside ROI).
    Must be classified as INSTRUCTOR_ZONE, excluded from student participation, and preserved in DB.
    """
    tracker = TemporalTracker()
    tracker.reset_session(session_id="test_teacher_in_zone")
    tracker.set_zone_config(polygon=LEFT_BOARD_POLYGON, enabled=True)

    # Teacher bounding box centered at x=0.18, y=0.30 (inside left blackboard area)
    teacher_bbox = PersonDetection(
        id="anon_001",
        confidence=0.92,
        x=0.10,
        y=0.15,
        width=0.16,
        height=0.45,
        x1=0.10,
        y1=0.15,
        x2=0.26,
        y2=0.60,
    )

    cls, evidence = classify_detection_zone(
        bbox=teacher_bbox,
        polygon=LEFT_BOARD_POLYGON,
        enabled=True,
    )
    assert cls == ZoneClassification.INSTRUCTOR_ZONE
    assert evidence["containment_ratio"] >= 0.65
    assert evidence["centroid_inside"] is True

    # Run through temporal tracker
    db = SessionLocal()
    try:
        # Create session
        s_repo = SessionRepository(db)
        if not s_repo.get_by_id("test_teacher_in_zone"):
            s_repo.create(
                id="test_teacher_in_zone",
                title="Teacher Zone Test",
                instructor_roi_polygon=LEFT_BOARD_POLYGON,
                zone_filtering_enabled=True,
            )

        # Feed 3 consecutive frames with arm raised (cx=100.0, cy=180.0 on 640x480 frame -> x=0.156, y=0.375 inside left blackboard zone)
        pose_det = make_synthetic_pose_frame("anon_001", cx=100.0, cy=180.0, right_hand_raised=True)

        for f in range(1, 4):
            tracker.update([pose_det], timestamp_seconds=f * 0.2, session_id="test_teacher_in_zone", db_session=db)

        # Finalize event
        for track in list(tracker.tracks.values()):
            tracker._finalize_event(track, end_timestamp=1.0, end_frame=3, final_state="COMPLETED", db_session=db)

        # Check in-memory statistics
        stats = tracker.get_statistics_response()
        assert stats.totalEvents == 1
        assert stats.instructorZoneEvents == 1
        assert stats.studentZoneEvents == 0

        # Verify record was NOT deleted in SQLite
        h_repo = HandRaiseEventRepository(db)
        events = h_repo.get_by_session("test_teacher_in_zone")
        assert len(events) == 1
        assert events[0].zone_classification == "INSTRUCTOR_ZONE"
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Test 3: Student Raises Hand Outside Zone
# ---------------------------------------------------------------------------

def test_student_raises_hand_outside_zone():
    """
    Simulates a student raising hand from a desk outside the instructor ROI.
    Must be classified as STUDENT_ZONE and included in student participation totals.
    """
    student_bbox = PersonDetection(
        id="anon_002",
        confidence=0.89,
        x=0.65,
        y=0.35,
        width=0.14,
        height=0.40,
        x1=0.65,
        y1=0.35,
        x2=0.79,
        y2=0.75,
    )

    cls, evidence = classify_detection_zone(
        bbox=student_bbox,
        polygon=LEFT_BOARD_POLYGON,
        enabled=True,
    )
    assert cls == ZoneClassification.STUDENT_ZONE
    assert evidence["containment_ratio"] <= 0.15
    assert evidence["centroid_inside"] is False


# ---------------------------------------------------------------------------
# Test 4: Teacher Moves Outside Zone (Pure Spatial Verification)
# ---------------------------------------------------------------------------

def test_teacher_moves_outside_zone():
    """
    Simulates a teacher walking away from the blackboard into student rows.
    Because ClassVision AI uses strictly SPATIAL origin and zero biometric identity,
    an action originating in the seating rows is classified as STUDENT_ZONE.
    """
    # Teacher moves to student bench area x=0.70, y=0.50
    teacher_outside_bbox = PersonDetection(
        id="anon_001",
        confidence=0.90,
        x=0.70,
        y=0.50,
        width=0.15,
        height=0.45,
        x1=0.70,
        y1=0.50,
        x2=0.85,
        y2=0.95,
    )

    cls, evidence = classify_detection_zone(
        bbox=teacher_outside_bbox,
        polygon=LEFT_BOARD_POLYGON,
        enabled=True,
    )
    assert cls == ZoneClassification.STUDENT_ZONE
    assert "does NOT verify individual identity" in evidence["spatial_disclaimer"]


# ---------------------------------------------------------------------------
# Test 5: Student Enters Instructor Zone
# ---------------------------------------------------------------------------

def test_student_enters_instructor_zone():
    """
    Simulates a student invited to the blackboard to solve an equation.
    Because the physical action occurs inside the teaching perimeter, it is classified
    as INSTRUCTOR_ZONE based purely on location.
    """
    student_at_blackboard = PersonDetection(
        id="anon_005",
        confidence=0.88,
        x=0.15,
        y=0.20,
        width=0.12,
        height=0.40,
        x1=0.15,
        y1=0.20,
        x2=0.27,
        y2=0.60,
    )

    cls, evidence = classify_detection_zone(
        bbox=student_at_blackboard,
        polygon=LEFT_BOARD_POLYGON,
        enabled=True,
    )
    assert cls == ZoneClassification.INSTRUCTOR_ZONE


# ---------------------------------------------------------------------------
# Test 6: Boundary Straddling & Uncertain Bounding Box Handling
# ---------------------------------------------------------------------------

def test_boundary_straddling_and_uncertain_boxes():
    """
    Tests edge cases:
    - Person sitting on the border of the polygon boundary -> NEEDS_REVIEW.
    - Low-confidence or degenerate bounding box -> NEEDS_REVIEW.
    """
    # Straddling the right border of LEFT_BOARD_POLYGON (x=0.38)
    straddling_bbox = PersonDetection(
        id="anon_007",
        confidence=0.85,
        x=0.33,
        y=0.30,
        width=0.12,
        height=0.40,
        x1=0.33,
        y1=0.30,
        x2=0.45,
        y2=0.70,
    )
    cls, evidence = classify_detection_zone(
        bbox=straddling_bbox,
        polygon=LEFT_BOARD_POLYGON,
        enabled=True,
    )
    assert cls == ZoneClassification.NEEDS_REVIEW

    # Degenerate / low confidence bounding box
    low_conf_box = PersonDetection(
        id="anon_008",
        confidence=0.18,  # Below 0.25 threshold
        x=0.15,
        y=0.20,
        width=0.15,
        height=0.40,
        x1=0.15,
        y1=0.20,
        x2=0.30,
        y2=0.60,
    )
    cls, evidence = classify_detection_zone(
        bbox=low_conf_box,
        polygon=LEFT_BOARD_POLYGON,
        enabled=True,
    )
    assert cls == ZoneClassification.NEEDS_REVIEW
    assert evidence["reason"] == "uncertain_bounding_box"


# ---------------------------------------------------------------------------
# Test 7: Polygon Disabled
# ---------------------------------------------------------------------------

def test_polygon_disabled_preserves_normal_processing():
    """When zone filtering is disabled or polygon is None, events are NOT_CONFIGURED and processed normally."""
    bbox = PersonDetection(
        id="anon_001",
        confidence=0.90,
        x=0.10,
        y=0.20,
        width=0.15,
        height=0.40,
        x1=0.10,
        y1=0.20,
        x2=0.25,
        y2=0.60,
    )
    # Disabled flag
    cls, evidence = classify_detection_zone(bbox=bbox, polygon=LEFT_BOARD_POLYGON, enabled=False)
    assert cls == ZoneClassification.NOT_CONFIGURED
    assert evidence["status"] == "filtering_disabled"

    # None polygon
    cls, evidence = classify_detection_zone(bbox=bbox, polygon=None, enabled=True)
    assert cls == ZoneClassification.NOT_CONFIGURED


# ---------------------------------------------------------------------------
# Test 8: Different Video Resolutions and Aspect Ratios
# ---------------------------------------------------------------------------

def test_different_video_resolutions_and_aspect_ratios():
    """
    Tests that normalized polygon filtering behaves identically across arbitrary resolutions:
    320x240 (4:3), 640x360 (16:9), 1280x720 (16:9), 1920x1080 (16:9), and 1080x1920 (9:16 portrait).
    """
    resolutions = [
        (320, 240),
        (640, 360),
        (640, 480),
        (1280, 720),
        (1920, 1080),
        (2560, 1440),
        (1080, 1920),  # Portrait orientation
    ]

    for w, h in resolutions:
        # A person occupying the left 20% width and top 30% height
        pixel_box = {
            "x": int(w * 0.10),
            "y": int(h * 0.15),
            "w": int(w * 0.15),
            "h": int(h * 0.40),
        }
        cls, ev = classify_detection_zone(
            bbox=pixel_box,
            polygon=LEFT_BOARD_POLYGON,
            enabled=True,
            video_width=w,
            video_height=h,
        )
        assert cls == ZoneClassification.INSTRUCTOR_ZONE, f"Failed for resolution {w}x{h}"


# ---------------------------------------------------------------------------
# Test 9: Session Zone Configuration REST Endpoints
# ---------------------------------------------------------------------------

def test_session_zone_configuration_endpoints():
    """Tests GET and PUT /api/sessions/{session_id}/zone-config."""
    sess_id = "test_zone_session_01"

    # 1. Update zone configuration
    put_res = client.put(
        f"/api/sessions/{sess_id}/zone-config",
        json={
            "instructorRoiPolygon": LEFT_BOARD_POLYGON,
            "zoneFilteringEnabled": True,
        },
    )
    assert put_res.status_code == 200
    data = put_res.json()
    assert data["zoneFilteringEnabled"] is True
    assert len(data["instructorRoiPolygon"]) == 4

    # 2. Retrieve zone configuration
    get_res = client.get(f"/api/sessions/{sess_id}/zone-config")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["sessionId"] == sess_id
    assert get_data["zoneFilteringEnabled"] is True
    assert get_data["instructorRoiPolygon"] == LEFT_BOARD_POLYGON


# ---------------------------------------------------------------------------
# Test 10: Analytics Comparison (Filtered vs Raw)
# ---------------------------------------------------------------------------

def test_analytics_comparison_filtered_vs_raw():
    """
    Tests that /api/analytics/session/{session_id} supports comparing results
    with zone filtering enabled vs disabled.
    """
    db = SessionLocal()
    sess_id = "test_analytics_comp_sess"
    try:
        s_repo = SessionRepository(db)
        if not s_repo.get_by_id(sess_id):
            s_repo.create(
                id=sess_id,
                title="Zone Comparison Session",
                instructor_roi_polygon=LEFT_BOARD_POLYGON,
                zone_filtering_enabled=True,
            )

        h_repo = HandRaiseEventRepository(db)
        # Clear existing
        existing = h_repo.get_by_session(sess_id)
        for e in existing:
            db.delete(e)
        db.commit()

        # Seed 2 student events and 1 instructor event
        h_repo.create(
            event_id="evt_stu_01",
            session_id=sess_id,
            track_id="track_01",
            hand_side="LEFT_HAND",
            state="COMPLETED",
            zone_classification="STUDENT_ZONE",
            start_timestamp_seconds=1.0,
            duration_seconds=2.0,
        )
        h_repo.create(
            event_id="evt_stu_02",
            session_id=sess_id,
            track_id="track_02",
            hand_side="RIGHT_HAND",
            state="COMPLETED",
            zone_classification="STUDENT_ZONE",
            start_timestamp_seconds=4.0,
            duration_seconds=2.5,
        )
        h_repo.create(
            event_id="evt_ins_01",
            session_id=sess_id,
            track_id="track_03",
            hand_side="RIGHT_HAND",
            state="COMPLETED",
            zone_classification="INSTRUCTOR_ZONE",
            start_timestamp_seconds=7.0,
            duration_seconds=3.0,
        )

        # 1. Query with zone_filtering=true (Filtered: excludes instructor event)
        res_filtered = client.get(f"/api/analytics/session/{sess_id}?zone_filtering=true")
        assert res_filtered.status_code == 200
        data_f = res_filtered.json()
        assert data_f["totalDetectedHandRaises"] == 3
        assert data_f["totalHandRaisingEvents"] == 2  # Student-only count!
        assert data_f["studentZoneEventsCount"] == 2
        assert data_f["instructorZoneEventsCount"] == 1

        # 2. Query with zone_filtering=false (Raw: includes all events)
        res_raw = client.get(f"/api/analytics/session/{sess_id}?zone_filtering=false")
        assert res_raw.status_code == 200
        data_r = res_raw.json()
        assert data_r["totalDetectedHandRaises"] == 3
        assert data_r["totalHandRaisingEvents"] == 3  # All events!
        assert data_r["instructorZoneEventsCount"] == 1
    finally:
        db.close()
