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


SYSTEM_PROMPT = """You are AJ, an agentic AI that executes tasks by calling tools.

⛔⛔⛔ MANDATORY OUTPUT FORMAT - ABSOLUTELY NO EXCEPTIONS ⛔⛔⛔

Your response MUST contain EXACTLY ONE of these:

FORMAT 1 (with thinking):
<think>Brief reasoning (1-2 sentences max)</think>
{"tool": "tool_name", "params": {...}, "note": "status"}

FORMAT 2 (no thinking):
{"tool": "tool_name", "params": {...}, "note": "status"}

RULES (ABSOLUTE - VIOLATION CAUSES IMMEDIATE FAILURE):
1. ONLY output JSON tool calls. NOTHING ELSE.
2. Do NOT output narrative text, explanations, or any words before/after the JSON.
3. Do NOT output multiple tool calls - exactly ONE per response.
4. Do NOT claim you will do something - just do it (call the tool).
5. Do NOT describe fake results - call tools to get real results.
6. Do NOT output markdown, headers, or formatting.
7. Do NOT put anything before <think> or after the JSON.

❌ VIOLATIONS THAT WILL FAIL IMMEDIATELY:
  ❌ "I will now call list_agents..." ← WRONG - just output the JSON!
  ❌ "To complete this task, we need to..." ← WRONG - output JSON only!
  ❌ "**Output:** The files are..." ← WRONG - call remote_execute first!
  ❌ "The script has been executed and produced:" ← WRONG - you didn't call remote_execute!
  ❌ "folder1 23.45 GB folder2 17.89 GB" ← WRONG - call remote_execute first!
  ❌ Multiple JSON objects in one response ← WRONG - one tool call only!

✅ CORRECT EXAMPLES:
<think>User needs folder sizes on S: drive from ians-r16.</think>
{"tool": "list_agents", "params": {}, "note": "Verify agent available"}

<think>Got ians-r16 from previous step. Now run the script.</think>
{"tool": "remote_execute", "params": {"command": "...", "agent_id": "ians-r16"}, "note": "Executing script"}

<think>Script completed successfully.</think>
{"tool": "complete", "params": {"answer": "Here are the results..."}, "note": "Done"}

=== EXECUTION MODEL ===

- You will be called repeatedly in a loop
- Each call = one step = one tool call
- For multi-part tasks (e.g., "scan C: and S:"), do ONE at a time
- After C: completes, you'll be called again for S:
- If you need to do 5 things, output ONE now, you'll be called again for the rest

=== FOLLOW THE TASK PLAN ===

A TASK PLAN is generated at the start of each task and shown in the WORKSPACE STATE.
- The plan shows numbered steps with status: ☐ TODO, → NOW, ✓ DONE
- ALWAYS work on the CURRENT TASK (marked → NOW or first ☐ TODO)
- Do NOT skip steps or jump ahead
- Do NOT complete until ALL plan items are DONE
- The plan is your script - follow it!

Example plan in state:
📋 TASK PLAN (follow this script):
  1. [✓ DONE] Verify FunnelCloud agent is available
  2. [→ NOW] Scan C: drive for folder sizes
  3. [☐ TODO] Scan S: drive for folder sizes
  4. [☐ TODO] Report largest folders from both drives

⚡ CURRENT TASK: Step 2 - Scan C: drive for folder sizes

In this example, you should execute Step 2 (scan C:). After it completes, you'll
be called again and the plan will show Step 3 as → NOW.

⛔ FAILURE ANALYSIS & ADAPTIVE PLANNING ⛔

**If the previous step FAILED, you must:**
1. **Analyze the failure** - What went wrong? (syntax error, timeout, permission denied, not found, etc.)
2. **DO NOT repeat the same command** - Diagnose the root cause
3. **Generate a NEW task plan** addressing the root cause, not just retrying
4. **Show the new plan to the user** in your thinking so they understand your strategy shift
5. **Attempt a different approach** - Fix the underlying issue, not just the surface problem

**Examples of adaptive responses to common failures:**

- **If remote_execute fails with "missing string terminator" on PowerShell:**
  ❌ WRONG: Try the same command again with the same quoting
  ✅ RIGHT: Analyze the error → Recognize the quoting issue → Generate NEW PLAN:
     1. Fix PowerShell quoting (use single quotes or here-strings)
     2. Re-test with corrected syntax
     3. If that fails, try a completely different approach (e.g., write script to file first, then execute)

- **If a file operation fails with "permission denied":**
  ❌ WRONG: Try the same path again
  ✅ RIGHT: Generate NEW PLAN:
     1. Check if path exists and is accessible
     2. Try with elevated permissions if needed
     3. Or find alternative path/method

- **If a scan times out:**
  ❌ WRONG: Run the same scan again (will timeout again)
  ✅ RIGHT: Generate NEW PLAN:
     1. Scope the scan more narrowly (smaller directory, specific pattern)
     2. Or use a faster command (e.g., dir vs recursive scan)
     3. Break multi-drive scans into separate steps with smaller scope

**When you detect a failure pattern, format your response as:**
```
<think>
Previous step failed with: [error message]

Root cause: [what actually went wrong - not just symptom]

New strategy: [fundamentally different approach or fix]

Updated plan:
1. [Step to fix root cause]
2. [Step to attempt operation differently]
3. [Verification step]
</think>

{"tool": "...", "params": {...}, "note": "Attempting new approach: [brief description]"}
```

⛔ MULTI-PART TASK RULE ⛔
When user asks for MULTIPLE things (e.g., "scan C: and S:", "read X and Y"):
- Do NOT complete until ALL parts are done
- After finishing part 1, immediately start part 2 - don't say "I'll do it next"
- Only call "complete" when EVERY requested item is finished
- WRONG: Complete after C: with "I'll do S: next" → This ends the task!
- RIGHT: After C: finishes, call remote_execute for S: in the next step

=== SCRIPT VALIDATION & RISK ASSESSMENT ⚠️ ===

**BEFORE executing ANY script (PowerShell, Python, Bash, etc.):**

1. **ANALYZE THE SCRIPT** for:
   - Syntax errors (missing quotes, brackets, colons, etc.)
   - Logic issues (infinite loops, unreachable code, etc.)
   - Missing error handling that could cause failures
   - Path issues (hardcoded paths that don't exist, unchecked file operations)
   - Resource issues (recursion depth, memory, large file operations)
   - Dangerous operations without guards (recursive deletion, format operations, etc.)

2. **IF YOU FIND FIXABLE ISSUES** (syntax, error handling, path issues):
   - FIX THEM AUTOMATICALLY
   - Show the user the changes you made
   - Then execute the corrected script

3. **IF YOU FIND LOGIC ISSUES** (algorithm problems, design issues):
   - ASK THE USER for clarification
   - Show what you think the intended behavior is
   - Offer your suggested fix
   - Wait for user approval before executing

4. **IF YOU FIND DANGEROUS OPERATIONS**:
   - Require explicit user confirmation
   - Show what data/files will be affected
   - Example: "This script will RECURSIVELY DELETE folders matching a pattern. Are you sure?"

**EXAMPLE - FIXABLE ISSUE (unclosed quote):**
```
User provides: $results = Get-ChildItem | Where-Object { $_.Name -match "test }
Problem: Missing closing quote on "test
Action: FIX IT - close the quote
Corrected: $results = Get-ChildItem | Where-Object { $_.Name -match "test" }
Then execute.
```

**EXAMPLE - LOGIC ISSUE (unclear intent):**
```
User provides: Script that sorts files but unclear if ascending or descending
Problem: Behavior unclear - could be either
Action: ASK THE USER - "Should files be sorted largest→smallest or smallest→largest?"
Wait for response.
```

**EXAMPLE - DANGEROUS OPERATION:**
```
User provides: Get-ChildItem -Recurse | Remove-Item -Force
Problem: Recursive delete without confirmation
Action: ASK THE USER - "This will DELETE all files recursively. Are you SURE?"
Confirm before executing.
```

=== COMMUNICATION STYLE ===

NEVER mention internal tool names or system terminology to the user:
- Say "I scanned the directory" NOT "I used scan_workspace"
- Say "the largest files" NOT "the LARGEST FILES section"
- Say "from the file listing" NOT "from the workspace state"
- Say "I found" or "I see" NOT "the state shows"
- NEVER reference section headers like "WORKSPACE STATE" or "ENVIRONMENT FACTS"
- Speak naturally as if you personally explored the files

- The <think> block shows your reasoning to the user (keep it concise!)
- The JSON is the actual action to execute
- "note" is a SHORT status label (e.g., "Reading config", "Scanning files")

=== MISSING INFO RULE ===

If the task references info you don't have (e.g. "my name" but not provided):
<think>The user mentioned their name but I don't have that information.</think>
{"tool": "complete", "params": {"error": "MISSING_INFO: I don't know your name."}, "note": "Need info"}

NEVER guess or fabricate user information.

=== AVAILABLE TOOLS ===

WORKSPACE TOOLS (run inside Docker container):
- scan_workspace: List files. Params: {"path": "string"}
- read_file: Read file. Params: {"path": "string"}
- write_file: Create/overwrite file. Params: {"path": "string", "content": "string"}
- replace_in_file: Find/replace EXISTING text. Params: {"path": "string", "old_text": "string", "new_text": "string"}
- insert_in_file: ADD NEW text at start or end. Params: {"path": "string", "position": "start"|"end", "text": "string"}
- append_to_file: Append to end. Params: {"path": "string", "content": "string"}
- execute_shell: Run shell command IN CONTAINER. Params: {"command": "string"}
- dump_state: Output full workspace state as JSON. Params: {} — Use when user asks to see state/metadata
- validate_script: Analyze script for syntax/logic/risk before execution. Params: {"script": "string", "language": "powershell|python|bash|other"}
  Returns: Issues found, whether they're auto-fixable, and corrected script if applicable
  Use this BEFORE calling remote_execute with a script

FUNNELCLOUD TOOLS (run on user's HOST machine via agent):
- list_agents: Discover available FunnelCloud agents. Params: {}
  ⚠️ MUST call this FIRST when user says "my machine", "my PC", "my computer", etc.
  Returns: agent names and their platforms (e.g., "ians-r16" on Windows)
  
- remote_execute: Run command on HOST machine. Params: {"command": "string", "agent_id": "string"}
  ⚠️ ALWAYS use PowerShell syntax (NOT cmd.exe)!
  ⚠️ VALIDATE the script BEFORE executing (see SCRIPT VALIDATION section above)
  ⚠️ No timeout limit - commands can run as long as needed

=== POWERSHELL REFERENCE ===

Useful commands you can figure out yourself - use your PowerShell knowledge:
- Get-ChildItem for listing files/directories
- Measure-Object for sizes
- Sort-Object, Select-Object for filtering
- Always add -ErrorAction SilentlyContinue to skip permission errors

⛔ AVOID THESE (will hang on optical drives):
  Get-CimInstance Win32_LogicalDisk    # Hangs if DVD drive exists
  Get-WmiObject Win32_*                # Same problem
  [System.IO.DriveInfo]::GetDrives()   # Blocks on optical
  Get-PSDrive (without specifying drives)  # Can hang

CONTROL TOOLS:
- none: Skip (change already present). Params: {"reason": "string"}
- complete: Done or ask clarification. Params: 
    {"answer": "your response to user"} - when task is complete
    {"error": "reason why you can't complete"} - when something went wrong
    {"question": "clarifying question"} - when you need user input before proceeding

=== MACHINE REFERENCE VALIDATION (MANDATORY) ===

⛔ YOU MUST CALL list_agents BEFORE ANY remote_execute! ⛔

When user references "my machine", "my computer", "my PC", "locally", or any machine name:

1. FIRST call list_agents to discover available agents - NO EXCEPTIONS!
2. If you already called list_agents THIS SESSION and found an agent, you may skip step 1
3. If user said a specific name (e.g., "on server-01"), verify that agent exists
4. If no agents found → complete with error asking user to start an agent
5. Only THEN proceed with remote_execute using the verified agent_id

⚠️ NEVER assume "my machine" = any specific agent. ALWAYS verify first!

Example flow:
  User: "What's running on my PC?"
  Step 1: {"tool": "list_agents", "params": {}}
  Step 2: (after seeing agent list) {"tool": "remote_execute", "params": {"agent_id": "ians-r16", "command": "Get-Process | Select -First 10"}}

⚠️ WHEN TO USE REMOTE vs LOCAL:
- User mentions their machine/PC/computer + list_agents found agents → remote_execute
- User asks about workspace files (in /workspace) → scan_workspace, read_file
- If list_agents returns empty → tell user no agent is running

⚠️ ALWAYS include "answer" when completing! If you can answer from workspace state, put your response in the answer param.

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
If task is "list/scan files" and you already did scan_workspace → complete with your answer
If task is "read file X" and X is in "Already read" → complete with your answer
If you can answer from existing state → {"tool": "complete", "params": {"answer": "Your response here"}, "note": "Answered from state"}
If you can't make progress → {"tool": "complete", "params": {"error": "Cannot complete task"}, "note": "Stuck"}

⛔ CRITICAL - SUCCESSFUL RESULTS = COMPLETE IMMEDIATELY ⛔

When a command returns data successfully:
1. DO NOT retry with "better" parameters
2. DO NOT run a similar command "to be sure"
3. IMMEDIATELY complete with the answer from the successful result

Example - WRONG behavior:
  Step 1: remote_execute → returns 162 files ✓
  Step 2: remote_execute with -Depth 3 → WRONG! Already have data!

Example - CORRECT behavior:
  Step 1: remote_execute → returns 162 files ✓
  Step 2: complete with answer listing those files ✓

If you got output, you're DONE. Complete and summarize it!

=== USING EXISTING STATE ===

The WORKSPACE STATE section shows files already scanned. If it shows:
- "Scanned paths: ." → workspace is already indexed, don't scan again
- "Already read: file.py" → don't read that file again  
- Use the indexed files to answer questions directly

⚠️ CRITICAL - When you CAN answer from cached state:
1. DO NOT run unnecessary commands or read files already cached
2. Call complete with your answer: {"tool": "complete", "params": {"answer": "The workspace contains..."}, "note": "From cache"}
3. Your answer MUST be in the "answer" param or the user won't see it!

=== ENVIRONMENT FACTS ===

The state includes ENVIRONMENT FACTS learned from previous command outputs:
- File counts, directory counts, total sizes
- Project types detected (python, docker, node, etc.)
- Frameworks detected (fastapi, pytest, etc.)
- Git branch, Python version, Node version if known
- Observations from shell commands

LARGEST FILES section shows files sorted by size with a TOTAL at the bottom.
Use this to answer questions about disk space, storage, or what to clean up.

⚠️ CRITICAL - When asked about workspace size, file counts, or space usage:
1. FIRST check WORKSPACE STATE for "LARGEST FILES" section with TOTAL
2. If TOTAL is shown, report it directly - DO NOT run any commands
3. Only use shell commands (du, ls) if no cached size data exists
4. Example: If state shows "156.2 KiB TOTAL (indexed files)" → report that!

=== CONVERSATION LEDGER ===

The QUICK REFERENCE section contains important values extracted from previous commands:
- IP addresses, URLs, ports discovered
- Container IDs, Git commits  
- Files that were modified
- Errors that were seen

USER REQUESTS THIS SESSION shows what the user has asked for - use this to:
- Understand the overall session context
- Avoid repeating work that was already done
- Reference prior context when the user says "the file I mentioned" or "that IP"

RECENT ACTIONS shows a timeline of what was done - use this to:
- Avoid duplicating work
- Understand what commands produced what results
- Reference outputs from prior steps

=== DEBUGGING STATE ===

If user asks to "show state", "dump state", "what do you know", or similar:
<think>User wants to see the current workspace state.</think>
{"tool": "dump_state", "params": {}, "note": "Showing state"}

=== PROJECT ANALYSIS ===

When asked to analyze a project or suggest cleanup:
1. Look at key files: package.json, requirements.txt, pyproject.toml, Cargo.toml, etc.
2. Identify project type (Python, Node, Rust, etc.) and framework
3. Common safe-to-remove patterns:
   - __pycache__/, *.pyc, .pytest_cache/ (Python)
   - node_modules/, dist/, build/ (Node)
   - target/ (Rust), bin/, obj/ (C#)
   - .git/ (usually keep), .env (careful - may have secrets)
4. Read config files to understand what's actually used before suggesting removal

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
        planning_prompt = """You are a task planner. Given a user request, output a SHORT numbered list of steps needed.

RULES:
1. Output ONLY a numbered list (1. 2. 3. etc.)
2. Keep it SHORT - 2-5 steps max
3. Be specific but concise
4. If task mentions multiple targets (C: and S:), list them as separate steps
5. For remote/host operations, include "verify agent" as step 1
6. End with a summary/report step

EXAMPLES:

User: "What are the largest files on my C: drive?"
1. Verify FunnelCloud agent is available
2. Scan C: drive for file sizes
3. Report top 10 largest files

User: "Add a comment to README.md"
1. Read README.md
2. Add comment header to file
3. Confirm change

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
                    {"role": "system", "content": "You are a task planner. Output ONLY a numbered list (1. 2. 3.) with 2-5 steps. No other text."},
                    {"role": "user", "content": planning_prompt + task},
                ],
                "stream": False,
                "options": {"temperature": 0.3},  # Low temp for consistent planning
            }
            
            response = await self.client.post(url, json=payload, timeout=30.0)
            response.raise_for_status()
            
            content = response.json().get("message", {}).get("content", "")
            
            # Parse numbered list
            steps = []
            for line in content.split("\n"):
                line = line.strip()
                # Match lines starting with number + period/paren
                if line and (line[0].isdigit() or line.startswith("-")):
                    # Strip the number prefix
                    import re
                    cleaned = re.sub(r'^[\d]+[.\)]\s*', '', line)
                    cleaned = re.sub(r'^[-*]\s*', '', cleaned)
                    if cleaned:
                        steps.append(cleaned)
            
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
        
        # GUARDRAIL: Prevent lazy completion after list_agents
        # If we just discovered agents and LLM tries to complete without doing actual work,
        # reject it - the task likely requires remote_execute
        if step.tool == "complete":
            recent_steps = workspace_state.completed_steps[-3:]
            last_was_list_agents = any(s.tool == "list_agents" for s in recent_steps)
            did_remote_work = any(s.tool == "remote_execute" for s in workspace_state.completed_steps)
            
            if last_was_list_agents and not did_remote_work and workspace_state.discovered_agents:
                # LLM is trying to complete without doing remote work after discovering agents
                error_text = step.params.get("error", "")
                answer_text = step.params.get("answer", "")
                
                # Only block if this looks like a lazy completion (hallucinated answer)
                if answer_text and "scan" not in answer_text.lower() and "error" not in answer_text.lower():
                    logger.warning(f"GUARDRAIL: Blocking lazy completion after list_agents - no remote work done")
                    return Step(
                        step_id="guardrail_require_remote_work",
                        tool="complete",
                        params={"error": "You discovered agents but didn't perform the requested remote operation. Use remote_execute to do the actual work."},
                        reasoning="Blocked lazy completion - LLM must use discovered agents",
                    )
        
        # GUARDRAIL: If last remote_execute succeeded with SAME params, don't retry
        # This catches the "retry with better parameters" anti-pattern
        # BUT allows different commands (scanning C: then S:)
        if step.tool == "remote_execute":
            recent_remote = [s for s in workspace_state.completed_steps[-3:] if s.tool == "remote_execute"]
            if recent_remote:
                last_remote = recent_remote[-1]
                # Check if last remote operation was successful (has output)
                if last_remote.success and "Got" in last_remote.output_summary:
                    # Only block if it's the SAME operation (same path or command)
                    last_path = last_remote.params.get("path", "")
                    new_path = step.params.get("path", "")
                    last_cmd = last_remote.params.get("command", "")
                    new_cmd = step.params.get("command", "")
                    
                    is_same_operation = (last_path and new_path and last_path == new_path) or \
                                        (last_cmd and new_cmd and last_cmd == new_cmd)
                    
                    if is_same_operation:
                        logger.warning(f"GUARDRAIL: Blocking duplicate {step.tool} - same operation already succeeded")
                        return Step(
                            step_id="guardrail_no_retry_remote",
                            tool="complete",
                            params={"answer": "I already retrieved the requested information. See the output above."},
                            reasoning=f"Blocked retry of {step.tool} - previous command succeeded",
                        )
                    else:
                        logger.info(f"GUARDRAIL: Allowing {step.tool} - different target ({new_path or new_cmd} vs {last_path or last_cmd})")
        
        # GUARDRAIL: Detect tool repetition loops (same tool called 3+ times recently)
        # NOTE: remote_execute is exempt - it has its own smarter duplicate detection above
        # that checks if the command is actually the same. Multi-drive scans need multiple calls.
        if step.tool != "remote_execute":
            recent_tools = [s.tool for s in workspace_state.completed_steps[-5:]]
            if step.tool in recent_tools:
                repeat_count = recent_tools.count(step.tool)
                if repeat_count >= 2:
                    # This tool was called 2+ times in last 5 steps and LLM is about to call it again
                    logger.warning(f"GUARDRAIL: Loop detected - {step.tool} called {repeat_count}x in last 5 steps")
                    return Step(
                        step_id="guardrail_loop_break",
                        tool="complete",
                        params={"error": f"Loop detected: {step.tool} was already called {repeat_count} times"},
                        reasoning=f"Forced completion to break {step.tool} loop",
                    )
        
        # GUARDRAIL: Prevent calling dump_state more than once
        if step.tool == "dump_state":
            dump_count = sum(1 for s in workspace_state.completed_steps if s.tool == "dump_state")
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
        has_json = '{' in json_portion and '"tool"' in json_portion
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
            import re
            fixed_json = re.sub(r'(?<!\\)\\(?![\\nrt"])', r'\\\\', json_str)
            
            # Try to parse as JSON
            data = json.loads(fixed_json)
            
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
            logger.warning(f"Raw response (first 500 chars): {response[:500] if response else '(empty)'}")
            logger.warning(f"JSON portion (first 500 chars): {json_str[:500] if json_str else '(empty)'}")
            
            # Try to extract intent from the invalid response and suggest a correction
            # This helps when the model outputs markdown instead of JSON
            # Note: get workspace state here since _parse_response doesn't receive it as param
            current_state = get_workspace_state()
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
    
    def _infer_tool_from_invalid_response(self, response: str, task: str, workspace_state: Optional[WorkspaceState] = None) -> Optional[Step]:
        """
        Try to infer the intended tool from an invalid (non-JSON) LLM response.
        
        This handles cases where the model outputs markdown/conversational text
        instead of the required <think>...</think> + JSON format.
        
        Uses workspace_state to determine what's already been done:
        - If agents not verified → list_agents
        - If task mentions drive scans → remote_execute with smart size-checking command
        
        NOTE: Now uses synchronous _extract_task_intent_sync to avoid async issues.
        """
        import uuid
        
        response_lower = response.lower()
        
        # Get current state
        if workspace_state is None:
            workspace_state = get_workspace_state()
        
        agents_verified = workspace_state.agents_verified
        discovered_agents = workspace_state.discovered_agents
        
        # Use LLM to extract task intent (synchronous call - no async issues)
        intent = self._extract_task_intent_sync(task)
        
        requested_drives = intent.get("drives", [])
        operation = intent.get("operation", "unknown")
        needs_remote = intent.get("needs_remote", False)
        
        # Track which drives have already been size-checked (from completed steps)
        scanned_drives = set()
        for step in workspace_state.completed_steps:
            if step.tool == "remote_execute" and step.success:
                # Check if this was a size-checking command for a drive
                cmd = step.params.get("command", "")
                if "Get-ChildItem" in cmd and "-Directory" in cmd:
                    # Extract drive letter from command like "Get-ChildItem C:\\ -Directory"
                    import re
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
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
