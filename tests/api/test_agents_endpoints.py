"""
tests/api/test_agents_endpoints.py — Autonomous Multi-Agent API & Orchestration Tests
======================================================================================
Tests agent registration, DAG planning, task execution, approvals, and WebSocket stream.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.agents.core.types import ApprovalActionType
from backend.app.agents.approval.approval_manager import approval_manager


@pytest.fixture
def client():
    return TestClient(app)


def test_get_all_agents_status(client):
    """Verifies that all 12 distinct engineering agents are registered and active."""
    response = client.get("/api/agents/status")
    assert response.status_code == 200
    agents = response.json()
    assert isinstance(agents, list)
    assert len(agents) == 12

    roles = {a["role"] for a in agents}
    assert "project_manager" in roles
    assert "software_architect" in roles
    assert "frontend_developer" in roles
    assert "backend_developer" in roles
    assert "aiml_engineer" in roles
    assert "dataset_manager" in roles
    assert "debugging_agent" in roles
    assert "testing_qa" in roles
    assert "code_review_security" in roles
    assert "documentation" in roles
    assert "devops_environment" in roles
    assert "supervisor" in roles


def test_get_agent_health(client):
    """Verifies agent and system health telemetry."""
    response = client.get("/api/agents/health")
    assert response.status_code == 200
    data = response.json()
    assert data["backendStatus"] == "HEALTHY"
    assert data["activeAgentCount"] == 12


def test_create_and_execute_task(client):
    """Verifies that submitting a task decomposes a DAG plan and executes milestones."""
    payload = {
        "title": "Inspect ClassVision AI and identify three important bugs",
        "description": "Autonomous multi-agent repository inspection and risk analysis.",
        "priority": "HIGH",
        "autoExecute": True,
    }
    response = client.post("/api/agents/tasks", json=payload)
    assert response.status_code == 201
    task = response.json()
    assert task["taskId"].startswith("task_")
    assert task["status"] in ("COMPLETED", "IN_PROGRESS")
    assert len(task["plan"]) >= 4
    assert task["progress"] > 0.0

    # Retrieve individual task
    task_id = task["taskId"]
    get_res = client.get(f"/api/agents/tasks/{task_id}")
    assert get_res.status_code == 200
    assert get_res.json()["taskId"] == task_id


def test_cancel_task(client):
    """Verifies that an unexecuted task can be formally cancelled."""
    payload = {
        "title": "Cancelable test task",
        "description": "Task created without autoExecute to test cancellation.",
        "priority": "LOW",
        "autoExecute": False,
    }
    res = client.post("/api/agents/tasks", json=payload)
    assert res.status_code == 201
    task_id = res.json()["taskId"]

    cancel_res = client.post(f"/api/agents/tasks/{task_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"


def test_agent_messages_log(client):
    """Verifies message audit trail across the communication bus."""
    response = client.get("/api/agents/messages")
    assert response.status_code == 200
    messages = response.json()
    assert isinstance(messages, list)


def test_human_approval_workflow(client):
    """Verifies creation and approval of high-risk actions."""
    # Create sample pending approval
    appr = approval_manager.create_request(
        task_id="task_test_appr",
        agent_id="backend_developer",
        action_type=ApprovalActionType.DELETE_FILE,
        description="Request to delete deprecated temporary artifact.",
    )

    # List pending
    list_res = client.get("/api/agents/approvals?pending_only=true")
    assert list_res.status_code == 200
    pending_list = list_res.json()
    assert any(a["approvalId"] == appr.approvalId for a in pending_list)

    # Approve
    approve_res = client.post(
        f"/api/agents/approvals/{appr.approvalId}/approve",
        json={"reviewedBy": "lead_engineer", "comment": "Approved for testing"},
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "APPROVED"


def test_agent_websocket_stream(client):
    """Verifies WebSocket connection to agent streaming feed."""
    with client.websocket_connect("/api/agents/ws/stream") as ws:
        greeting = ws.receive_json()
        assert greeting["type"] == "agents_status"
        assert len(greeting["agents"]) == 12

        ws.send_text("ping")
        pong = ws.receive_json()
        assert pong["type"] == "pong"
        ws.close()

