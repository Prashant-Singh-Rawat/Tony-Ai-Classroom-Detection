"""
backend/app/agents/tools/tool_registry.py — Secure Sandboxed Tool Registry
===========================================================================
Enforces path boundaries strictly inside REPO_ROOT. Logs every execution to SQLite.
Blocks destructive actions unless human authorization is formally registered.
"""

from __future__ import annotations
import inspect
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from backend.app.core.config import REPO_ROOT
from backend.app.agents.core.types import (
    ApprovalActionType,
    ApprovalStatus,
    ToolPermissionLevel,
)
from backend.app.database.db import SessionLocal
from backend.app.database.models import AgentApprovalRecord, AgentExecutionRecord
from backend.app.schemas.agents import ToolExecutionSchema


class ToolSecurityError(PermissionError):
    """Raised when an agent attempts unauthorized or out-of-sandbox operations."""
    pass


class ToolRegistry:
    """Central registry and policy enforcement engine for agent-invoked tools."""

    def __init__(self, sandbox_root: Optional[Path] = None) -> None:
        self.sandbox_root = (sandbox_root or REPO_ROOT).resolve()
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(
        self,
        name: str,
        func: Callable[..., Any],
        description: str,
        permission_level: ToolPermissionLevel = ToolPermissionLevel.READ_ONLY,
        approval_action: Optional[ApprovalActionType] = None,
    ) -> None:
        """Registers a callable tool with its security classification."""
        self._tools[name] = {
            "name": name,
            "func": func,
            "description": description,
            "permission_level": permission_level,
            "approval_action": approval_action,
        }

    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Returns metadata for a registered tool."""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Lists all registered tools."""
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "permission_level": t["permission_level"].value,
                "approval_action": t["approval_action"].value if t["approval_action"] else None,
            }
            for t in self._tools.values()
        ]

    def validate_path_safety(self, target_path: str | Path) -> Path:
        """
        Validates that a path is strictly inside the project root repository.
        Prevents directory traversal attacks ('../..') and absolute system path access.
        """
        resolved = (self.sandbox_root / target_path).resolve()
        try:
            resolved.relative_to(self.sandbox_root)
        except ValueError:
            raise ToolSecurityError(
                f"Path boundary violation: '{target_path}' resolves outside sandbox root ({self.sandbox_root})."
            )
        return resolved

    def check_approval(self, approval_id: Optional[str]) -> bool:
        """Checks if a destructive action has been approved by a human engineer."""
        if not approval_id:
            return False
        try:
            with SessionLocal() as db:
                rec = db.query(AgentApprovalRecord).filter(AgentApprovalRecord.id == approval_id).first()
                return rec is not None and rec.status == ApprovalStatus.APPROVED.value
        except Exception:
            return False

    def execute(
        self,
        tool_name: str,
        agent_id: str,
        task_id: Optional[str] = None,
        approval_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Executes a registered tool with sandbox validation, approval checks,
        latency timing, and auditable SQLite logging.
        """
        tool_entry = self._tools.get(tool_name)
        if not tool_entry:
            raise ValueError(f"Tool '{tool_name}' is not registered.")

        # Approval gate for destructive actions
        if tool_entry["permission_level"] == ToolPermissionLevel.APPROVAL_REQUIRED:
            if not self.check_approval(approval_id):
                raise ToolSecurityError(
                    f"Tool '{tool_name}' requires human approval. Missing or unapproved approval_id: {approval_id}"
                )

        t0 = time.time()
        status_flag = "SUCCESS"
        result: Any = None
        error_msg: Optional[str] = None

        try:
            func = tool_entry["func"]
            # Pass registry instance if tool expects it
            sig = inspect.signature(func)
            if "registry" in sig.parameters:
                kwargs["registry"] = self

            result = func(**kwargs)
        except Exception as e:
            status_flag = "FAILED"
            error_msg = str(e)
            raise e
        finally:
            elapsed_ms = round((time.time() - t0) * 1000, 2)
            # Log execution to SQLite
            try:
                with SessionLocal() as db:
                    exec_rec = AgentExecutionRecord(
                        task_id=task_id,
                        agent_id=agent_id,
                        action=f"Call {tool_name}",
                        tool_name=tool_name,
                        tool_input={k: str(v)[:200] for k, v in kwargs.items() if k != "registry"},
                        tool_output={"result": str(result)[:500]} if status_flag == "SUCCESS" else {"error": error_msg},
                        status=status_flag,
                        duration_ms=elapsed_ms,
                    )
                    db.add(exec_rec)
                    db.commit()
            except Exception:
                pass

        return result


tool_registry = ToolRegistry()

