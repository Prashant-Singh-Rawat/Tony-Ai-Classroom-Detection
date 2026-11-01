"""
backend/app/agents/tools/code_tools.py — Test Runner & Code Execution Tools
===========================================================================
Executes Pytest, Vitest, Oxlint, and Vite build with timeouts and formatted outputs.
"""

from __future__ import annotations
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.app.core.config import REPO_ROOT
from backend.app.agents.tools.tool_registry import ToolRegistry, tool_registry
from backend.app.agents.core.types import ToolPermissionLevel


def run_pytest(
    test_target: Optional[str] = None,
    extra_args: Optional[List[str]] = None,
    timeout_sec: int = 120,
    registry: Optional[ToolRegistry] = None,
) -> Dict[str, Any]:
    """Runs Python pytest test suite on the repository or specific test file."""
    reg = registry or tool_registry
    cmd = [sys.executable, "-m", "pytest"]
    if test_target:
        target_path = reg.validate_path_safety(test_target)
        cmd.append(str(target_path.relative_to(reg.sandbox_root)))
    if extra_args:
        cmd.extend(extra_args)

    try:
        proc = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            cwd=str(reg.sandbox_root),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        return {
            "exit_code": proc.returncode,
            "success": proc.returncode == 0,
            "stdout": proc.stdout[-2000:] if proc.stdout else "",
            "stderr": proc.stderr[-2000:] if proc.stderr else "",
            "target": test_target or "all_tests",
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "success": False,
            "stdout": "",
            "stderr": f"Pytest timed out after {timeout_sec}s.",
            "target": test_target or "all_tests",
        }


def run_vitest(
    timeout_sec: int = 60,
    registry: Optional[ToolRegistry] = None,
) -> Dict[str, Any]:
    """Runs frontend Vitest test suite."""
    reg = registry or tool_registry
    frontend_dir = reg.sandbox_root / "frontend"
    cmd = "npx vitest run --run"

    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            stdin=subprocess.DEVNULL,
            cwd=str(frontend_dir),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        return {
            "exit_code": proc.returncode,
            "success": proc.returncode == 0,
            "stdout": proc.stdout[-2000:] if proc.stdout else "",
            "stderr": proc.stderr[-2000:] if proc.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "success": False,
            "stdout": "",
            "stderr": f"Vitest timed out after {timeout_sec}s.",
        }


def run_lint(
    timeout_sec: int = 30,
    registry: Optional[ToolRegistry] = None,
) -> Dict[str, Any]:
    """Runs frontend linter (oxlint)."""
    reg = registry or tool_registry
    frontend_dir = reg.sandbox_root / "frontend"
    cmd = "npx oxlint"

    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            stdin=subprocess.DEVNULL,
            cwd=str(frontend_dir),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        return {
            "exit_code": proc.returncode,
            "success": proc.returncode == 0,
            "stdout": proc.stdout[-2000:] if proc.stdout else "",
            "stderr": proc.stderr[-2000:] if proc.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "success": False,
            "stdout": "",
            "stderr": f"Lint timed out after {timeout_sec}s.",
        }


def run_build(
    timeout_sec: int = 90,
    registry: Optional[ToolRegistry] = None,
) -> Dict[str, Any]:
    """Runs frontend production build (tsc -b && vite build)."""
    reg = registry or tool_registry
    frontend_dir = reg.sandbox_root / "frontend"
    cmd = "npx tsc -b && npx vite build"

    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            stdin=subprocess.DEVNULL,
            cwd=str(frontend_dir),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        return {
            "exit_code": proc.returncode,
            "success": proc.returncode == 0,
            "stdout": proc.stdout[-2000:] if proc.stdout else "",
            "stderr": proc.stderr[-2000:] if proc.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "success": False,
            "stdout": "",
            "stderr": f"Build timed out after {timeout_sec}s.",
        }


def run_python_script(
    script_path: str,
    args: Optional[List[str]] = None,
    timeout_sec: int = 60,
    registry: Optional[ToolRegistry] = None,
) -> Dict[str, Any]:
    """Executes a standalone Python script located inside the repository."""
    reg = registry or tool_registry
    target = reg.validate_path_safety(script_path)
    cmd = [sys.executable, str(target)]
    if args:
        cmd.extend(args)

    try:
        proc = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            cwd=str(reg.sandbox_root),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        return {
            "exit_code": proc.returncode,
            "success": proc.returncode == 0,
            "stdout": proc.stdout[-2000:] if proc.stdout else "",
            "stderr": proc.stderr[-2000:] if proc.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "success": False,
            "stdout": "",
            "stderr": f"Script execution timed out after {timeout_sec}s.",
        }


# Register code tools
tool_registry.register_tool(
    name="run_pytest",
    func=run_pytest,
    description="Runs Python pytest test suite.",
    permission_level=ToolPermissionLevel.READ_ONLY,
)

tool_registry.register_tool(
    name="run_vitest",
    func=run_vitest,
    description="Runs frontend Vitest test suite.",
    permission_level=ToolPermissionLevel.READ_ONLY,
)

tool_registry.register_tool(
    name="run_lint",
    func=run_lint,
    description="Runs frontend code quality & oxlint checks.",
    permission_level=ToolPermissionLevel.READ_ONLY,
)

tool_registry.register_tool(
    name="run_build",
    func=run_build,
    description="Runs frontend production bundle build.",
    permission_level=ToolPermissionLevel.READ_ONLY,
)

tool_registry.register_tool(
    name="run_python_script",
    func=run_python_script,
    description="Executes a controlled Python script inside the repository.",
    permission_level=ToolPermissionLevel.SAFE_WRITE,
)
