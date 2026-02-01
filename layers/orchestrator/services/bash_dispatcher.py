"""
Bash Dispatcher - FunnelCloud Remote Execute Only

The core principle: The LLM reasons and generates commands from its training.
Only remote_execute is provided as a tool - everything else is LLM reasoning.

Tools:
  - remote_execute: Execute command on a FunnelCloud agent (the ONLY execution tool)
  - list_agents: Discover available FunnelCloud agents  
  - think: Chain-of-thought reasoning (no execution)
  - complete: Signal task completion

All file operations, code execution, etc. are handled by remote_execute
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
    Dispatch tool execution - only remote_execute for FunnelCloud agents.
    
    Tools:
      - remote_execute: Execute command on agent (THE ONLY execution tool)
      - list_agents: Get available agents
      - think: Reasoning step (no execution)
      - complete: Signal completion
    """
    
    # === REMOTE_EXECUTE: Execute on FunnelCloud agent ===
    if tool == "remote_execute":
        agent_id = params.get("agent_id", "")
        command = params.get("command", "")
        
        if not agent_id:
            return {"success": False, "output": "", "error": "No agent_id provided. Use list_agents first to discover available agents."}
        if not command:
            return {"success": False, "output": "", "error": "No command provided"}
        
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
    
    # === REMOTE_EXECUTE_ALL: Execute on ALL agents ===
    if tool == "remote_execute_all":
        command = params.get("command", "")
        if not command:
            return {"success": False, "output": "", "error": "No command provided"}
        
        agents = await get_available_agents()
        if not agents:
            return {"success": False, "output": "", "error": "No agents available. Use list_agents first."}
        
        # Execute on all agents in parallel
        grpc_client = get_grpc_client()
        tasks = []
        for agent in agents:
            task_type = "powershell" if agent.platform == "windows" else "shell"
            tasks.append(grpc_client.execute(
                agent_id=agent.agent_id,
                command=command,
                task_type=task_type,
                timeout_seconds=params.get("timeout", 60),
            ))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        outputs = []
        all_success = True
        for agent, result in zip(agents, results):
            if isinstance(result, Exception):
                outputs.append(f"[{agent.agent_id}] ERROR: {result}")
                all_success = False
            else:
                # result is TaskResult from grpc_client.execute()
                task_result: TaskResult = result  # type: ignore
                if task_result.success:
                    outputs.append(f"[{agent.agent_id}]\n{task_result.stdout or task_result.stderr or ''}")
                else:
                    outputs.append(f"[{agent.agent_id}] ERROR: {task_result.stderr or 'Unknown'}")
                    all_success = False
        
        return {
            "success": all_success,
            "output": "\n\n".join(outputs),
            "error": None if all_success else "Some agents failed",
            "agent_count": len(agents),
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
    
    # === LIST_AGENTS: Get available agents ===
    if tool == "list_agents":
        agents = await get_available_agents()
        if not agents:
            return {"success": True, "output": "No agents available", "error": None}
        
        lines = ["Available agents:"]
        for a in agents:
            lines.append(f"  - {a.agent_id}: {a.hostname} ({a.platform}) @ {a.ip_address}:{a.grpc_port}")
        
        return {"success": True, "output": "\n".join(lines), "error": None}
    
    # === UNKNOWN TOOL ===
    return {
        "success": False,
        "output": "",
        "error": f"Unknown tool: {tool}. Available: remote_execute, remote_execute_all, list_agents, think, complete",
    }


# Tool definitions for the LLM - ONLY remote_execute
REMOTE_EXECUTE_TOOLS = """
Available tools (use JSON format):

1. remote_execute - Execute command on a specific FunnelCloud agent
   {"tool": "remote_execute", "params": {"agent_id": "workstation01", "command": "hostname"}}
   
   This is the ONLY execution tool. Use it for ALL operations:
   - File operations (read/write/list)
   - Code execution
   - System commands
   - Everything that requires running on a machine

2. remote_execute_all - Execute same command on ALL agents (parallel)
   {"tool": "remote_execute_all", "params": {"command": "uptime"}}

3. list_agents - Discover available FunnelCloud agents (CALL FIRST)
   {"tool": "list_agents", "params": {}}

4. think - Reason through a problem (no execution)
   {"tool": "think", "params": {"thought": "I need to first check if the file exists..."}}

5. complete - Signal task completion with answer
   {"tool": "complete", "params": {"answer": "Successfully updated the config"}}

WORKFLOW:
1. ALWAYS call list_agents FIRST to discover available machines
2. Use remote_execute with the appropriate agent_id for ALL operations
3. Generate the correct commands based on agent platform:
   - Windows agents: PowerShell (Get-ChildItem, Get-Content, Set-Content, etc.)
   - Linux agents: Bash (ls, cat, echo, sed, etc.)
"""
