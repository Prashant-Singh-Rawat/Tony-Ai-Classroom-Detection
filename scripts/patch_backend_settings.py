import re

# 1. Update backend/app/api/routes/vision.py
with open("backend/app/api/routes/vision.py", "r", encoding="utf-8") as f:
    vision_src = f.read()

# Add keypoint_threshold and elevation_margin_px to process_video
old_params = """    enable_tracking: bool = Form(default=True),
    instructor_roi_polygon: Optional[str] = Form(default=None),
    zone_filtering_enabled: bool = True,"""

new_params = """    enable_tracking: bool = Form(default=True),
    instructor_roi_polygon: Optional[str] = Form(default=None),
    zone_filtering_enabled: bool = True,
    keypoint_threshold: float = Form(default=0.25),
    elevation_margin_px: float = Form(default=15.0),"""

# In case Form(default=True) was used:
if "zone_filtering_enabled: bool = Form(default=True)," in vision_src:
    vision_src = vision_src.replace(
        "zone_filtering_enabled: bool = Form(default=True),",
        "zone_filtering_enabled: bool = Form(default=True),\n    keypoint_threshold: float = Form(default=0.25),\n    elevation_margin_px: float = Form(default=15.0),"
    )

if "instructor_roi_polygon=parsed_polygon,\n            zone_filtering_enabled=zone_filtering_enabled," in vision_src:
    vision_src = vision_src.replace(
        "instructor_roi_polygon=parsed_polygon,\n            zone_filtering_enabled=zone_filtering_enabled,",
        "instructor_roi_polygon=parsed_polygon,\n            zone_filtering_enabled=zone_filtering_enabled,\n            keypoint_threshold=keypoint_threshold,\n            elevation_margin_px=elevation_margin_px,"
    )

with open("backend/app/api/routes/vision.py", "w", encoding="utf-8") as f:
    f.write(vision_src)
print("Updated backend/app/api/routes/vision.py")


# 2. Update backend/app/services/computer_vision/service.py
with open("backend/app/services/computer_vision/service.py", "r", encoding="utf-8") as f:
    cv_src = f.read()

old_sig = """        instructor_roi_polygon: Optional[List[List[float]]] = None,
        zone_filtering_enabled: bool = True,
    ) -> VideoProcessResponse:"""

new_sig = """        instructor_roi_polygon: Optional[List[List[float]]] = None,
        zone_filtering_enabled: bool = True,
        keypoint_threshold: float = 0.25,
        elevation_margin_px: float = 15.0,
    ) -> VideoProcessResponse:"""

cv_src = cv_src.replace(old_sig, new_sig)

old_call = """                        pose_res = self.estimate_pose(
                            frame,
                            confidence_threshold=confidence_threshold,
                            imgsz=imgsz,
                        )"""

new_call = """                        pose_res = self.estimate_pose(
                            frame,
                            confidence_threshold=confidence_threshold,
                            keypoint_threshold=keypoint_threshold,
                            elevation_margin_px=elevation_margin_px,
                            imgsz=imgsz,
                        )"""

cv_src = cv_src.replace(old_call, new_call)

with open("backend/app/services/computer_vision/service.py", "w", encoding="utf-8") as f:
    f.write(cv_src)
print("Updated backend/app/services/computer_vision/service.py")


# 3. Update backend/app/api/routes/websocket.py
with open("backend/app/api/routes/websocket.py", "r", encoding="utf-8") as f:
    ws_src = f.read()

old_ws_payload = """                raw_frame = payload.get("frame", "")
                conf_thresh = float(payload.get("confidenceThreshold", 0.35))
                detect_pose = bool(payload.get("detectPose", True))
                server_side_blur = bool(payload.get("serverSideBlur", True))
                client_side_blur = bool(payload.get("clientSideBlur", False))
                sess_id = payload.get("sessionId", "sess_live")"""

new_ws_payload = """                raw_frame = payload.get("frame", "")
                conf_thresh = float(payload.get("confidenceThreshold", 0.20))
                detect_pose = bool(payload.get("detectPose", True))
                server_side_blur = bool(payload.get("serverSideBlur", True))
                client_side_blur = bool(payload.get("clientSideBlur", False))
                keypoint_thresh = float(payload.get("keypointThreshold", 0.25))
                elevation_margin = float(payload.get("elevationMarginPx", 15.0))
                instructor_polygon = payload.get("instructorRoiPolygon")
                zone_filtering = bool(payload.get("zoneFilteringEnabled", True))
                sess_id = payload.get("sessionId", "sess_live")"""

ws_src = ws_src.replace(old_ws_payload, new_ws_payload)

old_ws_est = """                            # 1. Human Pose Estimation (YOLOv8n-pose: 17 keypoints)
                            pose_res = cv_service.estimate_pose(
                                frame_bytes,
                                confidence_threshold=conf_thresh,
                            )"""

new_ws_est = """                            # 1. Human Pose Estimation (YOLOv8n-pose: 17 keypoints)
                            pose_res = cv_service.estimate_pose(
                                frame_bytes,
                                confidence_threshold=conf_thresh,
                                keypoint_threshold=keypoint_thresh,
                                elevation_margin_px=elevation_margin,
                            )"""

ws_src = ws_src.replace(old_ws_est, new_ws_est)

# Enrich boxes with zone classification if instructor_polygon is configured
old_track_map = """                            # 5. Enrich bounding boxes with stable anonymous track IDs and state
                            track_map = {t.bbox.id: t for t in active_tracks}
                            for b in summary.boxes:
                                matched_t = track_map.get(b.id)"""

new_track_map = """                            # 5. Enrich bounding boxes with stable anonymous track IDs and state
                            track_map = {t.bbox.id: t for t in active_tracks}
                            for b in summary.boxes:
                                if instructor_polygon and zone_filtering:
                                    try:
                                        from backend.app.services.tracking.zone_filter import classify_detection_zone
                                        z_cls, _ = classify_detection_zone(
                                            b,
                                            polygon=instructor_polygon,
                                            enabled=zone_filtering,
                                            video_width=summary.imageWidth,
                                            video_height=summary.imageHeight,
                                            confidence=b.confidence,
                                        )
                                        b.zoneClassification = z_cls.value
                                    except Exception:
                                        pass
                                matched_t = track_map.get(b.id)"""

ws_src = ws_src.replace(old_track_map, new_track_map)

with open("backend/app/api/routes/websocket.py", "w", encoding="utf-8") as f:
    f.write(ws_src)
print("Updated backend/app/api/routes/websocket.py")
