"""
backend/app/agents/tools/file_tools.py — Sandboxed File Inspection & Modification Tools
========================================================================================
Path-guarded within the project root. Deletion mandates human approval.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.app.agents.tools.tool_registry import ToolRegistry, tool_registry
from backend.app.agents.core.types import ApprovalActionType, ToolPermissionLevel


def read_file(
    file_path: str,
    start_line: int = 1,
    end_line: Optional[int] = None,
    registry: Optional[ToolRegistry] = None,
) -> str:
    """Reads lines from a file strictly within the project repository."""
    reg = registry or tool_registry
    target = reg.validate_path_safety(file_path)

    if not target.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(target, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    start_idx = max(0, start_line - 1)
    end_idx = len(lines) if end_line is None else min(len(lines), end_line)

    numbered_lines = [
        f"{idx + 1:4d}: {line}"
        for idx, line in enumerate(lines[start_idx:end_idx], start=start_idx)
    ]
    return "".join(numbered_lines)


def list_directory(
    dir_path: str = ".",
    max_depth: int = 2,
    registry: Optional[ToolRegistry] = None,
) -> List[str]:
    """Lists directory contents up to a maximum depth, ignoring noisy virtualenvs and git caches."""
    reg = registry or tool_registry
    target = reg.validate_path_safety(dir_path)

    if not target.is_dir():
        raise NotADirectoryError(f"Directory not found: {dir_path}")

    ignore_dirs = {".venv", "venv", ".git", "node_modules", "__pycache__", ".pytest_cache", "dist", ".cache"}
    entries = []

    for root, dirs, files in os.walk(target):
        # Prune ignored directories in place
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        rel_root = Path(root).relative_to(reg.sandbox_root)
        depth = len(rel_root.parts)
        if depth > max_depth:
            continue

        for d in dirs:
            entries.append(f"[DIR]  {(rel_root / d).as_posix()}/")
        for f in files:
            entries.append(f"[FILE] {(rel_root / f).as_posix()}")

    return sorted(entries)[:200]


def search_files(
    query: str,
    file_pattern: str = "*",
    max_results: int = 50,
    registry: Optional[ToolRegistry] = None,
) -> List[Dict[str, Any]]:
    """Searches for text query occurrences across project source files."""
    reg = registry or tool_registry
    ignore_dirs = {".venv", "venv", ".git", "node_modules", "__pycache__", "dist", ".cache"}
    results = []

    for path in reg.sandbox_root.rglob(file_pattern):
        if any(ignored in path.parts for ignored in ignore_dirs):
            continue
        if not path.is_file():
            continue

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line_idx, line in enumerate(f, start=1):
                    if query.lower() in line.lower():
                        results.append({
                            "file": path.relative_to(reg.sandbox_root).as_posix(),
                            "line": line_idx,
                            "match": line.strip(),
                        })
                        if len(results) >= max_results:
                            return results
        except Exception:
            continue

    return results


def create_file(
    file_path: str,
    content: str,
    overwrite: bool = False,
    registry: Optional[ToolRegistry] = None,
) -> str:
    """Creates a new file with specified content within the project root."""
    reg = registry or tool_registry
    target = reg.validate_path_safety(file_path)

    if target.exists() and not overwrite:
        raise FileExistsError(f"File already exists and overwrite=False: {file_path}")

    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(content)

    return f"Created file {file_path} ({len(content)} characters)."


def modify_file(
    file_path: str,
    target_string: str,
    replacement_string: str,
    registry: Optional[ToolRegistry] = None,
) -> str:
    """Replaces target string occurrences in an existing project file."""
    reg = registry or tool_registry
    target = reg.validate_path_safety(file_path)

    if not target.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(target, "r", encoding="utf-8") as f:
        data = f.read()

    if target_string not in data:
        raise ValueError(f"Target string not found in {file_path}.")

    count = data.count(target_string)
    updated_data = data.replace(target_string, replacement_string)

    with open(target, "w", encoding="utf-8") as f:
        f.write(updated_data)

    return f"Replaced {count} occurrence(s) in {file_path}."


def delete_file(
    file_path: str,
    registry: Optional[ToolRegistry] = None,
) -> str:
    """
    Deletes a file. Requires APPROVAL_REQUIRED clearance.
    Checked by ToolRegistry before execution.
    """
    reg = registry or tool_registry
    target = reg.validate_path_safety(file_path)

    if not target.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    target.unlink()
    return f"Successfully deleted {file_path}."


# Register tools in central registry
tool_registry.register_tool(
    name="read_file",
    func=read_file,
    description="Reads line range from a project file.",
    permission_level=ToolPermissionLevel.READ_ONLY,
)

tool_registry.register_tool(
    name="list_directory",
    func=list_directory,
    description="Lists files and subdirectories up to given depth.",
    permission_level=ToolPermissionLevel.READ_ONLY,
)

tool_registry.register_tool(
    name="search_files",
    func=search_files,
    description="Searches for keyword or text patterns across project files.",
    permission_level=ToolPermissionLevel.READ_ONLY,
)

tool_registry.register_tool(
    name="create_file",
    func=create_file,
    description="Creates or overwrites a project file with given content.",
    permission_level=ToolPermissionLevel.SAFE_WRITE,
)

tool_registry.register_tool(
    name="modify_file",
    func=modify_file,
    description="Performs exact substring replacement in a project file.",
    permission_level=ToolPermissionLevel.SAFE_WRITE,
)

tool_registry.register_tool(
    name="delete_file",
    func=delete_file,
    description="Deletes a file. Mandates prior human approval.",
    permission_level=ToolPermissionLevel.APPROVAL_REQUIRED,
    approval_action=ApprovalActionType.DELETE_FILE,
)

