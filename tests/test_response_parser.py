"""
Tests for ResponseParser - 100% coverage target.
"""

import pytest
import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "layers", "orchestrator")
)

from services.helpers.response_parser import ResponseParser


class TestDetectHallucination:
    def test_no_hallucination_valid_json(self):
        response = '{"tool": "execute", "params": {"agent_id": "localhost"}}'
        assert ResponseParser.detect_hallucination(response) is None

    def test_hallucination_narrating_execution(self):
        response = "**read_file output:**\nSome file content here"
        result = ResponseParser.detect_hallucination(response)
        assert result is not None
        assert "narrating" in result.lower()

    def test_hallucination_results_pattern(self):
        response = "↳ Got 15 results from the scan"
        result = ResponseParser.detect_hallucination(response)
        assert result is not None

    def test_hallucination_executed_successfully(self):
        response = "The command has been executed successfully on the server"
        result = ResponseParser.detect_hallucination(response)
        assert result is not None

    def test_hallucination_code_block(self):
        response = '```json\n{"data": true}\n```'
        result = ResponseParser.detect_hallucination(response)
        assert result is not None

    def test_hallucination_inside_think_block_ignored(self):
        response = (
            '<think>The script was executed</think>{"tool": "execute", "params": {}}'
        )
        result = ResponseParser.detect_hallucination(response)
        assert result is None

    def test_narrative_hallucination_indicators(self):
        # Must be >100 chars to trigger narrative check
        response = "I successfully retrieved all the folder sizes from the server and stored everything properly in the database for further analysis and reporting"
        result = ResponseParser.detect_hallucination(response)
        assert result is not None

    def test_narrative_hallucination_results_show(self):
        # Must be >100 chars to trigger narrative check
        response = "The results show that the server has 50GB of free disk space and many other important metrics that we should review carefully before proceeding"
        result = ResponseParser.detect_hallucination(response)
        assert result is not None

    def test_narrative_no_json_long_text(self):
        response = "This is a long narrative text without any JSON " * 5
        result = ResponseParser.detect_hallucination(response)
        assert result is not None
        assert "narrative" in result.lower() or "JSON" in result

    def test_short_non_json_no_hallucination(self):
        # Short text under 100 chars without hallucination indicators
        response = "ok"
        result = ResponseParser.detect_hallucination(response)
        assert result is None

    def test_execute_output_results(self):
        response = "execute output results:\n"
        result = ResponseParser.detect_hallucination(response)
        assert result is not None

    def test_got_lines_indicator(self):
        response = "↳ Got 42 lines from the log"
        result = ResponseParser.detect_hallucination(response)
        assert result is not None

    def test_got_folders(self):
        response = "↳ Got 3 folders in the directory"
        result = ResponseParser.detect_hallucination(response)
        assert result is not None


class TestDetectCompletionHallucination:
    def test_clean_answer(self):
        assert (
            ResponseParser.detect_completion_hallucination("Task completed.") is False
        )

    def test_hallucinated_file_listing(self):
        assert (
            ResponseParser.detect_completion_hallucination(
                "here are the top 10 largest files"
            )
            is True
        )

    def test_hallucinated_windows_paths(self):
        assert (
            ResponseParser.detect_completion_hallucination("c:\\windows\\system32")
            is True
        )

    def test_hallucinated_file_sizes(self):
        assert (
            ResponseParser.detect_completion_hallucination("file size is 500 MB")
            is True
        )

    def test_hallucinated_binary(self):
        assert (
            ResponseParser.detect_completion_hallucination("explorer.exe is running")
            is True
        )

    def test_hallucinated_directory_listing(self):
        assert (
            ResponseParser.detect_completion_hallucination("directory listing output")
            is True
        )

    def test_hallucinated_table(self):
        assert ResponseParser.detect_completion_hallucination("| name | size |") is True

    def test_windows_path_regex(self):
        assert (
            ResponseParser.detect_completion_hallucination(
                "Found C:\\Users\\admin\\file.txt"
            )
            is True
        )

    def test_empty_string(self):
        assert ResponseParser.detect_completion_hallucination("") is False

    def test_scanned_keyword(self):
        assert (
            ResponseParser.detect_completion_hallucination(
                "I scanned the entire directory"
            )
            is True
        )

    def test_home_path(self):
        assert (
            ResponseParser.detect_completion_hallucination("Located at /home/user")
            is True
        )

    def test_dll_reference(self):
        assert (
            ResponseParser.detect_completion_hallucination("kernel32.dll loaded")
            is True
        )

    def test_iso_reference(self):
        assert (
            ResponseParser.detect_completion_hallucination("Found backup.iso file")
            is True
        )

    def test_bytes_keyword(self):
        assert (
            ResponseParser.detect_completion_hallucination("Total: 1024 bytes") is True
        )

    def test_gb_keyword(self):
        assert (
            ResponseParser.detect_completion_hallucination("Free space: 120 GB") is True
        )

    def test_kb_keyword(self):
        assert ResponseParser.detect_completion_hallucination("File is 50 KB") is True


class TestExtractFirstJsonObject:
    def test_simple_object(self):
        result = ResponseParser.extract_first_json_object('{"key": "value"}')
        assert result == '{"key": "value"}'

    def test_nested_object(self):
        text = '{"outer": {"inner": "value"}}'
        result = ResponseParser.extract_first_json_object(text)
        assert result == text

    def test_with_prefix(self):
        text = 'Some text before {"tool": "execute"}'
        result = ResponseParser.extract_first_json_object(text)
        assert result == '{"tool": "execute"}'

    def test_with_suffix(self):
        text = '{"tool": "think"} some text after'
        result = ResponseParser.extract_first_json_object(text)
        assert result == '{"tool": "think"}'

    def test_no_json(self):
        result = ResponseParser.extract_first_json_object("no json here")
        assert result == "no json here"

    def test_empty_string(self):
        result = ResponseParser.extract_first_json_object("")
        assert result == ""

    def test_unclosed_brace(self):
        result = ResponseParser.extract_first_json_object('{"key": "value"')
        assert result == '{"key": "value"'

    def test_string_with_braces(self):
        text = '{"key": "value with {braces}"}'
        result = ResponseParser.extract_first_json_object(text)
        assert result == text

    def test_escaped_quotes_in_string(self):
        text = '{"key": "val\\"ue"}'
        result = ResponseParser.extract_first_json_object(text)
        assert result == text

    def test_multiple_json_objects_returns_first(self):
        text = '{"first": 1} {"second": 2}'
        result = ResponseParser.extract_first_json_object(text)
        assert result == '{"first": 1}'


class TestParseResponse:
    def test_valid_json_tool_call(self):
        response = '{"tool": "execute", "params": {"agent_id": "localhost", "command": "hostname"}}'
        step = ResponseParser.parse_response(response, "test task")
        assert step.tool == "execute"
        assert step.params["agent_id"] == "localhost"

    def test_valid_json_with_thinking(self):
        response = '<think>I need to check the agent</think>{"tool": "think", "params": {"thought": "analyzing"}}'
        step = ResponseParser.parse_response(response, "test task")
        assert step.tool == "think"
        assert "analyzing" in str(step.params)
        assert step.reasoning  # Should have thinking content

    def test_invalid_json_returns_error_step(self):
        response = "this is not json at all {broken"
        step = ResponseParser.parse_response(response, "test task")
        assert step.tool == "complete"
        assert "error" in step.params

    def test_hallucination_blocked(self):
        response = "**read_file output:** content here"
        step = ResponseParser.parse_response(response, "test task")
        assert step.tool == "complete"
        assert "error" in step.params
        assert "INVALID FORMAT" in step.params["error"]

    def test_empty_response(self):
        step = ResponseParser.parse_response("", "test task")
        # Empty string -> narrative text -> hallucination or parse error
        assert step.tool == "complete"

    def test_long_tool_name_normalized(self):
        response = (
            '{"tool": "scan_workspace is what I should use here maybe", "params": {}}'
        )
        step = ResponseParser.parse_response(response, "test task")
        assert step.tool == "scan_workspace"

    def test_unknown_long_tool_name(self):
        response = '{"tool": "some_really_long_tool_name_that_does_not_match_anything_at_all", "params": {}}'
        step = ResponseParser.parse_response(response, "test task")
        assert step.tool == "unknown"

    def test_action_key_fallback(self):
        response = '{"action": "think", "params": {"thought": "hmm"}}'
        step = ResponseParser.parse_response(response, "test task")
        assert step.tool == "think"

    def test_step_key_fallback(self):
        response = '{"step": "complete", "params": {"answer": "done"}}'
        step = ResponseParser.parse_response(response, "test task")
        assert step.tool == "complete"

    def test_params_from_top_level_path(self):
        response = '{"tool": "read_file", "path": "/some/file.py"}'
        step = ResponseParser.parse_response(response, "test task")
        assert step.params.get("path") == "/some/file.py"

    def test_params_from_top_level_file_path(self):
        response = '{"tool": "read_file", "file_path": "/some/file.py"}'
        step = ResponseParser.parse_response(response, "test task")
        assert step.params.get("path") == "/some/file.py"

    def test_params_from_top_level_command(self):
        response = '{"tool": "execute", "command": "hostname"}'
        step = ResponseParser.parse_response(response, "test task")
        assert step.params.get("command") == "hostname"

    def test_params_from_top_level_answer(self):
        response = '{"tool": "complete", "answer": "all done"}'
        step = ResponseParser.parse_response(response, "test task")
        assert step.params.get("answer") == "all done"

    def test_reasoning_from_note(self):
        response = '{"tool": "think", "params": {}, "note": "analyzing data"}'
        step = ResponseParser.parse_response(response, "test task")
        assert step.reasoning == "analyzing data"

    def test_reasoning_from_reasoning_field(self):
        response = '{"tool": "think", "params": {}, "reasoning": "step logic"}'
        step = ResponseParser.parse_response(response, "test task")
        assert step.reasoning == "step logic"

    def test_reasoning_from_description(self):
        response = '{"tool": "think", "params": {}, "description": "desc text"}'
        step = ResponseParser.parse_response(response, "test task")
        assert step.reasoning == "desc text"

    def test_reasoning_from_instruction(self):
        response = '{"tool": "think", "params": {}, "instruction": "instr text"}'
        step = ResponseParser.parse_response(response, "test task")
        assert step.reasoning == "instr text"

    def test_batch_id_passed_through(self):
        response = '{"tool": "execute", "params": {}, "batch_id": "batch_001"}'
        step = ResponseParser.parse_response(response, "test task")
        assert step.batch_id == "batch_001"

    def test_json_with_backslash_fix(self):
        response = (
            r'{"tool": "execute", "params": {"command": "Get-ChildItem C:\Users"}}'
        )
        step = ResponseParser.parse_response(response, "test task")
        assert step.tool == "execute"

    def test_known_tools_list(self):
        for tool in [
            "scan_workspace",
            "read_file",
            "write_file",
            "execute_shell",
            "execute",
            "think",
            "complete",
            "dump_state",
        ]:
            # Tool name embedded in a long string - avoid "think" in the narrative
            response = f'{{"tool": "I want to use {tool} for this operation and analysis", "params": {{}}}}'
            step = ResponseParser.parse_response(response, "test")
            assert step.tool == tool, f"Expected {tool}, got {step.tool}"


class TestMissedPaths:
    """Cover remaining uncovered lines in response_parser."""

    def test_windows_path_hallucination(self):
        """Line 96-97: Windows path hallucination detection.
        The path must NOT contain any COMPLETION_HALLUCINATION_INDICATORS
        (e.g. c:\\users) or is_hallucinating is already True before the regex check.
        """
        result = ResponseParser.detect_completion_hallucination(
            "The report is at D:\\MyData\\Report.docx and looks good"
        )
        assert result is True

    def test_extract_first_json_unclosed(self):
        """Lines 96-97: text[start:] returned for unclosed JSON."""
        result = ResponseParser.extract_first_json_object('before {"key": "val')
        assert result == '{"key": "val'
