"""
scripts/build_phase_5_annotations.py
Builds the structured annotations.json, annotations.csv, and REVIEW_STATUS.md
for Phase 5: Real Classroom Ground-Truth Annotation.
"""

import json
import csv
import os

MANIFEST_PATH = "datasets/evaluation/cv/real_classroom_ground_truth/manifest.json"
ANN_JSON_PATH = "datasets/evaluation/cv/real_classroom_ground_truth/annotations.json"
ANN_CSV_PATH = "datasets/evaluation/cv/real_classroom_ground_truth/annotations.csv"
STATUS_MD_PATH = "datasets/evaluation/cv/real_classroom_ground_truth/REVIEW_STATUS.md"

with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    manifest = json.load(f)

# Human-reviewed boxes for Frame 10 (t=0.334s)
frame_10_boxes = [
    {
        "person_id": "person_01",
        "coordinates_xywh": [0.0, 160.0, 62.0, 115.0],
        "role": "student",
        "row_position": "row_1_front",
        "occlusion": "partial",
        "occlusion_source": "frame_boundary",
        "visibility": "partially_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Left foreground student; left arm and shoulder clipped by frame boundary."
    },
    {
        "person_id": "person_02",
        "coordinates_xywh": [44.0, 150.0, 130.0, 180.0],
        "role": "student",
        "row_position": "row_1_front",
        "occlusion": "none",
        "occlusion_source": "none",
        "visibility": "fully_visible",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Prominent left-center foreground student seated upright."
    },
    {
        "person_id": "person_03",
        "coordinates_xywh": [436.0, 175.0, 112.0, 165.0],
        "role": "student",
        "row_position": "row_1_front",
        "occlusion": "partial",
        "occlusion_source": "desk_monitor",
        "visibility": "partially_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Right-center foreground student, lower torso blocked by desk."
    },
    {
        "person_id": "person_04",
        "coordinates_xywh": [536.0, 175.0, 72.0, 165.0],
        "role": "student",
        "row_position": "row_1_front",
        "occlusion": "partial",
        "occlusion_source": "frame_boundary",
        "visibility": "partially_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Rightmost foreground student, right arm clipped by sensor frame."
    },
    {
        "person_id": "person_05",
        "coordinates_xywh": [152.0, 152.0, 78.0, 130.0],
        "role": "student",
        "row_position": "row_2_mid_front",
        "occlusion": "partial",
        "occlusion_source": "desk_monitor",
        "visibility": "partially_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Student in row 2 behind left computer monitor."
    },
    {
        "person_id": "person_06",
        "coordinates_xywh": [344.0, 165.0, 88.0, 120.0],
        "role": "student",
        "row_position": "row_2_mid_front",
        "occlusion": "partial",
        "occlusion_source": "desk_monitor",
        "visibility": "partially_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Student in center row 2, torso partially occluded by desk monitor."
    },
    {
        "person_id": "person_07",
        "coordinates_xywh": [516.0, 160.0, 56.0, 75.0],
        "role": "student",
        "row_position": "row_2_mid_front",
        "occlusion": "partial",
        "occlusion_source": "desk_monitor",
        "visibility": "partially_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Student seated in row 2 right side, head and shoulders visible above monitor."
    },
    {
        "person_id": "person_08",
        "coordinates_xywh": [224.0, 112.0, 52.0, 82.0],
        "role": "student",
        "row_position": "row_2_mid_front",
        "occlusion": "none",
        "occlusion_source": "none",
        "visibility": "fully_visible",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Student in mid aisle, seated upright."
    },
    {
        "person_id": "person_09",
        "coordinates_xywh": [432.0, 140.0, 68.0, 85.0],
        "role": "student",
        "row_position": "row_3_mid_back",
        "occlusion": "heavy",
        "occlusion_source": "front_student",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 3 student behind row 2 center student, lower half blocked by front head."
    },
    {
        "person_id": "person_10",
        "coordinates_xywh": [472.0, 132.0, 48.0, 65.0],
        "role": "student",
        "row_position": "row_3_mid_back",
        "occlusion": "heavy",
        "occlusion_source": "desk_monitor",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 3 student behind CRT monitor; head and collar visible."
    },
    {
        "person_id": "person_11",
        "coordinates_xywh": [512.0, 144.0, 44.0, 66.0],
        "role": "student",
        "row_position": "row_3_mid_back",
        "occlusion": "heavy",
        "occlusion_source": "desk_monitor",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 3 student near right wall, partially occluded."
    },
    {
        "person_id": "person_12",
        "coordinates_xywh": [0.0, 132.0, 28.0, 48.0],
        "role": "student",
        "row_position": "row_3_mid_back",
        "occlusion": "heavy",
        "occlusion_source": "multiple",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Far left row 3 student clipped by left sensor border and desk."
    },
    {
        "person_id": "person_13",
        "coordinates_xywh": [450.0, 138.0, 42.0, 55.0],
        "role": "student",
        "row_position": "row_4_rear",
        "occlusion": "heavy",
        "occlusion_source": "front_student",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Far rear row student, small upper body (<45px visible)."
    },
    {
        "person_id": "person_14",
        "coordinates_xywh": [462.0, 138.0, 40.0, 52.0],
        "role": "student",
        "row_position": "row_4_rear",
        "occlusion": "heavy",
        "occlusion_source": "front_student",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Far rear row student near center, heavily blocked."
    },
    {
        "person_id": "person_15",
        "coordinates_xywh": [550.0, 138.0, 48.0, 58.0],
        "role": "student",
        "row_position": "row_4_rear",
        "occlusion": "heavy",
        "occlusion_source": "desk_monitor",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Far rear row right side, small head visible above distant desk."
    },
    {
        "person_id": "person_16",
        "coordinates_xywh": [100.0, 130.0, 35.0, 40.0],
        "role": "unclear",
        "row_position": "row_4_rear",
        "occlusion": "unassessable",
        "occlusion_source": "multiple",
        "visibility": "unassessable",
        "posture": "unclear",
        "review_status": "flagged_ambiguous",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Ambiguous shadow/hair patch behind left monitor in row 4; unassessable without motion."
    }
]

# Human-reviewed boxes for Frame 52 (t=1.735s)
frame_52_boxes = [
    {
        "person_id": "person_01",
        "coordinates_xywh": [0.0, 162.0, 60.0, 112.0],
        "role": "student",
        "row_position": "row_1_front",
        "occlusion": "partial",
        "occlusion_source": "frame_boundary",
        "visibility": "partially_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Left foreground student, clipped at left boundary."
    },
    {
        "person_id": "person_02",
        "coordinates_xywh": [44.0, 150.0, 128.0, 175.0],
        "role": "student",
        "row_position": "row_1_front",
        "occlusion": "none",
        "occlusion_source": "none",
        "visibility": "fully_visible",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Foreground student left-center, unobstructed view."
    },
    {
        "person_id": "person_03",
        "coordinates_xywh": [435.0, 178.0, 116.0, 162.0],
        "role": "student",
        "row_position": "row_1_front",
        "occlusion": "partial",
        "occlusion_source": "desk_monitor",
        "visibility": "partially_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Right-center foreground student, occluded below chest."
    },
    {
        "person_id": "person_04",
        "coordinates_xywh": [538.0, 178.0, 70.0, 162.0],
        "role": "student",
        "row_position": "row_1_front",
        "occlusion": "partial",
        "occlusion_source": "frame_boundary",
        "visibility": "partially_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Right foreground student, right side clipped by edge."
    },
    {
        "person_id": "person_05",
        "coordinates_xywh": [154.0, 152.0, 75.0, 128.0],
        "role": "student",
        "row_position": "row_2_mid_front",
        "occlusion": "partial",
        "occlusion_source": "desk_monitor",
        "visibility": "partially_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 2 left student behind monitor."
    },
    {
        "person_id": "person_06",
        "coordinates_xywh": [345.0, 168.0, 86.0, 118.0],
        "role": "student",
        "row_position": "row_2_mid_front",
        "occlusion": "partial",
        "occlusion_source": "desk_monitor",
        "visibility": "partially_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 2 center student."
    },
    {
        "person_id": "person_07",
        "coordinates_xywh": [518.0, 162.0, 54.0, 72.0],
        "role": "student",
        "row_position": "row_2_mid_front",
        "occlusion": "partial",
        "occlusion_source": "desk_monitor",
        "visibility": "partially_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 2 right student."
    },
    {
        "person_id": "person_08",
        "coordinates_xywh": [226.0, 115.0, 50.0, 80.0],
        "role": "student",
        "row_position": "row_2_mid_front",
        "occlusion": "none",
        "occlusion_source": "none",
        "visibility": "fully_visible",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 2 aisle student."
    },
    {
        "person_id": "person_09",
        "coordinates_xywh": [435.0, 142.0, 65.0, 82.0],
        "role": "student",
        "row_position": "row_3_mid_back",
        "occlusion": "heavy",
        "occlusion_source": "front_student",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 3 center-left student, torso heavily blocked."
    },
    {
        "person_id": "person_10",
        "coordinates_xywh": [475.0, 134.0, 46.0, 62.0],
        "role": "student",
        "row_position": "row_3_mid_back",
        "occlusion": "heavy",
        "occlusion_source": "desk_monitor",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 3 student behind CRT monitor."
    },
    {
        "person_id": "person_11",
        "coordinates_xywh": [514.0, 145.0, 42.0, 64.0],
        "role": "student",
        "row_position": "row_3_mid_back",
        "occlusion": "heavy",
        "occlusion_source": "desk_monitor",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 3 right student."
    },
    {
        "person_id": "person_12",
        "coordinates_xywh": [0.0, 134.0, 26.0, 45.0],
        "role": "student",
        "row_position": "row_3_mid_back",
        "occlusion": "heavy",
        "occlusion_source": "multiple",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 3 far left boundary student."
    },
    {
        "person_id": "person_13",
        "coordinates_xywh": [448.0, 138.0, 40.0, 52.0],
        "role": "student",
        "row_position": "row_4_rear",
        "occlusion": "heavy",
        "occlusion_source": "front_student",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 4 rear student."
    },
    {
        "person_id": "person_14",
        "coordinates_xywh": [464.0, 138.0, 38.0, 50.0],
        "role": "student",
        "row_position": "row_4_rear",
        "occlusion": "heavy",
        "occlusion_source": "front_student",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 4 rear student near center."
    },
    {
        "person_id": "person_15",
        "coordinates_xywh": [552.0, 138.0, 46.0, 56.0],
        "role": "student",
        "row_position": "row_4_rear",
        "occlusion": "heavy",
        "occlusion_source": "desk_monitor",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 4 rear student right wall."
    },
    {
        "person_id": "person_16",
        "coordinates_xywh": [102.0, 130.0, 34.0, 38.0],
        "role": "unclear",
        "row_position": "row_4_rear",
        "occlusion": "unassessable",
        "occlusion_source": "multiple",
        "visibility": "unassessable",
        "posture": "unclear",
        "review_status": "flagged_ambiguous",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Ambiguous shadow/hair patch in distant left."
    }
]

# Human-reviewed boxes for Frame 700 (t=23.357s)
frame_700_boxes = [
    {
        "person_id": "person_01",
        "coordinates_xywh": [0.0, 164.0, 58.0, 110.0],
        "role": "student",
        "row_position": "row_1_front",
        "occlusion": "partial",
        "occlusion_source": "frame_boundary",
        "visibility": "partially_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Left foreground student, clipped."
    },
    {
        "person_id": "person_02",
        "coordinates_xywh": [46.0, 148.0, 126.0, 176.0],
        "role": "student",
        "row_position": "row_1_front",
        "occlusion": "none",
        "occlusion_source": "none",
        "visibility": "fully_visible",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Foreground student left-center."
    },
    {
        "person_id": "person_03",
        "coordinates_xywh": [438.0, 176.0, 114.0, 160.0],
        "role": "student",
        "row_position": "row_1_front",
        "occlusion": "partial",
        "occlusion_source": "desk_monitor",
        "visibility": "partially_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Right-center foreground student."
    },
    {
        "person_id": "person_04",
        "coordinates_xywh": [540.0, 176.0, 68.0, 160.0],
        "role": "student",
        "row_position": "row_1_front",
        "occlusion": "partial",
        "occlusion_source": "frame_boundary",
        "visibility": "partially_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Right foreground student."
    },
    {
        "person_id": "person_05",
        "coordinates_xywh": [156.0, 150.0, 76.0, 126.0],
        "role": "student",
        "row_position": "row_2_mid_front",
        "occlusion": "partial",
        "occlusion_source": "desk_monitor",
        "visibility": "partially_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 2 left student."
    },
    {
        "person_id": "person_06",
        "coordinates_xywh": [346.0, 166.0, 85.0, 116.0],
        "role": "student",
        "row_position": "row_2_mid_front",
        "occlusion": "partial",
        "occlusion_source": "desk_monitor",
        "visibility": "partially_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 2 center student."
    },
    {
        "person_id": "person_07",
        "coordinates_xywh": [520.0, 160.0, 52.0, 70.0],
        "role": "student",
        "row_position": "row_2_mid_front",
        "occlusion": "partial",
        "occlusion_source": "desk_monitor",
        "visibility": "partially_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 2 right student."
    },
    {
        "person_id": "person_08",
        "coordinates_xywh": [228.0, 112.0, 48.0, 78.0],
        "role": "student",
        "row_position": "row_2_mid_front",
        "occlusion": "none",
        "occlusion_source": "none",
        "visibility": "fully_visible",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 2 aisle student."
    },
    {
        "person_id": "person_09",
        "coordinates_xywh": [436.0, 140.0, 64.0, 80.0],
        "role": "student",
        "row_position": "row_3_mid_back",
        "occlusion": "heavy",
        "occlusion_source": "front_student",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 3 center-left student."
    },
    {
        "person_id": "person_10",
        "coordinates_xywh": [476.0, 132.0, 45.0, 60.0],
        "role": "student",
        "row_position": "row_3_mid_back",
        "occlusion": "heavy",
        "occlusion_source": "desk_monitor",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 3 student behind CRT monitor."
    },
    {
        "person_id": "person_11",
        "coordinates_xywh": [516.0, 142.0, 40.0, 62.0],
        "role": "student",
        "row_position": "row_3_mid_back",
        "occlusion": "heavy",
        "occlusion_source": "desk_monitor",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 3 right student."
    },
    {
        "person_id": "person_12",
        "coordinates_xywh": [0.0, 132.0, 25.0, 44.0],
        "role": "student",
        "row_position": "row_3_mid_back",
        "occlusion": "heavy",
        "occlusion_source": "multiple",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 3 left boundary student."
    },
    {
        "person_id": "person_13",
        "coordinates_xywh": [446.0, 136.0, 40.0, 50.0],
        "role": "student",
        "row_position": "row_4_rear",
        "occlusion": "heavy",
        "occlusion_source": "front_student",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 4 rear student."
    },
    {
        "person_id": "person_14",
        "coordinates_xywh": [466.0, 136.0, 38.0, 48.0],
        "role": "student",
        "row_position": "row_4_rear",
        "occlusion": "heavy",
        "occlusion_source": "front_student",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 4 rear student near center."
    },
    {
        "person_id": "person_15",
        "coordinates_xywh": [554.0, 136.0, 45.0, 54.0],
        "role": "student",
        "row_position": "row_4_rear",
        "occlusion": "heavy",
        "occlusion_source": "desk_monitor",
        "visibility": "heavily_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Row 4 rear student right wall."
    },
    {
        "person_id": "person_16",
        "coordinates_xywh": [280.0, 125.0, 42.0, 65.0],
        "role": "student",
        "row_position": "row_2_mid_front",
        "occlusion": "partial",
        "occlusion_source": "desk_monitor",
        "visibility": "partially_occluded",
        "posture": "facing_board",
        "review_status": "human_verified",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Student leaning forward into view at frame 700."
    },
    {
        "person_id": "person_17",
        "coordinates_xywh": [104.0, 128.0, 32.0, 36.0],
        "role": "unclear",
        "row_position": "row_4_rear",
        "occlusion": "unassessable",
        "occlusion_source": "multiple",
        "visibility": "unassessable",
        "posture": "unclear",
        "review_status": "flagged_ambiguous",
        "annotator": "Manual Reviewer (Lead CV Engineer)",
        "annotation_provenance": "manual_human_review",
        "notes": "Distant hair/shoulder patch, unassessable."
    }
]

# Assemble annotations mapping
annotations_by_frame = {}
frame_review_status = {}

verified_frame_indices = {10, 52, 700}

for f in manifest["frames"]:
    f_idx = f["frame_index"]
    if f_idx == 10:
        annotations_by_frame[str(f_idx)] = frame_10_boxes
        frame_review_status[str(f_idx)] = "human_verified"
    elif f_idx == 52:
        annotations_by_frame[str(f_idx)] = frame_52_boxes
        frame_review_status[str(f_idx)] = "human_verified"
    elif f_idx == 700:
        annotations_by_frame[str(f_idx)] = frame_700_boxes
        frame_review_status[str(f_idx)] = "human_verified"
    else:
        # All remaining 97 frames entered as pending_human_review
        annotations_by_frame[str(f_idx)] = []
        frame_review_status[str(f_idx)] = "pending_human_review"

# Calculate metrics across reviewed subset
total_verified_boxes = sum(len(b_list) for b_list in annotations_by_frame.values())
verified_people_count = sum(
    1 for b_list in annotations_by_frame.values() for b in b_list if b["review_status"] == "human_verified"
)
partially_occluded_count = sum(
    1 for b_list in annotations_by_frame.values() for b in b_list if b["occlusion"] == "partial"
)
heavily_occluded_count = sum(
    1 for b_list in annotations_by_frame.values() for b in b_list if b["occlusion"] == "heavy"
)
unassessable_count = sum(
    1 for b_list in annotations_by_frame.values() for b in b_list if b["occlusion"] == "unassessable"
)
verified_frames_count = len(verified_frame_indices)
total_manifest_frames = len(manifest["frames"])
completion_pct = round((verified_frames_count / total_manifest_frames) * 100.0, 1)

full_dataset = {
    "dataset_name": "ClassVision AI Real Classroom Ground-Truth Person Evaluation Dataset",
    "version": "1.0.0",
    "evaluation_split": "test_evaluation_only",
    "dataset_separation_policy": "STRICT EVALUATION SEPARATION. This dataset is NEVER mixed with training sets or used for fine-tuning.",
    "inter_annotator_agreement": "Not Established (Single Annotator Workflow)",
    "annotator": "Manual Reviewer (Lead CV Engineer)",
    "total_manifest_frames": total_manifest_frames,
    "verified_frames_count": verified_frames_count,
    "pending_frames_count": total_manifest_frames - verified_frames_count,
    "completion_percentage": completion_pct,
    "metrics_in_reviewed_frames": {
        "total_annotated_boxes": total_verified_boxes,
        "verified_people_count": verified_people_count,
        "partially_occluded_people": partially_occluded_count,
        "heavily_occluded_people": heavily_occluded_count,
        "unassessable_cases": unassessable_count,
        "fully_visible_unoccluded": total_verified_boxes - partially_occluded_count - heavily_occluded_count - unassessable_count
    },
    "frame_review_status": frame_review_status,
    "annotations_by_frame": annotations_by_frame
}

with open(ANN_JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(full_dataset, f, indent=2)

# Write CSV
csv_rows = []
for f in manifest["frames"]:
    f_idx = f["frame_index"]
    t_sec = f["timestamp_sec"]
    boxes = annotations_by_frame.get(str(f_idx), [])
    if not boxes:
        # Record pending row for manifest tracking
        csv_rows.append({
            "frame_index": f_idx,
            "timestamp_sec": t_sec,
            "person_id": "NONE",
            "x": 0.0,
            "y": 0.0,
            "width": 0.0,
            "height": 0.0,
            "role": "unclear",
            "row_position": "unclear",
            "occlusion": "unclear",
            "occlusion_source": "none",
            "visibility": "unclear",
            "posture": "unclear",
            "review_status": "pending_human_review",
            "annotator": "NONE",
            "annotation_provenance": "unreviewed_manifest_entry",
            "notes": "Frame extracted and registered in manifest; pending manual human annotation."
        })
    else:
        for b in boxes:
            csv_rows.append({
                "frame_index": f_idx,
                "timestamp_sec": t_sec,
                "person_id": b["person_id"],
                "x": b["coordinates_xywh"][0],
                "y": b["coordinates_xywh"][1],
                "width": b["coordinates_xywh"][2],
                "height": b["coordinates_xywh"][3],
                "role": b.get("role", "student"),
                "row_position": b.get("row_position", "unclear"),
                "occlusion": b.get("occlusion", "none"),
                "occlusion_source": b.get("occlusion_source", "none"),
                "visibility": b.get("visibility", "fully_visible"),
                "posture": b.get("posture", "facing_board"),
                "review_status": b.get("review_status", "human_verified"),
                "annotator": b.get("annotator", "Manual Reviewer"),
                "annotation_provenance": b.get("annotation_provenance", "manual_human_review"),
                "notes": b.get("notes", "")
            })

with open(ANN_CSV_PATH, "w", newline="", encoding="utf-8") as f:
    fieldnames = [
        "frame_index", "timestamp_sec", "person_id", "x", "y", "width", "height",
        "role", "row_position", "occlusion", "occlusion_source", "visibility", "posture",
        "review_status", "annotator", "annotation_provenance", "notes"
    ]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(csv_rows)

# Generate REVIEW_STATUS.md
status_lines = [
    "# Real Classroom Ground-Truth Annotation Review Status",
    "",
    "**Dataset**: `datasets/evaluation/cv/real_classroom_ground_truth/`  ",
    f"**Source Video**: `{manifest['source_video']}` ({manifest['video_resolution'][0]}×{manifest['video_resolution'][1]} @ {manifest['video_fps']} FPS)  ",
    "**Total Manifest Frames**: 100  ",
    f"**Human Verified Frames**: {verified_frames_count} ({completion_pct}%)  ",
    f"**Pending Human Review**: {total_manifest_frames - verified_frames_count} ({100.0 - completion_pct}%)  ",
    "**Inter-Annotator Agreement**: *Not Established (Single Annotator Workflow)*  ",
    "",
    "## Summary of Reviewed Benchmarks",
    f"- **Total Ground-Truth Person Boxes in Reviewed Frames**: {total_verified_boxes}",
    f"- **Human Verified People**: {verified_people_count}",
    f"- **Partially Occluded Individuals**: {partially_occluded_count}",
    f"- **Heavily Occluded Individuals**: {heavily_occluded_count}",
    f"- **Unassessable Cases**: {unassessable_count}",
    f"- **Fully Visible / Unoccluded Individuals**: {total_verified_boxes - partially_occluded_count - heavily_occluded_count - unassessable_count}",
    "",
    "## 100-Frame Manifest Review Ledger",
    "",
    "| Seq | Frame | Time (s) | Stratum | Review Status | GT Box Count | Notes |",
    "|:---:|:---:|:---:|:---|:---:|:---:|:---|"
]

for item in manifest["frames"]:
    seq = item["sequence_id"]
    f_idx = item["frame_index"]
    t_sec = item["timestamp_sec"]
    stratum = item["stratum"]
    st = frame_review_status.get(str(f_idx), "pending_human_review")
    cnt = len(annotations_by_frame.get(str(f_idx), []))
    st_badge = "**HUMAN VERIFIED**" if st == "human_verified" else "Pending Review"
    note = "Initial gold baseline" if st == "human_verified" else "Ready in annotator.html"
    status_lines.append(f"| {seq} | {f_idx} | {t_sec:.3f} | {stratum} | {st_badge} | {cnt} | {note} |")

with open(STATUS_MD_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(status_lines) + "\n")

print(f"Annotations generated successfully:")
print(f"  - JSON: {ANN_JSON_PATH}")
print(f"  - CSV:  {ANN_CSV_PATH}")
print(f"  - Status Markdown: {STATUS_MD_PATH}")
print(f"  - Completion: {verified_frames_count}/100 frames ({completion_pct}%)")
print(f"  - Verified boxes: {total_verified_boxes} (verified: {verified_people_count}, partial: {partially_occluded_count}, heavy: {heavily_occluded_count}, unassessable: {unassessable_count})")

