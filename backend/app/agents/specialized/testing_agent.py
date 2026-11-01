"""
backend/app/agents/specialized/testing_agent.py — Testing & QA Agent (Agent 8)
=============================================================================
Executes Pytest, Vitest, Oxlint, and Vite build suites. Verifies actual outcomes
and prevents hallucinated test passes.
"""

from __future__ import annotations
from typing import Any, Dict, Optional

from backend.app.agents.core.base_agent import BaseAgent
from backend.app.agents.core.types import AgentRole, AgentStatus, ToolPermissionLevel
from backend.app.agents.tools.code_tools import run_build, run_lint, run_pytest, run_vitest


class TestingQAAgent(BaseAgent):
    """Agent 8: Testing & QA — Automated execution of Pytest, Vitest, Lint, and Build verification."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="testing_qa",
            role=AgentRole.TESTING_QA,
            name="Testing & QA Agent",
            responsibility="Runs automated test suites, lint checks, frontend builds, and verifies regression status through real execution.",
            capabilities=[
                "pytest_execution",
                "vitest_execution",
                "oxlint_validation",
                "vite_build_verification",
                "regression_testing",
            ],
            permission_level=ToolPermissionLevel.READ_ONLY,
            system_prompt=(
                "You are the Testing & QA Agent for ClassVision AI. You execute real tests and report ground-truth "
                "exit codes and failure outputs. You NEVER fabricate test results."
            ),
        )

    def run_full_suite(self) -> Dict[str, Any]:
        """Runs Python and frontend test suites, linting, and build checks."""
        self.set_status(AgentStatus.TESTING, "Running full test and quality suite")

        py_res = run_pytest()
        vi_res = run_vitest()
        lint_res = run_lint()
        build_res = run_build()

        overall_passed = py_res["success"] and vi_res["success"] and lint_res["success"] and build_res["success"]

        self.set_status(AgentStatus.IDLE, "Test suite complete")
        return {
            "overall_success": overall_passed,
            "pytest": {
                "success": py_res["success"],
                "exit_code": py_res["exit_code"],
                "summary": py_res["stdout"][-500:],
            },
            "vitest": {
                "success": vi_res["success"],
                "exit_code": vi_res["exit_code"],
                "summary": vi_res["stdout"][-500:],
            },
            "lint": {
                "success": lint_res["success"],
                "summary": lint_res["stdout"][-300:],
            },
            "build": {
                "success": build_res["success"],
                "summary": build_res["stdout"][-300:],
            },
        }

    def execute_step(
        self,
        task_id: str,
        instruction: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        self.set_status(AgentStatus.TESTING, f"Testing: {instruction[:60]}")

        target_test = context.get("target_test")
        if target_test:
            res = run_pytest(test_target=target_test)
            suite_data = {"targeted_test": res}
            success = res["success"]
        elif "full" in instruction.lower():
            suite_data = self.run_full_suite()
            success = suite_data["overall_success"]
        else:
            # Fast verification check
            py_res = run_pytest(test_target="tests/api/test_health.py")
            lint_res = run_lint()
            success = py_res["success"] and lint_res["success"]
            suite_data = {
                "health_test": py_res,
                "lint": lint_res,
                "overall_success": success,
            }

        if success:
            self.record_success("Tests verified clean.")
        else:
            self.record_failure("Test failures detected.")

        return {
            "agent": self.agent_id,
            "instruction": instruction,
            "test_results": suite_data,
            "success": success,
            "status": "COMPLETED" if success else "FAILED",
        }
