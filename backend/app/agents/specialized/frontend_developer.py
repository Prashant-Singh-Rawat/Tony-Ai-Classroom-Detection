"""
backend/app/agents/specialized/frontend_developer.py — Frontend Developer Agent (Agent 3)
========================================================================================
Develops React 19 components, TypeScript logic, responsive dashboards, and connects frontend APIs.
Preserves existing Tailwind v4 and Lucide-React styling conventions.
"""

from __future__ import annotations
from typing import Any, Dict

from backend.app.agents.core.base_agent import BaseAgent
from backend.app.agents.core.types import AgentRole, AgentStatus, ToolPermissionLevel
from backend.app.agents.providers.provider_manager import provider_manager
from backend.app.agents.tools.file_tools import list_directory, read_file


class FrontendDeveloperAgent(BaseAgent):
    """Agent 3: Frontend Developer — React 19, TypeScript, Tailwind v4 UI implementation."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="frontend_developer",
            role=AgentRole.FRONTEND_DEVELOPER,
            name="Frontend Developer Agent",
            responsibility="Develops React 19 components, TypeScript contracts, UI telemetry HUDs, and WebSocket frontends.",
            capabilities=[
                "react_development",
                "typescript_typing",
                "tailwind_styling",
                "websocket_ui_integration",
                "ui_bug_fixing",
            ],
            permission_level=ToolPermissionLevel.SAFE_WRITE,
            system_prompt=(
                "You are the Frontend Developer Agent for ClassVision AI. You build and maintain React 19, "
                "TypeScript, Vite, and Tailwind CSS v4 components. You ensure consistent dark obsidian UI design."
            ),
        )

    def execute_step(
        self,
        task_id: str,
        instruction: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        self.set_status(AgentStatus.EXECUTING, f"Executing frontend step: {instruction[:60]}")

        pages = list_directory("frontend/src/pages", max_depth=1)

        prompt = (
            f"Instruction: {instruction}\n"
            f"Existing Frontend Pages: {pages}\n"
            "Produce frontend implementation analysis, component plan, and TypeScript contract alignment."
        )

        response = provider_manager.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
        )

        self.record_success("Frontend step completed successfully.")
        return {
            "agent": self.agent_id,
            "instruction": instruction,
            "frontend_output": response.content,
            "status": "COMPLETED",
        }

