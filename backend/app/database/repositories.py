"""
backend/app/database/repositories.py — CRUD Repositories
=========================================================
Typed helper methods for all database tables.
All writes always include an explicit data_source label.
"""

from __future__ import annotations

import datetime
from typing import List, Optional, Any

from sqlalchemy.orm import Session as DBSession

from backend.app.database import models


# ---------------------------------------------------------------------------
# Session Repository
# ---------------------------------------------------------------------------

class SessionRepository:
    def __init__(self, db: DBSession) -> None:
        self.db = db

    def create(self, **kwargs) -> models.Session:
        obj = models.Session(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_id(self, session_id: str) -> Optional[models.Session]:
        return self.db.query(models.Session).filter(models.Session.id == session_id).first()

    def list_all(self) -> List[models.Session]:
        return self.db.query(models.Session).order_by(models.Session.created_at.desc()).all()

    def update_status(self, session_id: str, status: str) -> Optional[models.Session]:
        obj = self.get_by_id(session_id)
        if obj:
            obj.status = status
            obj.updated_at = datetime.datetime.utcnow()
            self.db.commit()
            self.db.refresh(obj)
        return obj

    def update_zone_config(
        self,
        session_id: str,
        instructor_roi_polygon: Optional[List[List[float]]],
        zone_filtering_enabled: bool = True,
    ) -> Optional[models.Session]:
        obj = self.get_by_id(session_id)
        if obj:
            obj.instructor_roi_polygon = instructor_roi_polygon
            obj.zone_filtering_enabled = zone_filtering_enabled
            obj.updated_at = datetime.datetime.utcnow()
            self.db.commit()
            self.db.refresh(obj)
        return obj

    def delete(self, session_id: str) -> bool:
        obj = self.get_by_id(session_id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False


# ---------------------------------------------------------------------------
# Detection Event Repository
# ---------------------------------------------------------------------------

class DetectionRepository:
    def __init__(self, db: DBSession) -> None:
        self.db = db

    def create(self, **kwargs) -> models.DetectionEvent:
        obj = models.DetectionEvent(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_session(self, session_id: str) -> List[models.DetectionEvent]:
        return (
            self.db.query(models.DetectionEvent)
            .filter(models.DetectionEvent.session_id == session_id)
            .order_by(models.DetectionEvent.frame_index)
            .all()
        )

    def get_session_summary(self, session_id: str) -> dict:
        events = self.get_by_session(session_id)
        if not events:
            return {"frames_processed": 0, "avg_person_count": 0.0, "max_hand_raises": 0}
        return {
            "frames_processed": len(events),
            "avg_person_count": sum(e.person_count for e in events) / len(events),
            "max_hand_raises": max(e.hand_raised_count for e in events),
            "total_hand_raise_events": sum(e.hand_raised_count for e in events),
        }


# ---------------------------------------------------------------------------
# Hand-Raise Event Repository (Phase 2.2)
# ---------------------------------------------------------------------------

class HandRaiseEventRepository:
    def __init__(self, db: DBSession) -> None:
        self.db = db

    def create(self, **kwargs) -> models.HandRaiseEventRecord:
        obj = models.HandRaiseEventRecord(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def upsert(self, **kwargs) -> models.HandRaiseEventRecord:
        event_id = kwargs.get("event_id")
        existing = (
            self.db.query(models.HandRaiseEventRecord)
            .filter(models.HandRaiseEventRecord.event_id == event_id)
            .first()
        )
        if existing:
            for k, v in kwargs.items():
                setattr(existing, k, v)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        return self.create(**kwargs)

    def get_by_session(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[models.HandRaiseEventRecord]:
        return (
            self.db.query(models.HandRaiseEventRecord)
            .filter(models.HandRaiseEventRecord.session_id == session_id)
            .order_by(models.HandRaiseEventRecord.start_timestamp_seconds.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_by_track(
        self,
        track_id: str,
        session_id: Optional[str] = None,
    ) -> List[models.HandRaiseEventRecord]:
        q = self.db.query(models.HandRaiseEventRecord).filter(
            models.HandRaiseEventRecord.track_id == track_id
        )
        if session_id:
            q = q.filter(models.HandRaiseEventRecord.session_id == session_id)
        return q.order_by(models.HandRaiseEventRecord.start_timestamp_seconds.asc()).all()

    def get_statistics(self, session_id: Optional[str] = None) -> dict:
        q = self.db.query(models.HandRaiseEventRecord)
        if session_id:
            q = q.filter(models.HandRaiseEventRecord.session_id == session_id)
        events = q.all()

        if not events:
            return {
                "total_events": 0,
                "completed_events": 0,
                "active_events": 0,
                "left_hand_count": 0,
                "right_hand_count": 0,
                "both_hands_count": 0,
                "avg_duration_seconds": 0.0,
                "max_duration_seconds": 0.0,
                "total_duration_seconds": 0.0,
                "needs_review_count": 0,
            }

        left = sum(1 for e in events if e.hand_side == "LEFT_HAND")
        right = sum(1 for e in events if e.hand_side == "RIGHT_HAND")
        both = sum(1 for e in events if e.hand_side == "BOTH_HANDS")
        completed = sum(1 for e in events if e.state == "COMPLETED")
        active = sum(1 for e in events if e.state == "RAISED")
        needs_review = sum(1 for e in events if e.state == "NEEDS_REVIEW")
        durations = [e.duration_seconds for e in events if e.duration_seconds is not None]

        # Zone-based participation counts
        student_zone_events = sum(
            1 for e in events
            if getattr(e, "zone_classification", "STUDENT_ZONE") in ("STUDENT_ZONE", "NOT_CONFIGURED", None)
        )
        instructor_zone_events = sum(
            1 for e in events
            if getattr(e, "zone_classification", None) == "INSTRUCTOR_ZONE"
        )
        uncertain_zone_events = sum(
            1 for e in events
            if getattr(e, "zone_classification", None) == "NEEDS_REVIEW"
        )

        return {
            "total_events": len(events),
            "completed_events": completed,
            "active_events": active,
            "left_hand_count": left,
            "right_hand_count": right,
            "both_hands_count": both,
            "avg_duration_seconds": round(sum(durations) / max(1, len(durations)), 2),
            "max_duration_seconds": round(max(durations), 2) if durations else 0.0,
            "total_duration_seconds": round(sum(durations), 2),
            "needs_review_count": needs_review,
            "student_zone_events": student_zone_events,
            "instructor_zone_events": instructor_zone_events,
            "uncertain_zone_events": uncertain_zone_events,
        }

    def get_distinct_session_ids(self) -> List[str]:
        results = self.db.query(models.HandRaiseEventRecord.session_id).distinct().all()
        return [r[0] for r in results if r[0]]

    def get_unique_tracks(self, session_id: str) -> List[str]:
        results = (
            self.db.query(models.HandRaiseEventRecord.track_id)
            .filter(models.HandRaiseEventRecord.session_id == session_id)
            .distinct()
            .all()
        )
        return [r[0] for r in results if r[0]]

    def get_filtered_events(
        self,
        session_id: Optional[str] = None,
        hand_side: Optional[str] = None,
        state: Optional[str] = None,
        zone_classification: Optional[str] = None,
        limit: int = 500,
        offset: int = 0,
    ) -> List[models.HandRaiseEventRecord]:
        q = self.db.query(models.HandRaiseEventRecord)
        if session_id:
            q = q.filter(models.HandRaiseEventRecord.session_id == session_id)
        if hand_side:
            q = q.filter(models.HandRaiseEventRecord.hand_side == hand_side)
        if state:
            q = q.filter(models.HandRaiseEventRecord.state == state)
        if zone_classification:
            q = q.filter(models.HandRaiseEventRecord.zone_classification == zone_classification)
        return q.order_by(models.HandRaiseEventRecord.start_timestamp_seconds.asc()).offset(offset).limit(limit).all()


class ActivityEventRepository:
    def __init__(self, db: DBSession) -> None:
        self.db = db

    def create(self, **kwargs) -> models.ActivityEventRecord:
        obj = models.ActivityEventRecord(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def upsert(self, **kwargs) -> models.ActivityEventRecord:
        event_id = kwargs.get("event_id")
        existing = (
            self.db.query(models.ActivityEventRecord)
            .filter(models.ActivityEventRecord.event_id == event_id)
            .first()
        )
        if existing:
            for k, v in kwargs.items():
                setattr(existing, k, v)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        return self.create(**kwargs)

    def get_by_session(
        self,
        session_id: str,
        limit: int = 200,
        offset: int = 0,
    ) -> List[models.ActivityEventRecord]:
        return (
            self.db.query(models.ActivityEventRecord)
            .filter(models.ActivityEventRecord.session_id == session_id)
            .order_by(models.ActivityEventRecord.start_timestamp_seconds.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_by_track(
        self,
        track_id: str,
        session_id: Optional[str] = None,
    ) -> List[models.ActivityEventRecord]:
        q = self.db.query(models.ActivityEventRecord).filter(
            models.ActivityEventRecord.track_id == track_id
        )
        if session_id:
            q = q.filter(models.ActivityEventRecord.session_id == session_id)
        return q.order_by(models.ActivityEventRecord.start_timestamp_seconds.asc()).all()

    def get_distribution(self, session_id: Optional[str] = None) -> dict:
        q = self.db.query(models.ActivityEventRecord)
        if session_id:
            q = q.filter(models.ActivityEventRecord.session_id == session_id)
        events = q.all()

        counts: Dict[str, int] = {}
        durations: Dict[str, List[float]] = {}
        for e in events:
            lbl = e.activity_label
            counts[lbl] = counts.get(lbl, 0) + 1
            if e.duration_seconds:
                durations.setdefault(lbl, []).append(e.duration_seconds)

        total = len(events)
        percentages = {
            lbl: round((c / max(1, total)) * 100, 1) for lbl, c in counts.items()
        }
        avg_durations = {
            lbl: round(sum(d_list) / max(1, len(d_list)), 2)
            for lbl, d_list in durations.items()
        }

        unique_tracks = len(set(e.track_id for e in events))

        return {
            "session_id": session_id or "all_sessions",
            "total_tracked_persons": unique_tracks,
            "total_activity_events": total,
            "activity_counts": counts,
            "activity_percentages": percentages,
            "avg_durations": avg_durations,
            "disclaimer": (
                "Observable activity labels reflect visible physical geometry and detected objects only. "
                "They do not evaluate student focus, attentiveness, engagement, or academic performance."
            ),
        }


# ---------------------------------------------------------------------------
# Transcript Repository
# ---------------------------------------------------------------------------

class TranscriptRepository:
    def __init__(self, db: DBSession) -> None:
        self.db = db

    def create(self, **kwargs) -> models.Transcript:
        obj = models.Transcript(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_session(self, session_id: str) -> List[models.Transcript]:
        return (
            self.db.query(models.Transcript)
            .filter(models.Transcript.session_id == session_id)
            .all()
        )

    def get_latest_by_session(self, session_id: str) -> Optional[models.Transcript]:
        return (
            self.db.query(models.Transcript)
            .filter(models.Transcript.session_id == session_id)
            .order_by(models.Transcript.created_at.desc())
            .first()
        )


# ---------------------------------------------------------------------------
# OCR Repository
# ---------------------------------------------------------------------------

class OcrRepository:
    def __init__(self, db: DBSession) -> None:
        self.db = db

    def create(self, **kwargs) -> models.OcrResult:
        obj = models.OcrResult(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_session(self, session_id: str) -> List[models.OcrResult]:
        return (
            self.db.query(models.OcrResult)
            .filter(models.OcrResult.session_id == session_id)
            .all()
        )


# ---------------------------------------------------------------------------
# NLP Repository
# ---------------------------------------------------------------------------

class NlpRepository:
    def __init__(self, db: DBSession) -> None:
        self.db = db

    def create(self, **kwargs) -> models.NlpResult:
        obj = models.NlpResult(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_session(self, session_id: str) -> List[models.NlpResult]:
        return (
            self.db.query(models.NlpResult)
            .filter(models.NlpResult.session_id == session_id)
            .all()
        )


# ---------------------------------------------------------------------------
# Dataset Registry Repository
# ---------------------------------------------------------------------------

class DatasetRepository:
    def __init__(self, db: DBSession) -> None:
        self.db = db

    def upsert(self, name: str, **kwargs) -> models.DatasetRecord:
        obj = self.db.query(models.DatasetRecord).filter(models.DatasetRecord.name == name).first()
        if obj:
            for k, v in kwargs.items():
                setattr(obj, k, v)
        else:
            obj = models.DatasetRecord(name=name, **kwargs)
            self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list_all(self) -> List[models.DatasetRecord]:
        return self.db.query(models.DatasetRecord).all()

    def list_by_source(self, source: str) -> List[models.DatasetRecord]:
        return self.db.query(models.DatasetRecord).filter(models.DatasetRecord.source == source).all()


# ---------------------------------------------------------------------------
# Model Registry Repository
# ---------------------------------------------------------------------------

class ModelRepository:
    def __init__(self, db: DBSession) -> None:
        self.db = db

    def upsert(self, name: str, **kwargs) -> models.ModelRecord:
        obj = self.db.query(models.ModelRecord).filter(models.ModelRecord.name == name).first()
        if obj:
            for k, v in kwargs.items():
                setattr(obj, k, v)
        else:
            obj = models.ModelRecord(name=name, **kwargs)
            self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list_all(self) -> List[models.ModelRecord]:
        return self.db.query(models.ModelRecord).all()

    def get_by_name(self, name: str) -> Optional[models.ModelRecord]:
        return self.db.query(models.ModelRecord).filter(models.ModelRecord.name == name).first()

    def mark_loaded(self, name: str) -> Optional[models.ModelRecord]:
        obj = self.get_by_name(name)
        if obj:
            obj.is_loaded = True
            obj.load_status = "LOADED"
            obj.last_used = datetime.datetime.utcnow()
            self.db.commit()
            self.db.refresh(obj)
        return obj

    def mark_failed(self, name: str, error: str) -> Optional[models.ModelRecord]:
        obj = self.get_by_name(name)
        if obj:
            obj.is_loaded = False
            obj.load_status = "LOAD_FAILED"
            obj.notes = error
            self.db.commit()
            self.db.refresh(obj)
        return obj


# ---------------------------------------------------------------------------
# Report Repository
# ---------------------------------------------------------------------------

class ReportRepository:
    def __init__(self, db: DBSession) -> None:
        self.db = db

    def create(self, **kwargs) -> models.Report:
        obj = models.Report(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list_all(self) -> List[models.Report]:
        return self.db.query(models.Report).order_by(models.Report.created_at.desc()).all()

    def get_by_id(self, report_id: int) -> Optional[models.Report]:
        return self.db.query(models.Report).filter(models.Report.id == report_id).first()


# ---------------------------------------------------------------------------
# Settings Repository
# ---------------------------------------------------------------------------

class SettingsRepository:
    def __init__(self, db: DBSession) -> None:
        self.db = db

    def get(self, key: str, default: Any = None) -> Any:
        obj = self.db.query(models.AppSettings).filter(models.AppSettings.key == key).first()
        return obj.value if obj else default

    def set(self, key: str, value: str, description: str = "") -> models.AppSettings:
        obj = self.db.query(models.AppSettings).filter(models.AppSettings.key == key).first()
        if obj:
            obj.value = value
            obj.updated_at = datetime.datetime.utcnow()
        else:
            obj = models.AppSettings(key=key, value=value, description=description)
            self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_all(self) -> List[models.AppSettings]:
        return self.db.query(models.AppSettings).all()

