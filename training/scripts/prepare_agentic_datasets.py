#!/usr/bin/env python3
"""
Download and prepare agentic/tool-use datasets for training.

This script downloads publicly available datasets with high-quality
agentic traces, function calling, and tool-use examples:

1. Salesforce xLAM Function Calling (60K) - High quality tool use
2. THUDM AgentInstruct (1.8M) - Diverse agent traces
3. NousResearch Hermes Function Calling (12K) - Function calling format

These datasets supplement local AJ training data to create a capable
agentic assistant.
"""

import os
import json
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"

# Output files
XLAM_OUTPUT = DATA_DIR / "xlam_function_calling.jsonl"
AGENT_INSTRUCT_OUTPUT = DATA_DIR / "agent_instruct.jsonl"
STATS_FILE = DATA_DIR / "agentic_dataset_stats.json"

# Dataset configurations
# Note: Some datasets are gated - we use publicly available alternatives
DATASETS = {
    "gorilla": {
        "name": "gorilla-llm/Berkeley-Function-Calling-Leaderboard",
        "output": XLAM_OUTPUT,  # Reuse the xlam output name
        "target_examples": 20000,
        "description": "Berkeley function calling benchmark data",
    },
    "agent_instruct": {
        "name": "THUDM/AgentInstruct",
        "output": AGENT_INSTRUCT_OUTPUT,
        "target_examples": 30000,
        "description": "Diverse agent instruction traces from Tsinghua",
        "splits": ["os", "db", "alfworld", "webshop", "kg", "mind2web"],
    },
}

# Default system prompt for agentic tasks
DEFAULT_SYSTEM = """You are AJ, an expert AI assistant specialized in tool use and task execution. You can analyze problems, select appropriate tools, and execute multi-step plans to accomplish user goals. Provide clear reasoning for your actions."""

TOOL_SYSTEM = """You are AJ, an expert AI assistant with access to various tools and functions. When a task requires using tools, analyze the request, select the appropriate tool, and provide the function call in the correct format. Always explain your reasoning."""


@dataclass
class DatasetStats:
    """Track dataset statistics."""
    total_downloaded: int = 0
    total_converted: int = 0
    by_source: Dict[str, int] = field(default_factory=dict)
    by_category: Dict[str, int] = field(default_factory=dict)


def download_xlam_dataset(max_examples: int = 60000, target: int = 20000) -> bool:
    """
    Download function calling datasets.
    
    Primary: glaiveai/glaive-function-calling-v2 (ungated, 113K examples)
    Fallback: NousResearch/hermes-function-calling-v1
    """
    try:
        from datasets import load_dataset
    except ImportError:
        print("ERROR: datasets library not installed.")
        return False
    
    # Try glaive first (ungated, large)
    print(f"\n  Downloading glaiveai/glaive-function-calling-v2...")
    
    try:
        dataset = load_dataset("glaiveai/glaive-function-calling-v2", split="train")
        print(f"  Downloaded {len(dataset)} examples")
    except Exception as e:
        print(f"  Warning: glaive dataset failed: {e}")
        print("  Trying NousResearch/hermes-function-calling-v1...")
        
        try:
            dataset = load_dataset("NousResearch/hermes-function-calling-v1", split="train")
            print(f"  Downloaded {len(dataset)} examples")
        except Exception as e2:
            print(f"  ERROR: Failed to download function calling datasets: {e2}")
            return False
    
    # Sample if needed
    indices = list(range(len(dataset)))
    if len(dataset) > target:
        random.shuffle(indices)
        indices = indices[:target]
    
    converted = []
    for idx in indices:
        example = dataset[idx]
        converted_example = convert_xlam_example(example)
        if converted_example:
            converted.append(converted_example)
    
    # Write output
    XLAM_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(XLAM_OUTPUT, 'w', encoding='utf-8') as f:
        for ex in converted:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')
    
    print(f"  ✓ Saved {len(converted)} examples to {XLAM_OUTPUT.name}")
    return True


def convert_xlam_example(example: Dict) -> Optional[Dict]:
    """Convert function calling formats to our training format.
    
    Handles multiple formats:
    - glaive: {"system": str, "chat": str} with function calls embedded
    - xLAM: {"query": str, "tools": list, "answers": list}
    - hermes: {"conversations": list}
    """
    try:
        # Glaive format: system + chat with function calls
        if "chat" in example:
            chat = example.get("chat", "")
            system = example.get("system", TOOL_SYSTEM)
            
            # Parse chat to extract user/assistant turns
            # Glaive uses "USER:" and "ASSISTANT:" markers
            if "USER:" in chat and "ASSISTANT:" in chat:
                parts = chat.split("USER:", 1)
                if len(parts) > 1:
                    rest = parts[1]
                    if "ASSISTANT:" in rest:
                        user_part, assistant_part = rest.split("ASSISTANT:", 1)
                        instruction = user_part.strip()
                        response = assistant_part.strip()
                        
                        if len(instruction) > 10 and len(response) > 10:
                            return {
                                "system": system if system else TOOL_SYSTEM,
                                "instruction": instruction,
                                "response": response,
                                "category": "function_calling",
                                "source": "glaive"
                            }
            return None
        
        # xLAM/Salesforce format
        query = example.get("query", "")
        tools = example.get("tools", [])
        answers = example.get("answers", "")
        
        if not query or not answers:
            return None
        
        # Format tools for context
        tools_str = ""
        if tools:
            if isinstance(tools, str):
                tools_str = tools
            else:
                tools_str = json.dumps(tools, indent=2)
        
        # Build instruction with tool context
        instruction = query
        if tools_str:
            instruction = f"Available tools:\n{tools_str}\n\nUser request: {query}"
        
        # Format response
        response = answers if isinstance(answers, str) else json.dumps(answers, indent=2)
        
        return {
            "system": TOOL_SYSTEM,
            "instruction": instruction,
            "response": response,
            "category": "function_calling",
            "source": "xlam"
        }
    except Exception:
        return None


def download_agent_instruct(max_examples: int = 100000, target: int = 30000) -> bool:
    """
    Download and prepare THUDM AgentInstruct dataset.
    
    This dataset contains diverse agent traces across categories:
    - ALFWorld (household tasks)
    - WebShop (e-commerce)
    - Mind2Web (web navigation)
    - Knowledge Graph (kg)
    - Operating System (os)
    - Database (db)
    
    Note: Dataset has separate splits, not a single 'train' split.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        print("ERROR: datasets library not installed.")
        return False
    
    print(f"\n  Downloading THUDM/AgentInstruct...")
    
    # AgentInstruct has multiple splits, not a 'train' split
    splits = ["os", "db", "alfworld", "webshop", "kg", "mind2web"]
    all_examples = []
    
    for split_name in splits:
        try:
            split_data = load_dataset("THUDM/AgentInstruct", split=split_name)
            print(f"    {split_name}: {len(split_data)} examples")
            for ex in split_data:
                ex["_split"] = split_name  # Track source
                all_examples.append(ex)
        except Exception as e:
            print(f"    {split_name}: Failed - {e}")
    
    if not all_examples:
        print(f"  ERROR: Failed to download any AgentInstruct splits")
        return False
    
    print(f"  Total downloaded: {len(all_examples)} examples")
    dataset = all_examples
    
    # Sample if needed
    if len(dataset) > target:
        dataset = random.sample(dataset, target)
    
    converted = []
    for example in dataset:
        converted_example = convert_agent_instruct_example(example)
        if converted_example:
            converted.append(converted_example)
    
    # Write output
    AGENT_INSTRUCT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(AGENT_INSTRUCT_OUTPUT, 'w', encoding='utf-8') as f:
        for ex in converted:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')
    
    print(f"  ✓ Saved {len(converted)} examples to {AGENT_INSTRUCT_OUTPUT.name}")
    return True


def convert_agent_instruct_example(example: Dict) -> Optional[Dict]:
    """Convert AgentInstruct format to our training format.
    
    AgentInstruct splits have format:
    - conversations: list of {"from": "human/gpt", "value": str}
    - OR specific fields per split
    """
    try:
        instruction = ""
        response = ""
        split_name = example.get("_split", "agent")
        
        # AgentInstruct uses conversations format
        if "conversations" in example:
            convs = example["conversations"]
            if isinstance(convs, list) and len(convs) >= 2:
                # Find human and gpt turns
                human_turns = []
                gpt_turns = []
                
                for turn in convs:
                    if isinstance(turn, dict):
                        role = turn.get("from", "")
                        value = turn.get("value", "")
                        if role == "human":
                            human_turns.append(value)
                        elif role == "gpt":
                            gpt_turns.append(value)
                
                if human_turns and gpt_turns:
                    instruction = human_turns[0]
                    response = "\n".join(gpt_turns)  # Include all assistant responses
        
        # Fallback to other field names
        if not instruction or not response:
            if "instruction" in example and "output" in example:
                instruction = example["instruction"]
                if example.get("input"):
                    instruction = f"{instruction}\n\nInput: {example['input']}"
                response = example["output"]
            elif "query" in example and "response" in example:
                instruction = example["query"]
                response = example["response"]
        
        if not instruction or not response:
            return None
        
        # Clean up
        instruction = str(instruction).strip()
        response = str(response).strip()
        
        if len(instruction) < 10 or len(response) < 10:
            return None
        
        return {
            "system": DEFAULT_SYSTEM,
            "instruction": instruction,
            "response": response,
            "category": f"agent_{split_name}",
            "source": "agent_instruct"
        }
    except Exception:
        return None


def main():
    """Download and prepare all agentic datasets."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download agentic training datasets")
    parser.add_argument("--xlam-target", type=int, default=20000,
                        help="Target examples from xLAM dataset")
    parser.add_argument("--agent-target", type=int, default=30000,
                        help="Target examples from AgentInstruct")
    parser.add_argument("--skip-xlam", action="store_true",
                        help="Skip xLAM dataset download")
    parser.add_argument("--skip-agent", action="store_true",
                        help="Skip AgentInstruct download")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Downloading Agentic Training Datasets")
    print("=" * 60)
    
    stats = DatasetStats()
    success = True
    
    # Download xLAM
    if not args.skip_xlam:
        if XLAM_OUTPUT.exists():
            with open(XLAM_OUTPUT, 'r') as f:
                count = sum(1 for _ in f)
            print(f"\n  xLAM dataset already exists: {count} examples")
            response = input("  Re-download? [y/N]: ").strip().lower()
            if response != 'y':
                stats.by_source["xlam"] = count
            else:
                if download_xlam_dataset(target=args.xlam_target):
                    with open(XLAM_OUTPUT, 'r') as f:
                        stats.by_source["xlam"] = sum(1 for _ in f)
                else:
                    success = False
        else:
            if download_xlam_dataset(target=args.xlam_target):
                with open(XLAM_OUTPUT, 'r') as f:
                    stats.by_source["xlam"] = sum(1 for _ in f)
            else:
                success = False
    
    # Download AgentInstruct
    if not args.skip_agent:
        if AGENT_INSTRUCT_OUTPUT.exists():
            with open(AGENT_INSTRUCT_OUTPUT, 'r') as f:
                count = sum(1 for _ in f)
            print(f"\n  AgentInstruct dataset already exists: {count} examples")
            response = input("  Re-download? [y/N]: ").strip().lower()
            if response != 'y':
                stats.by_source["agent_instruct"] = count
            else:
                if download_agent_instruct(target=args.agent_target):
                    with open(AGENT_INSTRUCT_OUTPUT, 'r') as f:
                        stats.by_source["agent_instruct"] = sum(1 for _ in f)
                else:
                    success = False
        else:
            if download_agent_instruct(target=args.agent_target):
                with open(AGENT_INSTRUCT_OUTPUT, 'r') as f:
                    stats.by_source["agent_instruct"] = sum(1 for _ in f)
            else:
                success = False
    
    # Calculate totals
    stats.total_converted = sum(stats.by_source.values())
    
    # Save stats
    with open(STATS_FILE, 'w') as f:
        json.dump({
            "total_examples": stats.total_converted,
            "by_source": stats.by_source,
        }, f, indent=2)
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for source, count in stats.by_source.items():
        print(f"  {source}: {count:,} examples")
    print(f"  Total: {stats.total_converted:,} examples")
    
    if success:
        print("\n✓ Agentic datasets ready!")
    else:
        print("\n⚠ Some datasets failed to download")
    
    return success


if __name__ == "__main__":
    random.seed(42)
    success = main()
    exit(0 if success else 1)
