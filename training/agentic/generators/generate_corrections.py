#!/usr/bin/env python3
"""
Correction Example Generator

Creates training pairs that teach the model to AVOID common mistakes.
These are "negative → positive" examples showing:
1. What the model did wrong
2. What it should have done instead

This is CRITICAL for fine-tuning - the model needs to see both:
- Good examples to imitate
- Bad patterns to avoid (with corrections)

Usage:
    python generate_corrections.py --from-chat-exports *.json --output corrections.jsonl
    python generate_corrections.py --known-issues
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict

# =============================================================================
# KNOWN BAD PATTERNS → CORRECTIONS
# =============================================================================

# These are documented mistakes we've seen and their corrections
KNOWN_CORRECTIONS = [
    {
        "category": "wrong_output_format",
        "bad_pattern": {
            "user": "run `hostname` on all",
            "assistant_bad": '{"action": "execute_command", "command": "for agent in $(list_agents | awk \'{print $2}\'); do echo \\"---\\"; echo \\"$agent:\\"; run_command -a $agent hostname; done", "explanation": "Executes hostname on all available agents"}'
        },
        "correction": {
            "user": "run `hostname` on all",
            "assistant_good": '{"tool": "remote_bash_all", "params": {"command": "hostname"}, "reasoning": "User wants to run hostname on all discovered agents"}'
        },
        "explanation": "Model used 'action' key instead of 'tool' key, and hallucinated shell constructs instead of using remote_bash_all"
    },
    {
        "category": "tool_none_error",
        "bad_pattern": {
            "context": "Agents already discovered in session",
            "user": "How many agents are online?",
            "assistant_bad": '{"tool": "none", "params": {"reason": "Agents already discovered: ians-r16, domain01"}, "reasoning": "Skipped redundant call"}'
        },
        "correction": {
            "context": "Agents already discovered in session",
            "user": "How many agents are online?",
            "assistant_good": 'Based on the agents discovered earlier, there are 2 agents online: `ians-r16` and `domain01`. Want me to refresh the list?'
        },
        "explanation": "Model tried to use tool='none' which doesn't exist. Should provide direct answer with cached info."
    },
    {
        "category": "lost_context",
        "bad_pattern": {
            "context": "Previous turn successfully ran list_agents and found 5 agents",
            "user": "Check CPU on all of them",
            "assistant_bad": '{"action": "direct_answer", "answer": "No agents were discovered in this session. I cannot run commands without connected agents."}'
        },
        "correction": {
            "context": "Previous turn successfully ran list_agents and found 5 agents",
            "user": "Check CPU on all of them",
            "assistant_good": '{"tool": "remote_bash_all", "params": {"command": "Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 Name,CPU"}, "reasoning": "Using previously discovered agents to check CPU usage on all 5 machines"}'
        },
        "explanation": "Model forgot the agents discovered in the same session. Should maintain context."
    },
    {
        "category": "hallucinated_commands",
        "bad_pattern": {
            "user": "list files on webserver",
            "assistant_bad": '{"tool": "bash", "params": {"command": "run_on_remote webserver ls -la"}}'
        },
        "correction": {
            "user": "list files on webserver",
            "assistant_good": '{"tool": "remote_bash", "params": {"agent_id": "webserver", "command": "ls -la"}, "reasoning": "Using remote_bash to execute ls on the webserver agent"}'
        },
        "explanation": "Model hallucinated 'run_on_remote' command. Should use remote_bash tool directly."
    },
    {
        "category": "wrong_count",
        "bad_pattern": {
            "context": "list_agents returned: ians-r16, domain01, r730xd, exchange01",
            "user": "How many agents are there?",
            "assistant_bad": "1 agent is currently online."
        },
        "correction": {
            "context": "list_agents returned: ians-r16, domain01, r730xd, exchange01", 
            "user": "How many agents are there?",
            "assistant_good": "4 agents are currently online: `ians-r16`, `domain01`, `r730xd`, and `exchange01`."
        },
        "explanation": "Model miscounted. Must accurately count items in tool output."
    },
    {
        "category": "code_block_instead_of_action",
        "bad_pattern": {
            "user": "restart nginx on prod01",
            "assistant_bad": "Here's how you can restart nginx:\n```bash\nsudo systemctl restart nginx\n```\nRun this on prod01."
        },
        "correction": {
            "user": "restart nginx on prod01",
            "assistant_good": '{"tool": "remote_bash", "params": {"agent_id": "prod01", "command": "sudo systemctl restart nginx"}, "reasoning": "Restarting nginx service on prod01 as requested"}'
        },
        "explanation": "Model provided instructions instead of taking action. Should execute when user clearly requests action."
    },
    {
        "category": "missing_list_agents",
        "bad_pattern": {
            "context": "Start of session, no agents discovered yet",
            "user": "Check disk space on all servers",
            "assistant_bad": '{"tool": "remote_bash_all", "params": {"command": "df -h"}}'
        },
        "correction": {
            "context": "Start of session, no agents discovered yet",
            "user": "Check disk space on all servers",
            "assistant_good": '{"tool": "list_agents", "params": {}, "reasoning": "Need to discover available agents first before running remote commands"}'
        },
        "explanation": "Model skipped agent discovery. Must call list_agents before remote operations."
    },
    {
        "category": "plan_as_dict",
        "bad_pattern": {
            "user": "check the hyper-v host",
            "assistant_bad": "> 📋 **Task Plan:**\n> • {'step': 1, 'action': 'Verify r730xd is available'}\n> • {'step': 2, 'action': 'Query VM list'}"
        },
        "correction": {
            "user": "check the hyper-v host",
            "assistant_good": "> 📋 **Task Plan:**\n> • Verify r730xd (Hyper-V host) is available\n> • Query list of running VMs\n> • Report VM status and resource usage"
        },
        "explanation": "Task plan should be clean markdown bullets, not Python dicts."
    },
]


def generate_training_pair(correction: Dict) -> Dict:
    """
    Generate a training example that teaches the correction.
    
    Strategy: Show the bad pattern in a "what not to do" system context,
    then show the correct response.
    """
    
    bad = correction["bad_pattern"]
    good = correction["correction"]
    
    # Build system message that includes the lesson
    system = f"""You are AJ, an AI assistant with FunnelCloud agent system.

IMPORTANT LESSON - {correction['category'].upper()}:
{correction['explanation']}

WRONG (do NOT do this):
{bad.get('assistant_bad', '')}

CORRECT approach:
{good.get('assistant_good', '')}

Always use the correct tool format: {{"tool": "name", "params": {{}}, "reasoning": "why"}}
Available tools: bash, remote_bash, remote_bash_all, list_agents, think, complete"""

    messages = []
    
    # Add context if present
    if good.get("context"):
        messages.append({
            "role": "system",
            "content": f"{system}\n\nCURRENT CONTEXT: {good['context']}"
        })
    else:
        messages.append({"role": "system", "content": system})
    
    messages.append({"role": "user", "content": good["user"]})
    messages.append({"role": "assistant", "content": good["assistant_good"]})
    
    return {
        "messages": messages,
        "metadata": {
            "source": "correction",
            "category": correction["category"],
            "teaches": correction["explanation"],
        }
    }


def generate_contrastive_pair(correction: Dict) -> Dict:
    """
    Generate a contrastive training example (DPO-style).
    
    Shows both the bad and good response for the same input,
    which is useful for preference learning.
    """
    bad = correction["bad_pattern"]
    good = correction["correction"]
    
    return {
        "prompt": good["user"],
        "context": good.get("context", ""),
        "chosen": good["assistant_good"],
        "rejected": bad["assistant_bad"],
        "category": correction["category"],
        "explanation": correction["explanation"],
    }


def main():
    parser = argparse.ArgumentParser(description="Generate correction training examples")
    parser.add_argument("--output", type=Path, default=Path("corrections.jsonl"))
    parser.add_argument("--output-dpo", type=Path, default=Path("corrections_dpo.jsonl"))
    parser.add_argument("--known-issues", action="store_true", help="Generate from known issues")
    parser.add_argument("--multiply", type=int, default=3, help="Generate N variations of each correction")
    
    args = parser.parse_args()
    
    # Generate from known corrections
    training_examples = []
    dpo_examples = []
    
    for correction in KNOWN_CORRECTIONS:
        # Standard training format
        example = generate_training_pair(correction)
        training_examples.append(example)
        
        # DPO/preference format
        dpo = generate_contrastive_pair(correction)
        dpo_examples.append(dpo)
    
    # Write training examples
    with open(args.output, "w") as f:
        for ex in training_examples:
            f.write(json.dumps(ex) + "\n")
    
    print(f"✅ Generated {len(training_examples)} correction examples → {args.output}")
    
    # Write DPO examples
    with open(args.output_dpo, "w") as f:
        for ex in dpo_examples:
            f.write(json.dumps(ex) + "\n")
    
    print(f"✅ Generated {len(dpo_examples)} DPO preference pairs → {args.output_dpo}")
    
    # Summary by category
    print("\n📊 Corrections by category:")
    from collections import Counter
    categories = Counter(c["category"] for c in KNOWN_CORRECTIONS)
    for cat, count in categories.most_common():
        print(f"  • {cat}: {count}")


if __name__ == "__main__":
    main()
