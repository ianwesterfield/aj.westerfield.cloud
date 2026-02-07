"""
ThinkingStreamParser - Streaming parser for <think>...</think> tagged content.

Handles partial tag boundaries by buffering near tag characters.
Yields only the text content inside <think> tags safely.
"""

import re


class ThinkingStreamParser:
    """
    Streaming parser for <think>...</think> tagged content.

    Handles partial tag boundaries by buffering near tag characters.
    Yields only the text content inside <think> tags safely.
    """

    def __init__(self):
        self._in_think = False
        self._finished = False
        self._pending = ""
        self._think_content = ""

    def feed(self, token: str) -> str:
        """
        Feed a token and return any content safe to yield.

        Buffers characters near '<' and '>' to handle partial tags.
        Returns content only when we're confident it's complete text.
        """
        if self._finished:
            return ""

        self._pending += token

        if not self._in_think:
            if "<think>" in self._pending:
                self._in_think = True
                self._pending = self._pending.split("<think>", 1)[1]
            else:
                if "<" in self._pending:
                    self._pending = self._pending[self._pending.rfind("<") :]
                else:
                    self._pending = ""
                return ""

        if "</think>" in self._pending:
            self._finished = True
            content = self._pending.split("</think>", 1)[0]
            self._think_content += content
            return content

        safe_content = ""
        danger_zone = 9

        if len(self._pending) > danger_zone:
            safe_content = self._pending[:-danger_zone]
            self._pending = self._pending[-danger_zone:]
            self._think_content += safe_content
        elif "<" in self._pending or "/" in self._pending:
            pass
        else:
            safe_content = self._pending
            self._think_content += safe_content
            self._pending = ""

        return safe_content

    def flush(self) -> str:
        """Flush any remaining buffered content (call at end of stream)."""
        if self._finished or not self._in_think:
            return ""
        content = self._pending
        self._pending = ""
        self._think_content += content
        return content

    def get_content(self) -> str:
        """Get all accumulated thinking content."""
        return self._think_content

    @staticmethod
    def extract_thinking(full_response: str) -> str:
        """Extract content between <think> and </think> from complete response."""
        match = re.search(r"<think>(.*?)</think>", full_response, re.DOTALL)
        return match.group(1).strip() if match else ""

    @staticmethod
    def extract_json(full_response: str) -> str:
        """Extract JSON portion from full response (after </think>)."""
        if "</think>" in full_response:
            return full_response.split("</think>", 1)[1].strip()
        return full_response.strip()
