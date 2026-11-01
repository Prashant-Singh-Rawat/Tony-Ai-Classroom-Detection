"""
backend/app/agents/specialized/architect.py — Software Architect Agent (Agent 2)
================================================================================
Inspects repository architecture, analyzes existing implementation, designs new modules,
identifies architectural bottlenecks, and prevents unnecessary complexity.
"""

from __future__ import annotations
from typing import Any, Dict

from backend.app.agents.core.base_agent import BaseAgent
from backend.app.agents.core.types import AgentRole, AgentStatus, ToolPermissionLevel
from backend.app.agents.providers.provider_manager import provider_manager
from backend.app.agents.tools.file_tools import list_directory
from backend.app.agents.tools.project_tools import inspect_api_endpoints, inspect_database_schemas


class SoftwareArchitectAgent(BaseAgent):
    """Agent 2: Software Architect — High-level technical design, module boundaries, risk analysis."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="software_architect",
            role=AgentRole.SOFTWARE_ARCHITECT,
            name="Software Architect Agent",
            responsibility="Inspects repository architecture, ensures clean modular boundaries, and assesses technical risks.",
            capabilities=[
                "architecture_inspection",
                "modular_design",
                "dependency_analysis",
                "technical_risk_assessment",
                "refactoring_guidance",
            ],
            permission_level=ToolPermissionLevel.READ_ONLY,
            system_prompt=(
                "You are the Software Architect Agent for ClassVision AI. Your duty is to inspect the codebase, "
                "preserve existing modular architecture, prevent anti-patterns, and evaluate system scalability."
            ),
        )

    def execute_step(
        self,
        task_id: str,
        instruction: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        self.set_status(AgentStatus.EXECUTING, f"Analyzing architecture for: {instruction[:60]}")

        # Introspect project state
        endpoints = inspect_api_endpoints()
        schemas = inspect_database_schemas()
        dir_tree = list_directory(".", max_depth=2)

        prompt = (
            f"Instruction: {instruction}\n"
            f"Context: {context.get('task_title', 'General Architecture Review')}\n"
            f"Discovered Endpoints Count: {len(endpoints)}\n"
            f"Discovered DB Tables Count: {len(schemas)}\n\n"
            "Provide an architectural assessment and risk analysis."
        )

        response = provider_manager.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
        )

        self.record_success("Architecture analyzed successfully.")
        return {
            "agent": self.agent_id,
            "instruction": instruction,
            "architecture_analysis": response.content,
            "endpoints_count": len(endpoints),
            "tables_count": len(schemas),
            "status": "COMPLETED",
        }

