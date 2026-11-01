"""
backend/app/services/database/session_repository.py — Session Data Access Layer
==============================================================================
Provides access to session records. Strictly distinguishes real classroom
records from demonstration sessions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional
from backend.app.core.config import REPO_ROOT
from backend.app.schemas.sessions import SessionInfo


DEMO_SESSIONS_DATA: List[SessionInfo] = [
    SessionInfo(
        sessionId="sess_01",
        title="CS402: Convolutional Neural Networks & Optimization",
        courseCode="CS402",
        date="2026-10-12",
        startTime="09:15 AM",
        durationMinutes=45,
        classroom="Lecture Hall 302",
        instructor="Dr. A. Sharma",
        status="active",
        totalStudents=28,
        activeHandRaises=4,
        totalHandRaiseEvents=19,
        averageEngagement=86.4,
        privacyProtected=True,
    ),
    SessionInfo(
        sessionId="sess_02",
        title="MATH301: Linear Algebra & Eigendecompositions",
        courseCode="MATH301",
        date="2026-10-12",
        startTime="11:00 AM",
        durationMinutes=50,
        classroom="Seminar Room 105",
        instructor="Prof. K. Verma",
        status="completed",
        totalStudents=18,
        activeHandRaises=0,
        totalHandRaiseEvents=12,
        averageEngagement=78.2,
        privacyProtected=True,
    ),
    SessionInfo(
        sessionId="sess_03",
        title="EE204: Signals, Transforms & Nyquist Sampling",
        courseCode="EE204",
        date="2026-10-13",
        startTime="02:00 PM",
        durationMinutes=55,
        classroom="Hall 401",
        instructor="Dr. M. Iyer",
        status="completed",
        totalStudents=34,
        activeHandRaises=0,
        totalHandRaiseEvents=24,
        averageEngagement=82.0,
        privacyProtected=True,
    ),
]


class SessionRepository:
    """Repository accessing real metadata and demo fallback sessions."""

    def __init__(self, data_root: Optional[Path] = None) -> None:
        self.data_root = data_root or (REPO_ROOT / "datasets" / "real_classroom")

    def get_real_sessions(self) -> List[SessionInfo]:
        """Loads real classroom sessions from metadata if present."""
        metadata_file = self.data_root / "metadata" / "sessions.json"
        if metadata_file.is_file():
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
                    return [SessionInfo(**rec) for rec in records]
            except Exception:
                return []
        return []

    def get_all_sessions(self, include_demo: bool = True) -> List[SessionInfo]:
        """Returns sessions according to mode."""
        real_sessions = self.get_real_sessions()
        if real_sessions:
            return real_sessions
        if include_demo:
            return list(DEMO_SESSIONS_DATA)
        return []

    def get_by_id(self, session_id: str, include_demo: bool = True) -> Optional[SessionInfo]:
        """Looks up a session by ID."""
        for s in self.get_real_sessions():
            if s.sessionId == session_id:
                return s
        if include_demo:
            for s in DEMO_SESSIONS_DATA:
                if s.sessionId == session_id:
                    return s
        return None


session_repository = SessionRepository()

