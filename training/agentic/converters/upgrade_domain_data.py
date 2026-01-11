#!/usr/bin/env python3
"""
Domain Data Upgrader

Converts existing instruction-response format to enhanced formats:
1. Add reasoning traces to suitable examples
2. Convert applicable examples to trajectory format
3. Enhance with CoT (chain-of-thought) prompting

Usage:
    python upgrade_domain_data.py --input ../../data --output ../data/domain/
"""

import json
import argparse
import random
from pathlib import Path
from typing import Dict, List, Generator

# Categories that benefit from trajectory conversion
TRAJECTORY_CANDIDATES = {
    "git_version_control",
    "docker_containerization", 
    "linux_admin",
    "windows_admin",
    "devops_cicd",
    "testing_debugging",
}

# Categories that benefit from reasoning enhancement
REASONING_CANDIDATES = {
    "architecture",
    "architecture_qa",
    "security",
    "code_review",
    "refactoring",
    "project_planning",
    "task_planning",
}


def add_reasoning_prefix(instruction: str, response: str) -> str:
    """Add chain-of-thought reasoning to a response."""
    
    # Detect if response is already structured
    if response.startswith("Let me") or "**" in response[:100]:
        return response
    
    # Add reasoning based on instruction type
    reasoning_templates = [
        "Let me think through this step by step.\n\n",
        "I'll break this down into the key considerations.\n\n",
        "Let me analyze this carefully.\n\n",
        "Here's my reasoning:\n\n",
    ]
    
    prefix = random.choice(reasoning_templates)
    return prefix + response


def convert_to_trajectory_format(example: Dict) -> Dict:
    """Convert a command-based example to trajectory format."""
    
    instruction = example.get("instruction", "")
    response = example.get("response", "")
    
    # Try to detect command-based responses
    if '"action": "execute_command"' in response or '"command":' in response:
        try:
            # Parse the command from response
            import re
            cmd_match = re.search(r'"command":\s*"([^"]+)"', response)
            if cmd_match:
                command = cmd_match.group(1)
                
                return {
                    "task": instruction,
                    "trajectory": [
                        {
                            "step_type": "thought",
                            "content": f"I need to {instruction.lower()}. The appropriate command for this is:"
                        },
                        {
                            "step_type": "action",
                            "tool": "run_in_terminal",
                            "tool_input": {
                                "command": command,
                                "explanation": instruction
                            }
                        },
                        {
                            "step_type": "observation",
                            "content": "Command executed successfully"
                        },
                        {
                            "step_type": "final_answer",
                            "content": f"Done. I ran `{command}` to {instruction.lower()}."
                        }
                    ],
                    "metadata": {
                        "category": "converted",
                        "difficulty": "easy",
                        "tools_used": ["run_in_terminal"],
                        "num_steps": 4,
                        "success": True
                    }
                }
        except:
            pass
    
    # Return enhanced but not trajectory format
    return None


def upgrade_example(example: Dict, domain: str) -> Dict:
    """Upgrade a single example based on its domain."""
    
    instruction = example.get("instruction", "")
    response = example.get("response", "")
    system = example.get("system", "You are AJ, a helpful AI assistant.")
    
    # Try trajectory conversion for applicable domains
    if domain in TRAJECTORY_CANDIDATES:
        trajectory = convert_to_trajectory_format(example)
        if trajectory:
            return {"format": "trajectory", "data": trajectory}
    
    # Add reasoning for applicable domains
    if domain in REASONING_CANDIDATES:
        enhanced_response = add_reasoning_prefix(instruction, response)
        return {
            "format": "enhanced",
            "data": {
                "system": system,
                "instruction": instruction,
                "response": enhanced_response
            }
        }
    
    # Return original format
    return {
        "format": "original",
        "data": example
    }


def process_domain_file(input_path: Path, output_dir: Path) -> Dict[str, int]:
    """Process a single domain file."""
    
    domain = input_path.stem
    stats = {"original": 0, "enhanced": 0, "trajectory": 0}
    
    examples = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    examples.append(json.loads(line))
                except:
                    continue
    
    # Separate outputs by format
    trajectories = []
    enhanced = []
    
    for example in examples:
        result = upgrade_example(example, domain)
        stats[result["format"]] += 1
        
        if result["format"] == "trajectory":
            trajectories.append(result["data"])
        else:
            enhanced.append(result["data"])
    
    # Write outputs
    if enhanced:
        output_path = output_dir / f"{domain}.jsonl"
        with open(output_path, 'w', encoding='utf-8') as f:
            for ex in enhanced:
                f.write(json.dumps(ex, ensure_ascii=False) + '\n')
    
    if trajectories:
        traj_dir = output_dir.parent / "trajectories"
        traj_dir.mkdir(exist_ok=True)
        output_path = traj_dir / f"{domain}_converted.jsonl"
        with open(output_path, 'w', encoding='utf-8') as f:
            for ex in trajectories:
                f.write(json.dumps(ex, ensure_ascii=False) + '\n')
    
    return stats


def main():
    parser = argparse.ArgumentParser(description="Upgrade domain training data")
    parser.add_argument("--input", "-i", type=str, default="../../data")
    parser.add_argument("--output", "-o", type=str, default="../data/domain/")
    parser.add_argument("--domain", "-d", type=str, help="Process single domain")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Upgrading domain training data...")
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    print()
    
    total_stats = {"original": 0, "enhanced": 0, "trajectory": 0}
    
    files = list(input_dir.glob("*.jsonl"))
    if args.domain:
        files = [f for f in files if f.stem == args.domain]
    
    # Skip meta files
    files = [f for f in files if f.stem not in ["all_training_data", "dataset_stats"]]
    
    for filepath in sorted(files):
        stats = process_domain_file(filepath, output_dir)
        for k, v in stats.items():
            total_stats[k] += v
        
        total = sum(stats.values())
        print(f"  {filepath.stem}: {total} examples "
              f"({stats['trajectory']} trajectory, {stats['enhanced']} enhanced)")
    
    print()
    print(f"Total: {sum(total_stats.values())} examples")
    print(f"  Original format: {total_stats['original']}")
    print(f"  Enhanced (CoT): {total_stats['enhanced']}")
    print(f"  Trajectory format: {total_stats['trajectory']}")


if __name__ == "__main__":
    main()
