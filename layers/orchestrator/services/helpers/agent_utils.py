"""
Agent target extraction and command redirection utilities.
"""

import re
import logging
from typing import List, Optional

from schemas.models import Step

logger = logging.getLogger("orchestrator.agent_utils")


class AgentTargetExtractor:
    """Extracts target agents from user requests."""

    @staticmethod
    def extract_target_agent(
        user_request: str, discovered_agents: List[str]
    ) -> Optional[str]:
        """
        Extract the target agent from a user request by matching against discovered agents.

        Handles: explicit names, contextual references, quoted targets, action patterns.
        """
        if not user_request or not discovered_agents:
            return None

        request_lower = user_request.lower()

        # Strategy 0: Contextual references
        personal_phrases = [
            "my workstation",
            "my pc",
            "my machine",
            "my computer",
            "my desktop",
            "my laptop",
            "workstation",
            "personal machine",
        ]
        if any(p in request_lower for p in personal_phrases):
            workstation_indicators = [
                "workstation",
                "desktop",
                "laptop",
                "ians",
                "ian-",
                "-pc",
                "-ws",
            ]
            for agent in discovered_agents:
                if any(ind in agent.lower() for ind in workstation_indicators):
                    logger.info(f"Target extraction: contextual match '{agent}'")
                    return agent
            for agent in discovered_agents:
                if re.match(r"^[a-z]+s?-[a-z0-9]+$", agent.lower()):
                    logger.info(f"Target extraction: user-pattern match '{agent}'")
                    return agent

        # Strategy 1: Exact match
        for agent in discovered_agents:
            if agent.lower() in request_lower:
                logger.info(f"Target extraction: exact match '{agent}'")
                return agent

        # Strategy 2: Quoted target
        quoted_matches = re.findall(r"['\"]([^'\"]+)['\"]", user_request)
        for quoted in quoted_matches:
            for agent in discovered_agents:
                if agent.lower() == quoted.lower() or quoted.lower() in agent.lower():
                    logger.info(f"Target extraction: quoted match '{agent}'")
                    return agent

        # Strategy 3: Action target
        action_patterns = [
            r"(?:reboot|restart|shutdown|stop|start|check|query|scan)\s+['\"]?(\S+?)['\"]?(?:\s|$)",
            r"(?:on|to|from)\s+['\"]?(\S+?)['\"]?(?:\s|$)",
        ]
        for pattern in action_patterns:
            matches = re.findall(pattern, request_lower)
            for match in matches:
                match = match.rstrip(".,!?")
                for agent in discovered_agents:
                    if agent.lower() == match or match in agent.lower():
                        logger.info(f"Target extraction: action match '{agent}'")
                        return agent

        logger.warning(
            f"Target extraction: no match for '{user_request}' in {discovered_agents}"
        )
        return None


class CommandRedirector:
    """Redirects commands to appropriate tools."""

    @staticmethod
    def redirect_workspace_command(command: str, code: str = "") -> Optional[Step]:
        """Convert bash/shell command to appropriate workspace tool."""
        if code and ("import " in code or "def " in code or "class " in code):
            filename = "app.py"
            if "flask" in code.lower():
                filename = "app.py"
            elif "django" in code.lower():
                filename = "manage.py"
            return Step(
                step_id="guardrail_redirect_code_to_file",
                tool="write_file",
                params={"path": filename, "content": code},
                batch_id=None,
                reasoning="Redirected execute code to write_file",
            )

        if command.startswith("touch "):
            files_str = command.replace("touch ", "").strip().replace("/workspace/", "")
            first_file = files_str.split()[0] if files_str.split() else "unnamed.txt"
            return Step(
                step_id="guardrail_redirect_workspace",
                tool="write_file",
                params={"path": first_file, "content": ""},
                batch_id=None,
                reasoning=f"Redirected touch to write_file - file: {first_file}",
            )

        if command.startswith("echo ") and " > " in command:
            parts = command.split(" > ")
            content = (
                parts[0]
                .replace("echo ", "")
                .replace("-n ", "")
                .strip()
                .strip('"')
                .strip("'")
            )
            filename = parts[1].strip().replace("/workspace/", "")
            return Step(
                step_id="guardrail_redirect_workspace",
                tool="write_file",
                params={"path": filename, "content": content},
                batch_id=None,
                reasoning="Redirected echo to write_file",
            )

        if command.startswith("cat "):
            filename = command.replace("cat ", "").strip().replace("/workspace/", "")
            return Step(
                step_id="guardrail_redirect_workspace",
                tool="read_file",
                params={"path": filename},
                batch_id=None,
                reasoning="Redirected cat to read_file",
            )

        if command.startswith("find ") or command.startswith("ls "):
            return Step(
                step_id="guardrail_redirect_workspace",
                tool="scan_workspace",
                params={"path": "."},
                batch_id=None,
                reasoning="Redirected find/ls to scan_workspace",
            )

        if command.startswith("mkdir "):
            return Step(
                step_id="guardrail_redirect_workspace",
                tool="execute_shell",
                params={"command": command},
                batch_id=None,
                reasoning="Redirected mkdir to execute_shell",
            )

        return None
