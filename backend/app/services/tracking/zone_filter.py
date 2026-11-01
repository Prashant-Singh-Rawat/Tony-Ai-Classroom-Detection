"""
backend/app/services/tracking/zone_filter.py — Teacher Zone Exclusion & Spatial ROI Filtering
=============================================================================================
Optional, per-session spatial polygon filtering to distinguish hand-raising events originating
within the instructional area (near blackboard / podium) from student seating areas.

Key Principles:
1. Spatial Origin Only: Polygon containment reflects where a physical action took place.
   It NEVER constitutes biometric identification, face recognition, or proof of identity.
2. Non-Destructive Filtering: Events inside the instructor polygon are marked as INSTRUCTOR_ZONE.
   They are excluded from student participation totals, but the underlying detection record
   is strictly preserved in SQLite.
3. Edge-Case Safety: Ambiguous events (boundary straddling, partial occlusion, noisy bounding boxes)
   are labeled NEEDS_REVIEW rather than being aggressively classified or discarded.
4. Resolution & Aspect-Ratio Invariant: Polygon vertices are normalized in [0.0, 1.0].
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union


class ZoneClassification(str, Enum):
    """Spatial classification of an observed physical event relative to ROI."""

    STUDENT_ZONE = "STUDENT_ZONE"
    INSTRUCTOR_ZONE = "INSTRUCTOR_ZONE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    NOT_CONFIGURED = "NOT_CONFIGURED"


def validate_polygon(
    polygon: Optional[List[Union[List[float], Tuple[float, float]]]],
) -> Tuple[bool, Optional[str]]:
    """
    Validates that a polygon is well-formed with normalized coordinates in [0.0, 1.0].
    Requires at least 3 distinct non-collinear vertices.
    """
    if polygon is None:
        return False, "Polygon is null or None."

    if not isinstance(polygon, (list, tuple)):
        return False, "Polygon must be a list of vertex coordinates."

    if len(polygon) < 3:
        return False, f"Polygon requires at least 3 vertices, got {len(polygon)}."

    cleaned_vertices: List[Tuple[float, float]] = []
    for idx, pt in enumerate(polygon):
        if not isinstance(pt, (list, tuple)) or len(pt) < 2:
            return False, f"Vertex {idx} must be a pair of (x, y) coordinates."
        try:
            x, y = float(pt[0]), float(pt[1])
        except (ValueError, TypeError):
            return False, f"Vertex {idx} coordinates must be numeric floats."

        if not (0.0 <= x <= 1.0) or not (0.0 <= y <= 1.0):
            return False, f"Vertex {idx} ({x}, {y}) out of normalized bounds [0.0, 1.0]."

        cleaned_vertices.append((x, y))

    # Calculate signed area using Shoelace formula to ensure non-degenerate polygon
    n = len(cleaned_vertices)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += cleaned_vertices[i][0] * cleaned_vertices[j][1]
        area -= cleaned_vertices[j][0] * cleaned_vertices[i][1]
    area = abs(area) * 0.5

    if area < 1e-5:
        return False, "Polygon area is degenerate (nearly zero or collinear)."

    return True, None


def point_in_polygon(
    x: float,
    y: float,
    polygon: List[Union[List[float], Tuple[float, float]]],
) -> bool:
    """
    Ray-casting algorithm to test whether a normalized point (x, y) lies inside a polygon.
    Handles arbitrary non-self-intersecting polygons with 3+ vertices.
    """
    n = len(polygon)
    inside = False
    p1x, p1y = float(polygon[0][0]), float(polygon[0][1])

    for i in range(1, n + 1):
        p2x, p2y = float(polygon[i % n][0]), float(polygon[i % n][1])
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def point_to_segment_distance(
    px: float, py: float, x1: float, y1: float, x2: float, y2: float
) -> float:
    """Calculates the Euclidean distance from point (px, py) to line segment (x1, y1)-(x2, y2)."""
    dx = x2 - x1
    dy = y2 - y1
    segment_len_sq = dx * dx + dy * dy

    if segment_len_sq == 0.0:
        return math.hypot(px - x1, py - y1)

    # Project point onto line segment, clamping t to [0.0, 1.0]
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / segment_len_sq))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy

    return math.hypot(px - proj_x, py - proj_y)


def min_distance_to_polygon_boundary(
    x: float,
    y: float,
    polygon: List[Union[List[float], Tuple[float, float]]],
) -> float:
    """Computes minimum Euclidean distance from normalized point (x, y) to any polygon boundary segment."""
    n = len(polygon)
    min_dist = float("inf")
    for i in range(n):
        j = (i + 1) % n
        x1, y1 = float(polygon[i][0]), float(polygon[i][1])
        x2, y2 = float(polygon[j][0]), float(polygon[j][1])
        dist = point_to_segment_distance(x, y, x1, y1, x2, y2)
        if dist < min_dist:
            min_dist = dist
    return min_dist


def classify_detection_zone(
    bbox: Any,
    polygon: Optional[List[Union[List[float], Tuple[float, float]]]] = None,
    enabled: bool = True,
    video_width: Optional[int] = None,
    video_height: Optional[int] = None,
    confidence: float = 0.85,
    is_occluded: bool = False,
    boundary_margin: float = 0.025,
) -> Tuple[ZoneClassification, Dict[str, Any]]:
    """
    Classifies a detected bounding box relative to the instructor ROI polygon.

    Parameters:
    - bbox: Dict or object with x, y, width/w, height/h (either [0-1] normalized or pixel coords).
    - polygon: Normalized polygon [[x1, y1], [x2, y2], ...] or None.
    - enabled: Whether zone filtering is active for this session.
    - video_width, video_height: Frame resolution for normalization if bbox is in pixels.
    - confidence: Detector confidence score.
    - is_occluded: Tracking occlusion flag.
    - boundary_margin: Normalized buffer width within which boundary crossings trigger NEEDS_REVIEW.

    Returns:
    - (ZoneClassification, evidence_dict)
    """
    if not enabled or polygon is None:
        return ZoneClassification.NOT_CONFIGURED, {
            "status": "filtering_disabled",
            "reason": "Zone filtering disabled or polygon not configured",
        }

    valid, err_msg = validate_polygon(polygon)
    if not valid:
        return ZoneClassification.NOT_CONFIGURED, {
            "status": "invalid_polygon",
            "error": err_msg,
        }

    # Extract coordinates from bbox
    if isinstance(bbox, dict):
        bx = float(bbox.get("x1", bbox.get("x", 0.0)))
        by = float(bbox.get("y1", bbox.get("y", 0.0)))
        bw = float(bbox.get("width", bbox.get("w", 0.0)))
        bh = float(bbox.get("height", bbox.get("h", 0.0)))
        if "confidence" in bbox and bbox["confidence"] is not None:
            confidence = float(bbox["confidence"])
    else:
        bx = float(getattr(bbox, "x1", getattr(bbox, "x", 0.0)) or 0.0)
        by = float(getattr(bbox, "y1", getattr(bbox, "y", 0.0)) or 0.0)
        bw = float(getattr(bbox, "width", getattr(bbox, "w", 0.0)) or 0.0)
        bh = float(getattr(bbox, "height", getattr(bbox, "h", 0.0)) or 0.0)
        if hasattr(bbox, "confidence") and getattr(bbox, "confidence") is not None:
            confidence = float(getattr(bbox, "confidence"))

    # Convert coordinates to normalized [0.0, 1.0]
    vw = float(video_width) if video_width and video_width > 0 else 1.0
    vh = float(video_height) if video_height and video_height > 0 else 1.0

    # Auto-infer 640x480 resolution if absolute pixels (>100) are detected without explicit dimensions
    if (bx > 100.0 or by > 100.0 or bw > 100.0 or bh > 100.0) and vw == 1.0:
        vw = 640.0
        vh = 480.0

    # Check if bbox is percentage [0-100] or absolute pixels or already normalized [0-1]
    if bx > 1.0 or by > 1.0 or bw > 1.0 or bh > 1.0:
        if vw > 1.0 and (bx > 100.0 or bw > 100.0 or vw > 100.0):
            # Absolute pixel coordinates
            nx = bx / vw
            ny = by / vh
            nw = bw / vw
            nh = bh / vh
        else:
            # Percentage coordinates [0-100]
            nx = bx / 100.0
            ny = by / 100.0
            nw = bw / 100.0
            nh = bh / 100.0
    else:
        nx, ny, nw, nh = bx, by, bw, bh

    # Clamp bounding box
    nx = max(0.0, min(1.0, nx))
    ny = max(0.0, min(1.0, ny))
    nw = max(0.001, min(1.0 - nx, nw))
    nh = max(0.001, min(1.0 - ny, nh))

    # Edge Case: Missing or uncertain bounding boxes
    if nw < 0.01 or nh < 0.01 or confidence < 0.25 or is_occluded:
        return ZoneClassification.NEEDS_REVIEW, {
            "reason": "uncertain_bounding_box",
            "confidence": round(confidence, 3),
            "is_occluded": is_occluded,
            "box_dims": [round(nw, 4), round(nh, 4)],
        }

    # Key spatial evaluation points
    centroid_x = nx + (nw / 2.0)
    centroid_y = ny + (nh / 2.0)
    base_x = centroid_x
    base_y = ny + nh  # Floor contact point (standing point)

    # Sample a 3x3 grid across the bounding box to evaluate spatial containment ratio
    grid_points = []
    for gx in (nx + 0.1 * nw, nx + 0.5 * nw, nx + 0.9 * nw):
        for gy in (ny + 0.1 * nh, ny + 0.5 * nh, ny + 0.9 * nh):
            grid_points.append((gx, gy))

    inside_count = sum(1 for (gx, gy) in grid_points if point_in_polygon(gx, gy, polygon))
    containment_ratio = inside_count / float(len(grid_points))

    centroid_inside = point_in_polygon(centroid_x, centroid_y, polygon)
    base_inside = point_in_polygon(base_x, base_y, polygon)
    boundary_dist = min_distance_to_polygon_boundary(centroid_x, centroid_y, polygon)

    evidence: Dict[str, Any] = {
        "containment_ratio": round(containment_ratio, 3),
        "centroid_inside": centroid_inside,
        "base_inside": base_inside,
        "boundary_dist": round(boundary_dist, 4),
        "normalized_bbox": [round(nx, 3), round(ny, 3), round(nw, 3), round(nh, 3)],
        "spatial_disclaimer": "Spatial origin only; does NOT verify individual identity or prove teacher status.",
    }

    # Decision Matrix:
    # 1. Clear Instructor Zone: Dominant containment AND centroid inside with safe boundary margin
    if containment_ratio >= 0.65 and (centroid_inside or base_inside) and boundary_dist >= boundary_margin:
        evidence["classification"] = ZoneClassification.INSTRUCTOR_ZONE.value
        return ZoneClassification.INSTRUCTOR_ZONE, evidence

    # 2. Clear Student Zone: Minimal or zero containment AND centroid outside with safe margin
    if containment_ratio <= 0.15 and not centroid_inside and boundary_dist >= boundary_margin:
        evidence["classification"] = ZoneClassification.STUDENT_ZONE.value
        return ZoneClassification.STUDENT_ZONE, evidence

    # 3. Edge Case: Boundary Straddling, Near-Edge, or Split Containment -> NEEDS_REVIEW
    # (e.g. Student in front row near blackboard, teacher stepping across line, tilted camera boundary)
    evidence["classification"] = ZoneClassification.NEEDS_REVIEW.value
    evidence["review_reason"] = (
        "boundary_straddling" if (0.15 < containment_ratio < 0.65) else "near_boundary_margin"
    )
    return ZoneClassification.NEEDS_REVIEW, evidence
