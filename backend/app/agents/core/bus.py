"""
backend/app/agents/core/bus.py — Central Multi-Agent Message Bus
================================================================
Routes structured agent-to-agent and agent-to-orchestrator messages,
persisting every communication to SQLite for auditable traceability.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from backend.app.agents.core.types import MessageType
from backend.app.database.db import SessionLocal
from backend.app.database.models import AgentMessageRecord
from backend.app.schemas.agents import AgentMessageSchema


class MessageBus:
    """Central managed communication bus for autonomous agents."""

    def __init__(self) -> None:
        self._subscribers: List[Callable[[AgentMessageSchema], None]] = []

    def subscribe(self, callback: Callable[[AgentMessageSchema], None]) -> None:
        """Registers a listener callback for real-time WebSocket broadcasting."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[AgentMessageSchema], None]) -> None:
        """Removes an active listener callback."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def publish(
        self,
        sender_agent: str,
        receiver_agent: str,
        message_type: MessageType,
        content: Dict[str, Any],
        task_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> AgentMessageSchema:
        """
        Publishes a typed message onto the bus, records it in SQLite,
        and dispatches it to registered streaming subscribers.
        """
        msg_id = message_id or f"msg_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        schema_msg = AgentMessageSchema(
            messageId=msg_id,
            taskId=task_id,
            senderAgent=sender_agent,
            receiverAgent=receiver_agent,
            messageType=message_type,
            content=content,
            status="DELIVERED",
            timestamp=now_iso,
        )

        # Persist to SQLite
        try:
            with SessionLocal() as db:
                record = AgentMessageRecord(
                    id=msg_id,
                    task_id=task_id,
                    sender_agent=sender_agent,
                    receiver_agent=receiver_agent,
                    message_type=message_type.value,
                    content=content,
                    status="DELIVERED",
                )
                db.add(record)
                db.commit()
        except Exception:
            pass

        # Dispatch to subscribers
        for callback in list(self._subscribers):
            try:
                callback(schema_msg)
            except Exception:
                pass

        return schema_msg

    def get_messages(
        self,
        task_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AgentMessageSchema]:
        """Retrieves recent message history from database."""
        try:
            with SessionLocal() as db:
                query = db.query(AgentMessageRecord)
                if task_id:
                    query = query.filter(AgentMessageRecord.task_id == task_id)
                records = query.order_by(AgentMessageRecord.timestamp.desc()).limit(limit).all()

                return [
                    AgentMessageSchema(
                        messageId=r.id,
                        taskId=r.task_id,
                        senderAgent=r.sender_agent,
                        receiverAgent=r.receiver_agent,
                        messageType=MessageType(r.message_type),
                        content=r.content or {},
                        status=r.status,
                        timestamp=r.timestamp.isoformat() if r.timestamp else datetime.now(timezone.utc).isoformat(),
                    )
                    for r in reversed(records)
                ]
        except Exception:
            return []


# Global singleton instance
agent_bus = MessageBus()

