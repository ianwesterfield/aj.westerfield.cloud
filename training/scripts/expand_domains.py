#!/usr/bin/env python3
"""
Domain Data Expander

Expands training data for domains that are under a target count.
Uses templates and LLM-assisted generation to reach target.

Usage:
    python expand_domains.py --target 100 --output-dir ../data/
    python expand_domains.py --domain python_development --target 150
    python expand_domains.py --use-llm --llm-count 50
"""

import json
import random
import argparse
from pathlib import Path
from typing import List, Dict, Generator, Optional, Tuple
from collections import defaultdict

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

SYSTEM_PROMPT = "You are AJ, a helpful AI assistant."

# Domain-specific knowledge for expansion
DOMAIN_TEMPLATES = {
    "python_development": {
        "topics": [
            "list comprehensions", "dictionary comprehensions", "generators",
            "context managers", "dataclasses", "enums", "abstract base classes",
            "metaclasses", "descriptors", "slots", "weakref", "functools",
            "itertools", "collections", "pathlib", "argparse", "logging",
            "unittest", "pytest", "mock", "coverage", "typing", "mypy",
            "pydantic", "attrs", "poetry", "setuptools", "pip", "virtualenv",
            "multiprocessing", "threading", "asyncio", "concurrent.futures",
            "subprocess", "os", "sys", "re", "json", "yaml", "toml",
        ],
        "question_patterns": [
            "How do I use {topic} in Python?",
            "What's the best way to {action} in Python?",
            "Can you explain Python {topic}?",
            "Python {topic} example",
            "When should I use {topic}?",
        ],
        "actions": [
            "read a file", "write to a file", "parse JSON", "handle exceptions",
            "create a class", "use inheritance", "implement a decorator",
            "work with dates", "make HTTP requests", "connect to a database",
            "run async code", "use environment variables", "parse arguments",
            "create a package", "write tests", "debug code", "profile performance",
        ]
    },
    "typescript_development": {
        "topics": [
            "interfaces", "types", "generics", "union types", "intersection types",
            "type guards", "type assertions", "mapped types", "conditional types",
            "utility types", "decorators", "modules", "namespaces", "enums",
            "classes", "abstract classes", "access modifiers", "readonly",
            "optional properties", "index signatures", "function overloads",
            "type inference", "strict mode", "declaration files", "triple-slash directives",
        ],
        "question_patterns": [
            "How do TypeScript {topic} work?",
            "What's the difference between {topic} in TypeScript?",
            "TypeScript {topic} example",
            "When to use {topic} vs {topic2}?",
            "Best practices for TypeScript {topic}",
        ],
        "comparisons": [
            ("interface", "type"),
            ("any", "unknown"),
            ("enum", "union type"),
            ("class", "interface"),
        ]
    },
    "docker_containerization": {
        "topics": [
            "Dockerfile", "docker-compose", "images", "containers", "volumes",
            "networks", "multi-stage builds", "build cache", "layer optimization",
            "health checks", "environment variables", "secrets", "configs",
            "swarm", "stack", "services", "replicas", "rolling updates",
            "resource limits", "logging", "monitoring", "security scanning",
        ],
        "question_patterns": [
            "How do I {action} with Docker?",
            "Docker {topic} best practices",
            "What's the difference between {topic} and {topic2}?",
            "Optimize Docker {topic}",
            "Troubleshoot Docker {topic}",
        ],
        "actions": [
            "reduce image size", "speed up builds", "handle secrets",
            "persist data", "connect containers", "debug a container",
            "view logs", "limit resources", "set up health checks",
            "use multi-stage builds", "cache dependencies", "run as non-root",
        ]
    },
    "git_version_control": {
        "topics": [
            "branches", "commits", "merge", "rebase", "cherry-pick", "stash",
            "reset", "revert", "reflog", "bisect", "blame", "log", "diff",
            "remote", "fetch", "pull", "push", "clone", "fork", "upstream",
            "hooks", "submodules", "worktrees", "tags", "releases",
            ".gitignore", ".gitattributes", "LFS", "sparse checkout",
        ],
        "question_patterns": [
            "How do I {action} with git?",
            "Git {topic} explained",
            "What's the difference between git {topic} and {topic2}?",
            "Fix git {problem}",
            "Best practices for git {topic}",
        ],
        "actions": [
            "undo a commit", "squash commits", "rename a branch", "delete a branch",
            "resolve conflicts", "rewrite history", "find a bug", "recover lost work",
            "sync with upstream", "create a release", "sign commits", "split a commit",
        ],
        "problems": [
            "merge conflict", "detached HEAD", "diverged branches",
            "lost commits", "wrong branch", "sensitive data in history",
        ]
    },
    "nodejs": {
        "topics": [
            "modules", "npm", "package.json", "node_modules", "require", "import",
            "exports", "CommonJS", "ESM", "event loop", "streams", "buffers",
            "fs", "path", "http", "https", "net", "child_process", "cluster",
            "worker_threads", "process", "events", "timers", "crypto",
        ],
        "question_patterns": [
            "How do I {action} in Node.js?",
            "Node.js {topic} explained",
            "What's the best way to {action} with Node?",
            "Node.js {topic} vs {topic2}",
            "Performance tips for Node.js {topic}",
        ],
        "actions": [
            "read files", "write files", "make HTTP requests", "create a server",
            "handle streams", "spawn processes", "use worker threads",
            "manage dependencies", "publish a package", "debug memory leaks",
        ]
    },
    "database_sql": {
        "topics": [
            "SELECT", "INSERT", "UPDATE", "DELETE", "JOIN", "LEFT JOIN", 
            "GROUP BY", "HAVING", "ORDER BY", "LIMIT", "OFFSET", "UNION",
            "subqueries", "CTEs", "window functions", "indexes", "constraints",
            "transactions", "ACID", "locks", "deadlocks", "normalization",
            "views", "stored procedures", "triggers", "foreign keys",
        ],
        "question_patterns": [
            "How do I {action} in SQL?",
            "SQL {topic} explained",
            "Optimize SQL {topic}",
            "What's the difference between {topic} and {topic2}?",
            "SQL {topic} best practices",
        ],
        "actions": [
            "join multiple tables", "aggregate data", "filter results",
            "handle NULL values", "prevent SQL injection", "optimize queries",
            "create indexes", "manage transactions", "design a schema",
        ]
    },
    "linux_admin": {
        "topics": [
            "file permissions", "users and groups", "sudo", "systemd",
            "journalctl", "cron", "rsync", "ssh", "scp", "tar", "gzip",
            "grep", "sed", "awk", "find", "xargs", "pipes", "redirection",
            "process management", "memory management", "disk management",
            "networking", "firewall", "iptables", "nftables", "SELinux",
        ],
        "question_patterns": [
            "How do I {action} on Linux?",
            "Linux {topic} explained",
            "What's the best way to {action}?",
            "Troubleshoot Linux {topic}",
            "Linux {topic} commands",
        ],
        "actions": [
            "find files", "search in files", "manage processes", "check disk space",
            "view logs", "schedule tasks", "manage services", "configure firewall",
            "set up SSH keys", "transfer files", "compress files", "monitor resources",
        ]
    },
    "networking": {
        "topics": [
            "TCP/IP", "UDP", "DNS", "DHCP", "HTTP", "HTTPS", "TLS/SSL",
            "IP addressing", "subnets", "CIDR", "routing", "NAT", "VPN",
            "firewalls", "load balancers", "reverse proxy", "CDN",
            "WebSocket", "REST", "GraphQL", "gRPC", "MQTT",
        ],
        "question_patterns": [
            "How does {topic} work?",
            "What's the difference between {topic} and {topic2}?",
            "Troubleshoot {topic} issues",
            "Configure {topic}",
            "{topic} best practices",
        ],
        "comparisons": [
            ("TCP", "UDP"),
            ("HTTP", "HTTPS"),
            ("REST", "GraphQL"),
            ("forward proxy", "reverse proxy"),
        ]
    },
    "security": {
        "topics": [
            "authentication", "authorization", "OAuth", "JWT", "OIDC",
            "CORS", "CSRF", "XSS", "SQL injection", "input validation",
            "encryption", "hashing", "salting", "TLS", "certificates",
            "secrets management", "API keys", "rate limiting", "OWASP",
        ],
        "question_patterns": [
            "How do I implement {topic}?",
            "Prevent {topic} attacks",
            "What's the difference between {topic} and {topic2}?",
            "{topic} best practices",
            "Secure my {thing} against {topic}",
        ],
        "things": ["API", "web app", "database", "server", "authentication flow"],
    },
}


def generate_from_domain(domain: str, count: int) -> Generator[Dict, None, None]:
    """Generate examples for a specific domain using templates."""
    
    if domain not in DOMAIN_TEMPLATES:
        return
    
    config = DOMAIN_TEMPLATES[domain]
    topics = config.get("topics", [])
    patterns = config.get("question_patterns", [])
    actions = config.get("actions", [])
    comparisons = config.get("comparisons", [])
    things = config.get("things", [])
    problems = config.get("problems", [])
    
    for _ in range(count):
        pattern = random.choice(patterns)
        
        # Fill in template
        instruction = pattern
        if "{topic}" in pattern:
            topic = random.choice(topics)
            instruction = instruction.replace("{topic}", topic)
        if "{topic2}" in pattern:
            topic2 = random.choice([t for t in topics if t != topic] or topics)
            instruction = instruction.replace("{topic2}", topic2)
        if "{action}" in pattern:
            action = random.choice(actions) if actions else "do something"
            instruction = instruction.replace("{action}", action)
        if "{thing}" in pattern:
            thing = random.choice(things) if things else "application"
            instruction = instruction.replace("{thing}", thing)
        if "{problem}" in pattern:
            problem = random.choice(problems) if problems else "issue"
            instruction = instruction.replace("{problem}", problem)
        
        # Generate a templated response
        response = f"""I'll help you with that!

Here's a quick overview and some guidance on {instruction.lower().rstrip('?')}:

**Key Points:**
- This is commonly used in {domain.replace('_', ' ')} workflows
- Make sure to follow best practices for your specific use case
- Consider edge cases and error handling

**Example approach:**
1. Start with the basic implementation
2. Add error handling
3. Test thoroughly
4. Optimize if needed

Want me to show you a specific code example or go deeper on any part?"""
        
        yield {
            "system": SYSTEM_PROMPT,
            "instruction": instruction,
            "response": response
        }


def expand_with_llm(
    domain: str,
    existing_examples: List[Dict],
    count: int,
    model: str = "qwen2.5:32b",
    ollama_url: str = "http://localhost:11434"
) -> Generator[Dict, None, None]:
    """Use LLM to generate variations based on existing examples."""
    
    if not HTTPX_AVAILABLE:
        print("  httpx not installed, skipping LLM expansion")
        return
    
    prompt_template = """You are generating training data for AJ, an AI coding assistant.

Domain: {domain}

Here's an existing example:
User: {instruction}
AJ: {response}

Generate a NEW, DIFFERENT example in the same domain. The question should be related but not identical.
AJ's response style: helpful, slightly informal, technical but clear, offers to help more.

Return ONLY valid JSON:
{{"instruction": "user's question", "response": "AJ's helpful answer"}}"""

    with httpx.Client(timeout=60.0) as client:
        for i in range(count):
            source = random.choice(existing_examples)
            prompt = prompt_template.format(
                domain=domain.replace('_', ' '),
                instruction=source.get("instruction", ""),
                response=source.get("response", "")[:800]
            )
            
            try:
                response = client.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.8}
                    }
                )
                response.raise_for_status()
                
                text = response.json()["response"]
                start = text.find("{")
                end = text.rfind("}") + 1
                if start >= 0 and end > start:
                    data = json.loads(text[start:end])
                    yield {
                        "system": SYSTEM_PROMPT,
                        "instruction": data["instruction"],
                        "response": data["response"]
                    }
            except Exception as e:
                continue
            
            if (i + 1) % 10 == 0:
                print(f"    LLM generated {i + 1}/{count}...")


def load_existing_data(data_dir: Path) -> Dict[str, Tuple[int, List[Dict]]]:
    """Load all existing training data and count by domain."""
    
    domain_data = {}
    
    for filepath in data_dir.glob("*.jsonl"):
        domain = filepath.stem
        examples = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        examples.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
        domain_data[domain] = (len(examples), examples)
    
    return domain_data


def main():
    parser = argparse.ArgumentParser(description="Expand domain training data")
    parser.add_argument("--data-dir", type=str, default="../data",
                        help="Directory with training data")
    parser.add_argument("--target", "-t", type=int, default=100,
                        help="Target count per domain")
    parser.add_argument("--domain", "-d", type=str, default=None,
                        help="Specific domain to expand (default: all under target)")
    parser.add_argument("--use-llm", action="store_true",
                        help="Use LLM for higher quality expansion")
    parser.add_argument("--llm-model", type=str, default="qwen2.5:32b")
    parser.add_argument("--ollama-url", type=str, default="http://localhost:11434")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be expanded without doing it")
    
    args = parser.parse_args()
    
    if args.seed:
        random.seed(args.seed)
    
    data_dir = Path(args.data_dir)
    
    # Load existing data
    print("Loading existing training data...")
    domain_data = load_existing_data(data_dir)
    
    # Find domains that need expansion
    to_expand = []
    
    print(f"\nDomain Analysis (target: {args.target}):")
    print("-" * 50)
    
    for domain, (count, examples) in sorted(domain_data.items()):
        if domain in ["all_training_data", "dataset_stats"]:
            continue
        if domain.startswith("generated_"):
            continue
            
        if args.domain and domain != args.domain:
            continue
            
        needed = max(0, args.target - count)
        status = "✓" if needed == 0 else f"need +{needed}"
        print(f"  {domain}: {count} ({status})")
        
        if needed > 0:
            to_expand.append((domain, count, examples, needed))
    
    if not to_expand:
        print("\nAll domains meet target!")
        return
    
    if args.dry_run:
        print(f"\nWould expand {len(to_expand)} domains")
        return
    
    # Expand each domain
    print(f"\nExpanding {len(to_expand)} domains...")
    
    for domain, current_count, existing, needed in to_expand:
        print(f"\n  {domain}: adding {needed} examples...")
        
        new_examples = []
        
        # Template-based generation
        if domain in DOMAIN_TEMPLATES:
            template_count = needed if not args.use_llm else needed // 2
            print(f"    Template generation: {template_count}")
            new_examples.extend(list(generate_from_domain(domain, template_count)))
        
        # LLM-based generation
        if args.use_llm and existing:
            llm_count = needed - len(new_examples)
            if llm_count > 0:
                print(f"    LLM generation: {llm_count}")
                new_examples.extend(list(expand_with_llm(
                    domain, existing, llm_count,
                    args.llm_model, args.ollama_url
                )))
        
        # If we still need more and don't have templates, use generic
        if len(new_examples) < needed and domain not in DOMAIN_TEMPLATES:
            remaining = needed - len(new_examples)
            print(f"    Generic expansion: {remaining}")
            # Just duplicate and vary existing
            for _ in range(remaining):
                if existing:
                    example = random.choice(existing)
                    new_examples.append(example.copy())
        
        # Append to file
        if new_examples:
            filepath = data_dir / f"{domain}.jsonl"
            with open(filepath, 'a', encoding='utf-8') as f:
                for example in new_examples:
                    f.write(json.dumps(example, ensure_ascii=False) + '\n')
            print(f"    ✓ Added {len(new_examples)} examples to {filepath.name}")
    
    print("\n✅ Domain expansion complete!")


if __name__ == "__main__":
    main()
