"""
backend/app/agents/core/types.py — Multi-Agent System Core Enums & Constants
=============================================================================
Defines standard statuses, roles, message types, and permissions across all 12 agents.
"""

from __future__ import annotations
from enum import Enum


class AgentRole(str, Enum):
    """The 12 specialized engineering agents in ClassVision AI."""

    PROJECT_MANAGER = "project_manager"
    SOFTWARE_ARCHITECT = "software_architect"
    FRONTEND_DEVELOPER = "frontend_developer"
    BACKEND_DEVELOPER = "backend_developer"
    AIML_ENGINEER = "aiml_engineer"
    DATASET_MANAGER = "dataset_manager"
    DEBUGGING_AGENT = "debugging_agent"
    TESTING_QA = "testing_qa"
    CODE_REVIEW_SECURITY = "code_review_security"
    DOCUMENTATION = "documentation"
    DEVOPS_ENVIRONMENT = "devops_environment"
    SUPERVISOR = "supervisor"


class AgentStatus(str, Enum):
    """Runtime activity state of an agent."""

    IDLE = "IDLE"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    TESTING = "TESTING"
    DEBUGGING = "DEBUGGING"
    REVIEWING = "REVIEWING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class TaskState(str, Enum):
    """Strict lifecycle states for agent-managed engineering tasks."""

    PENDING = "PENDING"
    PLANNING = "PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    TESTING = "TESTING"
    REVIEWING = "REVIEWING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskPriority(str, Enum):
    """Task urgency levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MessageType(str, Enum):
    """Formal communication message types exchanged across the agent message bus."""

    TASK_ASSIGNMENT = "TASK_ASSIGNMENT"
    TASK_ACCEPTANCE = "TASK_ACCEPTANCE"
    PROGRESS_UPDATE = "PROGRESS_UPDATE"
    ERROR_REPORT = "ERROR_REPORT"
    FIX_PROPOSAL = "FIX_PROPOSAL"
    REVIEW_FEEDBACK = "REVIEW_FEEDBACK"
    TEST_RESULT = "TEST_RESULT"
    COMPLETION_NOTIFICATION = "COMPLETION_NOTIFICATION"
    APPROVAL_REQUEST = "APPROVAL_REQUEST"
    APPROVAL_RESPONSE = "APPROVAL_RESPONSE"


class ToolPermissionLevel(str, Enum):
    """Execution clearance levels for tools."""

    READ_ONLY = "READ_ONLY"
    SAFE_WRITE = "SAFE_WRITE"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"


class ApprovalActionType(str, Enum):
    """High-risk operations that mandate human confirmation."""

    DELETE_FILE = "DELETE_FILE"
    OVERWRITE_DATASET = "OVERWRITE_DATASET"
    DEPENDENCY_CHANGE = "DEPENDENCY_CHANGE"
    DB_MIGRATION = "DB_MIGRATION"
    EXTERNAL_CALL = "EXTERNAL_CALL"
    CREDENTIAL_ACCESS = "CREDENTIAL_ACCESS"


class ApprovalStatus(str, Enum):
    """Status of human authorization requests."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class ErrorSeverity(str, Enum):
    """Diagnostic severity levels for bugs and test failures."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LLMProviderType(str, Enum):
    """Supported LLM backend providers."""

    LOCAL_OFFLINE = "local_offline"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"

