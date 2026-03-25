"""Tests for ResponseParser - coverage target for missing lines.

Covers the legacy action normalization, param extraction fallbacks,
long tool name normalization, hallucination detection paths, and
JSON extraction edge cases not covered by other test suites.
"""

import pytest
import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "layers", "orchestrator")
)

try:
    from services.helpers.response_parser import ResponseParser  # type: ignore[import-not-found]
    from schemas.models import Step  # type: ignore[import-not-found]
except ImportError:
    # Fallback: try importing from the added path directly
    import importlib.util

    rp_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "layers",
        "orchestrator",
        "services",
        "helpers",
        "response_parser.py",
    )

    spec = importlib.util.spec_from_file_location("response_parser", rp_path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec from {rp_path}")

    response_parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(response_parser)
    ResponseParser = response_parser.ResponseParser

    models_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "layers",
        "orchestrator",
        "schemas",
        "models.py",
    )

    spec = importlib.util.spec_from_file_location("models", models_path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec from {models_path}")

    models = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(models)
    Step = models.Step


# ==== detect_hallucination ====


class TestDetectHallucinationPatterns:
    """Cover lines 68-81: hallucination pattern matching and narrative detection."""

    def test_pattern_output_narration_bold(self):
        """Lines 69-71: HALLUCINATION_PATTERNS match returns narration message."""
        response = "**read_file output:**\nsome content here"
        result = ResponseParser.detect_hallucination(response)
        assert result is not None
        assert "narrating" in result.lower()

    def test_pattern_got_n_lines(self):
        """Lines 69-71: HALLUCINATION_PATTERNS - got N lines indicator."""
        response = "↳ Got 25 lines from the output"
        result = ResponseParser.detect_hallucination(response)
        assert result is not None

    def test_pattern_executed_successfully(self):
        """Lines 69-71: HALLUCINATION_PATTERNS - executed successfully."""
        response = "The command has been executed successfully on the remote host"
        result = ResponseParser.detect_hallucination(response)
        assert result is not None

    def test_pattern_code_block(self):
        """Lines 69-71: HALLUCINATION_PATTERNS - code block."""
        response = "```json\n{}\n```"
        result = ResponseParser.detect_hallucination(response)
        assert result is not None

    def test_narrative_indicator_retrieved(self):
        """Lines 78-80: NARRATIVE_HALLUCINATION_INDICATORS - retrieved."""
        response = (
            "I successfully retrieved all the folder sizes from the remote agent "
            "and the results look good with many items returned from the server"
        )
        result = ResponseParser.detect_hallucination(response)
        assert result is not None
        assert "narrating" in result.lower() or "narrative" in result.lower()

    def test_narrative_indicator_results_show(self):
        """Lines 78-80: NARRATIVE_HALLUCINATION_INDICATORS - results show."""
        response = (
            "The results show that the server has 50GB of free disk space and "
            "many other important metrics that we should review carefully now"
        )
        result = ResponseParser.detect_hallucination(response)
        assert result is not None

    def test_long_text_no_json_no_indicator_returns_narrative(self):
        """Line 81: No indicators but long text without JSON -> narrative error."""
        response = "This is a long block of plain text without any JSON structure " * 5
        result = ResponseParser.detect_hallucination(response)
        assert result is not None
        assert "narrative" in result.lower() or "JSON" in result


# ==== detect_completion_hallucination ====


class TestDetectCompletionHallucinationWindows:
    """Cover lines 95-97: Windows path regex hallucination detection."""

    def test_windows_path_drive_letter_file(self):
        """Lines 95-97: Windows path D:\\... triggers hallucination."""
        result = ResponseParser.detect_completion_hallucination(
            "The report is at D:\\MyData\\report.docx"
        )
        assert result is True

    def test_windows_path_not_in_indicators_but_matches_regex(self):
        """Lines 95-97: Path like E:\\Backup\\data.zip matches regex."""
        result = ResponseParser.detect_completion_hallucination(
            "Backup located at E:\\Backup\\data.zip was found"
        )
        assert result is True

    def test_no_hallucination_clean_text(self):
        """Line 94: is_hallucinating stays False for clean text."""
        result = ResponseParser.detect_completion_hallucination("Task complete.")
        assert result is False


# ==== extract_first_json_object ====


class TestExtractFirstJsonObjectEdgeCases:
    """Cover lines 105, 114-118, 131: edge cases in JSON extraction."""

    def test_empty_string_returns_empty(self):
        """Line 105: Empty string returns empty."""
        result = ResponseParser.extract_first_json_object("")
        assert result == ""

    def test_backslash_in_string_value(self):
        """Lines 114-118: Backslash handling (escape_next flag)."""
        text = r'{"path": "C:\\Users\\admin"}'
        result = ResponseParser.extract_first_json_object(text)
        assert result == text

    def test_escaped_quote_in_string(self):
        """Lines 114-118: Escaped quote in string value."""
        text = r'{"key": "val\"ue"}'
        result = ResponseParser.extract_first_json_object(text)
        assert result == text

    def test_unclosed_json_returns_from_start(self):
        """Line 131: Unclosed JSON returns text[start:]."""
        text = 'prefix {"key": "val'
        result = ResponseParser.extract_first_json_object(text)
        assert result == '{"key": "val'


# ==== parse_response - legacy action normalization ====


class TestParseResponseLegacyActions:
    """Cover lines 197-201: LEGACY_ACTION_MAP normalization."""

    def test_execute_command_normalizes_to_execute(self):
        """Lines 198-201: 'execute_command' -> 'execute'."""
        response = '{"action": "execute_command", "command": "Get-Process"}'
        step = ResponseParser.parse_response(response, "task")
        assert step.tool == "execute"

    def test_run_command_normalizes_to_execute(self):
        """Lines 198-201: 'run_command' -> 'execute'."""
        response = '{"action": "run_command", "command": "ls -la"}'
        step = ResponseParser.parse_response(response, "task")
        assert step.tool == "execute"

    def test_shell_normalizes_to_execute(self):
        """Lines 198-201: 'shell' -> 'execute'."""
        response = '{"action": "shell", "command": "whoami"}'
        step = ResponseParser.parse_response(response, "task")
        assert step.tool == "execute"

    def test_run_normalizes_to_execute(self):
        """Lines 198-201: 'run' -> 'execute'."""
        response = '{"action": "run", "command": "ipconfig"}'
        step = ResponseParser.parse_response(response, "task")
        assert step.tool == "execute"

    def test_provide_markdown_normalizes_to_complete(self):
        """Lines 198-201: 'provide_markdown' -> 'complete'."""
        response = '{"action": "provide_markdown", "markdown": "# Done"}'
        step = ResponseParser.parse_response(response, "task")
        assert step.tool == "complete"

    def test_provide_answer_normalizes_to_complete(self):
        """Lines 198-201: 'provide_answer' -> 'complete'."""
        response = '{"action": "provide_answer", "answer": "42"}'
        step = ResponseParser.parse_response(response, "task")
        assert step.tool == "complete"

    def test_respond_normalizes_to_complete(self):
        """Lines 198-201: 'respond' -> 'complete'."""
        response = '{"action": "respond", "answer": "done"}'
        step = ResponseParser.parse_response(response, "task")
        assert step.tool == "complete"

    def test_answer_action_normalizes_to_complete(self):
        """Lines 198-201: 'answer' -> 'complete'."""
        response = '{"action": "answer", "answer": "all finished"}'
        step = ResponseParser.parse_response(response, "task")
        assert step.tool == "complete"

    def test_reason_normalizes_to_think(self):
        """Lines 198-201: 'reason' -> 'think'."""
        response = '{"action": "reason", "thought": "analyzing"}'
        step = ResponseParser.parse_response(response, "task")
        assert step.tool == "think"

    def test_plan_normalizes_to_think(self):
        """Lines 198-201: 'plan' -> 'think'."""
        response = '{"action": "plan", "thought": "next steps"}'
        step = ResponseParser.parse_response(response, "task")
        assert step.tool == "think"


# ==== parse_response - long tool name normalization ====


class TestParseResponseLongToolName:
    """Cover lines 203-220: long tool name normalization."""

    def test_long_name_with_execute_shell_extracted(self):
        """Lines 204-218: Long name with 'execute_shell' -> 'execute_shell'."""
        response = '{"tool": "I should use execute_shell to run this on the agent now", "params": {}}'
        step = ResponseParser.parse_response(response, "task")
        assert step.tool == "execute_shell"

    def test_long_name_with_dump_state_extracted(self):
        """Lines 204-218: Long name with 'dump_state' -> 'dump_state'."""
        response = '{"tool": "the best approach is to call dump_state here for debugging", "params": {}}'
        step = ResponseParser.parse_response(response, "task")
        assert step.tool == "dump_state"

    def test_long_name_with_write_file_extracted(self):
        """Lines 204-218: Long name with 'write_file' -> 'write_file'."""
        response = '{"tool": "I need to use write_file to save the configuration data", "params": {}}'
        step = ResponseParser.parse_response(response, "task")
        assert step.tool == "write_file"

    def test_long_name_no_known_tool_becomes_unknown(self):
        """Lines 219-220: Long name with no known tool -> 'unknown'."""
        response = '{"tool": "this_is_a_very_long_tool_name_that_does_not_match_any_known_tools_at_all", "params": {}}'
        step = ResponseParser.parse_response(response, "task")
        assert step.tool == "unknown"


# ==== parse_response - param extraction fallbacks ====


class TestParseResponseParamFallbacks:
    """Cover lines 224-236: top-level param extraction for legacy schemas."""

    def test_path_param_extracted(self):
        """Line 225: 'path' key at top level becomes params['path']."""
        response = '{"tool": "read_file", "path": "/etc/hosts"}'
        step = ResponseParser.parse_response(response, "task")
        assert step.params.get("path") == "/etc/hosts"

    def test_file_path_param_extracted(self):
        """Line 227: 'file_path' key becomes params['path']."""
        response = '{"tool": "read_file", "file_path": "/var/log/syslog"}'
        step = ResponseParser.parse_response(response, "task")
        assert step.params.get("path") == "/var/log/syslog"

    def test_command_param_extracted(self):
        """Line 229: 'command' key becomes params['command']."""
        response = '{"action": "execute_command", "command": "hostname"}'
        step = ResponseParser.parse_response(response, "task")
        assert step.params.get("command") == "hostname"

    def test_answer_param_extracted(self):
        """Line 231: 'answer' key becomes params['answer']."""
        response = '{"action": "provide_answer", "answer": "Task complete"}'
        step = ResponseParser.parse_response(response, "task")
        assert step.params.get("answer") == "Task complete"

    def test_markdown_param_extracted_as_answer(self):
        """Lines 232-234: 'markdown' key becomes params['answer']."""
        response = '{"action": "provide_markdown", "markdown": "## Results Done"}'
        step = ResponseParser.parse_response(response, "task")
        assert step.params.get("answer") == "## Results Done"

    def test_thought_param_extracted(self):
        """Line 236: 'thought' key becomes params['thought']."""
        response = (
            '{"action": "reason", "thought": "I should scan the workspace first"}'
        )
        step = ResponseParser.parse_response(response, "task")
        assert step.params.get("thought") == "I should scan the workspace first"


# ==== parse_response - agent_id defaulting ====


class TestParseResponseAgentIdDefault:
    """Cover lines 240-246: agent_id defaulted to localhost for legacy execute."""

    def test_execute_command_without_agent_id_defaults_localhost(self):
        """Lines 245-246: execute with command but no agent_id -> agent_id='localhost'."""
        response = '{"action": "execute_command", "command": "Get-Process"}'
        step = ResponseParser.parse_response(response, "task")
        assert step.tool == "execute"
        assert step.params.get("agent_id") == "localhost"
        assert step.params.get("command") == "Get-Process"

    def test_execute_with_agent_id_not_overwritten(self):
        """Lines 240-244: execute with existing agent_id is not changed."""
        response = '{"tool": "execute", "params": {"agent_id": "remote-host", "command": "ls"}}'
        step = ResponseParser.parse_response(response, "task")
        assert step.tool == "execute"
        assert step.params.get("agent_id") == "remote-host"

    def test_run_command_without_agent_id_defaults_localhost(self):
        """Lines 245-246: 'run_command' action also gets localhost default."""
        response = '{"action": "run_command", "command": "ipconfig"}'
        step = ResponseParser.parse_response(response, "task")
        assert step.tool == "execute"
        assert step.params.get("agent_id") == "localhost"


# ==== parse_response - hallucination block in parse_response ====


class TestParseResponseHallucinationBlock:
    """Cover lines 141-149: hallucination early return in parse_response."""

    def test_hallucinated_response_returns_complete_with_error(self):
        """Lines 142-149: parse_response returns 'complete' with error on hallucination."""
        response = "**execute output:**\nsome fabricated content here"
        step = ResponseParser.parse_response(response, "task")
        assert step.tool == "complete"
        assert "error" in step.params
        assert "INVALID FORMAT" in step.params["error"]
        assert step.reasoning == "Blocked hallucinated response"

    def test_code_block_hallucination_blocked(self):
        """Lines 142-149: Code block in response is blocked."""
        response = "```powershell\nGet-Process\n```"
        step = ResponseParser.parse_response(response, "task")
        assert step.tool == "complete"
        assert "INVALID FORMAT" in step.params.get("error", "")
