"""
backend/app/agents/core/base_agent.py — Abstract Base Agent Definition
=======================================================================
Provides lifecycle management, capability scoping, permission validation,
and structured communication across all specialized engineering agents.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.agents.core.types import (
    AgentRole,
    AgentStatus,
    MessageType,
    ToolPermissionLevel,
)
from backend.app.schemas.agents import AgentInfo


class BaseAgent(ABC):
    """Abstract base class for all 12 specialized autonomous engineering agents."""

    def __init__(
        self,
        agent_id: str,
        role: AgentRole,
        name: str,
        responsibility: str,
        capabilities: List[str],
        permission_level: ToolPermissionLevel = ToolPermissionLevel.READ_ONLY,
        system_prompt: str = "",
    ) -> None:
        self.agent_id = agent_id
        self.role = role
        self.name = name
        self.responsibility = responsibility
        self.capabilities = capabilities
        self.permission_level = permission_level
        self.system_prompt = system_prompt

        self.status: AgentStatus = AgentStatus.IDLE
        self.current_task_id: Optional[str] = None
        self.success_count: int = 0
        self.failure_count: int = 0
        self.last_activity: str = "Initialized"

    def get_info(self) -> AgentInfo:
        """Returns structured metadata and live status."""
        return AgentInfo(
            agentId=self.agent_id,
            name=self.name,
            role=self.role,
            responsibility=self.responsibility,
            status=self.status,
            currentTaskId=self.current_task_id,
            lastActivity=self.last_activity,
            successCount=self.success_count,
            failureCount=self.failure_count,
            capabilities=self.capabilities,
            permissionLevel=self.permission_level,
        )

    def set_status(self, status: AgentStatus, activity: Optional[str] = None) -> None:
        """Updates agent activity state and records timestamped description."""
        self.status = status
        if activity:
            self.last_activity = activity

    def record_success(self, activity: str = "Task step completed successfully") -> None:
        """Increments success count and resets status to IDLE."""
        self.success_count += 1
        self.last_activity = activity
        self.status = AgentStatus.IDLE
        self.current_task_id = None

    def record_failure(self, error_message: str) -> None:
        """Increments failure count and sets status to ERROR."""
        self.failure_count += 1
        self.last_activity = f"Error: {error_message}"
        self.status = AgentStatus.ERROR

    @abstractmethod
    def execute_step(
        self,
        task_id: str,
        instruction: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Executes a dedicated plan step assigned to this agent.
        Returns a dictionary containing step output, artifacts, and success status.
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.agent_id!r} role={self.role.value!r} status={self.status.value!r}>"

