"""
Tests for intent classification.

CRITICAL: Intent classification must ALWAYS use LLM, never pattern matching.
Pattern matching is brittle and causes misclassifications.
"""

import pytest
import re
import inspect
from unittest.mock import AsyncMock, patch, MagicMock

# Test that the classify_intent method doesn't contain pattern matching


class TestNoPatternMatching:
    """Ensure classify_intent uses LLM only, no regex patterns."""

    def test_no_regex_patterns_in_classify_intent(self):
        """classify_intent must not use regex pattern matching."""
        from services.reasoning_engine import ReasoningEngine
        
        # Get the source code of classify_intent
        source = inspect.getsource(ReasoningEngine.classify_intent)
        
        # Check for forbidden patterns
        forbidden_patterns = [
            'task_patterns',
            'conversational_patterns', 
            're.search',
            're.match',
            're.findall',
            'for pattern in',
        ]
        
        for pattern in forbidden_patterns:
            assert pattern not in source, \
                f"classify_intent contains forbidden pattern matching code: '{pattern}'"

    def test_no_hardcoded_regex_in_classify_intent(self):
        """No hardcoded regex strings in classify_intent."""
        from services.reasoning_engine import ReasoningEngine
        
        source = inspect.getsource(ReasoningEngine.classify_intent)
        
        # Look for regex-like patterns (r'...' strings with regex chars)
        regex_indicators = [
            r"r'[^']*\\b",      # r'...\b patterns
            r"r'[^']*\\s",      # r'...\s patterns  
            r"r'\^",            # r'^... patterns
            r"r'[^']*\|",       # r'...|... alternation
        ]
        
        for indicator in regex_indicators:
            matches = re.findall(indicator, source)
            assert len(matches) == 0, \
                f"classify_intent contains regex pattern: {matches}"

    def test_classify_intent_calls_llm(self):
        """classify_intent must make an LLM API call."""
        from services.reasoning_engine import ReasoningEngine
        
        source = inspect.getsource(ReasoningEngine.classify_intent)
        
        # Must contain LLM call indicators
        assert 'api/chat' in source or 'client.post' in source, \
            "classify_intent must call the LLM API"
        
        # Must have the classification prompt
        assert 'task' in source.lower() and 'conversational' in source.lower(), \
            "classify_intent must distinguish between task and conversational"


class TestIntentClassificationBehavior:
    """Test actual classification behavior."""

    @pytest.fixture
    def engine(self):
        """Create a ReasoningEngine with mocked HTTP client."""
        with patch('services.reasoning_engine.httpx.AsyncClient'):
            from services.reasoning_engine import ReasoningEngine
            engine = ReasoningEngine()
            yield engine

    @pytest.mark.asyncio
    async def test_task_queries_classified_as_task(self, engine):
        """Queries requiring action should be classified as task."""
        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "task"}}
        mock_response.raise_for_status = MagicMock()
        
        engine.client.post = AsyncMock(return_value=mock_response)
        
        task_queries = [
            "What are the largest files on my machine?",
            "List files in C:\\Code",
            "Find all Python files",
            "How much disk space is left?",
            "Show me what's on the S: drive",
            "Scan for large folders",
            "What are the 10 largest files on ians-r16?",
        ]
        
        for query in task_queries:
            result = await engine.classify_intent(query)
            # The mock returns "task", so all should be task
            assert result["intent"] == "task", f"'{query}' should be classified as task"
            # Verify LLM was called (not pattern matched)
            assert engine.client.post.called, f"LLM should be called for '{query}'"

    @pytest.mark.asyncio
    async def test_conversational_queries_classified_as_conversational(self, engine):
        """Conceptual questions should be classified as conversational."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "conversational"}}
        mock_response.raise_for_status = MagicMock()
        
        engine.client.post = AsyncMock(return_value=mock_response)
        
        conversational_queries = [
            "What is a file system?",
            "How does FunnelCloud work?",
            "Explain what an agent does",
            "What can you do?",
            "Tell me about yourself",
        ]
        
        for query in conversational_queries:
            result = await engine.classify_intent(query)
            assert result["intent"] == "conversational", \
                f"'{query}' should be classified as conversational"
            assert engine.client.post.called, f"LLM should be called for '{query}'"

    @pytest.mark.asyncio
    async def test_llm_failure_defaults_to_task(self, engine):
        """If LLM call fails, default to task (safer)."""
        # Make the LLM call fail
        engine.client.post = AsyncMock(side_effect=Exception("Connection failed"))
        
        result = await engine.classify_intent("some query")
        
        assert result["intent"] == "task", "Should default to task on LLM failure"
        assert result["confidence"] == 0.5, "Confidence should be low on failure"

    @pytest.mark.asyncio
    async def test_ambiguous_llm_response_defaults_to_task(self, engine):
        """If LLM returns ambiguous response, default to task."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "I'm not sure"}}
        mock_response.raise_for_status = MagicMock()
        
        engine.client.post = AsyncMock(return_value=mock_response)
        
        result = await engine.classify_intent("do something")
        
        assert result["intent"] == "task", "Should default to task on ambiguous response"


class TestRegressionPrevention:
    """Prevent regression to pattern matching."""

    def test_no_pattern_lists_in_classify_intent(self):
        """classify_intent should not define pattern lists."""
        from services.reasoning_engine import ReasoningEngine
        
        source = inspect.getsource(ReasoningEngine.classify_intent)
        
        # These variable names indicate pattern matching
        forbidden_vars = [
            'task_patterns = [',
            'conversational_patterns = [',
            'patterns = [',
        ]
        
        for var in forbidden_vars:
            assert var not in source, \
                f"classify_intent contains pattern list: '{var}' - REMOVE IT!"

    def test_classify_intent_reason_mentions_llm(self):
        """Classification reason should indicate LLM was used."""
        from services.reasoning_engine import ReasoningEngine
        
        source = inspect.getsource(ReasoningEngine.classify_intent)
        
        # Should have "LLM classification" as reason
        assert 'LLM classification' in source, \
            "classify_intent should report 'LLM classification' as reason"
        
        # Should NOT have pattern-based reasons
        assert 'Matched task pattern' not in source, \
            "Should not have pattern-based reasons"
        assert 'Matched conversational pattern' not in source, \
            "Should not have pattern-based reasons"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
