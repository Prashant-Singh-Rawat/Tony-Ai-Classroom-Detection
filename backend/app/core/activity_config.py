"""
backend/app/core/activity_config.py — Central Configuration for Observable Activity Labels
==========================================================================================
All user-facing tag text strings, colors, and thresholds reside in this single file
so they can be renamed without touching the underlying computer vision logic.

Strict Scope Boundaries:
- NO facial recognition
- NO identity recognition
- NO emotion recognition
- NO attention/concentration scoring
- NO per-student rankings
- NO automatic disciplinary output
"""

from typing import Dict, Any, List

# ---------------------------------------------------------------------------
# Observable Tag Text Strings (Single Source of Truth)
# ---------------------------------------------------------------------------
TAG_FACING_BOARD = "Facing board"
TAG_HAND_RAISED = "Hand raised"
TAG_HAND_RAISED_LEFT = "Hand raised (Left)"
TAG_HAND_RAISED_RIGHT = "Hand raised (Right)"
TAG_HAND_RAISED_BOTH = "Hand raised (Both)"
TAG_PHONE_VISIBLE = "Phone visible"
TAG_HEAD_DOWN = "Head down"
TAG_TURNED_SIDEWAYS = "Turned sideways (possible interaction)"
TAG_NEEDS_REVIEW = "Needs review"

# ---------------------------------------------------------------------------
# Tag Colors (Strictly matching product specification)
# ---------------------------------------------------------------------------
COLOR_GREEN = "GREEN"     # Facing board
COLOR_BLUE = "BLUE"       # Hand raised
COLOR_RED = "RED"         # Phone visible
COLOR_ORANGE = "ORANGE"   # Head down, Turned sideways
COLOR_YELLOW = "YELLOW"   # Needs review

TAG_COLOR_MAP: Dict[str, str] = {
    TAG_FACING_BOARD: COLOR_GREEN,
    TAG_HAND_RAISED: COLOR_BLUE,
    TAG_HAND_RAISED_LEFT: COLOR_BLUE,
    TAG_HAND_RAISED_RIGHT: COLOR_BLUE,
    TAG_HAND_RAISED_BOTH: COLOR_BLUE,
    TAG_PHONE_VISIBLE: COLOR_RED,
    TAG_HEAD_DOWN: COLOR_ORANGE,
    TAG_TURNED_SIDEWAYS: COLOR_ORANGE,
    TAG_NEEDS_REVIEW: COLOR_YELLOW,
}

# ---------------------------------------------------------------------------
# Temporal Hysteresis & Geometric Thresholds
# ---------------------------------------------------------------------------
HEAD_DOWN_DURATION_THRESHOLD_SEC = 20.0  # Configurable threshold before amber flag (default 20s)
HEAD_DOWN_NOSE_ELEVATION_RATIO = 0.08   # Nose drops near/below shoulder line relative to shoulder width
PHONE_CONSECUTIVE_FRAMES = 3             # Consecutive frames phone object must overlap person
SIDEWAYS_SUSTAINED_FRAMES = 5            # Sustained frames oriented sideways
PEER_INTERACTION_MAX_DIST_RATIO = 2.5    # Max distance between shoulder centroids relative to torso height
HYSTERESIS_SMOOTHING_FRAMES = 3          # Frames required to confirm state transition (anti-flicker)

# Optional Whiteboard / Board Region Calibration (Normalized % [0-100])
WHITEBOARD_DEFAULT_CALIBRATION: Dict[str, Any] = {
    "x1": 20.0,
    "y1": 5.0,
    "x2": 80.0,
    "y2": 35.0,
    "forward_vector": [0.0, -1.0],  # Vector pointing from rear toward board
}
