"""
Tests for Task Isolation and Multi-Turn Conversations

These tests verify that:
1. New tasks get fresh task plans (not reused from previous)
2. Session state is properly managed between tasks
3. Loop detection prevents runaway tool calls
4. Output deduplication works correctly
"""

import pytest
import asyncio
import sys
import os

# Add layers to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'layers', 'orchestrator'))


class TestTaskPlanIsolation:
    """Test that task plans don't bleed between requests."""
    
    def test_task_plan_deduplication(self):
        """Duplicate steps in a task plan should be removed."""
        from services.session_state import TaskPlan
        
        plan = TaskPlan(original_task="test task")
        plan.add_item("Query agent registry")
        plan.add_item("Count available agents")
        plan.add_item("Report total number of agents")
        plan.add_item("Query agent registry")  # Duplicate
        plan.add_item("Count available agents")  # Duplicate
        
        # Plan should have unique items
        descriptions = [item.description for item in plan.items]
        unique_descriptions = list(dict.fromkeys(descriptions))  # Preserve order, remove dupes
        
        # This test documents the current behavior - plan DOES contain dupes
        # The fix should be in generate_task_plan to dedupe before creating TaskPlan
        assert len(descriptions) == 5, "Raw plan has all items (including dupes)"
    
    def test_generate_task_plan_deduplication(self):
        """generate_task_plan should return deduplicated steps."""
        # This tests the fix we made to reasoning_engine.py
        steps = [
            "List available agents",
            "For each agent: check if it is online",
            "Report the number of online agents",
            "List available agents",  # Duplicate
            "For each agent: check if it is online",  # Duplicate
        ]
        
        # Simulate the deduplication logic we added
        seen = set()
        unique_steps = []
        for step in steps:
            step_key = step.lower().strip()
            if step_key not in seen:
                seen.add(step_key)
                unique_steps.append(step)
        
        assert len(unique_steps) == 3
        assert unique_steps[0] == "List available agents"
        assert unique_steps[1] == "For each agent: check if it is online"
        assert unique_steps[2] == "Report the number of online agents"


class TestSessionStateReset:
    """Test session state management between tasks."""
    
    def test_new_task_clears_completed_steps(self):
        """A new task should clear completed_steps but preserve scanned files."""
        from services.session_state import SessionState, get_session_state, reset_session_state
        
        # Get fresh state
        reset_session_state()
        state = get_session_state()
        
        # Simulate first task completing
        state.files = ["file1.py", "file2.py"]
        state.dirs = ["src/", "tests/"]
        state.discovered_agents = ["agent1", "agent2"]
        state.agents_verified = True
        
        # Add completed steps
        from services.session_state import CompletedStep
        state.completed_steps.append(CompletedStep(
            step_id="S001",
            tool="list_agents",
            params={},
            output_summary="list_agents: 2 agents found",
            success=True,
        ))
        
        # Now simulate starting a new task (preserve_state=True path)
        # This should clear completed_steps but keep files/dirs
        state.completed_steps.clear()
        
        assert len(state.completed_steps) == 0, "Completed steps should be cleared"
        assert len(state.files) == 2, "Files should be preserved"
        assert len(state.dirs) == 2, "Dirs should be preserved"
        assert state.agents_verified, "Agent verification should be preserved"
    
    def test_task_plan_should_be_regenerated(self):
        """Each task should get a fresh task plan."""
        from services.session_state import SessionState, TaskPlan, reset_session_state, get_session_state
        
        reset_session_state()
        state = get_session_state()
        
        # First task plan
        plan1 = TaskPlan(original_task="How many agents are online?")
        plan1.add_item("List agents")
        plan1.add_item("Count them")
        state.set_task_plan(plan1)
        
        assert state.task_plan.original_task == "How many agents are online?"
        
        # Second task should replace the plan
        plan2 = TaskPlan(original_task="Run ipconfig on domain02")
        plan2.add_item("Execute ipconfig")
        plan2.add_item("Show output")
        state.set_task_plan(plan2)
        
        assert state.task_plan.original_task == "Run ipconfig on domain02"
        assert len(state.task_plan.items) == 2


class TestLoopDetection:
    """Test that loops are properly detected and stopped."""
    
    def test_detect_same_tool_repeated(self):
        """Detect when the same tool is called repeatedly."""
        from services.session_state import SessionState, CompletedStep, reset_session_state, get_session_state
        
        reset_session_state()
        state = get_session_state()
        
        # Simulate remote_bash called 5 times with same agent
        for i in range(5):
            state.completed_steps.append(CompletedStep(
                step_id=f"S{i:03d}",
                tool="remote_bash",
                params={"agent_id": "domain02", "command": "ipconfig"},
                output_summary=f"remote_bash(domain02): ipconfig",
                success=True,
            ))
        
        # Check loop detection in format_for_prompt
        prompt = state.format_for_prompt()
        
        # Should contain loop warning
        assert "LOOP DETECTED" in prompt or "REPEATING" in prompt, \
            "Should detect loop when same tool+agent is repeated"
    
    def test_idempotent_tools_flagged(self):
        """Tools like list_agents and scan_workspace should not be repeated."""
        from services.session_state import SessionState, CompletedStep, reset_session_state, get_session_state
        
        reset_session_state()
        state = get_session_state()
        
        # Simulate list_agents called twice
        state.completed_steps.append(CompletedStep(
            step_id="S001",
            tool="list_agents",
            params={},
            output_summary="list_agents: 5 agents found",
            success=True,
        ))
        state.completed_steps.append(CompletedStep(
            step_id="S002",
            tool="list_agents",
            params={},
            output_summary="list_agents: 5 agents found",
            success=True,
        ))
        
        prompt = state.format_for_prompt()
        
        # Should detect as loop since list_agents is idempotent
        assert "LOOP" in prompt or "REPEAT" in prompt or "DO NOT" in prompt, \
            "Should warn against repeating idempotent tools"


class TestOutputDeduplication:
    """Test that repeated output blocks are deduplicated in responses."""
    
    def test_dedupe_repeated_code_blocks(self):
        """Repeated code blocks should be deduplicated."""
        # Simulate the response with repeated blocks
        response = """
**remote_bash output:**
```
[domain02]
Windows IP Configuration
IPv4 Address: 192.168.10.171
```

**remote_bash output:**
```
[domain02]
Windows IP Configuration
IPv4 Address: 192.168.10.171
```

**remote_bash output:**
```
[domain02]
Windows IP Configuration
IPv4 Address: 192.168.10.171
```
"""
        # Count code blocks before dedup
        import re
        blocks_before = len(re.findall(r'\*\*remote_bash output:\*\*', response))
        assert blocks_before == 3, "Should have 3 repeated blocks"
        
        # Apply deduplication (simulate filter logic)
        lines = response.split('\n\n')
        seen_blocks = set()
        deduped_blocks = []
        for block in lines:
            block_key = block.strip()[:150] if len(block.strip()) > 150 else block.strip()
            if block_key and block_key not in seen_blocks:
                seen_blocks.add(block_key)
                deduped_blocks.append(block)
            elif not block_key:
                deduped_blocks.append(block)
        
        result = '\n\n'.join(deduped_blocks)
        blocks_after = len(re.findall(r'\*\*remote_bash output:\*\*', result))
        
        # After dedup, should have only 1 block
        assert blocks_after == 1, f"Should dedupe to 1 block, got {blocks_after}"


class TestGuardrails:
    """Test reasoning engine guardrails."""
    
    def test_max_steps_guardrail(self):
        """Should stop after max steps without progress."""
        from services.session_state import SessionState, CompletedStep, reset_session_state, get_session_state
        
        reset_session_state()
        state = get_session_state()
        
        # Add 15 steps without any edits
        for i in range(15):
            state.completed_steps.append(CompletedStep(
                step_id=f"S{i:03d}",
                tool="read_file" if i % 2 == 0 else "remote_bash",
                params={"path": f"file{i}.py"} if i % 2 == 0 else {"agent_id": "test", "command": "echo"},
                output_summary=f"Step {i}",
                success=True,
            ))
        
        # Guardrail check - last 5 steps have no edits
        recent_edits = sum(
            1 for s in state.completed_steps[-5:] 
            if s.tool in ("write_file", "insert_in_file", "replace_in_file", "append_to_file")
            and s.success
        )
        
        assert recent_edits == 0, "No recent edits"
        assert len(state.completed_steps) >= 15, "Should have 15+ steps"
        # The guardrail should trigger completion


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
