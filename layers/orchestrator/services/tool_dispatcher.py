"""
Tool Dispatcher - Unified tool execution routing.

Provides a single entry point for dispatching tool calls to the appropriate handlers.
Used by both the orchestrator API and ParallelExecutor for consistent tool execution.

This module eliminates duplication between orchestrator.py and parallel_executor.py
by centralizing tool dispatch logic.
"""

import logging
from typing import Any, Dict, List, Optional

from schemas.models import WorkspaceContext
from services.polyglot_handler import PolyglotHandler
from services.shell_handler import ShellHandler
from services.file_handler import FileHandler
from services.grpc_client import AgentGrpcClient, get_grpc_client
from services.agent_discovery import get_discovery_service, AgentCapabilities


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
    
    # FunnelCloud remote execution
    if tool == "remote_execute":
        return await _handle_remote_execute(params)
    
    if tool == "list_agents":
        return await _handle_list_agents(params)
    
    if tool == "parallel_scan":
        return await _handle_parallel_scan(params)
    
    # Unknown tool
    logger.warning(f"Unknown tool requested: {tool}")
    return {
        "success": False,
        "output": None,
        "error": f"Unknown tool: {tool}",
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
    command = params.get("command", "")
    agent_id = params.get("agent_id", "")
    timeout = params.get("timeout", 3600)  # 1 hour default for remote commands
    
    if not command:
        return {
            "success": False,
            "output": None,
            "error": "No command specified for remote execution",
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


async def _handle_parallel_scan(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursive parallel directory scan - fans out to scan subdirectories concurrently.
    
    Strategy:
    1. Get top-level directories from the root path
    2. Fan out parallel scans for each subdirectory (excluding system dirs)
    3. For LARGE directories (>50GB), recursively break them down into subdirs
    4. Merge results with hierarchical breakdown
    
    Params:
        path: Root path to scan (e.g., "C:\\", "S:\\")
        agent_id: Optional agent ID
        max_parallel: Max concurrent scans (default 4)
        exclude: Optional list of directories to skip (default: Windows system dirs)
        breakdown_threshold_gb: Size threshold to break down large dirs (default 50GB)
    """
    import asyncio
    
    root_path = params.get("path", "C:\\")
    agent_id = params.get("agent_id", "")
    max_parallel = params.get("max_parallel", 4)
    exclude = params.get("exclude", ["Windows", "$Recycle.Bin", "System Volume Information", "Recovery"])
    breakdown_threshold_gb = params.get("breakdown_threshold_gb", 50)
    breakdown_threshold_bytes = breakdown_threshold_gb * 1024 * 1024 * 1024
    
    try:
        # Get agent
        if agent_id:
            agent = await get_agent_by_id(agent_id)
        else:
            agents = await get_available_agents()
            agent = agents[0] if agents else None
        
        if not agent:
            return {
                "success": False,
                "output": None,
                "error": "No FunnelCloud agents available.",
            }
        
        client = get_grpc_client()
        semaphore = asyncio.Semaphore(max_parallel)
        
        # Track all results
        all_files = []
        scan_errors = []
        dir_summaries = []  # [{dir, files, size_mb, subdirs: [...]}]
        
        async def get_subdirs(path: str) -> List[str]:
            """Get immediate subdirectories of a path."""
            cmd = f"Get-ChildItem -Path '{path}' -Directory -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name"
            try:
                result = await client.execute(
                    agent_id=agent.agent_id,
                    command=cmd,
                    task_type="powershell",
                    timeout_seconds=30,
                )
                if result.success and result.stdout:
                    return [d.strip() for d in result.stdout.strip().split("\n") if d.strip()]
            except Exception as e:
                logger.warning(f"Failed to list subdirs of {path}: {e}")
            return []
        
        async def scan_directory(dir_path: str, dir_name: str, depth: int = 0) -> dict:
            """
            Scan a directory. If it's large, break it down recursively.
            
            Returns: {dir, files, size_bytes, file_list, subdirs}
            """
            async with semaphore:
                cmd = f"Get-ChildItem -Path '{dir_path}' -Recurse -File -ErrorAction SilentlyContinue | Select-Object FullName, Length | ConvertTo-Csv -NoTypeInformation"
                
                try:
                    result = await client.execute(
                        agent_id=agent.agent_id,
                        command=cmd,
                        task_type="powershell",
                        timeout_seconds=600,  # 10 min per dir
                    )
                    
                    files = []
                    if result.stdout:
                        lines = result.stdout.strip().split("\n")
                        for line in lines[1:]:  # Skip CSV header
                            if line.strip() and "," in line:
                                # Parse CSV: "path","size"
                                parts = line.strip().strip('"').split('","')
                                if len(parts) >= 2:
                                    try:
                                        files.append({
                                            "path": parts[0],
                                            "size": int(parts[1]) if parts[1].isdigit() else 0
                                        })
                                    except (ValueError, IndexError):
                                        pass
                    
                    total_size = sum(f["size"] for f in files)
                    
                    dir_result = {
                        "dir": dir_name,
                        "path": dir_path,
                        "files": len(files),
                        "size_bytes": total_size,
                        "size_mb": round(total_size / (1024 * 1024), 2),
                        "file_list": files,
                        "subdirs": [],
                        "depth": depth,
                    }
                    
                    # If directory is large and we haven't gone too deep, break it down
                    if total_size > breakdown_threshold_bytes and depth < 2:
                        logger.info(f"Large dir detected: {dir_name} ({dir_result['size_mb']:.0f} MB) - breaking down...")
                        
                        # Get subdirectories for breakdown
                        subdirs = await get_subdirs(dir_path)
                        if subdirs:
                            # Group files by immediate subdirectory
                            subdir_files = {sd: [] for sd in subdirs}
                            root_files = []
                            
                            for f in files:
                                file_path = f["path"]
                                # Find which subdir this file belongs to
                                rel_path = file_path[len(dir_path):].lstrip("\\")
                                if "\\" in rel_path:
                                    first_part = rel_path.split("\\")[0]
                                    if first_part in subdir_files:
                                        subdir_files[first_part].append(f)
                                    else:
                                        root_files.append(f)
                                else:
                                    root_files.append(f)
                            
                            # Build subdirectory breakdown
                            for sd_name, sd_files in subdir_files.items():
                                if sd_files:
                                    sd_size = sum(f["size"] for f in sd_files)
                                    dir_result["subdirs"].append({
                                        "dir": sd_name,
                                        "files": len(sd_files),
                                        "size_bytes": sd_size,
                                        "size_mb": round(sd_size / (1024 * 1024), 2),
                                    })
                            
                            # Sort subdirs by size
                            dir_result["subdirs"].sort(key=lambda x: x["size_bytes"], reverse=True)
                    
                    return dir_result
                    
                except Exception as e:
                    return {
                        "dir": dir_name,
                        "path": dir_path,
                        "files": 0,
                        "size_bytes": 0,
                        "size_mb": 0,
                        "file_list": [],
                        "subdirs": [],
                        "error": str(e),
                        "depth": depth,
                    }
        
        # Step 1: Get top-level directories
        logger.info(f"Parallel scan: Getting top-level dirs from {root_path}")
        
        top_dirs = await get_subdirs(root_path)
        if not top_dirs:
            return {
                "success": False,
                "output": f"Could not list directories in {root_path}",
                "error": "No directories found",
            }
        
        # Filter excluded dirs
        scan_dirs = [d for d in top_dirs if d not in exclude and not d.startswith("$")]
        
        logger.info(f"Parallel scan: Found {len(top_dirs)} dirs, scanning {len(scan_dirs)} (excluded {len(top_dirs) - len(scan_dirs)})")
        
        # Step 2: Fan out parallel scans
        tasks = []
        for d in scan_dirs:
            full_path = f"{root_path.rstrip(chr(92))}\\{d}"
            tasks.append(scan_directory(full_path, d, depth=0))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        total_files = 0
        total_size = 0
        
        for item in results:
            if isinstance(item, Exception):
                scan_errors.append(str(item))
                continue
            
            if item.get("error"):
                scan_errors.append(f"{item['dir']}: {item['error']}")
            
            if item.get("file_list"):
                all_files.extend(item["file_list"])
                total_files += item["files"]
                total_size += item["size_bytes"]
                dir_summaries.append(item)
        
        # Sort by size descending
        dir_summaries.sort(key=lambda x: x["size_bytes"], reverse=True)
        
        # Format output with hierarchical breakdown
        output_lines = [
            f"[Parallel scan of {root_path} on {agent.agent_id}]",
            f"Scanned {len(scan_dirs)} directories in parallel (max {max_parallel} concurrent)",
            f"Excluded: {', '.join(exclude)}",
            f"Large dir breakdown threshold: {breakdown_threshold_gb} GB",
            "",
            f"TOTAL: {total_files:,} files, {round(total_size / (1024 * 1024), 2):,.2f} MB ({round(total_size / (1024 * 1024 * 1024), 2):,.2f} GB)",
            "",
            "By directory (largest first):"
        ]
        
        for ds in dir_summaries[:15]:  # Top 15 dirs
            output_lines.append(f"  {ds['dir']}: {ds['files']:,} files, {ds['size_mb']:,.2f} MB")
            
            # Show subdirectory breakdown for large dirs
            if ds.get("subdirs"):
                for sd in ds["subdirs"][:5]:  # Top 5 subdirs
                    output_lines.append(f"    └─ {sd['dir']}: {sd['files']:,} files, {sd['size_mb']:,.2f} MB")
                if len(ds["subdirs"]) > 5:
                    output_lines.append(f"    └─ ... and {len(ds['subdirs']) - 5} more subdirectories")
        
        if len(dir_summaries) > 15:
            output_lines.append(f"  ... and {len(dir_summaries) - 15} more directories")
        
        # Top 10 largest files
        all_files.sort(key=lambda x: x["size"], reverse=True)
        if all_files:
            output_lines.append("")
            output_lines.append("Largest files:")
            for f in all_files[:10]:
                size_mb = round(f["size"] / (1024 * 1024), 2)
                output_lines.append(f"  {size_mb:,.2f} MB - {f['path']}")
        
        if scan_errors:
            output_lines.append("")
            output_lines.append(f"Errors ({len(scan_errors)}):")
            for err in scan_errors[:5]:
                output_lines.append(f"  {err}")
        
        return {
            "success": True,
            "output": "\n".join(output_lines),
            "error": None,
        }
        
    except Exception as e:
        logger.error(f"Parallel scan failed: {e}")
        return {
            "success": False,
            "output": None,
            "error": f"Parallel scan failed: {str(e)}",
        }
