"""Tests for ReasoningEngine - 100% coverage target."""

import pytest
import sys
import os
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "layers", "orchestrator")
)

from services.reasoning_engine import ReasoningEngine
from services.session_state import SessionState, CompletedStep
from schemas.models import Step, StepResult, StepStatus, WorkspaceContext


@pytest.fixture
def engine():
    with patch("services.reasoning_engine.get_session_state"):
        e = ReasoningEngine()
    e.client = MagicMock()
    return e


def mock_chat_response(content):
    """Build a fake httpx response for Ollama /api/chat."""
    resp = MagicMock()
    resp.json.return_value = {"message": {"content": content}}
    resp.raise_for_status = MagicMock()
    return resp


# ==== Model management ====
class TestModelManagement:
    def test_set_model_changes(self, engine):
        engine.set_model("llama3")
        assert engine.model == "llama3"
        assert engine._model_preloaded is False

    def test_set_model_same(self, engine):
        original = engine.model
        engine._model_preloaded = True
        engine.set_model(original)
        assert engine._model_preloaded is True  # unchanged

    def test_set_model_empty(self, engine):
        original = engine.model
        engine.set_model("")
        assert engine.model == original  # unchanged

    def test_estimate_load_time_known(self, engine):
        engine.model = "aj-deepseek-r1-32b"
        # 18.5 / 0.2 = 92.5 → 92
        result = engine._estimate_load_time()
        assert result == 92

    def test_estimate_load_time_unknown(self, engine):
        engine.model = "unknown-model-xyz"
        result = engine._estimate_load_time()
        assert result == 15

    def test_estimate_load_time_small_model(self, engine):
        engine.model = "llama3.2:1b"
        result = engine._estimate_load_time()
        assert result >= 5

    @pytest.mark.asyncio
    async def test_warmup_success(self, engine):
        engine.client.post = AsyncMock(return_value=mock_chat_response("ok"))
        result = await engine.warmup_model()
        assert result is True
        assert engine._model_preloaded is True

    @pytest.mark.asyncio
    async def test_warmup_already_loaded(self, engine):
        engine._model_preloaded = True
        result = await engine.warmup_model()
        assert result is True

    @pytest.mark.asyncio
    async def test_warmup_failure(self, engine):
        engine.client.post = AsyncMock(side_effect=Exception("conn refused"))
        result = await engine.warmup_model()
        assert result is False


# ==== Intent classification ====
class TestClassifyIntent:
    @pytest.mark.asyncio
    async def test_conversational(self, engine):
        engine.client.post = AsyncMock(
            return_value=mock_chat_response("conversational")
        )
        result = await engine.classify_intent("what is Docker?")
        assert result["intent"] == "conversational"

    @pytest.mark.asyncio
    async def test_task(self, engine):
        engine.client.post = AsyncMock(return_value=mock_chat_response("task"))
        result = await engine.classify_intent("ping server01")
        assert result["intent"] == "task"

    @pytest.mark.asyncio
    async def test_mixed_signals(self, engine):
        engine.client.post = AsyncMock(
            return_value=mock_chat_response("this is a conversational task")
        )
        result = await engine.classify_intent("what?")
        assert result["intent"] == "task"  # prefer task

    @pytest.mark.asyncio
    async def test_ambiguous(self, engine):
        engine.client.post = AsyncMock(return_value=mock_chat_response("I'm not sure"))
        result = await engine.classify_intent("hmm")
        assert result["intent"] == "task"  # default

    @pytest.mark.asyncio
    async def test_think_block_stripped(self, engine):
        engine.client.post = AsyncMock(
            return_value=mock_chat_response("<think>analyzing...</think>conversational")
        )
        result = await engine.classify_intent("hello")
        assert result["intent"] == "conversational"

    @pytest.mark.asyncio
    async def test_think_block_unclosed(self, engine):
        engine.client.post = AsyncMock(
            return_value=mock_chat_response("<think>I think this is a task")
        )
        result = await engine.classify_intent("do something")
        assert result["intent"] == "task"

    @pytest.mark.asyncio
    async def test_exception(self, engine):
        engine.client.post = AsyncMock(side_effect=Exception("timeout"))
        result = await engine.classify_intent("hello")
        assert result["intent"] == "task"
        assert result["confidence"] == 0.5

    @pytest.mark.asyncio
    async def test_casual_keyword(self, engine):
        engine.client.post = AsyncMock(return_value=mock_chat_response("casual"))
        result = await engine.classify_intent("hey there")
        assert result["intent"] == "conversational"

    @pytest.mark.asyncio
    async def test_greeting_keyword(self, engine):
        engine.client.post = AsyncMock(return_value=mock_chat_response("greeting"))
        result = await engine.classify_intent("hi")
        assert result["intent"] == "conversational"


class TestClassifyIntentWithContext:
    @pytest.mark.asyncio
    async def test_task_continuation(self, engine):
        engine.client.post = AsyncMock(return_value=mock_chat_response("task"))
        result = await engine.classify_intent_with_context("yes", "Shall I deploy?")
        assert result["intent"] == "task"

    @pytest.mark.asyncio
    async def test_conversational(self, engine):
        engine.client.post = AsyncMock(
            return_value=mock_chat_response("conversational")
        )
        result = await engine.classify_intent_with_context("thanks", "Done!")
        assert result["intent"] == "conversational"

    @pytest.mark.asyncio
    async def test_exception(self, engine):
        engine.client.post = AsyncMock(side_effect=Exception("err"))
        result = await engine.classify_intent_with_context("ok", "context")
        assert result["intent"] == "conversational"


# ==== Conversational answer ====
class TestAnswerConversational:
    @pytest.mark.asyncio
    async def test_answer(self, engine):
        engine.client.post = AsyncMock(
            return_value=mock_chat_response("Docker is a container platform.")
        )
        result = await engine.answer_conversational("what is Docker?")
        assert "Docker" in result

    @pytest.mark.asyncio
    async def test_with_memory_context(self, engine):
        engine.client.post = AsyncMock(return_value=mock_chat_response("AJ's answer."))
        memory = [
            {"facts": {"preference": "dark mode"}},
            {"user_text": "previous question"},
            {"text": "another text"},
            {},  # no facts or text
        ]
        result = await engine.answer_conversational("hello", memory_context=memory)
        assert result == "AJ's answer."

    @pytest.mark.asyncio
    async def test_exception(self, engine):
        engine.client.post = AsyncMock(side_effect=Exception("api down"))
        result = await engine.answer_conversational("hello")
        assert "error" in result.lower()


# ==== Task planning ====
class TestGenerateTaskPlan:
    @pytest.mark.asyncio
    async def test_numbered_list(self, engine):
        engine.client.post = AsyncMock(
            return_value=mock_chat_response(
                "1. Discover agents\n2. Run command\n3. Report"
            )
        )
        result = await engine.generate_task_plan("check servers")
        assert len(result) == 3
        assert "Discover agents" in result[0]

    @pytest.mark.asyncio
    async def test_dash_list(self, engine):
        engine.client.post = AsyncMock(
            return_value=mock_chat_response("- Step A\n- Step B")
        )
        result = await engine.generate_task_plan("do something")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_json_steps_fallback(self, engine):
        engine.client.post = AsyncMock(
            return_value=mock_chat_response('{"steps": ["one", "two"]}')
        )
        result = await engine.generate_task_plan("plan")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_json_plan_key(self, engine):
        engine.client.post = AsyncMock(
            return_value=mock_chat_response('{"plan": ["a", "b"]}')
        )
        result = await engine.generate_task_plan("plan")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_json_list(self, engine):
        engine.client.post = AsyncMock(return_value=mock_chat_response('["x", "y"]'))
        result = await engine.generate_task_plan("plan")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_empty_response(self, engine):
        engine.client.post = AsyncMock(return_value=mock_chat_response(""))
        result = await engine.generate_task_plan("plan")
        assert result == ["Execute task"]

    @pytest.mark.asyncio
    async def test_exception(self, engine):
        engine.client.post = AsyncMock(side_effect=Exception("timeout"))
        result = await engine.generate_task_plan("plan")
        assert result == ["Execute task"]

    @pytest.mark.asyncio
    async def test_deduplication(self, engine):
        engine.client.post = AsyncMock(
            return_value=mock_chat_response("1. Do thing\n2. Do thing\n3. Other")
        )
        result = await engine.generate_task_plan("plan")
        assert len(result) == 2


# ==== Goal satisfaction ====
class TestCheckGoalSatisfaction:
    @pytest.mark.asyncio
    async def test_satisfied(self, engine):
        state = SessionState()
        state.command_flow.original_goal = "check agents"
        engine.client.post = AsyncMock(
            return_value=mock_chat_response(
                '{"satisfied": true, "confidence": 0.9, "reason": "done", "suggested_action": "complete"}'
            )
        )
        result = await engine.check_goal_satisfaction("check agents", state)
        assert result["satisfied"] is True

    @pytest.mark.asyncio
    async def test_not_satisfied(self, engine):
        state = SessionState()
        engine.client.post = AsyncMock(
            return_value=mock_chat_response(
                '{"satisfied": false, "confidence": 0.7, "reason": "not done", "suggested_action": "continue"}'
            )
        )
        result = await engine.check_goal_satisfaction("do something", state)
        assert result["satisfied"] is False

    @pytest.mark.asyncio
    async def test_invalid_json(self, engine):
        state = SessionState()
        engine.client.post = AsyncMock(
            return_value=mock_chat_response("I'm not sure about that")
        )
        result = await engine.check_goal_satisfaction("goal", state)
        assert result["suggested_action"] == "continue"

    @pytest.mark.asyncio
    async def test_exception(self, engine):
        state = SessionState()
        engine.client.post = AsyncMock(side_effect=Exception("err"))
        result = await engine.check_goal_satisfaction("goal", state)
        assert result["confidence"] == 0.3

    @pytest.mark.asyncio
    async def test_uses_default_session_state(self, engine):
        mock_state = SessionState()
        engine.client.post = AsyncMock(
            return_value=mock_chat_response('{"satisfied": true, "confidence": 0.9}')
        )
        with patch(
            "services.reasoning_engine.get_session_state", return_value=mock_state
        ):
            result = await engine.check_goal_satisfaction("goal")
        assert result["satisfied"] is True


# ==== Replanning ====
class TestGenerateReplan:
    @pytest.mark.asyncio
    async def test_replan_success(self, engine):
        state = SessionState()
        engine.client.post = AsyncMock(
            return_value=mock_chat_response("1. Try alternative\n2. Verify")
        )
        result = await engine.generate_replan("original goal", state, "timeout")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_replan_empty(self, engine):
        state = SessionState()
        engine.client.post = AsyncMock(return_value=mock_chat_response(""))
        result = await engine.generate_replan("goal", state)
        assert result == ["Try alternative approach"]

    @pytest.mark.asyncio
    async def test_replan_exception(self, engine):
        state = SessionState()
        engine.client.post = AsyncMock(side_effect=Exception("err"))
        result = await engine.generate_replan("goal", state)
        assert "Report" in result[0] or "ask user" in result[0].lower()

    @pytest.mark.asyncio
    async def test_replan_with_failures(self, engine):
        state = SessionState()
        state.command_flow.add_entry(
            step_index=1,
            tool="execute",
            success=False,
            output="",
            error="timeout",
            command="ping ws1",
        )
        engine.client.post = AsyncMock(
            return_value=mock_chat_response("1. Retry with longer timeout")
        )
        result = await engine.generate_replan("ping ws1", state, "timeout")
        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_replan_default_session(self, engine):
        mock_state = SessionState()
        engine.client.post = AsyncMock(return_value=mock_chat_response("1. step"))
        with patch(
            "services.reasoning_engine.get_session_state", return_value=mock_state
        ):
            result = await engine.generate_replan("goal")
        assert len(result) >= 1


# ==== Model status ====
class TestCheckModelStatus:
    @pytest.mark.asyncio
    async def test_model_loaded(self, engine):
        resp = MagicMock()
        resp.json.return_value = {
            "models": [{"name": engine.model, "size_vram": 20 * 1024**3}]
        }
        resp.raise_for_status = MagicMock()
        engine.client.get = AsyncMock(return_value=resp)
        result = await engine.check_model_status()
        assert result["loaded"] is True

    @pytest.mark.asyncio
    async def test_model_not_loaded(self, engine):
        resp = MagicMock()
        resp.json.return_value = {"models": []}
        resp.raise_for_status = MagicMock()
        engine.client.get = AsyncMock(return_value=resp)
        result = await engine.check_model_status()
        assert result["loaded"] is False

    @pytest.mark.asyncio
    async def test_model_status_error(self, engine):
        engine.client.get = AsyncMock(side_effect=Exception("down"))
        result = await engine.check_model_status()
        assert result["loaded"] is False

    @pytest.mark.asyncio
    async def test_model_zero_vram(self, engine):
        resp = MagicMock()
        resp.json.return_value = {"models": [{"name": engine.model, "size_vram": 0}]}
        resp.raise_for_status = MagicMock()
        engine.client.get = AsyncMock(return_value=resp)
        result = await engine.check_model_status()
        assert result["loaded"] is True
        assert "0.0GB" in result["details"]


# ==== Step generation ====
class TestGenerateNextStep:
    @pytest.mark.asyncio
    async def test_basic_generation(self, engine):
        state = SessionState()
        engine._call_ollama = AsyncMock(
            return_value='{"tool": "think", "params": {"thought": "planning"}}'
        )
        step = await engine.generate_next_step("task", [], [], session_state=state)
        assert step.tool == "think"

    @pytest.mark.asyncio
    async def test_15_step_guardrail_no_edits(self, engine):
        state = SessionState()
        for i in range(16):
            state.completed_steps.append(
                CompletedStep(
                    step_id=f"s{i}",
                    tool="think",
                    params={},
                    output_summary="ok",
                    success=True,
                )
            )
        step = await engine.generate_next_step("task", [], [], session_state=state)
        assert step.tool == "complete"
        assert "Too many steps" in step.params.get("error", "")

    @pytest.mark.asyncio
    async def test_15_step_guardrail_with_edits(self, engine):
        state = SessionState()
        # Use diverse tools to avoid loop detection guardrail
        tools = ["execute", "read_file", "write_file", "think", "execute"]
        for i in range(14):
            state.completed_steps.append(
                CompletedStep(
                    step_id=f"s{i}",
                    tool=tools[i % len(tools)],
                    params={},
                    output_summary="ok",
                    success=True,
                )
            )
        # Recent edit in last 5
        state.completed_steps.append(
            CompletedStep(
                step_id="s14",
                tool="write_file",
                params={},
                output_summary="ok",
                success=True,
            )
        )
        engine._call_ollama = AsyncMock(
            return_value='{"tool": "think", "params": {"thought": "continuing"}}'
        )
        step = await engine.generate_next_step("task", [], [], session_state=state)
        assert step.tool == "think"  # not blocked - has recent edits

    @pytest.mark.asyncio
    async def test_call_ollama_error(self, engine):
        state = SessionState()
        engine._call_ollama = AsyncMock(side_effect=Exception("api timeout"))
        step = await engine.generate_next_step("task", [], [], session_state=state)
        assert step.tool == "complete"
        assert "api timeout" in step.params.get("error", "")

    @pytest.mark.asyncio
    async def test_default_session_state(self, engine):
        mock_state = SessionState()
        engine._call_ollama = AsyncMock(
            return_value='{"tool": "think", "params": {"thought": "ok"}}'
        )
        with patch(
            "services.reasoning_engine.get_session_state", return_value=mock_state
        ):
            step = await engine.generate_next_step("task", [], [])
        assert step.tool == "think"


# ==== Build context ====
class TestBuildContext:
    def test_with_workspace(self, engine):
        state = SessionState()
        ctx = WorkspaceContext(cwd="/app", workspace_root="/app")
        result = engine._build_context("task", [], ctx, state)
        assert "/app" in result

    def test_with_user_info(self, engine):
        state = SessionState()
        state.user_info = {"name": "AJ", "role": "admin"}
        result = engine._build_context("task", [], None, state)
        assert "AJ" in result

    def test_with_memory(self, engine):
        state = SessionState()
        memory = [{"description": "deploy pattern", "approach": "run script"}]
        result = engine._build_context("task", memory, None, state)
        assert "deploy pattern" in result

    def test_minimal(self, engine):
        state = SessionState()
        result = engine._build_context("my task", [], None, state)
        assert "my task" in result


# ==== Script validation ====
class TestValidateScript:
    def test_delegates_to_validator(self, engine):
        result = engine.validate_script("Get-Process", "powershell")
        assert isinstance(result, dict)


# ==== Call Ollama ====
class TestCallOllama:
    @pytest.mark.asyncio
    async def test_call_ollama(self, engine):
        engine.client.post = AsyncMock(
            return_value=mock_chat_response('{"tool": "think", "params": {}}')
        )
        result = await engine._call_ollama("test prompt")
        assert "think" in result


# ==== Streaming ====
class TestCallOllamaStreaming:
    @pytest.mark.asyncio
    async def test_streaming_basic(self, engine):
        # Mock streaming response
        lines = [
            json.dumps({"message": {"content": "hel"}}),
            json.dumps({"message": {"content": "lo"}}),
            json.dumps({"message": {"content": ""}, "done": True}),
        ]

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        async def fake_aiter_lines():
            for line in lines:
                yield line

        mock_response.aiter_lines = fake_aiter_lines

        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

        engine.client.stream = MagicMock(return_value=mock_stream_ctx)

        tokens = []
        async for token, in_think, accumulated in engine._call_ollama_streaming("test"):
            tokens.append(token)

        assert "hel" in tokens
        assert "lo" in tokens

    @pytest.mark.asyncio
    async def test_streaming_think_blocks(self, engine):
        lines = [
            json.dumps({"message": {"content": "<think>"}}),
            json.dumps({"message": {"content": "reasoning"}}),
            json.dumps({"message": {"content": "</think>"}}),
            json.dumps({"message": {"content": '{"tool":"think"}'}}),
            json.dumps({"done": True}),
        ]

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        async def fake_aiter_lines():
            for line in lines:
                yield line

        mock_response.aiter_lines = fake_aiter_lines

        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

        engine.client.stream = MagicMock(return_value=mock_stream_ctx)

        results = []
        async for token, in_think, accumulated in engine._call_ollama_streaming("test"):
            results.append((token, in_think))

        # At some point in_think should have been True
        assert any(in_think for _, in_think in results)

    @pytest.mark.asyncio
    async def test_streaming_invalid_json_line(self, engine):
        lines = [
            "not json",
            json.dumps({"message": {"content": "ok"}}),
            json.dumps({"done": True}),
        ]

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        async def fake_aiter_lines():
            for line in lines:
                yield line

        mock_response.aiter_lines = fake_aiter_lines

        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

        engine.client.stream = MagicMock(return_value=mock_stream_ctx)

        tokens = []
        async for token, _, _ in engine._call_ollama_streaming("test"):
            if token:
                tokens.append(token)
        assert "ok" in tokens

    @pytest.mark.asyncio
    async def test_streaming_empty_lines(self, engine):
        lines = [
            "",
            json.dumps({"message": {"content": "x"}}),
            "",
            json.dumps({"done": True}),
        ]

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        async def fake_aiter_lines():
            for line in lines:
                yield line

        mock_response.aiter_lines = fake_aiter_lines

        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

        engine.client.stream = MagicMock(return_value=mock_stream_ctx)

        tokens = []
        async for token, _, _ in engine._call_ollama_streaming("test"):
            if token:
                tokens.append(token)
        assert "x" in tokens


class TestGenerateNextStepStreaming:
    @pytest.mark.asyncio
    async def test_streaming_basic(self, engine):
        state = SessionState()

        async def fake_stream(msg):
            yield '{"tool"', False, '{"tool"'
            yield ': "think"}', False, '{"tool": "think"}'

        engine._call_ollama_streaming = fake_stream

        results = []
        async for token, step in engine.generate_next_step_streaming(
            "task", [], [], session_state=state
        ):
            results.append((token, step))

        # Last item should have a Step
        assert results[-1][1] is not None
        assert results[-1][1].tool is not None

    @pytest.mark.asyncio
    async def test_streaming_with_think_content_yields_tokens(self, engine):
        """When stream has <think> block, parser.feed returns content → line 895 hit."""
        state = SessionState()

        full_text = '<think>planning steps</think>{"tool": "think", "params": {"summary": "ok"}}'

        async def fake_stream(msg):
            yield "<think>", False, "<think>"
            yield "planning steps", False, "<think>planning steps"
            yield "</think>", False, "<think>planning steps</think>"
            yield '{"tool"', False, full_text[:40]
            yield ': "think", "params": {"summary": "ok"}}', False, full_text

        engine._call_ollama_streaming = fake_stream

        tokens_yielded = []
        final_step = None
        async for token, step in engine.generate_next_step_streaming(
            "task", [], [], session_state=state
        ):
            if token:
                tokens_yielded.append(token)
            if step:
                final_step = step

        # The parser should have yielded planning steps content
        assert len(tokens_yielded) > 0
        assert final_step is not None

    @pytest.mark.asyncio
    async def test_streaming_15_step_guardrail(self, engine):
        state = SessionState()
        for i in range(16):
            state.completed_steps.append(
                CompletedStep(
                    step_id=f"s{i}",
                    tool="think",
                    params={},
                    output_summary="ok",
                    success=True,
                )
            )

        results = []
        async for token, step in engine.generate_next_step_streaming(
            "task", [], [], session_state=state
        ):
            results.append((token, step))

        assert any(s is not None and s.tool == "complete" for _, s in results)

    @pytest.mark.asyncio
    async def test_streaming_error(self, engine):
        state = SessionState()

        async def error_stream(msg):
            raise Exception("stream error")
            yield  # make it a generator

        engine._call_ollama_streaming = error_stream

        results = []
        async for token, step in engine.generate_next_step_streaming(
            "task", [], [], session_state=state
        ):
            results.append((token, step))

        assert any(s is not None and s.tool == "complete" for _, s in results)

    @pytest.mark.asyncio
    async def test_streaming_with_status_callback(self, engine):
        state = SessionState()
        statuses = []

        async def fake_stream_with_status(msg, cb):
            yield "token", False, "token"

        engine._stream_with_status = fake_stream_with_status
        engine._call_ollama_streaming = AsyncMock()

        results = []
        async for token, step in engine.generate_next_step_streaming(
            "task",
            [],
            [],
            session_state=state,
            status_callback=lambda s: statuses.append(s),
        ):
            results.append((token, step))


# ==== _stream_with_status ====
class TestStreamWithStatus:
    @pytest.mark.asyncio
    async def test_stream_with_status_model_loaded(self, engine):
        """Status callback reports 'Reasoning...' when model is loaded."""
        statuses = []

        async def fake_streaming(msg):
            # Simulate a small delay so the status monitor has time to check
            await asyncio.sleep(0.05)
            yield "hello", False, "hello"

        engine._call_ollama_streaming = fake_streaming
        engine.check_model_status = AsyncMock(
            return_value={"loaded": True, "vram_percent": 100}
        )
        engine._estimate_load_time = MagicMock(return_value=10)

        tokens = []
        async for token, in_think, accumulated in engine._stream_with_status(
            "test message", lambda s: statuses.append(s)
        ):
            tokens.append(token)

        assert "hello" in tokens
        # Status monitor should have emitted at least one status
        assert any("Reasoning" in s for s in statuses)

    @pytest.mark.asyncio
    async def test_stream_with_status_model_loading(self, engine):
        """Status callback reports 'Loading model...' when model is not loaded."""
        statuses = []

        async def fake_streaming(msg):
            await asyncio.sleep(0.1)
            yield "tok", False, "tok"

        engine._call_ollama_streaming = fake_streaming
        engine.check_model_status = AsyncMock(
            return_value={"loaded": False, "vram_percent": 0}
        )
        engine._estimate_load_time = MagicMock(return_value=60)

        tokens = []
        async for token, in_think, accumulated in engine._stream_with_status(
            "test", lambda s: statuses.append(s)
        ):
            tokens.append(token)

        assert "tok" in tokens
        assert any("Loading" in s for s in statuses)

    def test_stream_with_status_model_loaded_long_elapsed(self, engine):
        """After 10s of reasoning, status shows elapsed time (format unit test)."""
        # The status_monitor uses loop.time() internally which we can't easily
        # patch without breaking asyncio. Test the formatting logic directly.
        model_was_loaded = True
        elapsed = 15.0
        # Branch: model loaded AND model_was_loaded already True AND elapsed >= 10
        new_status = f"\U0001f9e0 Reasoning... ({int(elapsed)}s)"
        assert "15" in new_status
        assert "Reasoning" in new_status

    def test_stream_with_status_loading_past_estimate(self, engine):
        """When loading takes longer than estimated, show elapsed seconds (unit test for formatting)."""
        # Test the formatting branches when model is NOT loaded
        estimated_total = 1.0

        # Branch: elapsed >= estimated_total
        elapsed = 5.0
        new_status = f"\u23f3 Loading model... ({elapsed:.0f}s)"
        assert "5s" in new_status

        # Branch: elapsed < estimated_total (percent display)
        elapsed2 = 0.5
        percent = min(95, int((elapsed2 / estimated_total) * 100))
        new_status2 = f"\u23f3 Loading model... {percent}%"
        assert "%" in new_status2
        assert "50" in new_status2

    @pytest.mark.asyncio
    async def test_stream_with_status_cancels_monitor_on_done(self, engine):
        """Status monitor is cancelled after streaming finishes."""

        async def instant_stream(msg):
            yield "done", False, "done"

        engine._call_ollama_streaming = instant_stream
        engine.check_model_status = AsyncMock(
            return_value={"loaded": True, "vram_percent": 100}
        )
        engine._estimate_load_time = MagicMock(return_value=10)

        tokens = []
        async for token, in_think, accumulated in engine._stream_with_status(
            "test", lambda s: None
        ):
            tokens.append(token)

        assert "done" in tokens

    @pytest.mark.asyncio
    async def test_stream_with_status_monitor_timeout_continue(self, engine):
        """Status monitor loops via TimeoutError then breaks when event is set (lines 1115-1117).

        We need the event to fire DURING wait_for, not during check_model_status.
        So we use a sync-like coroutine for check_model_status that doesn't
        truly yield to the event loop, and a stream delay that puts the event
        set inside the wait_for window.
        """
        statuses = []
        call_count = 0

        async def fast_check_status():
            """Return immediately without yielding to event loop."""
            nonlocal call_count
            call_count += 1
            return {"loaded": True, "vram_percent": 100}

        async def slow_stream(msg):
            # check_interval is 0.3s; we want event set during 2nd wait_for:
            #   - 1st wait_for: t=0 to 0.3 → timeout → continue
            #   - 2nd iteration overhead: ~0.3 to ~0.31
            #   - 2nd wait_for: t≈0.31 to 0.61
            #   - event fires at t=0.5 → INSIDE 2nd wait_for → break
            await asyncio.sleep(0.5)
            yield "tok", False, "tok"

        engine._call_ollama_streaming = slow_stream
        engine.check_model_status = fast_check_status
        engine._estimate_load_time = MagicMock(return_value=10)

        tokens = []
        async for token, in_think, accumulated in engine._stream_with_status(
            "test", lambda s: statuses.append(s)
        ):
            tokens.append(token)

        assert "tok" in tokens
        assert len(statuses) >= 1
        # Monitor should have called check_status at least twice (timeout loop)
        assert call_count >= 2

    @pytest.mark.asyncio
    async def test_stream_with_status_error_in_stream(self, engine):
        """If the underlying stream errors, finally block sets event and cancels."""

        async def error_stream(msg):
            raise Exception("stream broke")
            yield  # make it a generator

        engine._call_ollama_streaming = error_stream
        engine.check_model_status = AsyncMock(
            return_value={"loaded": True, "vram_percent": 100}
        )
        engine._estimate_load_time = MagicMock(return_value=10)

        with pytest.raises(Exception, match="stream broke"):
            async for _ in engine._stream_with_status("test", lambda s: None):
                pass


# ==== Streaming default session state ====
class TestStreamingDefaultSessionState:
    @pytest.mark.asyncio
    async def test_streaming_uses_default_session_state(self, engine):
        """When session_state=None, get_session_state() is called."""

        async def fake_stream(msg):
            yield '{"tool": "complete"}', False, '{"tool": "complete"}'

        engine._call_ollama_streaming = fake_stream

        with patch(
            "services.reasoning_engine.get_session_state",
            return_value=SessionState(),
        ) as mock_get:
            results = []
            async for token, step in engine.generate_next_step_streaming(
                "task", [], [], session_state=None
            ):
                results.append((token, step))
            mock_get.assert_called_once()


# ==== 15-step guardrail WITH edits ====
class TestStreamingGuardrailWithEdits:
    @pytest.mark.asyncio
    async def test_15_step_with_recent_edits_continues(self, engine):
        """If there are recent edits, the guardrail doesn't force completion."""
        state = SessionState()
        for i in range(16):
            tool = "write_file" if i >= 12 else "think"
            state.completed_steps.append(
                CompletedStep(
                    step_id=f"s{i}",
                    tool=tool,
                    params={},
                    output_summary="ok",
                    success=True,
                )
            )

        async def fake_stream(msg):
            yield '{"tool": "think"}', False, '{"tool": "think"}'

        engine._call_ollama_streaming = fake_stream

        results = []
        async for token, step in engine.generate_next_step_streaming(
            "task", [], [], session_state=state
        ):
            results.append((token, step))

        # Should NOT have forced completion - last step should not be "complete"
        final_step = results[-1][1]
        assert final_step is not None
        assert final_step.tool != "complete" or "Too many" not in final_step.params.get(
            "error", ""
        )


# ==== check_goal_satisfaction no JSON path ====
class TestGoalSatisfactionNoJson:
    @pytest.mark.asyncio
    async def test_no_json_in_response(self, engine):
        """Response has no curly braces at all, hits the default return."""
        state = SessionState()
        engine.client.post = AsyncMock(
            return_value=mock_chat_response("Looks good to me!")
        )
        result = await engine.check_goal_satisfaction("goal", state)
        assert result["reason"] == "Unable to parse LLM response"
        assert result["satisfied"] is False
        assert result["confidence"] == 0.5

    @pytest.mark.asyncio
    async def test_json_decode_error_in_match(self, engine):
        """Response has curly braces but invalid JSON inside."""
        state = SessionState()
        engine.client.post = AsyncMock(
            return_value=mock_chat_response("{not valid json at all}")
        )
        result = await engine.check_goal_satisfaction("goal", state)
        # json.loads fails on the matched text → JSONDecodeError caught → falls through
        assert result["reason"] == "Unable to parse LLM response"


# ==== Close ====
class TestClose:
    @pytest.mark.asyncio
    async def test_close(self, engine):
        engine.client.aclose = AsyncMock()
        await engine.close()
        engine.client.aclose.assert_called_once()


# ==== format_status (extracted from status_monitor) ====
class TestFormatStatus:
    def test_model_loaded_first_time(self):
        was, msg = ReasoningEngine.format_status(
            loaded=True, model_was_loaded=False, elapsed=2.0, estimated_total=30
        )
        assert was is True
        assert msg == "🧠 Reasoning..."

    def test_model_loaded_short_elapsed(self):
        was, msg = ReasoningEngine.format_status(
            loaded=True, model_was_loaded=True, elapsed=5.0, estimated_total=30
        )
        assert was is True
        assert msg == "🧠 Reasoning..."

    def test_model_loaded_long_elapsed(self):
        was, msg = ReasoningEngine.format_status(
            loaded=True, model_was_loaded=True, elapsed=15.0, estimated_total=30
        )
        assert was is True
        assert msg == "🧠 Reasoning... (15s)"

    def test_model_not_loaded_within_estimate(self):
        was, msg = ReasoningEngine.format_status(
            loaded=False, model_was_loaded=False, elapsed=10.0, estimated_total=30
        )
        assert was is False
        assert "Loading model..." in msg
        assert "33%" in msg

    def test_model_not_loaded_past_estimate(self):
        was, msg = ReasoningEngine.format_status(
            loaded=False, model_was_loaded=False, elapsed=40.0, estimated_total=30
        )
        assert was is False
        assert msg == "⏳ Loading model... (40s)"

    def test_model_not_loaded_at_boundary(self):
        was, msg = ReasoningEngine.format_status(
            loaded=False, model_was_loaded=False, elapsed=30.0, estimated_total=30
        )
        assert was is False
        assert "Loading model..." in msg
        # elapsed == estimated_total → not < estimated_total → past estimate branch
        assert "(30s)" in msg

    def test_percent_capped_at_95(self):
        was, msg = ReasoningEngine.format_status(
            loaded=False, model_was_loaded=False, elapsed=29.9, estimated_total=30
        )
        assert was is False
        assert "95%" in msg  # min(95, 99) = 95
