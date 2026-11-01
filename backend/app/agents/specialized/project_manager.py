"""
backend/app/agents/specialized/project_manager.py — Project Manager Agent (Agent 1)
===================================================================================
Receives user requests, understands requirements, breaks tasks into structured DAG steps,
assigns work to specialized agents, and monitors milestone progress.
"""

from __future__ import annotations
from typing import Any, Dict, List

from backend.app.agents.core.base_agent import BaseAgent
from backend.app.agents.core.types import AgentRole, AgentStatus, ToolPermissionLevel
from backend.app.agents.providers.provider_manager import provider_manager
from backend.app.schemas.agents import TaskPlanStep


class ProjectManagerAgent(BaseAgent):
    """Agent 1: Project Manager — Task decomposition, DAG scheduling, milestone tracking."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="project_manager",
            role=AgentRole.PROJECT_MANAGER,
            name="Project Manager Agent",
            responsibility="Receives user requests, decomposes objectives into DAG plans, and monitors execution milestones.",
            capabilities=[
                "task_decomposition",
                "dag_planning",
                "milestone_tracking",
                "priority_management",
                "acceptance_criteria_definition",
            ],
            permission_level=ToolPermissionLevel.READ_ONLY,
            system_prompt=(
                "You are the Project Manager Agent for ClassVision AI. Your responsibility is to break user "
                "requests into structured, sequential, dependency-aware plans assigned to the 12 engineering agents."
            ),
        )

    def decompose_task(self, title: str, description: str) -> List[TaskPlanStep]:
        """Decomposes an engineering request into a structured DAG plan."""
        desc_lower = (title + " " + description).lower()

        # 1. Bug Investigation Plan
        if "bug" in desc_lower or "issue" in desc_lower or "inspect" in desc_lower:
            return [
                TaskPlanStep(
                    stepIndex=1,
                    title="Inspect repository architecture and locate potential bugs",
                    assignedAgent=AgentRole.SOFTWARE_ARCHITECT,
                    dependencies=[],
                    acceptanceCriteria="Analyze codebase and identify genuine technical risks or bugs.",
                ),
                TaskPlanStep(
                    stepIndex=2,
                    title="Perform deep root-cause diagnostic investigation",
                    assignedAgent=AgentRole.DEBUGGING_AGENT,
                    dependencies=[1],
                    acceptanceCriteria="Collect logs, identify exact file locations and failure causes.",
                ),
                TaskPlanStep(
                    stepIndex=3,
                    title="Execute test suite verification",
                    assignedAgent=AgentRole.TESTING_QA,
                    dependencies=[2],
                    acceptanceCriteria="Run relevant tests to verify findings without regressions.",
                ),
                TaskPlanStep(
                    stepIndex=4,
                    title="Perform security, quality, and privacy code review",
                    assignedAgent=AgentRole.CODE_REVIEW_SECURITY,
                    dependencies=[3],
                    acceptanceCriteria="Verify compliance with zero secrets, path guards, and privacy standards.",
                ),
                TaskPlanStep(
                    stepIndex=5,
                    title="Supervisor final verification and acceptance report",
                    assignedAgent=AgentRole.SUPERVISOR,
                    dependencies=[4],
                    acceptanceCriteria="Verify all criteria met and deliver comprehensive task report.",
                ),
            ]

        # 2. Hand-Raise / CV Pipeline Improvement Plan
        if "hand" in desc_lower or "pose" in desc_lower or "vision" in desc_lower or "model" in desc_lower:
            return [
                TaskPlanStep(
                    stepIndex=1,
                    title="Analyze existing Computer Vision and Pose estimation pipeline",
                    assignedAgent=AgentRole.SOFTWARE_ARCHITECT,
                    dependencies=[],
                    acceptanceCriteria="Inspect cv_service and detection schemas for improvement areas.",
                ),
                TaskPlanStep(
                    stepIndex=2,
                    title="Evaluate model inference performance and pose keypoints",
                    assignedAgent=AgentRole.AIML_ENGINEER,
                    dependencies=[1],
                    acceptanceCriteria="Verify YOLOv8n-pose wrist/shoulder elevation accuracy.",
                ),
                TaskPlanStep(
                    stepIndex=3,
                    title="Validate dataset compliance and synthetic test samples",
                    assignedAgent=AgentRole.DATASET_MANAGER,
                    dependencies=[1],
                    acceptanceCriteria="Ensure 50/50 Kaggle/Synthetic ratio with 0% real classroom footage.",
                ),
                TaskPlanStep(
                    stepIndex=4,
                    title="Run end-to-end vision and regression test suites",
                    assignedAgent=AgentRole.TESTING_QA,
                    dependencies=[2, 3],
                    acceptanceCriteria="All backend vision tests and frontend tests pass.",
                ),
                TaskPlanStep(
                    stepIndex=5,
                    title="Supervisor final verification",
                    assignedAgent=AgentRole.SUPERVISOR,
                    dependencies=[4],
                    acceptanceCriteria="Validate live telemetry and deliver milestone summary.",
                ),
            ]

        # 3. Default General Engineering Plan
        return [
            TaskPlanStep(
                stepIndex=1,
                title="Inspect repository architecture and dependencies",
                assignedAgent=AgentRole.SOFTWARE_ARCHITECT,
                dependencies=[],
                acceptanceCriteria="Identify architectural impact and affected modules.",
            ),
            TaskPlanStep(
                stepIndex=2,
                title="Implement required software changes",
                assignedAgent=AgentRole.BACKEND_DEVELOPER,
                dependencies=[1],
                acceptanceCriteria="Implement clean logic preserving existing API contracts.",
            ),
            TaskPlanStep(
                stepIndex=3,
                title="Execute automated regression testing",
                assignedAgent=AgentRole.TESTING_QA,
                dependencies=[2],
                acceptanceCriteria="Pytest and Vitest test suites run clean.",
            ),
            TaskPlanStep(
                stepIndex=4,
                title="Supervisor verification and final acceptance",
                assignedAgent=AgentRole.SUPERVISOR,
                dependencies=[3],
                acceptanceCriteria="Confirm all acceptance criteria satisfied.",
            ),
        ]

    def execute_step(
        self,
        task_id: str,
        instruction: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        self.set_status(AgentStatus.EXECUTING, f"Planning task: {instruction[:60]}")
        response = provider_manager.generate(
            prompt=f"Decompose the following engineering objective into milestones:\n{instruction}",
            system_prompt=self.system_prompt,
        )
        self.record_success("Task plan decomposed and assigned.")
        return {
            "agent": self.agent_id,
            "instruction": instruction,
            "plan_summary": response.content,
            "status": "COMPLETED",
        }

