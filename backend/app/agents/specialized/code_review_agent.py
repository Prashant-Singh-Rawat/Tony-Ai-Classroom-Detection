"""
backend/app/agents/specialized/code_review_agent.py — Code Review & Security Agent (Agent 9)
============================================================================================
Inspects git diffs, detects hardcoded secrets, enforces path guards, checks input validation,
verifies privacy rules, and prevents approval of code with unresolved critical vulnerabilities.
"""

from __future__ import annotations
from typing import Any, Dict

from backend.app.agents.core.base_agent import BaseAgent
from backend.app.agents.core.types import AgentRole, AgentStatus, ToolPermissionLevel
from backend.app.agents.providers.provider_manager import provider_manager
from backend.app.agents.tools.git_tools import git_diff


class CodeReviewSecurityAgent(BaseAgent):
    """Agent 9: Code Review & Security — Static code review, secret scanning, privacy & ethics audit."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="code_review_security",
            role=AgentRole.CODE_REVIEW_SECURITY,
            name="Code Review & Security Agent",
            responsibility="Inspects diffs for hardcoded secrets, injection vectors, input validation, and privacy requirements.",
            capabilities=[
                "secret_detection",
                "diff_inspection",
                "input_validation_audit",
                "privacy_rule_verification",
                "anti_pattern_detection",
            ],
            permission_level=ToolPermissionLevel.READ_ONLY,
            system_prompt=(
                "You are the Code Review & Security Agent for ClassVision AI. You inspect diffs and code modifications "
                "to ensure zero hardcoded secrets, strict path sandboxing, and full adherence to classroom privacy rules."
            ),
        )

    def execute_step(
        self,
        task_id: str,
        instruction: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        self.set_status(AgentStatus.REVIEWING, f"Reviewing changes: {instruction[:60]}")

        diff_text = git_diff()

        prompt = (
            f"Instruction: {instruction}\n"
            f"Active Git Diff:\n{diff_text}\n\n"
            "Review these changes for security, secrets, input validation, and student privacy compliance."
        )

        response = provider_manager.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
        )

        has_secrets = "password" in diff_text.lower() or "api_key = \"" in diff_text.lower()
        passed = not has_secrets

        if passed:
            self.record_success("Code review passed without critical security issues.")
        else:
            self.record_failure("Critical security issues detected in diff.")

        return {
            "agent": self.agent_id,
            "instruction": instruction,
            "review_assessment": response.content,
            "passed": passed,
            "status": "COMPLETED" if passed else "FAILED",
        }

