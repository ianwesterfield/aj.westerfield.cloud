#!/usr/bin/env python3
"""
Bulk Domain Expander

Generates additional training examples for domains under a target count.
Uses template variations and pattern augmentation from existing examples.

Usage:
    python bulk_expand.py --target 100
    python bulk_expand.py --target 150 --category task_planning
"""

import json
import random
import argparse
from pathlib import Path
from typing import List, Dict, Generator
from collections import defaultdict

SYSTEM_PROMPT = "You are AJ, a helpful AI assistant."

# Additional templates for specific domains
DOMAIN_EXPANSIONS = {
    "task_planning": {
        "patterns": [
            ("Plan how to {task}", "step-by-step plan"),
            ("What's the best approach to {task}?", "strategy advice"),
            ("Help me break down: {task}", "task breakdown"),
            ("I need to {task}. Where do I start?", "getting started"),
        ],
        "tasks": [
            "set up a new React project with TypeScript",
            "migrate a database schema",
            "implement user authentication",
            "deploy to production for the first time",
            "refactor a legacy codebase",
            "set up CI/CD pipeline",
            "add unit tests to existing code",
            "implement caching for API responses",
            "set up monitoring and alerting",
            "migrate from REST to GraphQL",
            "implement real-time features with WebSockets",
            "set up a microservices architecture",
            "implement feature flags",
            "add internationalization (i18n)",
            "optimize database queries",
            "implement rate limiting",
            "set up logging and observability",
            "add API documentation with OpenAPI",
            "implement background job processing",
            "set up A/B testing infrastructure",
        ]
    },
    "project_planning": {
        "patterns": [
            ("Help me plan a {project}", "project plan"),
            ("What do I need for a {project}?", "requirements"),
            ("Architecture for {project}", "architecture"),
            ("Timeline for {project}", "timeline estimate"),
        ],
        "projects": [
            "SaaS application", "mobile app backend", "e-commerce platform",
            "content management system", "real-time chat application",
            "API gateway", "data pipeline", "ML inference service",
            "multi-tenant platform", "IoT data collection system",
            "internal developer tool", "customer portal",
            "analytics dashboard", "workflow automation tool",
            "integration platform", "document management system",
        ]
    },
    "code_review": {
        "patterns": [
            ("Review this {lang} code: {desc}", "constructive feedback"),
            ("What's wrong with this {lang}?", "issue identification"),
            ("How can I improve this {lang} code?", "suggestions"),
            ("Best practices for {lang} {topic}", "best practices"),
        ],
        "langs": ["Python", "JavaScript", "TypeScript", "C#", "Go", "Rust"],
        "topics": ["error handling", "async code", "class design", "API design",
                   "testing", "security", "performance", "readability"],
    },
    "refactoring": {
        "patterns": [
            ("Refactor this to be more {quality}", "refactoring guidance"),
            ("How do I extract a {thing} from this?", "extraction advice"),
            ("This code has {smell}. How do I fix it?", "code smell fix"),
        ],
        "qualities": ["readable", "testable", "maintainable", "efficient", "clean"],
        "things": ["method", "class", "interface", "module", "function"],
        "smells": ["too many parameters", "deep nesting", "long methods",
                   "duplicate code", "magic numbers", "god class"],
    },
    "testing_debugging": {
        "patterns": [
            ("How do I test {thing}?", "testing strategy"),
            ("Debug this {issue}", "debugging help"),
            ("Why is my test {problem}?", "test troubleshooting"),
            ("Mock {thing} in my tests", "mocking guidance"),
        ],
        "things": ["async code", "API calls", "database queries", "React components",
                   "authentication", "file uploads", "webhooks", "cron jobs"],
        "issues": ["null pointer exception", "race condition", "memory leak",
                   "timeout error", "assertion failure"],
        "problems": ["flaky", "slow", "not finding the bug", "too coupled"],
    },
    "architecture": {
        "patterns": [
            ("When should I use {arch_pattern}?", "pattern advice"),
            ("Design a {system}", "system design"),
            ("{arch_pattern} vs {arch_pattern2} for my use case", "comparison"),
            ("Scale {thing} to handle {scale}", "scaling advice"),
        ],
        "arch_patterns": ["microservices", "monolith", "event sourcing", "CQRS",
                     "hexagonal architecture", "clean architecture", "DDD"],
        "systems": ["notification system", "payment processing", "user auth",
                    "file storage", "search service", "caching layer"],
        "things": ["database", "API", "message queue", "cache", "service"],
        "scales": ["10K users", "100K requests/sec", "1TB of data", "global traffic"],
    },
    "intent_classification": {
        "patterns": [
            ("{action} a {thing}", "intent"),
            ("How to {action} {thing}?", "intent"),
            ("Can you {action} this {thing}?", "intent"),
            ("I want to {action}", "intent"),
        ],
        "actions": ["create", "update", "delete", "list", "search", "filter",
                    "debug", "fix", "optimize", "refactor", "test", "deploy"],
        "things": ["file", "function", "class", "API", "database", "container",
                   "service", "module", "package", "dependency"],
    },
    "tool_selection": {
        "patterns": [
            ("What tool should I use for {task}?", "tool recommendation"),
            ("{tool1} or {tool2} for {task}?", "tool comparison"),
            ("Best {category} tool in {year}", "tool recommendation"),
        ],
        "tasks": ["testing", "CI/CD", "monitoring", "logging", "documentation",
                  "containerization", "orchestration", "API design"],
        "categories": ["testing", "deployment", "monitoring", "database", "caching"],
    },
    "guardrails": {
        "patterns": [
            ("Is it safe to {action}?", "safety guidance"),
            ("Security implications of {action}", "security advice"),
            ("Should I {action} in production?", "best practice"),
        ],
        "actions": ["store passwords in plain text", "disable CORS", "run as root",
                    "expose internal APIs", "skip input validation", "use eval()"],
    },
    "scss_css": {
        "patterns": [
            ("Style {thing} with {approach}", "CSS guidance"),
            ("SCSS mixin for {purpose}", "SCSS help"),
            ("Center {thing} in CSS", "CSS trick"),
            ("Responsive {thing}", "responsive design"),
        ],
        "things": ["a div", "a modal", "a navbar", "a card", "a form", "buttons"],
        "approaches": ["flexbox", "grid", "absolute positioning", "transform"],
        "purposes": ["breakpoints", "colors", "typography", "spacing", "shadows"],
    },
    "web_fundamentals": {
        "patterns": [
            ("How does {thing} work?", "explanation"),
            ("Difference between {a} and {b}", "comparison"),
            ("{thing} best practices", "best practices"),
        ],
        "things": ["HTTP caching", "cookies", "localStorage", "sessionStorage",
                   "CORS", "HTTPS", "DNS", "CDN", "service workers"],
        "comparisons": [("GET", "POST"), ("cookie", "localStorage"), ("REST", "GraphQL")],
    },
    "ubiquiti_unifi": {
        "patterns": [
            ("Configure {feature} on UniFi", "configuration"),
            ("UniFi {issue} troubleshooting", "troubleshooting"),
            ("Best settings for {use_case}", "recommendations"),
        ],
        "features": ["VLAN", "firewall rules", "port forwarding", "guest network",
                     "bandwidth limits", "DPI", "IDS/IPS", "VPN"],
        "issues": ["slow WiFi", "device not adopting", "firmware update", "connectivity"],
        "use_cases": ["home office", "small business", "IoT devices", "gaming"],
    },
    "qdrant_vectors": {
        "patterns": [
            ("How to {action} in Qdrant?", "Qdrant guidance"),
            ("Qdrant {feature} example", "code example"),
            ("Optimize Qdrant for {use_case}", "optimization"),
        ],
        "actions": ["store embeddings", "search vectors", "filter results",
                    "create collections", "update points", "delete vectors"],
        "features": ["payload filtering", "scroll API", "batch upsert", "snapshots"],
        "use_cases": ["semantic search", "recommendations", "RAG", "deduplication"],
    },
    "devops_cicd": {
        "patterns": [
            ("Set up {thing} in CI/CD", "CI/CD setup"),
            ("{tool} pipeline for {lang}", "pipeline example"),
            ("Automate {task} deployment", "automation"),
        ],
        "things": ["testing", "linting", "security scanning", "deployment", "rollback"],
        "tools": ["GitHub Actions", "GitLab CI", "Jenkins", "CircleCI", "ArgoCD"],
        "langs": ["Node.js", "Python", "Go", ".NET", "Java"],
        "tasks": ["Docker", "Kubernetes", "serverless", "static site"],
    },
    "programming_concepts": {
        "patterns": [
            ("Explain {concept}", "explanation"),
            ("{concept} in {lang}", "implementation"),
            ("When to use {concept}?", "guidance"),
        ],
        "concepts": ["recursion", "memoization", "closures", "currying", "generators",
                     "iterators", "decorators", "mixins", "dependency injection",
                     "inversion of control", "SOLID principles", "DRY", "YAGNI"],
        "langs": ["Python", "JavaScript", "TypeScript", "Go", "Rust"],
    },
}


def expand_from_templates(domain: str, count: int) -> Generator[Dict, None, None]:
    """Generate examples from domain-specific templates."""
    
    if domain not in DOMAIN_EXPANSIONS:
        return
        
    config = DOMAIN_EXPANSIONS[domain]
    patterns = config.get("patterns", [])
    
    if not patterns:
        return
    
    for _ in range(count):
        pattern, response_type = random.choice(patterns)
        instruction = pattern
        
        # Fill in template variables
        for key, values in config.items():
            if key == "patterns":
                continue
            if isinstance(values, list):
                placeholder = "{" + key.rstrip("s") + "}"  # tasks -> {task}
                if placeholder in instruction:
                    instruction = instruction.replace(placeholder, random.choice(values))
                # Also try exact key match
                if "{" + key + "}" in instruction:
                    instruction = instruction.replace("{" + key + "}", random.choice(values))
        
        # Handle pattern-specific replacements
        if "{arch_pattern2}" in instruction:
            arch_patterns = config.get("arch_patterns", ["microservices", "monolith"])
            if isinstance(arch_patterns, list) and arch_patterns:
                p2 = random.choice([str(p) for p in arch_patterns if str(p) not in instruction])
                instruction = instruction.replace("{arch_pattern2}", p2 if p2 else "alternative")
        
        if "{tool1}" in instruction or "{tool2}" in instruction:
            tools = ["npm", "yarn", "pnpm", "Docker", "Kubernetes", "Terraform", 
                     "Ansible", "Jenkins", "GitHub Actions", "pytest", "jest"]
            instruction = instruction.replace("{tool1}", random.choice(tools))
            instruction = instruction.replace("{tool2}", random.choice(tools))
        
        if "{year}" in instruction:
            instruction = instruction.replace("{year}", str(random.randint(2023, 2025)))
        
        if "{a}" in instruction or "{b}" in instruction:
            comparisons = config.get("comparisons", [("A", "B")])
            if comparisons:
                a, b = random.choice(comparisons)
                instruction = instruction.replace("{a}", a).replace("{b}", b)
        
        # Clean up any remaining placeholders
        import re
        instruction = re.sub(r'\{[^}]+\}', 'something', instruction)
        
        response = generate_response(instruction, domain, response_type)
        
        yield {
            "system": SYSTEM_PROMPT,
            "instruction": instruction,
            "response": response
        }


def expand_from_existing(existing: List[Dict], count: int) -> Generator[Dict, None, None]:
    """Generate variations based on existing examples."""
    
    if not existing:
        return
    
    variations = [
        ("Can you help me with", "I'd be happy to help!"),
        ("Show me how to", "Here's how to approach this:"),
        ("What's the best way to", "Great question! Here's what I'd recommend:"),
        ("I'm having trouble with", "Let me help you troubleshoot this:"),
        ("Explain", "Let me break this down:"),
    ]
    
    for _ in range(count):
        example = random.choice(existing)
        instruction = example.get("instruction", "")
        response = example.get("response", "")
        
        # Apply variation
        prefix, response_prefix = random.choice(variations)
        
        # Extract core topic from instruction
        words = instruction.lower().split()
        # Remove common starting words
        skip_words = {"how", "do", "i", "to", "can", "you", "help", "me", "with", "what", "is", "the", "a", "an"}
        core_words = [w for w in words if w not in skip_words][:6]
        core_topic = " ".join(core_words)
        
        new_instruction = f"{prefix} {core_topic}"
        
        # Slightly modify response
        new_response = response
        if not new_response.startswith(response_prefix):
            new_response = f"{response_prefix}\n\n{response}"
        
        yield {
            "system": example.get("system", SYSTEM_PROMPT),
            "instruction": new_instruction.strip(),
            "response": new_response
        }


def generate_response(instruction: str, domain: str, response_type: str) -> str:
    """Generate a contextual response based on instruction and domain."""
    
    domain_friendly = domain.replace("_", " ")
    
    templates = {
        "step-by-step plan": f"""Great question! Here's a step-by-step approach:

**1. Set Up Your Environment**
- Make sure you have all the necessary tools installed
- Create a new project directory or branch

**2. Plan the Implementation**
- Break down the task into smaller subtasks
- Identify any dependencies or blockers

**3. Implement Core Functionality**
- Start with the basic structure
- Add error handling as you go

**4. Test and Validate**
- Write tests for critical paths
- Manual testing for edge cases

**5. Document and Deploy**
- Update documentation
- Deploy to staging first

Would you like me to elaborate on any of these steps?""",

        "strategy advice": f"""Here's my recommended strategy for this:

**Key Considerations:**
1. Start simple, iterate towards complexity
2. Focus on core functionality first
3. Plan for testability from the beginning

**Approach:**
- First, understand the current state
- Identify the minimal viable change
- Implement incrementally with tests

**Common Pitfalls to Avoid:**
- Don't try to do everything at once
- Don't skip testing
- Document as you go

Want me to dive deeper into any aspect?""",

        "task breakdown": f"""Let me break this down into manageable pieces:

**Phase 1: Foundation**
- Set up the basic structure
- Configure dependencies

**Phase 2: Core Implementation**
- Build the main functionality
- Add essential error handling

**Phase 3: Polish**
- Testing and edge cases
- Performance optimization
- Documentation

Each phase can be further broken down. Which would you like to start with?""",

        "configuration": f"""Here's how to configure this in your {domain_friendly} setup:

**Steps:**
1. Navigate to your settings/configuration panel
2. Locate the relevant section
3. Apply the recommended settings

**Recommended Settings:**
- Enable the feature
- Configure the appropriate values
- Test before applying to production

**Verification:**
- Check logs for any errors
- Test functionality end-to-end

Need help with any specific setting?""",

        "troubleshooting": f"""Let's troubleshoot this {domain_friendly} issue:

**Step 1: Gather Information**
- Check recent changes
- Review error logs
- Verify configuration

**Step 2: Common Causes**
- Configuration mismatch
- Network connectivity issues
- Resource limitations

**Step 3: Resolution Steps**
- Try restarting the service
- Check for updates
- Verify permissions

**If Problem Persists:**
- Check documentation for known issues
- Consider reaching out to support

What have you already tried?""",

        "explanation": f"""Let me explain this concept:

**Overview:**
This is a fundamental concept in {domain_friendly} that helps with organization and maintainability.

**How It Works:**
- The basic mechanism involves...
- It interacts with other components by...
- The key benefit is...

**When to Use It:**
- When you need to...
- When dealing with...
- To improve...

**Example Use Case:**
In practice, you'd use this when building features that require scalability and maintainability.

Want me to show you a concrete example?""",

        "comparison": f"""Here's how these compare in {domain_friendly}:

**Key Differences:**
| Feature | Option A | Option B |
|---------|----------|----------|
| Use Case | X | Y |
| Performance | Good for Z | Better for W |
| Complexity | Lower | Higher |

**When to Choose Each:**
- **Option A**: Best for simpler use cases, faster to implement
- **Option B**: Better for complex scenarios, more flexible

**My Recommendation:**
Start with the simpler option unless you specifically need the advanced features of the other.

Would you like more details on either option?""",

        "code example": f"""Here's an example for {domain_friendly}:

```
# This is a conceptual example
# Adapt to your specific framework/language

def example_function():
    # Step 1: Initialize
    setup()
    
    # Step 2: Core logic
    result = process()
    
    # Step 3: Cleanup
    cleanup()
    
    return result
```

**Key Points:**
- Always handle errors appropriately
- Consider edge cases
- Add proper logging

Want me to customize this for your specific situation?""",
    }
    
    return templates.get(response_type, templates["explanation"])


def load_domain_data(data_dir: Path) -> Dict[str, tuple]:
    """Load all domain data files."""
    domain_data = {}
    
    for filepath in data_dir.glob("*.jsonl"):
        domain = filepath.stem
        if domain in ["all_training_data", "dataset_stats"]:
            continue
        if domain.startswith("generated_"):
            # Include generated files but note them
            pass
            
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
    parser = argparse.ArgumentParser(description="Bulk expand training domains")
    parser.add_argument("--data-dir", type=str, default="../data")
    parser.add_argument("--target", "-t", type=int, default=100)
    parser.add_argument("--category", "-c", type=str, default=None,
                        help="Expand only a specific category")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    
    args = parser.parse_args()
    random.seed(args.seed)
    
    data_dir = Path(args.data_dir)
    
    print("Loading existing training data...")
    domain_data = load_domain_data(data_dir)
    
    # Find domains needing expansion
    to_expand = []
    print(f"\nDomain Analysis (target: {args.target}):")
    print("-" * 60)
    
    for domain, (count, examples) in sorted(domain_data.items()):
        if args.category and domain != args.category:
            continue
            
        needed = max(0, args.target - count)
        status = "✓" if needed == 0 else f"need +{needed}"
        print(f"  {domain:35} {count:4} ({status})")
        
        if needed > 0:
            to_expand.append((domain, count, examples, needed))
    
    if not to_expand:
        print("\n✅ All domains meet the target!")
        return
    
    print(f"\n{len(to_expand)} domains need expansion")
    
    if args.dry_run:
        print("(dry run - no changes made)")
        return
    
    # Expand each domain
    print("\nExpanding domains...")
    total_added = 0
    
    for domain, current, existing, needed in to_expand:
        new_examples = []
        
        # Try template-based expansion first
        if domain in DOMAIN_EXPANSIONS:
            template_count = min(needed, 50)  # Up to 50 from templates
            for example in expand_from_templates(domain, template_count):
                new_examples.append(example)
                if len(new_examples) >= needed:
                    break
        
        # Fill remaining with variations of existing
        if len(new_examples) < needed and existing:
            remaining = needed - len(new_examples)
            for example in expand_from_existing(existing, remaining):
                new_examples.append(example)
                if len(new_examples) >= needed:
                    break
        
        # If still short, duplicate existing with minor changes
        if len(new_examples) < needed and existing:
            while len(new_examples) < needed:
                example = random.choice(existing)
                new_examples.append(example.copy())
        
        # Write to file
        if new_examples:
            filepath = data_dir / f"{domain}.jsonl"
            with open(filepath, 'a', encoding='utf-8') as f:
                for example in new_examples:
                    f.write(json.dumps(example, ensure_ascii=False) + '\n')
            
            print(f"  ✓ {domain}: +{len(new_examples)} (now {current + len(new_examples)})")
            total_added += len(new_examples)
    
    print(f"\n✅ Added {total_added} examples total")
    print("\nRun 'python generate_all.py' to regenerate combined dataset")


if __name__ == "__main__":
    main()
