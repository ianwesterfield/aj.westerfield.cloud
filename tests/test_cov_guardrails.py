"""Tests for GuardrailEngine - 100% coverage target.
Imports real GuardrailEngine and SessionState, not inline stubs.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "layers", "orchestrator")
)

from services.helpers.guardrails import GuardrailEngine
from services.session_state import SessionState, CompletedStep, ConversationLedger
from schemas.models import Step


@pytest.fixture
def engine():
    return GuardrailEngine()


@pytest.fixture
def state():
    return SessionState()


def make_step(tool="execute", params=None, step_id="test_step"):
    return Step(
        step_id=step_id,
        tool=tool,
        params=params or {},
        batch_id=None,
        reasoning="test",
    )


def make_completed(tool, params=None, success=True, output="ok"):
    return CompletedStep(
        step_id="prev",
        tool=tool,
        params=params or {},
        output_summary=output,
        success=success,
    )


# ==== _check_execute ====
class TestCheckExecute:
    def test_non_execute_tool_passes(self, engine, state):
        step = make_step(tool="think", params={"thought": "hi"})
        result = engine._check_execute(step, state)
        assert result is None

    def test_localhost_always_allowed(self, engine, state):
        step = make_step(
            tool="execute", params={"agent_id": "localhost", "command": "ls"}
        )
        result = engine._check_execute(step, state)
        assert result is None

    def test_no_agents_discovered_suggests_discovery(self, engine, state):
        step = make_step(tool="execute", params={"agent_id": "ws1", "command": "ls"})
        result = engine._check_execute(step, state)
        assert result is not None
        assert result.tool == "execute"
        assert result.params["agent_id"] == "localhost"
        assert "discover-peers" in result.params["command"]

    def test_unknown_agent_blocked(self, engine, state):
        state.discovered_agents = ["ws1", "ws2"]
        step = make_step(tool="execute", params={"agent_id": "ws99", "command": "ls"})
        result = engine._check_execute(step, state)
        assert result is not None
        assert result.tool == "complete"
        assert "ws99" in result.params["error"]
        assert "ws1" in result.params["error"]

    def test_known_agent_passes(self, engine, state):
        state.discovered_agents = ["ws1"]
        step = make_step(
            tool="execute", params={"agent_id": "ws1", "command": "hostname"}
        )
        result = engine._check_execute(step, state)
        assert result is None

    def test_remote_bash_also_checked(self, engine, state):
        step = make_step(tool="remote_bash", params={"agent_id": "ws1"})
        result = engine._check_execute(step, state)
        # No agents discovered < suggests localhost
        assert result is not None
        assert result.params["agent_id"] == "localhost"

    def test_powershell_syntax_fix(self, engine, state):
        state.discovered_agents = ["ws1"]
        # Single quotes in PowerShell with variable = syntax error
        step = make_step(
            tool="execute",
            params={"agent_id": "ws1", "command": "Get-Content 'C:\\file.txt"},
        )
        with patch("services.helpers.powershell_utils.PowerShellValidator") as mock_ps:
            mock_ps.validate_syntax.return_value = ["Unclosed string"]
            mock_ps.fix_command.return_value = "Get-Content 'C:\\file.txt'"
            result = engine._check_execute(step, state)
            # fix_command returns different string → step replaced
            assert result is not None
            assert result.params["command"] == "Get-Content 'C:\\file.txt'"

    def test_powershell_no_fix_needed(self, engine, state):
        state.discovered_agents = ["ws1"]
        step = make_step(
            tool="execute",
            params={"agent_id": "ws1", "command": "hostname"},
        )
        with patch("services.helpers.powershell_utils.PowerShellValidator") as mock_ps:
            mock_ps.validate_syntax.return_value = ["minor"]
            mock_ps.fix_command.return_value = "hostname"  # same as original
            result = engine._check_execute(step, state)
            assert result is None

    def test_powershell_no_errors(self, engine, state):
        state.discovered_agents = ["ws1"]
        step = make_step(
            tool="execute",
            params={"agent_id": "ws1", "command": "hostname"},
        )
        with patch("services.helpers.powershell_utils.PowerShellValidator") as mock_ps:
            mock_ps.validate_syntax.return_value = []
            result = engine._check_execute(step, state)
            assert result is None

    def test_command_as_list(self, engine, state):
        state.discovered_agents = ["ws1"]
        step = make_step(
            tool="execute",
            params={"agent_id": "ws1", "command": ["echo", "hello"]},
        )
        result = engine._check_execute(step, state)
        assert result is None  # list joined, no errors

    def test_command_from_cmd_key(self, engine, state):
        state.discovered_agents = ["ws1"]
        step = make_step(
            tool="execute",
            params={"agent_id": "ws1", "cmd": "hostname"},
        )
        result = engine._check_execute(step, state)
        assert result is None

    def test_agent_from_agent_key(self, engine, state):
        step = make_step(
            tool="execute",
            params={"agent": "ws1", "command": "ls"},
        )
        # No agents discovered
        result = engine._check_execute(step, state)
        assert result is not None
        assert "discover-peers" in result.params["command"]

    def test_empty_command(self, engine, state):
        state.discovered_agents = ["ws1"]
        step = make_step(
            tool="execute",
            params={"agent_id": "ws1"},
        )
        result = engine._check_execute(step, state)
        assert result is None  # no command = nothing to validate


# ==== _check_force_execute ====
class TestCheckForceExecute:
    def test_no_agents_discovered(self, engine, state):
        step = make_step(tool="scan_workspace", params={"path": "C:\\"})
        result = engine._check_force_execute(step, state)
        assert result is None  # No agents → no redirect

    def test_non_scan_tool(self, engine, state):
        state.discovered_agents = ["ws1"]
        step = make_step(tool="think", params={"thought": "hi"})
        result = engine._check_force_execute(step, state)
        assert result is None

    def test_scan_workspace_redirected(self, engine, state):
        state.discovered_agents = ["ws1"]
        state.ledger = ConversationLedger()
        state.ledger.add_request("scan files on ws1")
        step = make_step(tool="scan_workspace", params={"path": "D:\\"})
        with patch("services.helpers.agent_utils.AgentTargetExtractor") as mock_ext:
            mock_ext.extract_target_agent.return_value = "ws1"
            result = engine._check_force_execute(step, state)
        assert result is not None
        assert result.tool == "execute"
        assert result.params["agent_id"] == "ws1"
        assert "D:\\" in result.params["command"]

    def test_execute_shell_redirected(self, engine, state):
        state.discovered_agents = ["ws1"]
        state.ledger = ConversationLedger()
        state.ledger.add_request("run command on ws1")
        step = make_step(tool="execute_shell", params={"cmd": "hostname"})
        with patch("services.helpers.agent_utils.AgentTargetExtractor") as mock_ext:
            mock_ext.extract_target_agent.return_value = "ws1"
            result = engine._check_force_execute(step, state)
        assert result is not None
        assert result.tool == "execute"
        assert result.params["command"] == "hostname"

    def test_execute_shell_with_command_key(self, engine, state):
        state.discovered_agents = ["ws1"]
        state.ledger = ConversationLedger()
        state.ledger.add_request("run command on ws1")
        step = make_step(tool="execute_shell", params={"command": "dir"})
        with patch("services.helpers.agent_utils.AgentTargetExtractor") as mock_ext:
            mock_ext.extract_target_agent.return_value = "ws1"
            result = engine._check_force_execute(step, state)
        assert result is not None
        assert result.params["command"] == "dir"

    def test_no_agent_match_defaults_first(self, engine, state):
        state.discovered_agents = ["ws1"]
        state.ledger = ConversationLedger()
        state.ledger.add_request("do stuff")
        step = make_step(tool="scan_workspace", params={"path": "C:\\"})
        with patch("services.helpers.agent_utils.AgentTargetExtractor") as mock_ext:
            mock_ext.extract_target_agent.return_value = None
            result = engine._check_force_execute(step, state)
        assert result is not None
        assert result.params["agent_id"] == "ws1"  # defaults to first

    def test_user_target_not_found_blocked(self, engine, state):
        state.discovered_agents = ["ws1"]
        state.ledger = ConversationLedger()
        state.ledger.add_request("check 'server99'")
        step = make_step(tool="scan_workspace", params={"path": "C:\\"})
        with patch("services.helpers.agent_utils.AgentTargetExtractor") as mock_ext:
            mock_ext.extract_target_agent.return_value = None
            result = engine._check_force_execute(step, state)
        assert result is not None
        assert result.tool == "complete"
        assert "Target not found" in result.params["error"]

    def test_no_user_requests(self, engine, state):
        state.discovered_agents = ["ws1"]
        state.ledger = ConversationLedger()
        step = make_step(tool="scan_workspace", params={"path": "C:\\"})
        with patch("services.helpers.agent_utils.AgentTargetExtractor") as mock_ext:
            mock_ext.extract_target_agent.return_value = None
            result = engine._check_force_execute(step, state)
        assert result is not None
        assert result.params["agent_id"] == "ws1"  # defaults to first agent


# ==== _check_completion_validity ====
class TestCheckCompletionValidity:
    def test_not_complete_tool(self, engine, state):
        step = make_step(tool="think")
        result = engine._check_completion_validity(step, state)
        assert result is None

    def test_hallucinated_answer_no_execution(self, engine, state):
        step = make_step(
            tool="complete",
            params={
                "answer": "The file contains C:\\Users\\Admin\\documents\\important.txt with 500 lines of configuration"
            },
        )
        with patch("services.helpers.response_parser.ResponseParser") as mock_rp:
            mock_rp.detect_completion_hallucination.return_value = True
            result = engine._check_completion_validity(step, state)
        assert result is not None
        assert "Cannot provide answer without executing" in result.params["error"]

    def test_hallucinated_but_has_execute_steps(self, engine, state):
        state.completed_steps.append(make_completed("execute", success=True))
        step = make_step(
            tool="complete",
            params={
                "answer": "Based on running the command, the server C:\\Windows\\System32\\config.sys has 200 services running with the following detailed listing of each one"
            },
        )
        with patch("services.helpers.response_parser.ResponseParser") as mock_rp:
            mock_rp.detect_completion_hallucination.return_value = True
            result = engine._check_completion_validity(step, state)
        # Has execute steps so hallucination check passes, but long answer triggers force error
        assert result is not None
        assert "No FunnelCloud agents" in result.params["error"]

    def test_hallucinated_only_think_steps(self, engine, state):
        state.completed_steps.append(make_completed("think", success=True))
        step = make_step(
            tool="complete",
            params={
                "answer": "The disk has C:\\Windows\\System32\\config detailed analysis running with full reports"
            },
        )
        with patch("services.helpers.response_parser.ResponseParser") as mock_rp:
            mock_rp.detect_completion_hallucination.return_value = True
            result = engine._check_completion_validity(step, state)
        assert result is not None
        assert "Cannot provide answer without executing" in result.params["error"]

    def test_long_answer_forces_error(self, engine, state):
        step = make_step(
            tool="complete",
            params={
                "answer": "This is a long answer with enough content to exceed the fifty character limit easily"
            },
        )
        with patch("services.helpers.response_parser.ResponseParser") as mock_rp:
            mock_rp.detect_completion_hallucination.return_value = False
            result = engine._check_completion_validity(step, state)
        assert result is not None
        assert "No FunnelCloud agents" in result.params["error"]

    def test_short_answer_passes(self, engine, state):
        step = make_step(tool="complete", params={"answer": "Done"})
        with patch("services.helpers.response_parser.ResponseParser") as mock_rp:
            mock_rp.detect_completion_hallucination.return_value = False
            result = engine._check_completion_validity(step, state)
        assert result is None

    def test_no_answer_passes(self, engine, state):
        step = make_step(tool="complete", params={})
        with patch("services.helpers.response_parser.ResponseParser") as mock_rp:
            mock_rp.detect_completion_hallucination.return_value = False
            result = engine._check_completion_validity(step, state)
        assert result is None


# ==== _check_duplicate_remote_bash ====
class TestCheckDuplicateRemoteBash:
    def test_not_remote_bash(self, engine, state):
        step = make_step(tool="execute")
        result = engine._check_duplicate_remote_bash(step, state)
        assert result is None

    def test_no_duplicate(self, engine, state):
        state.completed_steps.append(
            make_completed("remote_bash", {"agent_id": "ws1", "command": "ls"})
        )
        step = make_step(
            tool="remote_bash", params={"agent_id": "ws1", "command": "whoami"}
        )
        result = engine._check_duplicate_remote_bash(step, state)
        assert result is None

    def test_duplicate_blocked(self, engine, state):
        state.completed_steps.append(
            make_completed("remote_bash", {"agent_id": "ws1", "command": "ls"})
        )
        step = make_step(
            tool="remote_bash", params={"agent_id": "ws1", "command": "ls"}
        )
        result = engine._check_duplicate_remote_bash(step, state)
        assert result is not None
        assert result.tool == "complete"
        assert "already executed" in result.params["answer"]


# ==== _check_duplicate_execute ====
class TestCheckDuplicateExecute:
    def test_not_execute(self, engine, state):
        step = make_step(tool="think")
        result = engine._check_duplicate_execute(step, state)
        assert result is None

    def test_no_duplicate(self, engine, state):
        state.completed_steps.append(
            make_completed("execute", {"agent_id": "ws1", "command": "ls"})
        )
        step = make_step(
            tool="execute", params={"agent_id": "ws1", "command": "whoami"}
        )
        result = engine._check_duplicate_execute(step, state)
        assert result is None

    def test_duplicate_blocked(self, engine, state):
        state.completed_steps.append(
            make_completed("execute", {"agent_id": "ws1", "command": "hostname"})
        )
        step = make_step(
            tool="execute", params={"agent_id": "ws1", "command": "hostname"}
        )
        result = engine._check_duplicate_execute(step, state)
        assert result is not None
        assert "already retrieved" in result.params["answer"]

    def test_previous_failed_not_blocked(self, engine, state):
        state.completed_steps.append(
            make_completed(
                "execute", {"agent_id": "ws1", "command": "hostname"}, success=False
            )
        )
        step = make_step(
            tool="execute", params={"agent_id": "ws1", "command": "hostname"}
        )
        result = engine._check_duplicate_execute(step, state)
        assert result is None

    def test_agent_key_variations(self, engine, state):
        state.completed_steps.append(
            make_completed("execute", {"agent": "ws1", "command": "hostname"})
        )
        step = make_step(tool="execute", params={"agent": "ws1", "command": "hostname"})
        result = engine._check_duplicate_execute(step, state)
        assert result is not None

    def test_agent_name_key(self, engine, state):
        state.completed_steps.append(
            make_completed("execute", {"agent_name": "ws1", "command": "ls"})
        )
        step = make_step(tool="execute", params={"agent_name": "ws1", "command": "ls"})
        result = engine._check_duplicate_execute(step, state)
        assert result is not None


# ==== _check_tool_loops ====
class TestCheckToolLoops:
    def test_execute_exempt(self, engine, state):
        for _ in range(5):
            state.completed_steps.append(make_completed("execute", {"command": "ls"}))
        step = make_step(tool="execute", params={"command": "ls"})
        result = engine._check_tool_loops(step, state)
        assert result is None  # execute is always exempt

    def test_remote_bash_exempt(self, engine, state):
        for _ in range(5):
            state.completed_steps.append(make_completed("remote_bash"))
        step = make_step(tool="remote_bash")
        result = engine._check_tool_loops(step, state)
        assert result is None

    def test_file_tool_loop_detected(self, engine, state):
        for _ in range(3):
            state.completed_steps.append(
                make_completed("write_file", {"path": "/a.txt"})
            )
        step = make_step(tool="write_file", params={"path": "/a.txt"})
        result = engine._check_tool_loops(step, state)
        assert result is not None
        assert "Loop detected" in result.params["error"]

    def test_file_tool_different_paths_ok(self, engine, state):
        state.completed_steps.append(make_completed("write_file", {"path": "/a.txt"}))
        state.completed_steps.append(make_completed("write_file", {"path": "/b.txt"}))
        step = make_step(tool="write_file", params={"path": "/c.txt"})
        result = engine._check_tool_loops(step, state)
        assert result is None

    def test_file_tool_path_key_variation(self, engine, state):
        for _ in range(3):
            state.completed_steps.append(
                make_completed("read_file", {"file_path": "/x.txt"})
            )
        step = make_step(tool="read_file", params={"file_path": "/x.txt"})
        result = engine._check_tool_loops(step, state)
        assert result is not None

    def test_general_tool_loop(self, engine, state):
        for _ in range(3):
            state.completed_steps.append(make_completed("some_tool"))
        step = make_step(tool="some_tool")
        result = engine._check_tool_loops(step, state)
        assert result is not None
        assert "Loop detected" in result.params["error"]

    def test_once_only_tool_scan_workspace(self, engine, state):
        state.completed_steps.append(make_completed("scan_workspace"))
        step = make_step(tool="scan_workspace")
        result = engine._check_tool_loops(step, state)
        assert result is not None
        # once_only threshold=1, params is {} (no "error" key)
        assert result.tool == "complete"

    def test_once_only_tool_dump_state(self, engine, state):
        state.completed_steps.append(make_completed("dump_state"))
        step = make_step(tool="dump_state")
        result = engine._check_tool_loops(step, state)
        assert result is not None

    def test_general_tool_no_history(self, engine, state):
        step = make_step(tool="some_tool")
        result = engine._check_tool_loops(step, state)
        assert result is None

    def test_file_tool_under_threshold(self, engine, state):
        state.completed_steps.append(make_completed("write_file", {"path": "/a.txt"}))
        step = make_step(tool="write_file", params={"path": "/a.txt"})
        result = engine._check_tool_loops(step, state)
        assert result is None  # only 1 time, threshold is 2

    def test_no_path_file_tool(self, engine, state):
        for _ in range(3):
            state.completed_steps.append(make_completed("write_file", {}))
        step = make_step(tool="write_file", params={})
        result = engine._check_tool_loops(step, state)
        # No path and file_tools are in first branch → no general loop check
        assert result is None


# ==== _check_dump_state ====
class TestCheckDumpState:
    def test_not_dump_state(self, engine, state):
        step = make_step(tool="think")
        result = engine._check_dump_state(step, state)
        assert result is None

    def test_first_dump_allowed(self, engine, state):
        step = make_step(tool="dump_state")
        result = engine._check_dump_state(step, state)
        assert result is None

    def test_second_dump_blocked(self, engine, state):
        state.completed_steps.append(make_completed("dump_state"))
        step = make_step(tool="dump_state")
        result = engine._check_dump_state(step, state)
        assert result is not None
        assert result.tool == "complete"


# ==== _check_replace_failures ====
class TestCheckReplaceFailures:
    def test_not_replace_tool(self, engine, state):
        step = make_step(tool="write_file")
        result = engine._check_replace_failures(step, state)
        assert result is None

    def test_first_replace_attempt(self, engine, state):
        step = make_step(
            tool="replace_in_file", params={"path": "/a.txt", "new_text": "hi"}
        )
        result = engine._check_replace_failures(step, state)
        assert result is None

    def test_after_two_failures_auto_corrects(self, engine, state):
        for _ in range(2):
            state.completed_steps.append(
                make_completed("replace_in_file", {"path": "/a.txt"}, success=False)
            )
        step = make_step(
            tool="replace_in_file", params={"path": "/a.txt", "new_text": "content"}
        )
        result = engine._check_replace_failures(step, state)
        assert result is not None
        assert result.tool == "insert_in_file"
        assert result.params["position"] == "start"
        assert result.params["text"] == "content"

    def test_failures_on_different_path_ignored(self, engine, state):
        for _ in range(3):
            state.completed_steps.append(
                make_completed("replace_in_file", {"path": "/b.txt"}, success=False)
            )
        step = make_step(
            tool="replace_in_file", params={"path": "/a.txt", "new_text": "x"}
        )
        result = engine._check_replace_failures(step, state)
        assert result is None


# ==== _check_reread ====
class TestCheckReread:
    def test_not_read_file(self, engine, state):
        step = make_step(tool="write_file")
        result = engine._check_reread(step, state)
        assert result is None

    def test_first_read_allowed(self, engine, state):
        step = make_step(tool="read_file", params={"path": "/a.txt"})
        result = engine._check_reread(step, state)
        assert result is None

    def test_reread_blocked(self, engine, state):
        state.read_files.add("/a.txt")
        step = make_step(tool="read_file", params={"path": "/a.txt"})
        result = engine._check_reread(step, state)
        assert result is not None
        assert "Already read" in result.params["error"]

    def test_reread_file_path_key(self, engine, state):
        state.read_files.add("/b.txt")
        step = make_step(tool="read_file", params={"file_path": "/b.txt"})
        result = engine._check_reread(step, state)
        assert result is not None


# ==== _check_edit_paths ====
class TestCheckEditPaths:
    def test_not_edit_tool(self, engine, state):
        step = make_step(tool="read_file")
        result = engine._check_edit_paths(step, state)
        assert result is None

    def test_path_already_correct(self, engine, state):
        state.files = ["/project/src/main.py"]
        step = make_step(tool="insert_in_file", params={"path": "/project/src/main.py"})
        result = engine._check_edit_paths(step, state)
        assert result is None

    def test_path_corrected(self, engine, state):
        state.files = ["/project/src/main.py"]
        step = make_step(tool="replace_in_file", params={"path": "main.py"})
        result = engine._check_edit_paths(step, state)
        # Returns None after mutating step.params
        assert result is None
        assert step.params["path"] == "/project/src/main.py"

    def test_no_similar_path(self, engine, state):
        state.files = ["/project/src/main.py"]
        step = make_step(tool="insert_in_file", params={"path": "other.py"})
        result = engine._check_edit_paths(step, state)
        assert result is None

    def test_no_files_known(self, engine, state):
        step = make_step(tool="append_to_file", params={"path": "main.py"})
        result = engine._check_edit_paths(step, state)
        assert result is None

    def test_no_path_provided(self, engine, state):
        state.files = ["/project/src/main.py"]
        step = make_step(tool="insert_in_file", params={})
        result = engine._check_edit_paths(step, state)
        assert result is None

    def test_file_path_key(self, engine, state):
        state.files = ["/project/src/main.py"]
        step = make_step(tool="insert_in_file", params={"file_path": "main.py"})
        result = engine._check_edit_paths(step, state)
        # path key is "path" or "file_path" - but correction writes to "path"
        assert result is None


# ==== apply() ====
class TestApply:
    def test_no_guardrails_triggered(self, engine, state):
        state.discovered_agents = ["ws1"]
        step = make_step(tool="think", params={"thought": "hi"})
        result = engine.apply(step, state)
        assert result.tool == "think"  # unchanged

    def test_first_guardrail_wins(self, engine, state):
        # No agents discovered + execute on unknown agent = discovery suggestion
        step = make_step(tool="execute", params={"agent_id": "ws1", "command": "ls"})
        result = engine.apply(step, state)
        assert result.tool == "execute"
        assert result.params["agent_id"] == "localhost"
