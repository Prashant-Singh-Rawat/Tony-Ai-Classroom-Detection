"""
backend/app/agents/tools/git_tools.py — Sandboxed Git Tools
===========================================================
Inspects repository branches, status, diffs, and commit history.
"""

from __future__ import annotations
import subprocess
from typing import Any, Dict, List, Optional

from backend.app.agents.tools.tool_registry import ToolRegistry, tool_registry
from backend.app.agents.core.types import ToolPermissionLevel


def git_status(registry: Optional[ToolRegistry] = None) -> str:
    """Returns working tree git status."""
    reg = registry or tool_registry
    try:
        proc = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(reg.sandbox_root),
            capture_output=True,
            text=True,
            timeout=15,
        )
        return proc.stdout.strip() or "Clean working tree (no unstaged changes)."
    except Exception as e:
        return f"Git status error: {str(e)}"


def git_diff(cached: bool = False, registry: Optional[ToolRegistry] = None) -> str:
    """Returns active git diff for uncommitted changes."""
    reg = registry or tool_registry
    cmd = ["git", "diff"]
    if cached:
        cmd.append("--cached")

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(reg.sandbox_root),
            capture_output=True,
            text=True,
            timeout=15,
        )
        return proc.stdout[-3000:] if proc.stdout else "No uncommitted diff."
    except Exception as e:
        return f"Git diff error: {str(e)}"


def git_log(limit: int = 5, registry: Optional[ToolRegistry] = None) -> str:
    """Returns recent git commit history."""
    reg = registry or tool_registry
    try:
        proc = subprocess.run(
            ["git", "log", f"-n{limit}", "--oneline"],
            cwd=str(reg.sandbox_root),
            capture_output=True,
            text=True,
            timeout=15,
        )
        return proc.stdout.strip()
    except Exception as e:
        return f"Git log error: {str(e)}"


# Register git tools
tool_registry.register_tool(
    name="git_status",
    func=git_status,
    description="Inspects git working tree changes.",
    permission_level=ToolPermissionLevel.READ_ONLY,
)

tool_registry.register_tool(
    name="git_diff",
    func=git_diff,
    description="Inspects uncommitted line diffs.",
    permission_level=ToolPermissionLevel.READ_ONLY,
)

tool_registry.register_tool(
    name="git_log",
    func=git_log,
    description="Inspects recent commit history.",
    permission_level=ToolPermissionLevel.READ_ONLY,
)

