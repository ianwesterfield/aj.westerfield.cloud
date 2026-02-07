"""
Bash Dispatcher - FunnelCloud Execute Only

The core principle: The LLM reasons and generates commands from its training.
Only execute is provided as a tool - everything else is LLM reasoning.

Tools:
  - execute: Execute command on a FunnelCloud agent (the ONLY execution tool)
  - think: Chain-of-thought reasoning (no execution)
  - complete: Signal task completion

Agent discovery is done via execute on localhost with Invoke-RestMethod to /discover-peers.
All file operations, code execution, etc. are handled by execute
on the appropriate FunnelCloud agent. The LLM generates:
  - Windows: PowerShell commands (Get-Content, Set-Content, etc.)
  - Linux: Bash commands (cat, echo, sed, etc.)
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from schemas.models import WorkspaceContext
from services.grpc_client import get_grpc_client, TaskResult
from services.agent_discovery import get_discovery_service, AgentCapabilities


logger = logging.getLogger("orchestrator.dispatch")


async def get_available_agents() -> List[AgentCapabilities]:
    """Get list of available FunnelCloud agents via discovery."""
    discovery = get_discovery_service()
    return await discovery.discover(force=False)


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
    Dispatch tool execution - only execute for FunnelCloud agents.

    Tools:
      - execute: Execute command on agent (THE ONLY execution tool)
      - think: Reasoning step (no execution)
      - complete: Signal completion
    """

    # === EXECUTE: Execute on FunnelCloud agent ===
    if tool == "execute":
        agent_id = params.get("agent_id", "")
        command = params.get("command", "")

        if not agent_id:
            return {
                "success": False,
                "output": "",
                "error": "No agent_id provided. Use execute on localhost with discover-peers first.",
            }
        if not command:
            return {"success": False, "output": "", "error": "No command provided"}

        # === LOCALHOST: Special bootstrap agent for discovery ===
        if agent_id == "localhost":
            import httpx
            import os

            local_port = os.environ.get("FUNNEL_AGENT_HTTP_PORT", "41421")
            local_url = f"http://localhost:{local_port}"

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # Handle discover-peers command specially
                    if "discover-peers" in command.lower():
                        response = await client.get(f"{local_url}/discover-peers")
                        if response.status_code == 200:
                            return {
                                "success": True,
                                "output": response.text,
                                "error": None,
                                "agent_id": "localhost",
                                "platform": "linux",
                            }
                        else:
                            return {
                                "success": False,
                                "output": "",
                                "error": f"discover-peers failed: {response.status_code}",
                            }
                    # Other localhost commands - try to execute via shell
                    else:
                        import asyncio

                        proc = await asyncio.create_subprocess_shell(
                            command,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )
                        stdout, stderr = await asyncio.wait_for(
                            proc.communicate(), timeout=60
                        )
                        return {
                            "success": proc.returncode == 0,
                            "output": (
                                stdout.decode()
                                if stdout
                                else stderr.decode() if stderr else ""
                            ),
                            "error": (
                                stderr.decode()
                                if stderr and proc.returncode != 0
                                else None
                            ),
                            "agent_id": "localhost",
                            "platform": "linux",
                        }
            except Exception as e:
                return {
                    "success": False,
                    "output": "",
                    "error": f"localhost execution failed: {e}",
                    "agent_id": "localhost",
                }

        # Find agent
        agent = await get_agent_by_id(agent_id)
        if not agent:
            available = await get_available_agents()
            agent_list = ", ".join(a.agent_id for a in available) or "none"
            return {
                "success": False,
                "output": "",
                "error": f"Agent '{agent_id}' not found. Available: {agent_list}",
            }

        # Execute via gRPC - detect command type based on agent platform
        try:
            grpc_client = get_grpc_client()
            task_type = "powershell" if agent.platform == "windows" else "shell"

            result = await grpc_client.execute(
                agent_id=agent.agent_id,
                command=command,
                task_type=task_type,
                timeout_seconds=params.get("timeout", 60),
            )

            return {
                "success": result.success,
                "output": result.stdout or result.stderr or "",
                "error": result.stderr if not result.success else None,
                "agent_id": agent_id,
                "platform": agent.platform,  # windows or linux
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Failed to execute on {agent_id}: {e}",
                "agent_id": agent_id,
            }

    # === THINK: Reasoning step (no execution) ===
    if tool == "think":
        thought = params.get("thought", params.get("reasoning", ""))
        return {
            "success": True,
            "output": f"💭 {thought}",
            "error": None,
        }

    # === COMPLETE: Signal task completion ===
    if tool == "complete":
        message = params.get("message", "Task completed")
        error = params.get("error")

        if error:
            return {"success": False, "output": f"⚠️ {error}", "error": error}
        return {"success": True, "output": f"✅ {message}", "error": None}

    # === UNKNOWN TOOL ===
    return {
        "success": False,
        "output": "",
        "error": f"Unknown tool: {tool}. Available: execute, think, complete",
    }


# Tool definitions for the LLM - ONLY execute
EXECUTE_TOOLS = """
Available tools (use JSON format):

1. execute - Execute command on a specific FunnelCloud agent
   {"tool": "execute", "params": {"agent_id": "workstation01", "command": "hostname"}}
   
   This is the ONLY execution tool. Use it for ALL operations:
   - File operations (read/write/list)
   - Code execution
   - System commands
   - Agent discovery (Invoke-RestMethod http://localhost:41421/discover-peers)
   - Everything that requires running on a machine
   
   For multiple agents, call execute separately for each agent_id.
   
   BOOTSTRAP: Use "localhost" as agent_id to run on the local FunnelCloud agent.
   To discover all agents: {"tool": "execute", "params": {"agent_id": "localhost", "command": "Invoke-RestMethod http://localhost:41421/discover-peers"}}

2. think - Reason through a problem (no execution)
   {"tool": "think", "params": {"thought": "I need to first check if the file exists..."}}

3. complete - Signal task completion with answer
   {"tool": "complete", "params": {"answer": "Successfully updated the config"}}

WORKFLOW:
1. If you need to know what agents exist, execute discover-peers on localhost
2. Use execute with the appropriate agent_id for ALL operations
3. Generate the correct commands based on agent platform:
   - Windows agents: PowerShell (Get-ChildItem, Get-Content, Set-Content, etc.)
   - Linux agents: Bash (ls, cat, echo, sed, etc.)
"""
