#!/usr/bin/env python3
"""
Download and prepare agentic/tool-use datasets for training.

This script downloads publicly available datasets with high-quality
agentic traces, function calling, and tool-use examples:

1. Salesforce xLAM Function Calling (60K) - High quality tool use
2. THUDM AgentInstruct (1.8M) - Diverse agent traces
3. Agent-Ark Toucan-1.5M (1.5M) - Real MCP tool-use trajectories
4. NousResearch Hermes Function Calling (12K) - Function calling format

These datasets supplement local AJ training data to create a capable
agentic assistant.
"""

import os
import json
import random
from pathlib import Path
from typing import Dict, List, Any, Optional, Generator, cast
from dataclasses import dataclass, field

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"

# Output files
XLAM_OUTPUT = DATA_DIR / "xlam_function_calling.jsonl"
AGENT_INSTRUCT_OUTPUT = DATA_DIR / "agent_instruct.jsonl"
TOUCAN_OUTPUT = DATA_DIR / "toucan_trajectories.jsonl"
STATS_FILE = DATA_DIR / "agentic_dataset_stats.json"

# Dataset configurations
# Note: Some datasets are gated - we use publicly available alternatives
DATASETS = {
    "gorilla": {
        "name": "gorilla-llm/Berkeley-Function-Calling-Leaderboard",
        "output": XLAM_OUTPUT,  # Reuse the xlam output name
        "target_examples": 60000,
        "description": "Berkeley function calling benchmark data",
    },
    "agent_instruct": {
        "name": "THUDM/AgentInstruct",
        "output": AGENT_INSTRUCT_OUTPUT,
        "target_examples": 1800000,
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


def download_xlam_dataset(max_examples: int = 60000, target: int = 60000) -> bool:
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
    
    # Sample if needed (0 = all)
    indices = list(range(len(dataset)))
    if target > 0 and len(dataset) > target:
        random.shuffle(indices)
        indices = indices[:target]
    
    print(f"  Processing {len(indices)} examples...")
    
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


def download_agent_instruct(max_examples: int = 1800000, target: int = 1800000) -> bool:
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
    
    # Sample if needed (0 = all)
    if target > 0 and len(dataset) > target:
        dataset = random.sample(dataset, target)
    
    print(f"  Processing {len(dataset)} examples...")
    
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


def download_toucan_dataset(target: int = 50000, subsets: list = None) -> bool:
    """
    Download Agent-Ark/Toucan-1.5M dataset (ALL subsets for full 1.5M).
    
    Toucan-1.5M is the largest fully synthetic tool-agent dataset, comprising 
    over 1.5 million trajectories synthesized from 495 real-world Model Context 
    Protocols (MCPs) spanning 2,000+ tools.
    
    Available subsets (all downloaded by default):
    - Kimi-K2: ~519K trajectories (Kimi K2 model)
    - OSS: ~500K trajectories (open source models)
    - Qwen3: ~500K trajectories (Qwen3 model)
    - SFT: supervised fine-tuning formatted data
    
    Total: ~1.5M+ trajectories
    """
    try:
        from datasets import load_dataset
    except ImportError:
        print("ERROR: datasets library not installed.")
        return False
    
    # Default: download ALL subsets for full 1.5M+
    if subsets is None:
        subsets = ["Kimi-K2", "OSS", "Qwen3", "SFT"]
    
    print(f"\n  Downloading Agent-Ark/Toucan-1.5M (ALL {len(subsets)} subsets)...")
    print(f"  Subsets: {', '.join(subsets)}")
    print(f"  This dataset contains real MCP tool-use trajectories.")
    
    all_converted = []
    total_skipped = 0
    debug_printed = False
    
    for subset in subsets:
        print(f"\n  --- Subset: {subset} ---")
        
        try:
            # Use streaming to avoid loading entire dataset into memory
            dataset = load_dataset("Agent-Ark/Toucan-1.5M", subset, split="train", streaming=True)
            
            if target > 0:
                per_subset_target = target // len(subsets)
                print(f"  Streaming {subset}, sampling {per_subset_target} examples...")
            else:
                print(f"  Streaming {subset}, downloading ALL examples...")
            
            subset_converted = []
            skipped = 0
            
            for i, example in enumerate(dataset):
                # If target>0, limit per subset
                if target > 0:
                    per_subset_target = target // len(subsets)
                    if i >= per_subset_target * 2:
                        break
                
                # Debug: print schema of first example (once)
                if not debug_printed:
                    print(f"  Inspecting first example schema...")
                    convert_toucan_example(example, debug=True)
                    debug_printed = True
                
                converted_example = convert_toucan_example(example)
                if converted_example:
                    converted_example["_subset"] = subset  # Track source subset
                    subset_converted.append(converted_example)
                    # If target>0, stop at per-subset limit
                    if target > 0 and len(subset_converted) >= per_subset_target:
                        break
                else:
                    skipped += 1
                
                # Progress indicator for large downloads
                if (i + 1) % 50000 == 0:
                    print(f"    {subset}: {i + 1} processed, {len(subset_converted)} converted...")
            
            print(f"  {subset}: {len(subset_converted)} converted, {skipped} skipped")
            all_converted.extend(subset_converted)
            total_skipped += skipped
            
        except Exception as e:
            print(f"  ERROR: Failed to download {subset}: {e}")
            import traceback
            traceback.print_exc()
            # Continue with other subsets
            continue
    
    print(f"\n  TOTAL: {len(all_converted)} converted, {total_skipped} skipped")
    
    if not all_converted:
        print("  ERROR: No examples converted from Toucan")
        return False
    
    # Write output
    TOUCAN_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(TOUCAN_OUTPUT, 'w', encoding='utf-8') as f:
        for ex in all_converted:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')
    
    print(f"  ✓ Saved {len(all_converted)} examples to {TOUCAN_OUTPUT.name}")
    return True


def convert_toucan_example(example: Dict, debug: bool = False) -> Optional[Dict]:
    """Convert Toucan trajectory format to our training format.
    
    Toucan schema (from HuggingFace):
    - messages: JSON STRING containing chat trajectory
    - question: User task (string)
    - target_tools: COMMA-SEPARATED STRING of tool names
    - subset_name: Pipeline annotation (single-turn-original, multi-turn, etc.)
    """
    try:
        # Debug: print first example's schema
        if debug:
            print(f"    DEBUG - Keys: {list(example.keys())}")
            for k, v in example.items():
                if isinstance(v, str) and len(v) > 100:
                    print(f"    DEBUG - {k}: {type(v).__name__} = {v[:100]}...")
                elif isinstance(v, list) and len(v) > 0:
                    print(f"    DEBUG - {k}: list[{len(v)}], first={type(v[0]).__name__}")
                    if isinstance(v[0], dict):
                        print(f"    DEBUG -   first item keys: {list(v[0].keys())}")
                else:
                    print(f"    DEBUG - {k}: {type(v).__name__} = {v}")
            return None
        
        # messages is a JSON string, not a list!
        messages_raw = example.get("messages", "")
        question = example.get("question", "")
        target_tools_raw = example.get("target_tools", "")
        subset_type = example.get("subset_name", "")  # Note: it's subset_name, not subset
        
        # Parse messages from JSON string
        if isinstance(messages_raw, str):
            try:
                messages = json.loads(messages_raw)
            except json.JSONDecodeError:
                return None
        else:
            messages = messages_raw
        
        if not messages or not isinstance(messages, list) or len(messages) < 2:
            return None
        
        # Parse target_tools from comma-separated string
        if isinstance(target_tools_raw, str):
            target_tools = [t.strip() for t in target_tools_raw.split(",") if t.strip()]
        else:
            target_tools = target_tools_raw if target_tools_raw else []
        
        # Extract system, user, and assistant from messages
        system_content = ""
        instruction = ""
        response_parts = []
        
        for msg in messages:
            # Handle both dict format and other formats
            if isinstance(msg, dict):
                role = msg.get("role", "")
                content = msg.get("content", "")
            else:
                # Skip non-dict messages
                continue
            
            if role == "system":
                system_content = content if isinstance(content, str) else ""
            elif role == "user":
                if not instruction:  # Take first user message as instruction
                    instruction = content if isinstance(content, str) else ""
            elif role == "assistant":
                if isinstance(content, str) and content:
                    response_parts.append(content)
        
        # Use question if no user message found
        if not instruction and question:
            instruction = question if isinstance(question, str) else ""
        
        if not instruction or not response_parts:
            return None
        
        response = "\n".join(response_parts)
        
        # Clean up
        instruction = str(instruction).strip()
        response = str(response).strip()
        
        if len(instruction) < 10 or len(response) < 10:
            return None
        
        # Build tool context string
        tools_context = ""
        if target_tools:
            tools_str = ", ".join(target_tools[:5])  # Limit for readability
            if len(target_tools) > 5:
                tools_str += f" (+{len(target_tools) - 5} more)"
            tools_context = f" [Tools: {tools_str}]"
        
        return {
            "system": system_content if system_content else TOOL_SYSTEM,
            "instruction": instruction,
            "response": response,
            "category": "mcp_tool_use",
            "source": "toucan",
            "subset": subset_type,
        }
    except Exception:
        return None


def main():
    """Download and prepare all agentic datasets."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download agentic training datasets")
    parser.add_argument("--xlam-target", type=int, default=0,
                        help="Target examples from xLAM dataset (0 = all)")
    parser.add_argument("--agent-target", type=int, default=0,
                        help="Target examples from AgentInstruct (0 = all)")
    parser.add_argument("--toucan-target", type=int, default=0,
                        help="Target examples from Toucan-1.5M dataset (0 = all)")
    parser.add_argument("--toucan-subsets", type=str, nargs="*", default=None,
                        help="Toucan subsets to use (default: all three: Kimi-K2, Qwen3-32B, GPT-OSS-120B)")
    parser.add_argument("--skip-xlam", action="store_true",
                        help="Skip xLAM dataset download")
    parser.add_argument("--skip-agent", action="store_true",
                        help="Skip AgentInstruct download")
    parser.add_argument("--skip-toucan", action="store_true",
                        help="Skip Toucan-1.5M download")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="Skip confirmation prompts")
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
            if args.yes:
                response = 'n'
            else:
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
            if args.yes:
                response = 'n'
            else:
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
    
    # Download Toucan-1.5M (MCP tool-use trajectories)
    if not args.skip_toucan:
        if TOUCAN_OUTPUT.exists():
            with open(TOUCAN_OUTPUT, 'r') as f:
                count = sum(1 for _ in f)
            print(f"\n  Toucan dataset already exists: {count} examples")
            if args.yes:
                response = 'n'
            else:
                response = input("  Re-download? [y/N]: ").strip().lower()
            if response != 'y':
                stats.by_source["toucan"] = count
            else:
                if download_toucan_dataset(target=args.toucan_target, subsets=args.toucan_subsets):
                    with open(TOUCAN_OUTPUT, 'r') as f:
                        stats.by_source["toucan"] = sum(1 for _ in f)
                else:
                    success = False
        else:
            if download_toucan_dataset(target=args.toucan_target, subsets=args.toucan_subsets):
                with open(TOUCAN_OUTPUT, 'r') as f:
                    stats.by_source["toucan"] = sum(1 for _ in f)
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
