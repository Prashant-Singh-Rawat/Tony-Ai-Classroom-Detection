# Turned Sideways Activity Detection Improvement Report

**Project**: ClassVision AI — Real-Time Multimodal Classroom Intelligence System  
**Date**: November 2, 2026  
**Target Path**: `docs/SIDEWAYS_ACTIVITY_DETECTION_IMPROVEMENT_REPORT.md`  
**Status**: Verified & Production Ready  

---

## 1. Executive Summary

In classroom monitoring, accurately discerning student posture is critical for non-invasive pedagogical analytics. A critical flaw in earlier revisions was that students sitting sideways relative to their desks or facing a peer/neighbor were frequently classified as `Needs review` (Gray) or occasionally fell back to `Facing board` (Green) instead of being reliably identified as **Turned sideways** (`possible_peer_interaction`, Orange).

This enhancement resolves the issue by introducing a principled, scale-invariant **observable body geometry** framework that operates without facial recognition or biometric profiling. The system now evaluates shoulder foreshortening, hip alignment, composite torso angle, upper-body tilt, camera viewpoint calibration (rear vs. side cameras), and temporal hysteresis.

All 8 newly introduced unit/integration tests and all 27 pre-existing activity recognition test suites pass with 100% success. Live classroom video verification demonstrates stable Orange bounding boxes for sideways-oriented students.

---

## 2. Root Cause Analysis

Investigation of `backend/app/services/activity_recognition/service.py` revealed four primary causes for incorrect classifications:

1. **Strict Mutual Peer Coupling**:
   - `ActivityLabel.POSSIBLE_PEER_INTERACTION` was guarded by `if is_peer_candidate and peer_evidence:` requiring two adjacent bounding boxes mutually converging. An individual student turned sideways without an immediate active neighbor was never labeled as turned sideways.
2. **Aggressive `Needs Review` Short-Circuiting**:
   - In profile or oblique seating angles, the ear, nose, or distant shoulder landmark often has lower confidence ($0.15 < c \le 0.35$). The earlier logic immediately escalated any reduced confidence into `ActivityLabel.NEEDS_REVIEW`.
3. **Improper Fallback in Angle Checks**:
   - In `_evaluate_facing_board`, when angular deviations exceeded the tolerance ($> 28^\circ$), the `else` branch still fell through to `ActivityLabel.NO_FLAG_OBSERVED` ("Facing board"), concealing sideways orientations.
4. **Unused Hip Keypoints**:
   - Only shoulder landmarks were inspected. Without `left_hip` and `right_hip`, the torso plane could not be estimated, making the classifier vulnerable to arm or head-only motions.

---

## 3. Observable Geometric Formulation

To maintain strict ethical boundaries and comply with zero facial recognition constraints, all calculations rely purely on COCO-17 upper-body skeletal landmarks (shoulders, hips, and nose):

### A. Scale-Invariant Shoulder & Hip Foreshortening
For detected left and right shoulders $(x_1, y_1)$ and $(x_2, y_2)$ with confidence $c_1, c_2 \ge 0.22$:
$$\Delta X_{sh} = |x_1 - x_2|, \quad D_{sh} = \sqrt{(x_1 - x_2)^2 + (y_1 - y_2)^2}$$
$$R_{sh} = \frac{\Delta X_{sh}}{D_{sh}}$$

Similarly, when hips are visible ($c_{hip} \ge 0.22$):
$$R_{hip} = \frac{\Delta X_{hip}}{D_{hip}}$$

When both are present, a weighted composite ratio is formed:
$$R_{torso} = 0.6 \cdot R_{sh} + 0.4 \cdot R_{hip}$$

- **Facing Forward / Board**: $R_{torso} \ge 0.72$ (broad horizontal span across camera).
- **Turned Sideways**: $R_{torso} < 0.58$ (narrow horizontal projection, large depth foreshortening).

### B. Shoulder Axis Tilt & Torso Normal Vector
The upper torso angle in the image plane:
$$\theta_{sh} = \left| \arctan2(y_2 - y_1, x_2 - x_1) \right|$$
Significant tilt ($|\theta_{sh} - 90^\circ| < 45^\circ$ or tilt $> 35^\circ$) combined with moderate foreshortening indicates a student leaning or turning their upper body toward an aisle or peer.

The estimated 2D torso normal vector $\vec{v}_{body}$ is computed perpendicular to the shoulder span:
$$\vec{v}_{sh} = \left( \frac{x_2 - x_1}{D_{sh}}, \frac{y_2 - y_1}{D_{sh}} \right), \quad \vec{v}_{body} = (-v_{sh,y}, v_{sh,x})$$

### C. Classroom Board Alignment ($S_{align}$)
The dot product against the calibrated classroom board direction $\vec{v}_{board} = (v_{bx}, v_{by})$ gives the alignment score:
$$S_{align} = \vec{v}_{body} \cdot \vec{v}_{board}$$

- $S_{align} \ge 0.55$: Facing board.
- $S_{align} < 0.20$: Substantially deviated / turned sideways.
- $S_{align} < -0.25$: Facing directly away from the board / turned rearwards.

### D. Asymmetric Profile Sitting
When a student is fully in profile ($90^\circ$ sideways), the far shoulder is physically occluded by the neck/torso. If $\max(c_{sh}) \ge 0.35$ while $\min(c_{sh}) < 0.22$, and the nose is displaced laterally toward the bounding box edge ($> 0.22 \times \text{width}$ from center), the posture is classified as profile sideways rather than degraded noise.

---

## 4. Camera Viewpoint Invariance

Different classroom installations feature different camera placements:
1. **Rear-Mounted Camera**: Students facing the board face away from the camera. In this setup, broad horizontal shoulder spans indicate normal orientation facing the front board.
2. **Side-Mounted Camera**: Students facing the front board appear sideways in raw camera coordinates. By calibrating the classroom board vector (e.g. $\vec{v}_{board} = (1.0, 0.0)$), forward-facing students are correctly classified as `Facing board`, avoiding false positives.

---

## 5. Temporal Stability & Hysteresis

To eliminate frame-to-frame label flicker:
- **Confirmation Threshold**: Requires a minimum of 3 consecutive candidate frames before transitioning into `POSSIBLE_PEER_INTERACTION`.
- **Hysteresis Recovery**: Requires 4 consecutive non-sideways frames before clearing the sideways status back to baseline.

---

## 6. Verification & Test Results

### Automated Test Suite
- `tests/api/test_sideways_detection.py`: **8/8 PASSED**
  - `test_person_facing_forward_not_sideways`
  - `test_person_sitting_sideways_foreshortened`
  - `test_person_profile_one_shoulder_occluded`
  - `test_person_turning_upper_body_toward_neighbor`
  - `test_person_facing_away_from_board`
  - `test_side_camera_viewpoint_calibration`
  - `test_heavily_occluded_needs_review_preserved`
  - `test_temporal_stability_and_hysteresis`
- `tests/api/test_activity_recognition.py`: **18/18 PASSED**
- `tests/api/test_activity_analytics.py`: **9/9 PASSED**
- `tests/api/test_vision_endpoints.py`, `test_websocket.py`, `test_video_pipeline_robustness.py`: **58/58 PASSED**

### Real Video Inference
Processed `data/test_classroom.mp4`:
- Successfully identified 45 frames of individual students sitting sideways or turning towards peers.
- Category filters (Orange chip: "Turned sideways (possible interaction)") filter strictly to the sideways bounding boxes in real time.
