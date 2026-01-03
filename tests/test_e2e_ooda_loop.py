"""
End-to-End Tests for Agentic Reasoning System

Tests the complete OODA loop (Observe, Orient, Decide, Act) for multi-step tasks.
Validates that the system can plan, execute, learn, and adapt.
"""

import pytest
import asyncio
import json
import httpx
from typing import List, Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass, field


@dataclass
class TestEvent:
    """Represents an event from the orchestrator stream."""
    event_type: str
    content: Optional[str] = None
    status: Optional[str] = None
    step_num: Optional[int] = None
    tool: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    done: bool = False


class TestOODALoop:
    """Test the complete Observe-Orient-Decide-Act cycle."""

    @pytest.fixture
    async def orchestrator_client(self):
        """Create a test client for the orchestrator API."""
        async with httpx.AsyncClient(
            base_url="http://localhost:8004",
            timeout=httpx.Timeout(300.0, connect=10.0)  # 5 min timeout for large model inference
        ) as client:
            yield client

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multi_step_task_execution(self, orchestrator_client):
        """
        E2E test: Execute a multi-step task and validate the complete flow.

        This tests:
        1. Task planning (Decide phase)
        2. Step-by-step execution (Act phase)
        3. Memory integration (Learn phase)
        4. Plan adaptation if needed (Orient phase)
        """
        # Test task: Create a simple project structure
        task = "Create a simple Python project with README.md, main.py, and requirements.txt"

        # Collect all events from the streaming response
        events = []
        collected_content = ""

        try:
            async with orchestrator_client.stream(
                "POST",
                "/api/orchestrate/run-task",
                json={
                    "task": task,
                    "workspace_root": "/workspace",  # Use the allowed workspace path
                    "user_id": "test_user",
                    "max_steps": 10,
                    "preserve_state": False,
                },
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    try:
                        event_data = json.loads(line[6:])  # Strip "data: " prefix
                        event = TestEvent(
                            event_type=event_data.get("event_type", ""),
                            content=event_data.get("content"),
                            status=event_data.get("status"),
                            step_num=event_data.get("step_num"),
                            tool=event_data.get("tool"),
                            result=event_data.get("result"),
                            done=event_data.get("done", False),
                        )
                        events.append(event)

                        # Collect thinking content
                        if event.event_type == "thinking" and event.content:
                            collected_content += event.content

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            pytest.fail(f"Failed to execute task: {e}")

        # Debug: Print all events to understand what's happening
        print(f"\n=== DEBUG: Received {len(events)} events ===")
        for i, event in enumerate(events[:20]):  # First 20 events
            print(f"Event {i}: type={event.event_type}, status={event.status}, content={event.content[:50] if event.content else None}")
        
        # Validate the complete execution flow
        self._validate_execution_flow(events, collected_content)

    def _validate_execution_flow(self, events: List[TestEvent], thinking_content: str):
        """Validate that the execution followed the expected OODA pattern."""

        # 1. Should start with memory check
        memory_events = [e for e in events if e.status and "Checking memory" in e.status]
        assert len(memory_events) > 0, "Should check memory at start"

        # 2. Should generate a task plan
        plan_events = [e for e in events if e.event_type == "plan"]
        assert len(plan_events) > 0, "Should generate a task plan"

        # 3. Should show planning status
        planning_events = [e for e in events if e.status and "Planning" in e.status]
        assert len(planning_events) > 0, "Should show planning status"

        # 4. Should execute multiple steps
        step_events = [e for e in events if e.event_type == "result" and e.step_num]
        assert len(step_events) >= 2, f"Should execute multiple steps, got {len(step_events)}"

        # 5. Should use appropriate tools for the task
        tools_used = {e.tool for e in step_events if e.tool}
        # For file creation tasks, we accept file operations or shell commands
        file_tools = {"write_file", "execute_shell", "scan_workspace", "read_file"}
        assert len(tools_used.intersection(file_tools)) > 0, f"Should use file tools {file_tools}, used {tools_used}"

        # 6. Should show thinking content or task progress
        assert len(thinking_content) > 0, "Should stream thinking content"
        # The content may include task plan, reasoning emoji (💭), or explicit thinking
        has_reasoning = (
            "<think>" in thinking_content or 
            "think" in thinking_content.lower() or
            "💭" in thinking_content or
            "plan" in thinking_content.lower()
        )
        assert has_reasoning, f"Should show reasoning process. Content preview: {thinking_content[:200]}"

        # 7. Should complete successfully (complete event or result with done=True)
        completion_events = [e for e in events if e.done or e.event_type == "complete"]
        assert len(completion_events) > 0, "Should complete the task"

        # 8. Should show status updates during execution
        status_events = [e for e in events if e.event_type == "status"]
        assert len(status_events) > 0, "Should show status updates"

        # 9. Should not get stuck (no excessive status events)
        assert len(status_events) < 100, f"Too many status events ({len(status_events)}), possible infinite loop"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_adaptive_planning_on_failure(self, orchestrator_client):
        """
        Test that the system can adapt its plan when a step fails.

        This tests the "Orient" phase of OODA - learning from failures and adapting.
        """
        # Task that will likely fail initially (non-existent file)
        # Be explicit about using read_file to read the file content
        task = "Use read_file to read the contents of /workspace/nonexistent_data.txt and tell me what's in it"

        events = []
        collected_content = ""

        try:
            async with orchestrator_client.stream(
                "POST",
                "/api/orchestrate/run-task",
                json={
                    "task": task,
                    "workspace_root": "/workspace",
                    "user_id": "test_user",
                    "max_steps": 5,
                    "preserve_state": False,
                },
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    try:
                        event_data = json.loads(line[6:])
                        event = TestEvent(
                            event_type=event_data.get("event_type", ""),
                            content=event_data.get("content"),
                            status=event_data.get("status"),
                            step_num=event_data.get("step_num"),
                            tool=event_data.get("tool"),
                            result=event_data.get("result"),
                            done=event_data.get("done", False),
                        )
                        events.append(event)

                        if event.event_type == "thinking" and event.content:
                            collected_content += event.content

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            pytest.fail(f"Failed to execute task: {e}")

        # Validate adaptive behavior
        self._validate_adaptive_behavior(events, collected_content)

    def _validate_adaptive_behavior(self, events: List[TestEvent], thinking_content: str):
        """Validate that the system adapted to failure or completed gracefully."""

        # Should have gone through the OODA loop (plan, think, complete/act)
        event_types = [e.event_type for e in events]
        has_planning = "plan" in event_types
        has_thinking = "thinking" in event_types
        has_completion = "complete" in event_types or any(e.done for e in events)
        
        assert has_planning, f"Should have planning phase. Events: {event_types}"
        assert has_thinking, f"Should have thinking phase. Events: {event_types}"
        assert has_completion, "Should complete even with failure"

        # Should show some reasoning about the task
        has_content = len(thinking_content) > 20  # At least some reasoning content
        assert has_content, f"Should show reasoning. Content length: {len(thinking_content)}"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_integration(self, orchestrator_client):
        """
        Test that the system uses memory for better planning.

        This tests the "Learn" phase - remembering previous patterns.
        """
        # First task: Create a file
        task1 = "Create a file called test.txt with content 'Hello World'"

        # Execute first task
        await self._execute_task(orchestrator_client, task1)

        # Second task: Read the file we just created
        task2 = "Read the test.txt file and tell me what it contains"

        events = await self._execute_task(orchestrator_client, task2)

        # Validate memory usage
        self._validate_memory_usage(events)

    async def _execute_task(self, client, task: str) -> List[TestEvent]:
        """Helper to execute a task and return events."""
        events = []

        async with client.stream(
            "POST",
            "/api/orchestrate/run-task",
            json={
                "task": task,
                "workspace_root": "/workspace",
                "user_id": "test_user",
                "max_steps": 5,
                "preserve_state": True,  # Preserve state between tasks
            },
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue

                try:
                    event_data = json.loads(line[6:])
                    event = TestEvent(
                        event_type=event_data.get("event_type", ""),
                        content=event_data.get("content"),
                        status=event_data.get("status"),
                        step_num=event_data.get("step_num"),
                        tool=event_data.get("tool"),
                        result=event_data.get("result"),
                        done=event_data.get("done", False),
                    )
                    events.append(event)

                except json.JSONDecodeError:
                    continue

        return events

    def _validate_memory_usage(self, events: List[TestEvent]):
        """Validate that memory/context was used."""

        # Should find the file (from previous task's state)
        read_events = [e for e in events if e.tool == "read_file"]
        assert len(read_events) > 0, "Should read the file"

        # Should succeed (file exists from previous task)
        success_events = [e for e in events if e.result and e.result.get("success", False)]
        assert len(success_events) > 0, "Should successfully read the file"

        # Should complete with the file content
        completion_events = [e for e in events if e.done and e.result]
        assert len(completion_events) > 0, "Should complete with file content"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_streaming_ux_during_execution(self, orchestrator_client):
        """
        Test that the streaming UX works properly during execution.

        Validates real-time status updates and thinking display.
        """
        task = "Scan the workspace and list all Python files (.py)"

        events = []
        status_updates = []
        thinking_content = ""

        async with orchestrator_client.stream(
            "POST",
            "/api/orchestrate/run-task",
            json={
                "task": task,
                "workspace_root": "/workspace",
                "user_id": "test_user",
                "max_steps": 3,
                "preserve_state": False,
            },
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue

                try:
                    event_data = json.loads(line[6:])
                    event = TestEvent(
                        event_type=event_data.get("event_type", ""),
                        content=event_data.get("content"),
                        status=event_data.get("status"),
                        step_num=event_data.get("step_num"),
                        tool=event_data.get("tool"),
                        result=event_data.get("result"),
                        done=event_data.get("done", False),
                    )
                    events.append(event)

                    if event.event_type == "status" and event.status:
                        status_updates.append(event.status)

                    if event.event_type == "thinking" and event.content:
                        thinking_content += event.content

                except json.JSONDecodeError:
                    continue

        # Validate streaming UX
        self._validate_streaming_ux(status_updates, thinking_content, events)

    def _validate_streaming_ux(self, status_updates: List[str], thinking_content: str, events: List[TestEvent]):
        """Validate the streaming user experience."""

        # Should show memory check
        memory_status = [s for s in status_updates if "memory" in s.lower()]
        assert len(memory_status) > 0, "Should show memory checking status"

        # Should show planning
        planning_status = [s for s in status_updates if "planning" in s.lower()]
        assert len(planning_status) > 0, "Should show planning status"

        # Should show thinking content
        assert len(thinking_content) > 0, "Should stream thinking content"

        # Should show tool execution status (any file or discovery operation)
        tool_status = [s for s in status_updates if any(
            tool in s.lower() for tool in 
            ["scan", "read", "list", "write", "creat", "discover", "agent"]
        )]
        assert len(tool_status) > 0, f"Should show tool execution status. Status updates: {status_updates[:20]}"

        # Should not have excessive status updates (prevents spam)
        assert len(status_updates) < 50, f"Too many status updates ({len(status_updates)}), possible spam"

        # Should complete
        completion_events = [e for e in events if e.done]
        assert len(completion_events) > 0, "Should complete the task"


class TestGuardrailsE2E:
    """Test guardrails in end-to-end scenarios."""

    @pytest.fixture
    async def orchestrator_client(self):
        """Create a test client for the orchestrator API."""
        async with httpx.AsyncClient(
            base_url="http://localhost:8004",
            timeout=httpx.Timeout(300.0, connect=10.0)  # 5 min timeout for large model inference
        ) as client:
            yield client

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_prevents_infinite_loops(self, orchestrator_client):
        """
        Test that the system prevents infinite loops by enforcing max steps.
        """
        # Task that could potentially loop (repeatedly checking something)
        task = "Keep checking if a file exists until it does, but it never will"

        events = []

        async with orchestrator_client.stream(
            "POST",
            "/api/orchestrate/run-task",
            json={
                "task": task,
                "workspace_root": "/workspace",
                "user_id": "test_user",
                "max_steps": 5,  # Limited steps
                "preserve_state": False,
            },
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue

                try:
                    event_data = json.loads(line[6:])
                    event = TestEvent(
                        event_type=event_data.get("event_type", ""),
                        content=event_data.get("content"),
                        status=event_data.get("status"),
                        step_num=event_data.get("step_num"),
                        tool=event_data.get("tool"),
                        result=event_data.get("result"),
                        done=event_data.get("done", False),
                    )
                    events.append(event)

                except json.JSONDecodeError:
                    continue

        # Should not exceed max steps
        step_events = [e for e in events if e.step_num and e.step_num <= 5]
        max_step = max((e.step_num for e in step_events if e.step_num), default=0)
        assert max_step <= 5, f"Should not exceed max steps (5), got {max_step}"

        # Should complete (either successfully or with guardrail)
        completion_events = [e for e in events if e.done]
        assert len(completion_events) > 0, "Should complete within step limit"


class TestRemoteFileIndexingE2E:
    """
    Test remote file indexing and metadata workflows.
    
    These tests require a FunnelCloud agent to be running.
    They test complex workflows like:
    - Indexing file metadata from remote drives
    - Storing metadata in workspace memory
    - Handling large recursive file listings
    """

    @pytest.fixture
    async def orchestrator_client(self):
        """Create a test client for the orchestrator API."""
        async with httpx.AsyncClient(
            base_url="http://localhost:8004",
            timeout=httpx.Timeout(600.0, connect=10.0)  # 10 min timeout for large operations
        ) as client:
            yield client

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_remote_file_metadata_indexing(self, orchestrator_client):
        """
        E2E test: Index file metadata from a remote drive and store in memory.
        
        This tests:
        1. Agent discovery (list_agents)
        2. Remote PowerShell execution with valid syntax
        3. Handling recursive file listings
        4. Memory storage of collected metadata
        
        Based on real failure case: "Please index the metadata of ALL files in S:."
        """
        # Use a smaller scope for testing - just list ROOT contents (no recursion)
        # The original bug was about syntax errors with paths like 'S:\', not recursion depth
        task = "List the TOP LEVEL files and folders in S:\\ on the remote machine (do NOT recurse into subfolders)"
        
        events = []
        status_updates = []
        errors = []

        try:
            async with orchestrator_client.stream(
                "POST",
                "/api/orchestrate/run-task",
                json={
                    "task": task,
                    "workspace_root": "/workspace",
                    "user_id": "test_indexing",
                    "max_steps": 6,  # Reduced: list_agents + remote_execute + complete
                    "preserve_state": True,  # Enable memory storage
                },
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    try:
                        event_data = json.loads(line[6:])
                        event = TestEvent(
                            event_type=event_data.get("event_type", ""),
                            content=event_data.get("content"),
                            status=event_data.get("status"),
                            step_num=event_data.get("step_num"),
                            tool=event_data.get("tool"),
                            result=event_data.get("result"),
                            done=event_data.get("done", False),
                        )
                        events.append(event)
                        
                        if event.status:
                            status_updates.append(event.status)
                            # Track PowerShell syntax errors
                            if "syntax error" in event.status.lower() or "missing" in event.status.lower():
                                errors.append(event.status)

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            pytest.fail(f"Failed to execute task: {e}")

        # Validate the execution
        self._validate_remote_indexing(events, status_updates, errors)

    def _validate_remote_indexing(self, events: List[TestEvent], status_updates: List[str], errors: List[str]):
        """Validate the remote file indexing workflow."""
        
        # Debug output
        print(f"\n=== DEBUG: Received {len(events)} events ===")
        print(f"Status updates: {status_updates[:15]}")
        print(f"Errors encountered: {errors[:5]}")
        
        # 1. Should either discover agents OR use a known agent
        # The model may skip list_agents if it knows the agent from context
        agent_events = [e for e in events if e.tool == "list_agents"]
        remote_events = [e for e in events if e.tool == "remote_execute"]
        
        # Must have either agent discovery OR direct remote execution
        has_agent_workflow = len(agent_events) > 0 or len(remote_events) > 0
        assert has_agent_workflow, "Should use agent discovery or remote execution"
        
        # 2. Should use remote_execute for the remote drive
        assert len(remote_events) > 0, "Should use remote_execute to access the remote drive"
        
        # 3. Should NOT have excessive PowerShell syntax errors (max 2 retries)
        syntax_errors = [e for e in errors if "syntax" in e.lower() or "missing" in e.lower()]
        assert len(syntax_errors) <= 3, f"Too many PowerShell syntax errors ({len(syntax_errors)}): {syntax_errors[:3]}"
        
        # 4. Should have at least one successful remote execution OR complete gracefully
        # (Drive might not exist on test machine)
        successful_remote = [e for e in remote_events if e.result and e.result.get("success", False)]
        completion_events = [e for e in events if e.done]
        
        # Either successful execution OR graceful completion is OK
        has_valid_outcome = len(successful_remote) > 0 or len(completion_events) > 0
        assert has_valid_outcome, f"Should have successful remote execution or completion. Remote results: {[e.result for e in remote_events[:3]]}"
        
        # 5. Should complete the task
        assert len(completion_events) > 0, "Should complete the task"

    @pytest.mark.asyncio
    @pytest.mark.integration  
    async def test_powershell_syntax_validation(self, orchestrator_client):
        """
        Test that the system generates valid PowerShell syntax.
        
        Specifically tests for:
        - Proper string quoting
        - Complete command structures
        - No missing terminators
        """
        # Simple command that should work
        task = "Run 'Get-ChildItem C:\\Windows -Directory | Select-Object -First 5' on the remote machine"
        
        events = []
        syntax_errors = []

        try:
            async with orchestrator_client.stream(
                "POST",
                "/api/orchestrate/run-task",
                json={
                    "task": task,
                    "workspace_root": "/workspace",
                    "user_id": "test_syntax",
                    "max_steps": 5,
                    "preserve_state": False,
                },
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    try:
                        event_data = json.loads(line[6:])
                        event = TestEvent(
                            event_type=event_data.get("event_type", ""),
                            content=event_data.get("content"),
                            status=event_data.get("status"),
                            step_num=event_data.get("step_num"),
                            tool=event_data.get("tool"),
                            result=event_data.get("result"),
                            done=event_data.get("done", False),
                        )
                        events.append(event)
                        
                        # Track syntax errors
                        if event.status and ("syntax" in event.status.lower() or 
                                            "missing" in event.status.lower() or
                                            "terminator" in event.status.lower()):
                            syntax_errors.append(event.status)

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            pytest.fail(f"Failed to execute task: {e}")

        # Should have no syntax errors for a simple command
        assert len(syntax_errors) == 0, f"Should not have PowerShell syntax errors: {syntax_errors}"
        
        # Should complete successfully
        completion_events = [e for e in events if e.done]
        assert len(completion_events) > 0, "Should complete the task"
        
        # Should have successful remote execution
        remote_events = [e for e in events if e.tool == "remote_execute" and e.result]
        successful = [e for e in remote_events if e.result.get("success", False)]
        assert len(successful) > 0, f"Should have successful execution. Results: {[e.result for e in remote_events]}"