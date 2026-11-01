"""
backend/app/database/models.py — SQLAlchemy ORM Models
=======================================================
All data sources are clearly labeled:
  data_source: "KAGGLE_DATA" | "SYNTHETIC_DATA" | "PRETRAINED_MODEL" | "DEMO_DATA" | "REAL_PROCESSING"
No student identity data is stored — only anonymous tracking IDs.
"""

from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class Session(Base):
    """Classroom session record (real or demo)."""

    __tablename__ = "sessions"

    id = Column(String(64), primary_key=True)
    title = Column(String(256), nullable=False)
    course_code = Column(String(32))
    date = Column(String(16))
    start_time = Column(String(16))
    duration_minutes = Column(Integer)
    classroom = Column(String(128))
    instructor = Column(String(128))
    status = Column(String(32), default="active")
    data_source = Column(String(32), default="DEMO_DATA")  # DEMO_DATA | KAGGLE_DATA | SYNTHETIC_DATA | REAL_PROCESSING
    privacy_protected = Column(Boolean, default=True)
    instructor_roi_polygon = Column(JSON, nullable=True, default=None)  # Normalized [[x, y], ...]
    zone_filtering_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    # Relationships
    detection_events = relationship("DetectionEvent", back_populates="session", cascade="all, delete-orphan")
    transcripts = relationship("Transcript", back_populates="session", cascade="all, delete-orphan")
    ocr_results = relationship("OcrResult", back_populates="session", cascade="all, delete-orphan")
    nlp_results = relationship("NlpResult", back_populates="session", cascade="all, delete-orphan")
    processing_results = relationship("ProcessingResult", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Session id={self.id!r} title={self.title!r}>"


class DetectionEvent(Base):
    """Computer vision detection event — single frame analysis result."""

    __tablename__ = "detection_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.id"), nullable=False)
    frame_index = Column(Integer, default=0)
    timestamp_seconds = Column(Float, default=0.0)
    person_count = Column(Integer, default=0)
    hand_raised_count = Column(Integer, default=0)
    hand_not_raised_count = Column(Integer, default=0)
    bounding_boxes = Column(JSON, default=list)     # List[dict] — no face data
    keypoints = Column(JSON, default=list)           # Pose keypoints — no face data
    confidence_scores = Column(JSON, default=list)
    processing_fps = Column(Float)
    model_used = Column(String(64))                 # "yolov8n", "yolov8n-pose", "mediapipe"
    data_source = Column(String(32), default="REAL_PROCESSING")
    notes = Column(Text)
    created_at = Column(DateTime, default=_now)

    session = relationship("Session", back_populates="detection_events")

    def __repr__(self) -> str:
        return f"<DetectionEvent session={self.session_id!r} frame={self.frame_index}>"


class HandRaiseEventRecord(Base):
    """Phase 2.2: Temporal hand-raising event aggregated across consecutive video frames."""

    __tablename__ = "hand_raise_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, nullable=False)
    session_id = Column(String(64), ForeignKey("sessions.id"), nullable=False)
    track_id = Column(String(64), nullable=False)
    hand_side = Column(String(32), default="NONE")       # LEFT_HAND, RIGHT_HAND, BOTH_HANDS
    state = Column(String(32), default="COMPLETED")      # RAISED, COMPLETED, NEEDS_REVIEW
    zone_classification = Column(String(32), default="STUDENT_ZONE")  # STUDENT_ZONE, INSTRUCTOR_ZONE, NEEDS_REVIEW
    start_timestamp_seconds = Column(Float, default=0.0)
    end_timestamp_seconds = Column(Float, default=0.0)
    duration_seconds = Column(Float, default=0.0)
    start_frame = Column(Integer, default=0)
    end_frame = Column(Integer, default=0)
    frame_count = Column(Integer, default=1)
    max_confidence = Column(Float, default=0.0)
    avg_confidence = Column(Float, default=0.0)
    evidence = Column(JSON, default=dict)
    data_source = Column(String(32), default="REAL_PROCESSING")
    created_at = Column(DateTime, default=_now)

    session = relationship("Session", backref="hand_raise_events")

    def __repr__(self) -> str:
        return f"<HandRaiseEventRecord event_id={self.event_id!r} track={self.track_id!r} side={self.hand_side!r}>"


class ActivityEventRecord(Base):
    """Observable physical activity event based on body posture and visible objects."""

    __tablename__ = "activity_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, nullable=False)
    session_id = Column(String(64), ForeignKey("sessions.id"), nullable=False)
    track_id = Column(String(64), nullable=False)
    activity_label = Column(String(64), nullable=False)  # NO_FLAG_OBSERVED, HEAD_DOWN_POSTURE, PHONE_VISIBLE, etc.
    display_label = Column(String(64), nullable=False)
    status_color = Column(String(16), default="GREEN")    # GREEN, RED, ORANGE, BLUE, YELLOW
    status = Column(String(32), default="COMPLETED")      # ACTIVE, COMPLETED, NEEDS_REVIEW
    start_timestamp_seconds = Column(Float, default=0.0)
    end_timestamp_seconds = Column(Float, default=0.0)
    duration_seconds = Column(Float, default=0.0)
    start_frame = Column(Integer, default=0)
    end_frame = Column(Integer, default=0)
    frame_count = Column(Integer, default=1)
    confidence = Column(Float, default=0.0)
    evidence_source = Column(String(64), default="YOLOv8")
    evidence_details = Column(JSON, default=dict)
    data_source = Column(String(32), default="REAL_PROCESSING")
    created_at = Column(DateTime, default=_now)

    session = relationship("Session", backref="activity_events")

    def __repr__(self) -> str:
        return f"<ActivityEventRecord event_id={self.event_id!r} track={self.track_id!r} label={self.activity_label!r}>"



class Transcript(Base):
    """Speech transcription result from Faster-Whisper."""

    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.id"), nullable=False)
    audio_filename = Column(String(256))
    language = Column(String(8), default="en")
    full_text = Column(Text)
    segments = Column(JSON, default=list)   # List[{start, end, text}]
    word_count = Column(Integer, default=0)
    duration_seconds = Column(Float)
    model_used = Column(String(64), default="faster-whisper-tiny")
    data_source = Column(String(32), default="REAL_PROCESSING")
    created_at = Column(DateTime, default=_now)

    session = relationship("Session", back_populates="transcripts")


class OcrResult(Base):
    """Whiteboard / slide OCR result from EasyOCR."""

    __tablename__ = "ocr_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.id"), nullable=False)
    image_filename = Column(String(256))
    extracted_text = Column(Text)
    text_blocks = Column(JSON, default=list)   # List[{text, confidence, bbox}]
    overall_confidence = Column(Float)
    engine = Column(String(64), default="EasyOCR")
    data_source = Column(String(32), default="REAL_PROCESSING")
    created_at = Column(DateTime, default=_now)

    session = relationship("Session", back_populates="ocr_results")


class NlpResult(Base):
    """NLP analysis result for a transcript."""

    __tablename__ = "nlp_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.id"), nullable=False)
    source_type = Column(String(32))     # "transcript" | "ocr" | "combined"
    keywords = Column(JSON, default=list)
    topics = Column(JSON, default=list)
    summary = Column(Text)
    sentiment_label = Column(String(32))   # Only course-level sentiment, not individual
    model_used = Column(String(128))
    data_source = Column(String(32), default="REAL_PROCESSING")
    created_at = Column(DateTime, default=_now)

    session = relationship("Session", back_populates="nlp_results")


class RagDocument(Base):
    """Document indexed in the RAG vector store."""

    __tablename__ = "rag_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64))   # Optional — can be global
    doc_type = Column(String(32))     # "transcript" | "ocr_notes" | "uploaded_pdf"
    filename = Column(String(256))
    chunk_index = Column(Integer, default=0)
    content = Column(Text)
    embedding_model = Column(String(128))
    chroma_doc_id = Column(String(256))
    data_source = Column(String(32), default="REAL_PROCESSING")
    created_at = Column(DateTime, default=_now)


class ProcessingResult(Base):
    """Generic processing job result record."""

    __tablename__ = "processing_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.id"), nullable=False)
    job_type = Column(String(64))     # "vision", "speech", "ocr", "nlp", "rag"
    status = Column(String(32))       # "pending", "processing", "completed", "failed"
    input_file = Column(String(512))
    output_summary = Column(JSON)
    error_message = Column(Text)
    processing_time_seconds = Column(Float)
    data_source = Column(String(32), default="REAL_PROCESSING")
    created_at = Column(DateTime, default=_now)
    completed_at = Column(DateTime)

    session = relationship("Session", back_populates="processing_results")


class DatasetRecord(Base):
    """Dataset metadata registry — tracks what datasets are available."""

    __tablename__ = "dataset_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False)
    dataset_type = Column(String(64))   # "hand_gesture", "classroom_behavior", "speech", etc.
    source = Column(String(32))         # "KAGGLE_DATA" | "SYNTHETIC_DATA"
    path = Column(String(512))
    num_samples = Column(Integer, default=0)
    num_classes = Column(Integer)
    split = Column(String(16))          # "train" | "test" | "val" | "all"
    size_bytes = Column(Integer)
    checksum_verified = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=_now)


class ModelRecord(Base):
    """Model checkpoint registry."""

    __tablename__ = "model_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False)
    model_type = Column(String(64))         # "yolov8n", "whisper", "easyocr", etc.
    version = Column(String(64))
    checkpoint_path = Column(String(512))
    is_pretrained = Column(Boolean, default=True)
    is_loaded = Column(Boolean, default=False)
    load_status = Column(String(32), default="NOT_LOADED")
    accuracy_metric = Column(String(128))   # e.g. "mAP50: NOT_EVALUATED"
    data_source = Column(String(32), default="PRETRAINED_MODEL")
    notes = Column(Text)
    created_at = Column(DateTime, default=_now)
    last_used = Column(DateTime)


class Report(Base):
    """Generated report record."""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(256), nullable=False)
    report_type = Column(String(32))    # "session" | "analytics" | "dataset" | "model"
    format = Column(String(8))          # "pdf" | "xlsx" | "json"
    file_path = Column(String(512))
    session_id = Column(String(64))     # Optional — report may cover multiple sessions
    data_source = Column(String(32), default="DEMO_DATA")
    report_metadata = Column(JSON)
    created_at = Column(DateTime, default=_now)


class AppSettings(Base):
    """Persisted application settings (key-value store)."""

    __tablename__ = "app_settings"

    key = Column(String(128), primary_key=True)
    value = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime, default=_now, onupdate=_now)


# =============================================================================
# Autonomous Multi-Agent Software Engineering Records
# =============================================================================

class AgentTaskRecord(Base):
    """Persistent record of an autonomous engineering task and DAG plan."""

    __tablename__ = "agent_tasks"

    id = Column(String(64), primary_key=True)
    title = Column(String(256), nullable=False)
    description = Column(Text)
    priority = Column(String(16), default="MEDIUM")
    status = Column(String(32), default="PENDING")
    assigned_agents = Column(JSON, default=list)
    dependencies = Column(JSON, default=list)
    acceptance_criteria = Column(JSON, default=list)
    plan = Column(JSON, default=list)
    progress = Column(Float, default=0.0)
    result_summary = Column(Text)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)
    completed_at = Column(DateTime, nullable=True)


class AgentMessageRecord(Base):
    """Message audit log exchanged across the central agent communication bus."""

    __tablename__ = "agent_messages"

    id = Column(String(64), primary_key=True)
    task_id = Column(String(64), nullable=True)
    sender_agent = Column(String(64), nullable=False)
    receiver_agent = Column(String(64), nullable=False)
    message_type = Column(String(32), nullable=False)
    content = Column(JSON, default=dict)
    status = Column(String(32), default="DELIVERED")
    timestamp = Column(DateTime, default=_now)


class AgentExecutionRecord(Base):
    """Auditable log of controlled tool operations executed by an agent."""

    __tablename__ = "agent_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), nullable=True)
    agent_id = Column(String(64), nullable=False)
    action = Column(String(128))
    tool_name = Column(String(64))
    tool_input = Column(JSON, default=dict)
    tool_output = Column(JSON, default=dict)
    status = Column(String(32), default="SUCCESS")
    duration_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=_now)


class AgentDebuggingRecord(Base):
    """Diagnostic trace and resolution history tracked by the Debugging Engine."""

    __tablename__ = "agent_debugging_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), nullable=False)
    error_message = Column(Text, nullable=False)
    error_severity = Column(String(16), default="MEDIUM")
    stack_trace = Column(Text)
    root_cause = Column(Text)
    affected_files = Column(JSON, default=list)
    fix_description = Column(Text)
    repair_attempt = Column(Integer, default=1)
    max_attempts = Column(Integer, default=3)
    tests_executed = Column(JSON, default=list)
    status = Column(String(32), default="ANALYZING")
    created_at = Column(DateTime, default=_now)
    resolved_at = Column(DateTime, nullable=True)


class AgentApprovalRecord(Base):
    """High-risk operations awaiting human approval."""

    __tablename__ = "agent_approvals"

    id = Column(String(64), primary_key=True)
    task_id = Column(String(64), nullable=False)
    agent_id = Column(String(64), nullable=False)
    action_type = Column(String(64), nullable=False)
    description = Column(Text)
    details = Column(JSON, default=dict)
    status = Column(String(32), default="PENDING")
    reviewed_by = Column(String(64), nullable=True)
    review_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now)
    reviewed_at = Column(DateTime, nullable=True)


class AgentMemoryRecord(Base):
    """Structured persistent engineering knowledge and project memory."""

    __tablename__ = "agent_memory_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(64), nullable=False)
    key = Column(String(256), nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, default=dict)
    updated_at = Column(DateTime, default=_now, onupdate=_now)


