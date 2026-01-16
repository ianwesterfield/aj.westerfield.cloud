#!/usr/bin/env python3
"""
Agentic Trajectory Generator

Uses a frontier model (Claude/GPT-4) to solve coding tasks with tool use,
capturing full thought → action → observation traces for training.

Can also load and augment open datasets from HuggingFace (Toucan-1.5M, etc.)

Requirements:
    pip install anthropic openai httpx datasets

Usage:
    python generate_trajectories.py --count 1000 --category coding --output ../data/trajectories/
    python generate_trajectories.py --task-file tasks.txt --verify
    python generate_trajectories.py --load-dataset toucan --subset Kimi-K2 --sample 500
"""

import json
import argparse
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Generator, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from datasets import load_dataset
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# Tool definitions matching VS Code / MCP tools
TOOLS = [
    {
        "name": "read_file",
        "description": "Read contents of a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "filePath": {"type": "string"},
                "startLine": {"type": "integer"},
                "endLine": {"type": "integer"}
            },
            "required": ["filePath", "startLine", "endLine"]
        }
    },
    {
        "name": "replace_string_in_file",
        "description": "Replace a string in a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "filePath": {"type": "string"},
                "oldString": {"type": "string"},
                "newString": {"type": "string"}
            },
            "required": ["filePath", "oldString", "newString"]
        }
    },
    {
        "name": "create_file",
        "description": "Create a new file",
        "input_schema": {
            "type": "object",
            "properties": {
                "filePath": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["filePath", "content"]
        }
    },
    {
        "name": "run_in_terminal",
        "description": "Run a command in the terminal",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "explanation": {"type": "string"}
            },
            "required": ["command", "explanation"]
        }
    },
    {
        "name": "grep_search",
        "description": "Search for text patterns in files",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "isRegexp": {"type": "boolean"},
                "includePattern": {"type": "string"}
            },
            "required": ["query", "isRegexp"]
        }
    },
    {
        "name": "semantic_search",
        "description": "Semantic search across codebase",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "list_dir",
        "description": "List directory contents",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            },
            "required": ["path"]
        }
    }
]


# Task templates by category
TASK_TEMPLATES = {
    "debugging": [
        "Fix the {error_type} in {file_path}",
        "Debug why {component} is {symptom}",
        "Investigate the failing test in {test_file}",
        "Find and fix the memory leak in {module}",
        "Resolve the race condition in {async_component}",
    ],
    "coding": [
        "Add {feature} to the {component}",
        "Implement {pattern} for {use_case}",
        "Create a {thing} that {behavior}",
        "Refactor {module} to use {approach}",
        "Add validation for {input_type} in {endpoint}",
    ],
    "refactoring": [
        "Extract {thing} from {location} into a separate {target}",
        "Convert {old_pattern} to {new_pattern} in {scope}",
        "Remove code duplication between {file1} and {file2}",
        "Simplify the {complex_thing} in {location}",
        "Add TypeScript types to {javascript_file}",
    ],
    "devops": [
        "Set up {ci_tool} pipeline for {project_type}",
        "Dockerize the {application}",
        "Configure {monitoring_tool} for {service}",
        "Add {deployment_type} deployment to {environment}",
        "Fix the failing {pipeline_stage} in CI",
    ],
    "testing": [
        "Add unit tests for {module}",
        "Create integration tests for {api_endpoint}",
        "Add E2E tests for {user_flow}",
        "Increase test coverage for {component}",
        "Fix the flaky test in {test_file}",
    ],
}

# Fill-in values for templates
TEMPLATE_VALUES = {
    "error_type": ["TypeError", "ReferenceError", "null pointer exception", "CORS error", "timeout error"],
    "file_path": ["src/services/userService.ts", "src/middleware/auth.ts", "src/routes/api.ts", "src/utils/helpers.ts"],
    "component": ["the authentication flow", "the payment processor", "the search feature", "the notification system"],
    "symptom": ["returning null unexpectedly", "timing out", "throwing errors intermittently", "consuming too much memory"],
    "feature": ["pagination", "caching", "rate limiting", "input validation", "error handling"],
    "pattern": ["repository pattern", "factory pattern", "observer pattern", "strategy pattern"],
    "use_case": ["user management", "file uploads", "real-time updates", "background jobs"],
    "thing": ["REST endpoint", "middleware", "utility function", "custom hook", "service class"],
    "behavior": ["handles authentication", "validates input", "transforms data", "manages state"],
}


@dataclass
class TrajectoryStep:
    step_type: str  # thought, action, observation, final_answer
    content: Optional[str] = None
    tool: Optional[str] = None
    tool_input: Optional[Dict] = None


@dataclass
class Trajectory:
    task: str
    context: Optional[Dict]
    steps: List[TrajectoryStep]
    metadata: Dict


class SimulatedEnvironment:
    """Simulates tool responses for training data generation."""
    
    def __init__(self, scenario: Dict):
        self.scenario = scenario
        self.files = scenario.get("files", {})
        self.modified_files = {}
    
    def execute_tool(self, tool_name: str, tool_input: Dict) -> str:
        """Simulate tool execution and return plausible response."""
        
        if tool_name == "read_file":
            path = tool_input.get("filePath", "")
            if path in self.files:
                return self.files[path]
            return f"// File contents for {path}\n// ... implementation ..."
        
        elif tool_name == "replace_string_in_file":
            return "File edited successfully"
        
        elif tool_name == "create_file":
            return "File created successfully"
        
        elif tool_name == "run_in_terminal":
            cmd = tool_input.get("command", "")
            if "test" in cmd:
                return "All tests passed"
            elif "build" in cmd:
                return "Build successful"
            elif "docker" in cmd:
                return "Container started"
            return "Command executed successfully"
        
        elif tool_name == "grep_search":
            query = tool_input.get("query", "")
            return f"Found 3 matches for '{query}':\n  src/file1.ts:15\n  src/file2.ts:42\n  src/file3.ts:8"
        
        elif tool_name == "list_dir":
            return "file1.ts\nfile2.ts\nutils/\ntests/"
        
        return "Tool executed"


def generate_task(category: str) -> str:
    """Generate a random task from templates."""
    templates = TASK_TEMPLATES.get(category, TASK_TEMPLATES["coding"])
    template = random.choice(templates)
    
    # Fill in placeholders
    import re
    placeholders = re.findall(r'\{(\w+)\}', template)
    
    task = template
    for ph in placeholders:
        if ph in TEMPLATE_VALUES:
            task = task.replace(f"{{{ph}}}", random.choice(TEMPLATE_VALUES[ph]))
        else:
            task = task.replace(f"{{{ph}}}", ph.replace("_", " "))
    
    return task


def generate_with_claude(task: str, client: "anthropic.Anthropic") -> Optional[Trajectory]:
    """Use Claude to generate a trajectory with real tool use."""
    
    system_prompt = """You are an expert AI coding assistant. Solve the given task step by step.

For each step:
1. Think about what you need to do next (share your reasoning)
2. Use a tool to take action
3. Observe the result
4. Repeat until done

Be thorough but efficient. Use appropriate tools and show your reasoning."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            tools=TOOLS,
            messages=[{"role": "user", "content": f"Task: {task}"}]
        )
        
        # Parse response into trajectory steps
        steps = []
        for block in response.content:
            if block.type == "text":
                steps.append(TrajectoryStep(step_type="thought", content=block.text))
            elif block.type == "tool_use":
                steps.append(TrajectoryStep(
                    step_type="action",
                    tool=block.name,
                    tool_input=block.input
                ))
        
        # Note: In production, you'd continue the conversation with tool results
        # This is simplified for the sketch
        
        return Trajectory(
            task=task,
            context=None,
            steps=steps,
            metadata={
                "category": "generated",
                "difficulty": "medium",
                "tools_used": list(set(s.tool for s in steps if s.tool)),
                "num_steps": len(steps),
                "success": True,
                "verification_method": "manual_review"
            }
        )
    except Exception as e:
        print(f"  Error generating trajectory: {e}")
        return None


def generate_shutdown_trajectory_with_claude(prompt: Dict, client: "anthropic.Anthropic") -> Optional[Trajectory]:
    """Generate trajectory for shutdown/restart target selection using Claude.
    
    These are special prompts that involve agent discovery, disambiguation,
    and confirmation patterns for destructive operations.
    """
    
    system_prompt = f"""You are AJ, an agentic AI assistant with the FunnelCloud system.

CRITICAL SAFETY RULES:
1. For ANY shutdown/restart operation, ALWAYS:
   - Discover available agents (list_agents)
   - Identify the target machine clearly
   - If ambiguous, ask clarifying questions
   - Get explicit user confirmation before executing
   - Show impact on current running tasks

2. Destructive operations include: shutdown, restart, delete, format
3. If target is ambiguous or unclear, BLOCK execution and ask for clarification
4. Warn if target is the user's own machine or running critical services

CONTEXT:
{prompt.get('system_instruction', '')}

Available agents in this scenario:
{json.dumps(prompt.get('context', {}), indent=2)}

Expected guardrail: {prompt.get('guardrail_type', 'none')}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            tools=TOOLS,
            messages=[{"role": "user", "content": f"Task: {prompt['user_request']}"}]
        )
        
        # Parse response into trajectory steps
        steps = []
        for block in response.content:
            if block.type == "text":
                steps.append(TrajectoryStep(step_type="thought", content=block.text))
            elif block.type == "tool_use":
                steps.append(TrajectoryStep(
                    step_type="action",
                    tool=block.name,
                    tool_input=block.input
                ))
        
        if not steps:
            steps.append(TrajectoryStep(
                step_type="final_answer",
                content="Unable to generate valid trajectory"
            ))
        
        return Trajectory(
            task=prompt['user_request'],
            context=prompt.get('context'),
            steps=steps,
            metadata={
                "category": "shutdown_target_selection",
                "subcategory": prompt.get('category'),
                "difficulty": prompt.get('difficulty', 'medium'),
                "guardrail_type": prompt.get('guardrail_type'),
                "tools_used": list(set(s.tool for s in steps if s.tool)),
                "num_steps": len(steps),
                "success": True,
                "verification_method": "manual_review",
                "prompt_id": prompt.get('id'),
                "expected_outcome": prompt.get('expected_outcome')
            }
        )
    except Exception as e:
        print(f"  Error generating shutdown trajectory: {e}")
        return None
        return None


def generate_synthetic_trajectory(task: str, category: str) -> Trajectory:
    """Generate a synthetic trajectory using templates (no API calls)."""
    
    # Create a plausible multi-step trajectory
    steps = [
        TrajectoryStep(
            step_type="thought",
            content=f"I need to understand the current state before making changes. Let me explore the relevant files."
        ),
        TrajectoryStep(
            step_type="action",
            tool="grep_search",
            tool_input={"query": task.split()[-1], "isRegexp": False}
        ),
        TrajectoryStep(
            step_type="observation",
            content="Found relevant code in src/services/main.ts and src/utils/helpers.ts"
        ),
        TrajectoryStep(
            step_type="thought",
            content="Now I'll read the main file to understand the implementation."
        ),
        TrajectoryStep(
            step_type="action",
            tool="read_file",
            tool_input={"filePath": "src/services/main.ts", "startLine": 1, "endLine": 50}
        ),
        TrajectoryStep(
            step_type="observation",
            content="// File contents showing the relevant code..."
        ),
        TrajectoryStep(
            step_type="thought",
            content=f"I see the issue. I'll make the necessary changes to accomplish: {task}"
        ),
        TrajectoryStep(
            step_type="action",
            tool="replace_string_in_file",
            tool_input={
                "filePath": "src/services/main.ts",
                "oldString": "// original code",
                "newString": "// fixed code"
            }
        ),
        TrajectoryStep(
            step_type="observation",
            content="File edited successfully"
        ),
        TrajectoryStep(
            step_type="thought",
            content="Let me verify the changes work correctly by running tests."
        ),
        TrajectoryStep(
            step_type="action",
            tool="run_in_terminal",
            tool_input={"command": "npm test", "explanation": "Run tests to verify changes"}
        ),
        TrajectoryStep(
            step_type="observation",
            content="All tests passed (15 passed, 0 failed)"
        ),
        TrajectoryStep(
            step_type="final_answer",
            content=f"Successfully completed: {task}\n\nChanges made:\n1. Identified the relevant code\n2. Made the necessary modifications\n3. Verified with tests\n\nAll tests pass."
        )
    ]
    
    tools_used = list(set(s.tool for s in steps if s.tool))
    
    return Trajectory(
        task=task,
        context=None,
        steps=steps,
        metadata={
            "category": category,
            "difficulty": random.choice(["easy", "medium", "hard"]),
            "tools_used": tools_used,
            "num_steps": len(steps),
            "success": True,
            "verification_method": "tests_pass"
        }
    )


def trajectory_to_dict(traj: Trajectory) -> Dict:
    """Convert trajectory to serializable dict."""
    return {
        "task": traj.task,
        "context": traj.context,
        "trajectory": [
            {k: v for k, v in asdict(step).items() if v is not None}
            for step in traj.steps
        ],
        "metadata": traj.metadata
    }


def load_toucan_dataset(subset: str = "Kimi-K2", sample_size: Optional[int] = None) -> Generator[Dict, None, None]:
    """Load Toucan-1.5M dataset from HuggingFace and convert to trajectory format."""
    if not DATASETS_AVAILABLE:
        print("Error: datasets package required for open dataset loading")
        print("  pip install datasets")
        return
    
    try:
        print(f"Loading Toucan-1.5M ({subset})...")
        dataset = load_dataset("Agent-Ark/Toucan-1.5M", subset, split="train")
        
        if sample_size:
            dataset = dataset.shuffle(seed=42).select(range(min(sample_size, len(dataset))))
            print(f"Sampling {sample_size} examples")
        else:
            print(f"Loaded {len(dataset)} examples")
        
        for example in dataset:
            # Convert Toucan format to our Trajectory format
            trajectory_dict = {
                "task": example.get("question", ""),
                "context": {"source": "Toucan-1.5M", "subset": subset},
                "trajectory": [
                    {
                        "step_type": "chat_messages",
                        "content": example.get("messages", [])
                    }
                ],
                "metadata": {
                    "category": "open_dataset",
                    "source": "Toucan-1.5M",
                    "source_subset": subset,
                    "tools_used": example.get("target_tools", []),
                    "difficulty": "medium",
                    "uuid": example.get("uuid"),
                    "subset_type": example.get("subset"),  # single-turn-original, multi-turn, etc.
                    "question_quality": example.get("question_quality_assessment"),
                    "response_quality": example.get("response_quality_assessment"),
                    "success": True
                }
            }
            yield trajectory_dict
    except Exception as e:
        print(f"Error loading Toucan dataset: {e}")
        return


def main():
    parser = argparse.ArgumentParser(description="Generate agentic trajectories")
    parser.add_argument("--count", "-n", type=int, default=100)
    parser.add_argument("--category", "-c", type=str, default="coding",
                        choices=list(TASK_TEMPLATES.keys()) + ["shutdown"])
    parser.add_argument("--output", "-o", type=str, default="../data/trajectories/")
    parser.add_argument("--use-claude", action="store_true",
                        help="Use Claude API for generation (requires ANTHROPIC_API_KEY)")
    parser.add_argument("--task-file", type=str, help="File with custom tasks (one per line)")
    parser.add_argument("--load-dataset", choices=["toucan"], 
                        help="Load from open dataset instead of generating")
    parser.add_argument("--dataset-subset", type=str, default="Kimi-K2",
                        help="Dataset subset (for Toucan: Kimi-K2, Qwen3-32B, GPT-OSS-120B)")
    parser.add_argument("--sample", type=int, default=None,
                        help="Sample size from dataset")
    parser.add_argument("--seed", type=int, default=42)
    
    args = parser.parse_args()
    random.seed(args.seed)
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load custom tasks if provided
    custom_tasks = []
    if args.task_file:
        with open(args.task_file) as f:
            custom_tasks = [line.strip() for line in f if line.strip()]
    
    # Load shutdown prompts if category is shutdown
    shutdown_prompts = []
    if args.category == "shutdown":
        try:
            from shutdown_prompts import SHUTDOWN_PROMPTS
            shutdown_prompts = SHUTDOWN_PROMPTS
            # Override count if not explicitly set
            if args.count == 100:  # default value
                args.count = len(SHUTDOWN_PROMPTS)
        except ImportError:
            print("Error: shutdown_prompts module not found")
            return
    
    # Handle open dataset loading
    if args.load_dataset:
        if args.load_dataset == "toucan":
            output_file = output_dir / f"toucan_{args.dataset_subset}_trajectories.jsonl"
            generated = 0
            
            print(f"Loading Toucan-1.5M ({args.dataset_subset})...")
            if args.sample:
                print(f"Sampling {args.sample} examples")
            print(f"Output: {output_file}")
            print()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for i, trajectory in enumerate(load_toucan_dataset(args.dataset_subset, args.sample)):
                    f.write(json.dumps(trajectory, ensure_ascii=False) + '\n')
                    generated += 1
                    if (i + 1) % 100 == 0:
                        print(f"  Saved {i + 1}...")
            
            print(f"\n✅ Loaded and saved {generated} trajectories from Toucan-1.5M")
            print(f"   File: {output_file}")
        return
    
    # Initialize API client if using Claude
    claude_client = None
    if args.use_claude:
        if not ANTHROPIC_AVAILABLE:
            print("Error: anthropic package not installed")
            return
        import os
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY not set")
            return
        claude_client = anthropic.Anthropic(api_key=api_key)
    
    print(f"Generating {args.count} trajectories for category: {args.category}")
    print(f"Output: {output_dir}")
    print(f"Using Claude API: {args.use_claude}")
    print()
    
    output_file = output_dir / f"{args.category}_trajectories.jsonl"
    generated = 0
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for i in range(args.count):
            # Get task/prompt
            if args.category == "shutdown":
                if i < len(shutdown_prompts):
                    prompt = shutdown_prompts[i]
                else:
                    break
                # For shutdown, always use Claude if available
                if claude_client:
                    trajectory = generate_shutdown_trajectory_with_claude(prompt, claude_client)
                else:
                    print("  Warning: Shutdown trajectories require --use-claude")
                    continue
            else:
                if custom_tasks:
                    task = custom_tasks[i % len(custom_tasks)]
                else:
                    task = generate_task(args.category)
                
                # Generate trajectory
                if claude_client:
                    trajectory = generate_with_claude(task, claude_client)
                else:
                    trajectory = generate_synthetic_trajectory(task, args.category)
            
            if trajectory:
                f.write(json.dumps(trajectory_to_dict(trajectory), ensure_ascii=False) + '\n')
                generated += 1
                print(f"  [{i+1}/{args.count}] {trajectory.task[:60]}...")
            
            if (i + 1) % 5 == 0:
                print(f"  Progress: {generated} generated so far...")
    
    print(f"\n✅ Generated {generated} trajectories")
    print(f"   Saved to: {output_file}")


if __name__ == "__main__":
    main()
