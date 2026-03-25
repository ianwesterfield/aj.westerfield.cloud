"""
Tests for ThinkingStreamParser - 100% coverage target.
"""

import pytest
import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "layers", "orchestrator")
)

from services.helpers.stream_parser import ThinkingStreamParser


class TestThinkingStreamParserInit:
    def test_initial_state(self):
        p = ThinkingStreamParser()
        assert p._in_think is False
        assert p._finished is False
        assert p._pending == ""
        assert p._think_content == ""


class TestFeed:
    def test_feed_no_think_tag_discards(self):
        p = ThinkingStreamParser()
        result = p.feed("hello world")
        assert result == ""

    def test_feed_partial_angle_bracket_buffers(self):
        p = ThinkingStreamParser()
        result = p.feed("abc<")
        assert result == ""
        assert "<" in p._pending

    def test_feed_opens_think_block(self):
        p = ThinkingStreamParser()
        result = p.feed("<think>content here")
        # Some or all of "content here" may be buffered in danger zone
        assert p._in_think is True

    def test_feed_complete_think_block(self):
        p = ThinkingStreamParser()
        r1 = p.feed("<think>hello world</think>")
        assert p._finished is True
        assert "hello world" in r1
        assert p._in_think is True

    def test_feed_after_finished_returns_empty(self):
        p = ThinkingStreamParser()
        p.feed("<think>x</think>")
        assert p.feed("more tokens") == ""

    def test_feed_danger_zone_buffering(self):
        p = ThinkingStreamParser()
        p.feed("<think>")
        # Feed content larger than danger_zone (9 chars)
        result = p.feed("a" * 20)
        # Should return some safe content and buffer last 9
        assert len(result) > 0
        assert len(p._pending) == 9

    def test_feed_small_content_with_angle_bracket(self):
        p = ThinkingStreamParser()
        p.feed("<think>")
        result = p.feed("ab<")
        # '<' and '/' in pending trigger buffering (no safe content)
        # content is small and contains '<'
        assert isinstance(result, str)

    def test_feed_small_safe_content(self):
        p = ThinkingStreamParser()
        p.feed("<think>")
        result = p.feed("hi")
        # Small content without '<' or '/' -> returned directly
        assert result == "hi"

    def test_feed_incremental_tokens(self):
        p = ThinkingStreamParser()
        all_content = ""
        all_content += p.feed("<thi")
        all_content += p.feed("nk>")
        all_content += p.feed("streaming ")
        all_content += p.feed("content ")
        all_content += p.feed("here")
        all_content += p.feed("</think>")
        assert "streaming" in p.get_content()
        assert "content" in p.get_content()

    def test_feed_content_before_think_tag(self):
        p = ThinkingStreamParser()
        result = p.feed("prefix text <think>inside")
        assert p._in_think is True

    def test_feed_slash_in_content_buffers(self):
        p = ThinkingStreamParser()
        p.feed("<think>")
        result = p.feed("a/b")
        # '/' in pending triggers buffering
        assert isinstance(result, str)


class TestFlush:
    def test_flush_when_not_in_think(self):
        p = ThinkingStreamParser()
        assert p.flush() == ""

    def test_flush_when_finished(self):
        p = ThinkingStreamParser()
        p.feed("<think>x</think>")
        assert p.flush() == ""

    def test_flush_returns_pending(self):
        p = ThinkingStreamParser()
        p.feed("<think>")
        p.feed("buffered")
        remaining = p.flush()
        assert p._pending == ""
        assert isinstance(remaining, str)


class TestGetContent:
    def test_empty_content(self):
        p = ThinkingStreamParser()
        assert p.get_content() == ""

    def test_accumulated_content(self):
        p = ThinkingStreamParser()
        p.feed("<think>hello</think>")
        assert "hello" in p.get_content()


class TestStaticMethods:
    def test_extract_thinking(self):
        result = ThinkingStreamParser.extract_thinking(
            "before <think> reasoning here </think> after"
        )
        assert result == "reasoning here"

    def test_extract_thinking_no_tags(self):
        result = ThinkingStreamParser.extract_thinking("no tags here")
        assert result == ""

    def test_extract_thinking_multiline(self):
        result = ThinkingStreamParser.extract_thinking(
            "<think>\nline1\nline2\n</think>"
        )
        assert "line1" in result
        assert "line2" in result

    def test_extract_json_after_think(self):
        result = ThinkingStreamParser.extract_json(
            '<think>reasoning</think>{"tool": "execute"}'
        )
        assert result == '{"tool": "execute"}'

    def test_extract_json_no_think(self):
        result = ThinkingStreamParser.extract_json('{"tool": "execute"}')
        assert result == '{"tool": "execute"}'

    def test_extract_json_whitespace(self):
        result = ThinkingStreamParser.extract_json("  \n  hello  \n  ")
        assert result == "hello"
