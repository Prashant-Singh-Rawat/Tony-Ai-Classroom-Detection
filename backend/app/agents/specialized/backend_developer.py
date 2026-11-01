"""
backend/app/agents/specialized/backend_developer.py — Backend Developer Agent (Agent 4)
======================================================================================
Develops FastAPI endpoints, implements business logic, manages SQLAlchemy models & repositories,
enforces Pydantic schema validation, and handles exceptions safely.
"""

from __future__ import annotations
from typing import Any, Dict

from backend.app.agents.core.base_agent import BaseAgent
from backend.app.agents.core.types import AgentRole, AgentStatus, ToolPermissionLevel
from backend.app.agents.providers.provider_manager import provider_manager
from backend.app.agents.tools.project_tools import inspect_api_endpoints, inspect_database_schemas


class BackendDeveloperAgent(BaseAgent):
    """Agent 4: Backend Developer — FastAPI endpoints, SQLAlchemy ORM, Pydantic validation."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="backend_developer",
            role=AgentRole.BACKEND_DEVELOPER,
            name="Backend Developer Agent",
            responsibility="Develops FastAPI REST & WebSocket endpoints, business logic, SQLAlchemy ORM, and schema validation.",
            capabilities=[
                "fastapi_endpoint_development",
                "sqlalchemy_orm_persistence",
                "pydantic_schema_validation",
                "websocket_streaming_routes",
                "api_error_handling",
            ],
            permission_level=ToolPermissionLevel.SAFE_WRITE,
            system_prompt=(
                "You are the Backend Developer Agent for ClassVision AI. You develop robust, asynchronous, "
                "well-typed FastAPI endpoints and SQLAlchemy database models while preserving backward compatibility."
            ),
        )

    def execute_step(
        self,
        task_id: str,
        instruction: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        self.set_status(AgentStatus.EXECUTING, f"Executing backend step: {instruction[:60]}")

        routes = inspect_api_endpoints()
        schemas = inspect_database_schemas()

        prompt = (
            f"Instruction: {instruction}\n"
            f"Existing Route Count: {len(routes)}\n"
            f"Existing Table Count: {len(schemas)}\n"
            "Analyze and execute backend implementation step."
        )

        response = provider_manager.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
        )

        self.record_success("Backend step completed.")
        return {
            "agent": self.agent_id,
            "instruction": instruction,
            "backend_output": response.content,
            "status": "COMPLETED",
        }

