"""
LLM Response parsing utilities.
"""

import re
import json
import uuid
import logging
from typing import Optional

from schemas.models import Step

logger = logging.getLogger("orchestrator.response_parser")


class ResponseParser:
    """Parses LLM responses into structured Step objects."""

    HALLUCINATION_PATTERNS = [
        r"\*\*[a-z_]+\s+(?:output|results?):\*\*",
        r"↳\s+Got\s+\d+\s+(?:lines|results|entries|folders?)",
        r"(?:has been executed|has been run|was executed|executed successfully)",
        r"(?:execute|script|command).*(?:output|results?):\s*(?:\n|$)",
        r"```\s*(?:json|javascript|python|powershell|shell)",
    ]

    NARRATIVE_HALLUCINATION_INDICATORS = [
        r"script\s+(?:was|has been|has|was already)\s+executed",
        r"(?:successfully\s+)?(?:retrieved|gathered|collected|found)",
        r"folder\w*\s+(?:sizes?|information)",
        r"(?:the\s+)?results?\s+(?:are|show|indicate)",
    ]

    COMPLETION_HALLUCINATION_INDICATORS = [
        "here are the",
        "top 10",
        "largest files",
        "scanned",
        "/home/",
        "/user/",
        ".bin",
        ".tar",
        ".iso",
        "explorer.exe",
        "notepad.exe",
        "system32",
        "c:\\windows",
        "c:\\program",
        "c:\\users",
        ".dll",
        " kb",
        " mb",
        " gb",
        " bytes",
        "directory listing",
        "file listing",
        "| name |",
        "filename",
    ]

    @staticmethod
    def detect_hallucination(response: str) -> Optional[str]:
        """Detect if LLM is hallucinating tool execution."""
        json_portion = response
        if "</think>" in response:
            json_portion = response.split("</think>", 1)[1].strip()

        for pattern in ResponseParser.HALLUCINATION_PATTERNS:
            if re.search(pattern, json_portion, re.IGNORECASE):
                logger.warning(f"HALLUCINATION DETECTED: {pattern}")
                return f"LLM is narrating execution instead of calling tools."

        has_json = "{" in json_portion and any(
            key in json_portion
            for key in ['"tool"', '"action"', '"step"', '"task"', '"instruction"']
        )
        if not has_json and len(json_portion.strip()) > 100:
            for indicator in ResponseParser.NARRATIVE_HALLUCINATION_INDICATORS:
                if re.search(indicator, json_portion, re.IGNORECASE):
                    return "LLM is narrating results instead of calling tools"
            return "LLM produced narrative text instead of required JSON"

        return None

    @staticmethod
    def detect_completion_hallucination(answer_text: str) -> bool:
        """Detect if a completion answer contains hallucinated results."""
        answer_lower = answer_text.lower()
        is_hallucinating = any(
            ind in answer_lower
            for ind in ResponseParser.COMPLETION_HALLUCINATION_INDICATORS
        )

        if not is_hallucinating and answer_text:
            if re.search(r"[A-Z]:\\[A-Za-z0-9_\\]+\.[a-z]{2,4}", answer_text):
                is_hallucinating = True
                logger.warning("GUARDRAIL: Detected Windows path hallucination")

        return is_hallucinating

    @staticmethod
    def extract_first_json_object(text: str) -> str:
        """Extract only the first JSON object from text."""
        if not text:
            return text

        start = text.find("{")
        if start == -1:
            return text

        depth, in_string, escape_next = 0, False, False
        for i, char in enumerate(text[start:], start):
            if escape_next:
                escape_next = False
                continue
            if char == "\\":
                escape_next = True
                continue
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]

        return text[start:]

    @staticmethod
    def parse_response(response: str, task: str) -> Step:
        """Parse LLM response into a Step object."""
        logger.info(
            f"Raw LLM response (first 500 chars): {response[:500] if response else '(empty)'}"
        )

        hallucination_error = ResponseParser.detect_hallucination(response)
        if hallucination_error:
            logger.error(f"Hallucination error: {hallucination_error}")
            return Step(
                step_id=f"hallucination_{uuid.uuid4().hex[:8]}",
                tool="complete",
                params={"error": "INVALID FORMAT: " + hallucination_error},
                batch_id=None,
                reasoning="Blocked hallucinated response",
            )

        thinking = ""
        if "<think>" in response and "</think>" in response:
            think_start = response.index("<think>") + len("<think>")
            think_end = response.index("</think>")
            thinking = response[think_start:think_end].strip()

        json_str = response
        if "</think>" in response:
            json_str = response.split("</think>", 1)[1].strip()

        json_str = ResponseParser.extract_first_json_object(json_str)

        try:
            fixed_json = re.sub(r'(?<!\\)\\(?![\\nrt"])', r"\\\\", json_str)
            data = json.loads(fixed_json)
            step_id = f"step_{uuid.uuid4().hex[:8]}"

            note = (
                data.get("note", "")
                or data.get("reasoning", "")
                or data.get("description", "")
                or data.get("instruction", "")
            )
            reasoning = thinking if thinking else note

            tool_name = (
                data.get("tool") or data.get("action") or data.get("step") or "unknown"
            )
            if tool_name and len(tool_name) > 30:
                for known_tool in [
                    "scan_workspace",
                    "execute_shell",
                    "dump_state",
                    "read_file",
                    "write_file",
                    "execute",
                    "complete",
                    "think",
                ]:
                    if re.search(
                        r"\b" + re.escape(known_tool) + r"\b", tool_name.lower()
                    ):
                        tool_name = known_tool
                        break
                else:
                    tool_name = "unknown"

            params = data.get("params", {})
            if not params:
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
            return Step(
                step_id=f"parse_error_{uuid.uuid4().hex[:8]}",
                tool="complete",
                params={
                    "error": "LLM returned invalid response format. Please try again."
                },
                batch_id=None,
                reasoning=f"Parse error: {e}",
            )
