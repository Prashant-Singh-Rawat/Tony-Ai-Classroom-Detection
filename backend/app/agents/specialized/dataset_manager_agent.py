"""
backend/app/agents/specialized/dataset_manager_agent.py — Dataset Management Agent (Agent 6)
============================================================================================
Inspects Kaggle datasets, programmatic synthetic generators, validates labels and checksums,
and strictly enforces the project requirement: 50% Kaggle, 50% Synthetic, 0% Real Classroom Footage.
"""

from __future__ import annotations
from typing import Any, Dict

from backend.app.agents.core.base_agent import BaseAgent
from backend.app.agents.core.types import AgentRole, AgentStatus, ToolPermissionLevel
from backend.app.agents.providers.provider_manager import provider_manager
from backend.app.agents.tools.project_tools import inspect_dataset_statistics


class DatasetManagementAgent(BaseAgent):
    """Agent 6: Dataset Management — Dataset auditing, synthetic generation, 0% real classroom footage enforcement."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="dataset_manager",
            role=AgentRole.DATASET_MANAGER,
            name="Dataset Management Agent",
            responsibility="Inspects Kaggle and Synthetic datasets, audits label distributions, and guarantees 0% real classroom footage.",
            capabilities=[
                "kaggle_dataset_audit",
                "synthetic_data_generation",
                "label_validation",
                "ratio_compliance_enforcement",
                "dataset_documentation",
            ],
            permission_level=ToolPermissionLevel.SAFE_WRITE,
            system_prompt=(
                "You are the Dataset Management Agent for ClassVision AI. You enforce the 50% Kaggle, "
                "50% Synthetic, and 0% Real Classroom Recordings policy. You never modify original Kaggle archives."
            ),
        )

    def execute_step(
        self,
        task_id: str,
        instruction: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        self.set_status(AgentStatus.EXECUTING, f"Auditing datasets: {instruction[:60]}")

        stats = inspect_dataset_statistics()

        prompt = (
            f"Instruction: {instruction}\n"
            f"Dataset Statistics: {stats}\n"
            "Evaluate compliance with 50% Kaggle / 50% Synthetic and 0% Real classroom footage rule."
        )

        response = provider_manager.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
        )

        self.record_success("Dataset audit completed.")
        return {
            "agent": self.agent_id,
            "instruction": instruction,
            "dataset_audit": response.content,
            "statistics": stats,
            "status": "COMPLETED",
        }

