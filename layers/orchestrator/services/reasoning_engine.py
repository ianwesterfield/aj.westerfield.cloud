"""
Reasoning Engine - LLM Coordination for Step Generation

Uses Ollama to generate structured reasoning steps from user intents.
Parses LLM output into validated Step objects.

Architecture:
- State is maintained EXTERNALLY by SessionState (not by the LLM)
- LLM receives state as context, only outputs next step
- This prevents state drift and reduces token cost

Helper modules:
- helpers.guardrails: Step validation and correction rules
- helpers.powershell_utils: PowerShell syntax validation and fixing
- helpers.response_parser: LLM response parsing and JSON extraction
- helpers.agent_utils: Agent target extraction and command redirection
- helpers.stream_parser: ThinkingStreamParser for streaming <think> blocks
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

# Import helpers
from services.helpers import (
    GuardrailEngine,
    PowerShellValidator,
    ResponseParser,
    AgentTargetExtractor,
    ThinkingStreamParser,
)
from services.helpers.powershell_utils import ScriptValidator


logger = logging.getLogger("orchestrator.reasoning")

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "r1-distill-aj:32b-4k")

# Pragmatics API for intent classification (DistilBERT on CPU)
PRAGMATICS_API_URL = os.getenv("PRAGMATICS_API_URL", "http://pragmatics_api:8001")


SYSTEM_PROMPT = """
You are AJ, an infrastructure and context aware AI assistant to reason about infrastructure, coding, automation, and system management and any thing else the user might need.
FORMAT: {"tool": "name", "params": {...}, "reasoning": "why"}

ABSOLUTES:

1. NEVER FABRICATE OUTPUT
   - You CANNOT see command results until you execute a task
   - EVERY piece of data must come from a COMPLETED task
   - If you write "ping output:" without executing ALL TASKS first = FABRICATION
   - If you write times like "2ms, 3ms, 5ms" without actual commands = FABRICATION
   - There are NO tasks called "ping", "disk_iops", "memory_usage" - ONLY the 3 listed below

2. ONLY THESE 3 TOOLS EXIST:
   - execute: {"agent_id": "X", "command": "..."} - Runs command on indicated agent, returns output
   - think: {"thought": "..."} - Planning, user request decomposition / execution task composition
   - complete: {"answer": "..."} - Final response

3. BOOTSTRAP AGENT
   You have a LOCAL FunnelCloud agent available at localhost. Use it to discover other agents:
   - Discover agents: execute on "localhost" with command: Invoke-RestMethod http://localhost:41421/discover-peers
   - The discover-peers endpoint returns all FunnelCloud agents on the network via multicast
   - Each agent has: agent_id, hostname, platform, ip_address, grpc_port

4. TO GET DATA, YOU MUST EXECUTE
   ! User memories should only suffice to suggest what and where to execute, NOT provide actual data.
   - Need agent list? execute discover-peers on localhost first
   - Need ping times? execute Test-Connection command on target agent
   - Need disk info? execute Get-PSDrive command on target agent
   - Need memory? execute Get-Process or systeminfo command on target agent
   ! NO SHORTCUTS. NO IMAGINED RESULTS.

5. ANSWER ONLY WHAT WAS ASKED
   - User asks about ping → respond about ping only
   - Do NOT invent follow-up questions
   - Do NOT answer questions that weren't asked
   - Do NOT run extra commands beyond what is needed to answer the question
   - Do NOT repeat yourself. Analyze your previous task completions before adding new ones.

6. MINIMAL STEPS - DON'T OVERCOMPLICATE
   - "How many agents online?" → execute discover-peers on localhost → count → complete
   - "What agents do I have?" → execute discover-peers on localhost → list them → complete
   - Do NOT ping/test agents unless specifically asked to verify connectivity
   - discover-peers already confirms agents are registered and reachable

7. AMBIGUOUS REQUESTS - ASK FOR CLARIFICATION
   - If user asks for "installation ID" - ask: Windows installation ID? Product key? Some software?
   - If command target is unclear - ask which agent to run it on
   - Do NOT guess or invent software names
   - When in doubt: {"tool": "complete", "params": {"answer": "Could you clarify what you mean by X?"}}

WORKFLOW:

Step 1: Understand what user wants (user request decomposition, execution task composition)
Step 2: Call the MINIMUM tools needed
Step 3: Use ACTUAL tool output to answer
Step 4: Call complete with your answer
Step 5: STOP

QUICK ANSWERS:
- "How many agents?" → execute discover-peers on localhost → count → complete
- "What agents are available?" → execute discover-peers on localhost → list them → complete
- "Is agent X online?" → execute discover-peers on localhost → check if in list → complete

PLATFORM COMMANDS (all current agents are Windows):
- Ping: Test-Connection -ComputerName TARGET -Count 4
- Disk: Get-PSDrive C
- Memory: Get-Process | Measure-Object WorkingSet -Sum
- Time: Get-Date
- Windows Install ID: (Get-CimInstance -Class SoftwareLicensingService).OA3xOriginalProductKey
- Windows Product ID: (Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion').ProductId

ACTIVE DIRECTORY COMMANDS (run on domain controllers like domain01, domain02):
- AD user groups: Get-ADUser -Identity USERNAME | Get-ADPrincipalGroupMembership | Select-Object Name
- AD user info: Get-ADUser -Identity USERNAME -Properties *
- AD group members: Get-ADGroupMember -Identity "GROUP NAME" | Select-Object Name
- Domain controllers: Get-ADDomainController -Filter * | Select-Object HostName
NOTE: For AD users, use just the username (e.g., 'ian'), NOT domain\\username format

ERROR HANDLING:
- If a command fails, try an alternative approach
- If 'westerfield\\ian' fails → try just 'ian'
- If path not found → try alternative paths or ask user
- Report errors clearly so user can troubleshoot

EXAMPLE - "How many agents are online?":
1. {"tool": "execute", "params": {"agent_id": "localhost", "command": "Invoke-RestMethod http://localhost:41421/discover-peers"}}
2. [See output: {agents: [...], count: 5}]
3. {"tool": "complete", "params": {"answer": "There are 5 agents online: ians-r16, r730xd, domain01, domain02, exchange01"}}
DONE. No pinging needed.

EXAMPLE - "Ping domain01 from domain02":
1. {"tool": "execute", "params": {"agent_id": "domain02", "command": "Test-Connection -ComputerName domain01 -Count 4"}}
2. [WAIT FOR ACTUAL OUTPUT]
3. {"tool": "complete", "params": {"answer": "[use the REAL output from step 1]"}}

WRONG - FABRICATION:
- Writing "ping output: 2ms, 3ms, 5ms" without calling execute = HALLUCINATION
- Inventing tools like "disk_iops" or "memory_usage" = HALLUCINATION
- Looking for "FunnelCloud" software when user didn't mention it = HALLUCINATION
"""


# JSON Schema for structured output
TOOL_CALL_SCHEMA = {
    "type": "object",
    "properties": {
        "tool": {
            "type": "string",
            "description": "Tool to call",
            "enum": [
                "execute",
                "think",
                "complete",
            ],
        },
        "params": {"type": "object", "description": "Parameters for the tool"},
        "note": {"type": "string", "description": "Brief status note"},
        "reasoning": {
            "type": "string",
            "description": "Why this tool is being called",
        },
    },
    "required": ["tool", "params"],
}


class ReasoningEngine:
    """
    LLM-powered reasoning engine for step generation.

    Architecture:
    - State is maintained externally by SessionState
    - LLM receives state as context, only outputs the next step
    - This prevents hallucination and state drift
    """

    # Model size estimates for load time prediction (in GB)
    MODEL_SIZES = {
        "llama3.2:1b": 1.3,
        "llama3.2:3b": 2.0,
        "llama3.2": 2.0,
        "r1-distill-aj:32b-4k": 19.0,
        "r1-distill-aj:32b-8k": 19.0,
        "r1-distill-aj:32b-2k": 19.0,
        "r1-distill-aj:32b": 19.0,
        "aj-deepseek-r1-32b": 18.5,
        "aj-deepseek-r1-32b:q8": 32.5,
        "qwen2.5-aj:32b": 20.0,
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
        "qwen2.5:32b": 20.0,
        "qwen2.5:14b": 9.0,
        "qwen2.5:7b": 4.4,
        "qwen2.5": 4.4,
    }

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=300.0)
        self.model = OLLAMA_MODEL
        self.base_url = OLLAMA_BASE_URL
        self._load_speed_gb_per_sec = 0.2
        self._model_preloaded = False

        # Initialize helpers
        self._guardrails = GuardrailEngine()
        self._script_validator = ScriptValidator()

    def set_model(self, model: str) -> None:
        """Set the model to use for reasoning."""
        if model and model != self.model:
            logger.info(f"Switching model: {self.model} -> {model}")
            self.model = model
            self._model_preloaded = False

    async def warmup_model(self) -> bool:
        """Pre-load the model into Ollama's memory."""
        if self._model_preloaded:
            return True

        try:
            logger.info(f"Pre-loading model: {self.model}")
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": "x",
                "stream": False,
                "keep_alive": "24h",
            }

            response = await self.client.post(url, json=payload, timeout=300.0)
            response.raise_for_status()

            self._model_preloaded = True
            logger.info(f"Model pre-loaded successfully: {self.model}")
            return True

        except Exception as e:
            logger.warning(f"Model pre-load failed (non-blocking): {e}")
            return False

    def _estimate_load_time(self) -> int:
        """Estimate cold load time in seconds based on model size."""
        for model_prefix, size_gb in self.MODEL_SIZES.items():
            if self.model.startswith(model_prefix):
                return max(5, int(size_gb / self._load_speed_gb_per_sec))
        return 15

    @staticmethod
    def format_status(
        loaded: bool,
        model_was_loaded: bool,
        elapsed: float,
        estimated_total: float,
    ) -> Tuple[bool, str]:
        """Build the status string for streaming status monitor.

        Returns (model_was_loaded, status_string).
        """
        if loaded:
            if not model_was_loaded:
                model_was_loaded = True
                new_status = "🧠 Reasoning..."
            else:
                if elapsed < 10:
                    new_status = "🧠 Reasoning..."
                else:
                    new_status = f"🧠 Reasoning... ({int(elapsed)}s)"
        else:
            remaining = max(1, estimated_total - elapsed)
            percent = min(95, int((elapsed / estimated_total) * 100))

            if elapsed < estimated_total:
                new_status = f"⏳ Loading model... {percent}%"
            else:
                new_status = f"⏳ Loading model... ({elapsed:.0f}s)"

        return model_was_loaded, new_status

    # =========================================================================
    # Intent Classification
    # =========================================================================

    async def classify_intent(self, task: str) -> dict:
        """
        Classify user intent via pragmatics API (DistilBERT on CPU).

        Intent Types (4-class):
        - "casual": Greetings, general chat, questions about concepts
        - "save": User providing info to remember ("My name is Ian")
        - "recall": User asking for stored info ("What's my name?")
        - "task": Workspace/code/execution requests

        Returns dict with intent mapped to orchestrator expectations:
        - "conversational" for casual intents
        - "save" for memory save intents
        - "recall" for memory recall intents
        - "task" for execution intents
        """
        try:
            url = f"{PRAGMATICS_API_URL}/api/pragmatics/classify"
            payload = {"text": task}

            response = await self.client.post(url, json=payload, timeout=5.0)
            response.raise_for_status()

            result = response.json()
            intent = result.get("intent", "task")
            confidence = result.get("confidence", 0.5)
            all_probs = result.get("all_probs", {})

            logger.info(
                f"Intent classification: {intent} (conf={confidence:.2f}) "
                f"probs={all_probs}"
            )

            # Map pragmatics intents to orchestrator behavior
            # casual -> conversational (answer directly, no OODA)
            # save -> save (route to memory, no OODA)
            # recall -> recall (query memory, no OODA)
            # task -> task (run OODA loop)
            mapped_intent = "conversational" if intent == "casual" else intent

            return {
                "intent": mapped_intent,
                "confidence": confidence,
                "reason": "Pragmatics DistilBERT classification",
                "all_probs": all_probs,
            }

        except Exception as e:
            logger.warning(f"Pragmatics API classification failed: {e}")
            # Fallback to task (safer - will run OODA which can handle anything)
            return {
                "intent": "task",
                "confidence": 0.5,
                "reason": f"Pragmatics API failed, defaulting to task: {e}",
            }

    async def classify_intent_with_context(self, task: str, context: str) -> dict:
        """
        Classify intent with conversation context via pragmatics API.

        Used when a short message like "yes", "do it", "ok" follows an assistant
        message that proposed an action. Context helps determine if user is
        confirming a task vs. just chatting.
        """
        try:
            url = f"{PRAGMATICS_API_URL}/api/pragmatics/classify-with-context"
            payload = {
                "text": task,
                "context": context[:2000],  # API limit
            }

            response = await self.client.post(url, json=payload, timeout=5.0)
            response.raise_for_status()

            result = response.json()
            intent = result.get("intent", "task")
            confidence = result.get("confidence", 0.5)

            logger.info(f"Intent with context: {intent} (conf={confidence:.2f})")

            # Map casual -> conversational for orchestrator compatibility
            mapped_intent = "conversational" if intent == "casual" else intent

            return {
                "intent": mapped_intent,
                "confidence": confidence,
                "reason": "Pragmatics context-aware classification",
            }

        except Exception as e:
            logger.warning(f"Pragmatics context classification failed: {e}")
            # Fallback to conversational for short ambiguous messages
            return {
                "intent": "conversational",
                "confidence": 0.5,
                "reason": f"Pragmatics API failed: {e}",
            }

    async def answer_conversational(
        self, task: str, memory_context: Optional[List[dict]] = None
    ) -> str:
        """Answer a conversational question directly without OODA planning."""
        context_parts = []
        if memory_context:
            for item in memory_context[:5]:
                facts = item.get("facts")
                if facts and isinstance(facts, dict):
                    for fact_type, fact_value in facts.items():
                        context_parts.append(f"- {fact_type}: {fact_value}")
                else:
                    text = item.get("user_text", "") or item.get("text", "")
                    if text:
                        context_parts.append(f"- {text}")

        system_prompt = """You are AJ, a helpful AI assistant. Answer the user's question directly and concisely.

RESPONSE FORMAT:
- Respond in clean Markdown - NEVER output raw JSON objects or action wrappers
- Use fenced code blocks (```) for code, commands, or structured output
- Use backticks for `file paths`, `IP addresses`, `hostnames`, `commands`
- Write natural prose for explanations

If you have relevant context from memory, use it to personalize your response.
If you don't know something, say so honestly."""

        if context_parts:
            system_prompt += f"\n\nRelevant context from memory:\n" + "\n".join(
                context_parts
            )

        try:
            url = f"{self.base_url}/api/chat"
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task},
                ],
                "stream": False,
                "options": {"temperature": 0.6},
            }

            response = await self.client.post(url, json=payload, timeout=60.0)
            response.raise_for_status()

            return (
                response.json()
                .get("message", {})
                .get("content", "I'm not sure how to answer that.")
            )

        except Exception as e:
            logger.error(f"Conversational answer failed: {e}")
            return f"I encountered an error trying to answer: {e}"

    # =========================================================================
    # Task Planning
    # =========================================================================

    async def generate_task_plan(self, task: str) -> List[str]:
        """Generate a task plan (numbered list of steps) before execution begins."""
        planning_prompt = """
You are a task planner. Output ONLY a numbered list (1. 2. 3.) with 2-5 steps.
NO JSON. NO explanations. Just numbered steps.

TIPS:
- If task mentions multiple targets (C: and S:), list them as separate steps
- For remote operations, include "verify agent available" as first step
- End with a verification or summary step

Now create a plan for:
"""

        try:
            url = f"{self.base_url}/api/chat"
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": planning_prompt},
                    {"role": "user", "content": task},
                ],
                "stream": True,
                "options": {"temperature": 0.3, "num_predict": 500},
            }

            response = await self.client.post(url, json=payload, timeout=30.0)
            response.raise_for_status()

            content = response.json().get("message", {}).get("content", "")
            logger.debug(f"Task plan raw response: {content[:500]}")

            # Parse numbered list
            steps = []
            for line in content.split("\n"):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith("-")):
                    cleaned = re.sub(r"^[\d]+[.\)]\s*", "", line)
                    cleaned = re.sub(r"^[-*]\s*", "", cleaned)
                    if cleaned:
                        steps.append(cleaned)

            # Try JSON format as fallback
            if not steps:
                try:
                    json_data = json.loads(content)
                    if isinstance(json_data, dict):
                        if "steps" in json_data:
                            steps = [str(s) for s in json_data["steps"]]
                        elif "plan" in json_data:
                            steps = [str(s) for s in json_data["plan"]]
                    elif isinstance(json_data, list):
                        steps = [str(s) for s in json_data if s]
                except (json.JSONDecodeError, ValueError):
                    pass

            # Deduplicate
            seen = set()
            unique_steps = []
            for step in steps:
                step_key = step.lower().strip()
                if step_key not in seen:
                    seen.add(step_key)
                    unique_steps.append(step)

            logger.info(
                f"Generated task plan with {len(unique_steps)} steps: {unique_steps}"
            )
            return unique_steps if unique_steps else ["Execute task"]

        except Exception as e:
            logger.warning(f"Task planning failed: {e}")
            return ["Execute task"]

    # =========================================================================
    # OODA Loop: Goal Satisfaction & Replanning
    # =========================================================================

    async def check_goal_satisfaction(
        self,
        original_goal: str,
        session_state: Optional[SessionState] = None,
    ) -> dict:
        """
        Check if the current execution results satisfy the original goal.

        Returns:
            {
                "satisfied": bool,
                "confidence": float (0-1),
                "reason": str,
                "suggested_action": "complete" | "continue" | "replan"
            }
        """
        if session_state is None:
            session_state = get_session_state()

        # Build compact context from command flow
        flow_summary = session_state.command_flow.summarize_for_replan()
        recent_entries = session_state.command_flow.query_recent(5)
        recent_summary = "\n".join(
            session_state.command_flow.format_step_summary(e) for e in recent_entries
        )

        check_prompt = f"""Evaluate if the executed steps satisfy the user's goal.

ORIGINAL GOAL: {original_goal}

EXECUTION SUMMARY:
{flow_summary}

RECENT STEPS:
{recent_summary}

Respond with ONLY a JSON object:
{{"satisfied": true/false, "confidence": 0.0-1.0, "reason": "brief explanation", "suggested_action": "complete"/"continue"/"replan"}}

Rules:
- "satisfied": true if the goal has been achieved
- "continue": if current plan should proceed to next step
- "replan": if a different approach is needed due to errors or new information
- "complete": if done, even if partially (report what was accomplished)"""

        try:
            url = f"{self.base_url}/api/chat"
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a goal evaluation assistant. Respond only with JSON.",
                    },
                    {"role": "user", "content": check_prompt},
                ],
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 200},
            }

            response = await self.client.post(url, json=payload, timeout=15.0)
            response.raise_for_status()

            content = response.json().get("message", {}).get("content", "")

            # Parse JSON response
            try:
                # Extract JSON from response
                json_match = re.search(r"\{[^}]+\}", content)
                if json_match:
                    result = json.loads(json_match.group())
                    return {
                        "satisfied": result.get("satisfied", False),
                        "confidence": result.get("confidence", 0.5),
                        "reason": result.get("reason", ""),
                        "suggested_action": result.get("suggested_action", "continue"),
                    }
            except json.JSONDecodeError:
                pass

            # LLM didn't return valid JSON - default to continue
            return {
                "satisfied": False,
                "confidence": 0.5,
                "reason": "Unable to parse LLM response",
                "suggested_action": "continue",
            }

        except Exception as e:
            logger.warning(f"Goal satisfaction check failed: {e}")
            return {
                "satisfied": False,
                "confidence": 0.3,
                "reason": f"Check failed: {e}",
                "suggested_action": "continue",
            }

    async def generate_replan(
        self,
        original_goal: str,
        session_state: Optional[SessionState] = None,
        failure_reason: str = "",
    ) -> List[str]:
        """
        Generate a new plan based on execution results and failures.

        Called when:
        - A task fails and recovery is needed
        - Goal satisfaction check suggests replanning
        - New information changes the approach
        """
        if session_state is None:
            session_state = get_session_state()

        flow_summary = session_state.command_flow.summarize_for_replan()
        failures = session_state.command_flow.query_failures()
        failure_details = "\n".join(
            f"- Step {f.step_index}: {f.command or f.tool} failed: {f.error}"
            for f in failures[-3:]  # Last 3 failures
        )

        replan_prompt = f"""You need to create a NEW plan to achieve the goal.

ORIGINAL GOAL: {original_goal}

WHAT WAS TRIED:
{flow_summary}

FAILURES:
{failure_details if failures else "No failures"}

REASON FOR REPLAN: {failure_reason or "Previous approach did not fully satisfy the goal"}

Create a NEW numbered list (1. 2. 3.) with 2-4 steps.
- Learn from the failures - don't repeat the same mistakes
- Try alternative approaches if the original didn't work
- Be specific about what commands to run

Output ONLY the numbered list:"""

        try:
            url = f"{self.base_url}/api/chat"
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a task replanner. Output only numbered steps.",
                    },
                    {"role": "user", "content": replan_prompt},
                ],
                "stream": False,
                "options": {"temperature": 0.4, "num_predict": 400},
            }

            response = await self.client.post(url, json=payload, timeout=20.0)
            response.raise_for_status()

            content = response.json().get("message", {}).get("content", "")

            # Parse numbered list
            steps = []
            for line in content.split("\n"):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith("-")):
                    cleaned = re.sub(r"^[\d]+[.\)]\s*", "", line)
                    cleaned = re.sub(r"^[-*]\s*", "", cleaned)
                    if cleaned:
                        steps.append(cleaned)

            logger.info(f"Generated replan with {len(steps)} steps: {steps}")
            return steps if steps else ["Try alternative approach"]

        except Exception as e:
            logger.warning(f"Replan generation failed: {e}")
            return ["Report current status and ask user for guidance"]

    # =========================================================================
    # Model Status
    # =========================================================================

    async def check_model_status(self) -> dict:
        """Check if the model is loaded in Ollama."""
        try:
            url = f"{self.base_url}/api/ps"
            response = await self.client.get(url, timeout=5.0)
            response.raise_for_status()
            data = response.json()

            for m in data.get("models", []):
                if m.get("name", "").startswith(self.model):
                    size_vram = m.get("size_vram", 0)
                    size_gb = size_vram / (1024**3) if size_vram else 0
                    return {
                        "loaded": True,
                        "loading": False,
                        "size_vram": size_vram,
                        "details": f"{self.model} loaded ({size_gb:.1f}GB VRAM)",
                    }

            return {
                "loaded": False,
                "loading": False,
                "size_vram": 0,
                "details": "Model not loaded",
            }

        except Exception as e:
            logger.debug(f"Model status check failed: {e}")
            return {
                "loaded": False,
                "loading": False,
                "size_vram": 0,
                "details": str(e),
            }

    # =========================================================================
    # Step Generation
    # =========================================================================

    async def generate_next_step(
        self,
        task: str,
        history: List[StepResult],
        memory_context: List[Dict[str, Any]],
        workspace_context: Optional[WorkspaceContext] = None,
        session_state: Optional[SessionState] = None,
    ) -> Step:
        """Generate the next step for a task using LLM reasoning."""
        if session_state is None:
            session_state = get_session_state()

        # Build context
        user_message = self._build_context(
            task, memory_context, workspace_context, session_state
        )

        # Check step limit guardrail
        if len(session_state.completed_steps) >= 15:
            logger.warning(
                f"GUARDRAIL: {len(session_state.completed_steps)} steps - forcing completion check"
            )
            recent_edits = sum(
                1
                for s in session_state.completed_steps[-5:]
                if s.tool
                in ("write_file", "insert_in_file", "replace_in_file", "append_to_file")
                and s.success
            )
            if recent_edits == 0:
                return Step(
                    step_id="guardrail_complete",
                    tool="complete",
                    params={"error": "Too many steps without progress"},
                    batch_id=None,
                    reasoning="Forced completion after 15 steps without recent edits",
                )

        # Call Ollama
        try:
            response = await self._call_ollama(user_message)
            step = ResponseParser.parse_response(response, task)
            step = self._guardrails.apply(step, session_state)
            return step

        except Exception as e:
            logger.error(f"Reasoning engine error: {e}")
            return Step(
                step_id="error_fallback",
                tool="complete",
                params={"error": str(e)},
                batch_id=None,
                reasoning=f"Error during reasoning: {e}",
            )

    async def generate_next_step_streaming(
        self,
        task: str,
        history: List[StepResult],
        memory_context: List[Dict[str, Any]],
        workspace_context: Optional[WorkspaceContext] = None,
        session_state: Optional[SessionState] = None,
        status_callback: Optional[Callable[[str], None]] = None,
    ):
        """Generate next step with streaming - yields (token, Step|None) tuples."""
        if session_state is None:
            session_state = get_session_state()

        # Build context
        user_message = self._build_context(
            task, memory_context, workspace_context, session_state
        )

        # Check step limit guardrail
        if len(session_state.completed_steps) >= 15:
            logger.warning(
                f"GUARDRAIL: {len(session_state.completed_steps)} steps - forcing completion"
            )
            recent_edits = sum(
                1
                for s in session_state.completed_steps[-5:]
                if s.tool
                in ("write_file", "insert_in_file", "replace_in_file", "append_to_file")
                and s.success
            )
            if recent_edits == 0:
                yield "", Step(
                    step_id="guardrail_complete",
                    tool="complete",
                    params={"error": "Too many steps without progress"},
                    batch_id=None,
                    reasoning="Forced completion after 15 steps without recent edits",
                )
                return

        # Stream from Ollama
        full_response = ""
        parser = ThinkingStreamParser()

        try:
            if status_callback:
                stream = self._stream_with_status(user_message, status_callback)
            else:
                stream = self._call_ollama_streaming(user_message)

            async for token, in_think_block, accumulated in stream:
                full_response = accumulated
                content_to_yield = parser.feed(token)
                if content_to_yield:
                    yield content_to_yield, None

            step = ResponseParser.parse_response(full_response, task)
            step = self._guardrails.apply(step, session_state)
            yield "", step

        except Exception as e:
            logger.error(f"Streaming reasoning error: {e}")
            yield "", Step(
                step_id="error_fallback",
                tool="complete",
                params={"error": str(e)},
                batch_id=None,
                reasoning=f"Error during reasoning: {e}",
            )

    # =========================================================================
    # Script Validation (delegated to helper)
    # =========================================================================

    def validate_script(self, script: str, language: str = "powershell") -> dict:
        """Validate a script for syntax, logic, and safety issues."""
        return self._script_validator.validate(script, language)

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _build_context(
        self,
        task: str,
        memory_context: List[Dict[str, Any]],
        workspace_context: Optional[WorkspaceContext],
        session_state: SessionState,
    ) -> str:
        """Build the context string for LLM prompts."""
        context_parts = []

        # 1. External state
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

        # 3. User info
        if session_state.user_info:
            user_info_text = "\n".join(
                f"  {k}: {v}" for k, v in session_state.user_info.items()
            )
            context_parts.append(
                f"User info (use this, don't guess):\n{user_info_text}"
            )

        # 4. Memory patterns
        if memory_context:
            patterns = "\n".join(
                [
                    f"- {p.get('description', 'Similar task')}: {p.get('approach', '')}"
                    for p in memory_context[:3]
                ]
            )
            context_parts.append(f"Relevant patterns from memory:\n{patterns}")

        context = "\n\n".join(context_parts)
        user_message = f"Task: {task}"
        if context:
            user_message = f"{context}\n\n{user_message}"

        logger.debug(f"Prompt size: {len(user_message)} chars")
        return user_message

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
            "keep_alive": -1,
            "format": TOOL_CALL_SCHEMA,
            "options": {
                "temperature": 0,
                "top_p": 0.1,
                "top_k": 5,
            },
        }

        logger.debug(f"Calling Ollama: {self.model}")
        response = await self.client.post(url, json=payload)
        response.raise_for_status()

        return response.json().get("message", {}).get("content", "")

    async def _call_ollama_streaming(self, user_message: str):
        """Call Ollama API with streaming."""
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "stream": True,
            "keep_alive": -1,
            "format": TOOL_CALL_SCHEMA,
            "options": {
                "temperature": 0,
                "top_p": 0.1,
                "top_k": 5,
            },
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

                        if "<think>" in full_response and not in_think_block:
                            in_think_block = True
                        if "</think>" in full_response and in_think_block:
                            in_think_block = False

                        yield token, in_think_block, full_response
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue

        if full_response:
            yield "", False, full_response

    async def _stream_with_status(
        self,
        user_message: str,
        status_callback: Callable[[str], None],
    ) -> AsyncGenerator[Tuple[str, bool, str], None]:
        """Stream from Ollama while emitting status updates during cold start."""
        first_token_received = asyncio.Event()
        status_task = None
        start_time = asyncio.get_event_loop().time()
        estimated_total = self._estimate_load_time()

        async def status_monitor():
            model_was_loaded = False
            last_status = ""
            check_interval = 0.3

            while not first_token_received.is_set():
                elapsed = asyncio.get_event_loop().time() - start_time
                status = await self.check_model_status()

                model_was_loaded, new_status = ReasoningEngine.format_status(
                    loaded=status["loaded"],
                    model_was_loaded=model_was_loaded,
                    elapsed=elapsed,
                    estimated_total=estimated_total,
                )

                if new_status != last_status:
                    status_callback(new_status)
                    last_status = new_status

                try:
                    await asyncio.wait_for(
                        first_token_received.wait(), timeout=check_interval
                    )
                except asyncio.TimeoutError:
                    pass

        status_task = asyncio.create_task(status_monitor())

        try:
            async for token, in_think, accumulated in self._call_ollama_streaming(
                user_message
            ):
                if token and not first_token_received.is_set():
                    first_token_received.set()
                yield token, in_think, accumulated
        finally:
            first_token_received.set()
            if status_task:
                status_task.cancel()
                try:
                    await status_task
                except asyncio.CancelledError:
                    pass

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
