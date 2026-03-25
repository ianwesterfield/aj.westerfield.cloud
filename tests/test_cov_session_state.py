"""Tests for SessionState - 100% coverage target.
Imports real SessionState and all dataclasses.
"""

import pytest
import sys
import os
import json

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "layers", "orchestrator")
)

from services.session_state import (
    SessionState,
    CompletedStep,
    ConversationLedger,
    LedgerEntry,
    CommandFlowContext,
    CommandFlowEntry,
    FileMetadata,
    EnvironmentFacts,
    TaskPlan,
    TaskPlanItem,
    get_session_state,
    reset_session_state,
    get_existing_session,
    cleanup_session,
    get_active_sessions,
    _session_states,
)


# ==== CommandFlowContext ====
class TestCommandFlowContext:
    def test_add_entry(self):
        ctx = CommandFlowContext()
        entry = ctx.add_entry(
            step_index=1,
            tool="execute",
            success=True,
            output="hello",
            agent_id="ws1",
            command="hostname",
            error=None,
            duration_ms=50,
        )
        assert entry.step_index == 1
        assert entry.output_preview == "hello"
        assert entry.output_hash != ""
        assert "execute" in entry.tags

    def test_add_entry_empty_output(self):
        ctx = CommandFlowContext()
        entry = ctx.add_entry(step_index=1, tool="think", success=True, output="")
        assert entry.output_preview == ""
        assert entry.output_hash == ""

    def test_query_by_agent(self):
        ctx = CommandFlowContext()
        ctx.add_entry(1, "execute", True, "ok", agent_id="ws1")
        ctx.add_entry(2, "execute", True, "ok", agent_id="ws2")
        assert len(ctx.query_by_agent("ws1")) == 1

    def test_query_by_tag(self):
        ctx = CommandFlowContext()
        ctx.add_entry(1, "execute", True, "ok")
        ctx.add_entry(2, "think", True, "ok")
        assert len(ctx.query_by_tag("execute")) == 1

    def test_query_failures(self):
        ctx = CommandFlowContext()
        ctx.add_entry(1, "execute", True, "ok")
        ctx.add_entry(2, "execute", False, "", error="fail")
        assert len(ctx.query_failures()) == 1

    def test_query_recent(self):
        ctx = CommandFlowContext()
        for i in range(10):
            ctx.add_entry(i, "execute", True, f"out{i}")
        assert len(ctx.query_recent(3)) == 3
        assert ctx.query_recent(3)[0].step_index == 7

    def test_query_recent_empty(self):
        ctx = CommandFlowContext()
        assert ctx.query_recent() == []

    def test_get_agents_queried(self):
        ctx = CommandFlowContext()
        ctx.add_entry(1, "execute", True, "ok", agent_id="ws1")
        ctx.add_entry(2, "think", True, "ok")  # no agent
        assert ctx.get_agents_queried() == ["ws1"]

    def test_has_executed_on(self):
        ctx = CommandFlowContext()
        ctx.add_entry(1, "execute", True, "ok", agent_id="ws1")
        ctx.add_entry(2, "think", True, "ok", agent_id="ws1")
        assert ctx.has_executed_on("ws1") is True
        assert ctx.has_executed_on("ws2") is False

    def test_summarize_for_replan_empty(self):
        ctx = CommandFlowContext()
        assert "No commands" in ctx.summarize_for_replan()

    def test_summarize_for_replan_with_data(self):
        ctx = CommandFlowContext()
        ctx.original_goal = "check servers"
        ctx.add_entry(1, "execute", True, "ok", agent_id="ws1")
        ctx.add_entry(2, "execute", False, "", agent_id="ws1", error="timeout")
        result = ctx.summarize_for_replan()
        assert "check servers" in result
        assert "1 ok" in result
        assert "1 failed" in result
        assert "timeout" in result

    def test_format_step_summary_execute(self):
        ctx = CommandFlowContext()
        entry = ctx.add_entry(
            1, "execute", True, "ok", agent_id="ws1", command="hostname"
        )
        summary = ctx.format_step_summary(entry)
        assert "ws1" in summary
        assert "hostname" in summary
        assert "✓" in summary

    def test_format_step_summary_think(self):
        ctx = CommandFlowContext()
        entry = ctx.add_entry(1, "think", True, "ok")
        summary = ctx.format_step_summary(entry)
        assert "think" in summary

    def test_format_step_summary_failed(self):
        ctx = CommandFlowContext()
        entry = ctx.add_entry(1, "execute", False, "", agent_id="ws1", command="bad")
        summary = ctx.format_step_summary(entry)
        assert "✗" in summary


# ==== ConversationLedger ====
class TestConversationLedger:
    def test_add_request(self):
        ledger = ConversationLedger()
        ledger.add_request("hello")
        assert len(ledger.user_requests) == 1
        assert len(ledger.entries) == 1

    def test_add_request_long(self):
        ledger = ConversationLedger()
        ledger.add_request("x" * 200)
        assert "..." in ledger.entries[0].summary

    def test_add_request_truncation(self):
        ledger = ConversationLedger()
        for i in range(25):
            ledger.add_request(f"req{i}")
        assert len(ledger.user_requests) == 20

    def test_add_action(self):
        ledger = ConversationLedger()
        ledger.add_action("execute", "hostname", "ok")
        assert len(ledger.entries) == 1
        assert ledger.entries[0].entry_type == "action"

    def test_add_action_truncation(self):
        ledger = ConversationLedger()
        for i in range(55):
            ledger.add_action("t", "p", "r")
        assert len(ledger.entries) == 50

    def test_extract_value(self):
        ledger = ConversationLedger()
        ledger.extract_value("IP", "10.0.0.1", "execute")
        assert ledger.extracted_values["IP"] == "10.0.0.1"
        assert "execute" in ledger.entries[0].summary

    def test_extract_value_no_source(self):
        ledger = ConversationLedger()
        ledger.extract_value("port", "8080")
        assert "port" in ledger.entries[0].summary
        assert "from" not in ledger.entries[0].summary

    def test_format_for_prompt_empty(self):
        ledger = ConversationLedger()
        assert ledger.format_for_prompt() == ""

    def test_format_for_prompt_full(self):
        ledger = ConversationLedger()
        ledger.extract_value("IP", "10.0.0.1")
        ledger.add_request("check servers")
        ledger.add_action("execute", "hostname", "ws1")
        result = ledger.format_for_prompt()
        assert "10.0.0.1" in result
        assert "check servers" in result
        assert "hostname" in result

    def test_format_for_prompt_long_result(self):
        ledger = ConversationLedger()
        ledger.add_action("execute", "cmd", "x" * 100)
        result = ledger.format_for_prompt()
        assert "..." in result


# ==== FileMetadata ====
class TestFileMetadata:
    def test_to_summary(self):
        meta = FileMetadata(path="/a.py", size_human="1.2 KiB", line_count=50)
        s = meta.to_summary()
        assert "/a.py" in s
        assert "1.2 KiB" in s
        assert "50 lines" in s

    def test_to_summary_minimal(self):
        meta = FileMetadata(path="/b.txt")
        s = meta.to_summary()
        assert "/b.txt" in s


# ==== EnvironmentFacts ====
class TestEnvironmentFacts:
    def test_add_observation_unique(self):
        ef = EnvironmentFacts()
        ef.add_observation("fact1")
        ef.add_observation("fact1")  # duplicate
        assert len(ef.observations) == 1

    def test_add_observation_empty(self):
        ef = EnvironmentFacts()
        ef.add_observation("")
        assert len(ef.observations) == 0

    def test_add_observation_truncation(self):
        ef = EnvironmentFacts()
        for i in range(25):
            ef.add_observation(f"fact{i}")
        assert len(ef.observations) == 20


# ==== TaskPlan ====
class TestTaskPlan:
    def test_add_item(self):
        plan = TaskPlan()
        plan.add_item("Step 1", tool_hint="execute")
        assert len(plan.items) == 1
        assert plan.items[0].index == 1

    def test_mark_in_progress(self):
        plan = TaskPlan()
        plan.add_item("Step 1")
        plan.mark_in_progress(1)
        assert plan.items[0].status == "in_progress"

    def test_mark_completed(self):
        plan = TaskPlan()
        plan.add_item("Step 1")
        plan.mark_completed(1)
        assert plan.items[0].status == "completed"

    def test_mark_skipped(self):
        plan = TaskPlan()
        plan.add_item("Step 1")
        plan.mark_skipped(1, "not needed")
        assert plan.items[0].status == "skipped"
        assert "not needed" in plan.items[0].description

    def test_mark_skipped_no_reason(self):
        plan = TaskPlan()
        plan.add_item("Step 1")
        plan.mark_skipped(1)
        assert plan.items[0].status == "skipped"

    def test_get_current_item(self):
        plan = TaskPlan()
        plan.add_item("A")
        plan.add_item("B")
        plan.mark_completed(1)
        current = plan.get_current_item()
        assert current.description == "B"

    def test_get_current_item_none(self):
        plan = TaskPlan()
        plan.add_item("A")
        plan.mark_completed(1)
        assert plan.get_current_item() is None

    def test_get_progress(self):
        plan = TaskPlan()
        plan.add_item("A")
        plan.add_item("B")
        plan.mark_completed(1)
        completed, total = plan.get_progress()
        assert completed == 1
        assert total == 2

    def test_is_complete(self):
        plan = TaskPlan()
        plan.add_item("A")
        plan.add_item("B")
        assert plan.is_complete() is False
        plan.mark_completed(1)
        plan.mark_skipped(2)
        assert plan.is_complete() is True

    def test_format_for_display(self):
        plan = TaskPlan()
        plan.add_item("Step A")
        plan.add_item("Step B")
        plan.mark_completed(1)
        plan.mark_in_progress(2)
        display = plan.format_for_display()
        assert "✅" in display
        assert "⏳" in display

    def test_format_for_display_empty(self):
        plan = TaskPlan()
        assert plan.format_for_display() == ""

    def test_format_for_prompt(self):
        plan = TaskPlan()
        plan.add_item("Step A")
        plan.add_item("Step B")
        plan.mark_completed(1)
        prompt = plan.format_for_prompt()
        assert "DONE" in prompt
        assert "TODO" in prompt
        assert "CURRENT TASK" in prompt

    def test_format_for_prompt_all_done(self):
        plan = TaskPlan()
        plan.add_item("A")
        plan.mark_completed(1)
        prompt = plan.format_for_prompt()
        assert "ALL STEPS COMPLETE" in prompt

    def test_format_for_prompt_empty(self):
        plan = TaskPlan()
        assert plan.format_for_prompt() == ""

    def test_format_for_display_skipped(self):
        plan = TaskPlan()
        plan.add_item("Skippable")
        plan.mark_skipped(1)
        display = plan.format_for_display()
        assert "⏭" in display

    def test_format_for_display_unknown_status(self):
        """Line 422: unknown status gets bullet icon."""
        plan = TaskPlan()
        plan.add_item("Item")
        plan.items[0].status = "unknown_status"
        display = plan.format_for_display()
        assert "•" in display


# ==== SessionState core ====
class TestSessionStateCore:
    def test_initialize_goal(self):
        s = SessionState()
        s.initialize_goal("check servers")
        assert s.command_flow.original_goal == "check servers"
        assert len(s.ledger.user_requests) == 1

    def test_set_task_plan(self):
        s = SessionState()
        plan = TaskPlan()
        plan.add_item("Step 1")
        s.set_task_plan(plan)
        assert s.task_plan is plan

    def test_advance_plan(self):
        s = SessionState()
        plan = TaskPlan()
        plan.add_item("A")
        plan.add_item("B")
        s.set_task_plan(plan)
        s.advance_plan()
        assert plan.items[0].status == "completed"

    def test_advance_plan_no_plan(self):
        s = SessionState()
        s.advance_plan()  # no-op

    def test_add_user_request(self):
        s = SessionState()
        s.add_user_request("hello")
        assert len(s.ledger.user_requests) == 1

    def test_record_command_flow(self):
        s = SessionState()
        s.record_command_flow(
            "execute", {"agent_id": "ws1", "command": "ls"}, "ok", True
        )
        assert len(s.command_flow.entries) == 1
        assert s.command_flow.entries[0].agent_id == "ws1"

    def test_record_command_flow_non_execute(self):
        s = SessionState()
        s.record_command_flow("think", {}, "ok", True)
        assert s.command_flow.entries[0].agent_id is None

    def test_get_ooda_context(self):
        s = SessionState()
        s.record_command_flow("execute", {"command": "ls"}, "ok", True)
        result = s.get_ooda_context_for_replan()
        assert "Steps executed" in result

    def test_can_replan(self):
        s = SessionState()
        assert s.can_replan() is True
        for _ in range(3):
            s.increment_replan()
        assert s.can_replan() is False

    def test_has_scanned(self):
        s = SessionState()
        assert s.has_scanned(".") is False
        s.scanned_paths.add(".")
        assert s.has_scanned(".") is True

    def test_has_edited(self):
        s = SessionState()
        assert s.has_edited("/a.py") is False
        s.edited_files.add("/a.py")
        assert s.has_edited("/a.py") is True

    def test_has_read(self):
        s = SessionState()
        assert s.has_read("/a.py") is False
        s.read_files.add("/a.py")
        assert s.has_read("/a.py") is True

    def test_reset(self):
        s = SessionState()
        s.files.append("a.py")
        s.read_files.add("a.py")
        s.edited_files.add("a.py")
        s.user_info["name"] = "AJ"
        s.reset()
        assert len(s.files) == 0
        assert len(s.read_files) == 0
        assert s.user_info["name"] == "AJ"  # preserved

    def test_get_total_size(self):
        s = SessionState()
        assert s.get_total_size() is None
        s.file_metadata["/a.py"] = FileMetadata(path="/a.py", size_bytes=1024)
        result = s.get_total_size()
        assert result is not None
        assert "KiB" in result

    def test_get_total_size_zero(self):
        s = SessionState()
        s.file_metadata["/a.py"] = FileMetadata(path="/a.py", size_bytes=0)
        assert s.get_total_size() is None

    def test_get_file_info(self):
        s = SessionState()
        meta = FileMetadata(path="/a.py", size_bytes=100)
        s.file_metadata["/a.py"] = meta
        assert s.get_file_info("/a.py") is meta
        assert s.get_file_info("/b.py") is None

    def test_get_unread_files(self):
        s = SessionState()
        s.files = ["a.py", "b.py"]
        s.read_files.add("a.py")
        assert s.get_unread_files() == ["b.py"]


# ==== update_from_step ====
class TestUpdateFromStep:
    def test_scan_workspace(self):
        s = SessionState()
        output = "a.py  file  1.2 KiB  2025-01-01\nlib/  dir  -  2025-01-01"
        s.update_from_step("scan_workspace", {"path": "."}, output, True)
        assert "." in s.scanned_paths
        assert len(s.completed_steps) == 1

    def test_read_file(self):
        s = SessionState()
        s.update_from_step("read_file", {"path": "/a.py"}, "content\nline2", True)
        assert "/a.py" in s.read_files
        # Creates metadata entry
        assert "/a.py" in s.file_metadata

    def test_read_file_existing_metadata(self):
        s = SessionState()
        s.file_metadata["/a.py"] = FileMetadata(path="/a.py", size_bytes=100)
        s.update_from_step("read_file", {"path": "/a.py"}, "content", True)
        assert s.file_metadata["/a.py"].line_count == 1

    def test_read_file_empty_output(self):
        s = SessionState()
        s.update_from_step("read_file", {"path": "/a.py"}, "", True)
        assert "/a.py" in s.read_files

    def test_write_file_success(self):
        s = SessionState()
        s.update_from_step("write_file", {"path": "/a.py"}, "ok", True)
        assert "/a.py" in s.edited_files

    def test_write_file_failure(self):
        s = SessionState()
        s.update_from_step("write_file", {"path": "/a.py"}, "err", False)
        assert "/a.py" not in s.edited_files

    def test_replace_in_file(self):
        s = SessionState()
        s.update_from_step("replace_in_file", {"path": "/a.py"}, "ok", True)
        assert "/a.py" in s.edited_files

    def test_insert_in_file(self):
        s = SessionState()
        s.update_from_step("insert_in_file", {"path": "/a.py"}, "ok", True)
        assert "/a.py" in s.edited_files

    def test_append_to_file(self):
        s = SessionState()
        s.update_from_step("append_to_file", {"path": "/a.py"}, "ok", True)
        assert "/a.py" in s.edited_files

    def test_execute_shell(self):
        s = SessionState()
        s.update_from_step(
            "execute_shell", {"command": "python --version"}, "Python 3.11.0", True
        )
        assert s.environment_facts.python_version == "3.11.0"

    def test_none_tool(self):
        s = SessionState()
        s.update_from_step(
            "none", {"reason": "already present", "path": "/a.py"}, "", True
        )
        assert "skipped" in s.completed_steps[0].output_summary

    def test_none_tool_no_path(self):
        s = SessionState()
        s.update_from_step("none", {"reason": "noop"}, "", True)
        assert "skipped" in s.completed_steps[0].output_summary

    def test_dump_state(self):
        s = SessionState()
        s.update_from_step("dump_state", {}, "", True)
        assert "dump_state" in s.completed_steps[0].output_summary

    def test_remote_bash(self):
        s = SessionState()
        s.update_from_step(
            "remote_bash", {"command": "hostname", "agent_id": "ws1"}, "host1", True
        )
        assert "ws1" in s.queried_agents

    def test_execute_discover_peers(self):
        s = SessionState()
        peers_json = json.dumps(
            [
                {"Id": "ws1", "hostname": "host1"},
                {"Id": "ws2", "hostname": "host2"},
            ]
        )
        s.update_from_step(
            "execute",
            {"command": "Invoke-RestMethod discover-peers", "agent_id": "localhost"},
            peers_json,
            True,
        )
        assert s.agents_verified is True
        assert "ws1" in s.discovered_agents
        assert "ws2" in s.discovered_agents

    def test_execute_discover_peers_invalid_json(self):
        s = SessionState()
        s.update_from_step(
            "execute",
            {"command": "Invoke-RestMethod discover-peers", "agent_id": "localhost"},
            'not json but has "Id": "ws1" in it',
            True,
        )
        assert s.agents_verified is True
        assert "ws1" in s.discovered_agents

    def test_execute_discover_peers_empty(self):
        s = SessionState()
        s.update_from_step(
            "execute",
            {"command": "discover-peers", "agent_id": "localhost"},
            "[]",
            True,
        )
        assert s.agents_verified is True
        assert s.discovered_agents == []

    def test_execute_remote_agent_tracked(self):
        s = SessionState()
        s.update_from_step(
            "execute",
            {"command": "hostname", "agent_id": "ws1"},
            "host1",
            True,
        )
        assert "ws1" in s.queried_agents

    def test_execute_localhost_not_tracked(self):
        s = SessionState()
        s.update_from_step(
            "execute",
            {"command": "ls", "agent_id": "localhost"},
            "ok",
            True,
        )
        assert "localhost" not in s.queried_agents

    def test_execute_failed_agent_not_tracked(self):
        s = SessionState()
        s.update_from_step(
            "execute",
            {"command": "ls", "agent_id": "ws1"},
            "err",
            False,
        )
        assert "ws1" not in s.queried_agents

    def test_unknown_tool(self):
        s = SessionState()
        s.update_from_step("mystery_tool", {}, "output", True)
        assert "mystery_tool" in s.completed_steps[0].output_summary

    def test_error_classification(self):
        s = SessionState()
        s.update_from_step("execute", {"command": "ls"}, "Permission denied", False)
        assert s.completed_steps[0].error_type == "permission_denied"

    def test_agent_from_various_keys(self):
        s = SessionState()
        s.update_from_step("execute", {"command": "ls", "agent": "ws1"}, "ok", True)
        assert "ws1" in s.queried_agents

    def test_agent_from_agent_name(self):
        s = SessionState()
        s.update_from_step("execute", {"command": "ls", "agentName": "ws1"}, "ok", True)
        assert "ws1" in s.queried_agents

    def test_extract_important_values(self):
        s = SessionState()
        s.update_from_step("execute", {"command": "ip addr"}, "inet 192.168.1.1", True)
        assert any("192.168.1.1" in v for v in s.ledger.extracted_values.values())


# ==== _parse_scan_output ====
class TestParseScanOutput:
    def test_basic_parse(self):
        s = SessionState()
        output = "a.py  file  1.2 KiB  2025-01-01\nlib/  dir  -  2025-01-01"
        s._parse_scan_output(output, ".")
        assert "a.py" in s.files
        assert "lib" in s.dirs

    def test_with_base_path(self):
        s = SessionState()
        output = "main.py  file  500 B  2025-01-01"
        s._parse_scan_output(output, "/project/src")
        assert "/project/src/main.py" in s.files

    def test_skip_headers(self):
        s = SessionState()
        output = "PATH: .\nNAME  TYPE  SIZE\n─────────\na.py  file  100 B"
        s._parse_scan_output(output, ".")
        assert "a.py" in s.files

    def test_skip_totals(self):
        s = SessionState()
        output = "a.py  file  100 B\nTOTAL: 1 item (0 dirs, 1 file)"
        s._parse_scan_output(output, ".")
        assert "a.py" in s.files
        assert s.environment_facts.total_file_count == 1

    def test_empty_output(self):
        s = SessionState()
        s._parse_scan_output("", ".")
        assert len(s.files) == 0

    def test_skip_ellipsis(self):
        s = SessionState()
        s._parse_scan_output("... truncated", ".")
        assert len(s.files) == 0

    def test_size_mib(self):
        s = SessionState()
        output = "big.bin  file  2.5 MiB  2025-01-01"
        s._parse_scan_output(output, ".")
        assert "big.bin" in s.files
        assert s.file_metadata["big.bin"].size_bytes == int(2.5 * 1024**2)

    def test_size_numeric_only(self):
        s = SessionState()
        output = "small.txt  file  500  2025-01-01"
        s._parse_scan_output(output, ".")
        assert "small.txt" in s.files

    def test_no_size_field(self):
        s = SessionState()
        output = "file.txt  file"
        s._parse_scan_output(output, ".")
        assert "file.txt" in s.files

    def test_duplicate_files_skipped(self):
        s = SessionState()
        s.files.append("a.py")
        s._parse_scan_output("a.py  file  100 B", ".")
        assert s.files.count("a.py") == 1

    def test_duplicate_dirs_skipped(self):
        s = SessionState()
        s.dirs.append("lib")
        s._parse_scan_output("lib/  dir  -", ".")
        assert s.dirs.count("lib") == 1

    def test_parse_non_numeric_third_part(self):
        s = SessionState()
        output = "readme.md  file  2025-01-01"
        s._parse_scan_output(output, ".")
        assert "readme.md" in s.files


# ==== _parse_size_to_bytes ====
class TestParseSizeToBytes:
    def test_bytes(self):
        s = SessionState()
        assert s._parse_size_to_bytes("500 B") == 500

    def test_kib(self):
        s = SessionState()
        assert s._parse_size_to_bytes("1 KiB") == 1024

    def test_mib(self):
        s = SessionState()
        assert s._parse_size_to_bytes("1 MiB") == 1024**2

    def test_gib(self):
        s = SessionState()
        assert s._parse_size_to_bytes("1 GiB") == 1024**3

    def test_kb(self):
        s = SessionState()
        assert s._parse_size_to_bytes("1 KB") == 1024

    def test_mb(self):
        s = SessionState()
        assert s._parse_size_to_bytes("1 MB") == 1024**2

    def test_gb(self):
        s = SessionState()
        assert s._parse_size_to_bytes("1 GB") == 1024**3

    def test_no_unit(self):
        s = SessionState()
        assert s._parse_size_to_bytes("500") == 500

    def test_empty(self):
        s = SessionState()
        assert s._parse_size_to_bytes("") is None

    def test_dash(self):
        s = SessionState()
        assert s._parse_size_to_bytes("-") is None

    def test_invalid(self):
        s = SessionState()
        assert s._parse_size_to_bytes("abc") is None

    def test_decimal(self):
        s = SessionState()
        assert s._parse_size_to_bytes("1.5 KiB") == int(1.5 * 1024)


# ==== _detect_file_type ====
class TestDetectFileType:
    def test_python(self):
        s = SessionState()
        assert s._detect_file_type("main.py") == "python"

    def test_pyw(self):
        s = SessionState()
        assert s._detect_file_type("app.pyw") == "python"

    def test_javascript(self):
        s = SessionState()
        assert s._detect_file_type("app.js") == "javascript"

    def test_typescript(self):
        s = SessionState()
        assert s._detect_file_type("app.ts") == "typescript"

    def test_tsx(self):
        s = SessionState()
        assert s._detect_file_type("app.tsx") == "typescript"

    def test_markdown(self):
        s = SessionState()
        assert s._detect_file_type("README.md") == "markdown"

    def test_json(self):
        s = SessionState()
        assert s._detect_file_type("data.json") == "json"

    def test_yaml(self):
        s = SessionState()
        assert s._detect_file_type("config.yaml") == "yaml"

    def test_yml(self):
        s = SessionState()
        assert s._detect_file_type("config.yml") == "yaml"

    def test_dockerfile(self):
        s = SessionState()
        assert s._detect_file_type("Dockerfile") == "dockerfile"

    def test_dockerfile_base(self):
        s = SessionState()
        assert s._detect_file_type("Dockerfile.base") == "dockerfile"

    def test_shell(self):
        s = SessionState()
        assert s._detect_file_type("start.sh") == "shell"

    def test_powershell(self):
        s = SessionState()
        assert s._detect_file_type("deploy.ps1") == "powershell"

    def test_sql(self):
        s = SessionState()
        assert s._detect_file_type("schema.sql") == "sql"

    def test_html(self):
        s = SessionState()
        assert s._detect_file_type("index.html") == "html"

    def test_htm(self):
        s = SessionState()
        assert s._detect_file_type("page.htm") == "html"

    def test_css(self):
        s = SessionState()
        assert s._detect_file_type("style.css") == "css"

    def test_scss(self):
        s = SessionState()
        assert s._detect_file_type("style.scss") == "css"

    def test_mermaid(self):
        s = SessionState()
        assert s._detect_file_type("flow.mmd") == "mermaid"

    def test_toml(self):
        s = SessionState()
        assert s._detect_file_type("pyproject.toml") == "toml"

    def test_unknown(self):
        s = SessionState()
        assert s._detect_file_type("data.xyz") is None

    def test_mjs(self):
        s = SessionState()
        assert s._detect_file_type("module.mjs") == "javascript"

    def test_cjs(self):
        s = SessionState()
        assert s._detect_file_type("module.cjs") == "javascript"

    def test_less(self):
        s = SessionState()
        assert s._detect_file_type("style.less") == "css"

    def test_bash(self):
        s = SessionState()
        assert s._detect_file_type("script.bash") == "shell"


# ==== _detect_project_types ====
class TestDetectProjectTypes:
    def test_python_project(self):
        s = SessionState()
        s.files = ["main.py", "requirements.txt"]
        s._detect_project_types()
        assert "python" in s.environment_facts.project_types
        assert "pip" in s.environment_facts.package_managers

    def test_docker_project(self):
        s = SessionState()
        s.files = ["Dockerfile", "docker-compose.yaml"]
        s._detect_project_types()
        assert "docker" in s.environment_facts.project_types

    def test_docker_compose_yml(self):
        s = SessionState()
        s.files = ["docker-compose.yml"]
        s._detect_project_types()
        assert "docker" in s.environment_facts.project_types

    def test_node_project(self):
        s = SessionState()
        s.files = ["package.json", "index.js"]
        s._detect_project_types()
        assert "node" in s.environment_facts.project_types
        assert "npm" in s.environment_facts.package_managers

    def test_fastapi_framework(self):
        s = SessionState()
        s.files = ["main.py", "fastapi_app.py"]
        s._detect_project_types()
        assert "fastapi" in s.environment_facts.frameworks_detected

    def test_pytest_framework(self):
        s = SessionState()
        s.files = ["test_main.py"]
        s._detect_project_types()
        assert "pytest" in s.environment_facts.frameworks_detected

    def test_pyproject_toml(self):
        s = SessionState()
        s.files = ["pyproject.toml"]
        s._detect_project_types()
        assert "pip" in s.environment_facts.package_managers

    def test_ts_files_node(self):
        s = SessionState()
        s.files = ["app.ts"]
        s._detect_project_types()
        assert "node" in s.environment_facts.project_types


# ==== _extract_shell_facts ====
class TestExtractShellFacts:
    def test_git_branch(self):
        s = SessionState()
        s._extract_shell_facts("git status", "On branch main")
        assert s.environment_facts.git_branch == "main"

    def test_git_branch_star(self):
        s = SessionState()
        s._extract_shell_facts("git branch", "* develop\n  main")
        assert s.environment_facts.git_branch == "develop"

    def test_python_version(self):
        s = SessionState()
        s._extract_shell_facts("python --version", "Python 3.11.5")
        assert s.environment_facts.python_version == "3.11.5"

    def test_python_version_v_flag(self):
        s = SessionState()
        s._extract_shell_facts("python -V", "Python 3.12.0")
        assert s.environment_facts.python_version == "3.12.0"

    def test_node_version(self):
        s = SessionState()
        s._extract_shell_facts("node --version", "v20.10.0")
        assert s.environment_facts.node_version == "20.10.0"

    def test_docker_running(self):
        s = SessionState()
        s._extract_shell_facts("docker ps", "CONTAINER ID  IMAGE")
        assert s.environment_facts.docker_running is True

    def test_docker_not_running(self):
        s = SessionState()
        s._extract_shell_facts("docker ps", "Cannot connect to docker daemon")
        assert s.environment_facts.docker_running is False

    def test_pwd(self):
        s = SessionState()
        s._extract_shell_facts("pwd", "/home/user/project")
        assert s.environment_facts.working_directory == "/home/user/project"

    def test_du_command(self):
        s = SessionState()
        s._extract_shell_facts("du -sh .", "45M\t.")
        assert any("45M" in obs for obs in s.environment_facts.observations)

    def test_pip_list(self):
        s = SessionState()
        s._extract_shell_facts("pip list", "Package\n-------\nnumpy 1.0\npandas 2.0")
        assert any(
            "packages" in obs.lower() for obs in s.environment_facts.observations
        )

    def test_ls_command(self):
        s = SessionState()
        s._extract_shell_facts(
            "ls -la", "total 48\ndrwxr-xr-x  5 user  staff\nfile.txt"
        )
        assert any("entries" in obs.lower() for obs in s.environment_facts.observations)

    def test_docker_info(self):
        s = SessionState()
        s._extract_shell_facts("docker info", "Server Version: 24.0.7")
        assert s.environment_facts.docker_running is True


# ==== _classify_error ====
class TestClassifyError:
    def test_empty_output(self):
        s = SessionState()
        assert s._classify_error("execute", "") == (None, None)

    def test_none_output(self):
        s = SessionState()
        assert s._classify_error("execute", None) == (None, None)

    def test_syntax_error_missing(self):
        s = SessionState()
        result = s._classify_error("execute", "Missing terminator in command")
        assert result[0] == "syntax_error"

    def test_syntax_error_invalid(self):
        s = SessionState()
        result = s._classify_error("execute", "invalid syntax at line 5")
        assert result[0] == "syntax_error"

    def test_syntax_error_token(self):
        s = SessionState()
        result = s._classify_error("execute", "Unexpected token 'else'")
        assert result[0] == "syntax_error"

    def test_timeout(self):
        s = SessionState()
        result = s._classify_error("execute", "Operation timed out")
        assert result[0] == "timeout"

    def test_no_response(self):
        s = SessionState()
        result = s._classify_error("execute", "No response from server")
        assert result[0] == "timeout"

    def test_unresponsive(self):
        s = SessionState()
        result = s._classify_error("execute", "Server is unresponsive")
        assert result[0] == "timeout"

    def test_permission_denied(self):
        s = SessionState()
        result = s._classify_error("execute", "Permission denied for /root")
        assert result[0] == "permission_denied"

    def test_access_denied(self):
        s = SessionState()
        result = s._classify_error("execute", "Access denied to file")
        assert result[0] == "permission_denied"

    def test_unauthorized(self):
        s = SessionState()
        result = s._classify_error("execute", "Unauthorized request")
        assert result[0] == "permission_denied"

    def test_forbidden(self):
        s = SessionState()
        result = s._classify_error("execute", "403 Forbidden")
        assert result[0] == "permission_denied"

    def test_not_found(self):
        s = SessionState()
        result = s._classify_error("execute", "Command not found")
        assert result[0] == "not_found"

    def test_no_such_file(self):
        s = SessionState()
        result = s._classify_error("execute", "No such file or directory")
        assert result[0] == "not_found"

    def test_does_not_exist(self):
        s = SessionState()
        result = s._classify_error("execute", "Path does not exist")
        assert result[0] == "not_found"

    def test_path_not_found(self):
        s = SessionState()
        result = s._classify_error("execute", "Path not found on disk")
        assert result[0] == "not_found"

    def test_connection_refused(self):
        s = SessionState()
        result = s._classify_error("execute", "Connection refused")
        assert result[0] == "connection_error"

    def test_unable_to_connect(self):
        s = SessionState()
        result = s._classify_error("execute", "Unable to connect to host")
        assert result[0] == "connection_error"

    def test_unreachable(self):
        s = SessionState()
        result = s._classify_error("execute", "Host is unreachable")
        assert result[0] == "connection_error"

    def test_offline(self):
        s = SessionState()
        result = s._classify_error("execute", "Server appears offline")
        assert result[0] == "connection_error"

    def test_out_of_memory(self):
        s = SessionState()
        result = s._classify_error("execute", "Out of memory error")
        assert result[0] == "resource_error"

    def test_disk_full(self):
        s = SessionState()
        result = s._classify_error("execute", "Disk full, no space left")
        assert result[0] == "resource_error"

    def test_no_space_left(self):
        s = SessionState()
        result = s._classify_error("execute", "No space left on device")
        assert result[0] == "resource_error"

    def test_memory_exhausted(self):
        s = SessionState()
        result = s._classify_error("execute", "Memory exhausted in process")
        assert result[0] == "resource_error"

    def test_generic_error(self):
        s = SessionState()
        result = s._classify_error("execute", "Something error occurred")
        assert result[0] == "execution_error"

    def test_generic_failed(self):
        s = SessionState()
        result = s._classify_error("execute", "Task failed to complete")
        assert result[0] == "execution_error"

    def test_no_error(self):
        s = SessionState()
        result = s._classify_error("execute", "Everything is fine, no issues")
        assert result[0] is None

    def test_missing_quote(self):
        s = SessionState()
        result = s._classify_error("execute", "Missing closing quote in string")
        assert result[0] == "syntax_error"


# ==== get_editable_files ====
class TestGetEditableFiles:
    def test_basic(self):
        s = SessionState()
        s.files = ["main.py", "readme.md", "data.bin", "logo.png"]
        result = s.get_editable_files()
        assert "main.py" in result
        assert "readme.md" in result
        assert "data.bin" not in result
        assert "logo.png" not in result

    def test_excludes_edited(self):
        s = SessionState()
        s.files = ["main.py", "other.py"]
        s.edited_files.add("main.py")
        result = s.get_editable_files()
        assert "main.py" not in result
        assert "other.py" in result

    def test_sorted(self):
        s = SessionState()
        s.files = ["z.py", "a.py", "m.py"]
        result = s.get_editable_files()
        assert result == ["a.py", "m.py", "z.py"]

    def test_binary_extensions(self):
        s = SessionState()
        s.files = ["model.safetensors", "app.exe", "lib.dll", "img.jpg"]
        assert s.get_editable_files() == []

    def test_all_editable_types(self):
        s = SessionState()
        s.files = [
            "a.md",
            "b.py",
            "c.js",
            "d.ts",
            "e.yaml",
            "f.yml",
            "g.json",
            "h.txt",
            "i.sh",
            "j.ps1",
            "k.mmd",
            "l.html",
            "m.css",
            "n.env",
            "o.toml",
            "p.ini",
            "q.cfg",
        ]
        result = s.get_editable_files()
        assert len(result) == 17


# ==== _extract_important_values ====
class TestExtractImportantValues:
    def test_ip_addresses(self):
        s = SessionState()
        s._extract_important_values("execute", {}, "IP: 192.168.1.1")
        assert any("192.168.1.1" in v for v in s.ledger.extracted_values.values())

    def test_skip_localhost_ips(self):
        s = SessionState()
        s._extract_important_values("execute", {}, "127.0.0.1 and 0.0.0.0")
        assert "127.0.0.1" not in str(s.ledger.extracted_values)

    def test_urls(self):
        s = SessionState()
        s._extract_important_values("execute", {}, "Visit https://example.com/api")
        assert any("example.com" in v for v in s.ledger.extracted_values.values())

    def test_ports(self):
        s = SessionState()
        s._extract_important_values("execute", {}, "listening on port 8080")
        assert any("8080" in v for v in s.ledger.extracted_values.values())

    def test_docker_containers(self):
        s = SessionState()
        s._extract_important_values(
            "execute", {"command": "docker ps"}, "abc123def456 nginx"
        )
        assert any("abc123def456" in v for v in s.ledger.extracted_values.values())

    def test_git_commits(self):
        s = SessionState()
        s._extract_important_values(
            "execute", {"command": "git log"}, "abcdef1234567 Initial"
        )
        assert any("abcdef1" in v for v in s.ledger.extracted_values.values())

    def test_modified_file(self):
        s = SessionState()
        s._extract_important_values("write_file", {"path": "/a.py"}, "ok")
        assert any("/a.py" in v for v in s.ledger.extracted_values.values())

    def test_error_extraction(self):
        s = SessionState()
        s._extract_important_values(
            "execute", {}, "Error: something went wrong\nnext line"
        )
        assert any("Error" in v for v in s.ledger.extracted_values.values())


# ==== format_for_prompt ====
class TestFormatForPrompt:
    def test_empty_state(self):
        s = SessionState()
        result = s.format_for_prompt()
        assert "NOT YET SCANNED" in result

    def test_with_files(self):
        s = SessionState()
        s.files = ["src/main.py", "README.md"]
        s.dirs = ["src"]
        result = s.format_for_prompt()
        assert "ALREADY SCANNED" in result
        assert "src/" in result or "📁 src" in result

    def test_with_agents(self):
        s = SessionState()
        s.agents_verified = True
        s.discovered_agents = ["ws1", "ws2"]
        s.queried_agents = ["ws1"]
        result = s.format_for_prompt()
        assert "ws1" in result
        assert "ws2" in result
        assert "REMAINING" in result

    def test_agents_none_found(self):
        s = SessionState()
        s.agents_verified = True
        result = s.format_for_prompt()
        assert "None found" in result

    def test_all_agents_queried(self):
        s = SessionState()
        s.agents_verified = True
        s.discovered_agents = ["ws1"]
        s.queried_agents = ["ws1"]
        result = s.format_for_prompt()
        assert "All agents queried" in result

    def test_loop_detection(self):
        s = SessionState()
        for _ in range(3):
            s.completed_steps.append(
                CompletedStep(
                    step_id="s",
                    tool="scan_workspace",
                    params={},
                    output_summary="scan",
                    success=True,
                )
            )
        result = s.format_for_prompt()
        assert "LOOP DETECTED" in result

    def test_failure_analysis(self):
        s = SessionState()
        s.completed_steps.append(
            CompletedStep(
                step_id="s1",
                tool="execute",
                params={},
                output_summary="fail",
                success=False,
                error_type="syntax_error",
                error_message="Bad syntax",
            )
        )
        result = s.format_for_prompt()
        assert "FAILURES" in result
        assert "syntax" in result.lower()

    def test_many_read_files_truncated(self):
        """Line 1387: >30 read files shows truncation."""
        s = SessionState()
        for i in range(35):
            s.read_files.add(f"/file{i:03d}.py")
        result = s.format_for_prompt()
        assert "... and 5 more" in result

    def test_many_edited_files_truncated(self):
        """Line 1396: >30 edited files shows truncation."""
        s = SessionState()
        for i in range(35):
            s.edited_files.add(f"/file{i:03d}.py")
        result = s.format_for_prompt()
        assert "... and 5 more" in result

    def test_read_files_shown(self):
        s = SessionState()
        s.read_files.add("/a.py")
        result = s.format_for_prompt()
        assert "/a.py" in result

    def test_edited_files_shown(self):
        s = SessionState()
        s.edited_files.add("/a.py")
        result = s.format_for_prompt()
        assert "/a.py" in result

    def test_user_info_shown(self):
        s = SessionState()
        s.user_info["name"] = "AJ"
        result = s.format_for_prompt()
        assert "AJ" in result

    def test_environment_facts(self):
        s = SessionState()
        s.environment_facts.project_types.add("python")
        s.environment_facts.git_branch = "main"
        s.environment_facts.python_version = "3.11"
        s.environment_facts.docker_running = True
        s.environment_facts.total_file_count = 50
        s.environment_facts.total_dir_count = 10
        s.environment_facts.frameworks_detected.add("pytest")
        s.environment_facts.package_managers.add("pip")
        s.environment_facts.node_version = "20.0"
        result = s.format_for_prompt()
        assert "python" in result
        assert "main" in result
        assert "3.11" in result

    def test_observations(self):
        s = SessionState()
        s.environment_facts.add_observation("Found 10 packages")
        result = s.format_for_prompt()
        assert "10 packages" in result

    def test_file_metadata(self):
        s = SessionState()
        s.file_metadata["/big.bin"] = FileMetadata(
            path="/big.bin", size_bytes=1024000, size_human="1000 KiB"
        )
        result = s.format_for_prompt()
        assert "LARGEST FILES" in result

    def test_task_plan(self):
        s = SessionState()
        plan = TaskPlan()
        plan.add_item("Step 1")
        s.set_task_plan(plan)
        result = s.format_for_prompt()
        assert "TASK PLAN" in result

    def test_many_completed_steps(self):
        s = SessionState()
        for i in range(15):
            s.completed_steps.append(
                CompletedStep(
                    step_id=f"s{i}",
                    tool="execute",
                    params={},
                    output_summary=f"cmd{i}",
                    success=True,
                )
            )
        result = s.format_for_prompt()
        assert "earlier steps" in result

    def test_duplicate_execute_detection(self):
        s = SessionState()
        for _ in range(2):
            s.completed_steps.append(
                CompletedStep(
                    step_id="s",
                    tool="execute",
                    params={"agent_id": "ws1"},
                    output_summary="exec",
                    success=True,
                )
            )
        result = s.format_for_prompt()
        assert "LOOP DETECTED" in result

    def test_agents_not_discovered(self):
        s = SessionState()
        result = s.format_for_prompt()
        assert "NOT DISCOVERED" in result

    def test_docker_not_running(self):
        s = SessionState()
        s.environment_facts.docker_running = False
        result = s.format_for_prompt()
        assert "not running" in result

    def test_timeout_failure_suggestion(self):
        s = SessionState()
        s.completed_steps.append(
            CompletedStep(
                step_id="s",
                tool="execute",
                params={},
                output_summary="fail",
                success=False,
                error_type="timeout",
                error_message="timed out",
            )
        )
        result = s.format_for_prompt()
        assert "Reduce scope" in result

    def test_permission_failure_suggestion(self):
        s = SessionState()
        s.completed_steps.append(
            CompletedStep(
                step_id="s",
                tool="execute",
                params={},
                output_summary="fail",
                success=False,
                error_type="permission_denied",
                error_message="denied",
            )
        )
        result = s.format_for_prompt()
        assert "elevated permissions" in result

    def test_not_found_failure_suggestion(self):
        s = SessionState()
        s.completed_steps.append(
            CompletedStep(
                step_id="s",
                tool="execute",
                params={},
                output_summary="fail",
                success=False,
                error_type="not_found",
                error_message="not found",
            )
        )
        result = s.format_for_prompt()
        assert "Verify path" in result

    def test_agents_queried_none(self):
        s = SessionState()
        s.agents_verified = True
        s.discovered_agents = ["ws1"]
        result = s.format_for_prompt()
        assert "No agents queried" in result


# ==== _format_bytes ====
class TestFormatBytes:
    def test_bytes(self):
        s = SessionState()
        assert "B" in s._format_bytes(500)

    def test_kib(self):
        s = SessionState()
        assert "KiB" in s._format_bytes(2048)

    def test_mib(self):
        s = SessionState()
        assert "MiB" in s._format_bytes(2 * 1024**2)

    def test_gib(self):
        s = SessionState()
        assert "GiB" in s._format_bytes(2 * 1024**3)

    def test_tib(self):
        s = SessionState()
        assert "TiB" in s._format_bytes(2 * 1024**4)


# ==== _summarize_params ====
class TestSummarizeParams:
    def test_scan_workspace(self):
        s = SessionState()
        assert s._summarize_params("scan_workspace", {"path": "."}) == "."

    def test_read_file(self):
        s = SessionState()
        assert s._summarize_params("read_file", {"path": "/a.py"}) == "/a.py"

    def test_write_file(self):
        s = SessionState()
        assert s._summarize_params("write_file", {"path": "/b.py"}) == "/b.py"

    def test_execute_shell(self):
        s = SessionState()
        result = s._summarize_params("execute_shell", {"command": "ls -la"})
        assert "ls -la" in result

    def test_execute_shell_long(self):
        s = SessionState()
        result = s._summarize_params("execute_shell", {"command": "x" * 100})
        assert "..." in result

    def test_execute_code(self):
        s = SessionState()
        result = s._summarize_params("execute_code", {"language": "python"})
        assert "python" in result

    def test_unknown_tool(self):
        s = SessionState()
        result = s._summarize_params("mystery", {"a": 1, "b": 2})
        assert "a" in result


# ==== Session management functions ====
class TestSessionManagement:
    def setup_method(self):
        _session_states.clear()
        import services.session_state as mod

        mod._current_state = None
        mod._current_session_id = None

    def test_get_session_state_global(self):
        s = get_session_state()
        assert isinstance(s, SessionState)
        s2 = get_session_state()
        assert s is s2

    def test_get_session_state_with_id(self):
        s = get_session_state("sess1")
        assert isinstance(s, SessionState)
        s2 = get_session_state("sess1")
        assert s is s2

    def test_reset_session_state_global(self):
        s = get_session_state()
        s.files.append("a.py")
        s2 = reset_session_state()
        assert len(s2.files) == 0

    def test_reset_session_state_with_id(self):
        s = get_session_state("sess1")
        s.files.append("a.py")
        s2 = reset_session_state("sess1")
        assert len(s2.files) == 0

    def test_get_existing_session(self):
        get_session_state("sess1")
        assert get_existing_session("sess1") is not None
        assert get_existing_session("sess999") is None

    def test_cleanup_session(self):
        get_session_state("sess1")
        assert cleanup_session("sess1") is True
        assert cleanup_session("sess1") is False

    def test_get_active_sessions(self):
        get_session_state("a")
        get_session_state("b")
        sessions = get_active_sessions()
        assert "a" in sessions
        assert "b" in sessions


class TestOutputInStepSummary:
    """Tests for Fix 1: actual output included in step summaries."""

    def test_execute_with_output_includes_preview(self):
        """When remote execute returns output, it should appear in the summary."""
        s = SessionState()
        s.update_from_step(
            "execute",
            {"command": "Test-Connection google.com", "agent_id": "ians-r16"},
            "Reply from 142.250.80.46: bytes=32 time=15ms TTL=57",
            True,
        )
        step = s.completed_steps[-1]
        assert "OUTPUT:" in step.output_summary
        assert "142.250.80.46" in step.output_summary
        assert "15ms" in step.output_summary

    def test_execute_with_empty_output_says_empty(self):
        """When remote execute returns empty output, summary should say so."""
        s = SessionState()
        s.update_from_step(
            "execute",
            {"command": "Test-Connection google.com", "agent_id": "ians-r16"},
            "",
            True,
        )
        step = s.completed_steps[-1]
        assert "empty" in step.output_summary.lower()
        assert "no output" in step.output_summary.lower()

    def test_execute_failed_no_output_line(self):
        """When execute fails, we don't add the OUTPUT line for empty."""
        s = SessionState()
        s.update_from_step(
            "execute",
            {"command": "bad-command", "agent_id": "ians-r16"},
            "",
            False,
        )
        step = s.completed_steps[-1]
        assert "FAILED" in step.output_summary
        # Failed commands don't need '(empty - command returned no output)'
        # since the failure itself explains the lack of output

    def test_execute_output_truncated_to_500(self):
        """Long output should be truncated in summary."""
        s = SessionState()
        long_output = "x" * 1000
        s.update_from_step(
            "execute",
            {"command": "Get-Process", "agent_id": "ians-r16"},
            long_output,
            True,
        )
        step = s.completed_steps[-1]
        assert "OUTPUT:" in step.output_summary
        # Should be truncated - output_summary should contain at most ~500 chars of output
        output_part = step.output_summary.split("OUTPUT: ")[1]
        assert len(output_part) <= 510  # Allow small padding

    def test_execute_whitespace_only_counts_as_empty(self):
        """Whitespace-only output should be treated as empty."""
        s = SessionState()
        s.update_from_step(
            "execute",
            {"command": "echo", "agent_id": "ians-r16"},
            "   \n\t  ",
            True,
        )
        step = s.completed_steps[-1]
        assert "empty" in step.output_summary.lower()

    def test_output_visible_in_format_for_prompt(self):
        """The output should be visible when format_for_prompt is called."""
        s = SessionState()
        s.update_from_step(
            "execute",
            {"command": "hostname", "agent_id": "srv1"},
            "MY-SERVER-01",
            True,
        )
        prompt = s.format_for_prompt()
        assert "MY-SERVER-01" in prompt
