"""Tests for ParallelExecutor - 100% coverage target."""

import pytest
import sys
import os
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "layers", "orchestrator")
)

from services.parallel_executor import ParallelExecutor
from schemas.models import Step, StepResult, StepStatus, ErrorType, WorkspaceContext


@pytest.fixture
def executor():
    return ParallelExecutor()


class TestExecuteBatch:
    @pytest.mark.asyncio
    async def test_all_succeed(self, executor):
        steps = [
            Step(step_id="s1", tool="think", params={"thought": "ok"}, reasoning="t"),
            Step(step_id="s2", tool="think", params={"thought": "ok"}, reasoning="t"),
        ]
        executor._dispatch_tool = AsyncMock(
            return_value={"success": True, "output": "done"}
        )
        result = await executor.execute_batch(steps, "b1")
        assert result.batch_id == "b1"
        assert len(result.successful) == 2
        assert len(result.failed) == 0
        assert result.duration >= 0

    @pytest.mark.asyncio
    async def test_mixed_results(self, executor):
        steps = [
            Step(step_id="s1", tool="t", params={}, reasoning="t"),
            Step(step_id="s2", tool="t", params={}, reasoning="t"),
        ]

        async def mock_dispatch(tool, params, ctx=None):
            if tool == "t":
                return {"success": True, "output": "ok"}
            return {"success": False, "error": "nope"}

        executor._dispatch_tool = AsyncMock(
            side_effect=[
                {"success": True, "output": "ok"},
                {"success": False, "error": "nope"},
            ]
        )
        result = await executor.execute_batch(steps, "b2")
        assert len(result.successful) == 1
        assert len(result.failed) == 1

    @pytest.mark.asyncio
    async def test_step_raises_exception(self, executor):
        steps = [
            Step(step_id="s1", tool="t", params={}, reasoning="t"),
        ]
        executor._dispatch_tool = AsyncMock(side_effect=RuntimeError("boom"))
        result = await executor.execute_batch(steps, "b3")
        assert len(result.failed) == 1
        assert result.failed[0].error_type == ErrorType.EXECUTION_ERROR

    @pytest.mark.asyncio
    async def test_timeout_exception(self, executor):
        steps = [
            Step(step_id="s1", tool="t", params={}, reasoning="t"),
        ]
        executor._dispatch_tool = AsyncMock(side_effect=asyncio.TimeoutError())
        result = await executor.execute_batch(steps, "b4")
        assert len(result.successful) == 0
        # TimeoutError is caught in _execute_single_step, returns Failed StepResult
        assert len(result.failed) == 1

    @pytest.mark.asyncio
    async def test_workspace_context_limits_concurrency(self, executor):
        ctx = WorkspaceContext(cwd=".", workspace_root=".", max_parallel_tasks=2)
        steps = [
            Step(step_id=f"s{i}", tool="t", params={}, reasoning="t") for i in range(5)
        ]
        executor._dispatch_tool = AsyncMock(
            return_value={"success": True, "output": "ok"}
        )
        result = await executor.execute_batch(steps, "b5", workspace_context=ctx)
        assert len(result.successful) == 5

    @pytest.mark.asyncio
    async def test_step_result_with_no_output(self, executor):
        steps = [
            Step(step_id="s1", tool="t", params={}, reasoning="t"),
        ]
        executor._dispatch_tool = AsyncMock(return_value={"success": True})
        result = await executor.execute_batch(steps, "b6")
        assert len(result.successful) == 1
        # output is None when not in dict
        assert result.successful[0].output is None

    @pytest.mark.asyncio
    async def test_step_result_with_stderr_output(self, executor):
        steps = [
            Step(step_id="s1", tool="t", params={}, reasoning="t"),
        ]
        executor._dispatch_tool = AsyncMock(
            return_value={
                "success": True,
                "stdout": "out",
                "stderr": "warn",
            }
        )
        result = await executor.execute_batch(steps, "b7")
        assert len(result.successful) == 1
        assert result.successful[0].output == "out"


class TestClassifyError:
    def setup_method(self):
        self.executor = ParallelExecutor()
        self.step = Step(step_id="s1", tool="t", params={}, reasoning="t")

    def test_timeout_error(self):
        err = Exception("Connection timeout occurred")
        meta = self.executor._classify_error(self.step, err)
        assert meta.error_type == ErrorType.TIMEOUT
        assert meta.recoverable is True

    def test_permission_error(self):
        err = Exception("Permission denied for path /root")
        meta = self.executor._classify_error(self.step, err)
        assert meta.error_type == ErrorType.PERMISSION_DENIED
        assert meta.recoverable is False

    def test_sandbox_error(self):
        err = Exception("Sandbox violation detected")
        meta = self.executor._classify_error(self.step, err)
        assert meta.error_type == ErrorType.SANDBOX_VIOLATION
        assert meta.recoverable is False

    def test_resource_error(self):
        err = Exception("Resource limit exceeded")
        meta = self.executor._classify_error(self.step, err)
        assert meta.error_type == ErrorType.RESOURCE_LIMIT
        assert meta.recoverable is True

    def test_memory_error(self):
        err = Exception("Out of memory")
        meta = self.executor._classify_error(self.step, err)
        assert meta.error_type == ErrorType.RESOURCE_LIMIT
        assert meta.recoverable is True

    def test_generic_error(self):
        err = Exception("Something weird happened")
        meta = self.executor._classify_error(self.step, err)
        assert meta.error_type == ErrorType.EXECUTION_ERROR
        assert meta.recoverable is True

    def test_long_error_truncated(self):
        err = Exception("x" * 500)
        meta = self.executor._classify_error(self.step, err)
        assert len(meta.error) <= 200


class TestClose:
    @pytest.mark.asyncio
    async def test_close_is_noop(self):
        executor = ParallelExecutor()
        await executor.close()  # Should not raise


class TestMissedPaths:
    """Tests targeting specific uncovered lines."""

    @pytest.mark.asyncio
    async def test_execute_single_step_raises_covers_80_81_and_101_102(self):
        """Lines 80-81: execute_with_semaphore catches exception.
        Lines 101-102: result is Exception in aggregation."""
        executor = ParallelExecutor()
        steps = [
            Step(step_id="s1", tool="t", params={}, reasoning="t"),
        ]
        # Mock _execute_single_step to raise (bypasses _execute_single_step's own catches)
        executor._execute_single_step = AsyncMock(
            side_effect=RuntimeError("inner boom")
        )
        result = await executor.execute_batch(steps, "bx")
        assert len(result.failed) == 1
        assert result.failed[0].error_type == ErrorType.EXECUTION_ERROR

    @pytest.mark.asyncio
    async def test_asyncio_gather_returns_exception_directly(self):
        """Lines 94-95: asyncio.gather returns raw Exception."""
        executor = ParallelExecutor()
        steps = [
            Step(step_id="s1", tool="t", params={}, reasoning="t"),
        ]
        # Patch asyncio.gather to return raw exceptions
        with patch(
            "asyncio.gather", new=AsyncMock(return_value=[RuntimeError("brute")])
        ):
            result = await executor.execute_batch(steps, "bx2")
        # Exception is logged and skipped
        assert len(result.successful) == 0
        assert len(result.failed) == 0

    @pytest.mark.asyncio
    async def test_step_result_failed_status(self):
        """Lines 107-112: StepResult with FAILED status in aggregation."""
        executor = ParallelExecutor()
        steps = [
            Step(step_id="s1", tool="t", params={}, reasoning="t"),
        ]
        # Make _dispatch_tool return success=False so _execute_single_step returns FAILED StepResult
        executor._dispatch_tool = AsyncMock(
            return_value={"success": False, "error": "nah"}
        )
        result = await executor.execute_batch(steps, "bx3")
        assert len(result.successful) == 0
        assert len(result.failed) == 1
        assert result.failed[0].error == "nah"

    @pytest.mark.asyncio
    async def test_dispatch_tool_delegates(self):
        """Line 181: _dispatch_tool delegates to bash_dispatcher."""
        executor = ParallelExecutor()
        with patch(
            "services.parallel_executor.dispatch_tool",
            new=AsyncMock(return_value={"success": True, "output": "delegated"}),
        ):
            result = await executor._dispatch_tool("think", {"thought": "test"})
        assert result["output"] == "delegated"
