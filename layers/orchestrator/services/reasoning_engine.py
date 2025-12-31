"""
Reasoning Engine - LLM Coordination for Step Generation

Uses Ollama to generate structured reasoning steps from user intents.
Parses LLM output into validated Step objects.

Architecture:
- State is maintained EXTERNALLY by WorkspaceState (not by the LLM)
- LLM receives state as context, only outputs next step
- This prevents state drift and reduces token cost
"""

import os
import re
import json
import logging
import asyncio
import httpx
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Tuple

from schemas.models import Step, StepResult, WorkspaceContext
from services.workspace_state import WorkspaceState, get_workspace_state


logger = logging.getLogger("orchestrator.reasoning")

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


class ThinkingStreamParser:
    """
    Streaming parser for <think>...</think> tagged content.
    
    Handles partial tag boundaries by buffering near tag characters.
    Yields only the text content inside <think> tags safely.
    """
    
    def __init__(self):
        self._in_think = False
        self._finished = False
        self._pending = ""  # Buffer for partial tag detection
        self._think_content = ""
    
    def feed(self, token: str) -> str:
        """
        Feed a token and return any content safe to yield.
        
        Buffers characters near '<' and '>' to handle partial tags.
        Returns content only when we're confident it's complete text.
        """
        if self._finished:
            return ""
        
        # Add token to pending buffer
        self._pending += token
        
        # Check for opening tag
        if not self._in_think:
            if "<think>" in self._pending:
                self._in_think = True
                # Extract content after the opening tag
                self._pending = self._pending.split("<think>", 1)[1]
            else:
                # Not in think mode yet, discard content (keep potential partial tag)
                if "<" in self._pending:
                    # Keep from < onwards in case it's partial <think>
                    self._pending = self._pending[self._pending.rfind("<"):]
                else:
                    self._pending = ""
                return ""
        
        # We're inside <think> - look for closing tag
        if "</think>" in self._pending:
            self._finished = True
            content = self._pending.split("</think>", 1)[0]
            self._think_content += content
            return content
        
        # Check for potential partial closing tag
        # Buffer the last few chars if they could be start of </think>
        safe_content = ""
        danger_zone = 9  # Length of "</think>" plus 1 for safety
        
        if len(self._pending) > danger_zone:
            # Split: safe to yield vs keep buffered
            safe_content = self._pending[:-danger_zone]
            self._pending = self._pending[-danger_zone:]
            self._think_content += safe_content
        elif "<" in self._pending or "/" in self._pending:
            # Potential partial tag starting - hold everything
            pass
        else:
            # Small buffer, no tag chars - yield it all
            safe_content = self._pending
            self._think_content += safe_content
            self._pending = ""
        
        return safe_content
    
    def flush(self) -> str:
        """Flush any remaining buffered content (call at end of stream)."""
        if self._finished or not self._in_think:
            return ""
        # Return whatever is buffered (stream ended unexpectedly)
        content = self._pending
        self._pending = ""
        self._think_content += content
        return content
    
    def get_content(self) -> str:
        """Get all accumulated thinking content."""
        return self._think_content
    
    @staticmethod
    def extract_thinking(full_response: str) -> str:
        """Extract content between <think> and </think> from complete response."""
        match = re.search(r'<think>(.*?)</think>', full_response, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    @staticmethod
    def extract_json(full_response: str) -> str:
        """Extract JSON portion from full response (after </think>)."""
        if "</think>" in full_response:
            return full_response.split("</think>", 1)[1].strip()
        return full_response.strip()


SYSTEM_PROMPT = """You are AJ, an agentic AI that executes repository tasks step-by-step.

=== OUTPUT FORMAT ===

First, briefly think through your next action (1-2 sentences), then output JSON:

<think>
Your brief reasoning about what to do next and why.
</think>
{"tool": "tool_name", "params": {...}, "note": "Brief status"}

- The <think> block shows your reasoning to the user (keep it concise!)
- The JSON is the actual action to execute
- "note" is a SHORT status label (e.g., "Reading config", "Scanning files")

=== MISSING INFO RULE ===

If the task references info you don't have (e.g. "my name" but not provided):
<think>The user mentioned their name but I don't have that information.</think>
{"tool": "complete", "params": {"error": "MISSING_INFO: I don't know your name."}, "note": "Need info"}

NEVER guess or fabricate user information.

=== AVAILABLE TOOLS ===

- scan_workspace: List files. Params: {"path": "string"}
- read_file: Read file. Params: {"path": "string"}
- write_file: Create/overwrite file. Params: {"path": "string", "content": "string"}
- replace_in_file: Find/replace EXISTING text. Params: {"path": "string", "old_text": "string", "new_text": "string"}
- insert_in_file: ADD NEW text at start or end. Params: {"path": "string", "position": "start"|"end", "text": "string"}
- append_to_file: Append to end. Params: {"path": "string", "content": "string"}
- execute_shell: Run shell command. Params: {"command": "string"}
- none: Skip (change already present). Params: {"reason": "string"}
- complete: Done. Params: {} OR {"error": "reason"}

⚠️ CRITICAL - INSERT vs REPLACE:
- To ADD NEW text (comment, header, etc.) → use insert_in_file with position="start" or "end"
- To CHANGE EXISTING text you SAW in the file → use replace_in_file
- replace_in_file WILL FAIL if old_text is not found - it cannot add new content!
- If you need to add a comment/header that DOES NOT EXIST, you MUST use insert_in_file
- ALWAYS include a trailing newline in inserted text: "<!-- Comment -->\\n" not "<!-- Comment -->"
- For Markdown files (.md), use HTML comment syntax: <!-- Author: Name -->

=== CRITICAL RULES ===

1. PATH DISCIPLINE: Use EXACT paths from workspace state. Never invent paths.
   - Correct: ".github/copilot-instructions.md"
   - WRONG: "copilot-instructions.md" (missing directory)

2. NO RESCANS: If workspace state shows files, don't scan again.

3. NO RE-READS: If state shows "Already read" a file, DO NOT read it again. Move to editing.

3. MINIMAL EDITS: Prefer insert_in_file/replace_in_file over write_file.

4. ONE STEP: Return exactly one action. Don't bundle multiple operations.

5. PRIORITY ORDER:
   a) If no scan exists → scan_workspace(".")
   b) If task mentions file → locate in state, read if needed, then edit
   c) After all edits → complete

=== SHELL EXAMPLES ===

Git: {"tool": "execute_shell", "params": {"command": "git status"}}
     {"tool": "execute_shell", "params": {"command": "git checkout -b feature/x"}}
     {"tool": "execute_shell", "params": {"command": "git add . && git commit -m 'msg'"}}

=== LOOP DETECTION ===

If you see a step you just completed in "Completed steps", DO NOT repeat it.
If task is "list/scan files" and you already did scan_workspace → {"tool": "complete", "params": {}, "note": "Done"}
If task is "read file X" and X is in "Already read" → {"tool": "complete", "params": {}, "note": "Already read"}
If you can't make progress → {"tool": "complete", "params": {"error": "Cannot complete task"}, "note": "Stuck"}

=== COMPLETION ===

When finished: 
<think>Task is complete.</think>
{"tool": "complete", "params": {}, "note": "Done"}
"""


class ReasoningEngine:
    """
    LLM-powered reasoning engine for step generation.
    
    Architecture:
    - State is maintained externally by WorkspaceState
    - LLM receives state as context, only outputs the next step
    - This prevents hallucination and state drift
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=300.0)  # DEV MODE: Extended timeout
        self.model = OLLAMA_MODEL
        self.base_url = OLLAMA_BASE_URL
        
        # Model size estimates for load time prediction (in GB)
        # Used to estimate cold load time
        self._model_sizes = {
            "llama3.2:1b": 1.3,
            "llama3.2:3b": 2.0,
            "llama3.2": 2.0,
            "llama3.1:70b": 40.0,
            "llama3.1:8b": 4.7,
            "llama3.1": 4.7,
            "llama3:70b": 40.0,
            "llama3": 4.7,
            "mistral": 4.1,
            "phi3": 2.2,
            "qwen2.5:72b": 41.0,
            "qwen2.5:32b": 20.0,  # ~20GB actual
            "qwen2.5:14b": 9.0,
            "qwen2.5:7b": 4.4,
            "qwen2.5": 4.4,
        }
        # Estimate load speed - very conservative (0.2 GB/sec accounts for disk I/O)
        self._load_speed_gb_per_sec = 0.2
    
    def _estimate_load_time(self) -> int:
        """Estimate cold load time in seconds based on model size."""
        # Find matching model size
        for model_prefix, size_gb in self._model_sizes.items():
            if self.model.startswith(model_prefix):
                return max(5, int(size_gb / self._load_speed_gb_per_sec))
        # Default estimate for unknown models
        return 15
    
    async def check_model_status(self) -> dict:
        """
        Check if the model is loaded in Ollama.
        
        Returns:
            {"loaded": bool, "loading": bool, "size_vram": int, "details": str}
        """
        try:
            url = f"{self.base_url}/api/ps"
            response = await self.client.get(url, timeout=5.0)
            response.raise_for_status()
            data = response.json()
            
            models = data.get("models", [])
            for m in models:
                if m.get("name", "").startswith(self.model):
                    size_vram = m.get("size_vram", 0)
                    size_gb = size_vram / (1024**3) if size_vram else 0
                    return {
                        "loaded": True,
                        "loading": False,
                        "size_vram": size_vram,
                        "details": f"{self.model} loaded ({size_gb:.1f}GB VRAM)"
                    }
            
            return {"loaded": False, "loading": False, "size_vram": 0, "details": "Model not loaded"}
            
        except Exception as e:
            logger.debug(f"Model status check failed: {e}")
            return {"loaded": False, "loading": False, "size_vram": 0, "details": str(e)}
    
    async def stream_with_status(
        self,
        user_message: str,
        status_callback: Callable[[str], None],
    ) -> AsyncGenerator[Tuple[str, bool, str], None]:
        """
        Stream from Ollama while emitting status updates during cold start.
        
        Runs a background task that checks model status and shows progress
        with estimated time remaining until first token arrives.
        
        Yields same as _call_ollama_streaming: (token, in_think_block, full_response)
        """
        first_token_received = asyncio.Event()
        status_task = None
        start_time = asyncio.get_event_loop().time()
        estimated_total = self._estimate_load_time()
        
        async def status_monitor():
            """Background task to emit status while waiting for first token."""
            await asyncio.sleep(1.0)  # Initial delay before first status
            
            model_was_loaded = False
            last_status = ""
            
            while not first_token_received.is_set():
                elapsed = asyncio.get_event_loop().time() - start_time
                status = await self.check_model_status()
                
                if status["loaded"]:
                    if not model_was_loaded:
                        model_was_loaded = True
                        new_status = f"⏳ Thinking..."
                    else:
                        # Model loaded, waiting for generation - update every 5s
                        new_status = f"⏳ Thinking... ({int(elapsed)}s)"
                else:
                    # Model loading - show progress with time estimate
                    remaining = max(1, estimated_total - elapsed)
                    percent = min(95, int((elapsed / estimated_total) * 100))
                    
                    if elapsed < estimated_total:
                        new_status = f"⏳ Loading... {percent}%"
                    else:
                        # Taking longer than expected
                        new_status = f"⏳ Loading... ({elapsed:.0f}s)"
                
                # Only emit if status changed (reduces spam)
                if new_status != last_status:
                    status_callback(new_status)
                    last_status = new_status
                
                try:
                    await asyncio.wait_for(
                        first_token_received.wait(),
                        timeout=3.0  # Check every 3 seconds
                    )
                    break
                except asyncio.TimeoutError:
                    continue
        
        # Start status monitor
        status_task = asyncio.create_task(status_monitor())
        
        try:
            async for token, in_think, accumulated in self._call_ollama_streaming(user_message):
                if token and not first_token_received.is_set():
                    first_token_received.set()
                yield token, in_think, accumulated
        finally:
            first_token_received.set()  # Ensure monitor stops
            if status_task:
                status_task.cancel()
                try:
                    await status_task
                except asyncio.CancelledError:
                    pass
    
    async def generate_next_step(
        self,
        task: str,
        history: List[StepResult],
        memory_context: List[Dict[str, Any]],
        workspace_context: Optional[WorkspaceContext] = None,
        workspace_state: Optional[WorkspaceState] = None,
    ) -> Step:
        """
        Generate the next step for a task using LLM reasoning.
        
        Args:
            task: User's task description
            history: Previous step results (for backward compat, prefer workspace_state)
            memory_context: Relevant patterns from memory
            workspace_context: Current workspace settings
            workspace_state: External state (ground truth from actual tool outputs)
            
        Returns:
            Step object with tool, params, and reasoning
        """
        # Use external state if provided, otherwise fall back to old approach
        if workspace_state is None:
            workspace_state = get_workspace_state()
        
        context_parts = []
        
        # 1. Inject external state (the key change - LLM doesn't maintain this)
        state_context = workspace_state.format_for_prompt()
        if state_context:
            context_parts.append(state_context)
        
        # 2. Workspace permissions
        if workspace_context:
            context_parts.append(
                f"Workspace: {workspace_context.cwd}\n"
                f"Permissions: write={workspace_context.allow_file_write}, "
                f"shell={workspace_context.allow_shell_commands}"
            )
        
        # 3. User info from state (name, etc.)
        if workspace_state.user_info:
            user_info_text = "\n".join(f"  {k}: {v}" for k, v in workspace_state.user_info.items())
            context_parts.append(f"User info (use this, don't guess):\n{user_info_text}")
        
        # 4. Memory patterns (optional)
        if memory_context:
            patterns = "\n".join([
                f"- {p.get('description', 'Similar task')}: {p.get('approach', '')}"
                for p in memory_context[:3]
            ])
            context_parts.append(f"Relevant patterns from memory:\n{patterns}")
        
        # 5. GUARDRAIL: If too many steps without progress, force completion
        if len(workspace_state.completed_steps) >= 15:
            logger.warning(f"GUARDRAIL: {len(workspace_state.completed_steps)} steps - forcing completion check")
            # Check if we're making progress
            recent_edits = sum(1 for s in workspace_state.completed_steps[-5:] 
                             if s.tool in ("write_file", "insert_in_file", "replace_in_file", "append_to_file")
                             and s.success)
            if recent_edits == 0:
                # Not making progress - complete
                return Step(
                    step_id="guardrail_complete",
                    tool="complete",
                    params={"error": "Too many steps without progress"},
                    reasoning="Forced completion after 15 steps without recent edits",
                )
        
        context = "\n\n".join(context_parts)
        
        # Build user message
        user_message = f"Task: {task}"
        if context:
            user_message = f"{context}\n\n{user_message}"
        
        # Log prompt size (helpful for debugging)
        logger.debug(f"Prompt size: {len(user_message)} chars")
        
        # Call Ollama
        try:
            response = await self._call_ollama(user_message)
            step = self._parse_response(response, task)
            
            # Apply guardrails
            step = self._apply_guardrails(step, workspace_state)
            
            return step
            
        except Exception as e:
            logger.error(f"Reasoning engine error: {e}")
            return Step(
                step_id="error_fallback",
                tool="complete",
                params={"error": str(e)},
                reasoning=f"Error during reasoning: {e}",
            )
    
    async def _call_ollama(self, user_message: str) -> str:
        """Call Ollama API and return the response text."""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "keep_alive": -1,  # Keep model loaded indefinitely
            # No "format": "json" - we want <think>...</think> then JSON
        }
        
        logger.debug(f"Calling Ollama: {self.model}")
        
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        return data.get("message", {}).get("content", "")
    
    async def _call_ollama_streaming(self, user_message: str):
        """
        Call Ollama API with streaming.
        
        Yields (token, in_think_block, full_response) tuples:
        - token: the current token
        - in_think_block: True if we're inside <think>...</think>
        - full_response: accumulated response
        
        This allows the caller to stream only the thinking content.
        """
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "stream": True,
            "keep_alive": -1,  # Keep model loaded indefinitely
            # No "format": "json" - we want <think>...</think> then JSON
        }
        
        logger.debug(f"Calling Ollama (streaming): {self.model}")
        
        full_response = ""
        in_think_block = False
        
        async with self.client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    token = data.get("message", {}).get("content", "")
                    if token:
                        full_response += token
                        
                        # Track think block state
                        if "<think>" in full_response and not in_think_block:
                            in_think_block = True
                        if "</think>" in full_response and in_think_block:
                            in_think_block = False
                        
                        yield token, in_think_block, full_response
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue
        
        # Final yield with complete response (in_think_block is False at end)
        if full_response:
            yield "", False, full_response
    
    async def generate_next_step_streaming(
        self,
        task: str,
        history: List[StepResult],
        memory_context: List[Dict[str, Any]],
        workspace_context: Optional[WorkspaceContext] = None,
        workspace_state: Optional[WorkspaceState] = None,
        status_callback: Optional[Callable[[str], None]] = None,
    ):
        """
        Generate next step with streaming - yields (token, Step|None) tuples.
        
        During streaming: yields (token, None) for each token
        At completion: yields ("", Step) with the final parsed step
        
        Args:
            status_callback: Optional callback for model loading status updates
        """
        # Use external state if provided
        if workspace_state is None:
            workspace_state = get_workspace_state()
        
        # Build context (same as non-streaming version)
        context_parts = []
        
        state_context = workspace_state.format_for_prompt()
        if state_context:
            context_parts.append(state_context)
        
        if workspace_context:
            context_parts.append(
                f"Workspace: {workspace_context.cwd}\n"
                f"Permissions: write={workspace_context.allow_file_write}, "
                f"shell={workspace_context.allow_shell_commands}"
            )
        
        if workspace_state.user_info:
            user_info_text = "\n".join(f"  {k}: {v}" for k, v in workspace_state.user_info.items())
            context_parts.append(f"User info (use this, don't guess):\n{user_info_text}")
        
        if memory_context:
            patterns = "\n".join([
                f"- {p.get('description', 'Similar task')}: {p.get('approach', '')}"
                for p in memory_context[:3]
            ])
            context_parts.append(f"Relevant patterns from memory:\n{patterns}")
        
        # Guardrail check
        if len(workspace_state.completed_steps) >= 15:
            logger.warning(f"GUARDRAIL: {len(workspace_state.completed_steps)} steps - forcing completion")
            recent_edits = sum(1 for s in workspace_state.completed_steps[-5:] 
                             if s.tool in ("write_file", "insert_in_file", "replace_in_file", "append_to_file")
                             and s.success)
            if recent_edits == 0:
                yield "", Step(
                    step_id="guardrail_complete",
                    tool="complete",
                    params={"error": "Too many steps without progress"},
                    reasoning="Forced completion after 15 steps without recent edits",
                )
                return
        
        context = "\n\n".join(context_parts)
        user_message = f"Task: {task}"
        if context:
            user_message = f"{context}\n\n{user_message}"
        
        logger.debug(f"Prompt size: {len(user_message)} chars")
        
        # Stream from Ollama using ThinkingStreamParser
        full_response = ""
        parser = ThinkingStreamParser()
        
        try:
            # Use status-aware streaming if callback provided
            if status_callback:
                stream = self.stream_with_status(user_message, status_callback)
            else:
                stream = self._call_ollama_streaming(user_message)
            
            async for token, in_think_block, accumulated in stream:
                full_response = accumulated
                
                # Feed token to parser - it handles tag boundaries correctly
                content_to_yield = parser.feed(token)
                if content_to_yield:
                    yield content_to_yield, None  # Yield clean thinking content
            
            # Parse final response (extracts JSON after </think>)
            step = self._parse_response(full_response, task)
            
            # Apply guardrails (same as non-streaming)
            step = self._apply_guardrails(step, workspace_state)
            
            yield "", step  # Final yield with parsed step
            
        except Exception as e:
            logger.error(f"Streaming reasoning error: {e}")
            yield "", Step(
                step_id="error_fallback",
                tool="complete",
                params={"error": str(e)},
                reasoning=f"Error during reasoning: {e}",
            )
    
    def _apply_guardrails(self, step: Step, workspace_state: WorkspaceState) -> Step:
        """Apply guardrails to a parsed step. Returns corrected step if needed."""
        # GUARDRAIL: Detect repeated replace_in_file failures
        if step.tool == "replace_in_file":
            path = step.params.get("path", "")
            recent_failures = sum(
                1 for s in workspace_state.completed_steps[-5:]
                if s.tool == "replace_in_file" 
                and s.params.get("path") == path
                and not s.success
            )
            if recent_failures >= 2:
                logger.warning(f"GUARDRAIL: {recent_failures} replace failures on {path}")
                return Step(
                    step_id="guardrail_use_insert",
                    tool="insert_in_file",
                    params={
                        "path": path,
                        "position": "start",
                        "text": step.params.get("new_text", ""),
                    },
                    reasoning=f"Auto-corrected: replace_in_file failed {recent_failures}x",
                )
        
        # GUARDRAIL: Prevent re-reading already read files
        if step.tool == "read_file":
            path = step.params.get("path", "")
            if path and path in workspace_state.read_files:
                logger.warning(f"GUARDRAIL: Blocking re-read of '{path}'")
                return Step(
                    step_id="guardrail_no_reread",
                    tool="complete",
                    params={"error": f"Already read {path}. Move to editing or complete."},
                    reasoning=f"Blocked re-read of already-read file: {path}",
                )
        
        # GUARDRAIL: Validate paths exist in state
        if step.tool in ("read_file", "write_file", "insert_in_file", "replace_in_file", "append_to_file"):
            path = step.params.get("path", "")
            if path and workspace_state.files and path not in workspace_state.files:
                if step.tool != "write_file":
                    logger.warning(f"GUARDRAIL: Path '{path}' not in scanned files")
                    similar = [f for f in workspace_state.files if f.endswith(path) or path in f]
                    if similar:
                        correct_path = similar[0]
                        logger.info(f"GUARDRAIL: Correcting path to '{correct_path}'")
                        step.params["path"] = correct_path
        
        return step
    
    def _parse_response(self, response: str, task: str) -> Step:
        """Parse LLM response into a Step object.
        
        Response format is now:
        <think>reasoning here</think>
        {"tool": "...", "params": {...}, "note": "..."}
        """
        import uuid
        
        # Extract thinking content (for logging/reasoning field)
        thinking = ""
        if "<think>" in response and "</think>" in response:
            think_start = response.index("<think>") + len("<think>")
            think_end = response.index("</think>")
            thinking = response[think_start:think_end].strip()
        
        # Extract JSON after </think> (or try whole response if no tags)
        json_str = response
        if "</think>" in response:
            json_str = response.split("</think>", 1)[1].strip()
        
        try:
            # Try to parse as JSON
            data = json.loads(json_str)
            
            # Generate step ID
            step_id = f"step_{uuid.uuid4().hex[:8]}"
            
            # Use thinking as reasoning, fall back to note
            note = data.get("note", "") or data.get("reasoning", "")
            reasoning = thinking if thinking else note
            
            return Step(
                step_id=step_id,
                tool=data.get("tool", "unknown"),
                params=data.get("params", {}),
                reasoning=reasoning,
                batch_id=data.get("batch_id"),
            )
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw response: {response[:500]}")
            logger.debug(f"JSON portion: {json_str[:500]}")
            
            # Return error step
            return Step(
                step_id=f"parse_error_{uuid.uuid4().hex[:8]}",
                tool="complete",
                params={"error": "Failed to parse LLM response"},
                reasoning=f"Parse error: {e}",
            )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
