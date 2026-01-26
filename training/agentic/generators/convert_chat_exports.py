#!/usr/bin/env python3
"""
Quick converter: Turn Open-WebUI chat exports into training examples.

Specifically designed to extract the GOOD patterns from real AJ interactions
and format them for fine-tuning.

Usage:
    python convert_chat_exports.py chat-export-*.json --output training_from_sessions.jsonl
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ToolCall:
    tool: str
    params: Dict
    output: str
    success: bool


@dataclass
class Turn:
    role: str
    content: str
    tool_calls: List[ToolCall]
    is_good_example: bool  # Flag for quality
    quality_notes: str


def parse_assistant_content(content: str) -> Tuple[str, List[ToolCall]]:
    """
    Parse assistant message to extract:
    1. Clean response text
    2. Tool calls with their outputs
    """
    tool_calls = []
    
    # Pattern: **tool_name output:**\n```\n...\n```
    tool_pattern = r'\*\*(\w+) output:\*\*\s*```\s*([\s\S]*?)```'
    
    for match in re.finditer(tool_pattern, content):
        tool_name = match.group(1)
        output = match.group(2).strip()
        
        # Determine success based on output content
        success = "error" not in output.lower() and "failed" not in output.lower()
        
        tool_calls.append(ToolCall(
            tool=tool_name,
            params={},  # Would need to parse from thinking blocks
            output=output,
            success=success,
        ))
    
    # Extract clean response (remove tool outputs, keep final answer)
    clean_content = content
    
    # Remove task plan blocks
    clean_content = re.sub(r'> 📋 \*\*Task Plan:\*\*[\s\S]*?(?=\n\n|\*\*\w+ output:)', '', clean_content)
    
    # Remove tool output blocks
    clean_content = re.sub(r'\*\*\w+ output:\*\*\s*```[\s\S]*?```', '', clean_content)
    
    # Remove duplicate separators
    clean_content = re.sub(r'\n---\n+', '\n\n', clean_content)
    
    # Clean up whitespace
    clean_content = re.sub(r'\n{3,}', '\n\n', clean_content).strip()
    
    return clean_content, tool_calls


def assess_quality(turn: Turn, prev_turns: List[Turn]) -> Tuple[bool, str]:
    """
    Assess if this is a good training example.
    
    Good examples:
    - Correct tool usage
    - Coherent response
    - Appropriate tone
    - No errors like "Unknown tool"
    
    Bad examples:
    - Wrong output format (action vs tool)
    - Tool errors
    - Incoherent responses
    - Missing context
    """
    notes = []
    is_good = True
    
    content = turn.content.lower()
    
    # Check for known bad patterns
    if "unknown tool" in content:
        is_good = False
        notes.append("Contains 'Unknown tool' error")
    
    if '"action":' in content and '"tool":' not in content:
        is_good = False
        notes.append("Wrong format: uses 'action' instead of 'tool'")
    
    if "no agents were discovered" in content and any(
        "list_agents" in t.content for t in prev_turns if t.role == "assistant"
    ):
        is_good = False
        notes.append("Lost context: forgot discovered agents")
    
    # Check for good patterns
    if any(tc.success for tc in turn.tool_calls):
        notes.append("Has successful tool calls")
    
    if turn.content and len(turn.content) > 50 and "```" not in turn.content[:100]:
        notes.append("Has natural language response")
    
    # Multi-turn context check
    if len(prev_turns) >= 2:
        # Check if response references previous context
        prev_content = " ".join(t.content for t in prev_turns[-2:])
        if any(word in turn.content for word in ["earlier", "you mentioned", "as we saw"]):
            notes.append("Good context awareness")
    
    return is_good, "; ".join(notes) if notes else "Standard example"


def convert_chat_export(export_path: Path) -> List[Dict]:
    """Convert a single chat export file to training examples."""
    
    with open(export_path, encoding='utf-8') as f:
        data = json.load(f)
    
    examples = []
    
    for chat_data in data:
        chat = chat_data.get("chat", {})
        messages = chat.get("messages", [])
        title = chat.get("title", "untitled")
        
        if not messages:
            continue
        
        turns = []
        all_turns_for_context = []
        
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                turn = Turn(
                    role="user",
                    content=content,
                    tool_calls=[],
                    is_good_example=True,
                    quality_notes="User input",
                )
            else:
                clean_content, tool_calls = parse_assistant_content(content)
                turn = Turn(
                    role="assistant",
                    content=content,  # Keep original for training
                    tool_calls=tool_calls,
                    is_good_example=True,
                    quality_notes="",
                )
                
                # Assess quality
                is_good, notes = assess_quality(turn, all_turns_for_context)
                turn.is_good_example = is_good
                turn.quality_notes = notes
            
            turns.append(turn)
            all_turns_for_context.append(turn)
        
        # Determine overall example quality
        assistant_turns = [t for t in turns if t.role == "assistant"]
        good_ratio = sum(1 for t in assistant_turns if t.is_good_example) / len(assistant_turns) if assistant_turns else 0
        
        # Build training example
        example = {
            "messages": [
                {
                    "role": t.role,
                    "content": t.content,
                }
                for t in turns
            ],
            "metadata": {
                "source": "chat_export",
                "original_title": title,
                "quality_score": good_ratio,
                "turn_count": len(turns),
                "tools_used": list(set(
                    tc.tool for t in turns for tc in t.tool_calls
                )),
                "quality_notes": [
                    {"turn": i, "notes": t.quality_notes}
                    for i, t in enumerate(turns) if t.quality_notes
                ],
                "is_recommended": good_ratio >= 0.7,
            }
        }
        
        examples.append(example)
    
    return examples


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_chat_exports.py <export.json> [export2.json ...] [--output file.jsonl]")
        sys.exit(1)
    
    # Parse args
    input_files = []
    output_file = Path("training_from_chat_exports.jsonl")
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--output" and i + 1 < len(args):
            output_file = Path(args[i + 1])
            i += 2
        else:
            input_files.append(Path(args[i]))
            i += 1
    
    if not input_files:
        print("No input files specified")
        sys.exit(1)
    
    all_examples = []
    
    for input_path in input_files:
        if not input_path.exists():
            print(f"Warning: {input_path} not found, skipping")
            continue
        
        print(f"Processing: {input_path}")
        examples = convert_chat_export(input_path)
        all_examples.extend(examples)
        
        # Stats
        good = sum(1 for e in examples if e["metadata"]["is_recommended"])
        print(f"  → {len(examples)} conversations ({good} recommended for training)")
    
    # Write output
    with open(output_file, "w") as f:
        for ex in all_examples:
            f.write(json.dumps(ex) + "\n")
    
    print(f"\nTotal: {len(all_examples)} examples → {output_file}")
    
    # Summary stats
    recommended = [e for e in all_examples if e["metadata"]["is_recommended"]]
    not_recommended = [e for e in all_examples if not e["metadata"]["is_recommended"]]
    
    print(f"\n📊 Quality Summary:")
    print(f"  ✅ Recommended: {len(recommended)}")
    print(f"  ⚠️ Needs review: {len(not_recommended)}")
    
    if not_recommended:
        print(f"\n⚠️ Issues found in non-recommended examples:")
        for ex in not_recommended[:5]:  # Show first 5
            for note in ex["metadata"]["quality_notes"]:
                if "error" in note["notes"].lower() or "wrong" in note["notes"].lower():
                    print(f"  - Turn {note['turn']}: {note['notes']}")


if __name__ == "__main__":
    main()
