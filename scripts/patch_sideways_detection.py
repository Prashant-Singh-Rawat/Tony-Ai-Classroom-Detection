import sys

with open("backend/app/services/activity_recognition/service.py", "r", encoding="utf-8") as f:
    code = f.read()

# Normalize CRLF to LF for consistent replacement, then we'll write back
code = code.replace("\r\n", "\n")

# 1. New methods: _evaluate_turned_sideways and _evaluate_uncertain_posture
new_methods = """    def _evaluate_turned_sideways(
        self,
        box: BoundingBox,
        kp_map: Dict[str, Keypoint],
    ) -> Tuple[bool, float, ActivityEvidence]:
        \"\"\"
        Evaluates whether an individual student is turned sideways or facing away from the board.
        Uses observable upper-body geometry:
        1. Shoulder foreshortening (narrow horizontal span relative to euclidean distance).
        2. Hip foreshortening and torso orientation when hips are visible.
        3. Shoulder tilt relative to horizontal indicating body yaw.
        4. Torso normal vector alignment relative to calibrated classroom whiteboard vector.
        5. Asymmetric profile sitting (one shoulder dominant, contralateral shoulder occluded in narrow bbox).
        6. Sustained lateral head turn (nose/ear offset relative to shoulder axis).
        \"\"\"
        l_sh = kp_map.get("left_shoulder")
        r_sh = kp_map.get("right_shoulder")
        l_hip = kp_map.get("left_hip")
        r_hip = kp_map.get("right_hip")
        nose = kp_map.get("nose")
        l_ear = kp_map.get("left_ear")
        r_ear = kp_map.get("right_ear")

        ls_conf = l_sh.confidence if l_sh else 0.0
        rs_conf = r_sh.confidence if r_sh else 0.0
        lh_conf = l_hip.confidence if l_hip else 0.0
        rh_conf = r_hip.confidence if r_hip else 0.0
        nose_conf = nose.confidence if nose else 0.0

        both_shoulders_vis = (ls_conf >= 0.20 and rs_conf >= 0.20)
        both_hips_vis = (lh_conf >= 0.20 and rh_conf >= 0.20)
        one_shoulder_vis = (max(ls_conf, rs_conf) >= 0.35 and min(ls_conf, rs_conf) < 0.20)

        # Calibrated whiteboard direction
        calib = self.board_calibration or WHITEBOARD_DEFAULT_CALIBRATION
        board_cx = (calib.get("x1", 20.0) + calib.get("x2", 80.0)) / 2.0
        board_cy = (calib.get("y1", 5.0) + calib.get("y2", 35.0)) / 2.0
        student_cx = box.x + box.w / 2.0
        student_cy = box.y + box.h / 2.0

        target_vec = np.array([board_cx - student_cx, board_cy - student_cy], dtype=float)
        norm_t = np.linalg.norm(target_vec)
        if norm_t > 0:
            target_vec /= norm_t
        else:
            target_vec = np.array([0.0, -1.0])

        # Case 1: Both shoulders visible -> detailed vector & foreshortening analysis
        if both_shoulders_vis:
            sh_dx = r_sh.x - l_sh.x
            sh_dy = r_sh.y - l_sh.y
            sh_euclid = float(np.hypot(sh_dx, sh_dy))
            sh_width_x = abs(sh_dx)

            # Foreshortening ratio: projected horizontal width vs total euclidean length
            ratio_sh = sh_width_x / max(12.0, sh_euclid)
            sh_tilt_deg = abs(float(np.degrees(np.arctan2(sh_dy, sh_dx))))
            if sh_tilt_deg > 90.0:
                sh_tilt_deg = 180.0 - sh_tilt_deg

            # Hip foreshortening if visible
            ratio_hip = 1.0
            if both_hips_vis:
                hip_dx = r_hip.x - l_hip.x
                hip_dy = r_hip.y - l_hip.y
                hip_euclid = float(np.hypot(hip_dx, hip_dy))
                ratio_hip = abs(hip_dx) / max(10.0, hip_euclid)
                ratio_torso = 0.6 * ratio_sh + 0.4 * ratio_hip
            else:
                ratio_torso = ratio_sh

            # Torso normal vector (direction chest/upper body is facing)
            body_vec = np.array([sh_dy, -sh_dx], dtype=float)
            norm_b = np.linalg.norm(body_vec)
            if norm_b > 0:
                body_vec /= norm_b
            else:
                body_vec = np.array([0.0, -1.0])

            alignment = float(np.dot(body_vec, target_vec))

            # Head yaw offset relative to shoulder midline
            yaw_offset = 0.0
            if nose and nose_conf >= 0.20 and sh_width_x > 8.0:
                sh_mid_x = (l_sh.x + r_sh.x) / 2.0
                yaw_offset = (nose.x - sh_mid_x) / (sh_width_x / 2.0)

            # Ear asymmetry (one ear clearly visible while other is occluded)
            le_conf = l_ear.confidence if l_ear else 0.0
            re_conf = r_ear.confidence if r_ear else 0.0
            one_ear_vis = (max(le_conf, re_conf) >= 0.35 and min(le_conf, re_conf) < 0.15)

            # A. Facing Away from Board (alignment < -0.25)
            if alignment < -0.25:
                ev = ActivityEvidence(
                    detectorUsed="YOLOv8n-pose Torso Vector",
                    observedFeatures=["Torso facing away from whiteboard", f"Antiparallel board alignment ({alignment:.2f})"],
                    geometryMetrics={"alignmentScore": round(alignment, 3), "foreshorteningRatio": round(ratio_torso, 3)},
                    rationale=f"Body oriented away from classroom board into rear classroom (alignment {alignment:.2f}).",
                )
                return True, round(max(ls_conf, rs_conf), 2), ev

            # B. Heavy Torso Foreshortening (shoulders/hips compressed horizontally)
            if ratio_torso < 0.58:
                ev = ActivityEvidence(
                    detectorUsed="YOLOv8n-pose Torso Foreshortening",
                    observedFeatures=["Horizontal shoulder span foreshortened", f"Torso foreshortening ratio {ratio_torso:.2f} < 0.58"],
                    geometryMetrics={"foreshorteningRatio": round(ratio_torso, 3), "alignmentScore": round(alignment, 3)},
                    rationale=f"Torso foreshortened sideways (ratio: {ratio_torso:.2f} < 0.58). Seated sideways in desk.",
                )
                return True, 0.85, ev

            # C. Steep Shoulder Tilt with moderate foreshortening (perspective yaw angle)
            if sh_tilt_deg > 32.0 and ratio_sh < 0.75:
                ev = ActivityEvidence(
                    detectorUsed="YOLOv8n-pose Shoulder Axis Tilt",
                    observedFeatures=[f"Shoulder axis tilted ({sh_tilt_deg:.1f}°)", "Perspective yaw displacement"],
                    geometryMetrics={"shoulderTiltDeg": round(sh_tilt_deg, 1), "foreshorteningRatio": round(ratio_sh, 3)},
                    rationale=f"Shoulder line tilted {sh_tilt_deg:.1f}° with horizontal compression {ratio_sh:.2f}, indicating sideways yaw.",
                )
                return True, 0.82, ev

            # D. Deviated orientation relative to calibrated whiteboard
            if alignment < 0.15:
                ev = ActivityEvidence(
                    detectorUsed="YOLOv8n-pose + Board Alignment",
                    observedFeatures=["Body vector perpendicular to whiteboard axis", f"Alignment {alignment:.2f} < 0.15"],
                    geometryMetrics={"alignmentScore": round(alignment, 3), "boardCenterX": float(board_cx), "boardCenterY": float(board_cy)},
                    rationale=f"Upper body oriented at angle to whiteboard (alignment {alignment:.2f} < 0.15). Seated turned sideways.",
                )
                return True, 0.80, ev

            # E. Sustained Head Turn Sideways (yaw offset > 0.48 or one ear dominant)
            if abs(yaw_offset) > 0.48 or (abs(yaw_offset) > 0.35 and one_ear_vis):
                ev = ActivityEvidence(
                    detectorUsed="YOLOv8n-pose Lateral Head Yaw",
                    observedFeatures=[f"Head turned sideways ({abs(yaw_offset):.2f}x offset from shoulder midline)"],
                    geometryMetrics={"yawOffset": round(yaw_offset, 2)},
                    rationale=f"Head turned sideways ({abs(yaw_offset):.2f}x lateral offset from shoulder midline) toward adjacent desk.",
                )
                return True, 0.78, ev

        # Case 2: Asymmetric Shoulder Profile View (one shoulder dominant, far shoulder occluded in narrow box)
        if one_shoulder_vis:
            bbox_aspect = box.w / max(1.0, box.h)
            if bbox_aspect <= 0.65:
                vis_sh_name = "Left" if ls_conf > rs_conf else "Right"
                ev = ActivityEvidence(
                    detectorUsed="YOLOv8n-pose Profile Geometry",
                    observedFeatures=[f"Profile view with dominant {vis_sh_name} shoulder", f"Narrow bbox aspect ratio ({bbox_aspect:.2f})"],
                    geometryMetrics={"bboxAspect": round(bbox_aspect, 2), "dominantShoulderConf": round(max(ls_conf, rs_conf), 2)},
                    rationale=f"Profile sitting posture: {vis_sh_name} shoulder dominant ({max(ls_conf, rs_conf):.0%}), far shoulder occluded by torso.",
                )
                return True, 0.80, ev

        return False, 0.0, ActivityEvidence()

    def _evaluate_uncertain_posture(
        self,
        box: BoundingBox,
        kp_map: Dict[str, Keypoint],
    ) -> Tuple[bool, float, ActivityEvidence]:
        \"\"\"
        Determines if observable keypoints are genuinely insufficient or degraded,
        warranting a NEEDS_REVIEW flag rather than a definitive activity classification.
        \"\"\"
        nose = kp_map.get("nose")
        l_sh = kp_map.get("left_shoulder")
        r_sh = kp_map.get("right_shoulder")
        l_hip = kp_map.get("left_hip")
        r_hip = kp_map.get("right_hip")

        reliable_upper = [
            kp for kp in [nose, l_sh, r_sh, l_hip, r_hip]
            if kp and kp.confidence >= 0.20
        ]

        if len(reliable_upper) < 2:
            ev = ActivityEvidence(
                detectorUsed="YOLOv8n-pose Quality Gate",
                observedFeatures=["Fewer than 2 reliable upper-body keypoints"],
                geometryMetrics={"reliableKeypointsCount": len(reliable_upper)},
                rationale="Upper body keypoints heavily occluded or below confidence threshold (insufficient landmarks).",
            )
            return True, 0.50, ev

        # Low-confidence shoulder and nose pairing on non-sideways posture
        if (nose and 0.15 <= nose.confidence <= 0.30) and (l_sh and 0.15 <= l_sh.confidence <= 0.30):
            ev = ActivityEvidence(
                detectorUsed="YOLOv8n-pose Quality Gate",
                observedFeatures=["Low confidence or partially occluded keypoints"],
                geometryMetrics={"noseConfidence": nose.confidence, "leftShoulderConfidence": l_sh.confidence},
                rationale="Keypoints partially occluded or below confidence threshold.",
            )
            return True, 0.50, ev

        return False, 0.0, ActivityEvidence()
"""

# Insert new methods right before _detect_peer_orientations
marker = "    def _detect_peer_orientations("
if marker in code:
    code = code.replace(marker, new_methods + "\n" + marker)
else:
    print("ERROR: marker _detect_peer_orientations not found")
    sys.exit(1)

# 2. Update _evaluate_single_person_activity priorities 4, 5, 6
old_eval_body = """        # 4. Priority D: Possible Peer Interaction
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
        return ActivityLabel.NO_FLAG_OBSERVED, box.confidence, evidence"""

new_eval_body = """        # 4. Priority D: Possible Peer Interaction / Turned Sideways
        # Mutual peer candidate interaction if detected
        if is_peer_candidate and peer_evidence:
            peer_ev = ActivityEvidence(
                detectorUsed="YOLOv8n-pose Keypoint Geometry",
                observedFeatures=["Mutual upper-body orientation", "Centroid proximity to adjacent peer"],
                geometryMetrics=peer_evidence.get("metrics", {}),
                rationale="Upper body and head oriented toward adjacent peer within interaction distance.",
            )
            return ActivityLabel.POSSIBLE_PEER_INTERACTION, 0.85, peer_ev

        # Observable individual orientation, shoulder & hip foreshortening, and board alignment
        is_sideways, sw_conf, sw_ev = self._evaluate_turned_sideways(box, kp_map)
        if is_sideways:
            return ActivityLabel.POSSIBLE_PEER_INTERACTION, sw_conf, sw_ev

        # 5. Check for ambiguous / heavily occluded keypoints (NEEDS_REVIEW)
        is_uncertain, unc_conf, unc_ev = self._evaluate_uncertain_posture(box, kp_map)
        if is_uncertain:
            return ActivityLabel.NEEDS_REVIEW, unc_conf, unc_ev

        # 6. Facing Board (Calibrated forward direction - default upright seated state)
        is_facing, align_score, align_meta = self._evaluate_facing_board(box, kp_map)
        features = ["Upright posture", "Arms lowered", f"Oriented toward calibrated board (score: {align_score:.2f})"]
        rationale = f"Seated upright facing calibrated whiteboard region (alignment {align_score:.0%}). No supported physical activity flag observed."

        evidence = ActivityEvidence(
            detectorUsed="YOLOv8n-pose + Board Calibration",
            observedFeatures=features,
            geometryMetrics=align_meta,
            rationale=rationale,
        )
        return ActivityLabel.NO_FLAG_OBSERVED, box.confidence, evidence"""

if old_eval_body in code:
    code = code.replace(old_eval_body, new_eval_body)
else:
    print("ERROR: old_eval_body not found in code")
    sys.exit(1)

# 3. Update temporal hysteresis in _apply_temporal_rules
old_peer_rule = """        elif cand_counts.get(ActivityLabel.POSSIBLE_PEER_INTERACTION, 0) >= 4:
            # Check sustained seconds-based duration threshold
            if buffer.candidate_peer_start_time is None:
                # If first time reaching 4 observations, backdate to start of recent window (4 frames * dt)
                buffer.candidate_peer_start_time = max(0.0, current_time - 0.8)
            peer_elapsed = max(0.0, current_time - buffer.candidate_peer_start_time)

            if peer_elapsed >= self.peer_interaction_min_duration_s or buffer.current_label == ActivityLabel.POSSIBLE_PEER_INTERACTION:
                target_label = ActivityLabel.POSSIBLE_PEER_INTERACTION
            else:
                # Brief glance or turn under duration threshold: keep current label to prevent false accusations
                target_label = buffer.current_label"""

new_peer_rule = """        elif cand_counts.get(ActivityLabel.POSSIBLE_PEER_INTERACTION, 0) >= 3:
            # Check sustained seconds-based duration threshold
            if buffer.candidate_peer_start_time is None:
                # If first time reaching 3 observations, backdate to start of recent window (3 frames * dt)
                buffer.candidate_peer_start_time = max(0.0, current_time - 0.6)
            peer_elapsed = max(0.0, current_time - buffer.candidate_peer_start_time)

            if peer_elapsed >= 0.5 or buffer.current_label == ActivityLabel.POSSIBLE_PEER_INTERACTION:
                target_label = ActivityLabel.POSSIBLE_PEER_INTERACTION
            else:
                # Brief glance or turn under duration threshold: keep current label to prevent false accusations
                target_label = buffer.current_label"""

if old_peer_rule in code:
    code = code.replace(old_peer_rule, new_peer_rule)
else:
    print("ERROR: old_peer_rule not found in code")
    sys.exit(1)

# Write back to file
with open("backend/app/services/activity_recognition/service.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Activity recognition service successfully patched with robust turned-sideways logic!")
