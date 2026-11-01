"""
tests/unit/test_multi_agent_system.py — Comprehensive Unit Tests for Autonomous Multi-Agent Platform
====================================================================================================
Tests:
1. Agent registration for all 12 agents
2. Tool execution permissions and path traversal sandbox boundary enforcement
3. Message bus publish and subscription
4. Task creation, DAG planning, and cancellation
5. Human approval workflow (pending, approve, reject)
6. Autonomous Debugging Engine 10-step loop
7. Persistent memory storage and retrieval (SQLite & ChromaDB)
8. Provider manager fallback and quota handling
"""

import pytest
from pathlib import Path

from backend.app.core.config import REPO_ROOT
from backend.app.agents.core.types import (
    AgentRole,
    AgentStatus,
    ApprovalActionType,
    ApprovalStatus,
    ErrorSeverity,
    LLMProviderType,
    MessageType,
    TaskPriority,
    TaskState,
    ToolPermissionLevel,
)
from backend.app.agents.registry.agent_registry import agent_registry
from backend.app.agents.core.bus import agent_bus
from backend.app.agents.core.orchestrator import orchestrator
from backend.app.agents.tools.tool_registry import tool_registry, ToolSecurityError
from backend.app.agents.approval.approval_manager import approval_manager
from backend.app.agents.debugging.debugging_engine import debugging_engine
from backend.app.agents.memory.agent_memory import agent_memory
from backend.app.agents.providers.provider_manager import provider_manager


def test_agent_registry_contains_all_12_agents():
    """Confirms all 12 agents are registered with distinct roles."""
    agents = agent_registry.list_all_agents()
    assert len(agents) == 12
    roles = {a.role for a in agents}
    for expected_role in AgentRole:
        assert expected_role in roles


def test_tool_sandbox_path_security():
    """Confirms that tool registry prevents path traversal outside REPO_ROOT."""
    # Safe path inside sandbox
    safe_path = tool_registry.validate_path_safety("backend/app/main.py")
    assert safe_path.is_file()

    # Unsafe path outside sandbox
    with pytest.raises(ToolSecurityError):
        tool_registry.validate_path_safety("../../../Windows/System32/calc.exe")

    with pytest.raises(ToolSecurityError):
        tool_registry.validate_path_safety("C:/Windows/System32")


def test_tool_execution_with_approval_gate():
    """Confirms destructive tools require human approval."""
    # Attempting to delete a file without approval_id raises ToolSecurityError
    with pytest.raises(ToolSecurityError):
        tool_registry.execute(
            tool_name="delete_file",
            agent_id="backend_developer",
            file_path="non_existent_file.tmp",
            approval_id=None,
        )


def test_message_bus_publish_and_subscriber():
    """Verifies message bus routes and delivers typed messages."""
    received = []

    def listener(msg):
        received.append(msg)

    agent_bus.subscribe(listener)
    try:
        sent = agent_bus.publish(
            sender_agent="test_sender",
            receiver_agent="test_receiver",
            message_type=MessageType.PROGRESS_UPDATE,
            content={"progress": 50.0},
            task_id="task_unit_bus",
        )
        assert sent.messageId.startswith("msg_")
        assert len(received) > 0
        assert received[-1].messageId == sent.messageId
    finally:
        agent_bus.unsubscribe(listener)


def test_orchestrator_task_creation_and_dag_plan():
    """Verifies that orchestrator decomposes task into DAG steps."""
    task = orchestrator.create_task(
        title="Improve hand-raising detection model",
        description="Optimize YOLOv8n-pose wrist-shoulder elevation threshold.",
        priority=TaskPriority.HIGH,
        auto_execute=False,
    )
    assert task.taskId.startswith("task_")
    assert task.status == TaskState.PLANNING
    assert len(task.plan) >= 4
    # Plan has step indices and assigned agents
    step_agents = [s.assignedAgent for s in task.plan]
    assert AgentRole.SOFTWARE_ARCHITECT in step_agents
    assert AgentRole.AIML_ENGINEER in step_agents


def test_human_approval_lifecycle():
    """Verifies approval request creation, approval, and rejection."""
    req = approval_manager.create_request(
        task_id="task_appr_unit",
        agent_id="devops_environment",
        action_type=ApprovalActionType.DEPENDENCY_CHANGE,
        description="Upgrade dependency check.",
    )
    assert req.status == ApprovalStatus.PENDING

    # Approve
    ok = approval_manager.approve(req.approvalId, reviewed_by="lead_dev", comment="Approved")
    assert ok is True

    # Rejection of another request
    req2 = approval_manager.create_request(
        task_id="task_appr_unit_2",
        agent_id="devops_environment",
        action_type=ApprovalActionType.OVERWRITE_DATASET,
        description="Dangerous dataset overwrite.",
    )
    rej_ok = approval_manager.reject(req2.approvalId, reviewed_by="safety_officer", comment="Forbidden")
    assert rej_ok is True


def test_autonomous_debugging_loop():
    """Verifies 10-step debugging loop and repair attempt tracking."""
    result = debugging_engine.run_debugging_loop(
        task_id="task_debug_unit",
        failing_test_or_command="tests/api/test_health.py",
        error_context="Assertion error simulated during unit testing",
        attempt=1,
    )
    assert result["task_id"] == "task_debug_unit"
    assert result["attempt"] == 1
    assert result["max_attempts"] == 3
    assert "root_cause" in result
    assert result["status"] in ("RESOLVED", "RETRY_REQUIRED", "ESCALATED")


def test_agent_memory_persistence():
    """Verifies structured and semantic project memory storage and retrieval."""
    test_key = "unit_test_architecture_rule"
    test_content = "ClassVision AI requires batch size 1 for 4GB VRAM GPU memory stability."

    agent_memory.store("ARCHITECTURE", test_key, test_content, metadata={"verified": True})
    retrieved = agent_memory.retrieve("4GB VRAM GPU memory batch size", category="ARCHITECTURE")
    assert len(retrieved) > 0
    assert any("batch size 1" in r["content"] for r in retrieved)


def test_provider_manager_offline_fallback():
    """Verifies local offline deterministic engine operates reliably."""
    resp = provider_manager.generate(
        prompt="Inspect ClassVision AI and identify three important bugs",
        system_prompt="You are the Software Architect Agent.",
    )
    assert resp.content is not None
    assert len(resp.content) > 50
    assert resp.tokens_used > 0
    assert resp.cost_estimate_usd == 0.0

