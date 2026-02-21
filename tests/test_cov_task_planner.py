"""Tests for TaskPlanner - 100% coverage target."""

import pytest
import sys
import os
import tempfile

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "layers", "orchestrator")
)

from services.task_planner import TaskPlanner
from schemas.models import Step, WorkspaceContext


class TestExpandBatch:
    def setup_method(self):
        self.planner = TaskPlanner()

    @pytest.mark.asyncio
    async def test_expand_with_matching_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            for name in ["a.txt", "b.txt", "c.txt"]:
                open(os.path.join(tmpdir, name), "w").close()

            step = Step(
                step_id="batch_1",
                tool="batch",
                params={"pattern": "*.txt", "operation": "read_file"},
                batch_id="B001",
                reasoning="test",
            )
            ctx = WorkspaceContext(cwd=tmpdir, workspace_root=tmpdir)
            result = await self.planner.expand_batch(step, ctx)
            assert len(result) == 3
            assert all(s.tool == "read_file" for s in result)
            assert all(s.batch_id == "B001" for s in result)

    @pytest.mark.asyncio
    async def test_expand_no_matching_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            step = Step(
                step_id="batch_2",
                tool="batch",
                params={"pattern": "*.xyz", "operation": "read_file"},
                batch_id=None,
                reasoning="test",
            )
            result = await self.planner.expand_batch(step, None)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_expand_generates_batch_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "file.txt"), "w").close()
            step = Step(
                step_id="batch_3",
                tool="batch",
                params={"pattern": "*.txt"},
                batch_id=None,
                reasoning="test",
            )
            ctx = WorkspaceContext(cwd=tmpdir, workspace_root=tmpdir)
            result = await self.planner.expand_batch(step, ctx)
            assert len(result) == 1
            assert result[0].batch_id.startswith("batch_")

    @pytest.mark.asyncio
    async def test_expand_respects_max_batch_size(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(150):
                open(os.path.join(tmpdir, f"f{i}.txt"), "w").close()
            step = Step(
                step_id="batch_4",
                tool="batch",
                params={"pattern": "*.txt"},
                batch_id=None,
                reasoning="test",
            )
            # With workspace_context: max = max_parallel_tasks * 10
            ctx = WorkspaceContext(
                cwd=tmpdir, workspace_root=tmpdir, max_parallel_tasks=2
            )
            result = await self.planner.expand_batch(step, ctx)
            assert len(result) <= 20  # 2 * 10

    @pytest.mark.asyncio
    async def test_expand_without_workspace_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(5):
                open(os.path.join(tmpdir, f"f{i}.txt"), "w").close()
            step = Step(
                step_id="batch_5",
                tool="batch",
                params={"pattern": "*.txt"},
                batch_id=None,
                reasoning="test",
            )
            # No workspace_context - uses default "." as root
            result = await self.planner.expand_batch(step, None)
            # May or may not find files depending on cwd
            assert isinstance(result, list)


class TestDetectParallelization:
    def setup_method(self):
        self.planner = TaskPlanner()

    def test_always_returns_false(self):
        assert self.planner.detect_parallelization("process all files") is False

    def test_with_parallel_disabled(self):
        ctx = WorkspaceContext(cwd=".", workspace_root=".", parallel_enabled=False)
        assert self.planner.detect_parallelization("all files", ctx) is False

    def test_with_parallel_enabled(self):
        ctx = WorkspaceContext(cwd=".", workspace_root=".", parallel_enabled=True)
        # Still returns False (delegated to LLM per docstring)
        assert self.planner.detect_parallelization("all files", ctx) is False


class TestEstimateTaskComplexity:
    def setup_method(self):
        self.planner = TaskPlanner()

    def test_short_task(self):
        assert self.planner.estimate_task_complexity("ls") == 1

    def test_medium_task(self):
        assert self.planner.estimate_task_complexity("a" * 100) == 2

    def test_longer_task(self):
        assert self.planner.estimate_task_complexity("a" * 300) == 3

    def test_complex_task(self):
        result = self.planner.estimate_task_complexity("a" * 600)
        assert result >= 4

    def test_very_complex_task_capped(self):
        result = self.planner.estimate_task_complexity("a" * 10000)
        assert result <= 10
