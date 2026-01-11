#!/usr/bin/env python3
"""
Technical Q&A Generator for AJ Training

Generates technical/educational training examples by:
1. Combining topics with question templates
2. Using existing documentation/knowledge
3. LLM-assisted expansion of concepts

Usage:
    python generate_technical_data.py --output ../data/generated_technical.jsonl --count 300
    python generate_technical_data.py --domain python --count 100
    python generate_technical_data.py --use-llm --expand-existing ../data/conversational.jsonl
"""

import json
import random
import argparse
from pathlib import Path
from typing import List, Dict, Generator, Optional

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

SYSTEM_PROMPT = "You are AJ, a helpful AI assistant."

# ============================================================================
# KNOWLEDGE BASE - Topics and explanations
# ============================================================================

DOMAINS = {
    "python": {
        "concepts": [
            {
                "topic": "async/await",
                "question_variations": [
                    "How does async/await work in Python?",
                    "Can you explain Python async?",
                    "What's the deal with asyncio?",
                    "Help me understand Python coroutines",
                ],
                "response": """Async/await lets you write concurrent code that looks sequential.

```python
async def fetch_data(url):
    response = await http_client.get(url)  # Pauses here, doesn't block
    return await response.json()

# Run multiple concurrently
results = await asyncio.gather(
    fetch_data(url1),
    fetch_data(url2),
)
```

Key points:
- `async def` creates a coroutine
- `await` pauses until the operation completes
- Other tasks can run while you're waiting
- Use `asyncio.run()` to start the event loop

Great for I/O-bound work (HTTP, database, files). For CPU-bound work, use multiprocessing instead. What are you trying to build?"""
            },
            {
                "topic": "decorators",
                "question_variations": [
                    "How do Python decorators work?",
                    "Explain decorators in Python",
                    "What's the @ syntax in Python?",
                    "Help me understand Python decorators",
                ],
                "response": """Decorators wrap functions to add behavior without modifying them.

```python
def log_calls(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Done: {result}")
        return result
    return wrapper

@log_calls  # Same as: greet = log_calls(greet)
def greet(name):
    return f"Hello, {name}"

greet("AJ")  # Prints: Calling greet, Hello, AJ, Done: Hello, AJ
```

Common uses:
- `@property` - getters/setters
- `@staticmethod` / `@classmethod`
- `@functools.lru_cache` - memoization
- `@app.route()` - Flask/FastAPI routing

Want to see a specific decorator pattern?"""
            },
            {
                "topic": "virtual environments",
                "question_variations": [
                    "How do Python virtual environments work?",
                    "What's a venv?",
                    "Why use virtualenv?",
                    "Explain Python environment isolation",
                ],
                "response": """Virtual environments isolate project dependencies so they don't conflict.

```bash
# Create
python -m venv .venv

# Activate (Windows)
.venv\\Scripts\\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install packages (isolated to this env)
pip install fastapi uvicorn

# Freeze dependencies
pip freeze > requirements.txt

# Deactivate
deactivate
```

Why use them:
- Project A needs `requests==2.25`, Project B needs `requests==2.28`
- Keeps your system Python clean
- Makes deployments reproducible

Alternatives: `conda` (heavier, better for data science), `poetry` (modern dependency management), `uv` (fast, Rust-based). What's your setup?"""
            },
            {
                "topic": "type hints",
                "question_variations": [
                    "How do type hints work in Python?",
                    "Explain Python typing",
                    "What's the point of type annotations?",
                    "Should I use type hints?",
                ],
                "response": """Type hints add optional static typing to Python - they document intent and catch bugs with tools like mypy.

```python
from typing import List, Optional, Dict

def process_users(
    users: List[str],
    config: Optional[Dict[str, str]] = None
) -> int:
    \"\"\"Process users and return count.\"\"\"
    return len(users)

# Python 3.10+ simplified syntax
def greet(name: str | None = None) -> str:
    return f"Hello, {name or 'World'}"
```

Benefits:
- IDE autocomplete gets smarter
- Catch type errors before runtime
- Self-documenting code
- Easier refactoring

Run `mypy yourfile.py` to check types. They're optional - Python still runs without them. Worth it for any serious project. Want help adding types to your code?"""
            },
        ]
    },
    "docker": {
        "concepts": [
            {
                "topic": "containers vs VMs",
                "question_variations": [
                    "What's the difference between containers and VMs?",
                    "Docker vs virtual machines?",
                    "Why containers instead of VMs?",
                    "Container vs VM performance",
                ],
                "response": """Containers share the host OS kernel; VMs include their own OS.

```
VMs:                          Containers:
┌────────┐ ┌────────┐         ┌────────┐ ┌────────┐
│  App   │ │  App   │         │  App   │ │  App   │
├────────┤ ├────────┤         ├────────┤ ├────────┤
│Guest OS│ │Guest OS│         │  Libs  │ │  Libs  │
├────────┴─┴────────┤         ├────────┴─┴────────┤
│    Hypervisor     │         │  Container Engine │
├───────────────────┤         ├───────────────────┤
│     Host OS       │         │     Host OS       │
└───────────────────┘         └───────────────────┘
```

Containers:
- Start in seconds (vs minutes for VMs)
- Use MB of memory (vs GB for VMs)
- Share kernel = less isolation but more efficient

VMs:
- Stronger isolation (separate kernel)
- Can run different OS (Linux VM on Windows)
- Better for untrusted workloads

Use containers for microservices and dev environments; VMs when you need full OS isolation. What's your use case?"""
            },
            {
                "topic": "Dockerfile best practices",
                "question_variations": [
                    "How do I write a good Dockerfile?",
                    "Dockerfile best practices?",
                    "Optimize my Docker image",
                    "Make my Docker build faster",
                ],
                "response": """Key Dockerfile optimizations:

```dockerfile
# 1. Use specific base image tags (not :latest)
FROM python:3.11-slim

# 2. Set working directory
WORKDIR /app

# 3. Copy dependency files first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy source code last (changes most often)
COPY . .

# 5. Use non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# 6. Use ENTRYPOINT + CMD pattern
ENTRYPOINT ["python"]
CMD ["app.py"]
```

Tips:
- Order commands by change frequency (rarely→often)
- Combine RUN commands to reduce layers
- Use `.dockerignore` to exclude unnecessary files
- Multi-stage builds for compiled languages
- Use `--no-cache-dir` with pip

Want me to review your Dockerfile?"""
            },
            {
                "topic": "docker compose",
                "question_variations": [
                    "How does Docker Compose work?",
                    "Explain docker-compose",
                    "When should I use Docker Compose?",
                    "Docker Compose vs Kubernetes",
                ],
                "response": """Docker Compose defines multi-container applications in YAML.

```yaml
# docker-compose.yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://db:5432/app
    depends_on:
      - db
    
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=secret

volumes:
  postgres_data:
```

```bash
docker compose up -d      # Start all services
docker compose logs -f    # Watch logs
docker compose down       # Stop and remove
```

Use Compose for:
- Local development environments
- Simple multi-container apps
- CI/CD test environments

Use Kubernetes when you need:
- Production-grade orchestration
- Auto-scaling
- Rolling updates across clusters

For most dev work, Compose is plenty. What are you building?"""
            },
        ]
    },
    "git": {
        "concepts": [
            {
                "topic": "merge vs rebase",
                "question_variations": [
                    "What's the difference between merge and rebase?",
                    "Git merge vs rebase?",
                    "When should I rebase?",
                    "Should I merge or rebase?",
                ],
                "response": """Both integrate changes, but differently:

**Merge** - creates a merge commit:
```
main:    A---B---C---M
              \\     /
feature:       D---E
```

**Rebase** - replays commits on top:
```
main:    A---B---C
                  \\
feature:           D'---E'
```

When to use each:
- **Merge**: Shared branches, preserves complete history
- **Rebase**: Local branches, clean linear history

Golden rule: **Never rebase commits that others have pulled.**

```bash
# Safe rebase workflow
git checkout feature
git rebase main       # Replay your commits on main
git checkout main
git merge feature     # Fast-forward merge (no merge commit)
```

Interactive rebase (`git rebase -i`) is great for cleaning up commits before pushing. Want to walk through a specific scenario?"""
            },
            {
                "topic": "undoing changes",
                "question_variations": [
                    "How do I undo a git commit?",
                    "Revert changes in git",
                    "I messed up my git history",
                    "How to fix a git mistake",
                ],
                "response": """Depends on what you want to undo:

**Unstaged changes** (modified files):
```bash
git checkout -- file.txt   # Discard changes to one file
git restore .              # Discard all unstaged changes
```

**Staged changes** (added but not committed):
```bash
git reset HEAD file.txt    # Unstage one file
git reset HEAD             # Unstage everything
```

**Last commit** (not pushed):
```bash
git reset --soft HEAD~1    # Undo commit, keep changes staged
git reset --mixed HEAD~1   # Undo commit, keep changes unstaged
git reset --hard HEAD~1    # Undo commit, discard changes
```

**Pushed commit** (public history):
```bash
git revert <commit-hash>   # Creates new commit that undoes changes
```

**Nuclear option** (careful!):
```bash
git reflog                 # Find the commit you want
git reset --hard <hash>    # Go back to that state
```

What's your situation?"""
            },
        ]
    },
    "linux": {
        "concepts": [
            {
                "topic": "file permissions",
                "question_variations": [
                    "How do Linux file permissions work?",
                    "Explain chmod",
                    "What does 755 mean?",
                    "Linux permission denied",
                ],
                "response": """Linux permissions: read (r=4), write (w=2), execute (x=1) for owner/group/others.

```bash
ls -la file.txt
-rw-r--r-- 1 user group 1234 Jan 1 12:00 file.txt
│└┬┘└┬┘└┬┘
│ │  │  └── Others: read only
│ │  └───── Group: read only  
│ └──────── Owner: read + write
└────────── File type (- = file, d = directory)
```

Common patterns:
```bash
chmod 755 script.sh   # rwxr-xr-x (executable script)
chmod 644 file.txt    # rw-r--r-- (normal file)
chmod 600 secrets.key # rw------- (private file)
chmod +x script.sh    # Add execute permission

# Recursive
chmod -R 755 directory/

# Change ownership
chown user:group file.txt
```

For "Permission denied":
1. Check current permissions: `ls -la`
2. Who are you? `whoami`
3. Fix ownership or permissions as needed

What's the specific error you're seeing?"""
            },
            {
                "topic": "systemd services",
                "question_variations": [
                    "How do I create a systemd service?",
                    "Run my app as a service",
                    "Start application on boot Linux",
                    "Explain systemctl",
                ],
                "response": """Create a unit file in `/etc/systemd/system/`:

```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=My Application
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/myapp
ExecStart=/opt/myapp/venv/bin/python app.py
Restart=always
RestartSec=5
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

```bash
# Reload systemd
sudo systemctl daemon-reload

# Start service
sudo systemctl start myapp

# Enable on boot
sudo systemctl enable myapp

# Check status
sudo systemctl status myapp

# View logs
journalctl -u myapp -f
```

Key options:
- `Restart=always` - auto-restart on failure
- `RestartSec=5` - wait 5s before restart
- `Type=notify` - for apps that signal readiness

What kind of app are you trying to run as a service?"""
            },
        ]
    },
}


# ============================================================================
# GENERATORS
# ============================================================================

def generate_from_knowledge_base(count: int, domain: Optional[str] = None) -> Generator[Dict, None, None]:
    """Generate examples from the knowledge base."""
    
    if domain and domain in DOMAINS:
        domains_to_use = {domain: DOMAINS[domain]}
    else:
        domains_to_use = DOMAINS
    
    all_concepts = []
    for d, data in domains_to_use.items():
        for concept in data["concepts"]:
            all_concepts.append((d, concept))
    
    for _ in range(count):
        domain_name, concept = random.choice(all_concepts)
        question = random.choice(concept["question_variations"])
        
        yield {
            "system": SYSTEM_PROMPT,
            "instruction": question,
            "response": concept["response"].strip()
        }


def generate_followup_questions(count: int) -> Generator[Dict, None, None]:
    """Generate common follow-up patterns."""
    
    followups = [
        {
            "instruction": "Can you show me an example?",
            "response": "Sure! What specifically would you like to see? Give me a bit of context about what you're building and I'll make the example relevant."
        },
        {
            "instruction": "I'm still confused",
            "response": "No problem - let me try a different angle. What part isn't clicking? Sometimes it helps to identify the specific piece that's unclear."
        },
        {
            "instruction": "What about [alternative]?",
            "response": "Good question - there are usually multiple ways to approach things. Tell me more about your specific situation and I can help you pick the right approach."
        },
        {
            "instruction": "Is that the best way?",
            "response": "It depends on your context! What I showed is a common approach, but 'best' varies by situation. What are you optimizing for - simplicity, performance, maintainability?"
        },
        {
            "instruction": "That's not working",
            "response": "Let's debug it. What error are you seeing, or what's the unexpected behavior? Paste the relevant output and I'll help figure it out."
        },
        {
            "instruction": "Can you explain that differently?",
            "response": "Absolutely. Let me try another way - what's your background? Knowing what concepts you're already familiar with helps me frame this better."
        },
    ]
    
    for _ in range(count):
        example = random.choice(followups)
        yield {
            "system": SYSTEM_PROMPT,
            "instruction": example["instruction"],
            "response": example["response"]
        }


def expand_with_llm(
    existing_file: str,
    count: int,
    model: str = "qwen2.5:32b",
    ollama_url: str = "http://localhost:11434"
) -> Generator[Dict, None, None]:
    """Use LLM to generate variations of existing examples."""
    
    if not HTTPX_AVAILABLE:
        print("httpx not installed, skipping LLM expansion")
        return
    
    # Load existing examples
    existing = []
    with open(existing_file, 'r') as f:
        for line in f:
            if line.strip():
                existing.append(json.loads(line))
    
    prompt_template = """Given this training example for AJ (an AI coding assistant):

User: {instruction}
AJ: {response}

Generate a SIMILAR but DIFFERENT example. Keep the same topic area and AJ's style (helpful, slightly informal, technical but clear).
The new example should teach a related concept or be a variation of the question.

Return ONLY valid JSON: {{"instruction": "new user question", "response": "AJ's response"}}"""

    with httpx.Client(timeout=60.0) as client:
        for i in range(count):
            source = random.choice(existing)
            prompt = prompt_template.format(
                instruction=source["instruction"],
                response=source["response"][:500]  # Truncate long responses
            )
            
            try:
                response = client.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.7}
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
                print(f"  LLM expansion error: {e}")
                continue
            
            if (i + 1) % 10 == 0:
                print(f"  Expanded {i + 1}/{count}...")


def main():
    parser = argparse.ArgumentParser(description="Generate technical Q&A training data")
    parser.add_argument("--output", "-o", type=str, default="../data/generated_technical.jsonl")
    parser.add_argument("--count", "-n", type=int, default=300)
    parser.add_argument("--domain", "-d", type=str, choices=list(DOMAINS.keys()),
                        help="Specific domain to generate")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM for expansion")
    parser.add_argument("--expand-existing", type=str, help="Expand examples from existing file")
    parser.add_argument("--llm-model", type=str, default="qwen2.5:32b")
    parser.add_argument("--ollama-url", type=str, default="http://localhost:11434")
    parser.add_argument("--seed", type=int, default=None)
    
    args = parser.parse_args()
    
    if args.seed:
        random.seed(args.seed)
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating technical training data...")
    print(f"  Output: {output_path}")
    
    examples = []
    
    # Knowledge base examples
    kb_count = int(args.count * 0.7)
    print(f"  Generating {kb_count} from knowledge base...")
    examples.extend(list(generate_from_knowledge_base(kb_count, args.domain)))
    
    # Follow-up patterns
    followup_count = int(args.count * 0.15)
    print(f"  Generating {followup_count} follow-up patterns...")
    examples.extend(list(generate_followup_questions(followup_count)))
    
    # LLM expansion
    if args.use_llm or args.expand_existing:
        source_file = args.expand_existing or str(output_path)
        if Path(source_file).exists():
            llm_count = int(args.count * 0.15)
            print(f"  Expanding {llm_count} with LLM...")
            examples.extend(list(expand_with_llm(
                source_file, llm_count, args.llm_model, args.ollama_url
            )))
    
    random.shuffle(examples)
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"\n✅ Generated {len(examples)} examples")
    print(f"   Saved to: {output_path}")


if __name__ == "__main__":
    main()
