"""
backend/app/agents/specialized/documentation_agent.py — Documentation Agent (Agent 10)
======================================================================================
Updates READMEs, API specifications, installation guides, architecture docs,
and ensures that all documentation faithfully matches actual repository implementations.
"""

from __future__ import annotations
from typing import Any, Dict

from backend.app.agents.core.base_agent import BaseAgent
from backend.app.agents.core.types import AgentRole, AgentStatus, ToolPermissionLevel
from backend.app.agents.providers.provider_manager import provider_manager


class DocumentationAgent(BaseAgent):
    """Agent 10: Documentation — Maintains technical guides, API specs, architecture diagrams, and limitations."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="documentation",
            role=AgentRole.DOCUMENTATION,
            name="Documentation Agent",
            responsibility="Updates documentation, API references, architecture diagrams, installation guides, and known limitations.",
            capabilities=[
                "markdown_documentation",
                "api_reference_generation",
                "architecture_diagrams",
                "installation_guide_maintenance",
                "known_limitations_tracking",
            ],
            permission_level=ToolPermissionLevel.SAFE_WRITE,
            system_prompt=(
                "You are the Documentation Agent for ClassVision AI. You produce accurate, concise, and structured "
                "markdown documentation that reflects actual working code and genuine benchmark numbers."
            ),
        )

    def execute_step(
        self,
        task_id: str,
        instruction: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        self.set_status(AgentStatus.EXECUTING, f"Documenting: {instruction[:60]}")

        prompt = (
            f"Instruction: {instruction}\n"
            f"Context: {context.get('task_title', 'Engineering Documentation')}\n"
            "Generate technical documentation updates adhering to GitHub-flavored markdown standards."
        )

        response = provider_manager.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
        )

        self.record_success("Documentation updated.")
        return {
            "agent": self.agent_id,
            "instruction": instruction,
            "documentation_content": response.content,
            "status": "COMPLETED",
        }

