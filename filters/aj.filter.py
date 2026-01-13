# Awesome Task
"""
AJ Filter - Agentic Reasoning & Memory

Open-WebUI filter that handles:
  - Intent classification (recall, save, task)
  - Multi-step reasoning via orchestrator
  - Code execution via executor
  - Semantic memory storage and retrieval
"""

import os
import re
import json
import base64
import sys
from typing import Optional, List, Tuple, Dict, Any
from enum import Enum

import requests
from pydantic import BaseModel, Field


# ============================================================================
# Centralized Logging Utilities (Inline for Open-WebUI Compatibility)
# ============================================================================

class LogLevel(str, Enum):
    """Status/state of a message."""
    SUCCESS = "success"
    DONE = "done"
    SAVED = "saved"
    VERIFIED = "verified"
    RUNNING = "running"
    THINKING = "thinking"
    PROCESSING = "processing"
    LOADING = "loading"
    SCANNING = "scanning"
    INFO = "info"
    READY = "ready"
    WAITING = "waiting"
    WARNING = "warning"
    PARTIAL_ERROR = "partial_error"
    ERROR = "error"
    FAILED = "failed"
    BLOCKED = "blocked"
    MEMORY = "memory"
    CONTEXT = "context"
    EXECUTING = "executing"
    RESULT = "result"


class LogCategory(str, Enum):
    """Source/component emitting the message."""
    FILTER = "filter"
    ORCHESTRATOR = "orchestrator"
    EXECUTOR = "executor"
    MEMORY = "memory"
    PRAGMATICS = "pragmatics"
    EXTRACTOR = "extractor"
    DISPATCHER = "dispatcher"
    REASONING = "reasoning"
    FILE_HANDLER = "file_handler"
    SHELL_HANDLER = "shell_handler"
    POLYGLOT_HANDLER = "polyglot_handler"
    STATE = "state"
    TASK_PLANNER = "task_planner"
    TRAINING = "training"
    VALIDATION = "validation"
    MIGRATION = "migration"


# Icon mapping: (LogCategory, LogLevel) -> icon
ICON_MAP: Dict[Tuple[LogCategory, LogLevel], str] = {
    (LogCategory.FILTER, LogLevel.SUCCESS): "✅",
    (LogCategory.FILTER, LogLevel.DONE): "✅",
    (LogCategory.FILTER, LogLevel.SAVED): "💾",
    (LogCategory.FILTER, LogLevel.THINKING): "💭",
    (LogCategory.FILTER, LogLevel.RUNNING): "⏳",
    (LogCategory.FILTER, LogLevel.READY): "✅",
    (LogCategory.FILTER, LogLevel.MEMORY): "📚",
    (LogCategory.FILTER, LogLevel.CONTEXT): "📖",
    (LogCategory.FILTER, LogLevel.WAITING): "⏸️",
    (LogCategory.FILTER, LogLevel.INFO): "ℹ️",
    (LogCategory.FILTER, LogLevel.WARNING): "⚠️",
    (LogCategory.FILTER, LogLevel.PARTIAL_ERROR): "⚠️",
    (LogCategory.FILTER, LogLevel.ERROR): "❌",
    (LogCategory.FILTER, LogLevel.FAILED): "❌",
    (LogCategory.FILTER, LogLevel.BLOCKED): "🚫",
    (LogCategory.FILTER, LogLevel.SCANNING): "🔍",
    (LogCategory.ORCHESTRATOR, LogLevel.SUCCESS): "✅",
    (LogCategory.ORCHESTRATOR, LogLevel.DONE): "✅",
    (LogCategory.ORCHESTRATOR, LogLevel.THINKING): "🧠",
    (LogCategory.ORCHESTRATOR, LogLevel.RUNNING): "⚡",
    (LogCategory.ORCHESTRATOR, LogLevel.INFO): "ℹ️",
    (LogCategory.ORCHESTRATOR, LogLevel.WARNING): "⚠️",
    (LogCategory.ORCHESTRATOR, LogLevel.ERROR): "❌",
    (LogCategory.ORCHESTRATOR, LogLevel.LOADING): "⏳",
    (LogCategory.MEMORY, LogLevel.SAVED): "💾",
    (LogCategory.MEMORY, LogLevel.MEMORY): "📚",
    (LogCategory.MEMORY, LogLevel.CONTEXT): "📖",
    (LogCategory.MEMORY, LogLevel.ERROR): "❌",
}

DEFAULT_ICON = "◆"


def get_icon(category: LogCategory, level: LogLevel) -> str:
    """Get icon for category and level combination."""
    return ICON_MAP.get((category, level), DEFAULT_ICON)


def log_message(message: str, category: LogCategory, level: LogLevel, include_icon: bool = True, icon_override: Optional[str] = None) -> str:
    """Generate formatted log message with icon."""
    if not include_icon:
        return message
    icon = icon_override if icon_override else get_icon(category, level)
    return f"{icon} {message}"


def create_status_dict(message: str, category: LogCategory, level: LogLevel, done: bool = False, hidden: bool = False) -> Dict[str, any]:
    """Create status dict ready for event emitter."""
    formatted_message = log_message(message, category, level)
    return {
        "type": "status",
        "data": {
            "description": formatted_message,
            "done": done,
            "hidden": hidden,
        }
    }


def create_error_dict(message: str, category: LogCategory, done: bool = True, hidden: bool = False) -> Dict[str, any]:
    """Create error status dict."""
    return create_status_dict(message, category, LogLevel.ERROR, done=done, hidden=hidden)


def create_success_dict(message: str, category: LogCategory, done: bool = True, hidden: bool = False) -> Dict[str, any]:
    """Create success status dict."""
    return create_status_dict(message, category, LogLevel.SUCCESS, done=done, hidden=hidden)


# ============================================================================
# Configuration
# ============================================================================

MEMORY_API_URL = os.getenv("MEMORY_API_URL", "http://memory_api:8000")
EXTRACTOR_API_URL = os.getenv("EXTRACTOR_API_URL", "http://extractor_api:8002")
ORCHESTRATOR_API_URL = os.getenv("ORCHESTRATOR_API_URL", "http://orchestrator_api:8004")
EXECUTOR_API_URL = os.getenv("EXECUTOR_API_URL", "http://executor_api:8005")
PRAGMATICS_API_URL = os.getenv("PRAGMATICS_API_URL", "http://pragmatics_api:8001")

# System prompt describing AJ capabilities and output contracts
# This is injected into the chat LLM that presents results to users
AJ_SYSTEM_PROMPT = """# AJ

AJ is an agentic-capable AI-assisted filter for Open-WebUI. It sits between the LLM and your workspace to route intent, manage semantic memory, run workspace operations, and provide a streaming UX.

## What AJ Does

1. **Classifies Intent** — Determine whether the user is chatting, saving info, recalling, or requesting a task.
2. **Manages Memory** — Save facts/docs/notes and retrieve relevant context later.
3. **Runs Workspace Ops** — Read/list/edit files and run shell commands via the Executor.
4. **Streaming UX** — Show "thinking + progress" while tasks run, then display results verbatim.

## Key Principle (No Shortcuts)

- AJ must not hardcode "patterns" (e.g., "largest files" => `du`) inside the filter. The Orchestrator decides tools, parameters, and ordering.
- If intent == `task`, ALWAYS delegate planning and step selection to the Orchestrator.

## Intent Routing

- `casual`: respond normally, no tools.
- `save`: store memory payload, then confirm saved (short).
- `recall`: search memory, inject relevant results, answer using retrieved context.
- `task`: orchestrate multi-step work (plan → execute → verify → complete).

## Output Contract (VERBATIM-FIRST) — CRITICAL

When ANY tool/command produces output (stdout, stderr, file reads, scans, diffs):

1. **Show the raw output FIRST** in a fenced code block.
2. Output must be **EXACTLY as received**:
   - do NOT summarize
   - do NOT paraphrase
   - do NOT reformat into bullet points
   - do NOT reorder
   - do NOT trim "unimportant" lines
3. **No interpretation before output.** Status lines are allowed; prose is not.
4. After output, you MAY add brief commentary (max 3 lines) limited to:
   - the next step AJ will run (or what it needs from the user)
   - error handling / recovery choices
   - completion confirmation
5. If multiple outputs occur, show them **in chronological order** as separate code blocks.
6. If stdout and stderr both exist, show stdout first, then stderr (separate blocks).

### CORRECT (always do this):
```
total 15
drwxr-xr-x  4096  Dec 28 19:05  filters/
-rw-r--r-- 38618  Dec 29 03:04  README.md
```

### WRONG (never do this):
- filters/: A directory containing…
- README.md: The main documentation…

The user wants to SEE the actual terminal output, not your interpretation of it.

## File Editing Guardrails (Surgical)

- Prefer `replace_in_file` / `insert_in_file` / `append_to_file` over `write_file`.
- Do not overwrite entire files unless explicitly required.
- Preserve existing style and formatting; make minimal edits.
- If an overwrite is necessary, state that clearly BEFORE doing it.

## Role Boundary

- The Orchestrator plans. The Executor executes. AJ presents results and manages memory.
- Users should see the real outputs; AJ must not "translate" outputs into prose.
- If the user requests interpretation, do it only AFTER verbatim output, and do not restate the output in a different format.
"""

# File type to MIME type mapping
CONTENT_TYPE_MAP = {
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".py": "text/x-python",
    ".js": "text/javascript",
    ".ts": "text/typescript",
    ".json": "application/json",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
}


# ============================================================================
# Intent Classification
# ============================================================================

def _classify_intent(text: str) -> Dict[str, Any]:
    """
    Classify user intent via pragmatics 4-class model.
    
    All intent detection is handled by the pragmatics API - no hardcoded
    patterns in the filter. This follows the architecture principle:
    "Orchestrator owns all reasoning — Filter routes by intent but NEVER
    hardcodes tool selection patterns."
    
    Returns:
        {"intent": "recall"|"save"|"task"|"casual", "confidence": float}
    """
    try:
        resp = requests.post(
            f"{PRAGMATICS_API_URL}/api/pragmatics/classify",
            json={"text": text},
            timeout=5,
        )
        if resp.status_code == 200:
            result = resp.json()
            intent = result.get("intent", "casual")
            confidence = result.get("confidence", 0.5)
            print(f"[aj] Pragmatics: {intent} ({confidence:.2f})")
            return {"intent": intent, "confidence": confidence}
    except Exception as e:
        print(f"[aj] Pragmatics API error: {e}")
    
    # Fallback if pragmatics is down - default to casual (safe)
    print("[aj] Warning: Pragmatics unavailable, defaulting to casual")
    return {"intent": "casual", "confidence": 0.3}


def _detect_task_continuation(user_text: str, messages: List[dict], confidence: float) -> bool:
    """
    Detect if a 'casual' response is actually continuing a task.
    
    Uses pragmatics context-aware classification to determine if short
    responses like "yes", "ok", "do it" are task continuations.
    
    All pattern detection is delegated to the pragmatics API - no hardcoded
    patterns in the filter.
    
    Args:
        user_text: Current user message
        messages: Conversation history
        confidence: Initial classification confidence
    
    Returns True if we should upgrade intent to 'task'.
    """
    # Get recent assistant message for context
    context = ""
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip():
                # Take last ~500 chars of assistant message as context
                context = content[-500:] if len(content) > 500 else content
                break
    
    # If no context, can't determine continuation
    if not context:
        print(f"[aj] Task continuation: no assistant context")
        return False
    
    # Delegate to pragmatics context-aware endpoint
    try:
        resp = requests.post(
            f"{PRAGMATICS_API_URL}/api/pragmatics/classify-with-context",
            json={"text": user_text, "context": context},
            timeout=5,
        )
        if resp.status_code == 200:
            result = resp.json()
            intent = result.get("intent", "casual")
            ctx_confidence = result.get("confidence", 0.5)
            
            if intent == "task":
                print(f"[aj] Task continuation: YES via pragmatics (conf={ctx_confidence:.2f})")
                return True
            else:
                print(f"[aj] Task continuation: NO via pragmatics (intent={intent}, conf={ctx_confidence:.2f})")
                return False
    except Exception as e:
        print(f"[aj] Task continuation: pragmatics error: {e}")
    
    # Fallback: if pragmatics unavailable, don't upgrade (safe default)
    return False


# ============================================================================
# Orchestrator Integration
# ============================================================================

def _build_task_description(messages: List[dict]) -> str:
    """
    Build a complete task description from conversation context.
    
    For continuation requests like "Please do" or "yes", we need to include
    the original task context from previous messages so the orchestrator
    knows what to do.
    """
    user_text = _extract_user_text_prompt(messages) or ""
    
    # Check if this is a short continuation response
    short_continuations = [
        "please do", "yes", "yeah", "sure", "ok", "okay", "go ahead",
        "do it", "proceed", "make the changes", "sounds good",
        "that works", "perfect", "great", "continue", "next"
    ]
    
    user_lower = user_text.lower().strip()
    is_continuation = len(user_text) < 100 and any(
        user_lower.startswith(cont) or user_lower == cont
        for cont in short_continuations
    )
    
    if not is_continuation:
        return user_text
    
    # This is a continuation - find the original task from conversation history
    # Look for the most recent substantial user message
    for msg in reversed(messages[:-1]):  # Skip current message
        if msg.get("role") != "user":
            continue
        
        content = msg.get("content", "")
        if isinstance(content, list):
            # Extract text from multi-part content
            texts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"]
            content = " ".join(texts)
        
        if not isinstance(content, str):
            continue
            
        # Skip short messages that are also continuations
        if len(content) < 50:
            continue
            
        # Skip messages that look like injected context
        if content.startswith("### ") or "End Workspace Files" in content:
            continue
        
        # Found the original task
        print(f"[aj] Continuation detected - using original task: {content[:100]}...")
        return f"User originally asked: {content}\n\nUser now confirms: {user_text}"
    
    # Fallback to current text if no original task found
    return user_text


def _is_json_plan_content(content: str) -> bool:
    """
    Detect if content is raw JSON planning output that should be formatted.
    
    Returns True for:
    - JSON plan arrays with "step" and "action" fields
    - JSON objects with "requires_confirmation"
    - "Follow up" suggestion blocks
    """
    if not content:
        return False
    
    # Check for plan step patterns
    if '"step":' in content and '"action":' in content:
        return True
    
    # Check for confirmation patterns
    if '"requires_confirmation":' in content:
        return True
    
    # Check for follow-up blocks
    if content.strip().startswith('Follow up'):
        return True
    
    return False


def _format_json_plan_as_blockquote(content: str) -> str:
    """
    Convert raw JSON plan output into readable blockquote format.
    
    Input: {"step": 1, "action": "..."}, {"step": 2, "action": "..."}
    Output: > 1. First action
            > 2. Second action
    """
    import re
    
    # Try to extract steps from JSON
    steps = []
    
    # Pattern to match {"step": N, "action": "text"}
    step_pattern = r'\{\s*"step"\s*:\s*(\d+)\s*,\s*"action"\s*:\s*"([^"]+)"\s*\}'
    matches = re.findall(step_pattern, content)
    
    if matches:
        for step_num, action in matches:
            steps.append(f"> {step_num}. {action}")
    
    if steps:
        # Return formatted blockquote
        return "\n".join(steps) + "\n"
    
    # If no steps found, return empty (will be filtered)
    return ""


async def _orchestrate_task(
    user_id: str,
    messages: List[dict],
    workspace_root: Optional[str],
    __event_emitter__,
    memory_context: Optional[List[dict]] = None,
    model: Optional[str] = None,
) -> Tuple[Optional[str], str]:
    """
    Handle task intents via orchestrator streaming endpoint.
    
    Flow:
      1. POST /run-task to orchestrator (starts SSE stream)
      2. Forward status events to __event_emitter__
      3. Return (final_context, streamed_content) when complete
    
    The agentic loop now runs in the orchestrator, not here.
    Returns both the context for LLM and the accumulated streamed content
    to preserve thinking/results in the final response.
    """
    if not workspace_root:
        return None, ""
    
    # Build complete task description (handles continuations)
    user_text = _build_task_description(messages)
    
    # Accumulate all streamed content so it persists after LLM responds
    streamed_content = ""
    
    try:
        # Note: Don't emit "Thinking" here - orchestrator will emit it and we forward
        
        # Stream task execution from orchestrator
        import httpx
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=10.0)) as client:
            async with client.stream(
                "POST",
                f"{ORCHESTRATOR_API_URL}/api/orchestrate/run-task",
                json={
                    "task": user_text,
                    "workspace_root": workspace_root,
                    "user_id": user_id,
                    "memory_context": memory_context,
                    "max_steps": 100,
                    "preserve_state": True,  # Always preserve state for multi-turn conversations
                    "model": model,  # Pass selected model from Open-WebUI
                },
            ) as response:
                final_context = None
                plan_shown = False  # Track if we already showed the plan
                
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    
                    try:
                        event = json.loads(line[6:])  # Strip "data: " prefix
                    except json.JSONDecodeError:
                        continue
                    
                    event_type = event.get("event_type", "")
                    status = event.get("status", "")
                    done = event.get("done", False)
                    
                    # Forward status events to UI (these don't accumulate in message)
                    if event_type == "status" and status:
                        await __event_emitter__(
                            create_status_dict(status, LogCategory.FILTER, LogLevel.RUNNING, done=done)
                        )
                    
                    elif event_type == "plan":
                        # Stream formatted plan as blockquote (only once)
                        content = event.get("content", "")
                        if content and not plan_shown:
                            # Content already has "📋 Task Plan:" header from orchestrator
                            # Just wrap in blockquote without adding another header
                            lines = [f"> {line}" for line in content.split("\n") if line.strip()]
                            plan_block = "\n".join(lines) + "\n\n"
                            streamed_content += plan_block
                            await __event_emitter__({
                                "type": "message",
                                "data": {"content": plan_block}
                            })
                            plan_shown = True
                    
                    elif event_type == "thinking":
                        # Stream thinking content to the message AND accumulate
                        content = event.get("content", "")
                        if content:
                            # Skip if this is the plan content (already shown via plan event)
                            if plan_shown and ("Task Plan" in content or "📋" in content):
                                continue
                            
                            # Check for JSON plan output - format it nicely instead of raw JSON
                            if _is_json_plan_content(content):
                                formatted = _format_json_plan_as_blockquote(content)
                                if formatted:
                                    streamed_content += formatted
                                    await __event_emitter__({
                                        "type": "message",
                                        "data": {"content": formatted}
                                    })
                                # Skip raw JSON that couldn't be formatted
                                continue
                            
                            # Skip orphaned blockquote prefixes from orchestrator
                            if content.strip() in ("> 💭", "> 💭 ", "💭"):
                                continue
                            
                            streamed_content += content
                            await __event_emitter__({
                                "type": "message",
                                "data": {"content": content}
                            })
                    
                    elif event_type == "result":
                        # Stream tool output in a code block
                        tool = event.get("tool", "")
                        result = event.get("result", {})
                        output = result.get("output_preview", "")
                        
                        if output:
                            # Format output as a fenced code block with tool context
                            tool_labels = {
                                "scan_workspace": "Directory listing",
                                "read_file": "File content",
                                "execute_shell": "Command output",
                            }
                            label = tool_labels.get(tool, f"{tool} output")
                            
                            # Stream the code block AND accumulate
                            code_block = f"\n\n**{label}:**\n```\n{output}\n```\n"
                            streamed_content += code_block
                            await __event_emitter__({
                                "type": "message",
                                "data": {"content": code_block}
                            })
                    
                    elif event_type == "error":
                        await __event_emitter__(
                            create_error_dict(status, LogCategory.FILTER, done=done)
                        )
                    
                    elif event_type == "complete":
                        result = event.get("result", {})
                        final_context = result.get("context")
                        # Emit final completion status
                        complete_status = event.get("status", "Done")
                        await __event_emitter__(
                            create_status_dict(complete_status, LogCategory.FILTER, LogLevel.SUCCESS, done=True)
                        )
                
                return final_context, streamed_content
                
    except Exception as e:
        print(f"[aj] Orchestrator streaming error: {e}")
        await __event_emitter__(
            create_error_dict(str(e)[:30], LogCategory.FILTER, done=True)
        )
        return None, ""


# ============================================================================
# Content Extraction Layer
# ============================================================================

def _extract_all_content_batch(
    body: dict,
    messages: List[dict],
    user_prompt: Optional[str] = None
) -> Tuple[str, List[str], List[dict]]:
    """
    Extract and chunk all files + images in a SINGLE batch request.
    
    Consolidates what was previously multiple HTTP calls into one.
    
    Returns:
        Tuple of (file_content_text, filenames, all_chunks)
    """
    batch_items = []
    filenames = []
    
    # Collect files from body
    files = body.get("files") or []
    if not files:
        files = body.get("metadata", {}).get("files") or []
    
    for file_info in files:
        try:
            if not isinstance(file_info, dict):
                continue
            
            file_data = file_info.get("file", file_info)
            file_path = file_data.get("path")
            filename = file_data.get("filename", file_data.get("name", "unknown"))
            
            if not file_path or not os.path.exists(file_path):
                continue
            
            with open(file_path, "rb") as f:
                content = f.read()
            
            ext = os.path.splitext(filename)[1].lower()
            content_type = CONTENT_TYPE_MAP.get(ext, "text/plain")
            
            if content_type.startswith("text/") or content_type == "application/json":
                content_str = content.decode("utf-8", errors="ignore")
            else:
                content_str = base64.b64encode(content).decode("utf-8")
            
            batch_items.append({
                "content": content_str,
                "content_type": content_type,
                "source_name": filename,
                "source_type": "file",
            })
            filenames.append(filename)
            
        except Exception as e:
            print(f"[aj] Error preparing file for batch: {e}")
            continue
    
    # Collect images from messages
    for msg in messages:
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        
        for idx, item in enumerate(content):
            if not isinstance(item, dict) or item.get("type") != "image_url":
                continue
            
            image_url = item.get("image_url", {})
            url = image_url.get("url", "") if isinstance(image_url, dict) else image_url
            
            if not url:
                continue
            
            content_type, image_data = _load_image_url(url)
            if content_type and image_data:
                batch_items.append({
                    "content": image_data,
                    "content_type": content_type,
                    "source_name": f"image_{idx}",
                    "source_type": "image",
                })
    
    # No content to extract
    if not batch_items:
        return "", [], []
    
    # Single batch call to extractor
    try:
        resp = requests.post(
            f"{EXTRACTOR_API_URL}/api/extract/batch",
            json={
                "items": batch_items,
                "chunk_size": 500,
                "chunk_overlap": 50,
                "prompt": user_prompt,
            },
            timeout=120,
        )
        resp.raise_for_status()
        result = resp.json()
        
        all_chunks = []
        file_contents = []
        
        for i, extract_result in enumerate(result.get("results", [])):
            source_name = batch_items[i].get("source_name", "unknown")
            source_type = batch_items[i].get("source_type", "file")
            
            chunks = extract_result.get("chunks", [])
            for chunk in chunks:
                chunk["source_name"] = source_name
                chunk["source_type"] = source_type
                all_chunks.append(chunk)
            
            # Build text summary for files (first 3 chunks)
            if source_type == "file" and chunks:
                chunk_texts = [c.get("content", "") for c in chunks[:3]]
                file_contents.append(
                    f"[Document: {source_name}]\n" + "\n\n".join(chunk_texts)
                )
        
        return "\n\n".join(file_contents), filenames, all_chunks
        
    except Exception as e:
        print(f"[aj] Batch extraction error: {e}")
        return "", filenames, []


def _extract_images_from_messages(
    messages: List[dict],
    user_prompt: Optional[str] = None
) -> List[dict]:
    """
    Extract image URLs from message content and generate descriptions.
    DEPRECATED: Use _extract_all_content_batch instead.
    Kept for backwards compatibility.
    """
    image_chunks = []
    
    for msg in messages:
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        
        for idx, item in enumerate(content):
            if not isinstance(item, dict):
                continue
            if item.get("type") != "image_url":
                continue
            
            image_url = item.get("image_url", {})
            if isinstance(image_url, str):
                url = image_url
            else:
                url = image_url.get("url", "")
            
            if not url:
                continue
            
            try:
                content_type, image_data = _load_image_url(url)
                if not content_type or not image_data:
                    continue
                
                chunks = _call_extractor(
                    content=image_data,
                    content_type=content_type,
                    source_name=f"image_{idx}",
                    prompt=user_prompt,
                    overlap=0,
                )
                
                for chunk in chunks:
                    chunk["source_type"] = "image"
                    chunk["source_name"] = f"uploaded_image_{idx}"
                    image_chunks.append(chunk)
                
            except Exception as e:
                print(f"[aj] Image {idx} error: {e}")
                continue
    
    return image_chunks


def _load_image_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Load image from various sources (data URL, HTTP, local file)."""
    
    if url.startswith("data:"):
        match = re.match(r'data:([^;]+);base64,(.+)', url)
        if match:
            return match.group(1), match.group(2)
        return None, None
    
    if url.startswith("http"):
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "image/png")
            image_data = base64.b64encode(resp.content).decode("utf-8")
            return content_type, image_data
        except Exception as e:
            print(f"[aj] Failed to fetch {url}: {e}")
            return None, None
    
    if os.path.exists(url):
        try:
            with open(url, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            ext = os.path.splitext(url)[1].lower()
            content_type = CONTENT_TYPE_MAP.get(ext, "image/png")
            return content_type, image_data
        except Exception as e:
            print(f"[aj] Failed to read {url}: {e}")
            return None, None
    
    return None, None


def _extract_and_chunk_file(file_path: str, filename: str) -> List[dict]:
    """Extract text from file and split into chunks."""
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        
        ext = os.path.splitext(filename)[1].lower()
        content_type = CONTENT_TYPE_MAP.get(ext, "text/plain")
        
        if content_type.startswith("text/") or content_type == "application/json":
            content_str = content.decode("utf-8", errors="ignore")
        else:
            content_str = base64.b64encode(content).decode("utf-8")
        
        chunks = _call_extractor(
            content=content_str,
            content_type=content_type,
            source_name=filename,
            overlap=50,
        )
        
        return chunks
    
    except Exception as e:
        print(f"[aj] Extractor error for {filename}: {e}")
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return [{"content": f.read(), "chunk_index": 0, "chunk_type": "text"}]
        except Exception:
            return []


def _extract_file_contents(body: dict) -> Tuple[str, List[str], List[dict]]:
    """Extract and chunk all uploaded files from request."""
    file_contents = []
    filenames = []
    all_chunks = []
    
    files = body.get("files") or []
    if not files:
        files = body.get("metadata", {}).get("files") or []
    
    for file_info in files:
        try:
            if not isinstance(file_info, dict):
                continue
            
            file_data = file_info.get("file", file_info)
            file_path = file_data.get("path")
            filename = file_data.get("filename", file_data.get("name", "unknown"))
            
            if not file_path or not os.path.exists(file_path):
                continue
            
            chunks = _extract_and_chunk_file(file_path, filename)
            
            if chunks:
                filenames.append(filename)
                
                for chunk in chunks:
                    chunk["source_name"] = filename
                    all_chunks.append(chunk)
                
                chunk_texts = [c.get("content", "") for c in chunks[:3]]
                file_contents.append(
                    f"[Document: {filename}]\n" + "\n\n".join(chunk_texts)
                )
        
        except Exception as e:
            print(f"[aj] Error processing file: {e}")
            continue
    
    return "\n\n".join(file_contents), filenames, all_chunks


def _call_extractor(
    content: str,
    content_type: str,
    source_name: Optional[str],
    prompt: Optional[str] = None,
    overlap: int = 50,
) -> List[dict]:
    """Call extractor service to chunk content."""
    try:
        resp = requests.post(
            f"{EXTRACTOR_API_URL}/api/extract/",
            json={
                "content": content,
                "content_type": content_type,
                "source_name": source_name,
                "chunk_size": 500,
                "chunk_overlap": overlap,
                "prompt": prompt,
            },
            timeout=120,
        )
        resp.raise_for_status()
        result = resp.json()
        return result.get("chunks", [])
    
    except Exception as e:
        print(f"[aj] Extractor error: {e}")
        return []


# ============================================================================
# Memory Layer
# ============================================================================

async def _save_chunk_to_memory(
    user_id: str,
    chunk: dict,
    model: str,
    metadata: dict,
    source_name: str,
) -> bool:
    """Save a single chunk to memory service."""
    try:
        chunk_content = chunk.get("content", "")
        chunk_idx = chunk.get("chunk_index", 0)
        section = chunk.get("section_title", "")
        chunk_type = chunk.get("source_type", "document_chunk")
        
        if not chunk_content.strip():
            return False
        
        payload = {
            "user_id": user_id,
            "messages": [{"role": "user", "content": chunk_content}],
            "model": model,
            "metadata": {**metadata, "chunk_index": chunk_idx, "section_title": section},
            "source_type": chunk_type,
            "source_name": f"{source_name}#{chunk_idx}" + (f" ({section})" if section else ""),
            "skip_classifier": True,
        }
        
        resp = requests.post(f"{MEMORY_API_URL}/api/memory/save", json=payload, timeout=30)
        return resp.status_code == 200
    
    except Exception as e:
        print(f"[aj] Failed to save chunk: {e}")
        return False


async def _search_memory(
    user_id: str,
    query_text: str,
    top_k: int = 5,
) -> List[dict]:
    """Search memory for relevant context."""
    try:
        payload = {
            "user_id": user_id,
            "query_text": query_text,
            "top_k": top_k,
        }
        
        resp = requests.post(f"{MEMORY_API_URL}/api/memory/search", json=payload, timeout=10)
        
        if resp.status_code == 404:
            # No memories found - not an error
            return []
        
        resp.raise_for_status()
        return resp.json()
    
    except Exception as e:
        print(f"[aj] Search error: {e}")
        return []


async def _save_to_memory(
    user_id: str,
    messages: List[dict],
    source_type: Optional[str] = None,
    source_name: Optional[str] = None,
) -> bool:
    """Save conversation to memory. Returns True if saved successfully."""
    try:
        payload = {
            "user_id": user_id,
            "messages": messages,
            "source_type": source_type,
            "source_name": source_name,
        }
        
        resp = requests.post(f"{MEMORY_API_URL}/api/memory/save", json=payload, timeout=30)
        resp.raise_for_status()
        
        result = resp.json()
        return result.get("status") == "saved"
    
    except Exception as e:
        print(f"[aj] Save error: {e}")
        return False


def _extract_user_text_prompt(messages: List[dict]) -> Optional[str]:
    """Extract user's text prompt from last user message."""
    if not messages:
        return None
    
    for msg in reversed(messages):
        if msg.get("role") != "user":
            continue
        
        content = msg.get("content")
        if isinstance(content, str):
            return content
        
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            return " ".join(text_parts) if text_parts else None
    
    return None


# ============================================================================
# Context Formatting
# ============================================================================

def _format_source(ctx: dict) -> str:
    """Format a memory source as a brief status line with icon."""
    source_type = ctx.get("source_type")
    source_name = ctx.get("source_name")
    
    if source_type == "document" and source_name:
        return f"📄 {source_name}"
    
    if source_type == "url" and source_name:
        display = (source_name[:30] + "...") if len(source_name) > 30 else source_name
        return f"🔗 {display}"
    
    if source_type == "image":
        return f"🖼 {source_name or 'image'}"
    
    if source_type == "prompt" and source_name:
        snippet = source_name[:40].replace("\n", " ")
        if len(source_name) > 40:
            snippet += "..."
        return f'💬 "{snippet}"'
    
    user_text = ctx.get("user_text", "")
    if user_text:
        snippet = user_text[:60].replace("\n", " ")
        if len(user_text) > 60:
            snippet += "..."
        return f'💬 "{snippet}"'
    
    return "📝 memory"


# ============================================================================
# Filter Plugin Class
# ============================================================================

class Filter:
    """
    AJ - Agentic Assistant Filter for Open-WebUI.
    
    Provides:
      - Intent classification (recall, save, task, casual)
      - Multi-step reasoning via orchestrator
      - Code execution via executor
      - Semantic memory retrieval and storage
      - Document/image extraction
    """
    
    class UserValves(BaseModel):
        """User configuration for AJ."""
        enable_orchestrator: bool = Field(
            default=True,
            description="Enable multi-step reasoning for task intents"
        )
        enable_code_execution: bool = Field(
            default=False,
            description="Allow code execution (requires explicit enable)"
        )
        max_context_items: int = Field(
            default=5,
            description="Maximum memory items to inject as context"
        )
        workspace_root: str = Field(
            default="/workspace/aj.westerfield.cloud",
            description="Workspace root inside container (e.g., /workspace/myproject). "
                        "Maps to HOST_WORKSPACE_PATH on host machine."
        )
        host_workspace_hint: str = Field(
            default="C:/Code",
            description="Display hint: what HOST_WORKSPACE_PATH is set to on host. "
                        "This is informational only - actual mapping is in docker-compose."
        )
    
    def __init__(self):
        """Initialize AJ filter."""
        self.user_valves = self.UserValves()
        self.toggle = True
        # Track streamed content from orchestrator to preserve in final response
        self._streamed_content = ""
        # Butler icon - person with bow tie silhouette
        self.icon = (
            "data:image/svg+xml;base64,"
            "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iY3VycmVudENvbG9yIj4KICA8IS0tIEhlYWQgLS0+CiAgPGNpcmNsZSBjeD0iMTIiIGN5PSI2IiByPSIzLjUiLz4KICA8IS0tIEJvdyB0aWUgLS0+CiAgPHBhdGggZD0iTTkgMTJsLTIgMS41TDkgMTVoNmwyLTEuNUwxNSAxMkg5eiIvPgogIDwhLS0gQm9keSAtLT4KICA8cGF0aCBkPSJNNiAxNWMwLTEgMS41LTIgNi0yIDQuNSAwIDYgMSA2IDJ2NmMwIC41LS41IDEtMSAxSDdjLS41IDAtMS0uNS0xLTF2LTZ6Ii8+Cjwvc3ZnPgo="
        )
    
    def _inject_context(self, body: dict, context_items: List[dict], orchestrator_context: Optional[str] = None) -> dict:
        """Inject system prompt, retrieved memories, and orchestrator analysis into conversation."""
        messages = body.get("messages", [])
        
        # Inject AJ system prompt if not already present
        has_aj_system = any(
            m.get("role") == "system" and "AJ" in m.get("content", "")
            for m in messages
        )
        
        if not has_aj_system:
            # Add AJ system prompt at the beginning
            aj_system = {
                "role": "system",
                "content": AJ_SYSTEM_PROMPT
            }
            # Insert after any existing system messages, or at start
            insert_idx = 0
            for i, m in enumerate(messages):
                if m.get("role") == "system":
                    insert_idx = i + 1
                else:
                    break
            messages.insert(insert_idx, aj_system)
        
        if not context_items and not orchestrator_context:
            body["messages"] = messages
            return body
        
        # Build context block
        context_lines = []
        
        # Add orchestrator analysis first
        if orchestrator_context:
            context_lines.append(orchestrator_context)
        
        # Add memory context
        if context_items:
            context_lines.append("### Retrieved Memories ###")
            for ctx in context_items[:self.user_valves.max_context_items]:
                user_text = ctx.get("user_text")
                if user_text:
                    context_lines.append(f"- {user_text}")
            context_lines.append("### End Memories ###\n")
        
        if not context_lines:
            body["messages"] = messages
            return body
        
        context_block = "\n".join(context_lines) + "\n"
        
        # Find last user message and prepend context
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "user":
                content = messages[i].get("content", "")
                
                if isinstance(content, str):
                    messages[i]["content"] = context_block + content
                elif isinstance(content, list):
                    messages[i]["content"] = (
                        [{"type": "text", "text": context_block}] + content
                    )
                break
        
        body["messages"] = messages
        return body
    
    async def inlet(
        self,
        body: dict,
        __event_emitter__,
        __user__: Optional[dict] = None
    ) -> dict:
        """
        Main filter entry point.
        
        Process:
          1. Extract uploaded files/images
          2. Classify intent
          3. For tasks: engage orchestrator
          4. Search/save to memory
          5. Inject context
        """
        try:
            user_id = __user__["id"] if __user__ and "id" in __user__ else "anonymous"
            messages = body.get("messages", [])
            model = body.get("model", "unknown")
            metadata = body.get("metadata", {})
            
            if not messages or not isinstance(messages, list):
                return body
            
            await __event_emitter__(
                create_status_dict("Thinking", LogCategory.FILTER, LogLevel.THINKING)
            )
            
            # Extract user text for classification
            user_text = _extract_user_text_prompt(messages)
            
            # Extract files and images in a SINGLE batch call
            file_content, filenames, chunks = _extract_all_content_batch(
                body, messages, user_prompt=user_text
            )
            
            # Build immediate image context for injection
            immediate_image_context = [
                {
                    "user_text": f"[Image]: {chunk.get('content', '')}",
                    "source_type": "image",
                    "source_name": chunk.get("source_name", "image"),
                }
                for chunk in chunks
                if chunk.get("source_type") == "image" and chunk.get("content")
            ]
            
            # Save document chunks
            chunks_saved = 0
            if chunks:
                await __event_emitter__(
                    create_status_dict(
                        f"Saving {len(chunks)} chunk(s)",
                        LogCategory.MEMORY,
                        LogLevel.PROCESSING
                    )
                )
                
                source_name = filenames[0] if filenames else "attachment"
                for chunk in chunks:
                    if await _save_chunk_to_memory(
                        user_id, chunk, model, metadata, source_name
                    ):
                        chunks_saved += 1
            
            # Classify intent FIRST - this determines if we save
            orchestrator_context = None
            intent_result = {"intent": "casual", "confidence": 0.5}
            intent = "casual"
            
            if user_text:
                intent_result = _classify_intent(user_text)
                intent = intent_result.get("intent", "casual")
                confidence = intent_result.get("confidence", 0.5)
                
                # SMART TASK CONTINUATION DETECTION
                # Check if user is confirming/continuing a previous task proposal
                if intent == "casual":
                    should_upgrade = _detect_task_continuation(user_text, messages, confidence)
                    if should_upgrade:
                        print(f"[aj] Upgrading intent from casual to task (continuation detected)")
                        intent = "task"
            
            # Search memory for context (needed for tasks and recall)
            context = []
            if user_text:
                search_results = await _search_memory(user_id, user_text)
                # Convert search results to context format
                context = [
                    {
                        "user_text": r.get("user_text", ""),
                        "score": r.get("score", 0),
                        "source_type": r.get("source_type", "prompt"),
                        "source_name": r.get("source_name"),
                    }
                    for r in search_results
                ]
            
            # SAVE based on intent classification
            saved = False
            if intent == "save" and user_text:
                await __event_emitter__(
                    create_status_dict("Saving to memory...", LogCategory.MEMORY, LogLevel.PROCESSING)
                )
                saved = await _save_to_memory(
                    user_id,
                    messages,
                    source_type="prompt",
                    source_name=user_text[:50] if len(user_text) > 50 else user_text,
                )
                if saved:
                    print(f"[aj] Saved memory for user={user_id}")
            
            # For task intents, engage orchestrator (pass memory context for user info)
            if intent == "task" and self.user_valves.enable_orchestrator:
                orchestrator_context, streamed = await _orchestrate_task(
                    user_id,
                    messages,
                    self.user_valves.workspace_root if self.user_valves.workspace_root else None,
                    __event_emitter__,
                    memory_context=context,  # Pass user context (name, preferences)
                    model=model,  # Pass selected model from Open-WebUI
                )
                # Store streamed content to prepend to LLM response in outlet
                self._streamed_content = streamed
            
            # Merge immediate image context
            if immediate_image_context:
                context = immediate_image_context + context
            
            # Determine if we have context to inject
            has_context = bool(context) or bool(orchestrator_context)
            
            # Emit status and inject
            # Note: orchestrator already emitted completion status, so skip for tasks
            if has_context:
                memory_count = len(context) if context else 0
                
                if memory_count > 0:
                    await __event_emitter__(
                        create_status_dict(
                            f"Found {memory_count} memories",
                            LogCategory.MEMORY,
                            LogLevel.CONTEXT
                        )
                    )
                
                # Only emit Ready if we didn't go through orchestrator
                if not orchestrator_context:
                    await __event_emitter__(
                        create_status_dict("Ready", LogCategory.FILTER, LogLevel.READY, done=True)
                    )
                
                body = self._inject_context(body, context or [], orchestrator_context)
            
            elif saved:
                await __event_emitter__(
                    create_status_dict("Saved", LogCategory.FILTER, LogLevel.SAVED, done=True)
                )
            
            else:
                await __event_emitter__(
                    create_status_dict("Ready", LogCategory.FILTER, LogLevel.READY, done=True, hidden=True)
                )
            
            print(f"[aj] user={user_id} intent={intent} saved={saved} context={len(context or [])} chunks={chunks_saved}")
            return body
        
        except Exception as e:
            print(f"[aj] Error: {e}")
            
            await __event_emitter__(
                create_error_dict(str(e)[:40], LogCategory.FILTER, done=True)
            )
            
            return body
    
    async def outlet(self, body: dict, __event_emitter__, __user__: Optional[dict] = None) -> dict:
        """
        Post-response hook. Formats assistant responses for consistency.
        
        Ensures:
        - JSON structured responses are extracted to just the "response" field
        - Streamed thinking/results are preserved before LLM response
        - File/folder names are in `backticks`
        - Code references are in `backticks`
        - Lists and code blocks use fenced markdown
        """
        messages = body.get("messages", [])
        if not messages:
            return body
        
        # Find last assistant message and process it
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "assistant":
                content = messages[i].get("content", "")
                if isinstance(content, str):
                    # FIRST: Extract response from JSON structured output
                    content = self._extract_json_response(content)
                    
                    # Prepend any streamed thinking/results from orchestrator
                    if self._streamed_content:
                        # Clean streamed content - remove raw JSON planning output
                        cleaned_streamed = self._clean_streamed_content(self._streamed_content)
                        if cleaned_streamed.strip():
                            # Add separator between streamed content and LLM response
                            content = cleaned_streamed + "\n\n---\n\n" + content
                        # Clear for next request
                        self._streamed_content = ""
                    messages[i]["content"] = self._format_response(content)
                break
        
        body["messages"] = messages
        return body
    
    def _clean_streamed_content(self, text: str) -> str:
        """
        Clean streamed content from orchestrator, formatting raw JSON plans.
        
        Keeps:
        - Tool output in code blocks
        - Natural language thinking
        - Formatted plans (converted from JSON)
        
        Converts:
        - Raw JSON plan objects → numbered blockquote steps
        
        Removes:
        - Follow-up suggestion blocks
        - Orphaned JSON fragments
        """
        import re
        
        if not text:
            return text
        
        # First, try to extract and format any JSON plans
        # Pattern to match {"step": N, "action": "text"}
        step_pattern = r'\{\s*"step"\s*:\s*(\d+)\s*,\s*"action"\s*:\s*"([^"]+)"\s*\}'
        matches = re.findall(step_pattern, text)
        
        if matches:
            # Format matched steps into blockquotes
            formatted_steps = []
            for step_num, action in matches:
                formatted_steps.append(f"> {step_num}. {action}")
            
            # Remove the raw JSON and add formatted version
            text = re.sub(r'\{\s*"step"\s*:\s*\d+\s*,\s*"action"\s*:\s*"[^"]*"\s*\}[,\s]*', '', text)
            
            # If we had steps, prepend the formatted plan
            if formatted_steps and not any(f"> {s[0]}." in text for s in matches):
                text = "> 💭 **Plan:**\n" + "\n".join(formatted_steps) + "\n\n" + text
        
        # Remove plan arrays (already extracted content above)
        plan_array_pattern = r'\[\s*\{\s*"step"\s*:.*?\}\s*\]'
        text = re.sub(plan_array_pattern, '', text, flags=re.DOTALL)
        
        # Remove "requires_confirmation" JSON fragments
        text = re.sub(r'"requires_confirmation"\s*:\s*(true|false)\s*\}?', '', text)
        
        # Remove "Follow up" sections with suggestions
        text = re.sub(r'Follow up\s*\n.*?(?=\n\n|\Z)', '', text, flags=re.DOTALL)
        
        # Remove orphaned JSON-like fragments
        text = re.sub(r'\{\s*\}', '', text)  # Empty braces
        text = re.sub(r'\[\s*\]', '', text)  # Empty brackets
        text = re.sub(r'^\s*\],?\s*$', '', text, flags=re.MULTILINE)  # Orphaned array close
        text = re.sub(r'^\s*\},?\s*$', '', text, flags=re.MULTILINE)  # Orphaned object close
        text = re.sub(r'"action"\s*:\s*"[^"]*"', '', text)  # Orphaned action fields
        
        # Clean up excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        
        return text
    
    def _extract_json_response(self, text: str) -> str:
        """
        Extract the 'response' field from JSON structured output.
        
        If the LLM outputs structured JSON like:
        {"action": "casual", "response": "Hi there!", "guardrail_context": "..."}
        
        This extracts just the "response" field value.
        """
        import re
        
        # Skip if empty or doesn't look like JSON
        if not text or not text.strip().startswith('{'):
            return text
        
        try:
            # Try to parse as JSON
            data = json.loads(text.strip())
            
            # Check if it has a response field
            if isinstance(data, dict) and "response" in data:
                response = data["response"]
                
                # Optionally show guardrail context as a status-like prefix
                # (commented out for now - just return the response)
                # guardrail = data.get("guardrail_context", "")
                
                return response
            
            # Not our structured format, return as-is
            return text
            
        except json.JSONDecodeError:
            # Not valid JSON, might be partial or mixed content
            # Try to extract response field with regex as fallback
            match = re.search(r'"response"\s*:\s*"((?:[^"\\]|\\.)*)"\s*[,}]', text)
            if match:
                # Unescape the JSON string
                try:
                    return json.loads('"' + match.group(1) + '"')
                except:
                    return match.group(1)
            
            return text
    
    def _format_response(self, text: str) -> str:
        """
        Format response text for better markdown rendering.
        
        - Remove leaked tool call syntax (LLM hallucinations)
        - Remove raw JSON tool calls that leaked through
        - Wrap file/folder names in backticks
        - Wrap code references in backticks
        - Ensure code blocks are fenced
        """
        import re
        
        # Skip if empty
        if not text:
            return text
        
        # SANITIZATION: Remove raw JSON tool calls that leaked through
        # Pattern matches {"tool": "...", ...} or {"action": "...", ...} JSON objects
        json_tool_pattern = r'\{\s*"(?:tool|action)":\s*"[^"]+"\s*,\s*(?:"[^"]+"\s*:\s*(?:"[^"]*"|[^,}]+)\s*,?\s*)+\}'
        if '"tool":' in text or '"action":' in text:
            text = re.sub(json_tool_pattern, '', text, flags=re.DOTALL)
            # Clean up multiple newlines
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = text.strip()
        
        # SANITIZATION: Remove any leaked tool call syntax
        # Some models output [TOOL_CALLS] when they shouldn't
        tool_call_pattern = r'\[TOOL_CALLS\][^\[]*(?:\[ARGS\][^\[]*)?'
        if '[TOOL_CALLS]' in text:
            text = re.sub(tool_call_pattern, '', text)
            # Clean up any orphaned text that looks like tool calls
            text = re.sub(r'\{"file_path":\s*"[^"]*"\}', '', text)
            text = re.sub(r'\{"path":\s*"[^"]*"\}', '', text)
            # Remove multiple newlines created by cleanup
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = text.strip()
            # If we removed everything, provide a fallback
            if not text or len(text) < 20:
                text = "I'll help you with that task. Let me process the files in your workspace."
        
        # Skip further formatting if already well-formatted
        if text.startswith("```"):
            return text
        
        # Pattern for file paths and names (with extensions or path separators)
        # Match paths like: file.py, /path/to/file, ./folder, layers/executor/main.py
        file_pattern = r'(?<![`\w])([./\\]?[\w\-]+(?:[/\\][\w\-\.]+)+\.?\w*|[\w\-]+\.\w{1,10})(?![`\w])'
        
        def wrap_if_not_wrapped(match):
            path = match.group(1)
            # Don't wrap if it looks like a URL or already wrapped
            if path.startswith('http') or path.startswith('`'):
                return match.group(0)
            return f'`{path}`'
        
        # Apply file path formatting (but not inside code blocks)
        lines = text.split('\n')
        formatted_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                formatted_lines.append(line)
            elif in_code_block:
                formatted_lines.append(line)
            else:
                # Format file paths outside code blocks
                formatted_line = re.sub(file_pattern, wrap_if_not_wrapped, line)
                formatted_lines.append(formatted_line)
        
        return '\n'.join(formatted_lines)
