"""
Bash Dispatcher - "All You Need is Bash" Philosophy

The core principle: Let the LLM generate bash commands for everything.
No file handlers, no polyglot routers, no over-engineering.

Tools:
  - bash: Execute any command locally
  - remote_bash: Execute command on a FunnelCloud agent
  - think: Chain-of-thought reasoning (no execution)
  - complete: Signal task completion

File operations? The LLM generates:
  - cat file.txt (read)
  - echo "content" > file.txt (write)
  - sed -i 's/old/new/g' file.txt (replace)
  - rm file.txt (delete)
  - ls -la (list)

Code execution? The LLM generates:
  - python -c "print('hello')"
  - node -e "console.log('hello')"
  - pwsh -c "Get-Process"
"""

import asyncio
import logging
import shlex
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from schemas.models import WorkspaceContext
from services.grpc_client import get_grpc_client, TaskResult
from services.agent_discovery import get_discovery_service, AgentCapabilities


logger = logging.getLogger("orchestrator.bash")


@dataclass
class BashResult:
    """Result of a bash command execution."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    

class BashExecutor:
    """
    Simple bash command executor.
    
    No blocklists, no tokenization complexity.
    The LLM is responsible for generating safe commands.
    Workspace context can limit permissions if needed.
    """
    
    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root or os.getcwd()
    
    async def execute(
        self,
        command: str,
        timeout: int = 60,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> BashResult:
        """
        Execute a bash command.
        
        Args:
            command: The bash command to execute
            timeout: Timeout in seconds
            cwd: Working directory (defaults to workspace root)
            env: Additional environment variables
            
        Returns:
            BashResult with stdout, stderr, exit_code
        """
        work_dir = cwd or self.workspace_root
        
        # Merge environment
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
        
        try:
            # Use bash -c for full shell capabilities (pipes, redirects, etc.)
            process = await asyncio.create_subprocess_exec(
                "bash", "-c", command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir,
                env=full_env,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return BashResult(
                success=process.returncode == 0,
                stdout=stdout.decode("utf-8", errors="replace").strip(),
                stderr=stderr.decode("utf-8", errors="replace").strip(),
                exit_code=process.returncode or 0,
            )
            
        except asyncio.TimeoutError:
            return BashResult(
                success=False,
                stdout="",
                stderr=f"Command timed out after {timeout}s",
                exit_code=-1,
            )
        except Exception as e:
            return BashResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
            )


# Singleton executor
_bash_executor: Optional[BashExecutor] = None


def get_bash_executor(workspace_root: Optional[str] = None) -> BashExecutor:
    """Get or create singleton BashExecutor."""
    global _bash_executor
    if _bash_executor is None:
        _bash_executor = BashExecutor(workspace_root)
    return _bash_executor


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
    Dispatch tool execution - simplified to just bash.
    
    Tools:
      - bash: Execute command locally
      - remote_bash: Execute command on agent
      - think: Reasoning step (no execution)
      - complete: Signal completion
      - list_agents: Get available agents
    """
    
    # === BASH: Local command execution ===
    if tool == "bash":
        command = params.get("command", "")
        if not command:
            return {"success": False, "output": "", "error": "No command provided"}
        
        timeout = params.get("timeout", 60)
        cwd = params.get("cwd")
        
        executor = get_bash_executor()
        result = await executor.execute(command, timeout=timeout, cwd=cwd)
        
        # Combine stdout/stderr for output
        output = result.stdout
        if result.stderr and result.success:
            output = f"{output}\n{result.stderr}" if output else result.stderr
        
        return {
            "success": result.success,
            "output": output,
            "error": result.stderr if not result.success else None,
            "exit_code": result.exit_code,
        }
    
    # === REMOTE_BASH: Execute on FunnelCloud agent ===
    if tool == "remote_bash":
        agent_id = params.get("agent_id", "")
        command = params.get("command", "")
        
        if not agent_id:
            return {"success": False, "output": "", "error": "No agent_id provided"}
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
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Failed to execute on {agent_id}: {e}",
                "agent_id": agent_id,
            }
    
    # === REMOTE_BASH_ALL: Execute on ALL agents ===
    if tool == "remote_bash_all":
        command = params.get("command", "")
        if not command:
            return {"success": False, "output": "", "error": "No command provided"}
        
        agents = await get_available_agents()
        if not agents:
            return {"success": False, "output": "", "error": "No agents available"}
        
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
        "error": f"Unknown tool: {tool}. Available: bash, remote_bash, remote_bash_all, think, complete, list_agents",
    }


# Tool definitions for the LLM
BASH_TOOLS = """
Available tools (use JSON format):

1. bash - Execute any command locally
   {"tool": "bash", "command": "ls -la"}
   {"tool": "bash", "command": "cat file.txt"}
   {"tool": "bash", "command": "echo 'content' > newfile.txt"}
   {"tool": "bash", "command": "python -c 'print(1+1)'"}
   {"tool": "bash", "command": "sed -i 's/old/new/g' file.txt"}

2. remote_bash - Execute command on a specific agent
   {"tool": "remote_bash", "agent_id": "workstation01", "command": "hostname"}

3. remote_bash_all - Execute same command on ALL agents
   {"tool": "remote_bash_all", "command": "uptime"}

4. think - Reason through a problem (no execution)
   {"tool": "think", "thought": "I need to first check if the file exists..."}

5. complete - Signal task completion
   {"tool": "complete", "message": "Successfully updated the config"}

6. list_agents - Get available remote agents
   {"tool": "list_agents"}

File operations are just bash:
  - Read: cat file.txt
  - Write: echo 'content' > file.txt (or cat << 'EOF' > file.txt for multiline)
  - Append: echo 'content' >> file.txt
  - Delete: rm file.txt
  - List: ls -la
  - Find: find . -name "*.py"
  - Replace: sed -i 's/old/new/g' file.txt
  - Create dir: mkdir -p path/to/dir

Code execution is just bash:
  - Python: python -c "code" or python script.py
  - Node: node -e "code" or node script.js
  - PowerShell: pwsh -c "code"
"""
