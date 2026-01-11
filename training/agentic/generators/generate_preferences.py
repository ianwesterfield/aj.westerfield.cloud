#!/usr/bin/env python3
"""
DPO Preference Data Generator

Generates preference pairs for Direct Preference Optimization by:
1. Taking a task/prompt
2. Generating multiple candidate responses
3. Ranking them by quality criteria
4. Outputting (chosen, rejected) pairs

Usage:
    python generate_preferences.py --count 1000 --output ../data/preferences/
    python generate_preferences.py --from-trajectories ../data/trajectories/ --inject-errors
"""

import json
import argparse
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PreferencePair:
    prompt: str
    chosen: str
    rejected: str
    preference_reason: str
    margin: float  # How much better chosen is (0.0-1.0)
    category: str


# Quality degradation patterns for generating "rejected" responses
DEGRADATION_PATTERNS = {
    "missing_error_handling": {
        "description": "Remove error handling",
        "transform": lambda code: code.replace("try {", "// try {").replace("} catch", "// } catch"),
        "reason": "error_handling",
        "margin": 0.7
    },
    "poor_naming": {
        "description": "Use poor variable names",
        "transform": lambda code: code.replace("user", "x").replace("data", "d").replace("result", "r"),
        "reason": "readability",
        "margin": 0.5
    },
    "missing_validation": {
        "description": "Remove input validation",
        "transform": lambda code: "\n".join(l for l in code.split("\n") if "valid" not in l.lower() and "check" not in l.lower()),
        "reason": "safety",
        "margin": 0.8
    },
    "verbose": {
        "description": "Make unnecessarily verbose",
        "transform": lambda code: code.replace("const ", "const /* declaring variable */ ").replace("return ", "// returning value\nreturn "),
        "reason": "readability",
        "margin": 0.3
    },
    "no_types": {
        "description": "Remove type annotations",
        "transform": lambda code: code.replace(": string", "").replace(": number", "").replace(": boolean", "").replace(": any", ""),
        "reason": "correctness",
        "margin": 0.6
    }
}


# Task templates for generating new preference pairs
TASK_TEMPLATES = [
    "Write a function to {action}",
    "Implement {feature} for {context}",
    "Create a {component} that {behavior}",
    "Add error handling to this code: {code_snippet}",
    "Refactor this function to be more readable: {code_snippet}",
]

# Good vs bad response templates
RESPONSE_PAIRS = [
    {
        "prompt": "Write a function to validate email addresses",
        "chosen": '''```typescript
function validateEmail(email: string): boolean {
  if (!email || typeof email !== 'string') {
    return false;
  }
  
  // RFC 5322 compliant regex
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email.trim());
}
```

This handles edge cases like:
- Null/undefined input
- Non-string input
- Whitespace trimming
- Basic format validation''',
        "rejected": '''```javascript
function validateEmail(email) {
  return email.includes('@');
}
```

This checks if the email has an @ sign.''',
        "reason": "correctness",
        "margin": 0.9
    },
    {
        "prompt": "Fetch user data from an API",
        "chosen": '''```typescript
async function fetchUser(userId: string): Promise<User | null> {
  if (!userId) {
    throw new Error('userId is required');
  }
  
  try {
    const response = await fetch(`/api/users/${encodeURIComponent(userId)}`);
    
    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch user:', error);
    throw error;
  }
}
```

Includes proper error handling, input validation, and URL encoding.''',
        "rejected": '''```javascript
async function fetchUser(userId) {
  const response = await fetch('/api/users/' + userId);
  return response.json();
}
```

Simple fetch that gets the user.''',
        "reason": "error_handling",
        "margin": 0.85
    },
    {
        "prompt": "Parse command line arguments",
        "chosen": '''```python
import argparse
from typing import Optional

def parse_args() -> argparse.Namespace:
    """Parse and validate command line arguments."""
    parser = argparse.ArgumentParser(
        description='Process data files',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('input', help='Input file path')
    parser.add_argument('-o', '--output', default='output.txt',
                        help='Output file path (default: output.txt)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output')
    parser.add_argument('--limit', type=int, default=100,
                        help='Maximum records to process')
    
    args = parser.parse_args()
    
    # Validate input file exists
    from pathlib import Path
    if not Path(args.input).exists():
        parser.error(f'Input file not found: {args.input}')
    
    return args
```

Uses argparse with proper help text, defaults, and validation.''',
        "rejected": '''```python
import sys

input_file = sys.argv[1]
output_file = sys.argv[2] if len(sys.argv) > 2 else 'output.txt'
```

Gets input and output from sys.argv.''',
        "reason": "completeness",
        "margin": 0.8
    },
]


def generate_from_templates(count: int) -> List[PreferencePair]:
    """Generate preference pairs from templates."""
    pairs = []
    
    for _ in range(count):
        template = random.choice(RESPONSE_PAIRS)
        pairs.append(PreferencePair(
            prompt=template["prompt"],
            chosen=template["chosen"],
            rejected=template["rejected"],
            preference_reason=template["reason"],
            margin=template["margin"],
            category="code_quality"
        ))
    
    return pairs


def degrade_response(good_response: str, pattern_name: str) -> Tuple[str, str, float]:
    """Apply a degradation pattern to create a rejected response."""
    
    if pattern_name not in DEGRADATION_PATTERNS:
        pattern_name = random.choice(list(DEGRADATION_PATTERNS.keys()))
    
    pattern = DEGRADATION_PATTERNS[pattern_name]
    degraded = pattern["transform"](good_response)
    
    return degraded, pattern["reason"], pattern["margin"]


def generate_from_trajectories(trajectory_dir: Path, inject_errors: bool = False) -> List[PreferencePair]:
    """Generate preference pairs from existing trajectories."""
    
    pairs = []
    
    for filepath in trajectory_dir.glob("*.jsonl"):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                    
                try:
                    traj = json.loads(line)
                except:
                    continue
                
                task = traj.get("task", "")
                steps = traj.get("trajectory", [])
                
                # Find final answer
                final_answer = None
                for step in steps:
                    if step.get("step_type") == "final_answer":
                        final_answer = step.get("content", "")
                        break
                
                if not final_answer:
                    continue
                
                # Create chosen response (full trajectory)
                chosen = format_trajectory_response(steps)
                
                # Create rejected response (just the answer, no reasoning)
                rejected = final_answer
                
                pairs.append(PreferencePair(
                    prompt=task,
                    chosen=chosen,
                    rejected=rejected,
                    preference_reason="completeness",
                    margin=0.7,
                    category="reasoning_trace"
                ))
    
    return pairs


def format_trajectory_response(steps: List[Dict]) -> str:
    """Format trajectory steps into a response."""
    
    parts = []
    for step in steps:
        step_type = step.get("step_type")
        
        if step_type == "thought":
            parts.append(f"**Thinking:** {step.get('content', '')}")
        elif step_type == "action":
            tool = step.get("tool", "")
            tool_input = step.get("tool_input", {})
            parts.append(f"**Action:** Using `{tool}`")
        elif step_type == "observation":
            parts.append(f"**Result:** {step.get('content', '')[:200]}...")
        elif step_type == "final_answer":
            parts.append(f"\n**Summary:**\n{step.get('content', '')}")
    
    return "\n\n".join(parts)


def preference_to_dict(pair: PreferencePair) -> Dict:
    """Convert preference pair to serializable dict."""
    return {
        "prompt": pair.prompt,
        "chosen": pair.chosen,
        "rejected": pair.rejected,
        "metadata": {
            "preference_reason": pair.preference_reason,
            "margin": pair.margin,
            "category": pair.category
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Generate DPO preference data")
    parser.add_argument("--count", "-n", type=int, default=500)
    parser.add_argument("--output", "-o", type=str, default="../data/preferences/")
    parser.add_argument("--from-trajectories", type=str,
                        help="Generate pairs from existing trajectories")
    parser.add_argument("--inject-errors", action="store_true",
                        help="Create rejected by injecting errors into good responses")
    parser.add_argument("--seed", type=int, default=42)
    
    args = parser.parse_args()
    random.seed(args.seed)
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating DPO preference pairs...")
    
    pairs = []
    
    # Generate from templates
    template_count = args.count // 2
    pairs.extend(generate_from_templates(template_count))
    print(f"  Generated {template_count} from templates")
    
    # Generate from trajectories if provided
    if args.from_trajectories:
        traj_dir = Path(args.from_trajectories)
        traj_pairs = generate_from_trajectories(traj_dir, args.inject_errors)
        pairs.extend(traj_pairs[:args.count - len(pairs)])
        print(f"  Generated {len(traj_pairs)} from trajectories")
    
    # Fill remaining with templates
    while len(pairs) < args.count:
        pairs.extend(generate_from_templates(min(50, args.count - len(pairs))))
    
    # Write output
    output_file = output_dir / "preferences.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f:
        for pair in pairs[:args.count]:
            f.write(json.dumps(preference_to_dict(pair), ensure_ascii=False) + '\n')
    
    print(f"\n✅ Generated {min(len(pairs), args.count)} preference pairs")
    print(f"   Saved to: {output_file}")


if __name__ == "__main__":
    main()
