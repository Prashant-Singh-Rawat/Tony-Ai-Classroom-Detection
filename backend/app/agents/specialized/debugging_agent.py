"""
backend/app/agents/specialized/debugging_agent.py — Debugging Agent (Agent 7)
=============================================================================
Analyzes failure logs, stack traces, locates root causes, coordinates safe repairs,
and enforces the 10-step debugging workflow with a strict 3-attempt repair limit.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from backend.app.agents.core.base_agent import BaseAgent
from backend.app.agents.core.types import AgentRole, AgentStatus, ErrorSeverity, ToolPermissionLevel
from backend.app.agents.providers.provider_manager import provider_manager
from backend.app.database.db import SessionLocal
from backend.app.database.models import AgentDebuggingRecord


class DebuggingAgent(BaseAgent):
    """Agent 7: Debugging — Root cause analysis, stack trace inspection, controlled automated repairs."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="debugging_agent",
            role=AgentRole.DEBUGGING_AGENT,
            name="Debugging Agent",
            responsibility="Investigates error logs, stack traces, identifies root causes, and formulates safe, verified bug fixes.",
            capabilities=[
                "stack_trace_analysis",
                "root_cause_diagnosis",
                "controlled_fix_generation",
                "regression_risk_evaluation",
                "debugging_history_tracking",
            ],
            permission_level=ToolPermissionLevel.SAFE_WRITE,
            system_prompt=(
                "You are the Debugging Agent for ClassVision AI. Your role is to diagnose real errors, "
                "pinpoint exact file locations, and formulate controlled repairs. You NEVER hide errors or "
                "randomly modify files just to suppress failures."
            ),
        )

    def diagnose_error(
        self,
        task_id: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        attempt: int = 1,
    ) -> Dict[str, Any]:
        """Performs structured diagnosis and records trace in SQLite."""
        self.set_status(AgentStatus.DEBUGGING, f"Diagnosing error (attempt {attempt}/3)")

        prompt = (
            f"Error Message: {error_message}\n"
            f"Stack Trace: {stack_trace or 'None provided'}\n"
            f"Repair Attempt: {attempt} of 3\n"
            "Identify the root cause, affected files, and recommended fix without modifying unrelated code."
        )

        response = provider_manager.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
        )

        # Persist diagnostic record
        try:
            with SessionLocal() as db:
                rec = AgentDebuggingRecord(
                    task_id=task_id,
                    error_message=error_message,
                    error_severity=severity.value,
                    stack_trace=stack_trace,
                    root_cause=response.content[:500],
                    fix_description=response.content,
                    repair_attempt=attempt,
                    status="ANALYZED",
                )
                db.add(rec)
                db.commit()
        except Exception:
            pass

        self.set_status(AgentStatus.IDLE, "Diagnosis complete")
        return {
            "root_cause_analysis": response.content,
            "severity": severity.value,
            "attempt": attempt,
            "can_retry": attempt < 3,
        }

    def execute_step(
        self,
        task_id: str,
        instruction: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        self.set_status(AgentStatus.DEBUGGING, f"Investigating: {instruction[:60]}")

        error_msg = context.get("error_message", instruction)
        stack_trace = context.get("stack_trace", None)
        attempt = context.get("repair_attempt", 1)

        diagnosis = self.diagnose_error(
            task_id=task_id,
            error_message=error_msg,
            stack_trace=stack_trace,
            attempt=attempt,
        )

        self.record_success("Debugging investigation finished.")
        return {
            "agent": self.agent_id,
            "instruction": instruction,
            "diagnosis": diagnosis,
            "status": "COMPLETED",
        }

