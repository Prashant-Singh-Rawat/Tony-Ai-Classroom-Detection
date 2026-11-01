"""
backend/app/agents/registry/agent_registry.py — Central Agent Registry
======================================================================
Maintains, inspects, and manages the lifecycle of all 12 specialized engineering agents.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Union

from backend.app.agents.core.base_agent import BaseAgent
from backend.app.agents.core.types import AgentRole, AgentStatus
from backend.app.schemas.agents import AgentInfo
from backend.app.agents.specialized import (
    AIMLEngineerAgent,
    BackendDeveloperAgent,
    CodeReviewSecurityAgent,
    DatasetManagementAgent,
    DebuggingAgent,
    DevOpsEnvironmentAgent,
    DocumentationAgent,
    FrontendDeveloperAgent,
    ProjectManagerAgent,
    SoftwareArchitectAgent,
    SupervisorAgent,
    TestingQAAgent,
)


class AgentRegistry:
    """Manages the 12 specialized autonomous engineering agents."""

    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {}
        self._initialize_all_agents()

    def _initialize_all_agents(self) -> None:
        """Instantiates all 12 specialized agents."""
        agents_list: List[BaseAgent] = [
            ProjectManagerAgent(),
            SoftwareArchitectAgent(),
            FrontendDeveloperAgent(),
            BackendDeveloperAgent(),
            AIMLEngineerAgent(),
            DatasetManagementAgent(),
            DebuggingAgent(),
            TestingQAAgent(),
            CodeReviewSecurityAgent(),
            DocumentationAgent(),
            DevOpsEnvironmentAgent(),
            SupervisorAgent(),
        ]
        for ag in agents_list:
            self._agents[ag.agent_id] = ag
            # Also key by role enum value for convenient lookups
            self._agents[ag.role.value] = ag

    def get_agent(self, identifier: Union[str, AgentRole]) -> Optional[BaseAgent]:
        """Looks up an agent by ID or Role."""
        key = identifier.value if isinstance(identifier, AgentRole) else identifier
        return self._agents.get(key)

    def list_all_agents(self) -> List[AgentInfo]:
        """Returns structured metadata for all 12 distinct agents."""
        seen = set()
        result = []
        for ag in self._agents.values():
            if ag.agent_id not in seen:
                seen.add(ag.agent_id)
                result.append(ag.get_info())
        return result

    def get_agent_count(self) -> int:
        """Returns total distinct agent count (12)."""
        return len({ag.agent_id for ag in self._agents.values()})

    def get_busy_agents_count(self) -> int:
        """Returns count of agents currently executing tasks."""
        return sum(
            1
            for ag in {ag.agent_id: ag for ag in self._agents.values()}.values()
            if ag.status not in (AgentStatus.IDLE, AgentStatus.COMPLETED, AgentStatus.ERROR)
        )


agent_registry = AgentRegistry()

