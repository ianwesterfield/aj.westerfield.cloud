"""
Orchestrator API Router

Core endpoints for the agentic reasoning engine:
  - /set-workspace: Set active directory context for execution
  - /clone-workspace: Clone a git repo and set as workspace
  - /next-step: Generate single next step (may detect parallelization)
  - /run-task: Execute full task with SSE streaming (agentic loop)
  - /execute-batch: Execute parallel batch; continue on individual failures
  - /update-state: Update workspace state after tool execution
  - /reset-state: Reset state for new task
"""

import asyncio
import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import List, Optional, AsyncGenerator

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from schemas.models import (
    WorkspaceContext,
    SetWorkspaceRequest,
    CloneWorkspaceRequest,
    CloneWorkspaceResponse,
    NextStepRequest,
    NextStepResponse,
    ExecuteBatchRequest,
    BatchResult,
    RunTaskRequest,
    TaskEvent,
)
from services.reasoning_engine import ReasoningEngine
from services.task_planner import TaskPlanner
from services.parallel_executor import ParallelExecutor
from services.memory_connector import MemoryConnector
from services.workspace_state import WorkspaceState, get_workspace_state, reset_workspace_state
from services.tool_dispatcher import dispatch_tool
from services.agent_discovery import get_discovery_service, AgentCapabilities
from utils.workspace_context import WorkspaceContextManager


logger = logging.getLogger("orchestrator.api")
router = APIRouter(tags=["orchestrator"])

# Service instances (singleton pattern)
_workspace_manager: Optional[WorkspaceContextManager] = None
_reasoning_engine: Optional[ReasoningEngine] = None
_task_planner: Optional[TaskPlanner] = None
_parallel_executor: Optional[ParallelExecutor] = None
_memory_connector: Optional[MemoryConnector] = None


def _get_workspace_manager() -> WorkspaceContextManager:
    global _workspace_manager
    if _workspace_manager is None:
        _workspace_manager = WorkspaceContextManager()
    return _workspace_manager


def _get_reasoning_engine() -> ReasoningEngine:
    global _reasoning_engine
    if _reasoning_engine is None:
        _reasoning_engine = ReasoningEngine()
    return _reasoning_engine


def _get_task_planner() -> TaskPlanner:
    global _task_planner
    if _task_planner is None:
        _task_planner = TaskPlanner()
    return _task_planner


def _get_parallel_executor() -> ParallelExecutor:
    global _parallel_executor
    if _parallel_executor is None:
        _parallel_executor = ParallelExecutor()
    return _parallel_executor


def _get_memory_connector() -> MemoryConnector:
    global _memory_connector
    if _memory_connector is None:
        _memory_connector = MemoryConnector()
    return _memory_connector


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/set-workspace", response_model=WorkspaceContext)
async def set_workspace(request: SetWorkspaceRequest) -> WorkspaceContext:
    """
    Set the active workspace directory for execution.
    
    All subsequent operations will be scoped to this directory.
    Returns the workspace context with available paths and permissions.
    """
    logger.info(f"Setting workspace to: {request.cwd}")
    
    try:
        manager = _get_workspace_manager()
        context = await manager.set_workspace(
            cwd=request.cwd,
            user_id=request.user_id,
        )
        logger.info(f"Workspace set: {context.cwd} ({len(context.available_paths)} paths)")
        return context
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/discover-agents")
async def discover_agents(force: bool = False):
    """
    Discover FunnelCloud agents on the network.
    
    Broadcasts UDP discovery and returns list of available agents.
    Results are cached for 5 minutes unless force=True.
    
    Args:
        force: If True, bypass cache and re-discover
        
    Returns:
        List of agent capabilities
    """
    logger.info(f"Agent discovery requested (force={force})")
    discovery = get_discovery_service()
    agents = await discovery.discover(force=force)
    return {
        "agents": [agent.to_dict() for agent in agents],
        "count": len(agents),
    }


@router.get("/agents")
async def list_agents():
    """
    List currently cached FunnelCloud agents.
    
    Returns cached agents without re-broadcasting.
    Use /discover-agents to refresh the list.
    """
    discovery = get_discovery_service()
    return {
        "agents": discovery.list_agents(),
        "count": len(discovery.list_agents()),
    }


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """
    Get details for a specific agent by ID.
    """
    discovery = get_discovery_service()
    agent = discovery.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    return agent.to_dict()


@router.post("/clone-workspace", response_model=CloneWorkspaceResponse)
async def clone_workspace(request: CloneWorkspaceRequest) -> CloneWorkspaceResponse:
    """
    Clone a git repository and set it as the active workspace.
    
    Useful for working with remote codebases. The repo is cloned into
    /workspace/<repo_name> and automatically set as the active workspace.
    
    If the directory already exists, it will pull latest changes instead.
    """
    workspace_root = os.getenv("WORKSPACE_ROOT", "/workspace")
    
    # Extract repo name from URL
    # Handles: https://github.com/user/repo.git, git@github.com:user/repo.git
    repo_name = request.target_name
    if not repo_name:
        match = re.search(r"[/:]([^/:]+?)(?:\.git)?$", request.repo_url)
        if match:
            repo_name = match.group(1)
        else:
            repo_name = "cloned_repo"
    
    target_path = Path(workspace_root) / repo_name
    
    try:
        if target_path.exists():
            # Directory exists - pull latest
            logger.info(f"Workspace exists, pulling latest: {target_path}")
            result = subprocess.run(
                ["git", "pull"],
                cwd=str(target_path),
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                return CloneWorkspaceResponse(
                    success=False,
                    workspace_path=str(target_path),
                    message=f"Git pull failed: {result.stderr}",
                )
            message = f"Pulled latest changes: {result.stdout.strip()}"
        else:
            # Clone the repository
            logger.info(f"Cloning {request.repo_url} to {target_path}")
            cmd = ["git", "clone", request.repo_url, str(target_path)]
            if request.branch:
                cmd.extend(["--branch", request.branch])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout for large repos
            )
            if result.returncode != 0:
                return CloneWorkspaceResponse(
                    success=False,
                    workspace_path=str(target_path),
                    message=f"Git clone failed: {result.stderr}",
                )
            message = f"Cloned successfully"
        
        # Set as active workspace
        manager = _get_workspace_manager()
        context = await manager.set_workspace(
            cwd=str(target_path),
            user_id=request.user_id,
        )
        
        return CloneWorkspaceResponse(
            success=True,
            workspace_path=str(target_path),
            message=message,
            context=context,
        )
        
    except subprocess.TimeoutExpired:
        return CloneWorkspaceResponse(
            success=False,
            workspace_path=str(target_path),
            message="Clone operation timed out",
        )
    except Exception as e:
        logger.error(f"Clone failed: {e}")
        return CloneWorkspaceResponse(
            success=False,
            workspace_path=str(target_path),
            message=f"Clone failed: {str(e)}",
        )


@router.post("/next-step", response_model=NextStepResponse)
async def next_step(request: NextStepRequest) -> NextStepResponse:
    """
    Generate the next reasoning step for a task.
    
    Uses external WorkspaceState for ground-truth tracking (not LLM memory).
    The state is injected into the prompt so LLM doesn't need to track it.
    
    The response includes:
      - tool: The tool to execute
      - params: Parameters for the tool
      - batch_id: If parallelizable, a batch identifier
      - reasoning: Short status note for the user
    """
    logger.info(f"Generating next step for task: {request.task[:50]}...")
    
    reasoning_engine = _get_reasoning_engine()
    task_planner = _get_task_planner()
    memory_connector = _get_memory_connector()
    
    # Get or create workspace state
    workspace_state = get_workspace_state()
    
    # 1. Retrieve relevant patterns from memory
    memory_context = []
    if request.user_id:
        memory_context = await memory_connector.search_patterns(
            query=request.task,
            user_id=request.user_id,
            top_k=3,
        )
        
        # Extract user info from memory results and store in state
        for mem in memory_context:
            payload = mem.get("payload", {})
            if payload.get("facts"):
                facts = payload["facts"]
                if facts.get("names"):
                    workspace_state.user_info["name"] = facts["names"][0]
                if facts.get("emails"):
                    workspace_state.user_info["email"] = facts["emails"][0]
    
    # 2. Generate next step using reasoning engine with external state
    step = await reasoning_engine.generate_next_step(
        task=request.task,
        history=request.history or [],
        memory_context=memory_context,
        workspace_context=request.workspace_context,
        workspace_state=workspace_state,  # Pass external state
    )
    
    # 3. Check if step can be parallelized
    if step.tool == "batch":
        # Task planner detected parallel opportunity
        batch_steps = await task_planner.expand_batch(step, request.workspace_context)
        return NextStepResponse(
            tool="batch",
            params={"steps": [s.model_dump() for s in batch_steps]},
            batch_id=step.batch_id,
            reasoning=step.reasoning,
            is_batch=True,
        )
    
    return NextStepResponse(
        tool=step.tool,
        params=step.params,
        batch_id=None,
        reasoning=step.reasoning,
        is_batch=False,
    )


@router.post("/execute-batch", response_model=BatchResult)
async def execute_batch(request: ExecuteBatchRequest) -> BatchResult:
    """
    Execute a batch of steps in parallel.
    
    Uses asyncio.gather to run all steps concurrently.
    Individual failures do not cascade - other steps continue.
    Returns aggregated results with success/failure counts.
    """
    logger.info(f"Executing batch {request.batch_id} with {len(request.steps)} steps")
    
    executor = _get_parallel_executor()
    memory_connector = _get_memory_connector()
    
    # Execute batch
    result = await executor.execute_batch(
        steps=request.steps,
        batch_id=request.batch_id,
        workspace_context=request.workspace_context,
    )
    
    # Store execution trace for learning
    if request.user_id:
        await memory_connector.store_execution_trace(
            user_id=request.user_id,
            batch_id=request.batch_id,
            result=result,
        )
    
    logger.info(
        f"Batch {request.batch_id} complete: "
        f"{result.successful_count} OK, {result.failed_count} failed"
    )
    
    return result

# ============================================================================
# State Management Endpoints
# ============================================================================

from pydantic import BaseModel, Field
from typing import Dict, Any


class UpdateStateRequest(BaseModel):
    """Request to update workspace state after tool execution."""
    tool: str = Field(..., description="Tool that was executed")
    params: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    output: str = Field(default="", description="Tool output")
    success: bool = Field(..., description="Whether execution succeeded")


class StateResponse(BaseModel):
    """Response with current workspace state summary."""
    scanned_paths: list
    total_files: int
    total_dirs: int
    edited_files: list
    completed_steps: int
    user_info: Dict[str, str]


@router.post("/update-state", response_model=StateResponse)
async def update_state(request: UpdateStateRequest) -> StateResponse:
    """
    Update workspace state after a tool execution.
    
    Called by the filter after each tool is executed to keep
    the external state in sync with reality.
    """
    state = get_workspace_state()
    
    # Update state based on tool result
    state.update_from_step(
        tool=request.tool,
        params=request.params,
        output=request.output,
        success=request.success,
    )
    
    logger.debug(f"State updated: {len(state.completed_steps)} steps, {len(state.files)} files")
    
    return StateResponse(
        scanned_paths=list(state.scanned_paths),
        total_files=len(state.files),
        total_dirs=len(state.dirs),
        edited_files=list(state.edited_files),
        completed_steps=len(state.completed_steps),
        user_info=state.user_info,
    )


@router.post("/reset-state", response_model=StateResponse)
async def reset_state() -> StateResponse:
    """
    Reset workspace state for a new task.
    
    Called at the start of a new task to clear previous state.
    User info is preserved across resets.
    """
    state = reset_workspace_state()
    
    logger.info("Workspace state reset")
    
    return StateResponse(
        scanned_paths=[],
        total_files=0,
        total_dirs=0,
        edited_files=[],
        completed_steps=0,
        user_info=state.user_info,
    )


@router.get("/state", response_model=StateResponse)
async def get_state() -> StateResponse:
    """
    Get current workspace state.
    
    Returns the current external state for debugging/inspection.
    """
    state = get_workspace_state()
    
    return StateResponse(
        scanned_paths=list(state.scanned_paths),
        total_files=len(state.files),
        total_dirs=len(state.dirs),
        edited_files=list(state.edited_files),
        completed_steps=len(state.completed_steps),
        user_info=state.user_info,
    )


class SetUserInfoRequest(BaseModel):
    """Request to set user info in workspace state."""
    name: str = Field(None, description="User's name").__str__()
    email: str = Field(None, description="User's email").__str__()


@router.post("/set-user-info")
async def set_user_info(request: SetUserInfoRequest) -> Dict[str, str]:
    """
    Set user info directly in workspace state.
    
    Called when user info is extracted from the task or conversation.
    """
    state = get_workspace_state()
    
    if request.name:
        state.user_info["name"] = request.name
    if request.email:
        state.user_info["email"] = request.email
    
    logger.info(f"User info set: {state.user_info}")
    
    return state.user_info


# ============================================================================
# Streaming Task Execution (Agentic Loop)
# ============================================================================

async def _execute_tool(workspace_root: str, tool: str, params: dict) -> dict:
    """
    Execute a tool via LOCAL handlers (no HTTP).
    
    Executor functionality is merged into orchestrator for reduced latency.
    """
    try:
        # FunnelCloud remote tools operate on the HOST machine, not the container
        # DO NOT resolve paths for these - they use Windows paths like C:\
        remote_tools = {"remote_execute", "list_agents"}
        
        # Resolve relative paths in params (only for local tools)
        resolved_params = params.copy()
        
        # Normalize file_path to path for consistency
        if "file_path" in resolved_params and "path" not in resolved_params:
            resolved_params["path"] = resolved_params["file_path"]
        
        if "path" in resolved_params and tool not in remote_tools:
            path = resolved_params["path"]
            project_name = workspace_root.rstrip("/").split("/")[-1].lower()
            
            # Normalize path: strip leading/trailing slashes for comparison
            path_normalized = path.strip("/").lower()
            
            # Check if path is current dir, empty, project name, or variations
            if path == "." or path == "" or path_normalized == project_name or path_normalized.startswith(project_name):
                
                # Either exact match or subpath within workspace
                if path_normalized == project_name or path == "." or path == "":
                    resolved_params["path"] = workspace_root
                else:
                    # Subpath like "aj.westerfield.cloud/filters" -> strip project prefix
                    subpath = path_normalized[len(project_name):].lstrip("/")
                
                    if subpath:
                        resolved_params["path"] = f"{workspace_root}/{subpath}"
                    else:
                        resolved_params["path"] = workspace_root
            elif path.startswith("/"):
                # Absolute path - validate it's within workspace
                if not path.startswith(workspace_root.rstrip("/")):
                    logger.warning(f"Path {path} outside workspace, using workspace root")
                    resolved_params["path"] = workspace_root
                # else: keep absolute path as-is
            else:
                # Relative path - prepend workspace
                resolved_params["path"] = f"{workspace_root}/{path}"
        
        # Build workspace context for handlers
        workspace_context = WorkspaceContext(
            workspace_root="/workspace",
            cwd=workspace_root,
            allow_file_write=True,
            allow_shell_commands=True,
            allow_code_execution=True,
            allowed_languages=["python", "powershell", "node"],
        )
        
        # Dispatch to shared tool dispatcher
        return await dispatch_tool(tool, resolved_params, workspace_context)
            
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return {"success": False, "output": None, "error": str(e)}


def _format_result_block(tool: str, params: dict, output: str, reasoning: str) -> str:
    """Format tool result as context block for LLM."""
    if tool == "scan_workspace":
        # Count lines to decide on collapsing
        line_count = output.count('\n') if output else 0
        # Unique marker for continuation detection
        marker = "<!-- aj:workspace-scan -->"
        if line_count > 30:
            # Collapse long listings
            return f"""{marker}
**Directory listing:**
<details>
<summary>📂 Click to expand ({line_count} lines)</summary>

```
{output or "(no files found)"}
```
</details>
"""
        else:
            return f"""{marker}
**Directory listing:**
```
{output or "(no files found)"}
```
"""
    
    elif tool == "read_file":
        path = params.get("path", "file")
        line_count = output.count('\n') if output else 0
        marker = "<!-- aj:file-read -->"
        if line_count > 50:
            # Collapse long file contents
            return f"""{marker}
**File: {path}**
<details>
<summary>📄 Click to expand ({line_count} lines)</summary>

```
{output or "(empty)"}
```
</details>
"""
        else:
            return f"""{marker}
**File: {path}**
```
{output or "(empty)"}
```
"""
    
    elif tool in ("write_file", "append_to_file", "replace_in_file", "insert_in_file"):
        path = params.get("path", "file")
        content = params.get("content") or params.get("text") or params.get("new_text") or ""
        content_snippet = content[:200] + "..." if len(content) > 200 else content
        return f"""<!-- aj:file-edit -->
**Edited: {path}**
✅ {tool}: `{content_snippet}`
"""
    
    elif tool == "execute_shell":
        cmd = params.get("command", "")
        return f"""<!-- aj:shell-exec -->
**Command:** `{cmd}`
```
{output or "(no output)"}
```
"""
    
    elif tool == "remote_execute":
        cmd = params.get("command", "")
        agent = params.get("agent_id", "host")
        return f"""<!-- aj:remote-exec -->
**Remote ({agent}):** `{cmd}`
```
{output or "(no output)"}
```
"""
    
    elif tool == "list_agents":
        return f"""<!-- aj:agent-list -->
**Available Agents:**
```
{output or "(no agents found)"}
```
"""
    
    else:
        return f"""### {tool} Result ###
**Reasoning:** {reasoning}

```
{output or "(no output)"}
```
### End Result ###
"""


async def _run_task_generator(request: RunTaskRequest) -> AsyncGenerator[str, None]:
    """
    Generator that yields SSE events during task execution.
    
    This is the agentic loop moved from the filter to the orchestrator.
    """
    reasoning_engine = _get_reasoning_engine()
    workspace_state = get_workspace_state()
    
    # Set model from request if provided (dynamic model selection from Open-WebUI)
    if request.model:
        reasoning_engine.set_model(request.model)
        logger.info(f"Using model from request: {request.model}")
    
    # Determine if we should preserve state from previous task
    # Preserve if: explicit flag OR workspace already has files indexed
    # (we've already scanned something in a recent request)
    should_preserve = request.preserve_state or (
        len(workspace_state.files) > 0 or len(workspace_state.dirs) > 0
    )
    
    if not should_preserve:
        # Reset state for new task
        logger.info("Resetting workspace state (no prior scan)")
        reset_workspace_state()
        workspace_state = get_workspace_state()
    else:
        # Preserve scan results but clear completed steps for new task
        workspace_state.completed_steps.clear()
        logger.info(f"Preserving workspace state: {len(workspace_state.files)} files, {len(workspace_state.dirs)} dirs indexed")
    
    # Log user request to the conversation ledger
    workspace_state.add_user_request(request.task)
    
    # Build task with memory context
    user_text = request.task
    if request.memory_context:
        user_info = []
        
        for item in request.memory_context[:3]:
            facts = item.get('facts')
        
            if facts and isinstance(facts, dict):
                for fact_type, fact_value in facts.items():
                    user_info.append(f"{fact_type}: {fact_value}")
            else:
                text = item.get('user_text', '')
        
                if text:
                    user_info.append(text)
        
        if user_info:
            info_block = "\n".join(f"- {info}" for info in user_info)
            user_text = f"User information from memory:\n{info_block}\n\nTask: {user_text}"
    
    # Set workspace
    try:
        manager = _get_workspace_manager()
        await manager.set_workspace(cwd=request.workspace_root, user_id=request.user_id)
    except Exception as e:
        yield f"data: {json.dumps({'event_type': 'error', 'status': f'Failed to set workspace: {e}', 'done': True})}\n\n"
        return
    
    # Pre-load model to prevent cold start delays
    # This ensures the model stays in Ollama's memory with KEEP_ALIVE=24h
    try:
        await reasoning_engine.warmup_model()
    except Exception as e:
        logger.warning(f"Model warmup failed (non-blocking): {e}")
    
    # === INTENT CLASSIFICATION PHASE ===
    # Determine if this is a conversational question or an actionable task
    # Conversational questions skip the OODA loop entirely
    yield f"data: {json.dumps({'event_type': 'status', 'status': '🎯 Classifying intent...', 'done': False})}\n\n"
    
    intent_result = await reasoning_engine.classify_intent(request.task)
    logger.info(f"Intent classification: {intent_result}")
    
    # === MEMORY CONTEXT PHASE ===
    # Query memory for workspace/user context BEFORE planning
    # This implements the OODA loop's "Learn" phase - recall what we already know
    yield f"data: {json.dumps({'event_type': 'status', 'status': '📚 Checking memory...', 'done': False})}\n\n"
    
    memory_connector = _get_memory_connector()
    try:
        # Search memory for patterns related to this task
        # This provides learned approaches from previous similar tasks
        search_query = request.task if len(request.task) < 100 else request.task[:100]
        relevant_patterns = await memory_connector.search_patterns(
            query=search_query,
            user_id=request.user_id,
            top_k=3
        )
        
        # Also log successful completion - this adds to memory for future reference
        if relevant_patterns:
            logger.info(f"Found {len(relevant_patterns)} relevant memory patterns for task planning")
    except Exception as e:
        logger.warning(f"Memory context retrieval failed (non-blocking): {e}")
        relevant_patterns = []
    
    # === CONVERSATIONAL SHORTCUT ===
    # If intent is conversational, skip OODA loop entirely
    if intent_result.get("intent") == "conversational":
        logger.info("Conversational intent detected - skipping OODA loop")
        yield f"data: {json.dumps({'event_type': 'status', 'status': '💬 Answering...', 'done': False})}\n\n"
        
        # Get direct answer from LLM with memory context
        answer = await reasoning_engine.answer_conversational(
            task=request.task,
            memory_context=relevant_patterns
        )
        
        # Stream the answer
        yield f"data: {json.dumps({'event_type': 'content', 'content': answer})}\n\n"
        yield f"data: {json.dumps({'event_type': 'status', 'status': '✅ Done', 'done': True, 'content': answer})}\n\n"
        return
    
    # === PLANNING PHASE (Task intent only) ===
    # Generate task plan BEFORE execution to show user what will happen
    yield f"data: {json.dumps({'event_type': 'status', 'status': '📋 Planning...', 'done': False})}\n\n"
    
    plan_steps = await reasoning_engine.generate_task_plan(request.task)
    
    # Create TaskPlan and store in workspace state
    from services.workspace_state import TaskPlan
    task_plan = TaskPlan(original_task=request.task)
    for step_desc in plan_steps:
        task_plan.add_item(step_desc)
    workspace_state.set_task_plan(task_plan)
    
    # Stream the plan to user as markdown
    plan_markdown = task_plan.format_for_display()
    yield f"data: {json.dumps({'event_type': 'plan', 'content': plan_markdown, 'steps': plan_steps})}\n\n"
    yield f"data: {json.dumps({'event_type': 'thinking', 'content': plan_markdown + chr(10) + chr(10)})}\n\n"
    
    # Emit thinking blockquote prefix
    yield f"data: {json.dumps({'event_type': 'thinking', 'content': '> 💭 '})}\n\n"
    
    step_history = []
    all_results = []
    edit_tools = ("write_file", "replace_in_file", "insert_in_file", "append_to_file")
    
    # Queue for status updates from background model checker
    status_queue: asyncio.Queue = asyncio.Queue()
    
    def on_model_status(status_msg: str):
        """Callback to queue status updates from model checker."""
        try:
            status_queue.put_nowait(status_msg)
            logger.debug(f"Status queued: {status_msg}")  # Debug logging
        except asyncio.QueueFull:
            pass  # Drop if queue is full
    
    for step_num in range(1, request.max_steps + 1):
        try:
            # Get next step from reasoning engine with streaming
            step = None
            llm_tokens = ""
            
            # Start timer for monitoring how long model takes to load
            step_start_time = asyncio.get_event_loop().time()
            
            try:
                # Create generator for this step
                gen = reasoning_engine.generate_next_step_streaming(
                    task=user_text,
                    history=[],  # History is now in workspace_state
                    memory_context=relevant_patterns,  # Pass memory patterns from search above
                    workspace_context=None,
                    workspace_state=workspace_state,
                    status_callback=on_model_status,
                )
                
                async for token, parsed_step in gen:
                    # Flush status queue on EVERY iteration, not just periodically
                    # This ensures loading progress updates show immediately
                    try:
                        while not status_queue.empty():
                            status_msg = status_queue.get_nowait()
                            logger.debug(f"Flushing status: {status_msg}")
                            yield f"data: {json.dumps({'event_type': 'status', 'status': status_msg, 'done': False})}\n\n"
                    except asyncio.QueueEmpty:
                        pass
                    
                    # Small sleep to allow other tasks to run
                    await asyncio.sleep(0.001)
                    
                    if token:
                        # Stream each token as it arrives
                        llm_tokens += token
                        yield f"data: {json.dumps({'event_type': 'thinking', 'content': token})}\n\n"
                    if parsed_step is not None:
                        step = parsed_step
                
                # Final flush after streaming ends
                try:
                    while not status_queue.empty():
                        status_msg = status_queue.get_nowait()
                        logger.debug(f"Final flush: {status_msg}")
                        yield f"data: {json.dumps({'event_type': 'status', 'status': status_msg, 'done': False})}\n\n"
                except asyncio.QueueEmpty:
                    pass
            except Exception as e:
                logger.error(f"Error during step generation: {e}", exc_info=True)
                yield f"data: {json.dumps({'event_type': 'error', 'status': f'Reasoning error: {e}', 'done': True})}\n\n"
                break
            
            # End the thinking stream with newline
            newline_event = json.dumps({'event_type': 'thinking', 'content': '\n'})
            yield f"data: {newline_event}\n\n"
            
            if step is None:
                logger.error("No step returned from reasoning engine")
                break
            
            tool = step.tool
            params = step.params
            reasoning = step.reasoning or ""
            
            # Handle completion
            if tool == "complete":
                if params.get("error"):
                    all_results.append(f"""<!-- aj:error -->
⚠️ {params.get('error')}
""")
                elif params.get("answer"):
                    # LLM provided an answer directly from cached state
                    all_results.append(f"""<!-- aj:direct-answer -->
{params.get('answer')}
""")
                break
            
            # Build status message
            tool_path = params.get("path", "")
            short_path = tool_path.split("/")[-1].split("\\")[-1] if tool_path else ""
            
            # Descriptive icons for each tool type
            tool_icons = {
                "scan_workspace": "📂",
                "list_dir": "📁",
                "read_file": "📖",
                "write_file": "📝",
                "replace_in_file": "✏️",
                "insert_in_file": "✏️",
                "append_to_file": "➕",
                "delete_file": "🗑️",
                "execute_shell": "🔧",
                "execute_code": "▶️",
                "search_files": "🔎",
                "grep": "🔎",
                "remote_execute": "🖥️",
                "list_agents": "🔍",
            }
            icon = tool_icons.get(tool, "⚙️")
            
            # Build action description
            if tool == "scan_workspace":
                action = f"Scanning {short_path or 'workspace'}"
            elif tool == "list_dir":
                action = f"Listing {short_path or 'directory'}"
            elif tool == "read_file":
                action = f"Reading {short_path}"
            elif tool in edit_tools:
                action = f"Editing {short_path}"
            elif tool == "delete_file":
                action = f"Deleting {short_path}"
            elif tool == "execute_shell":
                cmd = params.get("command", "")[:25]
                action = f"Running `{cmd}`"
            elif tool == "remote_execute":
                cmd = params.get("command", "")[:30]
                action = f"Remote: `{cmd}`"
            elif tool == "list_agents":
                action = "Discovering agents"
            elif tool == "execute_code":
                lang = params.get("language", "code")
                action = f"Executing {lang}"
            elif tool in ("search_files", "grep"):
                query = params.get("query", params.get("pattern", ""))[:20]
                action = f"Searching for `{query}`"
            else:
                action = tool
            
            # Status is succinct: just icon + action (no reasoning/notes)
            status = f"{icon} {action}"
            
            # Silence batch edits after the first
            if tool in edit_tools:
                edit_count = sum(1 for h in step_history if h["tool"] in edit_tools and h.get("success"))
                if edit_count > 0:
                    status = None  # Silent for batch edits
            
            if status:
                yield f"data: {json.dumps({'event_type': 'status', 'step_num': step_num, 'tool': tool, 'status': status, 'done': False})}\n\n"
            
            # Execute tool
            result = await _execute_tool(request.workspace_root, tool, params)
            success = result.get("success", False)
            output = result.get("output")
            error = result.get("error")
            
            # Update workspace state
            workspace_state.update_from_step(
                tool=tool,
                params={k: v for k, v in params.items() if k not in ("content", "text", "new_text")},
                output=output[:500000] if output else "",  # DEV MODE: 500KB limit
                success=success,
            )
            
            # Advance task plan on successful steps
            if success and workspace_state.task_plan:
                workspace_state.advance_plan()
            
            # Record step
            step_history.append({
                "step_id": f"step_{step_num}",
                "tool": tool,
                "params": {k: v for k, v in params.items() if k != "content"},
                "success": success,
                "output": output[:100000] if output else None,  # DEV MODE: 100KB
                "error": error,
            })
            
            # Format result for context
            if success:
                result_block = _format_result_block(tool, params, output.__str__(), reasoning)
                all_results.append(result_block)
                
                # Yield result event with appropriate output length
                # DEV MODE: Max everything out - local hardware
                output_limit = 100000  # No practical limit
                yield f"data: {json.dumps({'event_type': 'result', 'step_num': step_num, 'tool': tool, 'result': {'success': True, 'output_preview': (output[:output_limit] if output else None)}, 'done': False})}\n\n"
                
                # No observation needed - raw output speaks for itself
            else:
                error_snippet = (error[:40] + "...") if error and len(error) > 40 else (error or "unknown")
                yield f"data: {json.dumps({'event_type': 'status', 'step_num': step_num, 'tool': tool, 'status': f'⚠️ Failed: {error_snippet}', 'done': False})}\n\n"
                
                # Stream error observation
                err_content = f'\n> ↳ ❌ _{error_snippet}_\n'
                err_event = json.dumps({'event_type': 'thinking', 'content': err_content})
                yield f"data: {err_event}\n\n"
                
                all_results.append(f"""### Step {step_num} Error ###
**Tool:** {tool}
**Reasoning:** {reasoning}
**Error:** {error or "Unknown error"}
### End Error ###
""")
            
            # Small delay to prevent overwhelming the client
            await asyncio.sleep(0.01)
            
        except Exception as e:
            logger.error(f"Step {step_num} error: {e}")
            yield f"data: {json.dumps({'event_type': 'error', 'step_num': step_num, 'status': f'Error: {str(e)[:50]}', 'done': False})}\n\n"
    
    # Build final context
    if all_results:
        file_ops = sum(1 for r in all_results if "File Operation Result" in r)
        scan_ops = sum(1 for r in all_results if "Workspace Files" in r)
        read_ops = sum(1 for r in all_results if "File Content:" in r)
        
        header = """### TASK COMPLETED ###
**CRITICAL:** Actions below have ALREADY been executed. Report in PAST TENSE.
"""
        if file_ops > 0:
            header += f"**Files modified:** {file_ops}\n"
        header += "### Action Log ###\n"
        
        # Context-appropriate summarization instructions
        if scan_ops > 0 and file_ops == 0 and read_ops == 0:
            # User just asked to list files - give a brief summary
            footer = """### End Action Log ###

⚠️ SUMMARIZATION: Give a BRIEF answer appropriate to the question.
- For "list files" / "what's in workspace": Just say "The workspace contains X directories and Y files" 
  then list only TOP-LEVEL items (not full paths). Example: "filters/, layers/, README.md, etc."
- Do NOT list every single file path - that's what the raw output is for
- Keep your summary to 2-3 sentences max for simple queries
- NEVER mention internal terms like "workspace state", "scan_workspace", "LARGEST FILES section", etc.
- Speak naturally: "I found..." or "The largest files are..." NOT "The state shows..."
"""
        elif file_ops > 0:
            # User made edits - confirm what was done
            footer = """### End Action Log ###

⚠️ SUMMARIZATION: Report EXACTLY what was done, briefly.
- Say what files were created/modified and what content was added
- Use past tense: "I added...", "I created...", "I updated..."
- Keep it concise - 1-2 sentences per file operation
- Do NOT dump the entire file content in your response
- NEVER mention internal terms like "workspace state", tool names, or section headers
"""
        else:
            # Generic - read operations, shell commands, etc.
            footer = """### End Action Log ###

⚠️ SUMMARIZATION: Answer the user's question directly and concisely.
- If they asked a yes/no question, answer yes or no first
- If they asked for specific info, provide just that info
- Do NOT dump raw command output - summarize the key findings
- Keep your response brief and helpful
- NEVER mention internal terms like "workspace state", tool names, or section headers
- Speak naturally as if you personally explored the files
"""
        
        final_context = header + "\n".join(all_results) + footer
    else:
        final_context = None
    
    # Build completion status
    if step_history:
        step_count = len(step_history)
        complete_status = f"✅ Done" if step_count == 1 else f"✅ Done ({step_count} steps)"
    else:
        complete_status = "✅ Done"
    
    # Emit completion with final context
    yield f"data: {json.dumps({'event_type': 'complete', 'status': complete_status, 'result': {'context': final_context, 'steps_executed': len(step_history)}, 'done': True})}\n\n"


@router.post("/run-task")
async def run_task(request: RunTaskRequest):
    """
    Execute a complete task with Server-Sent Events (SSE) streaming.
    
    This moves the entire agentic loop from the filter to the orchestrator.
    The filter can now simply:
      1. POST /run-task
      2. Stream SSE events
      3. Forward status events to __event_emitter__
      4. Inject final context into conversation
    
    Event types:
      - status: UI status update (step_num, tool, status, done)
      - result: Step result (step_num, tool, result, done)
      - error: Error occurred (status, done)
      - complete: Task finished (result.context, result.steps_executed, done)
    """
    return StreamingResponse(
        _run_task_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )