"""
Session State Manager - External State Tracking

Maintains ground-truth state from actual tool outputs rather than
asking the LLM to track state (which causes drift/hallucination).

The orchestrator updates this after each tool execution, then
injects it as context into the LLM prompt.

OODA Loop Architecture:
- CommandFlowContext: Queryable history of command/result/timestamp (token-efficient)
- TaskPlan: Current plan with status tracking
- Replanning: After each task, check if goal is satisfied or replanning needed
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
import re
import logging

logger = logging.getLogger("orchestrator.session_state")


# =============================================================================
# Command Flow Context - Queryable History (Token-Efficient)
# =============================================================================


@dataclass
class CommandFlowEntry:
    """
    A single command execution record.

    Designed for queryability - not fed wholesale into LLM prompts.
    Query methods filter and summarize as needed.
    """

    timestamp: datetime
    step_index: int  # 1-based step number
    agent_id: Optional[str]  # Which agent executed (None for non-execute tools)
    tool: str  # execute, think, complete
    command: Optional[str]  # The actual command (for execute)
    success: bool
    output_preview: str  # First 200 chars of output
    output_hash: str  # Hash for dedup detection
    output_size: int  # Full output size in bytes
    error: Optional[str]
    duration_ms: Optional[int]  # Execution duration

    # Tags for queryability
    tags: List[str] = field(default_factory=list)  # e.g., ["disk", "network", "ad"]


@dataclass
class CommandFlowContext:
    """
    Queryable command flow history.

    NOT fed wholesale into LLM - instead, query methods return
    relevant summaries to minimize token usage.
    """

    entries: List[CommandFlowEntry] = field(default_factory=list)
    original_goal: str = ""  # The user's original request

    def add_entry(
        self,
        step_index: int,
        tool: str,
        success: bool,
        output: str,
        agent_id: Optional[str] = None,
        command: Optional[str] = None,
        error: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> CommandFlowEntry:
        """Add a command execution to the flow."""
        import hashlib

        entry = CommandFlowEntry(
            timestamp=datetime.utcnow(),
            step_index=step_index,
            agent_id=agent_id,
            tool=tool,
            command=command,
            success=success,
            output_preview=output[:200] if output else "",
            output_hash=hashlib.md5(output.encode()).hexdigest()[:8] if output else "",
            output_size=len(output) if output else 0,
            error=error,
            duration_ms=duration_ms,
            tags=self._extract_tags(tool, command, output),
        )
        self.entries.append(entry)
        return entry

    def _extract_tags(
        self, tool: str, command: Optional[str], output: str
    ) -> List[str]:
        """Tag entries based on tool used. No keyword matching."""
        # Only tag by the tool - no keyword/regex analysis
        return [tool]

    def query_by_agent(self, agent_id: str) -> List[CommandFlowEntry]:
        """Get all commands executed on a specific agent."""
        return [e for e in self.entries if e.agent_id == agent_id]

    def query_by_tag(self, tag: str) -> List[CommandFlowEntry]:
        """Get all commands with a specific tag."""
        return [e for e in self.entries if tag in e.tags]

    def query_failures(self) -> List[CommandFlowEntry]:
        """Get all failed commands."""
        return [e for e in self.entries if not e.success]

    def query_recent(self, n: int = 5) -> List[CommandFlowEntry]:
        """Get the N most recent entries."""
        return self.entries[-n:] if self.entries else []

    def get_agents_queried(self) -> List[str]:
        """Get list of agents that have been queried."""
        return list(set(e.agent_id for e in self.entries if e.agent_id))

    def has_executed_on(self, agent_id: str) -> bool:
        """Check if we've executed anything on this agent."""
        return any(e.agent_id == agent_id and e.tool == "execute" for e in self.entries)

    def summarize_for_replan(self) -> str:
        """
        Generate a compact summary for replanning decisions.
        This IS fed to LLM, but only when replanning is needed.
        """
        if not self.entries:
            return "No commands executed yet."

        lines = [f"Original goal: {self.original_goal}"]
        lines.append(f"Steps executed: {len(self.entries)}")

        # Group by agent
        by_agent: Dict[str, List[CommandFlowEntry]] = {}
        for e in self.entries:
            key = e.agent_id or "system"
            by_agent.setdefault(key, []).append(e)

        for agent, entries in by_agent.items():
            success_count = sum(1 for e in entries if e.success)
            fail_count = len(entries) - success_count
            lines.append(f"  {agent}: {success_count} ok, {fail_count} failed")

        # Recent failures
        failures = self.query_failures()[-3:]
        if failures:
            lines.append("Recent failures:")
            for f in failures:
                lines.append(f"  - Step {f.step_index}: {f.error or 'unknown error'}")

        return "\n".join(lines)

    def format_step_summary(self, entry: CommandFlowEntry) -> str:
        """Format a single entry as a one-line summary."""
        ts = entry.timestamp.strftime("%H:%M:%S")
        if entry.tool == "execute":
            cmd_short = (entry.command or "")[:40]
            status = "✓" if entry.success else "✗"
            return f"[{ts}] {status} {entry.agent_id}: {cmd_short}"
        else:
            return f"[{ts}] {entry.tool}"


@dataclass
class LedgerEntry:
    """A single entry in the conversation ledger."""

    timestamp: str
    entry_type: str  # "request", "action", "result", "extracted"
    summary: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class ConversationLedger:
    """
    Running ledger of the entire conversation/session.

    Tracks user requests, actions taken, important extracted values,
    and provides a quick-reference summary for the LLM.
    """

    # User requests made this session
    user_requests: List[str] = field(default_factory=list)

    # Important values extracted from outputs (IPs, URLs, paths, credentials, etc.)
    extracted_values: Dict[str, str] = field(default_factory=dict)

    # Chronological log of all entries
    entries: List[LedgerEntry] = field(default_factory=list)

    # Running summary (regenerated periodically)
    session_summary: str = ""

    def add_request(self, request: str) -> None:
        """Log a user request."""
        self.user_requests.append(request)
        self.entries.append(
            LedgerEntry(
                timestamp=datetime.utcnow().strftime("%H:%M:%S"),
                entry_type="request",
                summary=request[:100] + "..." if len(request) > 100 else request,
            )
        )
        # Keep only last 20 requests
        if len(self.user_requests) > 20:
            self.user_requests = self.user_requests[-20:]

    def add_action(self, tool: str, params_summary: str, result_summary: str) -> None:
        """Log an action taken."""
        self.entries.append(
            LedgerEntry(
                timestamp=datetime.utcnow().strftime("%H:%M:%S"),
                entry_type="action",
                summary=f"{tool}: {params_summary}",
                details={"result": result_summary},
            )
        )
        # Keep only last 50 entries
        if len(self.entries) > 50:
            self.entries = self.entries[-50:]

    def extract_value(self, key: str, value: str, source: str = "") -> None:
        """Store an important extracted value for quick reference."""
        self.extracted_values[key] = value
        self.entries.append(
            LedgerEntry(
                timestamp=datetime.utcnow().strftime("%H:%M:%S"),
                entry_type="extracted",
                summary=f"Found {key}: {value}"
                + (f" (from {source})" if source else ""),
            )
        )

    def format_for_prompt(self) -> str:
        """Format ledger as context for LLM prompt."""
        lines = []

        # Show extracted values first - most useful for quick reference
        if self.extracted_values:
            lines.append("📋 QUICK REFERENCE (extracted from session):")
            for key, value in list(self.extracted_values.items())[-15:]:
                lines.append(f"  • {key}: {value}")
            lines.append("")

        # Show recent user requests
        if self.user_requests:
            lines.append("💬 USER REQUESTS THIS SESSION:")
            for i, req in enumerate(self.user_requests[-5:], 1):
                lines.append(f"  {i}. {req[:80]}{'...' if len(req) > 80 else ''}")
            lines.append("")

        # Show recent actions timeline
        recent_actions = [e for e in self.entries if e.entry_type == "action"][-10:]
        if recent_actions:
            lines.append("⏱️ RECENT ACTIONS:")
            for entry in recent_actions:
                result = entry.details.get("result", "") if entry.details else ""
                result_short = result[:50] + "..." if len(result) > 50 else result
                lines.append(f"  [{entry.timestamp}] {entry.summary}")
                if result_short:
                    lines.append(f"           → {result_short}")
            lines.append("")

        return "\n".join(lines) if lines else ""


@dataclass
class FileMetadata:
    """Metadata about a specific file."""

    path: str
    size_bytes: Optional[int] = None
    size_human: Optional[str] = None
    modified: Optional[str] = None
    line_count: Optional[int] = None
    file_type: Optional[str] = None  # e.g., "python", "markdown", "json"

    def to_summary(self) -> str:
        parts = [self.path]
        if self.size_human:
            parts.append(f"({self.size_human})")
        if self.line_count:
            parts.append(f"{self.line_count} lines")
        return " ".join(parts)


@dataclass
class EnvironmentFacts:
    """
    Facts learned about the environment from command outputs.
    Extracted by analyzing tool results to understand the workspace.
    """

    # Workspace metrics
    total_file_count: Optional[int] = None
    total_dir_count: Optional[int] = None
    total_size_bytes: Optional[int] = None
    total_size_human: Optional[str] = None

    # Project type detection
    project_types: Set[str] = field(default_factory=set)  # e.g., {"python", "docker"}
    frameworks_detected: Set[str] = field(
        default_factory=set
    )  # e.g., {"fastapi", "pytest"}
    package_managers: Set[str] = field(default_factory=set)  # e.g., {"pip", "npm"}

    # Environment observations
    observations: List[str] = field(default_factory=list)  # Free-form learnings

    # System info (from shell commands)
    working_directory: Optional[str] = None
    python_version: Optional[str] = None
    node_version: Optional[str] = None
    git_branch: Optional[str] = None
    docker_running: Optional[bool] = None

    def add_observation(self, fact: str) -> None:
        """Add a unique observation."""
        if fact and fact not in self.observations:
            self.observations.append(fact)
            # Keep only the last 20 observations
            if len(self.observations) > 20:
                self.observations = self.observations[-20:]


@dataclass
class TaskPlanItem:
    """A single item in the task plan."""

    index: int  # 1-based index
    description: str  # What this step will do
    status: str = "pending"  # pending, in_progress, completed, skipped
    tool_hint: Optional[str] = None  # Expected tool (optional)


@dataclass
class TaskPlan:
    """
    Structured plan generated at task start.

    Provides:
    - Clear visibility to user of what will happen
    - Script for LLM to follow
    - Progress tracking
    """

    items: List[TaskPlanItem] = field(default_factory=list)
    original_task: str = ""
    created_at: Optional[str] = None

    def add_item(self, description: str, tool_hint: Optional[str] = None) -> None:
        """Add a plan item."""
        self.items.append(
            TaskPlanItem(
                index=len(self.items) + 1,
                description=description,
                tool_hint=tool_hint,
            )
        )

    def mark_in_progress(self, index: int) -> None:
        """Mark an item as in progress."""
        for item in self.items:
            if item.index == index:
                item.status = "in_progress"
                break

    def mark_completed(self, index: int) -> None:
        """Mark an item as completed."""
        for item in self.items:
            if item.index == index:
                item.status = "completed"
                break

    def mark_skipped(self, index: int, reason: str = "") -> None:
        """Mark an item as skipped."""
        for item in self.items:
            if item.index == index:
                item.status = "skipped"
                if reason:
                    item.description += f" (skipped: {reason})"
                break

    def get_current_item(self) -> Optional[TaskPlanItem]:
        """Get the next pending or in-progress item."""
        for item in self.items:
            if item.status in ("pending", "in_progress"):
                return item
        return None

    def get_progress(self) -> tuple:
        """Return (completed_count, total_count)."""
        completed = sum(1 for i in self.items if i.status in ("completed", "skipped"))
        return completed, len(self.items)

    def is_complete(self) -> bool:
        """Check if all items are done."""
        return all(i.status in ("completed", "skipped") for i in self.items)

    def format_for_display(self) -> str:
        """Format plan for user display (markdown)."""
        if not self.items:
            return ""

        lines = ["📋 **Task Plan:**"]
        for item in self.items:
            if item.status == "completed":
                icon = "✅"
            elif item.status == "in_progress":
                icon = "⏳"
            elif item.status == "skipped":
                icon = "⏭️"
            else:
                icon = "•"
            lines.append(f"{icon} {item.description}")

        return "\n".join(lines)

    def format_for_prompt(self) -> str:
        """Format plan for LLM context injection."""
        if not self.items:
            return ""

        lines = ["📋 TASK PLAN (follow this script):"]
        for item in self.items:
            status_marker = {
                "completed": "✓ DONE",
                "in_progress": "→ NOW",
                "skipped": "⏭ SKIP",
                "pending": "☐ TODO",
            }.get(item.status, "☐")
            lines.append(f"  {item.index}. [{status_marker}] {item.description}")

        current = self.get_current_item()
        if current:
            lines.append(f"")
            lines.append(
                f"⚡ CURRENT TASK: Step {current.index} - {current.description}"
            )
            lines.append(f"   Complete this step, then move to the next.")
        else:
            lines.append(f"")
            lines.append(f"✅ ALL STEPS COMPLETE - call 'complete' with your answer")

        return "\n".join(lines)


@dataclass
class CompletedStep:
    """Record of a completed step."""

    step_id: str
    tool: str
    params: Dict[str, Any]
    output_summary: str  # Brief summary, not full output
    success: bool
    error_type: Optional[str] = (
        None  # e.g., "syntax_error", "timeout", "permission_denied"
    )
    error_message: Optional[str] = None  # Full error text for analysis
    timestamp: Optional[str] = None


@dataclass
class SessionState:
    """
    External state maintained by orchestrator, NOT the LLM.

    This is ground-truth state built from actual tool outputs.
    Injected into LLM context so it doesn't need to track state.
    """

    # Files discovered via scan_workspace
    scanned_paths: Set[str] = field(default_factory=set)
    files: List[str] = field(default_factory=list)
    dirs: List[str] = field(default_factory=list)

    # Files already edited (to avoid re-editing)
    edited_files: Set[str] = field(default_factory=set)

    # Files already read (to avoid re-reading)
    read_files: Set[str] = field(default_factory=set)

    # Completed steps (compact log)
    completed_steps: List[CompletedStep] = field(default_factory=list)

    # User info extracted from memory (name, preferences, etc.)
    user_info: Dict[str, str] = field(default_factory=dict)

    # Metadata caching from command outputs
    file_metadata: Dict[str, FileMetadata] = field(
        default_factory=dict
    )  # path -> metadata
    environment_facts: EnvironmentFacts = field(default_factory=EnvironmentFacts)

    # Conversation ledger - running record of entire session
    ledger: ConversationLedger = field(default_factory=ConversationLedger)

    # FunnelCloud agent tracking
    discovered_agents: List[str] = field(
        default_factory=list
    )  # Agent IDs discovered this session
    queried_agents: List[str] = field(
        default_factory=list
    )  # Agent IDs that have been queried with execute
    agents_verified: bool = False  # True after discover-peers has been called

    # Task plan - generated at start, guides execution
    task_plan: Optional[TaskPlan] = None

    # OODA Loop: Command Flow Context - queryable history (token-efficient)
    command_flow: CommandFlowContext = field(default_factory=CommandFlowContext)

    # OODA Loop: Replan tracking
    replan_count: int = 0  # How many times we've replanned
    max_replans: int = 3  # Circuit breaker for infinite replanning

    def initialize_goal(self, goal: str) -> None:
        """Initialize the OODA loop with the user's goal."""
        self.command_flow.original_goal = goal
        self.ledger.add_request(goal)

    def set_task_plan(self, plan: TaskPlan) -> None:
        """Set the task plan for this task."""
        self.task_plan = plan

    def advance_plan(self) -> None:
        """Mark current plan item as completed and advance to next."""
        if self.task_plan:
            current = self.task_plan.get_current_item()
            if current:
                self.task_plan.mark_completed(current.index)

    def add_user_request(self, request: str) -> None:
        """Log a user request to the ledger."""
        self.ledger.add_request(request)

    def record_command_flow(
        self,
        tool: str,
        params: Dict[str, Any],
        output: str,
        success: bool,
        error: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> None:
        """
        Record a command to the queryable flow context.

        This is separate from update_from_step - it maintains the
        token-efficient queryable history for OODA replanning.
        """
        step_index = len(self.command_flow.entries) + 1
        agent_id = params.get("agent_id") if tool == "execute" else None
        command = params.get("command") if tool == "execute" else None

        self.command_flow.add_entry(
            step_index=step_index,
            tool=tool,
            success=success,
            output=output or "",
            agent_id=agent_id,
            command=command,
            error=error,
            duration_ms=duration_ms,
        )

    def get_ooda_context_for_replan(self) -> str:
        """
        Get compact context for replanning decisions.

        Only called when the orchestrator needs to replan.
        NOT fed into every LLM request.
        """
        return self.command_flow.summarize_for_replan()

    def can_replan(self) -> bool:
        """Check if we can do another replan (circuit breaker)."""
        return self.replan_count < self.max_replans

    def increment_replan(self) -> None:
        """Increment replan counter."""
        self.replan_count += 1
        logger.info(f"Replan #{self.replan_count} of {self.max_replans}")

    def update_from_step(
        self, tool: str, params: Dict[str, Any], output: str, success: bool
    ) -> None:
        """
        Update state based on a completed step.

        Called by orchestrator after each tool execution.
        """
        step_id = f"S{len(self.completed_steps) + 1:03d}"

        # Build compact summary based on tool type
        if tool == "scan_workspace":
            scan_path = params.get("path", ".")
            self.scanned_paths.add(scan_path)
            self._parse_scan_output(output, scan_path)
            summary = (
                f"scan({scan_path}): {len(self.files)} files, {len(self.dirs)} dirs"
            )

        elif tool == "read_file":
            path = params.get("path", "")
            self.read_files.add(path)
            char_count = len(output) if output else 0
            line_count = output.count("\n") + 1 if output else 0
            summary = f"read({path}): {char_count:,} chars, {line_count} lines"

            # Update file metadata with line count
            if path in self.file_metadata:
                self.file_metadata[path].line_count = line_count
            elif output:
                # Create metadata entry if we read a file we hadn't seen in scan
                self.file_metadata[path] = FileMetadata(
                    path=path,
                    line_count=line_count,
                    size_bytes=char_count,  # Approximate
                    size_human=self._format_bytes(char_count),
                    file_type=self._detect_file_type(path),
                )

        elif tool in (
            "write_file",
            "replace_in_file",
            "insert_in_file",
            "append_to_file",
        ):
            path = params.get("path", "")
            # Only mark as edited if successful - failed edits should be retried
            if success:
                self.edited_files.add(path)
            summary = f"{tool}({path}): {'OK' if success else 'FAILED'}"

        elif tool == "execute_shell":
            cmd = params.get("command", "")[:40]
            summary = f"shell({cmd}): {'OK' if success else 'FAILED'}"
            # Extract facts from shell command outputs
            if success and output:
                self._extract_shell_facts(params.get("command", ""), output)

        elif tool == "none":
            # Idempotent skip - change already present
            reason = params.get("reason", "already present")
            path = params.get("path", "")
            summary = f"skipped({path}): {reason}" if path else f"skipped: {reason}"

        elif tool == "dump_state":
            summary = "dump_state: DONE - state already shown above, do NOT call again"

        elif tool in ("remote_bash", "execute"):  # Support both old and new names
            cmd = params.get("command", "")
            # Handle various param names for agent
            agent = (
                params.get("agent_id")
                or params.get("agent")
                or params.get("agent_name")
                or params.get("agentName")
                or "default"
            )
            cmd_preview = cmd[:40] if cmd else ""
            summary = (
                f"remote({agent}): {cmd_preview}... {'OK' if success else 'FAILED'}"
            )

            # Check if this is a discover-peers call (agent discovery via localhost)
            if success and agent == "localhost" and "discover-peers" in cmd.lower():
                self.agents_verified = True
                # Extract agent IDs from JSON output
                # Format: [{"Id":"agent-id", ...}, ...]
                import json

                try:
                    peers = json.loads(output) if output else []
                    agent_ids = [
                        p.get("Id") or p.get("id") for p in peers if isinstance(p, dict)
                    ]
                    self.discovered_agents = [a for a in agent_ids if a]
                    logger.info(
                        f"discover-peers extracted agents: {self.discovered_agents}"
                    )
                    summary = (
                        f"discover-peers: {len(self.discovered_agents)} agent(s) found"
                    )
                    if self.discovered_agents:
                        summary += f" ({', '.join(self.discovered_agents)})"
                except (json.JSONDecodeError, TypeError):
                    # Fallback: try regex for agent IDs in structured output
                    agent_matches = re.findall(
                        r'"(?:Id|id)":\s*"([^"]+)"', output or ""
                    )
                    self.discovered_agents = agent_matches
                    logger.info(f"discover-peers regex extracted: {agent_matches}")

            # Track that this agent has been queried (for multi-agent progress)
            if (
                success
                and agent
                and agent != "default"
                and agent != "localhost"
                and agent not in self.queried_agents
            ):
                self.queried_agents.append(agent)

        else:
            summary = f"{tool}: {'OK' if success else 'FAILED'}"

        # Detect error type and message if not successful
        error_type = None
        error_message = None
        if not success:
            error_type, error_message = self._classify_error(tool, output)

        self.completed_steps.append(
            CompletedStep(
                step_id=step_id,
                tool=tool,
                params={
                    k: v
                    for k, v in params.items()
                    if k not in ("content", "text", "new_text")
                },
                output_summary=summary,
                success=success,
                error_type=error_type,
                error_message=error_message,
                timestamp=datetime.utcnow().isoformat() + "Z",
            )
        )

        # Add to conversation ledger
        params_summary = self._summarize_params(tool, params)
        result_summary = output[:200] if output else ("OK" if success else "FAILED")
        self.ledger.add_action(tool, params_summary, result_summary)

        # Extract important values from output
        if success and output:
            self._extract_important_values(tool, params, output)

        logger.debug(f"State updated: {summary}")

    def _summarize_params(self, tool: str, params: Dict[str, Any]) -> str:
        """Create a brief summary of tool parameters."""
        if tool == "scan_workspace":
            return params.get("path", ".")
        elif tool == "read_file":
            return params.get("path", "")
        elif tool in (
            "write_file",
            "replace_in_file",
            "insert_in_file",
            "append_to_file",
        ):
            return params.get("path", "")
        elif tool == "execute_shell":
            cmd = params.get("command", "")
            return cmd[:60] + "..." if len(cmd) > 60 else cmd
        elif tool == "execute_code":
            lang = params.get("language", "unknown")
            return f"{lang} code"
        return str(list(params.keys()))

    def _extract_important_values(
        self, tool: str, params: Dict[str, Any], output: str
    ) -> None:
        """Extract and store important values from command output."""
        # IP addresses
        ip_matches = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", output)
        for ip in ip_matches:
            if ip not in ("0.0.0.0", "127.0.0.1", "255.255.255.255"):
                self.ledger.extract_value(f"IP address", ip, tool)

        # URLs
        url_matches = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', output)
        for url in url_matches[:3]:  # Limit to 3 URLs
            self.ledger.extract_value(f"URL", url[:100], tool)

        # Ports (from common patterns)
        port_matches = re.findall(
            r"(?:port|PORT|listening on|:)[\s:]*(\d{4,5})\b", output
        )
        for port in port_matches:
            self.ledger.extract_value(f"Port", port, tool)

        # Container IDs (docker)
        if "docker" in params.get("command", "").lower():
            container_matches = re.findall(r"\b([a-f0-9]{12})\b", output)
            for cid in container_matches[:3]:
                self.ledger.extract_value("Container ID", cid, "docker")

        # Git commit hashes
        if "git" in params.get("command", "").lower():
            commit_matches = re.findall(r"\b([a-f0-9]{7,40})\b", output)
            for commit in commit_matches[:2]:
                if len(commit) >= 7:
                    self.ledger.extract_value("Git commit", commit[:7], "git")

        # File paths created/modified (from write operations)
        if tool in ("write_file", "replace_in_file"):
            path = params.get("path", "")
            if path:
                self.ledger.extract_value("Modified file", path, tool)

        # Error messages (store for debugging)
        if "error" in output.lower() or "exception" in output.lower():
            error_line = next(
                (l for l in output.split("\n") if "error" in l.lower()), None
            )
            if error_line:
                self.ledger.extract_value("Error seen", error_line[:80], tool)

    def _parse_scan_output(self, output: str, base_path: str) -> None:
        """
        Parse scan_workspace output to extract file/dir lists.

        Expected format (from executor):
        PATH: .
        NAME          TYPE   SIZE      MODIFIED
        ─────────────────────────────────────────
        .github/      dir    -         ...
        README.md     file   1.2 KB    ...
        """
        if not output:
            return

        for line in output.split("\n"):
            line = line.strip()

            # Skip headers and separators
            if not line or line.startswith("PATH:") or line.startswith("TOTAL:"):
                continue
            if line.startswith("-") or line.startswith("─") or line.startswith("NAME"):
                continue
            if line.startswith("..."):
                continue

            # Parse: NAME  TYPE  SIZE_NUM SIZE_UNIT  DATE TIME
            # Example: "ARCHITECTURE.md  file  17.3 KiB  2025-12-31 04:13:13"
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                entry_type = parts[1] if len(parts) > 1 else ""

                # Size is typically parts[2] + parts[3] (e.g., "17.3" + "KiB")
                size_str = None
                modified_str = None
                if len(parts) >= 4 and parts[3] in (
                    "B",
                    "KiB",
                    "MiB",
                    "GiB",
                    "TiB",
                    "KB",
                    "MB",
                    "GB",
                ):
                    size_str = f"{parts[2]} {parts[3]}"
                    modified_str = " ".join(parts[4:]) if len(parts) > 4 else None
                elif len(parts) >= 3:
                    # Maybe size is just a number (bytes) or missing
                    try:
                        float(parts[2])
                        size_str = parts[2]
                        modified_str = " ".join(parts[3:]) if len(parts) > 3 else None
                    except ValueError:
                        # parts[2] is not a number, might be date
                        modified_str = " ".join(parts[2:]) if len(parts) > 2 else None

                # Build full path
                if base_path and base_path != ".":
                    full_path = f"{base_path.rstrip('/')}/{name.rstrip('/')}"
                else:
                    full_path = name.rstrip("/")

                if entry_type == "dir" or name.endswith("/"):
                    if full_path not in self.dirs:
                        self.dirs.append(full_path)
                elif entry_type == "file":
                    if full_path not in self.files:
                        self.files.append(full_path)
                    # Cache file metadata
                    if size_str and size_str != "-":
                        self.file_metadata[full_path] = FileMetadata(
                            path=full_path,
                            size_human=size_str,
                            size_bytes=self._parse_size_to_bytes(size_str),
                            modified=modified_str,
                            file_type=self._detect_file_type(full_path),
                        )

        # Update environment facts from scan totals
        if output:
            total_match = re.search(
                r"TOTAL:\s*(\d+)\s*items?\s*\((\d+)\s*dirs?,\s*(\d+)\s*files?\)", output
            )
            if total_match:
                self.environment_facts.total_dir_count = int(total_match.group(2))
                self.environment_facts.total_file_count = int(total_match.group(3))

            # Detect project types from file presence
            self._detect_project_types()

    def _parse_size_to_bytes(self, size_str: str) -> Optional[int]:
        """Convert human-readable size to bytes (e.g., '1.2 KiB' -> 1228)."""
        if not size_str or size_str == "-":
            return None

        size_str = size_str.strip().upper()

        # Match patterns like "1.2 KiB", "500 B", "2.5 MiB"
        match = re.match(r"^([\d.]+)\s*(B|KIB|MIB|GIB|KB|MB|GB)?$", size_str)
        if not match:
            return None

        value = float(match.group(1))
        unit = match.group(2) or "B"

        multipliers = {
            "B": 1,
            "KIB": 1024,
            "KB": 1024,
            "MIB": 1024**2,
            "MB": 1024**2,
            "GIB": 1024**3,
            "GB": 1024**3,
        }

        return int(value * multipliers.get(unit, 1))

    def _detect_file_type(self, path: str) -> Optional[str]:
        """Detect file type from extension."""
        ext_map = {
            ".py": "python",
            ".pyw": "python",
            ".js": "javascript",
            ".mjs": "javascript",
            ".cjs": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".md": "markdown",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".html": "html",
            ".htm": "html",
            ".css": "css",
            ".scss": "css",
            ".less": "css",
            ".sh": "shell",
            ".bash": "shell",
            ".ps1": "powershell",
            ".sql": "sql",
            ".dockerfile": "dockerfile",
            ".mmd": "mermaid",
        }

        path_lower = path.lower()
        if path_lower.endswith("dockerfile") or path_lower.endswith("dockerfile.base"):
            return "dockerfile"

        for ext, ftype in ext_map.items():
            if path_lower.endswith(ext):
                return ftype
        return None

    def _detect_project_types(self) -> None:
        """Detect project types from discovered files."""
        files_lower = {f.lower() for f in self.files}
        dirs_lower = {d.lower() for d in self.dirs}

        # Python detection
        if any(f.endswith(".py") for f in files_lower):
            self.environment_facts.project_types.add("python")
        if any(
            f.endswith("requirements.txt")
            or f.endswith("pyproject.toml")
            or f == "setup.py"
            for f in files_lower
        ):
            self.environment_facts.package_managers.add("pip")

        # Docker detection
        if (
            any("dockerfile" in f for f in files_lower)
            or "docker-compose.yaml" in files_lower
            or "docker-compose.yml" in files_lower
        ):
            self.environment_facts.project_types.add("docker")

        # Node.js detection
        if "package.json" in files_lower or any(
            f.endswith(".js") or f.endswith(".ts") for f in files_lower
        ):
            self.environment_facts.project_types.add("node")
            self.environment_facts.package_managers.add("npm")

        # Detect frameworks
        if any("fastapi" in f or "uvicorn" in f for f in files_lower):
            self.environment_facts.frameworks_detected.add("fastapi")
        if "pytest.ini" in files_lower or any(
            "test_" in f or "_test.py" in f for f in files_lower
        ):
            self.environment_facts.frameworks_detected.add("pytest")

    def _extract_shell_facts(self, command: str, output: str) -> None:
        """Extract environment facts from shell command outputs."""
        cmd_lower = command.lower()

        # Git branch detection
        if "git branch" in cmd_lower or "git status" in cmd_lower:
            branch_match = re.search(r"On branch\s+(\S+)", output)
            if branch_match:
                self.environment_facts.git_branch = branch_match.group(1)
            branch_match2 = re.search(r"^\*\s+(\S+)", output, re.MULTILINE)
            if branch_match2:
                self.environment_facts.git_branch = branch_match2.group(1)

        # Python version detection
        if "python" in cmd_lower and ("--version" in cmd_lower or "-v" in cmd_lower):
            version_match = re.search(r"Python\s+([\d.]+)", output)
            if version_match:
                self.environment_facts.python_version = version_match.group(1)

        # Node version detection
        if "node" in cmd_lower and ("--version" in cmd_lower or "-v" in cmd_lower):
            version_match = re.search(r"v?([\d.]+)", output)
            if version_match:
                self.environment_facts.node_version = version_match.group(1)

        # Docker status detection
        if "docker" in cmd_lower and ("ps" in cmd_lower or "info" in cmd_lower):
            self.environment_facts.docker_running = (
                "CONTAINER ID" in output or "Server Version" in output
            )

        # PWD/working directory
        if cmd_lower.strip() == "pwd" or cmd_lower.strip() == "echo $pwd":
            self.environment_facts.working_directory = output.strip().split("\n")[0]

        # Disk usage (from du commands)
        if cmd_lower.startswith("du "):
            size_match = re.search(r"^([\d.]+[KMGT]?)\s+", output.strip(), re.MULTILINE)
            if size_match:
                self.environment_facts.add_observation(
                    f"Disk usage: {size_match.group(1)}"
                )

        # Capture interesting observations from common commands
        if "pip list" in cmd_lower or "pip freeze" in cmd_lower:
            pkg_count = len(
                [l for l in output.split("\n") if l.strip() and not l.startswith("-")]
            )
            self.environment_facts.add_observation(
                f"Python packages installed: {pkg_count}"
            )

        if "ls -la" in cmd_lower or "dir" in cmd_lower:
            line_count = len([l for l in output.split("\n") if l.strip()])
            self.environment_facts.add_observation(
                f"Directory listing: {line_count} entries"
            )

    def get_editable_files(self) -> List[str]:
        """Get files that can be edited (not binary, not already edited)."""
        editable_extensions = {
            ".md",
            ".py",
            ".js",
            ".ts",
            ".yaml",
            ".yml",
            ".json",
            ".txt",
            ".sh",
            ".ps1",
            ".mmd",
            ".html",
            ".css",
            ".env",
            ".toml",
            ".ini",
            ".cfg",
        }
        binary_extensions = {
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".bin",
            ".exe",
            ".dll",
            ".pyc",
            ".pth",
            ".safetensors",
            ".ico",
            ".woff",
            ".woff2",
            ".ttf",
            ".eot",
        }

        editable = []
        for f in self.files:
            # Skip already edited
            if f in self.edited_files:
                continue

            # Skip binary
            if any(f.endswith(ext) for ext in binary_extensions):
                continue

            # Only include known editable extensions
            if any(f.endswith(ext) for ext in editable_extensions):
                editable.append(f)

        return sorted(editable)

    def get_unread_files(self) -> List[str]:
        """Get files that haven't been read yet."""
        return [f for f in self.files if f not in self.read_files]

    def _classify_error(
        self, tool: str, output: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Classify error type from tool output to enable intelligent failure analysis.

        Returns (error_type, error_message) tuple for logging and adaptive planning.
        """
        if not output:
            return None, None

        output_lower = output.lower()

        # Syntax/quoting errors
        if "missing" in output_lower and (
            "terminator" in output_lower or "quote" in output_lower
        ):
            return "syntax_error", output[:200]
        if "syntax error" in output_lower or "invalid syntax" in output_lower:
            return "syntax_error", output[:200]
        if "unexpected token" in output_lower:
            return "syntax_error", output[:200]

        # Timeout/hung operations
        if "timeout" in output_lower or "timed out" in output_lower:
            return "timeout", output[:200]
        if "no response" in output_lower or "unresponsive" in output_lower:
            return "timeout", output[:200]

        # Permission errors
        if "permission denied" in output_lower or "access denied" in output_lower:
            return "permission_denied", output[:200]
        if "unauthorized" in output_lower or "forbidden" in output_lower:
            return "permission_denied", output[:200]

        # File/path not found
        if "not found" in output_lower or "no such file" in output_lower:
            return "not_found", output[:200]
        if "does not exist" in output_lower or "path not found" in output_lower:
            return "not_found", output[:200]

        # Connection errors
        if "connection refused" in output_lower or "unable to connect" in output_lower:
            return "connection_error", output[:200]
        if "unreachable" in output_lower or "offline" in output_lower:
            return "connection_error", output[:200]

        # Resource exhaustion
        if "out of memory" in output_lower or "memory exhausted" in output_lower:
            return "resource_error", output[:200]
        if "disk full" in output_lower or "no space left" in output_lower:
            return "resource_error", output[:200]

        # Generic execution errors
        if "error" in output_lower or "failed" in output_lower:
            return "execution_error", output[:200]

        return None, None

    def format_for_prompt(self) -> str:
        """
        Format state as context for LLM prompt injection.

        This replaces asking the LLM to maintain state.
        """
        lines = []

        # Task plan - show at the TOP so LLM sees it first
        if self.task_plan and self.task_plan.items:
            lines.append(self.task_plan.format_for_prompt())
            lines.append("")

        # Workspace index - show status prominently
        if self.files or self.dirs:
            lines.append("=== session state (already indexed - use this data) ===\n")
            lines.append(
                f"✅ WORKSPACE ALREADY SCANNED - {len(self.files)} files, {len(self.dirs)} dirs indexed"
            )
            lines.append(
                "   DO NOT call scan_workspace again - data is available below"
            )
            lines.append("")
        else:
            lines.append("=== session state ===\n")
            lines.append("⚠️ WORKSPACE NOT YET SCANNED")
            lines.append("   You MUST call scan_workspace first to see files")
            lines.append("")

        # FunnelCloud agent status - critical for remote execution
        if self.agents_verified:
            if self.discovered_agents:
                lines.append(
                    f"🖥️ AGENTS DISCOVERED: {', '.join(self.discovered_agents)}"
                )

                # Show progress on multi-agent tasks
                if self.queried_agents:
                    lines.append(f"   ✅ QUERIED: {', '.join(self.queried_agents)}")
                    remaining = [
                        a
                        for a in self.discovered_agents
                        if a not in self.queried_agents
                    ]
                    if remaining:
                        lines.append(f"   ⏳ REMAINING: {', '.join(remaining)}")
                        lines.append(
                            f"   ⚠️ {len(remaining)} agent(s) still need remote_bash!"
                        )
                    else:
                        lines.append(
                            "   ✅ All agents queried - ready to summarize results"
                        )
                else:
                    lines.append(
                        "   ⏳ No agents queried yet - use remote_bash with agent_id"
                    )
            else:
                lines.append("🖥️ AGENTS VERIFIED: None found")
                lines.append(
                    "   No remote execution available - tell user to start an agent"
                )
            lines.append("")
        else:
            lines.append("🖥️ AGENTS NOT DISCOVERED")
            lines.append(
                "   ⏳ Use execute on localhost with discover-peers to find agents"
            )
            lines.append("")

        # Completed steps - with strong warnings against repetition
        if self.completed_steps:
            # Check for repeated tools (loop detection)
            recent_tools = [s.tool for s in self.completed_steps[-5:]]
            recent_steps = self.completed_steps[-5:]

            # Detect exact duplicates (same tool + same params = definitely a loop)
            duplicate_detected = False
            for i, step in enumerate(recent_steps):
                for j, other in enumerate(recent_steps):
                    if i != j and step.tool == other.tool:
                        # For remote_bash, check if same agent
                        if step.tool in ("remote_bash", "execute"):
                            step_agent = step.params.get("agent_id") or step.params.get(
                                "agent", ""
                            )
                            other_agent = other.params.get(
                                "agent_id"
                            ) or other.params.get("agent", "")
                            if step_agent == other_agent:
                                duplicate_detected = True
                                break
                        # For idempotent tools, any repeat is a loop
                        elif step.tool in (
                            "dump_state",
                            "scan_workspace",
                        ):
                            duplicate_detected = True
                            break
                if duplicate_detected:
                    break

            # Also check for general tool repetition
            repeated = any(recent_tools.count(t) >= 3 for t in set(recent_tools))

            if duplicate_detected or repeated:
                lines.append("⛔⛔⛔ LOOP DETECTED - YOU ARE REPEATING YOURSELF ⛔⛔⛔")
                lines.append(
                    "You called the same tool/agent multiple times. STOP and call complete."
                )
                lines.append("")

            lines.append("Completed steps (⛔ = DO NOT REPEAT):")
            for step in self.completed_steps[-10:]:  # Last 10 steps
                status = "✓" if step.success else "✗"
                # Mark idempotent tools with stronger warning
                if step.tool in ("dump_state", "scan_workspace"):
                    lines.append(f"  ⛔ {status} {step.output_summary}")
                else:
                    lines.append(f"  {status} {step.output_summary}")
            if len(self.completed_steps) > 10:
                lines.append(f"  ... ({len(self.completed_steps) - 10} earlier steps)")
            lines.append("")

            # CRITICAL: Show failure analysis if recent failures exist
            failed_steps = [s for s in self.completed_steps[-5:] if not s.success]
            if failed_steps:
                lines.append("⚠️⚠️⚠️ RECENT FAILURES - ANALYZE AND ADAPT ⚠️⚠️⚠️")
                lines.append(
                    "Previous attempts failed. Do NOT retry the same approach."
                )
                lines.append(
                    "Generate a new strategy and updated plan based on root causes:"
                )
                lines.append("")
                for step in failed_steps:
                    lines.append(f"  ❌ {step.tool} FAILED on step {step.step_id}")
                    if step.error_type:
                        lines.append(f"     Error type: {step.error_type}")
                    if step.error_message:
                        # Show first 150 chars of error
                        error_preview = step.error_message[:150].replace("\n", " ")
                        lines.append(f"     Error: {error_preview}...")
                    lines.append("")

                # Suggest specific adaptations based on error types
                error_types = {s.error_type for s in failed_steps if s.error_type}
                if "syntax_error" in error_types:
                    lines.append(
                        "  → FIX: Adjust command syntax (quoting, escaping, formatting)"
                    )
                if "timeout" in error_types:
                    lines.append(
                        "  → FIX: Reduce scope (smaller directory, specific pattern, shorter timeout)"
                    )
                if "permission_denied" in error_types:
                    lines.append(
                        "  → FIX: Try alternative paths or request elevated permissions"
                    )
                if "not_found" in error_types:
                    lines.append(
                        "  → FIX: Verify path exists or use different file/directory"
                    )

                lines.append("")
                lines.append("Now generate a NEW task plan that fixes the root cause:")
                lines.append("")

        # Show top-level structure (directories containing files)
        if self.files or self.dirs:
            # Get unique top-level directories from both files and dirs
            top_dirs_from_files = set()
            for f in self.files:
                if "/" in f:
                    top_dirs_from_files.add(f.split("/")[0])
            top_dirs_from_dirs = set(d.split("/")[0] for d in self.dirs)
            all_top_dirs = sorted(top_dirs_from_files | top_dirs_from_dirs)

            # Top-level files (no slash)
            top_files = sorted(f for f in self.files if "/" not in f)

            if all_top_dirs or top_files:
                lines.append("Top-level structure:")
                for d in all_top_dirs[:20]:  # DEV: Show more
                    lines.append(f"  📁 {d}/")
                for f in top_files[:20]:  # DEV: Show more
                    lines.append(f"  📄 {f}")
                lines.append("")

        # Read files - critical to prevent re-reading
        if self.read_files:
            lines.append(f"Already read ({len(self.read_files)}) - DO NOT read again:")
            for f in sorted(self.read_files)[:30]:  # DEV: Show more
                lines.append(f"  📖 {f}")
            if len(self.read_files) > 30:
                lines.append(f"  ... and {len(self.read_files) - 30} more")
            lines.append("")

        # Edited files
        if self.edited_files:
            lines.append(f"Already edited ({len(self.edited_files)}):")
            for f in sorted(self.edited_files)[:30]:  # DEV: Show more
                lines.append(f"  ✓ {f}")
            if len(self.edited_files) > 30:
                lines.append(f"  ... and {len(self.edited_files) - 30} more")
            lines.append("")

        # User info
        if self.user_info:
            lines.append("User info:")
            for key, value in self.user_info.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        # Environment facts - what we've learned about the workspace
        ef = self.environment_facts
        env_facts = []
        if ef.total_file_count:
            env_facts.append(f"Files: {ef.total_file_count}")
        if ef.total_dir_count:
            env_facts.append(f"Dirs: {ef.total_dir_count}")
        if ef.project_types:
            env_facts.append(f"Project: {', '.join(sorted(ef.project_types))}")
        if ef.frameworks_detected:
            env_facts.append(f"Frameworks: {', '.join(sorted(ef.frameworks_detected))}")
        if ef.package_managers:
            env_facts.append(f"Pkg managers: {', '.join(sorted(ef.package_managers))}")
        if ef.git_branch:
            env_facts.append(f"Git branch: {ef.git_branch}")
        if ef.python_version:
            env_facts.append(f"Python: {ef.python_version}")
        if ef.node_version:
            env_facts.append(f"Node: {ef.node_version}")
        if ef.docker_running is not None:
            env_facts.append(
                f"Docker: {'running' if ef.docker_running else 'not running'}"
            )

        if env_facts:
            lines.append("🔍 ENVIRONMENT FACTS (learned from outputs):")
            for fact in env_facts:
                lines.append(f"  • {fact}")
            lines.append("")

        # Observations from shell commands
        if ef.observations:
            lines.append("📊 OBSERVATIONS:")
            for obs in ef.observations[-10:]:
                lines.append(f"  • {obs}")
            lines.append("")

        # Show largest files if metadata available (for space questions)
        if self.file_metadata:
            files_with_size = [
                (p, m) for p, m in self.file_metadata.items() if m.size_bytes
            ]
            if files_with_size:
                # Sort by size descending
                files_with_size.sort(key=lambda x: x[1].size_bytes or 0, reverse=True)
                lines.append("📁 LARGEST FILES:")
                for path, meta in files_with_size[:10]:
                    lines.append(f"  {meta.size_human:>10}  {path}")

                # Total size calculation
                total_bytes = sum(m.size_bytes or 0 for _, m in files_with_size)
                if total_bytes > 0:
                    total_human = self._format_bytes(total_bytes)
                    lines.append(f"  {'─' * 10}")
                    lines.append(f"  {total_human:>10}  TOTAL (indexed files)")
                lines.append("")

        # Conversation ledger - quick reference values and session history
        ledger_output = self.ledger.format_for_prompt()
        if ledger_output:
            lines.append(ledger_output)

        lines.append("=== END STATE ===")
        return "\n".join(lines)

    def _format_bytes(self, num_bytes: int) -> str:
        """Format bytes as human-readable string."""
        for unit in ["B", "KiB", "MiB", "GiB"]:
            if abs(num_bytes) < 1024.0:
                return f"{num_bytes:.1f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.1f} TiB"

    def get_total_size(self) -> Optional[str]:
        """Get total size of indexed files."""
        if not self.file_metadata:
            return None
        total_bytes = sum(m.size_bytes or 0 for m in self.file_metadata.values())
        return self._format_bytes(total_bytes) if total_bytes > 0 else None

    def get_file_info(self, path: str) -> Optional[FileMetadata]:
        """Get cached metadata for a specific file."""
        return self.file_metadata.get(path)

    def has_scanned(self, path: str = ".") -> bool:
        """Check if a path has already been scanned."""
        return path in self.scanned_paths

    def has_edited(self, path: str) -> bool:
        """Check if a file has already been edited."""
        return path in self.edited_files

    def has_read(self, path: str) -> bool:
        """Check if a file has already been read."""
        return path in self.read_files

    def reset(self) -> None:
        """Reset state for a new task."""
        self.scanned_paths.clear()
        self.files.clear()
        self.dirs.clear()
        self.edited_files.clear()
        self.read_files.clear()
        self.completed_steps.clear()
        self.file_metadata.clear()
        self.environment_facts = EnvironmentFacts()
        # Keep user_info and ledger across tasks - they're session-level


# Session-based state storage
_session_states: Dict[str, SessionState] = {}
_current_session_id: Optional[str] = None

# Legacy singleton for backward compatibility (will be removed)
_current_state: Optional[SessionState] = None


def get_session_state(session_id: Optional[str] = None) -> SessionState:
    """
    Get or create session state for a session.

    Args:
        session_id: Optional session identifier. If provided, returns
                   session-specific state. Otherwise uses global state.

    Returns:
        SessionState for the session (or global if no session_id).
    """
    global _current_state, _current_session_id

    if session_id:
        if session_id not in _session_states:
            _session_states[session_id] = SessionState()
            logger.info(f"Created new session state for session: {session_id[:8]}...")
        _current_session_id = session_id
        return _session_states[session_id]

    # Fall back to global state for backward compatibility
    if _current_state is None:
        _current_state = SessionState()
    return _current_state


def reset_session_state(session_id: Optional[str] = None) -> SessionState:
    """
    Reset and return fresh session state.

    Args:
        session_id: Optional session identifier. If provided, resets
                   session-specific state. Otherwise resets global state.

    Returns:
        Fresh SessionState for the session (or global).
    """
    global _current_state

    if session_id:
        _session_states[session_id] = SessionState()
        logger.info(f"Reset session state for session: {session_id[:8]}...")
        return _session_states[session_id]

    # Fall back to global state reset
    _current_state = SessionState()
    return _current_state


def get_existing_session(session_id: str) -> Optional[SessionState]:
    """
    Get session state for a specific session if it exists.

    Args:
        session_id: Session identifier.

    Returns:
        SessionState if session exists, None otherwise.
    """
    return _session_states.get(session_id)


def cleanup_session(session_id: str) -> bool:
    """
    Remove session state for a session (cleanup on disconnect).

    Args:
        session_id: Session identifier to cleanup.

    Returns:
        True if session was removed, False if it didn't exist.
    """
    if session_id in _session_states:
        del _session_states[session_id]
        logger.info(f"Cleaned up session state for session: {session_id[:8]}...")
        return True
    return False


def get_active_sessions() -> List[str]:
    """Get list of active session IDs."""
    return list(_session_states.keys())
