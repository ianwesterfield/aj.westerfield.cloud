"""Tests for MemoryConnector - 100% coverage target."""

import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "layers", "orchestrator")
)

import httpx
from services.memory_connector import MemoryConnector
from schemas.models import BatchResult, StepResult, StepStatus, ErrorMetadata, ErrorType


@pytest.fixture
def connector():
    c = MemoryConnector()
    return c


class TestSearchPatterns:
    @pytest.mark.asyncio
    async def test_search_returns_agentic_patterns(self, connector):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "source_type": "agentic_execution",
                "user_text": "deploy my app",
                "messages": [{"content": "run deploy script"}],
                "score": 0.95,
            },
            {
                "source_type": "conversation",
                "user_text": "hello world",
            },
        ]
        mock_response.raise_for_status = MagicMock()
        connector.client.post = AsyncMock(return_value=mock_response)

        result = await connector.search_patterns("deploy", "user1", top_k=5)
        assert len(result) == 1
        assert result[0]["description"] == "deploy my app"
        assert result[0]["approach"] == "run deploy script"
        assert result[0]["score"] == 0.95

    @pytest.mark.asyncio
    async def test_search_empty_messages(self, connector):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "source_type": "agentic_execution",
                "user_text": "task",
                "messages": [],
            },
        ]
        mock_response.raise_for_status = MagicMock()
        connector.client.post = AsyncMock(return_value=mock_response)

        result = await connector.search_patterns("task", "user1")
        assert len(result) == 1
        assert result[0]["approach"] == ""

    @pytest.mark.asyncio
    async def test_search_http_error(self, connector):
        connector.client.post = AsyncMock(side_effect=httpx.HTTPError("timeout"))
        result = await connector.search_patterns("q", "u")
        assert result == []

    @pytest.mark.asyncio
    async def test_search_generic_error(self, connector):
        connector.client.post = AsyncMock(side_effect=RuntimeError("boom"))
        result = await connector.search_patterns("q", "u")
        assert result == []

    @pytest.mark.asyncio
    async def test_search_no_results(self, connector):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        connector.client.post = AsyncMock(return_value=mock_response)

        result = await connector.search_patterns("q", "u")
        assert result == []


class TestStoreExecutionTrace:
    @pytest.mark.asyncio
    async def test_store_success(self, connector):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        connector.client.post = AsyncMock(return_value=mock_response)

        batch = BatchResult(
            batch_id="b1",
            successful=[
                StepResult(step_id="s1", status=StepStatus.SUCCESS, output="ok")
            ],
            failed=[
                ErrorMetadata(
                    step_id="s2", error="fail", error_type=ErrorType.EXECUTION_ERROR
                )
            ],
            duration=1.5,
        )

        result = await connector.store_execution_trace("user1", "b1", batch)
        assert result is True

    @pytest.mark.asyncio
    async def test_store_http_error(self, connector):
        connector.client.post = AsyncMock(side_effect=httpx.HTTPError("500"))
        batch = BatchResult(batch_id="b1", successful=[], failed=[], duration=0.1)
        result = await connector.store_execution_trace("user1", "b1", batch)
        assert result is False

    @pytest.mark.asyncio
    async def test_store_generic_error(self, connector):
        connector.client.post = AsyncMock(side_effect=ValueError("bad"))
        batch = BatchResult(batch_id="b1", successful=[], failed=[], duration=0.1)
        result = await connector.store_execution_trace("user1", "b1", batch)
        assert result is False


class TestClose:
    @pytest.mark.asyncio
    async def test_close(self, connector):
        connector.client.aclose = AsyncMock()
        await connector.close()
        connector.client.aclose.assert_called_once()
