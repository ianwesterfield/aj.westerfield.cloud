"""
Tests for hallucination prevention in the orchestrator's complete answer validation.

Tests the _validate_complete_answer function which cross-validates
the reasoning model's answer against actual command output.
"""

import sys
import os
from unittest.mock import MagicMock
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

# Add project paths
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "layers", "orchestrator")
)

from api.orchestrator import _validate_complete_answer


@dataclass
class FakeCommandFlowEntry:
    """Minimal entry for testing."""

    output_preview: str = ""


@dataclass
class FakeCommandFlow:
    """Minimal command flow for testing."""

    entries: list = field(default_factory=list)


@dataclass
class FakeSessionState:
    """Minimal session state for testing."""

    command_flow: FakeCommandFlow = field(default_factory=FakeCommandFlow)


class TestValidateCompleteAnswer:
    """Tests for _validate_complete_answer hallucination detection."""

    def test_short_answer_always_passes(self):
        """Very short answers are not checked."""
        state = FakeSessionState()
        result = _validate_complete_answer("OK", state, [])
        assert result is None

    def test_empty_answer_passes(self):
        """Empty answer passes."""
        result = _validate_complete_answer("", FakeSessionState(), [])
        assert result is None

    def test_none_answer_passes(self):
        """None answer passes."""
        result = _validate_complete_answer(None, FakeSessionState(), [])
        assert result is None

    def test_answer_with_real_output_passes(self):
        """Answer that matches actual output should pass."""
        state = FakeSessionState()
        state.command_flow.entries.append(
            FakeCommandFlowEntry(
                output_preview="Reply from 142.250.80.46: bytes=32 time=15ms TTL=57"
            )
        )
        answer = (
            "The ping to google.com showed a response time of 15ms from 142.250.80.46."
        )
        result = _validate_complete_answer(answer, state, [])
        assert result is None

    def test_fabricated_ip_no_output(self):
        """Answer with IP address when no actual output exists -> hallucination."""
        state = FakeSessionState()
        # No entries with output
        answer = "The ping to google.com from ians-r16 showed: Reply from 216.58.194.174, time=29.7 ms"
        result = _validate_complete_answer(answer, state, [])
        assert result is not None
        assert "no output" in result.lower()

    def test_fabricated_response_time_no_output(self):
        """Answer with response times when no output -> hallucination."""
        state = FakeSessionState()
        answer = (
            "The network latency to google.com is approximately 29.7 ms with TTL 57."
        )
        result = _validate_complete_answer(answer, state, [])
        assert result is not None

    def test_fabricated_pid_no_output(self):
        """Answer with process IDs when no output -> hallucination."""
        state = FakeSessionState()
        answer = "The process is running with PID 23416 and consuming 150MB of memory."
        result = _validate_complete_answer(answer, state, [])
        assert result is not None

    def test_fabricated_ping_output_no_output(self):
        """Answer with Linux ping format when no output -> hallucination."""
        state = FakeSessionState()
        answer = "64 bytes from lb-in-f174.1e100.net (216.58.194.174): icmp_seq=1 ttl=57 time=29.7 ms"
        result = _validate_complete_answer(answer, state, [])
        assert result is not None

    def test_fabricated_windows_ping_no_output(self):
        """Answer with Windows ping format when no output -> hallucination."""
        state = FakeSessionState()
        answer = "Reply from 142.250.80.46: bytes=32 time<1ms TTL=128"
        result = _validate_complete_answer(answer, state, [])
        assert result is not None

    def test_fabricated_get_process_columns_no_output(self):
        """Answer with Get-Process table headers when no output -> hallucination."""
        state = FakeSessionState()
        answer = "Handles  NPM(K) PM(K) WS(K) CPU(s) Id ProcessName\n---\n451 23 45 67 0.5 23416 ping"
        result = _validate_complete_answer(answer, state, [])
        assert result is not None

    def test_generic_text_no_output_passes(self):
        """Answer without specific data patterns passes even with no output."""
        state = FakeSessionState()
        answer = "I ran the command on the agent but it returned no output. The command may have failed."
        result = _validate_complete_answer(answer, state, [])
        assert result is None

    def test_empty_output_entries_treated_as_no_output(self):
        """Entries with empty output_preview should count as no output."""
        state = FakeSessionState()
        state.command_flow.entries.append(FakeCommandFlowEntry(output_preview=""))
        state.command_flow.entries.append(FakeCommandFlowEntry(output_preview="   "))
        answer = "The ping showed a response time of 29.7 ms from 142.250.80.46."
        result = _validate_complete_answer(answer, state, [])
        assert result is not None

    def test_answer_matches_actual_output_with_ip(self):
        """When actual output has IP, answer referencing it should pass."""
        state = FakeSessionState()
        state.command_flow.entries.append(
            FakeCommandFlowEntry(output_preview="Reply from 10.0.0.1: time=5ms")
        )
        answer = "The ping showed a response time of 5ms from 10.0.0.1."
        # Output exists and has data, so this passes (regardless of match)
        result = _validate_complete_answer(answer, state, [])
        assert result is None

    def test_all_results_context_counts(self):
        """Data in all_results should also count as actual output."""
        state = FakeSessionState()
        all_results = [
            "```powershell\nReply from 192.168.1.1: bytes=32 time=2ms TTL=128\n```"
        ]
        # Even though command_flow has no entries, all_results has data
        # But the has_any_output check is on command_flow entries only
        # So if entries have no output but all_results do, should still flag
        answer = "Ping to 192.168.1.1 returned 2ms"
        result = _validate_complete_answer(answer, state, all_results)
        # No entries with output, so it should flag the fabricated data
        assert result is not None
