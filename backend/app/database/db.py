"""
backend/app/database/db.py — SQLAlchemy Database Engine
========================================================
Manages a local SQLite database for ClassVision AI.
All data is stored locally; no cloud upload.
"""

from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as DBSession

from backend.app.database.models import Base
from backend.app.core.config import REPO_ROOT

# SQLite database lives in the project root — never in datasets/
DB_PATH = REPO_ROOT / "classvision_ai.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite + threading
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Creates all tables if they don't already exist. Safe to call multiple times."""
    Base.metadata.create_all(bind=engine)

    # Lightweight schema migrations for existing SQLite databases
    with engine.connect() as conn:
        try:
            # Check sessions table columns
            columns = [c[1] for c in conn.exec_driver_sql("PRAGMA table_info(sessions)").fetchall()]
            if "instructor_roi_polygon" not in columns:
                conn.exec_driver_sql("ALTER TABLE sessions ADD COLUMN instructor_roi_polygon JSON;")
            if "zone_filtering_enabled" not in columns:
                conn.exec_driver_sql("ALTER TABLE sessions ADD COLUMN zone_filtering_enabled BOOLEAN DEFAULT 1;")

            # Check hand_raise_events table columns
            hre_columns = [c[1] for c in conn.exec_driver_sql("PRAGMA table_info(hand_raise_events)").fetchall()]
            if "zone_classification" not in hre_columns:
                conn.exec_driver_sql("ALTER TABLE hand_raise_events ADD COLUMN zone_classification VARCHAR(32) DEFAULT 'STUDENT_ZONE';")
            conn.commit()
        except Exception:
            pass


def get_db() -> Generator[DBSession, None, None]:
    """FastAPI dependency — yields a database session and ensures proper cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

