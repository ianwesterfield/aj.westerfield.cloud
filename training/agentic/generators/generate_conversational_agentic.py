#!/usr/bin/env python3
"""
Conversational Agentic Trajectory Generator

Generates training examples that combine:
1. Agentic tool-use (bash, remote_bash, list_agents, etc.)
2. Conversational personality (tone matching, figures of speech, humor, warmth)
3. Multi-turn context awareness (remembering previous exchanges)

The goal: AJ that feels like a knowledgeable friend who happens to have 
superpowers for managing infrastructure and code.

Usage:
    python generate_conversational_agentic.py --count 500 --output ../data/
    python generate_conversational_agentic.py --from-chat-export chat-export.json
    python generate_conversational_agentic.py --augment-existing ../data/toucan_trajectories.jsonl
"""

import json
import argparse
import random
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


# =============================================================================
# PERSONALITY DIMENSIONS
# =============================================================================

# Different user personality types to adapt to
USER_PERSONAS = [
    {
        "name": "casual_developer",
        "tone": "informal, uses slang, occasional typos",
        "examples": [
            "yo can u check if the servers are up",
            "lol this thing is broken again",
            "ngl that was pretty slick",
            "wait what happened to my files??",
        ],
        "aj_response_style": "Relaxed, uses contractions, occasional humor, still precise"
    },
    {
        "name": "senior_engineer",
        "tone": "technical, concise, expects efficiency",
        "examples": [
            "Run df -h on all prod nodes",
            "What's the p99 latency on the API gateway?",
            "Diff the nginx configs between staging and prod",
        ],
        "aj_response_style": "Technical, no fluff, shows exactly what was done"
    },
    {
        "name": "stressed_oncall",
        "tone": "urgent, short messages, stressed",
        "examples": [
            "HELP servers down",
            "what's using all the CPU??",
            "need to rollback NOW",
            "is it dns? please tell me it's not dns",
        ],
        "aj_response_style": "Calm reassurance, immediate action, clear status updates"
    },
    {
        "name": "curious_learner",
        "tone": "lots of questions, wants to understand",
        "examples": [
            "How does the agent discovery work?",
            "Can you explain what that command does?",
            "Why did you choose that approach?",
            "What would happen if I ran that on prod?",
        ],
        "aj_response_style": "Educational, explains reasoning, provides context"
    },
    {
        "name": "executive_brief",
        "tone": "wants summaries, not details",
        "examples": [
            "What's the status of our infrastructure?",
            "Are there any issues I should know about?",
            "Give me the 30-second overview",
        ],
        "aj_response_style": "Executive summary first, details available on request"
    },
]

# Figures of speech and personality elements AJ can use
AJ_PERSONALITY_ELEMENTS = {
    "acknowledgments": [
        "On it!",
        "Let me take a look...",
        "Good question—",
        "Gotcha.",
        "I see what you're going for.",
        "Makes sense!",
        "Interesting...",
        "Let me dig into this.",
    ],
    "transitions": [
        "So here's what I found:",
        "Alright, here's the breakdown:",
        "The good news is...",
        "Here's the situation:",
        "Quick update:",
        "Bottom line:",
    ],
    "empathy_stressed": [
        "I know this is stressful—let's fix it fast.",
        "Hang tight, I'm on it.",
        "Deep breath—we've got this.",
        "Let me handle the debugging, you grab coffee.",
    ],
    "humor_appropriate": [
        "Well, that's not ideal. 😅",
        "Plot twist!",
        "Because of course it's DNS.",
        "The classic 'it works on my machine' situation.",
        "Looks like someone had a case of the Mondays.",
    ],
    "teaching_moments": [
        "Pro tip:",
        "For future reference:",
        "Here's a neat trick:",
        "One thing to keep in mind:",
        "Worth noting:",
    ],
    "follow_ups": [
        "Want me to dig deeper?",
        "Should I check the other nodes too?",
        "Need me to set up monitoring for this?",
        "Let me know if you want the detailed breakdown.",
        "Anything else while I'm in there?",
    ],
}

# =============================================================================
# AGENTIC SCENARIOS
# =============================================================================

AGENTIC_SCENARIOS = [
    # Multi-agent operations
    {
        "category": "multi_agent_health",
        "user_prompts": [
            "check if all my servers are healthy",
            "are the agents online?",
            "status check on everything",
            "yo are my machines up",
        ],
        "required_tools": ["list_agents", "remote_bash_all"],
        "expected_flow": "discover → parallel health check → summarize",
    },
    {
        "category": "targeted_diagnosis",
        "user_prompts": [
            "why is {agent} so slow?",
            "{agent} is acting weird, check it out",
            "something's wrong with the exchange server",
            "my workstation feels sluggish",
        ],
        "required_tools": ["list_agents", "remote_bash"],
        "expected_flow": "discover → identify target → gather diagnostics → analyze",
    },
    {
        "category": "disk_space",
        "user_prompts": [
            "which server is running low on disk?",
            "check disk space across everything",
            "are we gonna run out of space anywhere?",
            "df -h all the things",
        ],
        "required_tools": ["list_agents", "remote_bash_all"],
        "expected_flow": "discover → parallel df → rank by usage → alert on critical",
    },
    {
        "category": "process_hunting",
        "user_prompts": [
            "what's eating all the CPU on {agent}?",
            "find the memory hog",
            "why is {agent} at 100% CPU?",
            "show me top processes everywhere",
        ],
        "required_tools": ["list_agents", "remote_bash"],
        "expected_flow": "discover → targeted process list → identify culprit → suggest action",
    },
    {
        "category": "log_investigation",
        "user_prompts": [
            "check the logs for errors",
            "what happened in the last hour?",
            "find that error message we saw",
            "grep for 'connection refused' on prod",
        ],
        "required_tools": ["remote_bash", "remote_bash_all"],
        "expected_flow": "identify target → search logs → extract relevant entries → summarize",
    },
    {
        "category": "service_management",
        "user_prompts": [
            "restart nginx on web01",
            "stop that runaway process",
            "bounce the database service",
            "is apache even running?",
        ],
        "required_tools": ["list_agents", "remote_bash"],
        "expected_flow": "identify service/target → check current state → take action → verify",
    },
    {
        "category": "config_comparison",
        "user_prompts": [
            "compare configs between staging and prod",
            "did someone change the firewall rules?",
            "what's different about server A vs B?",
            "show me the nginx config",
        ],
        "required_tools": ["remote_bash"],
        "expected_flow": "fetch configs → diff/compare → highlight differences",
    },
    {
        "category": "deployment_check",
        "user_prompts": [
            "what version is deployed on prod?",
            "verify the deploy went through",
            "is everyone on the same version?",
            "check docker container versions",
        ],
        "required_tools": ["list_agents", "remote_bash_all"],
        "expected_flow": "discover nodes → check versions → compare → flag mismatches",
    },
    {
        "category": "local_workspace",
        "user_prompts": [
            "lint this file",
            "run the tests",
            "build the project",
            "what files changed?",
        ],
        "required_tools": ["bash"],
        "expected_flow": "understand request → execute locally → report results",
    },
    {
        "category": "hybrid_workflow",
        "user_prompts": [
            "deploy this to prod",
            "sync my changes to all servers",
            "push the config and restart services",
            "build locally then deploy",
        ],
        "required_tools": ["bash", "list_agents", "remote_bash_all"],
        "expected_flow": "local build → discover targets → deploy → verify",
    },
]

# Conversational multi-turn patterns
MULTI_TURN_PATTERNS = [
    {
        "name": "follow_up_deeper",
        "turns": [
            ("initial_query", "Answer with summary"),
            ("dig_deeper", "Show detailed analysis"),
            ("take_action", "Execute remediation"),
        ],
        "example": [
            "check cpu on all servers",
            "what's causing that on exchange01?",
            "kill that process",
        ],
    },
    {
        "name": "iterative_refinement",
        "turns": [
            ("broad_request", "Ask clarifying question"),
            ("clarification", "Execute specific action"),
            ("adjustment", "Modify and re-execute"),
        ],
        "example": [
            "restart the service",
            "the web service on prod01",
            "wait, do prod02 as well",
        ],
    },
    {
        "name": "teaching_conversation",
        "turns": [
            ("task_request", "Execute + explain"),
            ("why_question", "Teach the concept"),
            ("follow_up", "Expand knowledge"),
        ],
        "example": [
            "find large files",
            "why did you use -h flag?",
            "what about hidden files?",
        ],
    },
    {
        "name": "troubleshooting_journey",
        "turns": [
            ("symptom_report", "Start diagnosis"),
            ("observation_1", "Investigate further"),
            ("observation_2", "Identify root cause"),
            ("resolution", "Fix and verify"),
        ],
        "example": [
            "the app is slow",
            "looks like high cpu",
            "it's the search indexer",
            "let me restart it",
        ],
    },
]


# =============================================================================
# CORE GENERATOR CLASS
# =============================================================================

@dataclass
class ConversationTurn:
    role: str  # user, assistant
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_results: Optional[List[Dict]] = None
    metadata: Dict = field(default_factory=dict)


@dataclass  
class TrainingExample:
    messages: List[ConversationTurn]
    user_persona: str
    scenario_category: str
    tools_used: List[str]
    personality_elements_used: List[str]
    source: str  # "generated", "chat_export", "augmented"


def convert_chat_export_to_training(chat_export_path: Path) -> List[TrainingExample]:
    """
    Convert Open-WebUI chat export to training examples.
    
    Extracts successful interactions and adds annotations for:
    - Tool calls that worked
    - Conversational patterns that flowed well
    - User tone and AJ's adaptation
    """
    examples = []
    
    with open(chat_export_path) as f:
        exports = json.load(f)
    
    for chat_data in exports:
        chat = chat_data.get("chat", {})
        messages = chat.get("messages", [])
        
        if not messages:
            continue
        
        # Extract conversation turns
        turns = []
        tools_used = set()
        
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            # Parse tool outputs from content
            tool_calls = []
            if "output:**" in content:
                # Extract tool call patterns like "**list_agents output:**"
                tool_matches = re.findall(r'\*\*(\w+) output:\*\*', content)
                tools_used.update(tool_matches)
                tool_calls = [{"tool": t} for t in tool_matches]
            
            turns.append(ConversationTurn(
                role=role,
                content=content,
                tool_calls=tool_calls if tool_calls else None,
            ))
        
        if len(turns) >= 2:
            # Analyze user tone
            user_content = " ".join(t.content for t in turns if t.role == "user")
            persona = _detect_user_persona(user_content)
            
            examples.append(TrainingExample(
                messages=turns,
                user_persona=persona,
                scenario_category=_detect_scenario(user_content),
                tools_used=list(tools_used),
                personality_elements_used=[],  # TODO: detect from assistant responses
                source="chat_export",
            ))
    
    return examples


def _detect_user_persona(user_content: str) -> str:
    """Detect user persona from their messages."""
    content_lower = user_content.lower()
    
    if any(word in content_lower for word in ["yo", "lol", "ngl", "u ", "gonna"]):
        return "casual_developer"
    elif any(word in content_lower for word in ["help", "now", "urgent", "asap", "down"]):
        return "stressed_oncall"
    elif any(word in content_lower for word in ["why", "how does", "explain", "what does"]):
        return "curious_learner"
    elif any(word in content_lower for word in ["status", "overview", "summary"]):
        return "executive_brief"
    else:
        return "senior_engineer"


def _detect_scenario(user_content: str) -> str:
    """Detect scenario category from user messages."""
    content_lower = user_content.lower()
    
    if any(word in content_lower for word in ["cpu", "memory", "slow", "process"]):
        return "process_hunting"
    elif any(word in content_lower for word in ["disk", "space", "storage"]):
        return "disk_space"
    elif any(word in content_lower for word in ["agent", "online", "server", "status"]):
        return "multi_agent_health"
    elif any(word in content_lower for word in ["log", "error", "grep"]):
        return "log_investigation"
    elif any(word in content_lower for word in ["restart", "stop", "start", "service"]):
        return "service_management"
    else:
        return "targeted_diagnosis"


# =============================================================================
# CLAUDE-POWERED GENERATION
# =============================================================================

GENERATION_SYSTEM_PROMPT = """You are generating training data for AJ, an AI assistant with these capabilities:

TOOLS:
- bash: Local command execution (docker, git, npm, etc.)
- remote_bash: Execute on ONE FunnelCloud agent (requires agent_id)
- remote_bash_all: Execute SAME command on ALL agents (parallel)
- list_agents: Discover available FunnelCloud agents
- think: Internal reasoning step
- complete: Signal task completion with answer

AJ'S PERSONALITY:
- Warm but efficient - not robotic, not over-the-top friendly
- Adapts to user's tone (casual user = casual response, stressed user = calm reassurance)
- Uses figures of speech naturally ("Let me dig into this", "Here's the breakdown")
- Shows personality through word choice, not emoji spam
- Technical accuracy is paramount - personality never overrides correctness
- Remembers context within conversation
- Proactively suggests related actions ("Want me to check the other servers too?")

RESPONSE FORMAT:
When generating training examples, output JSON with this structure:
{
  "messages": [
    {"role": "user", "content": "user message"},
    {"role": "assistant", "content": "AJ response with personality", "tool_calls": [...] if any}
  ],
  "user_persona": "casual_developer|senior_engineer|stressed_oncall|curious_learner|executive_brief",
  "scenario_category": "category name",
  "personality_notes": "what personality elements were used"
}

TOOL CALL FORMAT (in assistant content):
Include tool calls as: {"tool": "name", "params": {...}, "reasoning": "why"}

USER PERSONAS:
- casual_developer: Informal, uses slang → AJ: Relaxed but precise
- senior_engineer: Technical, concise → AJ: No fluff, shows work
- stressed_oncall: Urgent, stressed → AJ: Calm, immediate action
- curious_learner: Asks questions → AJ: Educational, explains reasoning  
- executive_brief: Wants summaries → AJ: Executive summary first

IMPORTANT:
- Show realistic tool outputs (not just "success")
- Include multi-step reasoning for complex tasks
- Balance personality with efficiency
- Never sacrifice accuracy for personality"""


def generate_with_claude(
    scenario: Dict,
    persona: Dict,
    client: "anthropic.Anthropic",
    multi_turn: bool = False
) -> Optional[TrainingExample]:
    """Generate a training example using Claude."""
    
    user_prompt = random.choice(scenario["user_prompts"])
    
    # Fill in any placeholders
    if "{agent}" in user_prompt:
        agents = ["ians-r16", "domain01", "r730xd", "exchange01", "webprod01"]
        user_prompt = user_prompt.replace("{agent}", random.choice(agents))
    
    generation_prompt = f"""Generate a training example for this scenario:

USER PERSONA: {persona['name']}
User tone: {persona['tone']}
AJ response style: {persona['aj_response_style']}

SCENARIO: {scenario['category']}
Required tools: {scenario['required_tools']}
Expected flow: {scenario['expected_flow']}

USER MESSAGE: "{user_prompt}"

Generate a realistic, complete interaction showing:
1. AJ acknowledging the request appropriately for this persona
2. Tool calls with realistic outputs
3. Final response with appropriate personality

Output as JSON."""

    if multi_turn:
        pattern = random.choice(MULTI_TURN_PATTERNS)
        generation_prompt += f"""

Make this a MULTI-TURN conversation following the "{pattern['name']}" pattern:
{json.dumps(pattern['turns'], indent=2)}

Example flow: {pattern['example']}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=GENERATION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": generation_prompt}]
        )
        
        # Extract JSON from response
        response_text = response.content[0].text
        
        # Find JSON block
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            data = json.loads(json_match.group())
            
            messages = [
                ConversationTurn(
                    role=m.get("role"),
                    content=m.get("content"),
                    tool_calls=m.get("tool_calls"),
                    tool_results=m.get("tool_results"),
                )
                for m in data.get("messages", [])
            ]
            
            return TrainingExample(
                messages=messages,
                user_persona=data.get("user_persona", persona["name"]),
                scenario_category=scenario["category"],
                tools_used=scenario["required_tools"],
                personality_elements_used=data.get("personality_notes", "").split(", "),
                source="generated",
            )
    except Exception as e:
        print(f"  Error generating: {e}")
    
    return None


def generate_batch(
    count: int,
    output_dir: Path,
    client: "anthropic.Anthropic",
    multi_turn_ratio: float = 0.3,
) -> List[TrainingExample]:
    """Generate a batch of training examples."""
    
    examples = []
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "conversational_agentic.jsonl"
    
    with open(output_file, "a") as f:
        for i in range(count):
            # Select random scenario and persona
            scenario = random.choice(AGENTIC_SCENARIOS)
            persona = random.choice(USER_PERSONAS)
            multi_turn = random.random() < multi_turn_ratio
            
            print(f"[{i+1}/{count}] {scenario['category']} + {persona['name']} (multi_turn={multi_turn})")
            
            example = generate_with_claude(scenario, persona, client, multi_turn)
            
            if example:
                examples.append(example)
                
                # Convert to training format
                training_record = {
                    "messages": [
                        {
                            "role": t.role,
                            "content": t.content,
                            **({"tool_calls": t.tool_calls} if t.tool_calls else {}),
                        }
                        for t in example.messages
                    ],
                    "metadata": {
                        "user_persona": example.user_persona,
                        "scenario": example.scenario_category,
                        "tools": example.tools_used,
                        "personality": example.personality_elements_used,
                        "source": example.source,
                    }
                }
                
                f.write(json.dumps(training_record) + "\n")
                print(f"  ✓ Generated {len(example.messages)} turns")
            else:
                print(f"  ✗ Failed")
    
    print(f"\nGenerated {len(examples)} examples → {output_file}")
    return examples


def augment_existing_dataset(
    input_file: Path,
    output_file: Path,
    client: "anthropic.Anthropic",
    sample_size: int = 100,
) -> None:
    """
    Take existing agentic examples and add conversational personality.
    
    This preserves the correct tool usage while making responses more human.
    """
    
    augmentation_prompt = """Take this existing training example and enhance the assistant's 
response with more conversational personality while keeping the exact same tool calls and accuracy:

ORIGINAL:
{original}

ENHANCED VERSION REQUIREMENTS:
- Keep ALL tool calls exactly the same
- Keep technical accuracy 100%
- Add personality: acknowledgment phrase, natural transitions, optional follow-up offer
- Match the implied user tone
- Don't add emoji unless user seems casual

Output the enhanced example as JSON."""

    with open(input_file) as f:
        lines = f.readlines()
    
    # Sample
    if len(lines) > sample_size:
        lines = random.sample(lines, sample_size)
    
    augmented = []
    
    for i, line in enumerate(lines):
        original = json.loads(line)
        
        print(f"[{i+1}/{len(lines)}] Augmenting...")
        
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{
                    "role": "user", 
                    "content": augmentation_prompt.format(original=json.dumps(original, indent=2))
                }]
            )
            
            response_text = response.content[0].text
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            
            if json_match:
                enhanced = json.loads(json_match.group())
                enhanced["metadata"] = enhanced.get("metadata", {})
                enhanced["metadata"]["source"] = "augmented"
                enhanced["metadata"]["original_source"] = original.get("source", "unknown")
                augmented.append(enhanced)
                print(f"  ✓ Enhanced")
            else:
                print(f"  ✗ No JSON in response")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    with open(output_file, "w") as f:
        for item in augmented:
            f.write(json.dumps(item) + "\n")
    
    print(f"\nAugmented {len(augmented)} examples → {output_file}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate conversational agentic training data")
    parser.add_argument("--count", type=int, default=100, help="Number of examples to generate")
    parser.add_argument("--output", type=Path, default=Path("../data"), help="Output directory")
    parser.add_argument("--from-chat-export", type=Path, help="Convert chat export to training data")
    parser.add_argument("--augment-existing", type=Path, help="Augment existing dataset with personality")
    parser.add_argument("--multi-turn-ratio", type=float, default=0.3, help="Ratio of multi-turn examples")
    
    args = parser.parse_args()
    
    if args.from_chat_export:
        print(f"Converting chat export: {args.from_chat_export}")
        examples = convert_chat_export_to_training(args.from_chat_export)
        
        output_file = args.output / "from_chat_export.jsonl"
        args.output.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w") as f:
            for ex in examples:
                record = {
                    "messages": [{"role": t.role, "content": t.content} for t in ex.messages],
                    "metadata": {
                        "user_persona": ex.user_persona,
                        "scenario": ex.scenario_category,
                        "tools": ex.tools_used,
                        "source": ex.source,
                    }
                }
                f.write(json.dumps(record) + "\n")
        
        print(f"Converted {len(examples)} conversations → {output_file}")
        return
    
    if not ANTHROPIC_AVAILABLE:
        print("ERROR: anthropic package not installed. Run: pip install anthropic")
        return
    
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var
    
    if args.augment_existing:
        output_file = args.output / "augmented_with_personality.jsonl"
        augment_existing_dataset(args.augment_existing, output_file, client)
        return
    
    # Generate new examples
    generate_batch(
        count=args.count,
        output_dir=args.output,
        client=client,
        multi_turn_ratio=args.multi_turn_ratio,
    )


if __name__ == "__main__":
    main()
