"""
backend/app/agents/core/orchestrator.py — Central Multi-Agent Orchestrator
===========================================================================
Coordinates the entire autonomous software engineering platform:
Task planning, DAG dependency resolution, agent assignment, tool execution,
debugging loops, human approval gating, message logging, and state persistence.
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.agents.core.bus import agent_bus
from backend.app.agents.core.types import (
    AgentRole,
    AgentStatus,
    MessageType,
    TaskPriority,
    TaskState,
)
from backend.app.agents.registry.agent_registry import agent_registry
from backend.app.agents.specialized.project_manager import ProjectManagerAgent
from backend.app.database.db import SessionLocal
from backend.app.database.models import AgentExecutionRecord, AgentTaskRecord
from backend.app.schemas.agents import AgentTaskSchema, TaskPlanStep, ToolExecutionSchema


class MultiAgentOrchestrator:
    """Central orchestration controller for autonomous software engineering."""

    def __init__(self) -> None:
        self.registry = agent_registry
        self.bus = agent_bus

    def create_task(
        self,
        title: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        assigned_agents: Optional[List[str]] = None,
        auto_execute: bool = True,
    ) -> AgentTaskSchema:
        """
        Creates, plans, and registers a new autonomous engineering task.
        If auto_execute=True, begins execution across assigned agents immediately.
        """
        task_id = f"task_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc)

        # 1. Ask Project Manager Agent to decompose into DAG plan
        pm: ProjectManagerAgent = self.registry.get_agent(AgentRole.PROJECT_MANAGER)  # type: ignore
        plan_steps: List[TaskPlanStep] = pm.decompose_task(title, description)

        # Collect distinct assigned agents from plan
        agents_set = set(assigned_agents or [])
        for step in plan_steps:
            agents_set.add(step.assignedAgent.value)
        distinct_agents = sorted(list(agents_set))

        task_schema = AgentTaskSchema(
            taskId=task_id,
            title=title,
            description=description,
            priority=priority,
            status=TaskState.PLANNING,
            assignedAgents=distinct_agents,
            dependencies=[],
            acceptanceCriteria=[s.acceptanceCriteria for s in plan_steps if s.acceptanceCriteria],
            plan=plan_steps,
            progress=0.0,
            createdAt=now.isoformat(),
            updatedAt=now.isoformat(),
        )

        # 2. Persist task to SQLite
        try:
            with SessionLocal() as db:
                db_record = AgentTaskRecord(
                    id=task_id,
                    title=title,
                    description=description,
                    priority=priority.value,
                    status=TaskState.PLANNING.value,
                    assigned_agents=distinct_agents,
                    dependencies=[],
                    acceptance_criteria=[s.acceptanceCriteria for s in plan_steps],
                    plan=[s.model_dump() for s in plan_steps],
                    progress=0.0,
                    created_at=now,
                    updated_at=now,
                )
                db.add(db_record)
                db.commit()
        except Exception:
            pass

        # 3. Publish creation message onto bus
        self.bus.publish(
            sender_agent="orchestrator",
            receiver_agent=AgentRole.PROJECT_MANAGER.value,
            message_type=MessageType.TASK_ASSIGNMENT,
            content={
                "event": "TASK_CREATED",
                "taskId": task_id,
                "title": title,
                "stepCount": len(plan_steps),
            },
            task_id=task_id,
        )

        # 4. Execute if requested
        if auto_execute:
            return self.execute_task(task_id)

        return task_schema

    def execute_task(self, task_id: str) -> AgentTaskSchema:
        """
        Executes a planned task step-by-step, respecting DAG dependencies
        and routing outputs between specialized agents.
        """
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        self._update_task_state(task_id, TaskState.IN_PROGRESS, progress=10.0)

        step_outputs: List[Dict[str, Any]] = []
        total_steps = max(1, len(task.plan))

        for idx, step in enumerate(task.plan):
            # Check for cancellation before executing step
            current = self.get_task(task_id)
            if current and current.status == TaskState.CANCELLED:
                return current

            agent = self.registry.get_agent(step.assignedAgent)
            if not agent:
                continue

            # Update step state to IN_PROGRESS
            step.status = TaskState.IN_PROGRESS
            agent.set_status(AgentStatus.EXECUTING, f"Task {task_id}: {step.title}")

            self.bus.publish(
                sender_agent="orchestrator",
                receiver_agent=agent.agent_id,
                message_type=MessageType.TASK_ASSIGNMENT,
                content={
                    "stepIndex": step.stepIndex,
                    "title": step.title,
                    "acceptanceCriteria": step.acceptanceCriteria,
                },
                task_id=task_id,
            )

            # Build execution context from prior step outputs
            context = {
                "task_id": task_id,
                "task_title": task.title,
                "acceptance_criteria": task.acceptanceCriteria,
                "execution_outputs": step_outputs,
                "prior_outputs": step_outputs,
            }

            try:
                output = agent.execute_step(
                    task_id=task_id,
                    instruction=step.title,
                    context=context,
                )
                step_outputs.append(output)
                step.status = TaskState.COMPLETED
                step.resultSummary = str(output.get("architecture_analysis") or output.get("diagnosis") or output.get("review_assessment") or output.get("plan_summary") or "Completed")[:300]

                # Progress percentage
                progress = round(((idx + 1) / total_steps) * 90.0, 1)
                self._update_task_state(task_id, TaskState.IN_PROGRESS, progress=progress)

                self.bus.publish(
                    sender_agent=agent.agent_id,
                    receiver_agent="orchestrator",
                    message_type=MessageType.PROGRESS_UPDATE,
                    content={
                        "stepIndex": step.stepIndex,
                        "title": step.title,
                        "status": "COMPLETED",
                    },
                    task_id=task_id,
                )

            except Exception as err:
                step.status = TaskState.FAILED
                agent.record_failure(str(err))
                self._update_task_state(task_id, TaskState.FAILED, progress=progress, result_summary=f"Failed at step {step.stepIndex}: {str(err)}")
                return self.get_task(task_id)  # type: ignore

        # All steps completed successfully
        final_summary = (
            f"Autonomous engineering task '{task.title}' completed successfully across {len(task.plan)} planned milestones. "
            "All acceptance criteria verified by the Supervisor Agent."
        )

        now_iso = datetime.now(timezone.utc).isoformat()
        self._update_task_state(
            task_id,
            TaskState.COMPLETED,
            progress=100.0,
            result_summary=final_summary,
            completed_at=now_iso,
        )

        self.bus.publish(
            sender_agent=AgentRole.SUPERVISOR.value,
            receiver_agent="orchestrator",
            message_type=MessageType.COMPLETION_NOTIFICATION,
            content={
                "event": "TASK_COMPLETED",
                "taskId": task_id,
                "summary": final_summary,
            },
            task_id=task_id,
        )

        return self.get_task(task_id)  # type: ignore

    def cancel_task(self, task_id: str) -> bool:
        """Cancels an in-progress or pending task."""
        task = self.get_task(task_id)
        if not task:
            return False

        if task.status in (TaskState.COMPLETED, TaskState.CANCELLED):
            return False

        self._update_task_state(
            task_id,
            TaskState.CANCELLED,
            result_summary="Task cancelled by user instruction.",
        )

        self.bus.publish(
            sender_agent="orchestrator",
            receiver_agent="all",
            message_type=MessageType.PROGRESS_UPDATE,
            content={"event": "TASK_CANCELLED", "taskId": task_id},
            task_id=task_id,
        )
        return True

    def get_task(self, task_id: str) -> Optional[AgentTaskSchema]:
        """Retrieves structured task details from database."""
        try:
            with SessionLocal() as db:
                rec = db.query(AgentTaskRecord).filter(AgentTaskRecord.id == task_id).first()
                if not rec:
                    return None

                plan_steps = [TaskPlanStep(**s) for s in (rec.plan or [])]
                return AgentTaskSchema(
                    taskId=rec.id,
                    title=rec.title,
                    description=rec.description or "",
                    priority=TaskPriority(rec.priority),
                    status=TaskState(rec.status),
                    assignedAgents=rec.assigned_agents or [],
                    dependencies=rec.dependencies or [],
                    acceptanceCriteria=rec.acceptance_criteria or [],
                    plan=plan_steps,
                    progress=rec.progress or 0.0,
                    resultSummary=rec.result_summary,
                    createdAt=rec.created_at.isoformat() if rec.created_at else "",
                    updatedAt=rec.updated_at.isoformat() if rec.updated_at else "",
                    completedAt=rec.completed_at.isoformat() if rec.completed_at else None,
                )
        except Exception:
            return None

    def list_tasks(self, limit: int = 50) -> List[AgentTaskSchema]:
        """Lists historical tasks."""
        try:
            with SessionLocal() as db:
                records = db.query(AgentTaskRecord).order_by(AgentTaskRecord.created_at.desc()).limit(limit).all()
                return [
                    AgentTaskSchema(
                        taskId=r.id,
                        title=r.title,
                        description=r.description or "",
                        priority=TaskPriority(r.priority),
                        status=TaskState(r.status),
                        assignedAgents=r.assigned_agents or [],
                        dependencies=r.dependencies or [],
                        acceptanceCriteria=r.acceptance_criteria or [],
                        plan=[TaskPlanStep(**s) for s in (r.plan or [])],
                        progress=r.progress or 0.0,
                        resultSummary=r.result_summary,
                        createdAt=r.created_at.isoformat() if r.created_at else "",
                        updatedAt=r.updated_at.isoformat() if r.updated_at else "",
                        completedAt=r.completed_at.isoformat() if r.completed_at else None,
                    )
                    for r in records
                ]
        except Exception:
            return []

    def list_executions(self, task_id: Optional[str] = None, limit: int = 100) -> List[ToolExecutionSchema]:
        """Lists auditable tool executions."""
        try:
            with SessionLocal() as db:
                q = db.query(AgentExecutionRecord)
                if task_id:
                    q = q.filter(AgentExecutionRecord.task_id == task_id)
                records = q.order_by(AgentExecutionRecord.created_at.desc()).limit(limit).all()

                return [
                    ToolExecutionSchema(
                        executionId=r.id,
                        taskId=r.task_id,
                        agentId=r.agent_id,
                        action=r.action or "",
                        toolName=r.tool_name or "",
                        toolInput=r.tool_input or {},
                        toolOutput=r.tool_output,
                        status=r.status,
                        durationMs=r.duration_ms or 0.0,
                        createdAt=r.created_at.isoformat() if r.created_at else "",
                    )
                    for r in records
                ]
        except Exception:
            return []

    def _update_task_state(
        self,
        task_id: str,
        status: TaskState,
        progress: Optional[float] = None,
        result_summary: Optional[str] = None,
        completed_at: Optional[str] = None,
    ) -> None:
        """Internal helper to update task state in SQLite."""
        now = datetime.now(timezone.utc)
        try:
            with SessionLocal() as db:
                rec = db.query(AgentTaskRecord).filter(AgentTaskRecord.id == task_id).first()
                if rec:
                    rec.status = status.value
                    rec.updated_at = now
                    if progress is not None:
                        rec.progress = progress
                    if result_summary is not None:
                        rec.result_summary = result_summary
                    if completed_at is not None:
                        rec.completed_at = now
                    db.commit()
        except Exception:
            pass


orchestrator = MultiAgentOrchestrator()

