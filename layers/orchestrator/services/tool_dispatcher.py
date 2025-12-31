"""
Tool Dispatcher - Unified tool execution routing.

Provides a single entry point for dispatching tool calls to the appropriate handlers.
Used by both the orchestrator API and ParallelExecutor for consistent tool execution.

This module eliminates duplication between orchestrator.py and parallel_executor.py
by centralizing tool dispatch logic.
"""

import logging
from typing import Any, Dict, Optional

from schemas.models import WorkspaceContext
from services.polyglot_handler import PolyglotHandler
from services.shell_handler import ShellHandler
from services.file_handler import FileHandler


logger = logging.getLogger("orchestrator.dispatcher")


# Singleton handlers - created once, reused across calls
_polyglot_handler: Optional[PolyglotHandler] = None
_shell_handler: Optional[ShellHandler] = None
_file_handler: Optional[FileHandler] = None


def get_polyglot_handler() -> PolyglotHandler:
    """Get or create singleton PolyglotHandler."""
    global _polyglot_handler
    if _polyglot_handler is None:
        _polyglot_handler = PolyglotHandler()
    return _polyglot_handler


def get_shell_handler() -> ShellHandler:
    """Get or create singleton ShellHandler."""
    global _shell_handler
    if _shell_handler is None:
        _shell_handler = ShellHandler()
    return _shell_handler


def get_file_handler() -> FileHandler:
    """Get or create singleton FileHandler."""
    global _file_handler
    if _file_handler is None:
        _file_handler = FileHandler()
    return _file_handler


async def dispatch_tool(
    tool: str,
    params: Dict[str, Any],
    workspace_context: Optional[WorkspaceContext] = None,
) -> Dict[str, Any]:
    """
    Dispatch tool execution to the appropriate handler.
    
    Tool routing:
      - execute_code → PolyglotHandler
      - execute_shell → ShellHandler  
      - read_file, write_file, list_dir, scan_workspace, etc. → FileHandler
      - none → No-op (idempotent skip)
      - complete → Completion signal
    
    Args:
        tool: Tool name to execute
        params: Parameters for the tool
        workspace_context: Execution context (limits, permissions)
        
    Returns:
        Normalized result dict with: success, output, error
    """
    # No-op handler
    if tool == "none":
        reason = params.get("reason", "no change needed")
        path = params.get("path", "")
        return {
            "success": True,
            "output": f"Skipped: {reason}" + (f" ({path})" if path else ""),
            "error": None,
        }
    
    # Completion signal
    if tool == "complete":
        return {
            "success": True,
            "output": params.get("message", "Task completed"),
            "error": params.get("error"),
        }
    
    # Dump workspace state for debugging/inspection
    if tool == "dump_state":
        from services.workspace_state import get_workspace_state
        import json
        state = get_workspace_state()
        
        # Build comprehensive state dump
        state_dump = {
            "scanned_paths": list(state.scanned_paths),
            "file_count": len(state.files),
            "dir_count": len(state.dirs),
            "files": state.files[:50],  # Limit for readability
            "dirs": state.dirs[:30],
            "edited_files": list(state.edited_files),
            "read_files": list(state.read_files),
            "file_metadata": {
                path: {
                    "size_bytes": meta.size_bytes,
                    "size_human": meta.size_human,
                    "line_count": meta.line_count,
                    "file_type": meta.file_type,
                }
                for path, meta in list(state.file_metadata.items())[:30]
            },
            "environment_facts": {
                "total_file_count": state.environment_facts.total_file_count,
                "total_dir_count": state.environment_facts.total_dir_count,
                "project_types": list(state.environment_facts.project_types),
                "frameworks": list(state.environment_facts.frameworks_detected),
                "package_managers": list(state.environment_facts.package_managers),
                "git_branch": state.environment_facts.git_branch,
                "python_version": state.environment_facts.python_version,
                "observations": state.environment_facts.observations[-10:],
            },
            "ledger": {
                "user_requests": state.ledger.user_requests[-10:],
                "extracted_values": dict(list(state.ledger.extracted_values.items())[-15:]),
            },
            "user_info": state.user_info,
        }
        
        # Calculate total size from metadata
        total_bytes = sum(m.size_bytes or 0 for m in state.file_metadata.values())
        if total_bytes > 0:
            state_dump["total_size_bytes"] = total_bytes
            state_dump["total_size_human"] = state._format_bytes(total_bytes)
        
        return {
            "success": True,
            "output": json.dumps(state_dump, indent=2),
            "error": None,
        }
    
    # Code execution
    if tool == "execute_code":
        result = await get_polyglot_handler().execute(
            language=params.get("language", "python"),
            code=params.get("code", ""),
            timeout=params.get("timeout", 30),
            workspace_context=workspace_context,
        )
        return {
            "success": result.get("success", False),
            "output": result.get("stdout") or result.get("stderr"),
            "error": result.get("stderr") if not result.get("success") else None,
        }
    
    # Shell execution
    if tool == "execute_shell":
        result = await get_shell_handler().execute(
            command=params.get("command", ""),
            timeout=params.get("timeout", 30),
            workspace_context=workspace_context,
        )
        return {
            "success": result.get("success", False),
            "output": result.get("output"),
            "error": result.get("error"),
        }
    
    # File operations
    file_handler = get_file_handler()
    
    if tool == "read_file":
        result = await file_handler.read(
            path=params.get("path", ""),
            workspace_context=workspace_context,
        )
        return {
            "success": result.get("success", False),
            "output": result.get("data"),
            "error": result.get("error"),
        }
    
    if tool == "write_file":
        result = await file_handler.write(
            path=params.get("path", ""),
            content=params.get("content", ""),
            workspace_context=workspace_context,
        )
        return {
            "success": result.get("success", False),
            "output": result.get("message", "File written"),
            "error": result.get("error"),
        }
    
    if tool == "list_dir":
        result = await file_handler.list_dir(
            path=params.get("path", "."),
            workspace_context=workspace_context,
        )
        return {
            "success": result.get("success", False),
            "output": result.get("output") or result.get("data"),
            "error": result.get("error"),
        }
    
    if tool == "scan_workspace":
        result = await file_handler.scan_workspace(
            path=params.get("path", "."),
            pattern=params.get("pattern", "*"),
            workspace_context=workspace_context,
        )
        return {
            "success": result.get("success", False),
            "output": result.get("output") or result.get("data"),
            "error": result.get("error"),
        }
    
    if tool == "replace_in_file":
        result = await file_handler.replace_in_file(
            path=params.get("path", ""),
            search=params.get("search", params.get("old_text", "")),
            replace=params.get("replace", params.get("new_text", "")),
            workspace_context=workspace_context,
        )
        return {
            "success": result.get("success", False),
            "output": result.get("message", result.get("output")),
            "error": result.get("error"),
        }
    
    if tool == "delete_file":
        result = await file_handler.delete(
            path=params.get("path", ""),
            workspace_context=workspace_context,
        )
        return {
            "success": result.get("success", False),
            "output": result.get("message", "File deleted"),
            "error": result.get("error"),
        }
    
    if tool == "append_to_file":
        result = await file_handler.append(
            path=params.get("path", ""),
            content=params.get("content", ""),
            workspace_context=workspace_context,
        )
        return {
            "success": result.get("success", False),
            "output": result.get("message", "Content appended"),
            "error": result.get("error"),
        }
    
    if tool == "insert_in_file":
        result = await file_handler.insert(
            path=params.get("path", ""),
            line=params.get("line", 0),
            content=params.get("content", ""),
            workspace_context=workspace_context,
        )
        return {
            "success": result.get("success", False),
            "output": result.get("message", "Content inserted"),
            "error": result.get("error"),
        }
    
    # Unknown tool
    logger.warning(f"Unknown tool requested: {tool}")
    return {
        "success": False,
        "output": None,
        "error": f"Unknown tool: {tool}",
    }
