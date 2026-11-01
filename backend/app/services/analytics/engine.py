"""
backend/app/services/analytics/engine.py — Classroom Activity Analytics Engine
==============================================================================
Phase 2.3: Session-level metrics, temporal participation intervals, track-level breakdown,
multi-session comparative analytics, and CSV / PDF report generators.

Core Design Rules:
1. Strictly reports observable physical activity (hand raising, posture, movements).
2. Never infers internal cognitive/mental states (attention, concentration, emotion, intelligence).
3. Never equates anonymous track counts to real student headcounts.
4. Generates zero-hallucination metrics directly from SQLite hand_raise_events.
5. Handles zero-event and incomplete sessions gracefully without division-by-zero errors.
"""

from __future__ import annotations

import csv
import datetime
import io
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session as DBSession

from backend.app.core.config import REPO_ROOT
from backend.app.database.db import SessionLocal
from backend.app.database.models import DetectionEvent, HandRaiseEventRecord, Session as SessionModel
from backend.app.database.repositories import DetectionRepository, HandRaiseEventRepository, SessionRepository
from backend.app.schemas.activities import ActivityDistributionSummary
from backend.app.schemas.analytics import (
    EventTypeDistribution,
    ParticipationTimeBucket,
    SessionActivityAnalytics,
    SessionComparisonResponse,
    SessionComparisonSummary,
    TrackParticipationSummary,
)
from backend.app.services.database.session_repository import DEMO_SESSIONS_DATA

REPORTS_DIR = REPO_ROOT / "data" / "generated_reports"


class ClassroomActivityAnalyticsEngine:
    """Computes session-level activity analytics, timelines, comparisons, and exports."""

    def __init__(self, reports_dir: Optional[Path] = None) -> None:
        self.reports_dir = reports_dir or REPORTS_DIR
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------------------
    # Session Activity Intelligence
    # ---------------------------------------------------------------------------

    def get_session_activity(
        self,
        session_id: str,
        interval_seconds: int = 60,
        db: Optional[DBSession] = None,
        include_demo: bool = True,
        zone_filtering: Optional[bool] = None,
    ) -> SessionActivityAnalytics:
        """
        Calculates session activity analytics directly from SQLite records.
        If the session has real records, processes them dynamically.
        If no SQLite records exist and demo is enabled, loads grounded demo baseline.
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            repo = HandRaiseEventRepository(db)
            events: List[HandRaiseEventRecord] = repo.get_by_session(session_id, limit=5000, offset=0)

            # Check if real events exist
            if events:
                return self._build_analytics_from_records(
                    session_id=session_id,
                    events=events,
                    interval_seconds=interval_seconds,
                    db=db,
                    zone_filtering_override=zone_filtering,
                )

            # Check if this is a known demo session
            if include_demo and session_id in ("sess_01", "sess_02", "sess_03"):
                return self._build_demo_session_analytics(session_id, interval_seconds)

            # Zero-event real session
            return self._build_empty_session_analytics(session_id, interval_seconds, db)

        finally:
            if should_close:
                db.close()

    def _build_analytics_from_records(
        self,
        session_id: str,
        events: List[HandRaiseEventRecord],
        interval_seconds: int,
        db: DBSession,
        zone_filtering_override: Optional[bool] = None,
    ) -> SessionActivityAnalytics:
        """Assembles SessionActivityAnalytics from actual SQLite database rows."""
        # Chronological sort
        events = sorted(events, key=lambda e: (e.start_timestamp_seconds or 0.0))

        # Peak people detection count from detection_events table
        peak_people = 0
        try:
            det_repo = DetectionRepository(db)
            det_summary = det_repo.get_session_summary(session_id)
            peak_people = int(det_summary.get("avg_person_count", 0)) or 1
        except Exception:
            peak_people = 1

        # Session metadata & zone filtering configuration
        sess_title = f"Classroom Session ({session_id})"
        course_code = "CS402"
        sess_date = datetime.datetime.now().strftime("%Y-%m-%d")
        start_time = "09:00 AM"
        dur_mins = 45.0
        instructor_roi_polygon = None
        zone_filtering_enabled = True

        try:
            sess_row = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if sess_row:
                sess_title = sess_row.title or sess_title
                course_code = sess_row.course_code or course_code
                sess_date = sess_row.date or sess_date
                start_time = sess_row.start_time or start_time
                dur_mins = float(sess_row.duration_minutes or 45.0)
                instructor_roi_polygon = sess_row.instructor_roi_polygon
                if sess_row.zone_filtering_enabled is not None:
                    zone_filtering_enabled = sess_row.zone_filtering_enabled
        except Exception:
            pass

        if zone_filtering_override is not None:
            zone_filtering_enabled = zone_filtering_override

        # Breakdown by Teacher Zone Exclusion
        student_zone_events = [
            e for e in events
            if getattr(e, "zone_classification", "STUDENT_ZONE") in ("STUDENT_ZONE", "NOT_CONFIGURED", None)
        ]
        instructor_zone_events = [
            e for e in events
            if getattr(e, "zone_classification", None) == "INSTRUCTOR_ZONE"
        ]
        uncertain_zone_events = [
            e for e in events
            if getattr(e, "zone_classification", None) == "NEEDS_REVIEW"
        ]

        total_detected_count = len(events)
        student_zone_count = len(student_zone_events)
        instructor_zone_count = len(instructor_zone_events)
        uncertain_zone_count = len(uncertain_zone_events)

        # If zone filtering is active and polygon is configured, student participation totals exclude instructor events
        active_analysis_events = student_zone_events if (zone_filtering_enabled and instructor_roi_polygon) else events

        # Track IDs & Hand classification
        unique_tracks = sorted(list({e.track_id for e in active_analysis_events if e.track_id}))
        left_events = [e for e in active_analysis_events if e.hand_side == "LEFT_HAND"]
        right_events = [e for e in active_analysis_events if e.hand_side == "RIGHT_HAND"]
        both_events = [e for e in active_analysis_events if e.hand_side == "BOTH_HANDS"]
        completed_events = [e for e in active_analysis_events if e.state == "COMPLETED"]
        active_events = [e for e in active_analysis_events if e.state == "RAISED"]

        durations = [float(e.duration_seconds or 0.0) for e in active_analysis_events if e.duration_seconds is not None]
        total_duration = round(sum(durations), 2)
        avg_duration = round(total_duration / max(1, len(durations)), 2)
        max_duration = round(max(durations), 2) if durations else 0.0

        total_evts = len(active_analysis_events)
        dist = EventTypeDistribution(
            leftHandPct=round((len(left_events) / total_evts) * 100, 1) if total_evts else 0.0,
            rightHandPct=round((len(right_events) / total_evts) * 100, 1) if total_evts else 0.0,
            bothHandsPct=round((len(both_events) / total_evts) * 100, 1) if total_evts else 0.0,
            unknownPct=round(((total_evts - len(left_events) - len(right_events) - len(both_events)) / total_evts) * 100, 1) if total_evts else 0.0,
        )

        # Per-track participation summaries
        track_map: Dict[str, Dict[str, Any]] = {}
        for t_id in unique_tracks:
            track_map[t_id] = {
                "events": 0,
                "durations": [],
                "left": 0,
                "right": 0,
                "both": 0,
                "first_seen": None,
                "last_seen": None,
            }

        for e in events:
            t_data = track_map.get(e.track_id)
            if not t_data:
                continue
            t_data["events"] += 1
            if e.duration_seconds is not None:
                t_data["durations"].append(float(e.duration_seconds))
            if e.hand_side == "LEFT_HAND":
                t_data["left"] += 1
            elif e.hand_side == "RIGHT_HAND":
                t_data["right"] += 1
            elif e.hand_side == "BOTH_HANDS":
                t_data["both"] += 1

            start_t = float(e.start_timestamp_seconds or 0.0)
            end_t = float(e.end_timestamp_seconds or start_t)
            if t_data["first_seen"] is None or start_t < t_data["first_seen"]:
                t_data["first_seen"] = start_t
            if t_data["last_seen"] is None or end_t > t_data["last_seen"]:
                t_data["last_seen"] = end_t

        track_summaries: List[TrackParticipationSummary] = []
        for t_id, data in track_map.items():
            t_durs = data["durations"]
            t_sum_dur = round(sum(t_durs), 2)
            t_avg_dur = round(t_sum_dur / max(1, len(t_durs)), 2)
            track_summaries.append(
                TrackParticipationSummary(
                    trackId=t_id,
                    eventCount=data["events"],
                    totalDurationSeconds=t_sum_dur,
                    avgDurationSeconds=t_avg_dur,
                    leftHandCount=data["left"],
                    rightHandCount=data["right"],
                    bothHandsCount=data["both"],
                    firstSeenSeconds=round(data["first_seen"], 2) if data["first_seen"] is not None else None,
                    lastSeenSeconds=round(data["last_seen"], 2) if data["last_seen"] is not None else None,
                )
            )

        # Sort track summaries by event count descending
        track_summaries = sorted(track_summaries, key=lambda s: s.eventCount, reverse=True)
        most_active_track = track_summaries[0].trackId if track_summaries else None
        least_active_track = track_summaries[-1].trackId if track_summaries else None

        # Build timeline buckets
        timeline, peak_interval = self._calculate_timeline_buckets(events, interval_seconds)

        act_dist_summary = None
        try:
            from backend.app.database.repositories import ActivityEventRepository
            act_repo = ActivityEventRepository(db)
            raw_act = act_repo.get_distribution(session_id)
            if raw_act and raw_act.get("total_activity_events", 0) > 0:
                act_dist_summary = ActivityDistributionSummary(
                    sessionId=session_id,
                    totalTrackedPersons=raw_act.get("total_tracked_persons", 0),
                    totalActivityEvents=raw_act.get("total_activity_events", 0),
                    activityCounts=raw_act.get("activity_counts", {}),
                    activityPercentages=raw_act.get("activity_percentages", {}),
                    avgDurations=raw_act.get("avg_durations", {}),
                )
        except Exception:
            pass

        return SessionActivityAnalytics(
            sessionId=session_id,
            title=sess_title,
            courseCode=course_code,
            date=sess_date,
            startTime=start_time,
            durationMinutes=dur_mins,
            totalObservedPeoplePeak=max(peak_people, len(unique_tracks)),
            uniqueAnonymousTracksObserved=len(unique_tracks),
            totalHandRaisingEvents=total_evts,
            completedEventsCount=len(completed_events),
            activeEventsCount=len(active_events),
            leftHandEvents=len(left_events),
            rightHandEvents=len(right_events),
            bothHandEvents=len(both_events),
            averageEventDurationSeconds=avg_duration,
            maxEventDurationSeconds=max_duration,
            totalEventDurationSeconds=total_duration,
            observableParticipationEvents=total_evts,
            eventTypeDistribution=dist,
            activityDistribution=act_dist_summary,
            mostFrequentlyObservedTrack=most_active_track,
            leastFrequentlyObservedTrack=least_active_track,
            peakParticipationInterval=peak_interval,
            intervalSeconds=interval_seconds,
            timeline=timeline,
            trackSummaries=track_summaries,
            dataSource="REAL_PROCESSING",
            isDemoData=False,
            instructorRoiPolygon=instructor_roi_polygon,
            zoneFilteringEnabled=zone_filtering_enabled,
            totalDetectedHandRaises=total_detected_count,
            studentZoneEventsCount=student_zone_count,
            instructorZoneEventsCount=instructor_zone_count,
            uncertainZoneEventsCount=uncertain_zone_count,
        )

    def _calculate_timeline_buckets(
        self,
        events: List[HandRaiseEventRecord],
        interval_seconds: int,
    ) -> Tuple[List[ParticipationTimeBucket], Optional[str]]:
        """Slices events into discrete intervals of interval_seconds."""
        if not events:
            return [], None

        max_t = max(float(e.end_timestamp_seconds or e.start_timestamp_seconds or 0.0) for e in events)
        # Pad session to at least 1 interval
        total_span = max(float(interval_seconds), max_t)
        num_buckets = max(1, math.ceil(total_span / interval_seconds))

        buckets: List[ParticipationTimeBucket] = []
        peak_label = None
        peak_count = -1

        for b_idx in range(num_buckets):
            b_start = b_idx * interval_seconds
            b_end = (b_idx + 1) * interval_seconds

            # Format human label e.g. "00:00 - 01:00" or "05:00 - 10:00"
            m_start, s_start = divmod(b_start, 60)
            m_end, s_end = divmod(b_end, 60)
            label = f"{int(m_start):02d}:{int(s_start):02d} - {int(m_end):02d}:{int(s_end):02d}"

            # Filter events whose start timestamp falls inside this interval
            b_evts = [
                e for e in events
                if b_start <= float(e.start_timestamp_seconds or 0.0) < b_end
            ]

            l_count = sum(1 for e in b_evts if e.hand_side == "LEFT_HAND")
            r_count = sum(1 for e in b_evts if e.hand_side == "RIGHT_HAND")
            b_count = sum(1 for e in b_evts if e.hand_side == "BOTH_HANDS")
            active_tracks = len(set(e.track_id for e in b_evts if e.track_id))
            ev_count = len(b_evts)

            if ev_count > peak_count:
                peak_count = ev_count
                peak_label = label

            buckets.append(
                ParticipationTimeBucket(
                    bucketIndex=b_idx,
                    startTimeSeconds=float(b_start),
                    endTimeSeconds=float(b_end),
                    label=label,
                    eventCount=ev_count,
                    leftHandCount=l_count,
                    rightHandCount=r_count,
                    bothHandsCount=b_count,
                    activeTracksCount=active_tracks,
                )
            )

        return buckets, peak_label

    def _build_empty_session_analytics(
        self,
        session_id: str,
        interval_seconds: int,
        db: DBSession,
    ) -> SessionActivityAnalytics:
        """Returns zeroed session activity analytics when no events exist."""
        sess_title = f"Classroom Session {session_id}"
        course_code = "CS402"
        sess_date = datetime.datetime.now().strftime("%Y-%m-%d")

        try:
            sess_row = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if sess_row:
                sess_title = sess_row.title or sess_title
                course_code = sess_row.course_code or course_code
                sess_date = sess_row.date or sess_date
        except Exception:
            pass

        return SessionActivityAnalytics(
            sessionId=session_id,
            title=sess_title,
            courseCode=course_code,
            date=sess_date,
            startTime="09:00 AM",
            durationMinutes=45.0,
            totalObservedPeoplePeak=0,
            uniqueAnonymousTracksObserved=0,
            totalHandRaisingEvents=0,
            completedEventsCount=0,
            activeEventsCount=0,
            leftHandEvents=0,
            rightHandEvents=0,
            bothHandEvents=0,
            averageEventDurationSeconds=0.0,
            maxEventDurationSeconds=0.0,
            totalEventDurationSeconds=0.0,
            observableParticipationEvents=0,
            eventTypeDistribution=EventTypeDistribution(),
            mostFrequentlyObservedTrack=None,
            leastFrequentlyObservedTrack=None,
            peakParticipationInterval="None",
            intervalSeconds=interval_seconds,
            timeline=[],
            trackSummaries=[],
            dataSource="DATABASE_EMPTY_SESSION",
            isDemoData=False,
        )

    def _build_demo_session_analytics(
        self,
        session_id: str,
        interval_seconds: int,
    ) -> SessionActivityAnalytics:
        """Constructs grounded baseline activity analytics for standard demo sessions."""
        demo_meta = next((s for s in DEMO_SESSIONS_DATA if s.sessionId == session_id), DEMO_SESSIONS_DATA[0])

        total_evts = demo_meta.totalHandRaiseEvents
        dur_mins = demo_meta.durationMinutes
        total_seconds = dur_mins * 60

        # Hand distributions
        if session_id == "sess_01":
            left_cnt = 9
            right_cnt = 8
            both_cnt = 2
            avg_dur = 2.45
            max_dur = 4.80
            tracks_count = 12
        elif session_id == "sess_02":
            left_cnt = 5
            right_cnt = 6
            both_cnt = 1
            avg_dur = 2.10
            max_dur = 3.90
            tracks_count = 8
        else:
            left_cnt = 11
            right_cnt = 10
            both_cnt = 3
            avg_dur = 2.75
            max_dur = 5.20
            tracks_count = 15

        dist = EventTypeDistribution(
            leftHandPct=round((left_cnt / total_evts) * 100, 1),
            rightHandPct=round((right_cnt / total_evts) * 100, 1),
            bothHandsPct=round((both_cnt / total_evts) * 100, 1),
            unknownPct=0.0,
        )

        # Generate realistic track summaries
        track_summaries: List[TrackParticipationSummary] = []
        for i in range(tracks_count):
            t_id = f"track_{i+1:03d}"
            ev_for_track = max(1, round(total_evts / tracks_count) + (1 if i % 3 == 0 else -1 if i % 4 == 0 else 0))
            track_summaries.append(
                TrackParticipationSummary(
                    trackId=t_id,
                    eventCount=ev_for_track,
                    totalDurationSeconds=round(ev_for_track * avg_dur, 2),
                    avgDurationSeconds=avg_dur,
                    leftHandCount=round(ev_for_track * 0.5),
                    rightHandCount=round(ev_for_track * 0.4),
                    bothHandsCount=max(0, ev_for_track - round(ev_for_track * 0.5) - round(ev_for_track * 0.4)),
                    firstSeenSeconds=round(i * 120.0, 1),
                    lastSeenSeconds=round(min(total_seconds, (i + 1) * 200.0), 1),
                )
            )

        track_summaries = sorted(track_summaries, key=lambda s: s.eventCount, reverse=True)

        # Generate timeline intervals
        num_buckets = max(1, math.ceil(total_seconds / interval_seconds))
        timeline: List[ParticipationTimeBucket] = []
        peak_interval = None
        peak_evts = -1

        for b_idx in range(min(num_buckets, 30)):  # capped to avoid huge arrays
            b_start = b_idx * interval_seconds
            b_end = (b_idx + 1) * interval_seconds
            m_start, s_start = divmod(b_start, 60)
            m_end, s_end = divmod(b_end, 60)
            label = f"{int(m_start):02d}:{int(s_start):02d} - {int(m_end):02d}:{int(s_end):02d}"

            # Distribute events with mid-session peak
            progress = b_idx / max(1, num_buckets)
            # Gaussian-like bell curve for participation peak
            factor = math.exp(-((progress - 0.45) ** 2) / 0.05)
            b_ev_cnt = max(0, round((total_evts / num_buckets) * (0.3 + 1.8 * factor)))

            if b_ev_cnt > peak_evts:
                peak_evts = b_ev_cnt
                peak_interval = label

            timeline.append(
                ParticipationTimeBucket(
                    bucketIndex=b_idx,
                    startTimeSeconds=float(b_start),
                    endTimeSeconds=float(b_end),
                    label=label,
                    eventCount=b_ev_cnt,
                    leftHandCount=round(b_ev_cnt * 0.48),
                    rightHandCount=round(b_ev_cnt * 0.42),
                    bothHandsCount=max(0, b_ev_cnt - round(b_ev_cnt * 0.48) - round(b_ev_cnt * 0.42)),
                    activeTracksCount=min(tracks_count, max(1, round(b_ev_cnt * 0.8))),
                )
            )

        demo_activity_dist = ActivityDistributionSummary(
            sessionId=session_id,
            totalTrackedPersons=tracks_count,
            totalActivityEvents=total_evts + 12,
            activityCounts={
                "NO_FLAG_OBSERVED": max(0, total_evts * 2),
                "HAND_RAISED": total_evts,
                "HEAD_DOWN_POSTURE": 3,
                "POSSIBLE_PEER_INTERACTION": 2,
                "PHONE_VISIBLE": 0,
            },
            activityPercentages={
                "NO_FLAG_OBSERVED": 62.5,
                "HAND_RAISED": 25.0,
                "HEAD_DOWN_POSTURE": 7.5,
                "POSSIBLE_PEER_INTERACTION": 5.0,
                "PHONE_VISIBLE": 0.0,
            },
            avgDurations={
                "NO_FLAG_OBSERVED": 42.0,
                "HAND_RAISED": avg_dur,
                "HEAD_DOWN_POSTURE": 4.5,
                "POSSIBLE_PEER_INTERACTION": 2.8,
                "PHONE_VISIBLE": 0.0,
            },
        )

        return SessionActivityAnalytics(
            sessionId=session_id,
            title=demo_meta.title,
            courseCode=demo_meta.courseCode,
            date=demo_meta.date,
            startTime=demo_meta.startTime,
            durationMinutes=float(dur_mins),
            totalObservedPeoplePeak=demo_meta.totalStudents,
            uniqueAnonymousTracksObserved=tracks_count,
            totalHandRaisingEvents=total_evts,
            completedEventsCount=total_evts,
            activeEventsCount=0,
            leftHandEvents=left_cnt,
            rightHandEvents=right_cnt,
            bothHandEvents=both_cnt,
            averageEventDurationSeconds=avg_dur,
            maxEventDurationSeconds=max_dur,
            totalEventDurationSeconds=round(total_evts * avg_dur, 2),
            observableParticipationEvents=total_evts,
            eventTypeDistribution=dist,
            activityDistribution=demo_activity_dist,
            mostFrequentlyObservedTrack=track_summaries[0].trackId if track_summaries else "track_001",
            leastFrequentlyObservedTrack=track_summaries[-1].trackId if track_summaries else "track_008",
            peakParticipationInterval=peak_interval or "15:00 - 20:00",
            intervalSeconds=interval_seconds,
            timeline=timeline,
            trackSummaries=track_summaries,
            dataSource="DEMO_DATA",
            isDemoData=True,
        )

    # ---------------------------------------------------------------------------
    # Session Comparison Engine
    # ---------------------------------------------------------------------------

    def compare_sessions(
        self,
        session_a_id: str,
        session_b_id: str,
        db: Optional[DBSession] = None,
        include_demo: bool = True,
    ) -> SessionComparisonResponse:
        """
        Computes a side-by-side comparison between Session A and Session B.
        Generates objective physical deltas without subjective or cognitive ranking.
        """
        a_metrics = self.get_session_activity(session_a_id, db=db, include_demo=include_demo)
        b_metrics = self.get_session_activity(session_b_id, db=db, include_demo=include_demo)

        diffs: List[SessionComparisonSummary] = []

        # 1. Total Hand-Raising Events
        ev_diff = a_metrics.totalHandRaisingEvents - b_metrics.totalHandRaisingEvents
        ev_sign = "+" if ev_diff > 0 else ""
        diffs.append(
            SessionComparisonSummary(
                metric="Total Observed Hand-Raising Events",
                sessionAValue=a_metrics.totalHandRaisingEvents,
                sessionBValue=b_metrics.totalHandRaisingEvents,
                difference=f"{ev_sign}{ev_diff} events",
                interpretation=(
                    f"Session {session_a_id} recorded {abs(ev_diff)} "
                    f"{'more' if ev_diff >= 0 else 'fewer'} physical hand-raise events than Session {session_b_id}."
                ),
            )
        )

        # 2. Unique Anonymous Tracks Observed
        tr_diff = a_metrics.uniqueAnonymousTracksObserved - b_metrics.uniqueAnonymousTracksObserved
        tr_sign = "+" if tr_diff > 0 else ""
        diffs.append(
            SessionComparisonSummary(
                metric="Unique Anonymous Tracks Observed",
                sessionAValue=a_metrics.uniqueAnonymousTracksObserved,
                sessionBValue=b_metrics.uniqueAnonymousTracksObserved,
                difference=f"{tr_sign}{tr_diff} tracks",
                interpretation=(
                    f"Session {session_a_id} tracked {abs(tr_diff)} "
                    f"{'more' if tr_diff >= 0 else 'fewer'} unique anonymous individuals exhibiting movement."
                ),
            )
        )

        # 3. Average Event Duration
        dur_diff = round(a_metrics.averageEventDurationSeconds - b_metrics.averageEventDurationSeconds, 2)
        dur_sign = "+" if dur_diff > 0 else ""
        diffs.append(
            SessionComparisonSummary(
                metric="Average Hand-Raising Duration",
                sessionAValue=f"{a_metrics.averageEventDurationSeconds} s",
                sessionBValue=f"{b_metrics.averageEventDurationSeconds} s",
                difference=f"{dur_sign}{dur_diff} s",
                interpretation=(
                    f"Hand-raising gestures were held on average for {abs(dur_diff)}s "
                    f"{'longer' if dur_diff >= 0 else 'shorter'} in Session {session_a_id}."
                ),
            )
        )

        # 4. Left vs Right Hand Distribution
        diffs.append(
            SessionComparisonSummary(
                metric="Left / Right / Both Hand Distribution",
                sessionAValue=f"L:{a_metrics.leftHandEvents} / R:{a_metrics.rightHandEvents} / Both:{a_metrics.bothHandEvents}",
                sessionBValue=f"L:{b_metrics.leftHandEvents} / R:{b_metrics.rightHandEvents} / Both:{b_metrics.bothHandEvents}",
                difference=None,
                interpretation=(
                    f"Session {session_a_id} showed {a_metrics.eventTypeDistribution.leftHandPct}% left-arm preference; "
                    f"Session {session_b_id} showed {b_metrics.eventTypeDistribution.leftHandPct}% left-arm preference."
                ),
            )
        )

        # 5. Peak Participation Interval
        diffs.append(
            SessionComparisonSummary(
                metric="Peak Observable Activity Interval",
                sessionAValue=a_metrics.peakParticipationInterval or "N/A",
                sessionBValue=b_metrics.peakParticipationInterval or "N/A",
                difference=None,
                interpretation="Observable physical hand raises peaked during these respective session time-windows.",
            )
        )

        return SessionComparisonResponse(
            sessionA=a_metrics,
            sessionB=b_metrics,
            comparisons=diffs,
            generatedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

    # ---------------------------------------------------------------------------
    # CSV Export Generator
    # ---------------------------------------------------------------------------

    def export_session_csv(
        self,
        session_id: str,
        db: Optional[DBSession] = None,
        include_demo: bool = True,
    ) -> str:
        """
        Renders session activity analytics and granular event records into a structured CSV string.
        Includes academic metadata, aggregate metrics, and data provenance.
        """
        analytics = self.get_session_activity(session_id, db=db, include_demo=include_demo)

        output = io.StringIO()
        writer = csv.writer(output)

        # 1. Academic Header
        writer.writerow(["# CLASSVISION AI — CLASSROOM ACTIVITY ANALYTICS EXPORT"])
        writer.writerow(["# Session ID", analytics.sessionId])
        writer.writerow(["# Course Code", analytics.courseCode or "CS402"])
        writer.writerow(["# Session Title", analytics.title])
        writer.writerow(["# Date", analytics.date])
        writer.writerow(["# Duration (Minutes)", analytics.durationMinutes])
        writer.writerow(["# Data Source", analytics.dataSource])
        writer.writerow(["# Export Timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow([])

        # 2. Aggregate Physical Metrics
        writer.writerow(["=== AGGREGATE OBSERVABLE METRICS ==="])
        writer.writerow(["Metric", "Value", "Notes"])
        writer.writerow(["Unique Anonymous Tracks", analytics.uniqueAnonymousTracksObserved, "Unique tracks within session; not student count"])
        writer.writerow(["Total Hand-Raising Events", analytics.totalHandRaisingEvents, "Continuous gestures aggregated into single events"])
        writer.writerow(["Left-Hand Events", analytics.leftHandEvents, f"{analytics.eventTypeDistribution.leftHandPct}% of total"])
        writer.writerow(["Right-Hand Events", analytics.rightHandEvents, f"{analytics.eventTypeDistribution.rightHandPct}% of total"])
        writer.writerow(["Both-Hands Events", analytics.bothHandEvents, f"{analytics.eventTypeDistribution.bothHandsPct}% of total"])
        writer.writerow(["Average Duration (Seconds)", analytics.averageEventDurationSeconds, "Mean physical gesture duration"])
        writer.writerow(["Maximum Duration (Seconds)", analytics.maxEventDurationSeconds, "Peak continuous raise duration"])
        writer.writerow(["Peak Activity Interval", analytics.peakParticipationInterval or "N/A", "Time window with highest observable hand raises"])
        writer.writerow([])

        # 3. Timeline Intervals
        writer.writerow(["=== TIMELINE PARTICIPATION INTERVALS (INTERVAL = 60s) ==="])
        writer.writerow(["Interval Index", "Time Window", "Event Count", "Left Hand", "Right Hand", "Both Hands", "Active Tracks"])
        for b in analytics.timeline:
            writer.writerow([b.bucketIndex, b.label, b.eventCount, b.leftHandCount, b.rightHandCount, b.bothHandsCount, b.activeTracksCount])
        writer.writerow([])

        # 4. Anonymous Track Breakdown
        writer.writerow(["=== ANONYMOUS TRACK BREAKDOWN ==="])
        writer.writerow(["Anonymous Track ID", "Event Count", "Total Duration (s)", "Avg Duration (s)", "Left Hand", "Right Hand", "Both Hands"])
        for t in analytics.trackSummaries:
            writer.writerow([t.trackId, t.eventCount, t.totalDurationSeconds, t.avgDurationSeconds, t.leftHandCount, t.rightHandCount, t.bothHandsCount])
        writer.writerow([])

        # 5. Provenance & Privacy Statement
        writer.writerow(["=== DATA PROVENANCE & ETHICS ==="])
        writer.writerow(["[POLICY]", "50% Kaggle Datasets | 50% Synthetic Datasets | 0% Real Classroom Recordings"])
        writer.writerow(["[PRIVACY]", "Strictly observable physical movements. Zero facial recognition or biometric profiling."])
        writer.writerow(["[INTERPRETATION]", analytics.privacyDisclaimer])

        return output.getvalue()

    # ---------------------------------------------------------------------------
    # PDF Export Generator (ReportLab)
    # ---------------------------------------------------------------------------

    def export_session_pdf(
        self,
        session_id: str,
        db: Optional[DBSession] = None,
        include_demo: bool = True,
    ) -> str:
        """
        Compiles publication-grade PDF report using ReportLab.
        Stores generated file in data/generated_reports and returns its absolute path.
        """
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        analytics = self.get_session_activity(session_id, db=db, include_demo=include_demo)

        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"activity_analytics_{session_id}_{timestamp_str}.pdf"
        filepath = self.reports_dir / filename

        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a"),
            alignment=0,
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#64748b"),
        )
        heading_style = ParagraphStyle(
            "Heading",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#0284c7"),
            spaceBefore=12,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
        )
        callout_style = ParagraphStyle(
            "Callout",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#0369a1"),
            backColor=colors.HexColor("#f0f9ff"),
        )

        elements = []

        # 1. Header
        elements.append(Paragraph("ClassVision AI — Classroom Activity Analytics", title_style))
        elements.append(Spacer(1, 3))
        elements.append(Paragraph(
            f"Session ID: <b>{analytics.sessionId}</b> | Course: <b>{analytics.courseCode or 'CS402'}</b> | "
            f"Date: <b>{analytics.date}</b> | Data Source: <b>{analytics.dataSource}</b>",
            subtitle_style,
        ))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(
            f"Provenance: 50% Kaggle / 50% Synthetic / 0% Real Classroom | Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            callout_style,
        ))
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceBefore=2, spaceAfter=10))

        # 2. Executive Overview Table
        elements.append(Paragraph("1. Observable Activity Summary", heading_style))
        overview_data = [
            ["Metric", "Observed Value", "Interpretation Notes"],
            ["Unique Anonymous Tracks", str(analytics.uniqueAnonymousTracksObserved), "Tracks observed in video frames; not student count"],
            ["Total Hand-Raising Events", str(analytics.totalHandRaisingEvents), "Single continuous episodes aggregated via Phase 2.2 FSM"],
            ["Left-Hand Events", f"{analytics.leftHandEvents} ({analytics.eventTypeDistribution.leftHandPct}%)", "Anatomically validated shoulder-wrist geometry"],
            ["Right-Hand Events", f"{analytics.rightHandEvents} ({analytics.eventTypeDistribution.rightHandPct}%)", "Anatomically validated shoulder-wrist geometry"],
            ["Both-Hands Events", f"{analytics.bothHandEvents} ({analytics.eventTypeDistribution.bothHandsPct}%)", "Concurrent bilateral elevation episodes"],
            ["Average Gesture Duration", f"{analytics.averageEventDurationSeconds} s", "Mean duration of sustained hand elevation"],
            ["Maximum Gesture Duration", f"{analytics.maxEventDurationSeconds} s", "Longest continuous hand raise recorded"],
            ["Peak Participation Window", analytics.peakParticipationInterval or "N/A", "Interval with highest event density"],
        ]
        t_overview = Table(overview_data, colWidths=[170, 130, 240])
        t_overview.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ]))
        elements.append(t_overview)
        elements.append(Spacer(1, 10))

        # 3. Timeline Intervals Table (Top 10)
        elements.append(Paragraph("2. Participation Frequency Over Time (Sample Intervals)", heading_style))
        timeline_rows = [["Interval Label", "Total Events", "Left Hand", "Right Hand", "Both Hands", "Active Tracks"]]
        for b in analytics.timeline[:10]:
            timeline_rows.append([
                b.label,
                str(b.eventCount),
                str(b.leftHandCount),
                str(b.rightHandCount),
                str(b.bothHandsCount),
                str(b.activeTracksCount),
            ])
        t_timeline = Table(timeline_rows, colWidths=[120, 80, 80, 80, 80, 100])
        t_timeline.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ]))
        elements.append(t_timeline)
        elements.append(Spacer(1, 10))

        # 4. Anonymous Tracks Breakdown
        elements.append(Paragraph("3. Anonymous Track Participation Distribution", heading_style))
        track_rows = [["Track ID", "Events", "Total Duration", "Avg Duration", "Left Hand", "Right Hand", "Both Hands"]]
        for t in analytics.trackSummaries[:8]:
            track_rows.append([
                t.trackId,
                str(t.eventCount),
                f"{t.totalDurationSeconds} s",
                f"{t.avgDurationSeconds} s",
                str(t.leftHandCount),
                str(t.rightHandCount),
                str(t.bothHandsCount),
            ])
        t_tracks = Table(track_rows, colWidths=[100, 70, 80, 80, 70, 70, 70])
        t_tracks.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ]))
        elements.append(t_tracks)
        elements.append(Spacer(1, 12))

        # 5. Ethical & Privacy Safeguards
        elements.append(Paragraph("4. Academic Ethics & Interpretation Boundaries", heading_style))
        elements.append(Paragraph(
            "<b>Objective Physical Reporting:</b> This report reflects observable physical movements only. "
            "The system does not measure or infer attention, concentration, emotional affect, cognitive engagement, "
            "or student intelligence. Track IDs are anonymous and session-scoped. Facial images and biometric "
            "identifications are strictly prohibited.",
            body_style,
        ))

        doc.build(elements)
        return str(filepath)


# Singleton Activity Analytics Engine
analytics_engine = ClassroomActivityAnalyticsEngine()

