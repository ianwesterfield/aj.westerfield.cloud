#!/usr/bin/env python3
"""
Generate CLI-centric training data using Claude API.

Philosophy: "All you need is the command line" - teaches the model to solve 
problems with shell commands on BOTH Windows (PowerShell/CMD) and Linux (Bash).

Usage:
    export ANTHROPIC_API_KEY="your-key"
    python generate_bash_knowledge.py --category linux_cli --count 500
    python generate_bash_knowledge.py --category windows_cli --count 500
    python generate_bash_knowledge.py --category all --count 200
"""

import argparse
import json
import os
import random
import time
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

try:
    import anthropic
except ImportError:
    print("pip install anthropic")
    exit(1)

# Thread-safe counter for progress
progress_lock = threading.Lock()
progress_count = 0

# Generation categories with prompts and seed topics
CATEGORIES = {
    "linux_cli": {
        "description": "Linux/Unix command line mastery (Bash, sh, zsh)",
        "output_file": "linux_cli_generated.jsonl",
        "topics": [
            "Process management (ps, top, htop, kill, nice, nohup)",
            "File operations (find, xargs, chmod, chown, ln, tar, rsync)",
            "Text processing (grep, sed, awk, cut, sort, uniq, tr, head, tail)",
            "Disk and storage (df, du, mount, fdisk, lsblk, dd)",
            "Network diagnostics (netstat, ss, lsof, tcpdump, curl, wget, nc)",
            "System monitoring (vmstat, iostat, sar, dmesg, journalctl)",
            "User management (useradd, usermod, passwd, groups, sudo)",
            "Service management (systemctl, service, cron, at)",
            "Log analysis (journalctl, /var/log, logrotate)",
            "SSH operations (ssh, scp, ssh-keygen, ssh-agent, tunneling)",
            "Package management (apt, yum, dnf, snap)",
            "Environment variables and shell configuration (.bashrc, .profile)",
            "Bash scripting patterns (loops, conditionals, functions, arrays)",
            "Pipeline composition for complex data transformations",
            "Docker CLI (build, run, exec, logs, compose, volume, network)",
            "Git command line operations",
        ]
    },
    "windows_cli": {
        "description": "Windows command line mastery (PowerShell and CMD)",
        "output_file": "windows_cli_generated.jsonl",
        "topics": [
            "PowerShell object pipeline (Get-*, Select-Object, Where-Object, ForEach-Object)",
            "PowerShell file operations (Get-ChildItem, Copy-Item, Move-Item, Remove-Item)",
            "PowerShell text processing (Select-String, -match, -replace, ConvertFrom-*)",
            "PowerShell remoting (Enter-PSSession, Invoke-Command, WinRM)",
            "PowerShell process management (Get-Process, Stop-Process, Start-Process)",
            "PowerShell service management (Get-Service, Start-Service, Stop-Service)",
            "PowerShell registry operations (Get-ItemProperty, Set-ItemProperty, HKLM:, HKCU:)",
            "PowerShell Active Directory (Get-ADUser, Get-ADGroup, Get-ADComputer)",
            "PowerShell network diagnostics (Test-Connection, Test-NetConnection, Resolve-DnsName)",
            "PowerShell event log analysis (Get-EventLog, Get-WinEvent)",
            "PowerShell scheduled tasks (Get-ScheduledTask, Register-ScheduledTask)",
            "PowerShell WMI/CIM queries (Get-CimInstance, Get-WmiObject)",
            "CMD basics (dir, copy, move, del, robocopy, xcopy, attrib)",
            "CMD batch scripting (for loops, if statements, call, setlocal)",
            "Windows package management (winget, choco, scoop)",
            "WSL interop (wsl, wslpath, running Linux commands from Windows)",
        ]
    },
    "cross_platform_cli": {
        "description": "Cross-platform CLI patterns - same task, both OSes",
        "output_file": "cross_platform_cli_generated.jsonl",
        "topics": [
            "Find files by name or content (find/grep vs Get-ChildItem/Select-String)",
            "Process management across platforms",
            "Service/daemon management comparison",
            "User and permission management differences",
            "Network diagnostics equivalents",
            "Environment variables (export vs $env:)",
            "Path manipulation differences (/ vs \\, PATH vs Path)",
            "Text file processing and encoding",
            "Compression and archiving (tar/gzip vs Compress-Archive)",
            "Remote execution patterns (SSH vs WinRM)",
            "Package management comparison",
            "Docker CLI (same on both platforms)",
            "Git CLI (same on both platforms)",
            "Python/Node CLI operations (cross-platform)",
            "Translating bash scripts to PowerShell and vice versa",
            "Handling line endings and encoding differences",
        ]
    },
    "devops_cli": {
        "description": "DevOps automation via command line (both platforms)",
        "output_file": "devops_cli_generated.jsonl",
        "topics": [
            "Docker operations (build, run, exec, logs, compose, multi-stage)",
            "Container debugging and inspection",
            "Git workflows via CLI (branch, merge, rebase, cherry-pick, bisect)",
            "CI/CD scripting patterns",
            "Database CLI tools (psql, mysql, mongosh, redis-cli, sqlcmd)",
            "Cloud CLI tools (az, aws, gcloud, doctl)",
            "Kubernetes CLI (kubectl basics)",
            "Infrastructure automation scripts",
            "Secrets and credential management via CLI",
            "Health checks and monitoring scripts",
            "Log aggregation and analysis",
            "Certificate management (openssl, certbot)",
        ]
    },
    "mesosync_patterns": {
        "description": "AJ/Mesosync architecture - CLI-first, Human-in-the-Loop",
        "output_file": "mesosync_generated.jsonl",
        "topics": [
            # Core Philosophy
            "CLI-first execution: bash on Linux, PowerShell on Windows - no function calling",
            "Human-in-the-Loop: when to pause and confirm vs when to proceed autonomously",
            "Minimizing tool dependencies: file ops via cat/echo/sed, not specialized handlers",
            "LLM generates commands, system executes them - clean separation",
            
            # OODA Loop Implementation
            "OODA loop: Observe phase - gathering context from user and environment",
            "OODA loop: Orient phase - analyzing intent, classifying task vs conversational",
            "OODA loop: Decide phase - generating bash/PowerShell commands",
            "OODA loop: Act phase - executing commands, capturing results",
            "OODA loop: iteration and replanning when commands fail or results unexpected",
            
            # Multi-Agent Architecture
            "FunnelCloud agent discovery via UDP broadcast on local network",
            "Remote command execution: remote_bash to single agent vs remote_bash_all for parallel",
            "Agent identification: matching user descriptions to known machine names",
            "Cross-platform remote execution: bash commands to Linux, PowerShell to Windows agents",
            "Graceful degradation when agents are unavailable",
            
            # Memory and Context
            "Semantic memory: storing facts about user preferences, machine names, paths",
            "Episodic memory: recalling previous conversation context",
            "Context window optimization: maximizing user context, minimizing system overhead",
            "Memory-assisted agent resolution: 'my workstation' -> remembered machine name",
            
            # Session State Management
            "External state management: LLM is stateless, SessionState tracks everything",
            "Conversation threading and multi-turn context preservation",
            "Workspace context: cwd, allowed operations, parallelism limits",
            "Step tracking and execution history for debugging",
            
            # Streaming and UX
            "Streaming responses: <think> tags for reasoning, JSON for tool calls",
            "Thinking output parsing: extracting reasoning from <think>...</think>",
            "Progressive status updates during long-running operations",
            
            # Error Handling and Safety
            "Command failure recovery: retry, replan, or escalate to user",
            "Timeout handling for long-running bash commands",
            "Permission errors and elevation requirements (sudo, Run as Administrator)",
            "Dangerous operation detection and confirmation prompts",
            
            # Docker Compose Orchestration
            "Service startup order and health checks in docker-compose",
            "Inter-service communication: gRPC between orchestrator and agents",
            "Volume mounting for workspace access",
            "Environment variable injection for configuration",
        ]
    },
    "cannabis_cultivation": {
        "description": "Cannabis cultivation techniques and best practices",
        "output_file": "cannabis_cultivation_generated.jsonl",
        "topics": [
            "Indoor grow room setup (lighting, ventilation, environmental controls)",
            "LED vs HPS vs CMH lighting comparison and optimization",
            "VPD (Vapor Pressure Deficit) management for optimal growth",
            "Nutrient schedules for vegetative and flowering stages",
            "pH and EC/PPM management in different growing media",
            "Soil vs coco coir vs hydroponic growing methods",
            "Training techniques (LST, HST, topping, FIM, SCROG, SOG)",
            "Pest identification and integrated pest management (IPM)",
            "Disease prevention and treatment (powdery mildew, root rot, etc.)",
            "Cloning and mother plant maintenance",
            "Seed germination and seedling care",
            "Flowering stage optimization and timing",
            "Environmental automation (climate controllers, timers, sensors)",
            "Water quality and filtration requirements",
            "Organic vs synthetic nutrient approaches",
            "Troubleshooting common deficiencies and toxicities",
        ]
    },
    "cannabis_processing": {
        "description": "Cannabis harvesting, processing, and extraction",
        "output_file": "cannabis_processing_generated.jsonl",
        "topics": [
            "Harvest timing (trichome assessment, amber vs cloudy)",
            "Wet trim vs dry trim techniques",
            "Drying room setup and optimal conditions",
            "Curing process and jar burping schedules",
            "Long-term storage and preservation methods",
            "Solventless extraction (rosin press, bubble hash, dry sift)",
            "Solvent-based extraction overview (BHO, CO2, ethanol)",
            "Decarboxylation science and methods",
            "Edible preparation and dosing calculations",
            "Tincture and oil infusion techniques",
            "Quality control and testing parameters",
            "Terpene preservation during processing",
            "Concentrate consistency types (shatter, wax, budder, live resin)",
            "Post-harvest plant material handling",
            "Equipment maintenance and cleaning protocols",
        ]
    },
    "cannabis_science": {
        "description": "Cannabis science, cannabinoids, and therapeutic applications",
        "output_file": "cannabis_science_generated.jsonl",
        "topics": [
            "Cannabinoid profiles (THC, CBD, CBG, CBN, CBC, THCV, etc.)",
            "The endocannabinoid system (ECS) and receptor mechanisms",
            "Terpene profiles and the entourage effect",
            "Cannabis chemovars (chemotypes) vs strain names",
            "Therapeutic applications and current research",
            "Dosing considerations for different consumption methods",
            "Bioavailability differences (inhalation, oral, sublingual, topical)",
            "Drug interactions and contraindications",
            "Tolerance, dependence, and responsible use",
            "Cannabis genetics and breeding basics",
            "Landrace strains and genetic origins",
            "Lab testing interpretation (potency, terpenes, contaminants)",
            "Microdosing protocols and benefits",
            "Indica vs Sativa vs hybrid (myths and science)",
            "Medical conditions and cannabinoid research",
            "Consumption method comparison (flower, vape, edible, topical)",
        ]
    },
    "aj_persona_behaviors": {
        "description": "AJ persona, system prompt behaviors, and interaction patterns",
        "output_file": "aj_persona_generated.jsonl",
        "topics": [
            # CLI-First Philosophy in Action
            "Responding to 'read this file' with cat/Get-Content instead of a tool call",
            "Responding to 'write to file' with echo/Set-Content instead of a tool call",
            "Explaining why CLI approach is preferred over specialized tools",
            "Converting a function-calling request to equivalent bash/PowerShell",
            
            # Human-in-the-Loop Examples
            "Pausing to confirm before rm -rf or Remove-Item -Recurse",
            "Asking for clarification when machine identity is ambiguous",
            "Proceeding autonomously for read-only operations in user's workspace",
            "Explaining reasoning before executing a complex multi-step plan",
            "Detecting potentially dangerous operations and requesting confirmation",
            
            # Context and Memory Usage
            "Referencing a machine name the user mentioned earlier in conversation",
            "Remembering user's preferred text editor or shell",
            "Using project structure knowledge from previous interactions",
            "Recognizing when to ask vs when to use remembered context",
            
            # Response Format Excellence
            "Formatting command output in proper code blocks",
            "Using inline backticks for paths, commands, and variables",
            "Providing concise explanations without unnecessary caveats",
            "Structuring multi-step instructions clearly",
            
            # Error Handling Gracefully
            "Analyzing a 'permission denied' error and suggesting sudo/elevation",
            "Handling 'command not found' by suggesting installation",
            "Recovering from a failed command with an alternative approach",
            "Knowing when to retry vs when to ask the user for help",
            
            # Multi-Agent Coordination
            "Discovering agents before remote execution",
            "Matching 'my laptop' to a known machine name from memory",
            "Explaining parallel vs sequential remote execution choice",
            "Handling agent unavailability gracefully",
            
            # Conversational vs Task Classification
            "Recognizing 'what is X?' as conversational, answering directly",
            "Recognizing 'list files in X' as task, executing commands",
            "Handling ambiguous requests by asking clarifying questions",
            "Smoothly transitioning between conversation and task execution",
        ]
    },
}

SYSTEM_PROMPT = """You are an expert in command-line operations on BOTH Windows and Linux systems.
Your philosophy is "All you need is the command line" - you solve problems elegantly with 
shell commands, pipelines, and scripts rather than relying on GUI tools or complex frameworks.

You are fluent in:
- Linux/Unix: Bash, sh, zsh, common Unix utilities
- Windows: PowerShell (preferred), CMD batch scripting
- Cross-platform tools: Docker, Git, Python CLI, Node CLI

When generating training examples:
1. Provide realistic, practical scenarios
2. Show the thought process: why this approach?
3. Use idiomatic commands for the target OS
4. Include error handling where appropriate
5. Explain non-obvious commands, flags, or syntax
6. Prefer composable solutions over monolithic scripts
7. When relevant, show how to do the same thing on both Windows and Linux

Format your response as a conversation between a user asking a question and an assistant
providing a helpful, educational answer with working commands."""

# Robust system prompt for AJ - this is what gets baked into training
AJ_SYSTEM_PROMPT = """You are AJ, an AI assistant specializing in coding, infrastructure, and general conversation.

EXECUTION PHILOSOPHY: "All You Need is the Command Line"
- Generate bash commands (Linux) or PowerShell commands (Windows) for ALL operations
- No function calling, no specialized tools - just shell commands
- File operations: cat, echo, sed, awk (Linux) or Get-Content, Set-Content (Windows)
- Code execution: python3 -c "...", node -e "...", pwsh -c "..."
- The LLM generates commands, the system executes them - clean separation

HUMAN-IN-THE-LOOP PRINCIPLES:
- ALWAYS confirm before: destructive operations (rm -rf, Remove-Item -Recurse), system changes, remote execution on unfamiliar machines
- Proceed autonomously for: read-only operations, user's own workspace, explicitly approved patterns
- When uncertain about machine identity: ASK, don't assume
- Surface your reasoning so the user can verify your plan

CONTEXT WINDOW OPTIMIZATION:
- Prioritize user context over system boilerplate
- Remember facts the user tells you (machine names, preferences, project structure)
- Reference previous conversation context when relevant
- Keep responses focused - don't repeat information the user already knows

MULTI-AGENT OPERATIONS:
- Discover agents before executing remote commands
- Match user descriptions ("my workstation", "the server") to known machine names from memory
- Use parallel execution (remote_bash_all) for "each agent", "all machines"
- Use sequential execution for different commands per target

RESPONSE FORMAT:
- Use proper Markdown formatting
- Wrap code and command output in fenced code blocks (```)
- Use backticks for inline `file paths`, `commands`, `variables`
- Explain your reasoning, especially for complex multi-step operations
- Be concise but thorough - don't pad responses with unnecessary caveats

ERROR HANDLING:
- If a command fails, analyze the error and suggest fixes
- Consider common issues: permissions, path not found, network connectivity
- Offer alternatives when the primary approach doesn't work
- Know when to escalate to the user vs retry autonomously"""

USER_TEMPLATE = """Generate a training example about: {topic}

The example should be a realistic question a developer, sysadmin, or DevOps engineer might ask,
followed by a thorough answer that demonstrates command-line mastery.

Return ONLY valid JSON in this exact format:
{{
  "messages": [
    {{"role": "user", "content": "the realistic question"}},
    {{"role": "assistant", "content": "the helpful answer with commands and explanation"}}
  ]
}}"""


def extract_json_from_response(content: str) -> Dict:
    """
    Extract JSON from Claude's response, handling various formats.
    Claude often wraps JSON in markdown code blocks or adds extra text.
    """
    import re
    
    # Try direct parse first
    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        pass
    
    # Try extracting from ```json ... ``` blocks
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            pass
    
    # Try extracting from ``` ... ``` blocks (no language specified)
    code_match = re.search(r'```\s*([\s\S]*?)\s*```', content)
    if code_match:
        try:
            return json.loads(code_match.group(1).strip())
        except json.JSONDecodeError:
            pass
    
    # Try finding JSON object pattern { ... }
    # Find the first { and last } to extract potential JSON
    first_brace = content.find('{')
    last_brace = content.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        potential_json = content[first_brace:last_brace + 1]
        try:
            return json.loads(potential_json)
        except json.JSONDecodeError:
            pass
    
    # Nothing worked
    raise json.JSONDecodeError("Could not extract valid JSON from response", content, 0)


def generate_single_example(
    client: anthropic.Anthropic,
    topic: str,
    category: str,
    system_prompt: str,
    user_template: str,
    model: str,
    total_count: int,
    max_retries: int = 3,
) -> Dict:
    """Generate a single training example with retry logic for rate limits."""
    global progress_count
    
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=2000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_template.format(topic=topic)}
                ]
            )
            
            content = response.content[0].text
            example = extract_json_from_response(content)
            
            if "messages" in example and len(example["messages"]) >= 2:
                example["_source"] = f"claude_generated_{category}"
                example["_topic"] = topic
                
                with progress_lock:
                    progress_count += 1
                    print(f"  [{progress_count}/{total_count}] ✓ {topic[:45]}...")
                
                return example
            else:
                with progress_lock:
                    progress_count += 1
                    print(f"  [{progress_count}/{total_count}] ⚠ Invalid structure: {topic[:35]}...")
                return None
                
        except anthropic.RateLimitError as e:
            # Exponential backoff for rate limits
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            if attempt < max_retries - 1:
                time.sleep(wait_time)
                continue
            else:
                with progress_lock:
                    progress_count += 1
                    print(f"  [{progress_count}/{total_count}] ⚠ Rate limit (retries exhausted): {topic[:30]}...")
                return None
        except json.JSONDecodeError as e:
            with progress_lock:
                progress_count += 1
                print(f"  [{progress_count}/{total_count}] ⚠ JSON error: {topic[:40]}...")
            return None
        except Exception as e:
            # Check if it's a 429 in the error message
            if "429" in str(e) or "rate" in str(e).lower():
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    continue
            with progress_lock:
                progress_count += 1
                print(f"  [{progress_count}/{total_count}] ⚠ {str(e)[:30]}: {topic[:30]}...")
            return None
    
    return None


def generate_examples(
    client: anthropic.Anthropic,
    category: str,
    count: int,
    model: str = "claude-sonnet-4-20250514",
    max_workers: int = 10,
) -> List[Dict]:
    """Generate training examples for a category using parallel API calls."""
    global progress_count
    progress_count = 0
    
    config = CATEGORIES[category]
    topics = config["topics"]
    
    # Use AJ-specific system prompt for mesosync and persona categories
    if category in ["mesosync_patterns", "aj_persona_behaviors"]:
        system_prompt = AJ_SYSTEM_PROMPT + """

When generating training examples for this category:
1. The assistant should demonstrate the AJ persona and behaviors
2. Show CLI-first thinking - generate bash/PowerShell, not function calls
3. Demonstrate Human-in-the-Loop principles where appropriate
4. Use proper markdown formatting in responses
5. Show memory/context awareness when relevant"""
        user_template = """Generate a training example demonstrating: {topic}

The example should show a realistic interaction where the AI assistant (AJ) demonstrates 
the described behavior. Include the user's request and AJ's response showing proper CLI-first,
Human-in-the-Loop, and context-aware patterns.

Return ONLY valid JSON in this exact format:
{{
  "messages": [
    {{"role": "user", "content": "the user's realistic request"}},
    {{"role": "assistant", "content": "AJ's response demonstrating the behavior"}}
  ]
}}"""
    else:
        system_prompt = SYSTEM_PROMPT
        user_template = USER_TEMPLATE
    
    # Build task list - repeat topics to reach count
    tasks = []
    examples_per_topic = max(1, count // len(topics))
    for topic in topics:
        for _ in range(examples_per_topic):
            if len(tasks) < count:
                tasks.append(topic)
    
    print(f"\nGenerating {len(tasks)} examples for: {category} ({max_workers} parallel workers)")
    print(f"Topics: {len(topics)}, {examples_per_topic} examples each")
    
    examples = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                generate_single_example,
                client, topic, category, system_prompt, user_template, model, len(tasks)
            )
            for topic in tasks
        ]
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                examples.append(result)
    
    print(f"  Completed: {len(examples)}/{len(tasks)} successful")
    return examples


def save_examples(examples: List[Dict], output_path: Path):
    """Save examples to JSONL file."""
    
    # Remove internal tags before saving
    clean_examples = []
    for ex in examples:
        clean = {k: v for k, v in ex.items() if not k.startswith("_")}
        clean_examples.append(clean)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for ex in clean_examples:
            f.write(json.dumps(ex) + "\n")
    
    print(f"\nSaved {len(clean_examples)} examples to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate CLI-centric training data")
    parser.add_argument("--category", type=str, default="all",
                       choices=list(CATEGORIES.keys()) + ["all"],
                       help="Category to generate")
    parser.add_argument("--count", type=int, default=100,
                       help="Number of examples per category")
    parser.add_argument("--output-dir", type=str, default="../data",
                       help="Output directory for generated files")
    parser.add_argument("--model", type=str, default="claude-sonnet-4-20250514",
                       help="Claude model to use")
    parser.add_argument("--workers", type=int, default=10,
                       help="Number of parallel API workers (default: 10)")
    
    args = parser.parse_args()
    
    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # Try reading from secrets file
        secrets_path = Path(__file__).parent.parent.parent / "secrets" / "anthropic_key.txt"
        if secrets_path.exists():
            api_key = secrets_path.read_text().strip()
        else:
            print("Error: ANTHROPIC_API_KEY not set and secrets/anthropic_key.txt not found")
            exit(1)
    
    client = anthropic.Anthropic(api_key=api_key)
    output_dir = Path(__file__).parent / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    categories = list(CATEGORIES.keys()) if args.category == "all" else [args.category]
    
    print("="*60)
    print("CLI Knowledge Generator (Parallel)")
    print(f"Model: {args.model}")
    print(f"Categories: {len(categories)}")
    print(f"Count per category: {args.count}")
    print(f"Parallel workers: {args.workers}")
    print(f"Total examples: {len(categories) * args.count}")
    print("="*60)
    
    total_generated = 0
    
    for category in categories:
        config = CATEGORIES[category]
        output_path = output_dir / config["output_file"]
        
        examples = generate_examples(
            client=client,
            category=category,
            count=args.count,
            model=args.model,
            max_workers=args.workers,
        )
        
        if examples:
            save_examples(examples, output_path)
            total_generated += len(examples)
    
    print("\n" + "="*60)
    print(f"Generation complete! Total: {total_generated} examples")
    print("="*60)


if __name__ == "__main__":
    main()
