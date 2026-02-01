"""
Reasoning Engine - LLM Coordination for Step Generation

Uses Ollama to generate structured reasoning steps from user intents.
Parses LLM output into validated Step objects.

Architecture:
- State is maintained EXTERNALLY by SessionState (not by the LLM)
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
from services.session_state import SessionState, get_session_state


logger = logging.getLogger("orchestrator.reasoning")

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "aj-deepseek-r1-32b")


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


SYSTEM_PROMPT = """
You are AJ, an AI assistant for infrastructure tasks.
FORMAT: {"tool": "name", "params": {...}, "reasoning": "why"}

═══════════════════════════════════════════════════════════════════════════════
🚨 ABSOLUTE RULES - VIOLATION = SYSTEM FAILURE
═══════════════════════════════════════════════════════════════════════════════

1. NEVER FABRICATE OUTPUT
   - You CANNOT see command results until you call a tool
   - EVERY piece of data must come from a tool call
   - If you write "ping output:" without calling remote_execute first = FABRICATION
   - If you write times like "2ms, 3ms, 5ms" without actual commands = FABRICATION
   - There are NO tools called "ping", "disk_iops", "memory_usage" - ONLY the 5 listed below

2. ONLY THESE 5 TOOLS EXIST:
   - list_agents: Returns agent list. NOTHING ELSE.
   - remote_execute: {"agent_id": "X", "command": "..."} - Runs command, returns output
   - remote_execute_all: {"command": "..."} - Runs on ALL agents
   - think: {"thought": "..."} - Planning only
   - complete: {"answer": "..."} - Final response

3. TO GET DATA, YOU MUST CALL A TOOL
   - Want ping times? Call remote_execute with Test-Connection command
   - Want disk info? Call remote_execute with Get-PSDrive command  
   - Want memory? Call remote_execute with Get-Process or systeminfo command
   - NO SHORTCUTS. NO IMAGINED RESULTS.

4. ANSWER ONLY WHAT WAS ASKED
   - User asks about ping → respond about ping only
   - Do NOT invent follow-up questions
   - Do NOT answer questions that weren't asked

═══════════════════════════════════════════════════════════════════════════════
WORKFLOW
═══════════════════════════════════════════════════════════════════════════════

Step 1: Understand what user wants
Step 2: Call the minimum tools needed (usually list_agents first)
Step 3: Use ACTUAL tool output to answer
Step 4: Call complete with your answer
Step 5: STOP

PLATFORM COMMANDS (all current agents are Windows):
- Ping: Test-Connection -ComputerName TARGET -Count 4
- Disk: Get-PSDrive C
- Memory: Get-Process | Measure-Object WorkingSet -Sum
- Time: Get-Date

EXAMPLE - "Ping domain01 from domain02":
1. {"tool": "remote_execute", "params": {"agent_id": "domain02", "command": "Test-Connection -ComputerName domain01 -Count 4"}}
2. [WAIT FOR ACTUAL OUTPUT]
3. {"tool": "complete", "params": {"answer": "[use the REAL output from step 1]"}}

WRONG - FABRICATION:
- Writing "ping output: 2ms, 3ms, 5ms" without calling remote_execute = HALLUCINATION
- Inventing tools like "disk_iops" or "memory_usage" = HALLUCINATION
"""

class ReasoningEngine:
    """
    LLM-powered reasoning engine for step generation.
    
    Architecture:
    - State is maintained externally by SessionState
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
            "aj-deepseek-r1-32b": 18.5,  # Fine-tuned DeepSeek-R1-Distill-Qwen-32B Q4_K_M - primary model
            "aj-deepseek-r1-32b:q8": 32.5,  # Q8_0 quantization - higher quality
            "qwen2.5-aj:32b": 20.0,  # Legacy fine-tuned Qwen2.5-32B
            "qwen2.5-aj:32b-4k": 20.0,
            "qwen2.5-aj:32b-8k": 20.0,
            "nous-hermes2:34b": 22.0,
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
        self._model_preloaded = False
    
    def set_model(self, model: str) -> None:
        """
        Set the model to use for reasoning.
        
        This allows dynamic model selection based on Open-WebUI user choice.
        If the model changes, reset the preloaded flag to force a warmup.
        """
        if model and model != self.model:
            logger.info(f"Switching model: {self.model} -> {model}")
            self.model = model
            self._model_preloaded = False  # Force warmup with new model
    
    async def warmup_model(self) -> bool:
        """
        Pre-load the model into Ollama's memory to prevent cold start delays.
        
        This is called at the START of task execution to ensure the model is
        already loaded and will stay loaded with KEEP_ALIVE=24h setting.
        
        Returns:
            True if successful, False if failed (but doesn't block execution)
        """
        if self._model_preloaded:
            return True  # Already warmed up in this session
        
        try:
            logger.info(f"Pre-loading model: {self.model}")
            
            # Send a simple completion request that won't generate much output
            # This loads the model into memory without doing real work
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": "x",  # Minimal prompt
                "stream": False,
                "keep_alive": "24h",  # Ensure it stays loaded
            }
            
            response = await self.client.post(url, json=payload, timeout=300.0)
            response.raise_for_status()
            
            self._model_preloaded = True
            logger.info(f"Model pre-loaded successfully: {self.model}")
            return True
            
        except Exception as e:
            logger.warning(f"Model pre-load failed (non-blocking): {e}")
            return False  # Non-fatal - execution will continue
    
    def _estimate_load_time(self) -> int:
        """Estimate cold load time in seconds based on model size."""
        # Find matching model size
        for model_prefix, size_gb in self._model_sizes.items():
            if self.model.startswith(model_prefix):
                return max(5, int(size_gb / self._load_speed_gb_per_sec))
        # Default estimate for unknown models
        return 15
    
    async def classify_intent(self, task: str) -> dict:
        """
        Classify user intent BEFORE the OODA loop to determine if planning is needed.
        
        Intent Types:
        - "conversational": Questions about concepts, explanations, how things work
          → Route directly to memory + LLM, skip OODA planning
        - "task": File operations, remote execution, workspace changes
          → Full OODA loop with planning
        
        Returns:
            dict with:
            - intent: "conversational" or "task"
            - confidence: float 0-1
            - reason: brief explanation
        """
        # Always use LLM for intent classification - pattern matching is too brittle
        try:
            url = f"{self.base_url}/api/chat"
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": """Classify user intent as either:
- "task": Requires file operations, code execution, workspace changes, remote machine access, finding/listing files, checking disk space, running commands on agents
- "conversational": Questions about concepts, explanations, definitions, chit-chat, asking how things work in general

Examples:
- "What are the largest files on my machine?" → task (requires scanning files)
- "What is a file system?" → conversational (conceptual question)
- "List files in C:\\Code" → task (requires file listing)
- "How does FunnelCloud work?" → conversational (explanation)
- "Find agents" → task (requires discovery)
- "What can you do?" → conversational (capabilities question)

Respond with ONLY one word: task OR conversational"""},
                    {"role": "user", "content": task},
                ],
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 10},  # Very constrained
            }
            
            response = await self.client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            
            content = response.json().get("message", {}).get("content", "").strip().lower()
            logger.info(f"Intent LLM response: {content}")
            
            if "task" in content:
                return {"intent": "task", "confidence": 0.85, "reason": "LLM classification"}
            elif "conversational" in content:
                return {"intent": "conversational", "confidence": 0.85, "reason": "LLM classification"}
            else:
                # Default to task for safety (won't miss important operations)
                logger.warning(f"Ambiguous intent response: {content}, defaulting to task")
                return {"intent": "task", "confidence": 0.5, "reason": "Ambiguous, defaulting to task"}
                
        except Exception as e:
            logger.warning(f"Intent classification LLM call failed: {e}")
            # Default to task on error (safer)
            return {"intent": "task", "confidence": 0.5, "reason": f"Classification failed: {e}"}
    
    async def answer_conversational(self, task: str, memory_context: List[dict] = None) -> str:
        """
        Answer a conversational question directly without OODA planning.
        
        Uses memory context and LLM to provide a direct response.
        """
        # Build context from memory
        context_parts = []
        if memory_context:
            for item in memory_context[:5]:
                facts = item.get('facts')
                if facts and isinstance(facts, dict):
                    for fact_type, fact_value in facts.items():
                        context_parts.append(f"- {fact_type}: {fact_value}")
                else:
                    text = item.get('user_text', '') or item.get('text', '')
                    if text:
                        context_parts.append(f"- {text}")
        
        system_prompt = """You are AJ, a helpful AI assistant. Answer the user's question directly and concisely.

RESPONSE FORMAT:
- Respond in clean Markdown - NEVER output raw JSON objects or action wrappers
- Use fenced code blocks (```) for code, commands, or structured output
- Use backticks for `file paths`, `IP addresses`, `hostnames`, `commands`
- Write natural prose for explanations

If you have relevant context from memory, use it to personalize your response.
If you don't know something, say so honestly.
Keep responses focused and informative."""
        
        if context_parts:
            system_prompt += f"\n\nRelevant context from memory:\n" + "\n".join(context_parts)
        
        try:
            url = f"{self.base_url}/api/chat"
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task},
                ],
                "stream": False,
                "options": {"temperature": 0.7},
            }
            
            response = await self.client.post(url, json=payload, timeout=60.0)
            response.raise_for_status()
            
            return response.json().get("message", {}).get("content", "I'm not sure how to answer that.")
            
        except Exception as e:
            logger.error(f"Conversational answer failed: {e}")
            return f"I encountered an error trying to answer: {e}"

    async def generate_task_plan(self, task: str) -> List[str]:
        """
        Generate a task plan (numbered list of steps) before execution begins.
        
        This runs ONCE at task start to:
        1. Show user what will happen
        2. Give LLM a script to follow
        3. Enable progress tracking
        
        Returns:
            List of step descriptions (strings)
        """
        planning_prompt = """
You are a task planner that helps AI assistants break down complex tasks into clear, sequential steps.

OUTPUT FORMAT - CRITICAL:
1. First, briefly explain your strategy (1-2 sentences)
2. Then output a SHORT numbered list (1. 2. 3. etc.) of concrete steps
3. Each step should be specific and actionable

STRATEGY TIPS:
- If task mentions multiple targets (C: and S:), list them as separate steps
- For remote/host operations, include "verify agent available" as first step  
- Break complex operations into atomic steps (read, process, verify, report)
- End plan with a final verification or summary step

MULTI-AGENT PATTERN - CRITICAL:
When user says "each agent", "all agents", "every machine", etc:
- List agents first
- Then create ONE step PER AGENT for the operation
- Use placeholders like "agent1", "agent2" etc. or "for each agent"

EXAMPLES:

User: "What are the largest files on my C: drive?"
1. Verify FunnelCloud agent is available
2. Scan C: drive for file sizes
3. Report top 10 largest files

User: "Ask each agent for disk space"
1. Query agent registry
2. For each agent: query disk space
3. Report results per agent

User: "Check folder sizes on all my machines"
1. List available agents
2. For each agent: scan for largest folders
3. Summarize by machine

User: "Scan C: and S: for large folders"
1. Verify FunnelCloud agent is available
2. Scan C: drive for folder sizes
3. Scan S: drive for folder sizes
4. Report largest folders from both drives

User: "What's in this workspace?"
1. Scan workspace directory
2. Summarize project structure

Now create a plan for:
"""
        
        try:
            url = f"{self.base_url}/api/chat"
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a task planner. Output ONLY a numbered list (1. 2. 3.) with 2-5 steps. NO JSON. NO explanations. Just numbered steps."},
                    {"role": "user", "content": planning_prompt + task},
                ],
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 256},  # Low temp for consistent planning, limited output
            }
            
            response = await self.client.post(url, json=payload, timeout=30.0)
            response.raise_for_status()
            
            content = response.json().get("message", {}).get("content", "")
            logger.debug(f"Task plan raw response: {content[:500]}")
            
            # Parse numbered list
            steps = []
            
            # First try: numbered list format (1. Step or - Step)
            for line in content.split("\n"):
                line = line.strip()
                # Match lines starting with number + period/paren
                if line and (line[0].isdigit() or line.startswith("-")):
                    # Strip the number prefix (uses module-level re import)
                    cleaned = re.sub(r'^[\d]+[.\)]\s*', '', line)
                    cleaned = re.sub(r'^[-*]\s*', '', cleaned)
                    if cleaned:
                        steps.append(cleaned)
            
            # Second try: JSON format (fine-tuned model may output JSON)
            if not steps:
                try:
                    # Try to parse as JSON - model might output structured format
                    json_data = json.loads(content)
                    if isinstance(json_data, dict):
                        # Check for steps/plan array
                        if "steps" in json_data and isinstance(json_data["steps"], list):
                            steps = [str(s) for s in json_data["steps"]]
                        elif "plan" in json_data and isinstance(json_data["plan"], list):
                            steps = [str(s) for s in json_data["plan"]]
                        # Check for action/response format (single-step)
                        elif "action" in json_data:
                            action = json_data.get("action", "")
                            if action and action != "casual":
                                steps = [f"{action}: {json_data.get('response', 'Execute task')[:100]}"]
                    elif isinstance(json_data, list):
                        # Direct array of steps
                        steps = [str(s) for s in json_data if s]
                except (json.JSONDecodeError, ValueError):
                    pass  # Not JSON, stick with empty steps
            
            # DEDUPE: Remove duplicate steps (model sometimes outputs plan twice)
            seen = set()
            unique_steps = []
            for step in steps:
                step_key = step.lower().strip()
                if step_key not in seen:
                    seen.add(step_key)
                    unique_steps.append(step)
            steps = unique_steps
            
            logger.info(f"Generated task plan with {len(steps)} steps: {steps}")
            return steps if steps else ["Execute task"]
            
        except Exception as e:
            logger.warning(f"Task planning failed: {e}")
            return ["Execute task"]  # Fallback to single generic step
    
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
        
        **Important**: Also yields empty tokens with status updates to keep
        the async loop active even while Ollama is loading the model.
        """
        first_token_received = asyncio.Event()
        status_task = None
        start_time = asyncio.get_event_loop().time()
        estimated_total = self._estimate_load_time()
        
        async def status_monitor():
            """Background task to emit status while waiting for first token."""
            # NO initial delay - start checking immediately
            model_was_loaded = False
            last_status = ""
            check_interval = 0.3  # Check every 300ms for smooth updates
            
            while not first_token_received.is_set():
                elapsed = asyncio.get_event_loop().time() - start_time
                status = await self.check_model_status()
                
                if status["loaded"]:
                    if not model_was_loaded:
                        model_was_loaded = True
                        new_status = "🧠 Reasoning..."
                    else:
                        # Model loaded, waiting for generation - update every 5s
                        if elapsed < 10:
                            new_status = "🧠 Reasoning..."
                        else:
                            new_status = f"🧠 Reasoning... ({int(elapsed)}s)"
                else:
                    # Model loading - show progress with time estimate
                    remaining = max(1, estimated_total - elapsed)
                    percent = min(95, int((elapsed / estimated_total) * 100))
                    
                    if elapsed < estimated_total:
                        new_status = f"⏳ Loading model... {percent}%"
                    else:
                        # Taking longer than expected
                        new_status = f"⏳ Loading model... ({elapsed:.0f}s)"
                
                # Only emit if status changed (reduces spam)
                if new_status != last_status:
                    status_callback(new_status)
                    last_status = new_status
                
                try:
                    await asyncio.wait_for(
                        first_token_received.wait(),
                        timeout=check_interval  # Check every 300ms
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
        session_state: Optional[SessionState] = None,
    ) -> Step:
        """
        Generate the next step for a task using LLM reasoning.
        
        Args:
            task: User's task description
            history: Previous step results (for backward compat, prefer session_state)
            memory_context: Relevant patterns from memory
            workspace_context: Current workspace settings
            session_state: External state (ground truth from actual tool outputs)
            
        Returns:
            Step object with tool, params, and reasoning
        """
        # Use external state if provided, otherwise fall back to old approach
        if session_state is None:
            session_state = get_session_state()
        
        context_parts = []
        
        # 1. Inject external state (the key change - LLM doesn't maintain this)
        state_context = session_state.format_for_prompt()
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
        if session_state.user_info:
            user_info_text = "\n".join(f"  {k}: {v}" for k, v in session_state.user_info.items())
            context_parts.append(f"User info (use this, don't guess):\n{user_info_text}")
        
        # 4. Memory patterns (optional)
        if memory_context:
            patterns = "\n".join([
                f"- {p.get('description', 'Similar task')}: {p.get('approach', '')}"
                for p in memory_context[:3]
            ])
            context_parts.append(f"Relevant patterns from memory:\n{patterns}")
        
        # 5. GUARDRAIL: If too many steps without progress, force completion
        if len(session_state.completed_steps) >= 15:
            logger.warning(f"GUARDRAIL: {len(session_state.completed_steps)} steps - forcing completion check")
            # Check if we're making progress
            recent_edits = sum(1 for s in session_state.completed_steps[-5:] 
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
            step = self._apply_guardrails(step, session_state)
            
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
        
        # JSON Schema for structured output - forces exact format
        # MUST match SYSTEM_PROMPT tools exactly (remote_execute only)
        tool_call_schema = {
            "type": "object",
            "properties": {
                "tool": {
                    "type": "string",
                    "description": "Tool to call",
                    "enum": [
                        "remote_execute",     # Execute on ONE specific FunnelCloud agent
                        "remote_execute_all", # Execute on ALL discovered agents
                        "list_agents",        # Discover available FunnelCloud agents
                        "think",              # Reason about the problem
                        "complete",           # Task done or error
                    ]
                },
                "params": {
                    "type": "object",
                    "description": "Parameters for the tool"
                },
                "note": {
                    "type": "string",
                    "description": "Brief status note"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Why this tool is being called"
                }
            },
            "required": ["tool", "params"]
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "keep_alive": -1,  # Keep model loaded indefinitely
            "format": tool_call_schema,  # Structured output with JSON schema
            "options": {
                "temperature": 0,  # Deterministic - force format compliance
                "top_p": 0.1,  # Very narrow sampling to avoid hallucinations
                "top_k": 5,    # Only consider top 5 tokens
            }
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
        
        # JSON Schema for structured output - forces exact format
        # MUST match SYSTEM_PROMPT tools exactly (remote_execute only)
        tool_call_schema = {
            "type": "object",
            "properties": {
                "tool": {
                    "type": "string",
                    "description": "Tool to call",
                    "enum": [
                        "remote_execute",     # Execute on ONE specific FunnelCloud agent
                        "remote_execute_all", # Execute on ALL discovered agents
                        "list_agents",        # Discover available FunnelCloud agents
                        "think",              # Reason about the problem
                        "complete",           # Task done or error
                    ]
                },
                "params": {
                    "type": "object",
                    "description": "Parameters for the tool"
                },
                "note": {
                    "type": "string",
                    "description": "Brief status note"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Why this tool is being called"
                }
            },
            "required": ["tool", "params"]
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "stream": True,
            "keep_alive": -1,  # Keep model loaded indefinitely
            "format": tool_call_schema,  # Structured output with JSON schema
            "options": {
                "temperature": 0,  # Deterministic - force format compliance
                "top_p": 0.1,  # Very narrow sampling to avoid hallucinations
                "top_k": 5,    # Only consider top 5 tokens
            }
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
        session_state: Optional[SessionState] = None,
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
        if session_state is None:
            session_state = get_session_state()
        
        # Build context (same as non-streaming version)
        context_parts = []
        
        state_context = session_state.format_for_prompt()
        if state_context:
            context_parts.append(state_context)
        
        if workspace_context:
            context_parts.append(
                f"Workspace: {workspace_context.cwd}\n"
                f"Permissions: write={workspace_context.allow_file_write}, "
                f"shell={workspace_context.allow_shell_commands}"
            )
        
        if session_state.user_info:
            user_info_text = "\n".join(f"  {k}: {v}" for k, v in session_state.user_info.items())
            context_parts.append(f"User info (use this, don't guess):\n{user_info_text}")
        
        if memory_context:
            patterns = "\n".join([
                f"- {p.get('description', 'Similar task')}: {p.get('approach', '')}"
                for p in memory_context[:3]
            ])
            context_parts.append(f"Relevant patterns from memory:\n{patterns}")
        
        # Guardrail check
        if len(session_state.completed_steps) >= 15:
            logger.warning(f"GUARDRAIL: {len(session_state.completed_steps)} steps - forcing completion")
            recent_edits = sum(1 for s in session_state.completed_steps[-5:] 
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
            step = self._apply_guardrails(step, session_state)
            
            yield "", step  # Final yield with parsed step
            
        except Exception as e:
            logger.error(f"Streaming reasoning error: {e}")
            yield "", Step(
                step_id="error_fallback",
                tool="complete",
                params={"error": str(e)},
                reasoning=f"Error during reasoning: {e}",
            )
    
    def _apply_guardrails(self, step: Step, session_state: SessionState) -> Step:
        """Apply guardrails to a parsed step. Returns corrected step if needed."""
        
        # ⛔ GUARDRAIL: Prevent calling list_agents twice
        # If already verified, skip redundant call by completing with the cached info
        if step.tool == "list_agents" and session_state.agents_verified:
            logger.warning("GUARDRAIL: list_agents already called - returning cached agents")
            # Return the cached agent info as a completed step instead of "none"
            agent_list = ', '.join(session_state.discovered_agents) if session_state.discovered_agents else "none found"
            return Step(
                step_id="guardrail_cached_agents",
                tool="complete",
                params={"answer": f"Agents already discovered: {agent_list}"},
                reasoning="Returned cached agent list - already verified this session",
            )
        
        # ⛔ CRITICAL GUARDRAIL: remote_execute requires verified agents
        # If model tries remote_execute without agents, block it
        if step.tool in ("remote_bash", "remote_execute"):  # Support both old and new names
            agent_id = step.params.get("agent_id", "") or step.params.get("agent", "")
            # Model uses various param names: 'command', 'cmd', 'commands' (plural), 'code', etc.
            command = step.params.get("command", "") or step.params.get("cmd", "") or step.params.get("commands", "")
            
            if isinstance(command, list):
                command = " ".join(command) if command else ""  # Handle ["touch", "file.txt"] or ["touch file.txt"]
            command = str(command).strip()
            
            if not session_state.discovered_agents:
                logger.error(f"GUARDRAIL BLOCK: remote_execute without agent discovery")
                return Step(
                    step_id="guardrail_require_list_agents",
                    tool="complete",
                    params={"error": "Cannot execute remote commands - no FunnelCloud agents discovered. Call list_agents first to discover available agents."},
                    reasoning="Blocked remote_execute - agent verification required",
                )
            if agent_id and agent_id not in session_state.discovered_agents:
                logger.error(f"GUARDRAIL BLOCK: remote_execute on unknown agent '{agent_id}'")
                available = ", ".join(session_state.discovered_agents)
                return Step(
                    step_id="guardrail_unknown_agent",
                    tool="complete",
                    params={"error": f"Cannot execute on '{agent_id}' - not running. Available: {available}"},
                    reasoning=f"Blocked remote_execute - target agent '{agent_id}' unavailable",
                )
            
            # ⛔ GUARDRAIL: Validate PowerShell syntax before executing
            # Catch common model mistakes that cause massive error output
            if command:
                syntax_errors = self._validate_powershell_syntax(command)
                if syntax_errors:
                    logger.warning(f"GUARDRAIL: Fixing PowerShell syntax errors: {syntax_errors}")
                    fixed_command = self._fix_powershell_command(command, syntax_errors)
                    if fixed_command != command:
                        logger.info(f"GUARDRAIL: Fixed command: {fixed_command[:100]}")
                        return Step(
                            step_id=step.step_id,
                            tool="remote_execute",
                            params={**step.params, "command": fixed_command},
                            reasoning=f"Fixed PowerShell syntax: {syntax_errors[0]}"
                        )
        
        # ⛔ CRITICAL GUARDRAIL: Force remote_execute when agents are discovered
        # If we found agents via list_agents, the model MUST use remote_execute for subsequent operations
        # This catches the common failure where model uses scan_workspace/execute_shell instead
        logger.debug(f"Guardrail check: discovered_agents={session_state.discovered_agents}, tool={step.tool}")
        if session_state.discovered_agents and step.tool in ("scan_workspace", "execute_shell"):
            # Check if we just did list_agents in the last few steps
            recent_steps = session_state.completed_steps[-3:]
            did_list_agents = any(s.tool == "list_agents" for s in recent_steps)
            logger.info(f"Guardrail: agents={session_state.discovered_agents}, recent_tools={[s.tool for s in recent_steps]}, did_list_agents={did_list_agents}")
            
            if did_list_agents:
                # CRITICAL: Extract target from user request - do NOT blindly use first agent
                user_request = session_state.ledger.user_requests[-1] if session_state.ledger.user_requests else ""
                agent_id = self._extract_target_agent(user_request, session_state.discovered_agents)
                
                if not agent_id:
                    # No match found AND user specified a target - block instead of defaulting
                    # Check if user mentioned any specific hostname/target
                    # NOTE: Uses module-level 're' import (line 14)
                    target_patterns = re.findall(r"['\"]([^'\"]+)['\"]|(?:on|reboot|restart|shutdown|check)\s+(\S+)", user_request.lower())
                    user_specified_target = any(target_patterns)
                    
                    if user_specified_target:
                        logger.error(f"GUARDRAIL BLOCK: User specified target not found in discovered agents: {user_request}")
                        return Step(
                            step_id="guardrail_target_mismatch",
                            tool="complete",
                            params={"error": f"Target not found. User request mentions a specific target that doesn't match any discovered agent. Available agents: {', '.join(session_state.discovered_agents)}"},
                            reasoning="Blocked - user-specified target not found in discovered agents",
                        )
                    else:
                        # Generic request like "check my machine" - OK to use first agent
                        agent_id = session_state.discovered_agents[0]
                        logger.info(f"GUARDRAIL: Generic request, using first agent: {agent_id}")
                
                logger.warning(f"GUARDRAIL: Redirecting {step.tool} to remote_execute on {agent_id} (matched from user request)")
                
                # Convert the workspace tool call to remote_execute
                if step.tool == "scan_workspace":
                    # Convert scan_workspace to Get-ChildItem on remote - keep it simple!
                    path = step.params.get("path", "C:\\")
                    return Step(
                        step_id="guardrail_force_remote",
                        tool="remote_execute",
                        params={
                            "agent_id": agent_id,
                            "command": f"Get-ChildItem -Path '{path}' -File"
                        },
                        reasoning=f"Redirected scan_workspace to remote_execute on {agent_id} - use discovered agent",
                    )
                elif step.tool == "execute_shell":
                    # Convert execute_shell to remote_execute
                    cmd = step.params.get("cmd", "") or step.params.get("command", "")
                    return Step(
                        step_id="guardrail_force_remote",
                        tool="remote_execute",
                        params={
                            "agent_id": agent_id,
                            "command": cmd
                        },
                        reasoning=f"Redirected execute_shell to remote_execute on {agent_id} - use discovered agent",
                    )
        
        # GUARDRAIL: Prevent lazy completion after list_agents
        # If we just discovered agents and LLM tries to complete without doing actual work,
        # reject it - the task likely requires remote_execute
        if step.tool == "complete":
            recent_steps = session_state.completed_steps[-3:]
            last_was_list_agents = any(s.tool == "list_agents" for s in recent_steps)
            did_remote_work = any(s.tool == "remote_execute" for s in session_state.completed_steps)
            
            # CRITICAL: If list_agents found NO agents, force completion with clear error message
            # This prevents the model from hallucinating fake results
            if last_was_list_agents and not session_state.discovered_agents:
                answer_text = step.params.get("answer", "")
                # Detect if model is trying to provide fake results (hallucination)
                # Include both Unix and Windows path patterns
                hallucination_indicators = [
                    "here are the",
                    "top 10",
                    "largest files",
                    "scanned",
                    "/home/",
                    "/user/",
                    ".bin",
                    ".tar",
                    ".iso",
                    # Windows-specific hallucination patterns
                    "explorer.exe",
                    "notepad.exe",
                    "system32",
                    "c:\\windows",
                    "c:\\program",
                    "c:\\users",
                    ".dll",
                    # Made-up file size patterns
                    " kb",
                    " mb",
                    " gb",
                    " bytes",
                    # Directory listing patterns
                    "directory listing",
                    "file listing",
                    "| name |",
                    "filename",
                ]
                is_hallucinating = any(ind in answer_text.lower() for ind in hallucination_indicators)
                
                # Also check for Windows path regex patterns (C:\Something\file.ext)
                if not is_hallucinating and answer_text:
                    windows_path_pattern = re.search(r'[A-Z]:\\[A-Za-z0-9_\\]+\.[a-z]{2,4}', answer_text)
                    if windows_path_pattern:
                        is_hallucinating = True
                        logger.warning(f"GUARDRAIL: Detected Windows path hallucination: {windows_path_pattern.group()}")
                
                if is_hallucinating:
                    logger.warning(f"GUARDRAIL: Blocking hallucinated results - no agents available")
                    return Step(
                        step_id="guardrail_no_hallucination",
                        tool="complete",
                        params={"error": "No FunnelCloud agents are available. I cannot access remote machines without an agent running. Please start the FunnelCloud agent on the target machine and try again."},
                        reasoning="Blocked hallucination - list_agents returned empty but model tried to provide fake results",
                    )
                
                # Even if not obviously hallucinating, if no agents and trying to complete with an "answer"
                # (not an "error"), it's suspicious - force a proper error response
                if answer_text and len(answer_text) > 50:
                    logger.warning(f"GUARDRAIL: Blocking completion with answer when no agents - should be error")
                    return Step(
                        step_id="guardrail_force_error_no_agents",
                        tool="complete",
                        params={"error": "No FunnelCloud agents are available. I cannot access your remote machine to perform this task. Please ensure the FunnelCloud agent is running on the target machine."},
                        reasoning="Forced error completion - no agents available but model tried to provide answer",
                    )
        
        # GUARDRAIL: If last remote_bash succeeded with SAME params, don't retry
        # This catches looping behavior where the model keeps calling the same command
        if step.tool == "remote_bash":
            new_agent = step.params.get("agent_id", "")
            new_cmd = step.params.get("command", "")
            
            # Check for exact duplicate (same agent AND same command)
            duplicate_count = 0
            for prev_step in session_state.completed_steps[-10:]:
                if prev_step.tool != "remote_bash":
                    continue
                
                prev_agent = prev_step.params.get("agent_id", "")
                prev_cmd = prev_step.params.get("command", "")
                
                if prev_agent == new_agent and prev_cmd == new_cmd:
                    duplicate_count += 1
            
            if duplicate_count >= 1:
                logger.warning(f"GUARDRAIL: Blocking duplicate remote_bash - same agent+command called {duplicate_count}x: {new_agent}")
                return Step(
                    step_id="guardrail_no_retry_remote_bash",
                    tool="complete",
                    params={"answer": "I already executed this command. See the output above."},
                    reasoning=f"Blocked retry of remote_bash - {new_agent} + {new_cmd[:30]} already executed",
                )
        
        # GUARDRAIL: If last remote_execute succeeded with SAME params, don't retry
        # This catches the "retry with better parameters" anti-pattern
        # BUT allows different commands (scanning C: then S:) OR different agents
        if step.tool == "remote_execute":
            # Handle various param names the model might use for agent
            new_agent = (step.params.get("agent_id") or step.params.get("agent") or 
                        step.params.get("agent_name") or step.params.get("agentName") or "")
            new_cmd = step.params.get("command", "")
            
            # Check for exact duplicate (same agent AND same command)
            for prev_step in session_state.completed_steps[-10:]:
                if prev_step.tool != "remote_execute" or not prev_step.success:
                    continue
                
                # Handle various param names
                prev_agent = (prev_step.params.get("agent_id") or prev_step.params.get("agent") or
                             prev_step.params.get("agent_name") or prev_step.params.get("agentName") or "")
                prev_cmd = prev_step.params.get("command", "")
                
                # Only block if BOTH agent AND command match exactly
                is_duplicate = (prev_agent == new_agent) and (prev_cmd == new_cmd)
                
                if is_duplicate:
                    logger.warning(f"GUARDRAIL: Blocking duplicate remote_execute - same agent+command: {new_agent}")
                    return Step(
                        step_id="guardrail_no_retry_remote",
                        tool="complete",
                        params={"answer": "I already retrieved the requested information. See the output above."},
                        reasoning=f"Blocked retry of remote_execute - agent {new_agent} already queried",
                    )
            
            # Allow: same command to DIFFERENT agent
            # Allow: different command to same agent (multi-step on one machine)
            logger.info(f"GUARDRAIL: Allowing remote_execute to {new_agent or 'default'} - not a duplicate")
        
        # GUARDRAIL: Detect tool repetition loops (same tool called 3+ times with SAME target)
        # For file operations, allow multiple calls to different paths
        # NOTE: remote_execute/remote_bash are exempt - they have their own smarter duplicate detection above
        if step.tool not in ("remote_execute", "remote_execute_all", "remote_bash", "remote_bash_all"):
            # For file tools, check if we're targeting the same path
            file_tools = {"write_file", "read_file", "replace_in_file", "insert_in_file", "append_to_file"}
            if step.tool in file_tools:
                current_path = step.params.get("path", "") or step.params.get("file_path", "")
                if current_path:
                    same_path_count = sum(
                        1 for s in session_state.completed_steps[-5:]
                        if s.tool == step.tool and 
                        (s.params.get("path", "") or s.params.get("file_path", "")) == current_path
                    )
                    if same_path_count >= 2:
                        logger.warning(f"GUARDRAIL: Loop detected - {step.tool} on same path {current_path} {same_path_count}x")
                        return Step(
                            step_id="guardrail_loop_break",
                            tool="complete",
                            params={"error": f"Loop detected: {step.tool} on {current_path} was already called {same_path_count} times"},
                            reasoning=f"Forced completion to break {step.tool} loop on same file",
                        )
            else:
                # For non-file tools, use simple count
                recent_tools = [s.tool for s in session_state.completed_steps[-5:]]
                if step.tool in recent_tools:
                    repeat_count = recent_tools.count(step.tool)
                    # Tools that should never be called twice
                    once_only_tools = {"list_agents", "scan_workspace", "dump_state"}
                    threshold = 1 if step.tool in once_only_tools else 2
                    
                    if repeat_count >= threshold:
                        logger.warning(f"GUARDRAIL: Loop detected - {step.tool} called {repeat_count}x in last 5 steps")
                        return Step(
                            step_id="guardrail_loop_break",
                            tool="complete",
                            params={"error": f"Loop detected: {step.tool} was already called {repeat_count} times"} if threshold > 1 else {},
                            reasoning=f"Forced completion to break {step.tool} loop",
                        )
        
        # GUARDRAIL: Prevent calling dump_state more than once
        if step.tool == "dump_state":
            dump_count = sum(1 for s in session_state.completed_steps if s.tool == "dump_state")
            if dump_count >= 1:
                logger.warning(f"GUARDRAIL: dump_state already called {dump_count}x")
                return Step(
                    step_id="guardrail_no_dump_repeat",
                    tool="complete",
                    params={},
                    reasoning="dump_state already executed - completing task",
                )
        
        # GUARDRAIL: Detect repeated replace_in_file failures
        if step.tool == "replace_in_file":
            path = step.params.get("path", "")
            recent_failures = sum(
                1 for s in session_state.completed_steps[-5:]
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
            path = step.params.get("path", "") or step.params.get("file_path", "")
            if path and path in session_state.read_files:
                logger.warning(f"GUARDRAIL: Blocking re-read of '{path}'")
                return Step(
                    step_id="guardrail_no_reread",
                    tool="complete",
                    params={"error": f"Already read {path}. Move to editing or complete."},
                    reasoning=f"Blocked re-read of already-read file: {path}",
                )
        
        # GUARDRAIL: Validate paths exist in state (for edit operations only)
        # NOTE: read_file should return actual errors, not be blocked by guardrails
        # NOTE: write_file can create new files, so don't block it
        if step.tool in ("insert_in_file", "replace_in_file", "append_to_file"):
            path = step.params.get("path", "") or step.params.get("file_path", "")
            if path and session_state.files and path not in session_state.files:
                logger.warning(f"GUARDRAIL: Path '{path}' not in scanned files for edit operation")
                similar = [f for f in session_state.files if f.endswith(path) or path in f]
                if similar:
                    correct_path = similar[0]
                    logger.info(f"GUARDRAIL: Correcting path to '{correct_path}'")
                    step.params["path"] = correct_path
        
        return step
    
    def _detect_hallucinated_output(self, response: str) -> Optional[str]:
        """
        Detect if LLM is hallucinating tool execution instead of calling tools.
        
        CRITICAL: Only checks the JSON portion (after </think>), NOT the thinking block.
        Thinking blocks can contain narrative - only JSON output matters.
        
        Hallucination patterns in JSON:
        - "**tool_name output:**" (fake markdown results)
        - "↳ Got X lines" (fake result indicators)
        - Statements claiming execution happened without corresponding tool call
        - Extensive narrative text instead of JSON object
        
        Returns error message if hallucination detected, None if valid.
        """
        # Extract JSON portion only (after </think> if present)
        json_portion = response
        if "</think>" in response:
            json_portion = response.split("</think>", 1)[1].strip()
        
        # Patterns that indicate hallucination in the JSON portion
        # These are ONLY checked against JSON, not thinking blocks
        hallucination_patterns = [
            r'\*\*[a-z_]+\s+(?:output|results?):\*\*',  # **tool_name output:** or **results:**
            r'↳\s+Got\s+\d+\s+(?:lines|results|entries|folders?)',  # ↳ Got X lines
            r'(?:has been executed|has been run|was executed|executed successfully)',  # Claims of execution without tool call
            r'(?:remote_execute|script|command).*(?:output|results?):\s*(?:\n|$)',  # Tool output followed by results
            r'```\s*(?:json|javascript|python|powershell|shell)',  # Code block (fake results)
        ]
        
        for pattern in hallucination_patterns:
            if re.search(pattern, json_portion, re.IGNORECASE):
                logger.warning(f"HALLUCINATION DETECTED in JSON: Pattern matched: {pattern}")
                logger.warning(f"JSON portion: {json_portion[:300]}")
                return f"LLM is narrating execution instead of calling tools. Detected: '{pattern[:40]}...'"
        
        # Check if JSON portion is mostly narrative instead of JSON
        # Accept various key names that models might use for tool/action
        has_json = '{' in json_portion and any(
            key in json_portion for key in ['"tool"', '"action"', '"step"', '"task"', '"instruction"']
        )
        if not has_json:
            # If there's substantial text but no JSON, it's hallucination
            text_length = len(json_portion.strip())
            
            # Look for key hallucination indicators in narrative-only responses
            if text_length > 100:
                hallucination_indicators = [
                    r'script\s+(?:was|has been|has|was already)\s+executed',
                    r'(?:successfully\s+)?(?:retrieved|gathered|collected|found)',
                    r'folder\w*\s+(?:sizes?|information)',
                    r'(?:the\s+)?results?\s+(?:are|show|indicate)',
                ]
                
                for indicator in hallucination_indicators:
                    if re.search(indicator, json_portion, re.IGNORECASE):
                        logger.warning(f"HALLUCINATION DETECTED: Narration pattern matched: {indicator}")
                        logger.warning(f"Full response: {json_portion[:200]}")
                        return "LLM is narrating results instead of calling tools to execute them"
                
                # Fallback: if we have substantial text but no JSON, assume hallucination
                logger.warning(f"HALLUCINATION DETECTED: No JSON found in substantial response")
                logger.warning(f"JSON portion (no JSON found): {json_portion[:200]}")
                return "LLM produced narrative text instead of required JSON tool call format"
        
        return None
    
    def _parse_response(self, response: str, task: str) -> Step:
        """Parse LLM response into a Step object.
        
        Response format is now:
        <think>reasoning here</think>
        {"tool": "...", "params": {...}, "note": "..."}
        
        Handles edge cases:
        - Multiple JSON objects (LLM outputting more than one action) - takes first only
        - Windows paths with unescaped backslashes
        - Extra content after JSON
        """
        import uuid
        
        # Log the raw response for debugging
        logger.info(f"Raw LLM response (first 500 chars): {response[:500] if response else '(empty)'}")
        
        # Check for hallucination FIRST
        hallucination_error = self._detect_hallucinated_output(response)
        if hallucination_error:
            logger.error(f"Hallucination error: {hallucination_error}")
            return Step(
                step_id=f"hallucination_{uuid.uuid4().hex[:8]}",
                tool="complete",
                params={"error": "INVALID FORMAT: " + hallucination_error + " Output must be exactly: <think>reasoning</think> then JSON."},
                reasoning="Blocked hallucinated response",
            )
        
        # Extract thinking content (for logging/reasoning field)
        # Only extract from the FIRST think block
        thinking = ""
        if "<think>" in response and "</think>" in response:
            think_start = response.index("<think>") + len("<think>")
            think_end = response.index("</think>")
            thinking = response[think_start:think_end].strip()
        
        # Extract JSON after </think> (or try whole response if no tags)
        json_str = response
        if "</think>" in response:
            json_str = response.split("</think>", 1)[1].strip()
        
        # CRITICAL: Extract only the FIRST JSON object
        # LLMs sometimes output multiple tool calls - we only want the first one
        json_str = self._extract_first_json_object(json_str)
        
        try:
            # Fix common JSON issues from LLMs
            # 1. Windows paths with single backslashes: C:\ → C:\\
            # (uses module-level re import)
            fixed_json = re.sub(r'(?<!\\)\\(?![\\nrt"])', r'\\\\', json_str)
            
            # Try to parse as JSON
            data = json.loads(fixed_json)
            
            # Generate step ID
            step_id = f"step_{uuid.uuid4().hex[:8]}"
            
            # Use thinking as reasoning, fall back to note
            note = data.get("note", "") or data.get("reasoning", "") or data.get("description", "") or data.get("instruction", "")
            reasoning = thinking if thinking else note
            
            # Handle alternative key names from the model
            # Model sometimes outputs various keys instead of "tool"
            tool_name = (
                data.get("tool") or 
                data.get("action") or 
                data.get("step") or  # Sometimes model puts tool name in "step"
                "unknown"
            )
            
            # If tool_name is a full sentence, try to extract tool from it
            if tool_name and len(tool_name) > 30:
                # Model might output something like "call scan_workspace to identify..."
                for known_tool in ["scan_workspace", "read_file", "write_file", "execute_shell", 
                                   "list_agents", "remote_execute", "complete", "dump_state"]:
                    if known_tool in tool_name.lower():
                        tool_name = known_tool
                        break
                else:
                    tool_name = "unknown"
            
            # Model sometimes outputs params in different ways
            params = data.get("params", {})
            if not params:
                # Try to extract params from other common model outputs
                if "path" in data:
                    params = {"path": data["path"]}
                elif "file_path" in data:
                    params = {"path": data["file_path"]}
                elif "command" in data:
                    params = {"command": data["command"]}
                elif "answer" in data:
                    params = {"answer": data["answer"]}
            
            logger.info(f"Parsed step: tool={tool_name}, params={params}")
            
            return Step(
                step_id=step_id,
                tool=tool_name,
                params=params,
                reasoning=reasoning,
                batch_id=data.get("batch_id"),
            )
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            logger.warning(f"Raw response (first 500 chars): {response[:500] if response else '(empty)'}")
            logger.warning(f"JSON portion (first 500 chars): {json_str[:500] if json_str else '(empty)'}")
            
            # Try to extract intent from the invalid response and suggest a correction
            # This helps when the model outputs markdown instead of JSON
            # Note: get session state here since _parse_response doesn't receive it as param
            current_state = get_session_state()
            suggested_tool = self._infer_tool_from_invalid_response(response, task, current_state)
            if suggested_tool:
                logger.info(f"Auto-correcting invalid response to: {suggested_tool}")
                return suggested_tool
            
            # Return error step
            return Step(
                step_id=f"parse_error_{uuid.uuid4().hex[:8]}",
                tool="complete",
                params={"error": f"LLM returned invalid response format. Please try again."},
                reasoning=f"Parse error: {e}",
            )
    
    def _extract_task_intent_sync(self, task: str) -> dict:
        """
        Use LLM to extract structured intent from a user task (SYNCHRONOUS version).
        
        This is called from _infer_tool_from_invalid_response which is sync.
        Uses requests library instead of httpx to avoid async issues.
        
        Returns dict with:
            - drives: List of drive letters mentioned (e.g., ["C", "S"])
            - operation: What the user wants (e.g., "scan", "list", "find")
            - needs_remote: Whether this requires a remote agent
        """
        import requests as sync_requests
        
        extraction_prompt = """Extract structured information from this user request.
Return ONLY valid JSON, no explanation.

User request: "{task}"

Return JSON with:
- "drives": array of drive letters mentioned (uppercase, e.g., ["C", "S"]). Include drives mentioned as "C:", "C drive", "C:\\", etc.
- "operation": the main operation ("scan", "list", "find", "read", "other")
- "needs_remote": true if this requires accessing user's machine/drives, false for workspace operations

Example outputs:
{{"drives": ["C", "S"], "operation": "scan", "needs_remote": true}}
{{"drives": ["D"], "operation": "find", "needs_remote": true}}
{{"drives": [], "operation": "list", "needs_remote": false}}

JSON only:"""
        
        try:
            url = f"{self.base_url}/api/chat"
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": extraction_prompt.format(task=task)},
                ],
                "stream": False,
                "format": "json",  # Force JSON output
                "options": {"temperature": 0},  # Deterministic
            }
            
            response = sync_requests.post(url, json=payload, timeout=15.0)
            response.raise_for_status()
            
            content = response.json().get("message", {}).get("content", "{}")
            result = json.loads(content)
            
            logger.info(f"Task intent extraction: {result}")
            return result
            
        except Exception as e:
            logger.warning(f"Task intent extraction failed: {e}")
            return {"drives": [], "operation": "unknown", "needs_remote": False}
    
    def _infer_tool_from_invalid_response(self, response: str, task: str, session_state: Optional[SessionState] = None) -> Optional[Step]:
        """
        Try to infer the intended tool from an invalid (non-JSON) LLM response.
        
        This handles cases where the model outputs markdown/conversational text
        instead of the required <think>...</think> + JSON format.
        
        Uses session_state to determine what's already been done:
        - If agents not verified → list_agents
        - If task mentions drive scans → remote_execute with smart size-checking command
        
        NOTE: Now uses synchronous _extract_task_intent_sync to avoid async issues.
        """
        import uuid
        
        response_lower = response.lower()
        
        # Get current state
        if session_state is None:
            session_state = get_session_state()
        
        agents_verified = session_state.agents_verified
        discovered_agents = session_state.discovered_agents
        
        # Use LLM to extract task intent (synchronous call - no async issues)
        intent = self._extract_task_intent_sync(task)
        
        requested_drives = intent.get("drives", [])
        operation = intent.get("operation", "unknown")
        needs_remote = intent.get("needs_remote", False)
        
        # Track which drives have already been size-checked (from completed steps)
        scanned_drives = set()
        for step in session_state.completed_steps:
            if step.tool == "remote_execute" and step.success:
                # Check if this was a size-checking command for a drive
                cmd = step.params.get("command", "")
                if "Get-ChildItem" in cmd and "-Directory" in cmd:
                    # Extract drive letter from command (uses module-level re import)
                    drive_match = re.search(r'Get-ChildItem\s+([A-Z]):\\', cmd, re.IGNORECASE)
                    if drive_match:
                        scanned_drives.add(drive_match.group(1).upper())
        
        logger.info(f"Auto-correct analysis: agents_verified={agents_verified}, requested_drives={requested_drives}, scanned_drives={scanned_drives}, operation={operation}")
        
        # MINIMAL AUTO-CORRECTION: Only handle critical prerequisites
        # The LLM should decide what commands to run - we just ensure agents are verified first
        
        # If task needs remote execution but agents not verified, verify them first
        if needs_remote or requested_drives:
            if not agents_verified:
                logger.info("Auto-correcting: agents not verified, calling list_agents first")
                return Step(
                    step_id=f"autocorrect_{uuid.uuid4().hex[:8]}",
                    tool="list_agents",
                    params={},
                    reasoning="Auto-corrected: need to verify agents before remote operations",
                )
            
            # If no agents available, can't do remote operations
            if not discovered_agents:
                logger.info("Auto-correcting: no agents available, completing with error")
                return Step(
                    step_id=f"autocorrect_{uuid.uuid4().hex[:8]}",
                    tool="complete",
                    params={"error": "No FunnelCloud agents available. Start an agent on your machine first."},
                    reasoning="Auto-corrected: no agents available for remote operations",
                )
        
        # PRIORITY 2: If response mentions needing agents and we haven't verified
        if not agents_verified and ("agent" in response_lower or "list_agents" in response_lower):
            return Step(
                step_id=f"autocorrect_{uuid.uuid4().hex[:8]}",
                tool="list_agents",
                params={},
                reasoning="Auto-corrected: need to discover agents first",
            )
        
        return None
    
    def _extract_first_json_object(self, text: str) -> str:
        """
        Extract only the first JSON object from text.
        
        Handles cases where LLM outputs multiple JSON objects or extra content.
        Uses brace counting to find the end of the first object.
        """
        if not text:
            return text
        
        # Find start of JSON
        start = text.find('{')
        if start == -1:
            return text
        
        # Count braces to find matching close
        depth = 0
        in_string = False
        escape_next = False
        
        for i, char in enumerate(text[start:], start):
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            
            if in_string:
                continue
            
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    # Found end of first JSON object
                    result = text[start:i+1]
                    # Log if we truncated additional content
                    remaining = text[i+1:].strip()
                    if remaining and (remaining.startswith('<think>') or remaining.startswith('{')):
                        logger.warning(f"Truncated additional LLM output: {remaining[:100]}...")
                    return result
        
        # If we get here, braces didn't balance - return original
        return text[start:]
    
    def validate_script(self, script: str, language: str = "powershell") -> dict:
        """
        Validate a script for syntax, logic, and safety issues.
        
        Returns dict with:
            {
                "valid": bool,
                "issues": [{"type": "syntax|logic|safety|resource", "severity": "error|warning", "description": "...", "line": int or None, "suggestion": "..."}],
                "summary": "...",
                "can_fix": bool,  # True if issues are automatically fixable
                "fixed_script": str or None,
            }
        """
        issues = []
        language = language.lower()
        
        if language == "powershell":
            issues = self._validate_powershell(script)
        elif language == "python":
            issues = self._validate_python(script)
        elif language in ("bash", "shell", "sh"):
            issues = self._validate_bash(script)
        else:
            # Generic validation
            issues = self._validate_generic(script)
        
        # Categorize issues
        errors = [i for i in issues if i.get("severity") == "error"]
        warnings = [i for i in issues if i.get("severity") == "warning"]
        
        # Determine if fixable
        fixable_types = {"syntax", "missing_error_handling", "missing_quoting"}
        can_fix = all(i.get("type") in fixable_types for i in errors)
        
        # Build fixed version if issues are fixable
        fixed_script = None
        if can_fix and errors:
            fixed_script = self._fix_script(script, errors, language)
        
        # Build summary
        if not issues:
            summary = "✅ Script looks good - no syntax or safety issues detected"
        elif can_fix:
            summary = f"⚠️ Found {len(errors)} fixable issue(s). Can auto-correct."
        else:
            summary = f"❌ Found {len(errors)} issue(s) needing review + {len(warnings)} warning(s)"
        
        return {
            "valid": len(errors) == 0,
            "issues": issues,
            "errors": errors,
            "warnings": warnings,
            "summary": summary,
            "can_fix": can_fix,
            "fixed_script": fixed_script,
            "language": language,
        }
    
    def _validate_powershell(self, script: str) -> list:
        """Validate PowerShell script."""
        issues = []
        lines = script.split("\n")
        
        # Check for unmatched quotes
        quote_issues = self._check_unmatched_quotes(script)
        for line_num, quote_char in quote_issues:
            issues.append({
                "type": "syntax",
                "severity": "error",
                "description": f"Missing closing {quote_char}",
                "line": line_num,
                "suggestion": f"Check line {line_num} for unclosed {quote_char}"
            })
        
        # Check for unmatched braces/parens
        brace_issues = self._check_unmatched_braces(script)
        for line_num, pair in brace_issues:
            issues.append({
                "type": "syntax",
                "severity": "error",
                "description": f"Unmatched {pair[0]}...{pair[1]}",
                "line": line_num,
                "suggestion": f"Check line {line_num} for unclosed bracket"
            })
        
        # Check for missing $_ in script blocks (common LLM mistake)
        # Wrong: Where-Object {.PSIsContainer -eq $false}
        # Right: Where-Object {$_.PSIsContainer -eq $false}
        if re.search(r'Where-Object|Where\s+\{|ForEach-Object|ForEach\s+\{', script):
            if re.search(r'\{\s*\.([A-Za-z])', script):
                issues.append({
                    "type": "syntax",
                    "severity": "error",
                    "description": "Missing $_ before property in script block (e.g., {.Property} should be {$_.Property})",
                    "line": None,
                    "suggestion": "Use $_.PropertyName instead of .PropertyName in Where-Object/ForEach-Object blocks"
                })
        
        # Check for missing error handling on Get-ChildItem with -Recurse
        if "Get-ChildItem" in script and "-Recurse" in script:
            if "-ErrorAction" not in script:
                issues.append({
                    "type": "missing_error_handling",
                    "severity": "warning",
                    "description": "Get-ChildItem -Recurse without -ErrorAction handling",
                    "line": None,
                    "suggestion": "Add -ErrorAction SilentlyContinue to skip permission errors"
                })
        
        # Check for dangerous operations without guards
        dangerous_patterns = [
            (r"Remove-Item\s+.*-Recurse", "Recursive delete without confirmation"),
            (r"Format-Volume", "Disk format operation without confirmation"),
        ]
        for pattern, description in dangerous_patterns:
            if re.search(pattern, script, re.IGNORECASE):
                issues.append({
                    "type": "safety",
                    "severity": "error",
                    "description": description,
                    "line": None,
                    "suggestion": "This operation requires explicit user confirmation"
                })
        
        # Check for problematic cmdlets that might hang
        problematic = [
            (r"Get-CimInstance\s+Win32_", "Get-CimInstance hangs if DVD drive present"),
            (r"Get-WmiObject\s+Win32_", "Get-WmiObject can hang on optical drives"),
            (r"\[System.IO.DriveInfo\]", "DriveInfo can block on optical drives"),
        ]
        for pattern, note in problematic:
            if re.search(pattern, script, re.IGNORECASE):
                issues.append({
                    "type": "resource",
                    "severity": "warning",
                    "description": f"Potential timeout: {note}",
                    "line": None,
                    "suggestion": "Consider specifying drives explicitly (e.g., @('C:', 'D:'))"
                })
        
        return issues
    
    def _validate_python(self, script: str) -> list:
        """Validate Python script."""
        issues = []
        
        # Check for syntax with ast module
        try:
            import ast
            ast.parse(script)
        except SyntaxError as e:
            issues.append({
                "type": "syntax",
                "severity": "error",
                "description": f"Syntax error: {e.msg}",
                "line": e.lineno,
                "suggestion": f"Check line {e.lineno}: {e.text.strip() if e.text else ''}"
            })
        
        # Check for common issues
        if "import" in script and "__name__" not in script:
            if any(line.strip().startswith("import") for line in script.split("\n")):
                issues.append({
                    "type": "logic",
                    "severity": "warning",
                    "description": "No if __name__ == '__main__' guard",
                    "line": None,
                    "suggestion": "Add proper main guard for script execution"
                })
        
        # Check for missing error handling on file operations
        if "open(" in script and "except" not in script:
            issues.append({
                "type": "missing_error_handling",
                "severity": "warning",
                "description": "File operations without error handling",
                "line": None,
                "suggestion": "Add try/except for file operations"
            })
        
        return issues
    
    def _validate_bash(self, script: str) -> list:
        """Validate Bash script."""
        issues = []
        
        # Check for shebang
        if not script.startswith("#!/"):
            issues.append({
                "type": "logic",
                "severity": "warning",
                "description": "No shebang line",
                "line": 1,
                "suggestion": "Start script with #!/bin/bash"
            })
        
        # Check for unmatched quotes
        quote_issues = self._check_unmatched_quotes(script)
        for line_num, quote_char in quote_issues:
            issues.append({
                "type": "syntax",
                "severity": "error",
                "description": f"Missing closing {quote_char}",
                "line": line_num,
                "suggestion": f"Check line {line_num} for unclosed {quote_char}"
            })
        
        # Check for rm -rf without safety
        if "rm -rf" in script and "-i" not in script:
            issues.append({
                "type": "safety",
                "severity": "error",
                "description": "rm -rf without confirmation",
                "line": None,
                "suggestion": "This is dangerous. Requires explicit user confirmation."
            })
        
        return issues
    
    def _validate_generic(self, script: str) -> list:
        """Generic validation for unknown script types."""
        issues = []
        
        # Just check for obvious syntax patterns
        quote_issues = self._check_unmatched_quotes(script)
        for line_num, quote_char in quote_issues:
            issues.append({
                "type": "syntax",
                "severity": "error",
                "description": f"Possible unmatched {quote_char}",
                "line": line_num,
                "suggestion": f"Check line {line_num}"
            })
        
        return issues
    
    def _check_unmatched_quotes(self, text: str) -> list:
        """Check for unmatched quotes. Returns [(line_num, quote_char), ...]"""
        issues = []
        lines = text.split("\n")
        
        for line_num, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith("#"):
                continue
            
            # Simple quote counting (not perfect, but catches common issues)
            double_quotes = 0
            single_quotes = 0
            
            in_string = False
            escape_next = False
            
            for char in line:
                if escape_next:
                    escape_next = False
                    continue
                
                if char == "\\":
                    escape_next = True
                    continue
                
                if char == '"' and not in_string:
                    double_quotes += 1
                    in_string = True
                elif char == '"' and in_string:
                    double_quotes -= 1
                    if double_quotes < 0:
                        double_quotes = 0
                    in_string = False
                
                if char == "'" and not in_string:
                    single_quotes += 1
                    in_string = True
                elif char == "'" and in_string:
                    single_quotes -= 1
                    if single_quotes < 0:
                        single_quotes = 0
                    in_string = False
            
            if double_quotes > 0:
                issues.append((line_num, '"'))
            if single_quotes > 0:
                issues.append((line_num, "'"))
        
        return issues
    
    def _check_unmatched_braces(self, text: str) -> list:
        """Check for unmatched braces/brackets. Returns [(line_num, (open, close)), ...]"""
        issues = []
        lines = text.split("\n")
        
        # Track nesting
        stack = []
        pairs = {"{": "}", "[": "]", "(": ")"}
        
        for line_num, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith("#"):
                continue
            
            for char in line:
                if char in pairs:
                    stack.append((char, line_num))
                elif char in pairs.values():
                    if not stack:
                        # Close without open
                        issues.append((line_num, ("?", char)))
                    else:
                        open_char, open_line = stack[-1]
                        if pairs[open_char] == char:
                            stack.pop()
                        else:
                            # Mismatched
                            issues.append((line_num, (open_char, char)))
        
        # Any remaining on stack are unclosed
        for char, line_num in stack:
            issues.append((line_num, (char, pairs[char])))
        
        return issues
    
    def _fix_script(self, script: str, errors: list, language: str) -> str:
        """
        Attempt to fix known-fixable issues.
        Returns fixed script or original if can't fix.
        """
        fixed = script
        
        # For PowerShell, add missing error handling
        if language == "powershell":
            for error in errors:
                if error.get("type") == "missing_error_handling":
                    if "Get-ChildItem" in fixed and "-ErrorAction" not in fixed:
                        # Add -ErrorAction to Get-ChildItem
                        fixed = re.sub(
                            r"(Get-ChildItem\s+[^|]*?)(\s*\|)",
                            r"\1 -ErrorAction SilentlyContinue\2",
                            fixed
                        )
        
        return fixed
    
    def _redirect_workspace_command(self, command: str, code: str = "") -> Optional[Step]:
        """
        Convert a bash/shell command targeting the workspace into the appropriate workspace tool.
        Returns None if the command cannot be redirected.
        """
        # If 'code' param contains a Python script, redirect to write_file
        if code and ("import " in code or "def " in code or "class " in code):
            filename = "app.py"  # Default
            if "flask" in code.lower():
                filename = "app.py"
            elif "django" in code.lower():
                filename = "manage.py"
            return Step(
                step_id="guardrail_redirect_code_to_file",
                tool="write_file",
                params={"path": filename, "content": code},
                reasoning="Redirected remote_execute code to write_file (workspace operation)",
            )
        
        if command.startswith("touch "):
            # touch file.py -> write_file
            files_str = command.replace("touch ", "").strip().replace("/workspace/", "")
            files = files_str.split()
            first_file = files[0] if files else "unnamed.txt"
            return Step(
                step_id="guardrail_redirect_workspace",
                tool="write_file",
                params={"path": first_file, "content": ""},
                reasoning=f"Redirected touch to write_file - file: {first_file}",
            )
        elif command.startswith("echo ") and " > " in command:
            # echo content > file -> write_file
            parts = command.split(" > ")
            content = parts[0].replace("echo ", "").replace("-n ", "").strip().strip('"').strip("'")
            filename = parts[1].strip().replace("/workspace/", "")
            return Step(
                step_id="guardrail_redirect_workspace",
                tool="write_file",
                params={"path": filename, "content": content},
                reasoning="Redirected echo to write_file",
            )
        elif command.startswith("cat "):
            # cat file -> read_file
            filename = command.replace("cat ", "").strip().replace("/workspace/", "")
            return Step(
                step_id="guardrail_redirect_workspace",
                tool="read_file",
                params={"path": filename},
                reasoning="Redirected cat to read_file",
            )
        elif command.startswith("find ") or command.startswith("ls "):
            # find/ls -> scan_workspace
            return Step(
                step_id="guardrail_redirect_workspace",
                tool="scan_workspace",
                params={"path": "."},
                reasoning="Redirected find/ls to scan_workspace",
            )
        elif command.startswith("mkdir "):
            # Let execute_shell handle mkdir
            return Step(
                step_id="guardrail_redirect_workspace",
                tool="execute_shell",
                params={"command": command},
                reasoning="Redirected mkdir to execute_shell",
            )
        
        # Can't redirect this command
        return None
    
    def _extract_target_agent(self, user_request: str, discovered_agents: List[str]) -> Optional[str]:
        """
        Extract the target agent from a user request by matching against discovered agents.
        
        This is CRITICAL for preventing the wrong-target bug where the model defaults
        to the first agent instead of using the user-specified target.
        
        Handles:
        - Explicit names: "domain02", "prod-api-01"
        - Contextual references: "my workstation", "my PC", "my machine"
        - Quoted targets: 'server-name' or "server-name"
        - Action patterns: "reboot X", "shutdown X"
        
        Args:
            user_request: The user's original request (e.g., "reboot domain02")
            discovered_agents: List of available agent IDs
            
        Returns:
            Matching agent ID if found, None otherwise
        """
        if not user_request or not discovered_agents:
            return None
        
        request_lower = user_request.lower()
        
        # Strategy 0: Contextual references - "my workstation", "my PC", "my machine"
        # These refer to the user's personal machine
        personal_machine_phrases = [
            "my workstation", "my pc", "my machine", "my computer", "my desktop",
            "my laptop", "workstation", "personal machine"
        ]
        if any(phrase in request_lower for phrase in personal_machine_phrases):
            # Look for agents that are likely workstations
            workstation_indicators = ["workstation", "desktop", "laptop", "ians", "ian-", "-pc", "-ws"]
            for agent in discovered_agents:
                agent_lower = agent.lower()
                if any(ind in agent_lower for ind in workstation_indicators):
                    logger.info(f"Target extraction: contextual match '{agent}' for personal machine reference")
                    return agent
            # Also check for agents with user name patterns (e.g., "ians-r16")
            for agent in discovered_agents:
                if re.match(r'^[a-z]+s?-[a-z0-9]+$', agent.lower()):  # Pattern like "ians-r16"
                    logger.info(f"Target extraction: user-pattern match '{agent}' for personal machine")
                    return agent
        
        # Strategy 1: Exact match - check if any agent ID appears in the request
        for agent in discovered_agents:
            if agent.lower() in request_lower:
                logger.info(f"Target extraction: exact match '{agent}' in request")
                return agent
        
        # Strategy 2: Quoted target - extract 'target' or "target" from request
        quoted_matches = re.findall(r"['\"]([^'\"]+)['\"]", user_request)
        for quoted in quoted_matches:
            quoted_lower = quoted.lower()
            for agent in discovered_agents:
                if agent.lower() == quoted_lower or quoted_lower in agent.lower():
                    logger.info(f"Target extraction: quoted match '{agent}' from '{quoted}'")
                    return agent
        
        # Strategy 3: Action target - "reboot X", "shutdown X", "restart X", "check X"
        action_patterns = [
            r"(?:reboot|restart|shutdown|stop|start|check|query|scan)\s+['\"]?(\S+?)['\"]?(?:\s|$)",
            r"(?:on|to|from)\s+['\"]?(\S+?)['\"]?(?:\s|$)",
        ]
        for pattern in action_patterns:
            matches = re.findall(pattern, request_lower)
            for match in matches:
                # Clean up the match (remove trailing punctuation)
                match = match.rstrip(".,!?")
                for agent in discovered_agents:
                    if agent.lower() == match or match in agent.lower():
                        logger.info(f"Target extraction: action match '{agent}' from pattern")
                        return agent
        
        # No match found
        logger.warning(f"Target extraction: no match found for request '{user_request}' in agents {discovered_agents}")
        return None
    
    def _validate_powershell_syntax(self, command: str) -> List[str]:
        """
        Validate PowerShell command syntax and return list of errors.
        Catches common LLM mistakes before they cause massive error output.
        
        NOTE: Uses module-level 're' import - do NOT add local 'import re' here
        as it causes Python scoping bugs (UnboundLocalError).
        """
        errors = []
        
        # Check for unnecessary powershell -Command wrapper (agent already runs PS)
        if command.startswith("powershell -Command") or command.startswith('powershell -c'):
            errors.append("Unnecessary 'powershell -Command' wrapper - agent runs PowerShell directly")
        
        # Check for unbalanced quotes (causes "missing terminator" errors)
        # PowerShell uses backtick (`) for escaping, NOT backslash
        # So 'S:\\' is valid (two chars: backslash, backslash) not an escape sequence
        single_quotes = command.count("'")
        double_quotes = command.count('"')
        # Only count backtick-escaped quotes as escaped in PowerShell
        single_quotes -= command.count("`'")
        double_quotes -= command.count('`"')
        
        if single_quotes % 2 != 0:
            errors.append("Missing closing single quote (') - unbalanced quotes")
        if double_quotes % 2 != 0:
            errors.append("Missing closing double quote (\") - unbalanced quotes")
        
        # Check for unbalanced braces (script blocks)
        open_braces = command.count('{')
        close_braces = command.count('}')
        if open_braces != close_braces:
            errors.append(f"Missing closing brace - {open_braces} open, {close_braces} close")
        
        # Check for unbalanced parentheses
        open_parens = command.count('(')
        close_parens = command.count(')')
        if open_parens != close_parens:
            errors.append(f"Missing closing parenthesis - {open_parens} open, {close_parens} close")
        
        # Check for missing $_ in Where-Object script blocks
        # Wrong: Where-Object {.Property -eq ...}  
        # Right: Where-Object {$_.Property -eq ...}
        if "Where-Object" in command or "Where" in command:
            # Pattern: { followed by .PropertyName without $_ prefix
            bad_where = re.search(r'\{\s*\.([A-Za-z]+)', command)
            if bad_where:
                errors.append(f"Missing $_ before .{bad_where.group(1)} in Where-Object")
        
        # Check for Where-Object PSIsContainer pattern (should use -File flag)
        if re.search(r'Where-Object.*PSIsContainer.*\$false', command, re.IGNORECASE):
            errors.append("Use -File flag instead of Where-Object PSIsContainer filter")
        
        # Check for missing $_ in ForEach-Object script blocks
        if "ForEach-Object" in command or "ForEach" in command:
            bad_foreach = re.search(r'\{\s*\.([A-Za-z]+)', command)
            if bad_foreach:
                errors.append(f"Missing $_ before .{bad_foreach.group(1)} in ForEach-Object")
        
        # Check for cmd.exe syntax in what should be PowerShell
        # ANY use of 'dir' command should be converted to Get-ChildItem
        if command.strip().lower().startswith("dir ") or command.strip().lower() == "dir":
            errors.append("Using cmd.exe 'dir' command - use Get-ChildItem instead")
        
        # Check for broken piping (common with recursive patterns)
        if "| |" in command:
            errors.append("Broken pipe syntax: '| |'")
        
        # Check for $False/$True not being boolean (common typo)
        if re.search(r'-eq\s+Fal', command) and "$false" not in command.lower():
            errors.append("Use $false instead of False/Fal in comparisons")
        
        return errors
    
    def _fix_powershell_command(self, command: str, errors: List[str]) -> str:
        """
        Attempt to fix PowerShell syntax errors.
        Returns fixed command or simplified alternative.
        
        NOTE: Uses module-level 're' import - do NOT add local 'import re' here.
        """
        fixed = command
        
        for error in errors:
            # Remove unnecessary powershell -Command wrapper
            if "Unnecessary 'powershell -Command'" in error:
                # Extract the actual command from: powershell -Command "actual command"
                wrapper_match = re.search(r'powershell\s+(?:-Command|-c)\s+["\'](.+)["\']$', fixed, re.IGNORECASE | re.DOTALL)
                if wrapper_match:
                    fixed = wrapper_match.group(1)
                    logger.info(f"GUARDRAIL: Removed powershell wrapper, command: {fixed[:80]}")
            
            if "Missing $_" in error:
                # Fix: {.Property -> {$_.Property
                fixed = re.sub(r'\{\s*\.', '{$_.', fixed)
            
            # Replace Where-Object PSIsContainer with -File flag
            if "Use -File flag instead" in error:
                # Remove the Where-Object clause and add -File
                fixed = re.sub(
                    r'\|\s*Where-Object\s*\{[^}]*PSIsContainer[^}]*\}',
                    '',
                    fixed,
                    flags=re.IGNORECASE
                )
                # Add -File flag if not present
                if "-File" not in fixed and "Get-ChildItem" in fixed:
                    fixed = re.sub(r'(Get-ChildItem\s+)', r'\1-File ', fixed)
                logger.info(f"GUARDRAIL: Replaced PSIsContainer filter with -File flag")
            
            if "cmd.exe 'dir'" in error:
                # Replace dir with Get-ChildItem equivalent
                # Patterns: dir, dir S:\, dir /s C:\path, dir S:\ /ad
                # Extract path (drive letter with colon and optional backslash/path)
                path_match = re.search(r'dir\s+(?:/[a-z-]+\s+)*([A-Z]:[\\]?[^\s/]*)', fixed, re.IGNORECASE)
                recurse_flag = "/s" in fixed.lower()
                
                if path_match:
                    path = path_match.group(1)
                    # Ensure path ends properly
                    if path.endswith(':'):
                        path = path + '\\'
                else:
                    path = 'C:\\'
                
                recurse = "-Recurse" if recurse_flag else ""
                fixed = f"Get-ChildItem -Path {path} {recurse}".strip()
            
            if "$false instead of False" in error:
                # Fix False -> $false
                fixed = re.sub(r'-eq\s+False', '-eq $false', fixed, flags=re.IGNORECASE)
                fixed = re.sub(r'-eq\s+Fal\w*', '-eq $false', fixed, flags=re.IGNORECASE)
        
        # Add -ErrorAction if missing on Get-ChildItem -Recurse
        if "Get-ChildItem" in fixed and "-Recurse" in fixed and "-ErrorAction" not in fixed:
            fixed = re.sub(
                r'(Get-ChildItem[^|]*-Recurse[^|]*?)(\s*\||$)',
                r'\1 -ErrorAction SilentlyContinue\2',
                fixed
            )
        
        return fixed
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
