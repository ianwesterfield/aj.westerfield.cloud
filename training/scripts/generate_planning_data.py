#!/usr/bin/env python3
"""
Task Planning & Error Recovery Generator

Generates training examples for:
1. Multi-step task planning (OODA loop compatible)
2. Error recovery and debugging patterns
3. Clarification and disambiguation

Usage:
    python generate_planning_data.py --count 500 --output ../data/generated_planning.jsonl
"""

import json
import random
import argparse
from pathlib import Path
from typing import List, Dict, Generator

SYSTEM_PROMPT = "You are AJ, a helpful AI assistant."

# ============================================================================
# TASK PLANNING PATTERNS
# ============================================================================

TASK_PLANNING = {
    "simple_tasks": [
        {
            "instruction": "Create a new React component for a login form",
            "response": """I'll create a login form component. Here's my plan:

1. **Create component file** - `src/components/LoginForm.tsx`
2. **Add form structure** - email/password inputs with labels
3. **Add state management** - useState for form values
4. **Add validation** - basic email format, required fields
5. **Add submit handler** - calls your auth function

Let me start with step 1. Do you have a preferred location for components, or is `src/components/` good?"""
        },
        {
            "instruction": "Set up a new Python project with FastAPI",
            "response": """I'll set up a FastAPI project. Here's the plan:

1. **Create project structure**
   ```
   project/
   ├── src/app/
   │   ├── __init__.py
   │   ├── main.py
   │   └── api/
   ├── tests/
   ├── pyproject.toml
   └── requirements.txt
   ```

2. **Initialize dependencies** - FastAPI, uvicorn, pydantic
3. **Create main.py** - basic app with health endpoint
4. **Add API router structure**
5. **Set up virtual environment**

Should I create this in the current directory or a new folder?"""
        },
        {
            "instruction": "Add authentication to my Express app",
            "response": """I'll help add authentication. Here's my approach:

1. **Choose auth strategy** - JWT tokens (stateless, scalable)
2. **Install dependencies** - bcrypt, jsonwebtoken, express-validator
3. **Create auth middleware** - token verification
4. **Add user routes** - register, login, refresh token
5. **Protect existing routes** - add middleware to private endpoints
6. **Add password hashing** - bcrypt for secure storage

First question: Do you already have a User model/table, or should I create that too?"""
        },
        {
            "instruction": "Deploy my app to AWS",
            "response": """Let's plan the AWS deployment. I need to understand your setup first:

**Questions:**
1. What type of app? (static site, Node API, containerized, etc.)
2. Expected traffic/scale?
3. Do you have an AWS account set up?

**Typical approach for a web API:**
1. **Containerize** - Dockerfile if not already done
2. **Push to ECR** - container registry
3. **Set up ECS or EKS** - container orchestration
4. **Configure ALB** - load balancer + SSL
5. **Set up RDS** - if you need a database
6. **Configure secrets** - AWS Secrets Manager
7. **Set up CI/CD** - GitHub Actions or CodePipeline

What kind of app are we deploying?"""
        },
        {
            "instruction": "Refactor this code to be more maintainable",
            "response": """I'll help refactor. Let me analyze what we're working with first.

**My refactoring approach:**
1. **Identify code smells** - duplication, long methods, tight coupling
2. **Extract functions** - single responsibility
3. **Add types/interfaces** - better documentation and IDE support
4. **Improve naming** - clear, descriptive names
5. **Add error handling** - graceful failures
6. **Write tests** - protect against regressions

Can you share the code you want to refactor? I'll give specific recommendations based on what I see."""
        },
    ],
    
    "complex_tasks": [
        {
            "instruction": "Build a complete user management system",
            "response": """That's a substantial feature. Let me break it down into manageable phases:

**Phase 1: Core User CRUD**
- User model (id, email, password_hash, created_at, roles)
- Registration endpoint with validation
- Login with JWT tokens
- Password hashing with bcrypt

**Phase 2: Authorization**
- Role-based access control (RBAC)
- Permission middleware
- Admin vs regular user separation

**Phase 3: User Management UI**
- User list with pagination
- Edit user details
- Disable/enable accounts
- Password reset flow

**Phase 4: Security Hardening**
- Rate limiting on auth endpoints
- Account lockout after failed attempts
- Audit logging

Want to start with Phase 1? I'll need to know your stack (backend framework, database) to give you specific code."""
        },
        {
            "instruction": "Migrate our monolith to microservices",
            "response": """Microservices migration is a big undertaking. Let's approach it carefully:

**Assessment Phase:**
1. Map current monolith domains/boundaries
2. Identify highest-value extraction candidates
3. Assess data dependencies between domains

**Recommended Strategy - Strangler Fig Pattern:**
1. **Don't rewrite everything at once**
2. Extract one bounded context at a time
3. Keep monolith running during transition
4. Route traffic gradually to new services

**First Steps:**
1. Identify a self-contained domain (e.g., notifications, reporting)
2. Define API contract for that service
3. Extract to separate service + database
4. Add API gateway for routing
5. Repeat for next domain

What's your current architecture? I can help identify good extraction candidates."""
        },
        {
            "instruction": "Set up a CI/CD pipeline",
            "response": """I'll help you set up CI/CD. Here's a comprehensive plan:

**Pipeline Stages:**
1. **Build** - compile, install dependencies
2. **Test** - unit tests, integration tests
3. **Lint/Security** - code quality, vulnerability scanning
4. **Package** - Docker image or artifact
5. **Deploy Staging** - auto-deploy to test environment
6. **Deploy Production** - manual approval or auto after staging

**Tool Options:**
- GitHub Actions (free for public repos, good integration)
- GitLab CI (if using GitLab)
- Jenkins (self-hosted, more control)
- CircleCI, TravisCI (hosted options)

**Questions:**
1. Where's your code hosted? (GitHub, GitLab, etc.)
2. Where do you deploy? (AWS, GCP, Azure, VPS?)
3. Do you use containers?

Answer those and I'll give you a specific pipeline config."""
        },
    ],
    
    "clarification_needed": [
        {
            "instruction": "Fix the bug",
            "response": """I'd like to help fix the bug! Can you tell me:

1. **What's the expected behavior?**
2. **What's actually happening?**
3. **Any error messages?**
4. **Which file/function is involved?**

If you can share the relevant code or error output, I can give you a specific fix."""
        },
        {
            "instruction": "Make it faster",
            "response": """I can help optimize performance! To give good recommendations, I need to understand:

1. **What's slow?** (page load, API response, build time, query?)
2. **How slow?** (current timing vs target)
3. **Have you profiled it?** (where is time being spent?)

Share some context about what you're seeing and I'll suggest specific optimizations."""
        },
        {
            "instruction": "Update the code",
            "response": """Happy to help update code! What specifically needs to change?

- Adding a new feature?
- Fixing a bug?
- Refactoring for clarity?
- Updating dependencies?
- Changing existing behavior?

Point me to the file and tell me what you want different, and I'll make it happen."""
        },
        {
            "instruction": "Help",
            "response": """Of course! What do you need help with?

I can assist with:
- **Code** - writing, debugging, refactoring
- **Architecture** - design decisions, patterns
- **DevOps** - deployment, CI/CD, containers
- **Infrastructure** - servers, networking, cloud

What are you working on?"""
        },
        {
            "instruction": "This doesn't work",
            "response": """Let's figure out what's going wrong. Can you share:

1. **The code** that's not working
2. **What you expected** to happen
3. **What actually happens** (error message, wrong output, crash?)
4. **Steps to reproduce** if relevant

The more context you give me, the faster I can help debug it."""
        },
    ],
    
    "multi_step_workflows": [
        {
            "instruction": "I need to add a new API endpoint that fetches user orders",
            "response": """I'll help you add that endpoint. Here's my plan:

**Step 1: Define the route**
- GET `/api/users/:userId/orders`
- Add pagination (limit, offset)
- Add filters (status, date range)

**Step 2: Create the handler**
- Validate userId
- Check authorization (user can only see own orders, or admin)
- Query orders from database
- Format response

**Step 3: Add to router**
- Register route in your API router
- Add any middleware (auth, validation)

**Step 4: Test**
- Unit test for handler logic
- Integration test for full endpoint

Which framework are you using? I'll give you the specific code."""
        },
        {
            "instruction": "Set up database migrations",
            "response": """I'll help you set up migrations. Here's the approach by stack:

**For Node.js (Prisma):**
1. `npx prisma init` - creates schema.prisma
2. Define models in schema
3. `npx prisma migrate dev` - creates migration
4. `npx prisma generate` - updates client

**For Python (Alembic with SQLAlchemy):**
1. `pip install alembic`
2. `alembic init migrations`
3. Configure `alembic.ini` with DB URL
4. `alembic revision --autogenerate -m "description"`
5. `alembic upgrade head`

**For .NET (EF Core):**
1. `dotnet ef migrations add InitialCreate`
2. `dotnet ef database update`

Which stack are you using? I'll give you the specific setup."""
        },
    ],
}

ERROR_RECOVERY = {
    "common_errors": [
        {
            "instruction": "I'm getting 'Module not found' error",
            "response": """Module not found usually means one of these:

**1. Package not installed:**
```bash
npm install <package-name>
# or
pip install <package-name>
```

**2. Wrong import path:**
```javascript
// Wrong
import Thing from 'components/Thing'
// Right (check your actual path)
import Thing from './components/Thing'
import Thing from '@/components/Thing'  // if using aliases
```

**3. TypeScript path issues:**
Check `tsconfig.json` for `baseUrl` and `paths` configuration.

**4. Case sensitivity:**
Linux is case-sensitive: `Component.tsx` ≠ `component.tsx`

What's the exact error message and which file is it in?"""
        },
        {
            "instruction": "CORS error in browser",
            "response": """CORS errors mean your backend isn't allowing requests from your frontend origin.

**Quick fix (development):**
```javascript
// Express
app.use(cors({ origin: 'http://localhost:3000' }));

// FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**For production:**
- Set specific origins (not `*`)
- Only allow needed methods/headers

**If using a proxy:**
In React/Vite, add to config:
```javascript
// vite.config.js
server: {
  proxy: {
    '/api': 'http://localhost:8000'
  }
}
```

What's your frontend and backend setup?"""
        },
        {
            "instruction": "My Docker container keeps crashing",
            "response": """Let's diagnose the container crash:

**1. Check logs:**
```bash
docker logs <container_name>
docker logs --tail 100 <container_name>
```

**2. Check exit code:**
```bash
docker ps -a  # Look at STATUS column
docker inspect <container> --format='{{.State.ExitCode}}'
```

Common exit codes:
- 0: Clean exit
- 1: Application error
- 137: OOM killed (out of memory)
- 139: Segfault
- 143: SIGTERM (graceful shutdown)

**3. Run interactively:**
```bash
docker run -it <image> /bin/sh
```

**4. Check resources:**
```bash
docker stats <container>
```

What does `docker logs` show you?"""
        },
        {
            "instruction": "Database connection refused",
            "response": """Connection refused means the database isn't accepting connections. Check:

**1. Is the database running?**
```bash
# PostgreSQL
sudo systemctl status postgresql
# MySQL
sudo systemctl status mysql
# Docker
docker ps | grep postgres
```

**2. Correct host/port?**
- Local: `localhost` or `127.0.0.1`
- Docker: container name (e.g., `db`) or `host.docker.internal`
- Remote: actual IP/hostname

**3. Firewall/network?**
```bash
# Test connection
nc -zv localhost 5432
telnet localhost 5432
```

**4. Auth configured?**
- Check `pg_hba.conf` for PostgreSQL
- Check user permissions

**5. Connection string format:**
```
postgresql://user:password@host:5432/dbname
```

What database and what's your connection setup?"""
        },
        {
            "instruction": "Git says 'fatal: refusing to merge unrelated histories'",
            "response": """This happens when Git can't find a common ancestor between branches - usually when combining repos or after a `git init`.

**If you're sure you want to merge:**
```bash
git pull origin main --allow-unrelated-histories
# or
git merge <branch> --allow-unrelated-histories
```

**Then resolve any conflicts and commit.**

**Why this happens:**
- Fresh `git init` + trying to pull from existing repo
- Combining two separate repositories
- Rebasing went wrong somewhere

**Better approach if starting fresh:**
```bash
# Clone instead of init + pull
git clone <repo-url>
```

What's your situation - new repo or trying to combine existing ones?"""
        },
        {
            "instruction": "Permission denied when running npm install",
            "response": """Permission errors with npm usually mean ownership issues. Here's how to fix:

**Option 1: Fix ownership (recommended)**
```bash
sudo chown -R $(whoami) ~/.npm
sudo chown -R $(whoami) node_modules
```

**Option 2: Use a node version manager**
```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
# Then reinstall node
nvm install node
```

**Option 3: Change npm's default directory**
```bash
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
# Add to ~/.bashrc: export PATH=~/.npm-global/bin:$PATH
```

**DON'T do this:**
```bash
sudo npm install  # Creates root-owned files, makes things worse
```

Which approach would you like to try?"""
        },
    ],
    
    "debugging_strategies": [
        {
            "instruction": "My code works locally but fails in production",
            "response": """Classic environment mismatch. Here's my debugging checklist:

**1. Environment variables**
- All required vars set in production?
- Values correct? (no typos, right endpoints)
```bash
printenv | grep -i database
```

**2. Dependencies**
- Same versions? Check `package-lock.json` / `requirements.txt`
- All dependencies installed? (`npm ci` vs `npm install`)

**3. Network/endpoints**
- Database URL pointing to prod DB?
- API URLs correct?
- SSL/TLS required in prod but not local?

**4. File paths**
- Hardcoded paths that don't exist in prod?
- Case sensitivity (Linux vs Windows/Mac)

**5. Permissions**
- File/directory permissions different?
- Service account has needed access?

**6. Check logs**
```bash
# Get detailed error
docker logs <container>
journalctl -u <service>
```

What error are you seeing in production?"""
        },
        {
            "instruction": "It was working yesterday",
            "response": """Something changed - let's find what:

**1. Check recent changes:**
```bash
git log --oneline -10
git diff HEAD~5
```

**2. Check dependencies:**
```bash
# Did something update?
git diff package-lock.json
git diff requirements.txt
```

**3. External services:**
- API you depend on changed?
- Database schema changed?
- SSL cert expired?

**4. Environment:**
- Someone change env vars?
- Config file modified?

**5. System changes:**
- OS update?
- Docker/runtime version change?

**6. Quick rollback test:**
```bash
git stash  # Save current changes
git checkout <last-known-good-commit>
# Test if it works
git checkout -  # Go back
git stash pop
```

When exactly did it stop working? Can you correlate with any deploy or change?"""
        },
        {
            "instruction": "I don't know where to start debugging",
            "response": """No worries - here's a systematic approach:

**1. Reproduce the issue**
- Can you make it happen consistently?
- What are the exact steps?

**2. Read the error message carefully**
- File name and line number
- Error type/code
- Stack trace (bottom is usually most relevant)

**3. Isolate the problem**
- Comment out code until it works
- Add back piece by piece
- Find the smallest reproduction

**4. Add logging**
```javascript
console.log('checkpoint 1', { variable });
```
```python
print(f"checkpoint 1: {variable=}")
```

**5. Check recent changes**
```bash
git diff
git log --oneline -5
```

**6. Google the error**
- Copy the exact error message
- Add your framework/language
- Check Stack Overflow

**7. Rubber duck it**
- Explain the problem out loud
- Often reveals the issue

Tell me what's happening and I'll help you narrow it down."""
        },
    ],
    
    "recovery_patterns": [
        {
            "instruction": "I accidentally deleted important files",
            "response": """Don't panic - let's try to recover:

**If using Git:**
```bash
# See what was deleted
git status

# Restore deleted files
git checkout -- <filename>
git restore <filename>

# Restore everything
git checkout -- .

# If already committed the deletion
git checkout HEAD~1 -- <filename>
```

**If NOT in Git:**
```bash
# Check trash/recycle bin first

# Linux - try extundelete or testdisk
sudo extundelete /dev/sda1 --restore-file path/to/file

# Mac - check Time Machine

# Windows - check Previous Versions (right-click folder)
```

**For databases:**
- Check for backups
- Check binary logs (MySQL) or WAL (PostgreSQL)
- Point-in-time recovery if configured

What kind of files and what's your setup?"""
        },
        {
            "instruction": "I broke my git history",
            "response": """Git almost never loses data - let's fix it:

**Reflog is your friend:**
```bash
# See recent HEAD positions
git reflog

# Find the commit before things went wrong
# Reset to it
git reset --hard HEAD@{2}  # or specific hash
```

**Common fixes:**

**Undo last commit (keep changes):**
```bash
git reset --soft HEAD~1
```

**Undo bad rebase:**
```bash
git reflog
git reset --hard <hash-before-rebase>
```

**Recover deleted branch:**
```bash
git reflog
git checkout -b recovered-branch <hash>
```

**Undo bad merge:**
```bash
git reset --hard ORIG_HEAD
```

**Nuclear option (start fresh from remote):**
```bash
git fetch origin
git reset --hard origin/main
```

What happened specifically? I can give you the exact fix."""
        },
        {
            "instruction": "My database has corrupted data",
            "response": """Data corruption is serious - let's assess and recover:

**1. Stop the bleeding:**
- Identify affected records
- Consider taking app offline briefly

**2. Check backups:**
```bash
# Do you have backups?
ls -la /backups/
# Check backup integrity before restoring
```

**3. Find the scope:**
```sql
-- How bad is it?
SELECT COUNT(*) FROM table WHERE <corruption_condition>;

-- When did it start?
SELECT * FROM table 
WHERE updated_at > '2024-01-01' 
AND <corruption_condition>
ORDER BY updated_at;
```

**4. Recovery options:**
- **Restore from backup** (cleanest)
- **Fix in place** (if you know the correct values)
- **Rollback transaction logs** (if available)

**5. Find root cause:**
- Bug in application code?
- Concurrent update issue?
- Migration gone wrong?

What database and what kind of corruption are you seeing?"""
        },
    ],
}

# ============================================================================
# GENERATORS
# ============================================================================

def generate_task_planning(count: int) -> Generator[Dict, None, None]:
    """Generate task planning examples."""
    all_examples = []
    for category in TASK_PLANNING.values():
        all_examples.extend(category)
    
    for _ in range(count):
        example = random.choice(all_examples)
        yield {
            "system": SYSTEM_PROMPT,
            "instruction": example["instruction"],
            "response": example["response"].strip()
        }


def generate_error_recovery(count: int) -> Generator[Dict, None, None]:
    """Generate error recovery examples."""
    all_examples = []
    for category in ERROR_RECOVERY.values():
        all_examples.extend(category)
    
    for _ in range(count):
        example = random.choice(all_examples)
        yield {
            "system": SYSTEM_PROMPT,
            "instruction": example["instruction"],
            "response": example["response"].strip()
        }


def generate_task_variations(count: int) -> Generator[Dict, None, None]:
    """Generate variations of task planning by combining elements."""
    
    actions = [
        "Create", "Build", "Set up", "Configure", "Add", "Implement",
        "Write", "Design", "Deploy", "Migrate", "Refactor", "Optimize"
    ]
    
    targets = [
        "a REST API", "a GraphQL API", "a CLI tool", "a web scraper",
        "a cron job", "a background worker", "a webhook handler",
        "a file upload system", "a notification system", "a search feature",
        "a caching layer", "a rate limiter", "an auth system",
        "a logging system", "a metrics dashboard", "a health check endpoint"
    ]
    
    tech_stacks = [
        "using Python and FastAPI", "using Node.js and Express",
        "using TypeScript", "using Go", "using Rust",
        "using .NET Core", "using Django", "using Flask",
        "using NestJS", "using Spring Boot"
    ]
    
    plan_template = """I'll help you {action} {target} {tech}. Here's my approach:

**Step 1: Project Setup**
- Initialize project structure
- Set up dependencies
- Configure development environment

**Step 2: Core Implementation**
- Create main module/class
- Implement business logic
- Add error handling

**Step 3: Integration**
- Connect to external services if needed
- Add configuration management
- Set up environment variables

**Step 4: Testing**
- Unit tests for core logic
- Integration tests
- Manual testing

**Step 5: Documentation**
- API docs if applicable
- README with setup instructions
- Code comments for complex parts

Want me to start with Step 1? Or do you have a specific part you want to tackle first?"""

    for _ in range(count):
        action = random.choice(actions).lower()
        target = random.choice(targets)
        tech = random.choice(tech_stacks)
        
        instruction = f"{action.capitalize()} {target} {tech}"
        response = plan_template.format(action=action, target=target, tech=tech)
        
        yield {
            "system": SYSTEM_PROMPT,
            "instruction": instruction,
            "response": response
        }


def generate_error_variations(count: int) -> Generator[Dict, None, None]:
    """Generate error message variations."""
    
    error_patterns = [
        {
            "errors": [
                "TypeError: Cannot read property '{prop}' of undefined",
                "TypeError: Cannot read properties of undefined (reading '{prop}')",
                "TypeError: {var} is undefined",
            ],
            "response": """This error means you're trying to access a property on something that's `undefined`.

**Common causes:**

1. **Async data not loaded yet:**
```javascript
// Problem
const name = user.name;  // user is undefined until fetch completes

// Fix
const name = user?.name;  // Optional chaining
// or
if (user) {{ const name = user.name; }}
```

2. **Wrong variable name/typo:**
```javascript
// Check spelling
console.log(userData);  // Did you mean 'user'?
```

3. **Array access out of bounds:**
```javascript
const item = items[5];  // items might only have 3 elements
```

4. **Object key doesn't exist:**
```javascript
// Check what you actually have
console.log(Object.keys(obj));
```

Can you share the line of code causing this?"""
        },
        {
            "errors": [
                "SyntaxError: Unexpected token",
                "SyntaxError: Unexpected end of input",
                "SyntaxError: missing ) after argument list",
            ],
            "response": """Syntax error means the code structure is wrong. Common causes:

**1. Missing brackets/braces:**
```javascript
// Missing closing brace
if (condition) {{
  doSomething();
// } <- missing

// Missing parenthesis
console.log("hello"  // <- missing )
```

**2. Extra/wrong comma:**
```javascript
const obj = {{
  a: 1,
  b: 2,  // <- trailing comma can cause issues in older JS
}};
```

**3. JSON issues:**
```json
{{
  "key": "value"  // <- trailing comma not allowed in JSON
}}
```

**4. String not closed:**
```javascript
const str = "hello world;  // <- missing closing quote
```

**Tips:**
- Use an IDE with syntax highlighting
- Check the line BEFORE the error (often the real issue)
- Use a linter (ESLint)

What's the exact error and which file?"""
        },
        {
            "errors": [
                "ENOENT: no such file or directory",
                "FileNotFoundError: [Errno 2] No such file or directory",
                "Error: ENOENT: no such file or directory, open '{path}'",
            ],
            "response": """File not found error. Let's check:

**1. Does the file exist?**
```bash
ls -la /path/to/file
```

**2. Is the path correct?**
- Relative vs absolute path
- Current working directory matters for relative paths
```javascript
console.log(process.cwd());  // Node.js
```
```python
import os; print(os.getcwd())  # Python
```

**3. Case sensitivity:**
- Linux is case-sensitive: `File.txt` ≠ `file.txt`

**4. Path construction:**
```javascript
// Better
const path = require('path');
const filePath = path.join(__dirname, 'data', 'file.txt');

// Avoid
const filePath = './data/file.txt';  // Relative to cwd, not script
```

**5. Permissions:**
```bash
ls -la /path/to/directory/
```

What's the full path and where is your code running from?"""
        },
    ]
    
    props = ["name", "id", "data", "value", "length", "map", "forEach", "items", "result"]
    vars = ["user", "data", "response", "result", "config", "items", "options"]
    paths = ["/app/config.json", "./data/users.json", "../config/settings.yaml", "/var/log/app.log"]
    
    for _ in range(count):
        pattern = random.choice(error_patterns)
        error = random.choice(pattern["errors"])
        
        # Fill in placeholders
        error = error.format(
            prop=random.choice(props),
            var=random.choice(vars),
            path=random.choice(paths)
        )
        
        yield {
            "system": SYSTEM_PROMPT,
            "instruction": f"I'm getting this error: {error}",
            "response": pattern["response"]
        }


def main():
    parser = argparse.ArgumentParser(description="Generate task planning and error recovery data")
    parser.add_argument("--output", "-o", type=str, default="../data/generated_planning.jsonl")
    parser.add_argument("--count", "-n", type=int, default=500)
    parser.add_argument("--category", "-c", type=str, 
                        choices=["planning", "errors", "all"], default="all")
    parser.add_argument("--seed", type=int, default=None)
    
    args = parser.parse_args()
    
    if args.seed:
        random.seed(args.seed)
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating task planning and error recovery data...")
    print(f"  Output: {output_path}")
    print(f"  Count: {args.count}")
    
    examples = []
    
    if args.category in ["planning", "all"]:
        planning_count = args.count // 2 if args.category == "all" else args.count
        print(f"  Generating {planning_count} task planning examples...")
        examples.extend(list(generate_task_planning(planning_count // 3)))
        examples.extend(list(generate_task_variations(planning_count * 2 // 3)))
    
    if args.category in ["errors", "all"]:
        error_count = args.count // 2 if args.category == "all" else args.count
        print(f"  Generating {error_count} error recovery examples...")
        examples.extend(list(generate_error_recovery(error_count // 2)))
        examples.extend(list(generate_error_variations(error_count // 2)))
    
    random.shuffle(examples)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"\n✅ Generated {len(examples)} examples")
    print(f"   Saved to: {output_path}")


if __name__ == "__main__":
    main()
