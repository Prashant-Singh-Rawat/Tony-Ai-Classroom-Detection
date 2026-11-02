"""
scripts/patch_false_sideways_fix.py
Clean string replacement patch.
"""

from pathlib import Path

target_file = Path("backend/app/services/activity_recognition/service.py")
content = target_file.read_text(encoding="utf-8")

# Let's inspect the exact lines around _detect_peer_orientations and _evaluate_turned_sideways
start_peer = content.find("    def _detect_peer_orientations(")
end_peer = content.find("    # ---------------------------------------------------------------------------", start_peer)

new_peer_block = '''    def _detect_peer_orientations(
        self,
        person_boxes: List[BoundingBox],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Identifies pairs of tracked persons who are:
        1. In spatial proximity (adjacent desks/benches).
        2. Mutually oriented towards each other (converging head/shoulder angles).
        Strictly verifies that neither person is firmly facing the board.
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

                # Check horizontal interaction distance (focused on adjacent desk)
                dx = abs(c1_x - c2_x)
                dy = abs(c1_y - c2_y)
                max_interaction_dx = (b1.w + b2.w) * 1.15
                max_interaction_dy = (b1.h + b2.h) * 0.35

                if dx > max_interaction_dx or dy > max_interaction_dy:
                    continue

                # Determine which person is on the left vs right
                left_person = b1 if c1_x < c2_x else b2
                right_person = b2 if c1_x < c2_x else b1

                # Check head/shoulder orientation convergence
                left_facing_right = self._is_facing_right(left_person)
                right_facing_left = self._is_facing_left(right_person)

                if left_facing_right and right_facing_left:
                    # Mutual convergence: both turned to each other
                    metrics = {"peerDistanceDx": round(dx, 1), "peerDistanceDy": round(dy, 1)}
                    candidates[left_person.id] = {"peerId": right_person.id, "metrics": metrics}
                    candidates[right_person.id] = {"peerId": left_person.id, "metrics": metrics}

        return candidates

    def _is_facing_right(self, box: BoundingBox) -> bool:
        """Determines if a person's upper body / head is genuinely oriented to the right."""
        if not box.keypoints:
            return False
        kp_map = {kp.name: kp for kp in box.keypoints}
        nose = kp_map.get("nose")
        l_sh = kp_map.get("left_shoulder")
        r_sh = kp_map.get("right_shoulder")
        if not (nose and l_sh and r_sh and nose.confidence >= 0.40 and l_sh.confidence >= 0.30 and r_sh.confidence >= 0.30):
            return False

        # Guard: If student's torso is broadly facing the board, they are not turned to a peer
        is_fb, align, _ = self._evaluate_facing_board(box, kp_map)
        sh_span = abs(r_sh.x - l_sh.x)
        if align >= 0.65 and sh_span > 14.0:
            return False

        mid_x = (l_sh.x + r_sh.x) / 2.0
        min_offset = max(6.0, 0.35 * (sh_span / 2.0))
        return (nose.x - mid_x) > min_offset

    def _is_facing_left(self, box: BoundingBox) -> bool:
        """Determines if a person's upper body / head is genuinely oriented to the left."""
        if not box.keypoints:
            return False
        kp_map = {kp.name: kp for kp in box.keypoints}
        nose = kp_map.get("nose")
        l_sh = kp_map.get("left_shoulder")
        r_sh = kp_map.get("right_shoulder")
        if not (nose and l_sh and r_sh and nose.confidence >= 0.40 and l_sh.confidence >= 0.30 and r_sh.confidence >= 0.30):
            return False

        # Guard: If student's torso is broadly facing the board, they are not turned to a peer
        is_fb, align, _ = self._evaluate_facing_board(box, kp_map)
        sh_span = abs(r_sh.x - l_sh.x)
        if align >= 0.65 and sh_span > 14.0:
            return False

        mid_x = (l_sh.x + r_sh.x) / 2.0
        min_offset = max(6.0, 0.35 * (sh_span / 2.0))
        return (mid_x - nose.x) > min_offset

'''

assert start_peer != -1 and end_peer != -1, "Could not find peer block"
content = content[:start_peer] + new_peer_block + content[end_peer:]

# Now replace the branches in _evaluate_turned_sideways
start_sw = content.find("            # Forward Guard:")
if start_sw == -1:
    start_sw = content.find("            # A. Facing Away from Board")
assert start_sw != -1, "Could not find start_sw"

end_sw = content.find("        # Case 2: Asymmetric Shoulder Profile View", start_sw)
assert end_sw != -1, "Could not find end_sw"

new_sw_branches = '''            mean_sh_conf = (ls_conf + rs_conf) / 2.0

            # A. Facing Away from Board (alignment < -0.25)
            if alignment < -0.25 and mean_sh_conf >= 0.28:
                ev = ActivityEvidence(
                    detectorUsed="YOLOv8n-pose Torso Vector",
                    observedFeatures=["Torso facing away from whiteboard", f"Antiparallel board alignment ({alignment:.2f})"],
                    geometryMetrics={"alignmentScore": round(alignment, 3), "foreshorteningRatio": round(ratio_torso, 3)},
                    rationale=f"Body oriented away from classroom board into rear classroom (alignment {alignment:.2f}).",
                )
                return True, round(max(ls_conf, rs_conf), 2), ev

            # B. Heavy Torso Foreshortening (shoulders/hips compressed horizontally from sideways seating)
            if ratio_torso < 0.58 and mean_sh_conf >= 0.28:
                ev = ActivityEvidence(
                    detectorUsed="YOLOv8n-pose Torso Foreshortening",
                    observedFeatures=["Horizontal shoulder span foreshortened", f"Torso foreshortening ratio {ratio_torso:.2f} < 0.58"],
                    geometryMetrics={"foreshorteningRatio": round(ratio_torso, 3), "alignmentScore": round(alignment, 3)},
                    rationale=f"Torso foreshortened sideways (ratio: {ratio_torso:.2f} < 0.58). Seated sideways in desk.",
                )
                return True, 0.85, ev

            # C. Steep Shoulder Tilt with moderate foreshortening (perspective yaw angle)
            if sh_tilt_deg > 32.0 and ratio_sh < 0.72 and mean_sh_conf >= 0.30:
                ev = ActivityEvidence(
                    detectorUsed="YOLOv8n-pose Shoulder Axis Tilt",
                    observedFeatures=[f"Shoulder axis tilted ({sh_tilt_deg:.1f}°)", "Perspective yaw displacement", "Torso foreshortened"],
                    geometryMetrics={"shoulderTiltDeg": round(sh_tilt_deg, 1), "foreshorteningRatio": round(ratio_sh, 3)},
                    rationale=f"Torso foreshortened sideways: shoulder line tilted {sh_tilt_deg:.1f}° with horizontal compression {ratio_sh:.2f}, indicating sideways yaw.",
                )
                return True, 0.82, ev

            # D. Deviated orientation relative to calibrated whiteboard (requires non-forward torso)
            if alignment < 0.15 and ratio_torso < 0.70 and mean_sh_conf >= 0.28:
                ev = ActivityEvidence(
                    detectorUsed="YOLOv8n-pose + Board Alignment",
                    observedFeatures=["Body vector perpendicular to whiteboard axis", f"Alignment {alignment:.2f} < 0.15"],
                    geometryMetrics={"alignmentScore": round(alignment, 3), "boardCenterX": float(board_cx), "boardCenterY": float(board_cy)},
                    rationale=f"Upper body oriented at angle to whiteboard (alignment {alignment:.2f} < 0.15). Seated turned sideways.",
                )
                return True, 0.80, ev

            # E. Substantial Lateral Head Turn toward neighbor (requires strong nose confidence and large offset)
            if nose and nose_conf >= 0.40 and abs(yaw_offset) >= 0.55 and sh_width_x > 8.0:
                # If torso is firmly aligned and yaw is moderate (< 0.80), consider it attentive glance
                if not (alignment >= 0.65 and abs(yaw_offset) < 0.80):
                    ev = ActivityEvidence(
                        detectorUsed="YOLOv8n-pose Lateral Head Yaw",
                        observedFeatures=[f"Head turned sideways ({abs(yaw_offset):.2f}x offset from shoulder midline)"],
                        geometryMetrics={"yawOffset": round(yaw_offset, 2)},
                        rationale=f"Head turned sideways ({abs(yaw_offset):.2f}x lateral offset from shoulder midline) toward adjacent desk.",
                    )
                    return True, 0.78, ev

'''

content = content[:start_sw] + new_sw_branches + content[end_sw:]
target_file.write_text(content, encoding="utf-8")
print("Successfully patched backend/app/services/activity_recognition/service.py!")
