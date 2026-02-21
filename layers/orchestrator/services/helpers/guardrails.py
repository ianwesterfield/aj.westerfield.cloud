"""
Guardrail engine for step validation and correction.
"""

import re
import logging
from typing import Optional

from schemas.models import Step
from services.session_state import SessionState

logger = logging.getLogger("orchestrator.guardrails")


class GuardrailEngine:
    """Applies guardrails to validate and correct LLM-generated steps."""

    def apply(self, step: Step, session_state: SessionState) -> Step:
        """Apply all guardrails to a parsed step."""
        checks = [
            self._check_execute,
            self._check_force_execute,
            self._check_completion_validity,
            self._check_duplicate_remote_bash,
            self._check_duplicate_execute,
            self._check_tool_loops,
            self._check_dump_state,
            self._check_replace_failures,
            self._check_reread,
            self._check_edit_paths,
        ]
        for check in checks:
            result = check(step, session_state)
            if result:
                return result
        return step

    def _check_execute(self, step: Step, state: SessionState) -> Optional[Step]:
        if step.tool not in ("remote_bash", "execute"):
            return None

        agent_id = step.params.get("agent_id", "") or step.params.get("agent", "")
        command = (
            step.params.get("command", "")
            or step.params.get("cmd", "")
            or step.params.get("commands", "")
        )
        if isinstance(command, list):
            command = " ".join(command) if command else ""
        command = str(command).strip()

        # localhost is always allowed (bootstrap agent for discovery)
        if agent_id == "localhost":
            return None

        # If no agents discovered yet and not targeting localhost, suggest discovery
        if not state.discovered_agents and agent_id != "localhost":
            logger.warning(
                f"GUARDRAIL: execute on '{agent_id}' without discovery - suggesting localhost discover-peers first"
            )
            return Step(
                step_id="guardrail_suggest_discovery",
                tool="execute",
                params={
                    "agent_id": "localhost",
                    "command": "Invoke-RestMethod http://localhost:41421/discover-peers",
                },
                batch_id=None,
                reasoning="Discovering agents first via localhost",
            )

        if (
            agent_id
            and agent_id not in state.discovered_agents
            and agent_id != "localhost"
        ):
            logger.error(f"GUARDRAIL BLOCK: execute on unknown agent '{agent_id}'")
            available = ", ".join(state.discovered_agents)
            return Step(
                step_id="guardrail_unknown_agent",
                tool="complete",
                params={
                    "error": f"Cannot execute on '{agent_id}' - not found. Available: {available}"
                },
                batch_id=None,
                reasoning=f"Blocked - target agent '{agent_id}' unavailable",
            )

        if command:
            from .powershell_utils import PowerShellValidator

            errors = PowerShellValidator.validate_syntax(command)
            if errors:
                logger.warning(f"GUARDRAIL: Fixing PowerShell errors: {errors}")
                fixed = PowerShellValidator.fix_command(command, errors)
                if fixed != command:
                    return Step(
                        step_id=step.step_id,
                        tool="execute",
                        params={**step.params, "command": fixed},
                        batch_id=None,
                        reasoning=f"Fixed PowerShell syntax: {errors[0]}",
                    )
        return None

    def _check_force_execute(self, step: Step, state: SessionState) -> Optional[Step]:
        if not state.discovered_agents or step.tool not in (
            "scan_workspace",
            "execute_shell",
        ):
            return None

        # Agents have been discovered - redirect to execute
        user_request = (
            state.ledger.user_requests[-1] if state.ledger.user_requests else ""
        )
        from .agent_utils import AgentTargetExtractor

        agent_id = AgentTargetExtractor.extract_target_agent(
            user_request, state.discovered_agents
        )

        if not agent_id:
            target_patterns = re.findall(
                r"['\"]([^'\"]+)['\"]|(?:on|reboot|restart|shutdown|check)\s+(\S+)",
                user_request.lower(),
            )
            if any(target_patterns):
                logger.error(f"GUARDRAIL BLOCK: User target not found")
                return Step(
                    step_id="guardrail_target_mismatch",
                    tool="complete",
                    params={
                        "error": f"Target not found. Available: {', '.join(state.discovered_agents)}"
                    },
                    batch_id=None,
                    reasoning="Blocked - user-specified target not found",
                )
            agent_id = state.discovered_agents[0]

        logger.warning(f"GUARDRAIL: Redirecting {step.tool} to execute on {agent_id}")
        if step.tool == "scan_workspace":
            path = step.params.get("path", "C:\\")
            return Step(
                step_id="guardrail_force_remote",
                tool="execute",
                params={
                    "agent_id": agent_id,
                    "command": f"Get-ChildItem -Path '{path}' -File",
                },
                batch_id=None,
                reasoning=f"Redirected scan_workspace to execute on {agent_id}",
            )
        elif step.tool == "execute_shell":
            cmd = step.params.get("cmd", "") or step.params.get("command", "")
            return Step(
                step_id="guardrail_force_remote",
                tool="execute",
                params={"agent_id": agent_id, "command": cmd},
                batch_id=None,
                reasoning=f"Redirected execute_shell to execute on {agent_id}",
            )

    def _check_completion_validity(
        self, step: Step, state: SessionState
    ) -> Optional[Step]:
        if step.tool != "complete":
            return None

        # Check for hallucinated results when completing without actual data
        answer_text = step.params.get("answer", "")
        from .response_parser import ResponseParser

        if ResponseParser.detect_completion_hallucination(answer_text):
            logger.warning("GUARDRAIL: Blocking potentially hallucinated results")
            # Only block if we haven't executed anything yet
            if not state.completed_steps or all(
                s.tool == "think" for s in state.completed_steps
            ):
                return Step(
                    step_id="guardrail_no_hallucination",
                    tool="complete",
                    params={
                        "error": "Cannot provide answer without executing commands first."
                    },
                    batch_id=None,
                    reasoning="Blocked hallucination - no commands executed",
                )
        if answer_text and len(answer_text) > 50:
            return Step(
                step_id="guardrail_force_error_no_agents",
                tool="complete",
                params={"error": "No FunnelCloud agents available."},
                batch_id=None,
                reasoning="Forced error - no agents but model tried to answer",
            )
        return None

    def _check_duplicate_remote_bash(
        self, step: Step, state: SessionState
    ) -> Optional[Step]:
        if step.tool != "remote_bash":
            return None
        new_agent = step.params.get("agent_id", "")
        new_cmd = step.params.get("command", "")
        for prev in state.completed_steps[-10:]:
            if (
                prev.tool == "remote_bash"
                and prev.params.get("agent_id", "") == new_agent
                and prev.params.get("command", "") == new_cmd
            ):
                return Step(
                    step_id="guardrail_no_retry_remote_bash",
                    tool="complete",
                    params={"answer": "I already executed this command."},
                    batch_id=None,
                    reasoning="Blocked duplicate remote_bash",
                )
        return None

    def _check_duplicate_execute(
        self, step: Step, state: SessionState
    ) -> Optional[Step]:
        if step.tool != "execute":
            return None
        new_agent = (
            step.params.get("agent_id")
            or step.params.get("agent")
            or step.params.get("agent_name")
            or ""
        )
        new_cmd = step.params.get("command", "")
        for prev in state.completed_steps[-10:]:
            if prev.tool != "execute" or not prev.success:
                continue
            prev_agent = (
                prev.params.get("agent_id")
                or prev.params.get("agent")
                or prev.params.get("agent_name")
                or ""
            )
            if prev_agent == new_agent and prev.params.get("command", "") == new_cmd:
                return Step(
                    step_id="guardrail_no_retry_remote",
                    tool="complete",
                    params={"answer": "I already retrieved the requested information."},
                    batch_id=None,
                    reasoning=f"Blocked duplicate execute on {new_agent}",
                )
        return None

    def _check_tool_loops(self, step: Step, state: SessionState) -> Optional[Step]:
        if step.tool in (
            "execute",
            "remote_bash",
            "remote_bash_all",
        ):
            return None

        file_tools = {
            "write_file",
            "read_file",
            "replace_in_file",
            "insert_in_file",
            "append_to_file",
        }
        if step.tool in file_tools:
            current_path = step.params.get("path", "") or step.params.get(
                "file_path", ""
            )
            if current_path:
                same_path_count = sum(
                    1
                    for s in state.completed_steps[-5:]
                    if s.tool == step.tool
                    and (s.params.get("path", "") or s.params.get("file_path", ""))
                    == current_path
                )
                if same_path_count >= 2:
                    return Step(
                        step_id="guardrail_loop_break",
                        tool="complete",
                        params={
                            "error": f"Loop detected: {step.tool} on {current_path} called {same_path_count}x"
                        },
                        batch_id=None,
                        reasoning=f"Forced completion to break loop",
                    )
        else:
            recent_tools = [s.tool for s in state.completed_steps[-5:]]
            if step.tool in recent_tools:
                repeat_count = recent_tools.count(step.tool)
                once_only = {"scan_workspace", "dump_state"}
                threshold = 1 if step.tool in once_only else 2
                if repeat_count >= threshold:
                    return Step(
                        step_id="guardrail_loop_break",
                        tool="complete",
                        params=(
                            {
                                "error": f"Loop detected: {step.tool} called {repeat_count}x"
                            }
                            if threshold > 1
                            else {}
                        ),
                        batch_id=None,
                        reasoning=f"Forced completion to break {step.tool} loop",
                    )
        return None

    def _check_dump_state(self, step: Step, state: SessionState) -> Optional[Step]:
        if step.tool != "dump_state":
            return None
        dump_count = sum(1 for s in state.completed_steps if s.tool == "dump_state")
        if dump_count >= 1:
            return Step(
                step_id="guardrail_no_dump_repeat",
                tool="complete",
                params={},
                batch_id=None,
                reasoning="dump_state already executed",
            )
        return None

    def _check_replace_failures(
        self, step: Step, state: SessionState
    ) -> Optional[Step]:
        if step.tool != "replace_in_file":
            return None
        path = step.params.get("path", "")
        recent_failures = sum(
            1
            for s in state.completed_steps[-5:]
            if s.tool == "replace_in_file"
            and s.params.get("path") == path
            and not s.success
        )
        if recent_failures >= 2:
            return Step(
                step_id="guardrail_use_insert",
                tool="insert_in_file",
                params={
                    "path": path,
                    "position": "start",
                    "text": step.params.get("new_text", ""),
                },
                batch_id=None,
                reasoning=f"Auto-corrected: replace_in_file failed {recent_failures}x",
            )
        return None

    def _check_reread(self, step: Step, state: SessionState) -> Optional[Step]:
        if step.tool != "read_file":
            return None
        path = step.params.get("path", "") or step.params.get("file_path", "")
        if path and path in state.read_files:
            return Step(
                step_id="guardrail_no_reread",
                tool="complete",
                params={"error": f"Already read {path}. Move to editing or complete."},
                batch_id=None,
                reasoning=f"Blocked re-read of {path}",
            )
        return None

    def _check_edit_paths(self, step: Step, state: SessionState) -> Optional[Step]:
        if step.tool not in ("insert_in_file", "replace_in_file", "append_to_file"):
            return None
        path = step.params.get("path", "") or step.params.get("file_path", "")
        if path and state.files and path not in state.files:
            similar = [f for f in state.files if f.endswith(path) or path in f]
            if similar:
                step.params["path"] = similar[0]
                logger.info(f"GUARDRAIL: Corrected path to '{similar[0]}'")
        return None
