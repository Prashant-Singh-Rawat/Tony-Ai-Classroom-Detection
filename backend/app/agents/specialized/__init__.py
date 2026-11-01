"""
backend/app/agents/specialized/__init__.py
"""

from backend.app.agents.specialized.project_manager import ProjectManagerAgent
from backend.app.agents.specialized.architect import SoftwareArchitectAgent
from backend.app.agents.specialized.frontend_developer import FrontendDeveloperAgent
from backend.app.agents.specialized.backend_developer import BackendDeveloperAgent
from backend.app.agents.specialized.aiml_engineer import AIMLEngineerAgent
from backend.app.agents.specialized.dataset_manager_agent import DatasetManagementAgent
from backend.app.agents.specialized.debugging_agent import DebuggingAgent
from backend.app.agents.specialized.testing_agent import TestingQAAgent
from backend.app.agents.specialized.code_review_agent import CodeReviewSecurityAgent
from backend.app.agents.specialized.documentation_agent import DocumentationAgent
from backend.app.agents.specialized.devops_agent import DevOpsEnvironmentAgent
from backend.app.agents.specialized.supervisor_agent import SupervisorAgent

__all__ = [
    "ProjectManagerAgent",
    "SoftwareArchitectAgent",
    "FrontendDeveloperAgent",
    "BackendDeveloperAgent",
    "AIMLEngineerAgent",
    "DatasetManagementAgent",
    "DebuggingAgent",
    "TestingQAAgent",
    "CodeReviewSecurityAgent",
    "DocumentationAgent",
    "DevOpsEnvironmentAgent",
    "SupervisorAgent",
]

