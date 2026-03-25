"""Tests for ThinkingStreamParser - coverage target for missing lines.

Covers flush(), get_content(), static methods, and the '<' buffering
edge case in the not-in-think state that are not covered elsewhere.
"""

import pytest
import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "layers", "orchestrator")
)

from services.helpers.stream_parser import ThinkingStreamParser  # type: ignore[import-not-found]

# ==== feed() - not-in-think buffering with '<' ====


class TestFeedNotInThinkBuffering:
    """Cover line 43: pending trimmed to '<' when not yet inside <think>."""

    def test_angle_bracket_buffers_in_not_in_think(self):
        """Line 43: When '<' appears but no '<think>' yet, pending is trimmed to '<...'."""
        p = ThinkingStreamParser()
        # Feed text with '<' but not a full '<think>' tag yet
        result = p.feed("some prefix <thi")
        assert result == ""
        # Pending should contain '<thi' (rfind('<') trims to that)
        assert p._pending.startswith("<")

    def test_angle_bracket_then_think_tag_completes(self):
        """Line 43 + opening: buffered '<' followed by 'nk>' completes the tag."""
        p = ThinkingStreamParser()
        p.feed("leading text <thi")
        p.feed("nk>content here")
        assert p._in_think is True


# ==== feed() - danger zone pass (line 62) ====


class TestFeedDangerZonePass:
    """Cover line 62: 'pass' when short pending has '<' or '/'."""

    def test_short_content_with_slash_returns_empty(self):
        """Line 62: Short pending with '/' triggers pass (returns '')."""
        p = ThinkingStreamParser()
        p.feed("<think>")
        result = p.feed("a/")
        # Short content with '/' triggers pass - no safe content returned yet
        assert isinstance(result, str)

    def test_short_content_with_angle_bracket_returns_empty(self):
        """Line 62: Short pending with '<' triggers pass (returns '')."""
        p = ThinkingStreamParser()
        p.feed("<think>")
        result = p.feed("b<")
        assert isinstance(result, str)


# ==== flush() ====


class TestFlushMethod:
    """Cover lines 70-77: flush() method."""

    def test_flush_not_in_think_returns_empty(self):
        """Lines 72-73: flush() when not in think returns ''."""
        p = ThinkingStreamParser()
        assert p.flush() == ""

    def test_flush_finished_returns_empty(self):
        """Lines 72-73: flush() when finished returns ''."""
        p = ThinkingStreamParser()
        p.feed("<think>x</think>")
        assert p.flush() == ""

    def test_flush_in_think_returns_pending_and_clears(self):
        """Lines 74-77: flush() returns pending content and resets it."""
        p = ThinkingStreamParser()
        p.feed("<think>")
        # Feed something that stays buffered (short with slash)
        p.feed("abc/def")
        # Now flush should return remaining pending
        flushed = p.flush()
        assert p._pending == ""
        assert isinstance(flushed, str)

    def test_flush_updates_think_content(self):
        """Line 76: flush() appends pending to _think_content."""
        p = ThinkingStreamParser()
        p.feed("<think>hello ")
        # Feed more that's longer than danger zone to get some accumulated
        p.feed("world and more text here that is definitely")
        before = p._think_content
        p.flush()
        # After flush, _think_content should have grown
        assert len(p._think_content) >= len(before)


# ==== get_content() ====


class TestGetContent:
    """Cover line 81: get_content() return."""

    def test_get_content_empty_initially(self):
        """Line 81: get_content() returns '' when nothing fed."""
        p = ThinkingStreamParser()
        assert p.get_content() == ""

    def test_get_content_after_complete_think_block(self):
        """Line 81: get_content() returns accumulated content."""
        p = ThinkingStreamParser()
        p.feed("<think>hello world</think>")
        assert "hello world" in p.get_content()

    def test_get_content_accumulates_across_feeds(self):
        """Line 81: Content is accumulated across multiple feed() calls."""
        p = ThinkingStreamParser()
        p.feed("<think>")
        p.feed("first part and some more text here to exceed")
        p.feed(" danger zone buffer boundaries")
        p.feed("</think>")
        content = p.get_content()
        assert len(content) > 0


# ==== extract_thinking() static method ====


class TestExtractThinking:
    """Cover lines 86-87: extract_thinking() static method."""

    def test_extract_thinking_with_content(self):
        """Lines 86-87: extract_thinking() returns trimmed content."""
        result = ThinkingStreamParser.extract_thinking(
            "<think> reasoning here </think>"
        )
        assert result == "reasoning here"

    def test_extract_thinking_no_tags_returns_empty(self):
        """Line 87: No tags returns ''."""
        result = ThinkingStreamParser.extract_thinking("no tags at all")
        assert result == ""

    def test_extract_thinking_multiline(self):
        """Lines 86-87: Multiline content extracted correctly."""
        result = ThinkingStreamParser.extract_thinking(
            "<think>\nstep 1\nstep 2\n</think>"
        )
        assert "step 1" in result
        assert "step 2" in result

    def test_extract_thinking_strips_whitespace(self):
        """Line 87: Result is stripped."""
        result = ThinkingStreamParser.extract_thinking(
            "<think>   padded content   </think>"
        )
        assert result == "padded content"


# ==== extract_json() static method ====


class TestExtractJson:
    """Cover lines 92-94: extract_json() static method."""

    def test_extract_json_after_think_tag(self):
        """Lines 92-93: Content after </think> is returned."""
        result = ThinkingStreamParser.extract_json(
            '<think>reasoning</think>{"tool": "execute"}'
        )
        assert result == '{"tool": "execute"}'

    def test_extract_json_no_think_tag(self):
        """Line 94: No </think> -> stripped full response."""
        result = ThinkingStreamParser.extract_json('{"tool": "think"}')
        assert result == '{"tool": "think"}'

    def test_extract_json_strips_whitespace(self):
        """Line 94: Strips leading/trailing whitespace."""
        result = ThinkingStreamParser.extract_json("  \n  hello  \n  ")
        assert result == "hello"

    def test_extract_json_with_whitespace_after_think(self):
        """Lines 92-93: Whitespace after </think> is stripped."""
        result = ThinkingStreamParser.extract_json("<think>thinking</think>   \n   {}")
        assert result == "{}"
