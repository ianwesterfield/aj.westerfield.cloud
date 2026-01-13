"""
Tool Dispatcher - Unified tool execution routing.

Provides a single entry point for dispatching tool calls to the appropriate handlers.
Used by both the orchestrator API and ParallelExecutor for consistent tool execution.

This module eliminates duplication between orchestrator.py and parallel_executor.py
by centralizing tool dispatch logic.
"""

import base64
import logging
from typing import Any, Dict, List, Optional

from schemas.models import WorkspaceContext
from services.polyglot_handler import PolyglotHandler
from services.shell_handler import ShellHandler
from services.file_handler import FileHandler
from services.grpc_client import AgentGrpcClient, get_grpc_client
from services.agent_discovery import get_discovery_service, AgentCapabilities
from shared.logging_utils import LogLevel, LogCategory, log_message, get_icon


logger = logging.getLogger("orchestrator.dispatcher")


# Singleton handlers - created once, reused across calls
_polyglot_handler: Optional[PolyglotHandler] = None
_shell_handler: Optional[ShellHandler] = None
_file_handler: Optional[FileHandler] = None
_grpc_client: Optional[AgentGrpcClient] = None
_discovered_agents: List[AgentCapabilities] = []


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


async def get_available_agents() -> List[AgentCapabilities]:
    """Get list of available FunnelCloud agents via discovery."""
    global _discovered_agents
    discovery = get_discovery_service()
    _discovered_agents = await discovery.discover(force=False)  # Use cache if recent
    return _discovered_agents


async def get_agent_by_id(agent_id: str) -> Optional[AgentCapabilities]:
    """Get a specific agent by ID."""
    agents = await get_available_agents()
    for agent in agents:
        if agent.agent_id.lower() == agent_id.lower():
            return agent
    return None


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
        error_msg = params.get("error")
        # If there's an error, surface it as the output too (for visibility)
        if error_msg:
            return {
                "success": False,
                "output": f"⚠️ {error_msg}",
                "error": error_msg,
            }
        return {
            "success": True,
            "output": params.get("message", "Task completed"),
            "error": None,
        }
    
    # Dump session state for debugging/inspection
    if tool == "dump_state":
        from services.session_state import get_session_state
        import json
        state = get_session_state()
        
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
            path=params.get("path", "") or params.get("file_path", ""),
            workspace_context=workspace_context,
        )
        return {
            "success": result.get("success", False),
            "output": result.get("data"),
            "error": result.get("error"),
        }
    
    if tool == "write_file":
        result = await file_handler.write(
            path=params.get("path", "") or params.get("file_path", ""),
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
    
    # Script validation (pre-execution analysis)
    if tool == "validate_script":
        return await _handle_validate_script(params)
    
    # FunnelCloud remote execution
    if tool == "remote_execute":
        return await _handle_remote_execute(params)
    
    if tool == "list_agents":
        return await _handle_list_agents(params)
    
    # Unknown tool
    logger.warning(f"Unknown tool requested: {tool}")
    return {
        "success": False,
        "output": None,
        "error": f"Unknown tool: {tool}",
    }


async def _handle_validate_script(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a script for syntax, logic, and safety issues.
    
    Params:
        script: The script code to validate
        language: Programming language (powershell, python, bash, etc.)
    
    Returns dict with:
        {
            "success": bool,
            "output": validation summary (formatted for display),
            "error": null or error message
        }
    """
    from services.reasoning_engine import ReasoningEngine
    
    script = params.get("script", "")
    language = params.get("language", "powershell")
    
    if not script:
        return {
            "success": False,
            "output": None,
            "error": "No script provided for validation",
        }
    
    try:
        # Use the reasoning engine's validation method
        engine = ReasoningEngine()  # Creates an instance with default Ollama settings
        validation = engine.validate_script(script, language)
        
        # Format output for display
        lines = [f"📋 Script Validation ({language.upper()}):"]
        lines.append(f"")
        lines.append(validation["summary"])
        lines.append("")
        
        if validation["issues"]:
            lines.append("Issues found:")
            for issue in validation["issues"]:
                # Use centralized logging for icon selection
                severity_level = LogLevel.ERROR if issue["severity"] == "error" else LogLevel.WARNING
                severity_icon = get_icon(LogCategory.VALIDATION, severity_level)
                lines.append(f"  {severity_icon} [{issue['type']}] {issue['description']}")
                if issue.get("line"):
                    lines.append(f"      Line {issue['line']}")
                if issue.get("suggestion"):
                    lines.append(f"      Suggestion: {issue['suggestion']}")
            lines.append("")
        
        if validation["can_fix"]:
            lines.append("✅ Issues are auto-fixable. Fixed script:")
            lines.append("")
            lines.append("```" + language)
            lines.append(validation["fixed_script"])
            lines.append("```")
        
        if not validation["valid"] and not validation["can_fix"]:
            if validation.get("errors"):
                lines.append("")
                lines.append("❌ Script has issues that need user review or approval.")
                lines.append("Ask the user for guidance before executing.")
        
        return {
            "success": True,
            "output": "\n".join(lines),
            "error": None,
        }
        
    except Exception as e:
        logger.error(f"Script validation failed: {e}")
        return {
            "success": False,
            "output": None,
            "error": f"Validation error: {str(e)}",
        }


async def _handle_list_agents(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    List available FunnelCloud agents.
    
    Returns list of agents with their capabilities.
    """
    try:
        agents = await get_available_agents()
        
        if not agents:
            return {
                "success": True,
                "output": "No FunnelCloud agents discovered. Make sure an agent is running on the host.",
                "error": None,
            }
        
        lines = [f"Found {len(agents)} FunnelCloud agent(s):"]
        for agent in agents:
            lines.append(f"")
            lines.append(f"  Agent: {agent.agent_id}")
            lines.append(f"  Address: {agent.ip_address}:{agent.grpc_port}")
            lines.append(f"  Platform: {agent.platform}")
            lines.append(f"  Capabilities: {', '.join(agent.capabilities)}")
        
        return {
            "success": True,
            "output": "\n".join(lines),
            "error": None,
        }
        
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        return {
            "success": False,
            "output": None,
            "error": f"Agent discovery failed: {str(e)}",
        }


async def _handle_remote_execute(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a command on a remote FunnelCloud agent.
    
    Params:
        agent_id: Optional agent ID (uses first available if not specified)
        command: Command to execute (PowerShell on Windows)
        timeout: Optional timeout in seconds (default 30)
    """
    command = params.get("command", "") or params.get("cmd", "")
    # Handle list format: ["python", "-m", "venv", "..."] -> "python -m venv ..."
    if isinstance(command, list):
        command = " ".join(str(c) for c in command)
    command = str(command).strip()
    
    # ⚡ BASE64 DECODING: If command_b64 is provided, decode it (avoids JSON escaping issues)
    command_b64 = params.get("command_b64", "")
    if command_b64:
        try:
            command = base64.b64decode(command_b64).decode('utf-8')
            logger.info(f"Decoded base64 command: {command[:80]}...")
        except Exception as e:
            logger.warning(f"Failed to decode base64 command: {e}")
            # Fall back to regular command if base64 decode fails
    
    agent_id = params.get("agent_id", "") or params.get("agent", "")
    # Handle list format for agent_id too
    if isinstance(agent_id, list):
        agent_id = agent_id[0] if agent_id else ""
    agent_id = str(agent_id).strip()
    
    timeout = params.get("timeout", 86400)  # 24 hour default for remote commands
    
    if not command:
        return {
            "success": False,
            "output": None,
            "error": "No command specified for remote execution",
        }
    
    # ⛔ SAFETY: Validate script before execution
    from services.reasoning_engine import ReasoningEngine
    engine = ReasoningEngine()
    validation = engine.validate_script(command, "powershell")
    
    if not validation.get("valid", True):
        errors = validation.get("errors", [])
        error_msgs = [e.get("description", str(e)) for e in errors]
        logger.warning(f"Script validation failed: {error_msgs}")
        return {
            "success": False,
            "output": None,
            "error": f"PowerShell syntax error: {'; '.join(error_msgs)}. Fix the command and try again.",
        }
    
    try:
        # Get agent - either specified or first available
        if agent_id:
            agent = await get_agent_by_id(agent_id)
            if not agent:
                return {
                    "success": False,
                    "output": None,
                    "error": f"Agent '{agent_id}' not found. Use list_agents to see available agents.",
                }
        else:
            agents = await get_available_agents()
            if not agents:
                return {
                    "success": False,
                    "output": None,
                    "error": "No FunnelCloud agents available. Make sure an agent is running.",
                }
            agent = agents[0]
        
        logger.info(f"Executing remote command on {agent.agent_id}: {command[:50]}...")
        
        # Execute via gRPC
        client = get_grpc_client()
        result = await client.execute(
            agent_id=agent.agent_id,
            command=command,
            task_type="powershell",
            timeout_seconds=timeout,
        )
        
        # Format output with better error messages
        output_parts = []
        output_parts.append(f"[Remote: {agent.agent_id} @ {agent.ip_address}]")
        
        # Check for specific error codes and provide helpful messages
        error_msg = None
        has_useful_output = bool(result.stdout and len(result.stdout.strip()) > 10)
        
        if not result.success:
            if result.error_code == "timeout":
                error_msg = f"Command timed out after {timeout}s. Try a faster command (e.g., add -Depth 2 to limit recursion)."
            elif result.error_code == "permission_denied":
                error_msg = "Permission denied. The command may require elevation."
            elif result.error_code == "grpc_error":
                error_msg = f"Connection error: {result.stderr}"
            elif result.error_code == "elevation_required":
                error_msg = "This command requires administrator privileges."
            elif result.error_code == "internal" and has_useful_output:
                # Command produced output but had some errors (e.g., permission denied on some files)
                # Treat as partial success - the output is still valuable
                error_msg = None  # Don't report error if we got useful data
            else:
                error_msg = result.stderr or f"Command failed with error: {result.error_code}"
        
        if result.stdout:
            output_parts.append(result.stdout)
        if result.stderr and result.success:  # Only show stderr if command succeeded (warnings)
            output_parts.append(f"STDERR: {result.stderr}")
        if not result.stdout and not result.stderr and result.success:
            output_parts.append("(no output)")
        if not result.success and error_msg:
            output_parts.append(f"ERROR: {error_msg}")
        
        output_parts.append(f"[Exit code: {result.exit_code}, Duration: {result.duration_ms}ms]")
        
        # If we got useful output, treat as success even if exit code was non-zero
        # (common with PowerShell commands that have partial permission errors)
        effective_success = result.success or has_useful_output
        
        return {
            "success": effective_success,
            "output": "\n".join(output_parts),
            "error": error_msg,
        }
        
    except Exception as e:
        logger.error(f"Remote execution failed: {e}")
        return {
            "success": False,
            "output": None,
            "error": f"Remote execution failed: {str(e)}",
        }

