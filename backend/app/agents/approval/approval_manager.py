"""
backend/app/agents/approval/approval_manager.py — Human Approval Gate System
=============================================================================
Intercepts destructive and high-risk operations, pausing agent execution until
a human engineer formally reviews, approves, or rejects the requested action.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.agents.core.types import ApprovalActionType, ApprovalStatus
from backend.app.database.db import SessionLocal
from backend.app.database.models import AgentApprovalRecord
from backend.app.schemas.agents import ApprovalRequestSchema


class ApprovalManager:
    """Manages authorization checkpoints for destructive actions."""

    def create_request(
        self,
        task_id: str,
        agent_id: str,
        action_type: ApprovalActionType,
        description: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> ApprovalRequestSchema:
        """Creates and persists an approval request, pausing risky execution."""
        app_id = f"appr_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc)
        schema = ApprovalRequestSchema(
            approvalId=app_id,
            taskId=task_id,
            agentId=agent_id,
            actionType=action_type,
            description=description,
            details=details or {},
            status=ApprovalStatus.PENDING,
            createdAt=now.isoformat(),
        )

        try:
            with SessionLocal() as db:
                rec = AgentApprovalRecord(
                    id=app_id,
                    task_id=task_id,
                    agent_id=agent_id,
                    action_type=action_type.value,
                    description=description,
                    details=details or {},
                    status=ApprovalStatus.PENDING.value,
                    created_at=now,
                )
                db.add(rec)
                db.commit()
        except Exception:
            pass

        return schema

    def approve(
        self,
        approval_id: str,
        reviewed_by: str = "engineer",
        comment: Optional[str] = None,
    ) -> bool:
        """Grants authorization for the pending action."""
        now = datetime.now(timezone.utc)
        try:
            with SessionLocal() as db:
                rec = db.query(AgentApprovalRecord).filter(AgentApprovalRecord.id == approval_id).first()
                if not rec or rec.status != ApprovalStatus.PENDING.value:
                    return False

                rec.status = ApprovalStatus.APPROVED.value
                rec.reviewed_by = reviewed_by
                rec.review_comment = comment or "Approved by human engineer."
                rec.reviewed_at = now
                db.commit()
                return True
        except Exception:
            return False

    def reject(
        self,
        approval_id: str,
        reviewed_by: str = "engineer",
        comment: Optional[str] = None,
    ) -> bool:
        """Rejects the action, halting destructive execution."""
        now = datetime.now(timezone.utc)
        try:
            with SessionLocal() as db:
                rec = db.query(AgentApprovalRecord).filter(AgentApprovalRecord.id == approval_id).first()
                if not rec or rec.status != ApprovalStatus.PENDING.value:
                    return False

                rec.status = ApprovalStatus.REJECTED.value
                rec.reviewed_by = reviewed_by
                rec.review_comment = comment or "Rejected by human engineer."
                rec.reviewed_at = now
                db.commit()
                return True
        except Exception:
            return False

    def list_pending(self) -> List[ApprovalRequestSchema]:
        """Lists all actions awaiting human review."""
        try:
            with SessionLocal() as db:
                records = db.query(AgentApprovalRecord).filter(
                    AgentApprovalRecord.status == ApprovalStatus.PENDING.value
                ).all()
                return [
                    ApprovalRequestSchema(
                        approvalId=r.id,
                        taskId=r.task_id,
                        agentId=r.agent_id,
                        actionType=ApprovalActionType(r.action_type),
                        description=r.description or "",
                        details=r.details or {},
                        status=ApprovalStatus(r.status),
                        reviewedBy=r.reviewed_by,
                        reviewComment=r.review_comment,
                        createdAt=r.created_at.isoformat() if r.created_at else "",
                        reviewedAt=r.reviewed_at.isoformat() if r.reviewed_at else None,
                    )
                    for r in records
                ]
        except Exception:
            return []

    def list_all(self, limit: int = 50) -> List[ApprovalRequestSchema]:
        """Lists historical approval requests."""
        try:
            with SessionLocal() as db:
                records = db.query(AgentApprovalRecord).order_by(
                    AgentApprovalRecord.created_at.desc()
                ).limit(limit).all()
                return [
                    ApprovalRequestSchema(
                        approvalId=r.id,
                        taskId=r.task_id,
                        agentId=r.agent_id,
                        actionType=ApprovalActionType(r.action_type),
                        description=r.description or "",
                        details=r.details or {},
                        status=ApprovalStatus(r.status),
                        reviewedBy=r.reviewed_by,
                        reviewComment=r.review_comment,
                        createdAt=r.created_at.isoformat() if r.created_at else "",
                        reviewedAt=r.reviewed_at.isoformat() if r.reviewed_at else None,
                    )
                    for r in records
                ]
        except Exception:
            return []


approval_manager = ApprovalManager()

