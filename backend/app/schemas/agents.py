"""
backend/app/schemas/agents.py — Pydantic Schemas for Multi-Agent System
========================================================================
Implements camelCase serialized response and request models for the Agent Command Center.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import Field

from backend.app.schemas.common import CamelModel
from backend.app.agents.core.types import (
    AgentRole,
    AgentStatus,
    ApprovalActionType,
    ApprovalStatus,
    ErrorSeverity,
    MessageType,
    TaskPriority,
    TaskState,
    ToolPermissionLevel,
)


class AgentInfo(CamelModel):
    """Runtime representation and health metrics of a specialized agent."""

    agentId: str
    name: str
    role: AgentRole
    responsibility: str
    status: AgentStatus = AgentStatus.IDLE
    currentTaskId: Optional[str] = None
    lastActivity: str = Field(default_factory=lambda: "System Initialized")
    successCount: int = 0
    failureCount: int = 0
    capabilities: List[str] = Field(default_factory=list)
    permissionLevel: ToolPermissionLevel = ToolPermissionLevel.READ_ONLY


class AgentMessageSchema(CamelModel):
    """Structured message payload passed over the central agent message bus."""

    messageId: str
    taskId: Optional[str] = None
    senderAgent: str
    receiverAgent: str
    messageType: MessageType
    content: Dict[str, Any] = Field(default_factory=dict)
    status: str = "DELIVERED"
    timestamp: str


class TaskPlanStep(CamelModel):
    """Individual decomposed step within an overall project plan."""

    stepIndex: int
    title: str
    assignedAgent: AgentRole
    dependencies: List[int] = Field(default_factory=list)
    status: TaskState = TaskState.PENDING
    acceptanceCriteria: str = ""
    resultSummary: Optional[str] = None


class AgentTaskSchema(CamelModel):
    """Lifecycle representation of an autonomous engineering task."""

    taskId: str
    title: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskState = TaskState.PENDING
    assignedAgents: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    acceptanceCriteria: List[str] = Field(default_factory=list)
    plan: List[TaskPlanStep] = Field(default_factory=list)
    progress: float = 0.0
    resultSummary: Optional[str] = None
    createdAt: str
    updatedAt: str
    completedAt: Optional[str] = None


class TaskCreateRequest(CamelModel):
    """Payload to initiate a new autonomous engineering request."""

    title: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    assignedAgents: Optional[List[str]] = None
    autoExecute: bool = True


class ApprovalRequestSchema(CamelModel):
    """Pending high-risk action awaiting human confirmation."""

    approvalId: str
    taskId: str
    agentId: str
    actionType: ApprovalActionType
    description: str
    details: Dict[str, Any] = Field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewedBy: Optional[str] = None
    reviewComment: Optional[str] = None
    createdAt: str
    reviewedAt: Optional[str] = None


class ApprovalActionRequest(CamelModel):
    """Decision payload submitted by human supervisor."""

    reviewedBy: str = "engineer"
    comment: Optional[str] = None


class DebuggingRecordSchema(CamelModel):
    """Diagnostic trace and fix history maintained by the Debugging Engine."""

    id: int
    taskId: str
    errorMessage: str
    errorSeverity: ErrorSeverity = ErrorSeverity.MEDIUM
    stackTrace: Optional[str] = None
    rootCause: Optional[str] = None
    affectedFiles: List[str] = Field(default_factory=list)
    fixDescription: Optional[str] = None
    repairAttempt: int = 1
    maxAttempts: int = 3
    testsExecuted: List[str] = Field(default_factory=list)
    status: str = "ANALYZING"
    createdAt: str
    resolvedAt: Optional[str] = None


class ToolExecutionSchema(CamelModel):
    """Auditable log entry for every tool execution invoked by an agent."""

    executionId: int
    taskId: Optional[str] = None
    agentId: str
    action: str
    toolName: str
    toolInput: Dict[str, Any] = Field(default_factory=dict)
    toolOutput: Optional[Dict[str, Any]] = None
    status: str = "SUCCESS"
    durationMs: float = 0.0
    createdAt: str


class ProjectHealthSchema(CamelModel):
    """Comprehensive health telemetry of the application and agent environment."""

    backendStatus: str = "HEALTHY"
    frontendStatus: str = "HEALTHY"
    databaseStatus: str = "CONNECTED"
    aiModelStatus: str = "READY"
    datasetStatus: str = "COMPLIANT"
    latestTestRun: Dict[str, Any] = Field(default_factory=dict)
    systemMemory: Dict[str, Any] = Field(default_factory=dict)
    activeAgentCount: int = 12
    pendingApprovalsCount: int = 0

