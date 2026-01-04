#!/usr/bin/env python3
"""
VS Code & IDE Workflows Training Data Generator
Target: ~200 examples for IDE operations, debugging, extensions, settings
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SYSTEM_PROMPT = """You are AJ, an expert AI assistant for VS Code and IDE workflows.
You help with editor configuration, debugging, extensions, keybindings, and development workflows."""

# =============================================================================
# TOOL SELECTION TASKS
# =============================================================================

BASIC_IDE_TASKS = [
    {
        "instruction": "Open the file src/components/Header.tsx",
        "tool": "read_file",
        "parameters": {"filePath": "src/components/Header.tsx", "startLine": 1, "endLine": 100}
    },
    {
        "instruction": "Find all TypeScript files in the project",
        "tool": "file_search",
        "parameters": {"query": "**/*.ts"}
    },
    {
        "instruction": "Search for 'TODO' comments in the codebase",
        "tool": "grep_search",
        "parameters": {"query": "TODO", "isRegexp": False}
    },
    {
        "instruction": "List files in the src directory",
        "tool": "list_dir",
        "parameters": {"path": "src"}
    },
    {
        "instruction": "Create a new file called utils/helpers.ts",
        "tool": "create_file",
        "parameters": {"filePath": "utils/helpers.ts", "content": "// Helper utilities\n"}
    },
    {
        "instruction": "Show me the errors in the current project",
        "tool": "get_errors",
        "parameters": {}
    },
    {
        "instruction": "Find where the function calculateTotal is defined",
        "tool": "list_code_usages",
        "parameters": {"symbolName": "calculateTotal"}
    },
    {
        "instruction": "Search for files named config",
        "tool": "file_search",
        "parameters": {"query": "**/config.*"}
    },
    {
        "instruction": "Find all React components that use useState",
        "tool": "grep_search",
        "parameters": {"query": "useState", "isRegexp": False, "includePattern": "**/*.tsx"}
    },
    {
        "instruction": "Look for environment variable usage",
        "tool": "grep_search",
        "parameters": {"query": "process\\.env\\.|import\\.meta\\.env", "isRegexp": True}
    },
    # NEW: Additional basic IDE tasks
    {
        "instruction": "Find all Python files in the tests folder",
        "tool": "file_search",
        "parameters": {"query": "tests/**/*.py"}
    },
    {
        "instruction": "Show me the package.json file",
        "tool": "read_file",
        "parameters": {"filePath": "package.json", "startLine": 1, "endLine": 100}
    },
    {
        "instruction": "Search for all import statements",
        "tool": "grep_search",
        "parameters": {"query": "^import ", "isRegexp": True}
    },
    {
        "instruction": "Find all FIXME comments",
        "tool": "grep_search",
        "parameters": {"query": "FIXME|HACK|XXX", "isRegexp": True}
    },
    {
        "instruction": "List what's in the root directory",
        "tool": "list_dir",
        "parameters": {"path": "."}
    },
    {
        "instruction": "Create a new README.md file",
        "tool": "create_file",
        "parameters": {"filePath": "README.md", "content": "# Project Title\n\nDescription here.\n"}
    },
    {
        "instruction": "Find all Jest test files",
        "tool": "file_search",
        "parameters": {"query": "**/*.test.{ts,tsx,js,jsx}"}
    },
    {
        "instruction": "Search for unused imports",
        "tool": "get_errors",
        "parameters": {}
    },
    {
        "instruction": "Find the main entry point file",
        "tool": "file_search",
        "parameters": {"query": "**/index.{ts,tsx,js,jsx}"}
    },
    {
        "instruction": "Look for any API keys in the code",
        "tool": "grep_search",
        "parameters": {"query": "api[_-]?key|apiKey|API_KEY", "isRegexp": True}
    },
    {
        "instruction": "Find all CSS or SCSS files",
        "tool": "file_search",
        "parameters": {"query": "**/*.{css,scss,less}"}
    },
    {
        "instruction": "Search for fetch or axios calls",
        "tool": "grep_search",
        "parameters": {"query": "fetch\\(|axios\\.", "isRegexp": True}
    },
    {
        "instruction": "Find configuration files",
        "tool": "file_search",
        "parameters": {"query": "**/*.config.{js,ts,json}"}
    },
    {
        "instruction": "Look for class components in React",
        "tool": "grep_search",
        "parameters": {"query": "class.*extends.*Component", "isRegexp": True}
    },
    {
        "instruction": "Find all markdown files",
        "tool": "file_search",
        "parameters": {"query": "**/*.md"}
    },
    {
        "instruction": "Search for database queries",
        "tool": "grep_search",
        "parameters": {"query": "SELECT|INSERT|UPDATE|DELETE|prisma\\.", "isRegexp": True}
    },
    {
        "instruction": "Find Docker-related files",
        "tool": "file_search",
        "parameters": {"query": "**/Dockerfile*"}
    },
    {
        "instruction": "List the contents of node_modules/@types",
        "tool": "list_dir",
        "parameters": {"path": "node_modules/@types"}
    },
    {
        "instruction": "Find all async functions",
        "tool": "grep_search",
        "parameters": {"query": "async\\s+(function|\\()", "isRegexp": True}
    },
    {
        "instruction": "Search for error handling patterns",
        "tool": "grep_search",
        "parameters": {"query": "try\\s*\\{|catch\\s*\\(|\\.catch\\(", "isRegexp": True}
    },
]

ADVANCED_IDE_TASKS = [
    {
        "instruction": "Find all usages of the UserContext across the project",
        "tool": "list_code_usages",
        "parameters": {"symbolName": "UserContext", "filePaths": ["src/contexts/UserContext.tsx"]}
    },
    {
        "instruction": "Search for deprecated API usage patterns",
        "tool": "grep_search",
        "parameters": {"query": "@deprecated|componentWillMount|componentWillUpdate", "isRegexp": True}
    },
    {
        "instruction": "Find all test files that test the auth module",
        "tool": "grep_search",
        "parameters": {"query": "auth|Auth|authentication", "isRegexp": True, "includePattern": "**/*.test.{ts,tsx,js}"}
    },
    {
        "instruction": "Check for console.log statements that should be removed",
        "tool": "grep_search",
        "parameters": {"query": "console\\.(log|debug|info)", "isRegexp": True}
    },
    {
        "instruction": "Find all files importing from @mui/material",
        "tool": "grep_search",
        "parameters": {"query": "from ['\"]@mui/material", "isRegexp": True}
    },
    {
        "instruction": "Search for hardcoded URLs in the codebase",
        "tool": "grep_search",
        "parameters": {"query": "https?://[^\\s'\"]+", "isRegexp": True}
    },
    {
        "instruction": "Find files with more than one default export",
        "tool": "grep_search",
        "parameters": {"query": "export default", "isRegexp": False}
    },
    {
        "instruction": "Locate all GraphQL queries and mutations",
        "tool": "grep_search",
        "parameters": {"query": "gql`|useQuery|useMutation", "isRegexp": True}
    },
    {
        "instruction": "Find circular dependency patterns",
        "tool": "semantic_search",
        "parameters": {"query": "circular dependency import export module"}
    },
    {
        "instruction": "Search for async functions without try-catch",
        "tool": "grep_search",
        "parameters": {"query": "async.*\\{[^}]*await[^}]*\\}", "isRegexp": True}
    },
    {
        "instruction": "Find all Tailwind CSS classes being used",
        "tool": "grep_search",
        "parameters": {"query": "className=['\"][^'\"]+['\"]", "isRegexp": True}
    },
    {
        "instruction": "Locate all API endpoint definitions",
        "tool": "grep_search",
        "parameters": {"query": "@(Get|Post|Put|Delete|Patch)|router\\.(get|post|put|delete)", "isRegexp": True}
    },
    # NEW: Additional advanced IDE tasks
    {
        "instruction": "Find all React hooks that have dependency arrays",
        "tool": "grep_search",
        "parameters": {"query": "use(Effect|Callback|Memo)\\([^)]+,\\s*\\[", "isRegexp": True}
    },
    {
        "instruction": "Search for potential memory leaks in useEffect",
        "tool": "grep_search",
        "parameters": {"query": "useEffect\\([^)]*\\{[^}]*(?!return)[^}]*\\}", "isRegexp": True}
    },
    {
        "instruction": "Find all Redux actions and reducers",
        "tool": "grep_search",
        "parameters": {"query": "createSlice|createAction|createReducer|dispatch\\(", "isRegexp": True}
    },
    {
        "instruction": "Locate all form validation schemas",
        "tool": "grep_search",
        "parameters": {"query": "yup\\.|zod\\.|Joi\\.", "isRegexp": True}
    },
    {
        "instruction": "Find components with inline styles",
        "tool": "grep_search",
        "parameters": {"query": "style=\\{\\{", "isRegexp": True}
    },
    {
        "instruction": "Search for magic numbers in the code",
        "tool": "grep_search",
        "parameters": {"query": "(?<!['\"])\\b\\d{2,}\\b(?!['\"])", "isRegexp": True}
    },
    {
        "instruction": "Find all event listener additions",
        "tool": "grep_search",
        "parameters": {"query": "addEventListener|on[A-Z][a-z]+\\s*=", "isRegexp": True}
    },
    {
        "instruction": "Locate all type assertions in TypeScript",
        "tool": "grep_search",
        "parameters": {"query": "as\\s+[A-Z]|<[A-Z][a-z]+>", "isRegexp": True}
    },
    {
        "instruction": "Find all uses of the any type",
        "tool": "grep_search",
        "parameters": {"query": ":\\s*any[^a-z]", "isRegexp": True}
    },
    {
        "instruction": "Search for commented out code blocks",
        "tool": "grep_search",
        "parameters": {"query": "//.*\\{|/\\*[^*]*\\*/", "isRegexp": True}
    },
    {
        "instruction": "Find all custom hooks in the project",
        "tool": "grep_search",
        "parameters": {"query": "function\\s+use[A-Z]|const\\s+use[A-Z]", "isRegexp": True}
    },
    {
        "instruction": "Locate all zustand store definitions",
        "tool": "grep_search",
        "parameters": {"query": "create\\(.*set.*=>|useStore", "isRegexp": True}
    },
    {
        "instruction": "Find all Next.js API routes",
        "tool": "file_search",
        "parameters": {"query": "pages/api/**/*.{ts,js}"}
    },
    {
        "instruction": "Search for potential XSS vulnerabilities",
        "tool": "grep_search",
        "parameters": {"query": "dangerouslySetInnerHTML|innerHTML\\s*=", "isRegexp": True}
    },
    {
        "instruction": "Find all useRef usages without cleanup",
        "tool": "grep_search",
        "parameters": {"query": "useRef\\(", "isRegexp": True}
    },
    {
        "instruction": "Locate all context providers",
        "tool": "grep_search",
        "parameters": {"query": "createContext|Provider\\s+value=", "isRegexp": True}
    },
    {
        "instruction": "Find files exceeding 500 lines",
        "tool": "semantic_search",
        "parameters": {"query": "large files code organization refactoring"}
    },
    {
        "instruction": "Search for direct DOM manipulation",
        "tool": "grep_search",
        "parameters": {"query": "document\\.(getElementById|querySelector|getElement)", "isRegexp": True}
    },
    {
        "instruction": "Find all environment-specific configurations",
        "tool": "file_search",
        "parameters": {"query": "**/*.{env,env.*,development,production}.{json,ts,js}"}
    },
    {
        "instruction": "Locate all lazy-loaded components",
        "tool": "grep_search",
        "parameters": {"query": "React\\.lazy|dynamic\\(|loadable\\(", "isRegexp": True}
    },
]

DEBUGGING_TASKS = [
    {
        "instruction": "Run the tests for the auth module",
        "tool": "runTests",
        "parameters": {"files": ["src/auth/__tests__"]}
    },
    {
        "instruction": "Check for syntax errors in app.py",
        "tool": "get_errors",
        "parameters": {"filePaths": ["app.py"]}
    },
    {
        "instruction": "Run all unit tests with coverage",
        "tool": "runTests",
        "parameters": {"mode": "coverage"}
    },
    {
        "instruction": "Execute the specific test for login functionality",
        "tool": "runTests",
        "parameters": {"testNames": ["test_login_success", "test_login_failure"]}
    },
    # NEW: Additional debugging tasks
    {
        "instruction": "Run all tests in the components folder",
        "tool": "runTests",
        "parameters": {"files": ["src/components/**/*.test.tsx"]}
    },
    {
        "instruction": "Check TypeScript errors in the entire project",
        "tool": "get_errors",
        "parameters": {}
    },
    {
        "instruction": "Run tests matching 'user' in the name",
        "tool": "runTests",
        "parameters": {"testNames": ["*user*"]}
    },
    {
        "instruction": "Get coverage for the utils module",
        "tool": "runTests",
        "parameters": {"mode": "coverage", "coverageFiles": ["src/utils"]}
    },
    {
        "instruction": "Run integration tests only",
        "tool": "runTests",
        "parameters": {"files": ["tests/integration/**/*.test.ts"]}
    },
    {
        "instruction": "Check for errors in all TypeScript files",
        "tool": "get_errors",
        "parameters": {"filePaths": ["**/*.ts", "**/*.tsx"]}
    },
    {
        "instruction": "Run the API endpoint tests",
        "tool": "runTests",
        "parameters": {"files": ["tests/api/*.test.ts"]}
    },
    {
        "instruction": "Execute snapshot tests",
        "tool": "runTests",
        "parameters": {"testNames": ["*snapshot*", "*Snapshot*"]}
    },
    {
        "instruction": "Get detailed coverage for specific file",
        "tool": "runTests",
        "parameters": {"mode": "coverage", "coverageFiles": ["src/services/AuthService.ts"]}
    },
    {
        "instruction": "Run e2e tests",
        "tool": "runTests",
        "parameters": {"files": ["e2e/**/*.spec.ts"]}
    },
]

# =============================================================================
# MULTI-STEP PLANNING TASKS
# =============================================================================

PLANNING_TASKS = [
    {
        "instruction": "Set up a new debugging configuration for Node.js",
        "steps": [
            "Check if .vscode/launch.json exists",
            "Create or update launch.json with Node.js debug configuration",
            "Add breakpoint configurations for common debugging scenarios",
            "Create compound configuration for debugging with tests"
        ]
    },
    {
        "instruction": "Configure VS Code for a Python project with linting and formatting",
        "steps": [
            "Check for existing .vscode/settings.json",
            "Configure Python interpreter path",
            "Set up pylint or flake8 as linter",
            "Configure black or autopep8 as formatter",
            "Add format-on-save settings"
        ]
    },
    {
        "instruction": "Create a workspace configuration for a monorepo",
        "steps": [
            "Analyze repository structure to identify packages/projects",
            "Create .vscode/workspace.code-workspace file",
            "Configure per-folder settings for each package",
            "Set up task configurations for building each package",
            "Add recommended extensions for the workspace"
        ]
    },
    {
        "instruction": "Set up code snippets for React development",
        "steps": [
            "Check existing .vscode/snippets or global snippets",
            "Create typescriptreact.json for TSX snippets",
            "Add functional component snippet",
            "Add hooks snippets (useState, useEffect, useCallback)",
            "Add testing snippets for Jest/React Testing Library"
        ]
    },
    {
        "instruction": "Configure multi-root workspace with different linting rules",
        "steps": [
            "Create workspace file with all project folders",
            "Configure folder-specific ESLint settings",
            "Set up different TypeScript configurations per folder",
            "Configure task runners for each project"
        ]
    },
    {
        "instruction": "Migrate VS Code settings from one machine to another",
        "steps": [
            "Export current settings.json",
            "Export keybindings.json",
            "List installed extensions",
            "Create setup script or Settings Sync configuration",
            "Document workspace-specific settings"
        ]
    },
    # NEW: Additional planning tasks
    {
        "instruction": "Set up VS Code for Rust development",
        "steps": [
            "Install rust-analyzer extension",
            "Configure Cargo as the build system in tasks.json",
            "Set up launch.json for debugging with CodeLLDB or LLDB",
            "Configure settings for format-on-save with rustfmt",
            "Add clippy linting configuration",
            "Set up test runner integration"
        ]
    },
    {
        "instruction": "Configure VS Code for a Django project",
        "steps": [
            "Set up Python virtual environment selection",
            "Configure Django-specific settings in settings.json",
            "Create launch.json for debugging Django server",
            "Configure pytest or Django test runner",
            "Set up HTML/template file associations",
            "Add Django snippets extension"
        ]
    },
    {
        "instruction": "Set up remote development with SSH",
        "steps": [
            "Install Remote - SSH extension",
            "Configure SSH host in ~/.ssh/config",
            "Add host entry to VS Code Remote Explorer",
            "Set up key-based authentication",
            "Configure remote-specific settings",
            "Install necessary extensions on remote"
        ]
    },
    {
        "instruction": "Configure VS Code for Docker development",
        "steps": [
            "Install Docker extension",
            "Create Dockerfile with proper structure",
            "Set up docker-compose.yml if needed",
            "Configure launch.json for debugging in containers",
            "Set up tasks for build and run commands",
            "Configure Remote - Containers for development"
        ]
    },
    {
        "instruction": "Set up a complete Java development environment",
        "steps": [
            "Install Extension Pack for Java",
            "Configure JDK path in settings",
            "Set up Maven or Gradle tasks",
            "Configure launch.json for Java debugging",
            "Set up test runner integration",
            "Configure code formatting with Google Java Format"
        ]
    },
    {
        "instruction": "Configure VS Code for Go development",
        "steps": [
            "Install Go extension (gopls)",
            "Configure GOPATH and GOROOT settings",
            "Set up debugging with Delve",
            "Configure test runner and coverage",
            "Enable format-on-save with gofmt/goimports",
            "Set up linting with golangci-lint"
        ]
    },
    {
        "instruction": "Set up collaborative development with Live Share",
        "steps": [
            "Install Live Share extension pack",
            "Configure sharing permissions and settings",
            "Set up audio call integration",
            "Configure read-only vs. edit permissions",
            "Set up shared terminals and servers",
            "Configure session auto-sharing"
        ]
    },
    {
        "instruction": "Configure VS Code for Kubernetes development",
        "steps": [
            "Install Kubernetes extension",
            "Set up kubeconfig file access",
            "Install YAML language support",
            "Configure Helm chart support",
            "Set up kubectl task shortcuts",
            "Configure port forwarding for debugging"
        ]
    },
    {
        "instruction": "Set up VS Code for database development",
        "steps": [
            "Install database client extension (SQLTools, etc.)",
            "Configure database connections",
            "Set up SQL file associations and highlighting",
            "Configure query execution shortcuts",
            "Set up result export functionality",
            "Add SQL formatting and linting"
        ]
    },
    {
        "instruction": "Configure GitHub Copilot in VS Code",
        "steps": [
            "Install GitHub Copilot extension",
            "Sign in with GitHub account",
            "Configure suggestion settings (inline, panel)",
            "Set up keybindings for accept/reject suggestions",
            "Configure language-specific enable/disable",
            "Set up Copilot Chat integration"
        ]
    },
    {
        "instruction": "Set up a complete testing workflow",
        "steps": [
            "Install Test Explorer extension",
            "Configure test framework (Jest, Mocha, pytest, etc.)",
            "Set up launch.json for debugging tests",
            "Configure coverage reporting",
            "Set up test file associations",
            "Create tasks for running test subsets"
        ]
    },
    {
        "instruction": "Configure VS Code for C++ development",
        "steps": [
            "Install C/C++ extension",
            "Configure compiler path (gcc/clang/MSVC)",
            "Set up c_cpp_properties.json for IntelliSense",
            "Configure CMake or build tasks",
            "Set up debugging with GDB/LLDB",
            "Configure clang-format for code formatting"
        ]
    },
    {
        "instruction": "Set up VS Code for Terraform/Infrastructure as Code",
        "steps": [
            "Install HashiCorp Terraform extension",
            "Configure terraform formatter",
            "Set up validation and linting",
            "Configure workspace settings for .tf files",
            "Set up tasks for terraform commands",
            "Add snippets for common resources"
        ]
    },
    {
        "instruction": "Configure VS Code for Flutter development",
        "steps": [
            "Install Flutter and Dart extensions",
            "Configure Flutter SDK path",
            "Set up device emulator integration",
            "Configure launch.json for debugging",
            "Set up hot reload shortcuts",
            "Configure DevTools integration"
        ]
    },
]

# =============================================================================
# CONCEPT Q&A
# =============================================================================

BASIC_CONCEPTS = [
    {
        "question": "What is the VS Code Command Palette?",
        "answer": "The Command Palette (Ctrl+Shift+P / Cmd+Shift+P) is VS Code's central hub for accessing all commands and features. It provides fuzzy search across all available commands, recently used commands appear first, and you can access it from anywhere in the editor. Common uses include changing settings, running tasks, git operations, and installing extensions."
    },
    {
        "question": "How do VS Code workspaces differ from folders?",
        "answer": "A folder is simply opening a directory in VS Code. A workspace (.code-workspace file) is a collection of one or more folders with shared settings. Workspaces enable: multi-root development (multiple project folders), workspace-specific settings that don't affect user settings, shared task and launch configurations, and per-folder settings in multi-root scenarios."
    },
    {
        "question": "What are VS Code tasks?",
        "answer": "Tasks (tasks.json) automate common operations like building, testing, or deploying. They can run shell commands, be bound to keyboard shortcuts, have problem matchers to parse output for errors, be configured as build or test tasks for quick access (Ctrl+Shift+B), and support variables like ${workspaceFolder} and ${file}."
    },
    {
        "question": "How does IntelliSense work in VS Code?",
        "answer": "IntelliSense provides intelligent code completion powered by language services. It includes: auto-completion based on language semantics, parameter hints showing function signatures, quick info on hover, go-to-definition and find references, and type inference and error detection. Different languages get IntelliSense through extensions (like Pylance for Python, or built-in for TypeScript)."
    },
    {
        "question": "What is the integrated terminal in VS Code?",
        "answer": "The integrated terminal (Ctrl+`) runs a shell directly in VS Code. Key features: multiple terminal instances, split terminals, shell selection (bash, PowerShell, zsh), automatic working directory set to workspace, terminal profiles for quick access, and integration with tasks. Terminals can be renamed, colored, and persisted across sessions."
    },
    {
        "question": "How do I install extensions in VS Code?",
        "answer": "Extensions are installed via the Extensions view (Ctrl+Shift+X). You can search the marketplace, view ratings and downloads, read reviews, and install with one click. Extensions can also be installed via command line: code --install-extension publisher.extension. For offline use, download .vsix files and install via 'Install from VSIX' command."
    },
    {
        "question": "What is the Activity Bar in VS Code?",
        "answer": "The Activity Bar is the vertical bar on the far left showing icons for different views: Explorer (files), Search, Source Control, Run and Debug, Extensions. Clicking icons switches the Side Bar content. You can reorder, hide, or add custom views. Extensions can contribute their own Activity Bar icons."
    },
    {
        "question": "How does file navigation work in VS Code?",
        "answer": "VS Code offers multiple navigation methods: Explorer tree view, Quick Open (Ctrl+P) for fuzzy file search, breadcrumbs for path navigation, Go to Symbol (Ctrl+Shift+O) for code symbols, and recently opened files (Ctrl+Tab). You can also use Ctrl+Click on imports to jump to definitions."
    },
    {
        "question": "What are VS Code snippets?",
        "answer": "Snippets are code templates you can insert quickly. Trigger by typing a prefix and pressing Tab. They support: tabstops for cursor positioning, placeholders with default values, choice lists, variable substitution (like $TM_FILENAME), and nested tabstops. Create custom snippets via Preferences: Configure User Snippets."
    },
    {
        "question": "How does VS Code handle version control?",
        "answer": "VS Code has built-in Git support accessible via Source Control view (Ctrl+Shift+G). Features include: viewing changes, staging files, committing, pushing/pulling, branch management, merge conflict resolution, viewing diffs, blame annotations via GitLens extension, and timeline view for file history."
    },
    {
        "question": "What is the minimap in VS Code?",
        "answer": "The minimap is a high-level overview of your code shown on the right side of the editor. It provides quick visual navigation - click to jump to that location. Shows syntax highlighting, search highlights, and git changes. Can be configured: enable/disable, show slider, rendering mode (blocks/actual characters), and size."
    },
    {
        "question": "How do editor groups work in VS Code?",
        "answer": "Editor groups let you split the editor into multiple panes. Drag tabs to create new groups, use Ctrl+\\ to split, or View > Editor Layout. You can have vertical splits, horizontal splits, or grid layouts. Each group maintains its own tab bar and scrolls independently. Close groups by closing all tabs in them."
    },
    {
        "question": "What is the Problems panel in VS Code?",
        "answer": "The Problems panel (Ctrl+Shift+M) shows errors, warnings, and info from linters, compilers, and language services. It aggregates issues from all open files, allows filtering by type or text, and clicking jumps to the problem location. Problem counts are shown in the status bar."
    },
    {
        "question": "How does search work in VS Code?",
        "answer": "VS Code provides file search (Ctrl+Shift+F) across the workspace. Features: regex support, case sensitivity, whole word matching, include/exclude patterns, replace all, search in open editors only, and result grouping. Search results show context and clicking opens the file at that line."
    },
    {
        "question": "What are VS Code keybindings?",
        "answer": "Keybindings map keyboard shortcuts to commands. View and customize via File > Preferences > Keyboard Shortcuts (Ctrl+K Ctrl+S). Features: search by key or command, reset to default, add custom keybindings in keybindings.json, context-specific bindings (when clause), and extension keybindings. You can install keymap extensions for other editors."
    },
    {
        "question": "How does VS Code handle different file encodings?",
        "answer": "VS Code auto-detects file encoding and shows it in the status bar. Click to change encoding for save or reopen. Settings: files.encoding sets default, files.autoGuessEncoding enables detection. Supports UTF-8, UTF-16, ISO-8859 variants, and many others. Be careful with encoding changes on existing files."
    },
    {
        "question": "What is the Output panel in VS Code?",
        "answer": "The Output panel shows logs from VS Code and extensions. Use the dropdown to switch between channels: Git, Tasks, Extensions, language servers like TypeScript or Python. Useful for debugging when things don't work - check the relevant output channel for error messages."
    },
    {
        "question": "How do I use multiple cursors in VS Code?",
        "answer": "Multiple cursors enable simultaneous editing. Add cursors: Alt+Click, Ctrl+Alt+Up/Down, or Ctrl+D to select next occurrence. Ctrl+Shift+L selects all occurrences. Type normally and all cursors receive input. Box selection: Shift+Alt+drag. Escape returns to single cursor."
    },
]

ADVANCED_CONCEPTS = [
    {
        "question": "How does VS Code's Language Server Protocol work?",
        "answer": "The Language Server Protocol (LSP) standardizes communication between editors and language servers. The editor acts as a client, language servers run as separate processes, communication happens via JSON-RPC over stdio or sockets. Benefits include: one language server works with many editors, features like completion/diagnostics/navigation are server-provided, and it enables rich tooling without editor-specific code. Examples: Pylance, TypeScript language server, gopls."
    },
    {
        "question": "What is the Debug Adapter Protocol in VS Code?",
        "answer": "The Debug Adapter Protocol (DAP) standardizes debugging across languages. Similar to LSP, VS Code communicates with debug adapters via protocol. Adapters translate between VS Code's debug UI and language-specific debuggers. This enables consistent debugging experience across languages, compound debug configurations, and custom debug visualizations. Configuration lives in launch.json."
    },
    {
        "question": "How do VS Code extension host processes work?",
        "answer": "VS Code runs extensions in separate processes called Extension Hosts to maintain UI responsiveness. The main process handles rendering and user input, Extension Host runs all extensions in a Node.js process, they communicate via IPC. There can be multiple hosts: Local Extension Host (runs on local machine), Remote Extension Host (runs on remote/container), and Web Extension Host (runs in browser). Extensions can specify where they need to run via extensionKind."
    },
    {
        "question": "What are VS Code's workspace trust implications?",
        "answer": "Workspace Trust is a security feature protecting against malicious code in opened folders. Restricted Mode disables: task execution, debugging, certain extensions, and terminal profiles from workspace. Trust is per-folder and can be configured globally. Extensions must declare trust requirements and some features only work in trusted workspaces. This prevents attacks from opening malicious repositories."
    },
    {
        "question": "How does VS Code handle remote development?",
        "answer": "VS Code Remote Development uses a client-server architecture. The local VS Code acts as a thin client while a VS Code Server runs on the remote target (SSH, container, WSL). Extensions run where appropriate (UI extensions local, workspace extensions remote). File system access, terminals, and debugging happen on the remote. This provides full development capabilities with local UI performance."
    },
    {
        "question": "What is VS Code's extension API architecture?",
        "answer": "VS Code extensions use a contribution-based architecture. The package.json declares contributions (commands, views, settings), while activate() is called when extension is first needed. Extensions can contribute: commands, views, languages, debuggers, themes, snippets, and more. The vscode module provides APIs for editor manipulation, file system, workspace, and UI components. Extensions should be lazy-loaded for performance."
    },
    {
        "question": "How does VS Code's settings resolution work?",
        "answer": "VS Code settings have a hierarchy: Default settings < User settings < Workspace settings < Folder settings (in multi-root). Language-specific settings override general ones. Settings can be scoped to specific contexts. The settings.json is merged at each level. Settings sync can synchronize user settings across machines while respecting machine-specific overrides."
    },
    {
        "question": "What is the Virtual Workspaces concept in VS Code?",
        "answer": "Virtual Workspaces allow working with non-local file systems like GitHub repositories, FTP servers, or cloud storage without cloning. Extensions implement virtual file system providers. Not all features work - some require local file access. Extensions can declare virtualWorkspaces capability to indicate support level. This enables quick browsing and light edits without full project setup."
    },
    {
        "question": "How do source maps work for debugging in VS Code?",
        "answer": "Source maps connect compiled/transpiled code back to original sources. VS Code's debugger reads .map files to display original code during debugging. Key settings in launch.json: sourceMap (enable), outFiles (where to find compiled JS), sourceMapPathOverrides (fix path mismatches). Common issues include path mismatches, missing maps, or stale maps after rebuilds."
    },
    {
        "question": "What is VS Code's file watcher and how does it work?",
        "answer": "VS Code watches files for changes using OS-native APIs (inotify on Linux, FSEvents on macOS, ReadDirectoryChangesW on Windows). Watchers trigger: file tree updates, search index updates, and extension notifications. Large workspaces can exceed OS watcher limits - configure files.watcherExclude to reduce load. Performance issues often trace to watching node_modules or other large directories."
    },
    {
        "question": "How does VS Code's extension bisect feature work?",
        "answer": "Extension bisect helps identify problematic extensions. Run 'Help: Start Extension Bisect' - VS Code disables half your extensions, you report if the issue persists, and it binary searches to find the culprit. This is efficient for debugging performance issues or bugs caused by extension conflicts. Much faster than manually disabling extensions one by one."
    },
    {
        "question": "What are VS Code profiles and how do they work?",
        "answer": "Profiles let you create different VS Code configurations for different workflows. Each profile has its own: extensions, settings, keybindings, UI state, snippets, and tasks. Create via Settings gear > Profiles. Useful for: work vs personal, different languages/frameworks, teaching vs development. Profiles can be exported/imported and synced. Switch quickly via Ctrl+Shift+P > Profiles."
    },
    {
        "question": "How does VS Code handle large files?",
        "answer": "VS Code has protections for large files to maintain performance. Files over editor.largeFileOptimizations size (default 20MB) disable features like tokenization and folding. Very large files trigger a warning. For huge files, consider: splitting the file, using a different tool, or disabling minimap/wordWrap. Language features may also be limited on large files to prevent UI freezing."
    },
    {
        "question": "What is the difference between launch and attach debugging?",
        "answer": "Launch starts a new process with debugging from the beginning - VS Code spawns the program. Attach connects to an already-running process - useful for servers, long-running applications, or processes started outside VS Code. Launch configs specify program/args, attach configs specify process ID or port. Some scenarios require attach: debugging remote processes, docker containers, or production-like environments."
    },
    {
        "question": "How does VS Code's semantic highlighting work?",
        "answer": "Semantic highlighting enhances syntax highlighting with language-aware coloring from the language server. While syntax highlighting is regex-based, semantic highlighting understands code semantics - distinguishing local vs global variables, mutable vs immutable, etc. Configured via editor.semanticHighlighting.enabled. Language servers provide semantic tokens that VS Code maps to theme colors."
    },
    {
        "question": "What are VS Code Dev Containers?",
        "answer": "Dev Containers define development environments in Docker containers configured via devcontainer.json. Benefits: reproducible environments, isolated dependencies, team consistency, and easy onboarding. Features include: forwarded ports, mounted volumes, post-create commands, and extension auto-installation. The container runs the VS Code Server while you use the local UI. Works with Docker Desktop or remote Docker hosts."
    },
    {
        "question": "How does VS Code's compound launch configurations work?",
        "answer": "Compound configurations launch multiple debug sessions simultaneously. Defined in launch.json with type 'compound' and a list of configuration names. Useful for: full-stack debugging (frontend + backend), microservices, or client-server applications. All sessions start together and can be controlled independently. The debug toolbar shows a dropdown to switch between active sessions."
    },
    {
        "question": "What is workspace state vs global state in extensions?",
        "answer": "Extensions can store persistent data in two scopes: workspaceState (per-workspace, stored in .vscode folder) and globalState (per-user, stored in user data directory). Use workspaceState for project-specific data like recent files or project preferences. Use globalState for user preferences that should persist across all workspaces. Both are key-value stores with async get/update operations."
    },
]

# =============================================================================
# ERROR/GUARDRAIL SCENARIOS
# =============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "VS Code is running slow and using too much memory",
        "error_type": "performance",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Open Process Explorer: Help > Open Process Explorer",
                "Check Extension Host CPU/memory usage",
                "Run 'Developer: Show Running Extensions' to find slow extensions",
                "Check for large files causing indexing issues"
            ],
            "common_solutions": [
                "Disable unused extensions",
                "Exclude large folders from search: files.exclude, search.exclude",
                "Reduce git.autorefresh frequency",
                "Disable telemetry if not needed",
                "Clear extension cache: delete ~/.vscode/extensions/.obsolete"
            ],
            "warnings": ["Don't disable essential extensions without testing"]
        }
    },
    {
        "instruction": "IntelliSense stopped working for TypeScript",
        "error_type": "language_service",
        "response": {
            "status": "recoverable",
            "diagnostic_steps": [
                "Check TypeScript version: 'TypeScript: Select TypeScript Version'",
                "Look for tsconfig.json errors",
                "Check Output panel for TypeScript server logs"
            ],
            "solutions": [
                "Restart TS server: 'TypeScript: Restart TS Server'",
                "Ensure tsconfig.json includes the file",
                "Check for node_modules issues - try deleting and reinstalling",
                "Verify TypeScript extension is enabled"
            ]
        }
    },
    {
        "instruction": "Extensions won't install, getting EACCES errors",
        "error_type": "permissions",
        "response": {
            "status": "recoverable",
            "cause": "Permission issues with VS Code extensions directory",
            "solutions": [
                "Fix permissions: sudo chown -R $(whoami) ~/.vscode/extensions",
                "On Windows: Run VS Code as administrator once",
                "Check disk space - extensions need room to download",
                "Try installing from VSIX if network issues"
            ],
            "warnings": ["Don't regularly run VS Code as admin - fix permissions instead"]
        }
    },
    {
        "instruction": "Settings sync conflicts between machines",
        "error_type": "sync_conflict",
        "response": {
            "status": "needs_decision",
            "explanation": "Settings Sync shows conflicts when same setting differs between local and remote",
            "options": [
                "Accept Local: Keep your current machine's settings",
                "Accept Remote: Use the cloud-synced settings",
                "Merge: Manually combine both versions"
            ],
            "best_practice": "Review conflicts carefully - some settings should be machine-specific (like terminal paths)",
            "machine_specific_settings": [
                "terminal.integrated.shell.*",
                "python.pythonPath",
                "git.path"
            ]
        }
    },
    {
        "instruction": "Debug breakpoints aren't being hit",
        "error_type": "debugging",
        "response": {
            "status": "needs_investigation",
            "common_causes": [
                "Source maps not configured correctly",
                "Code was modified after build - rebuild required",
                "Breakpoint in unreachable code",
                "Wrong debug configuration selected"
            ],
            "diagnostic_steps": [
                "Verify breakpoint shows solid red (not hollow)",
                "Check Debug Console for errors",
                "Enable 'sourceMap': true in launch.json",
                "Try 'debugger;' statement in code"
            ],
            "solutions": {
                "sourcemap_issue": "Ensure build outputs sourcemaps and paths match",
                "node_specific": "Use 'skipFiles' to skip node_modules",
                "browser_specific": "Check webRoot matches your setup"
            }
        }
    },
    {
        "instruction": "Git integration shows wrong branch or outdated status",
        "error_type": "git_sync",
        "response": {
            "status": "recoverable",
            "solutions": [
                "Refresh: Click refresh icon in Source Control",
                "Restart Git: 'Git: Refresh' from command palette",
                "Check git.autorefresh is enabled",
                "Verify .git folder is in workspace root"
            ],
            "if_persists": "Try closing and reopening the folder, or check for git lock files"
        }
    },
    {
        "instruction": "Python interpreter not found or wrong version selected",
        "error_type": "python_environment",
        "response": {
            "status": "recoverable",
            "diagnostic_steps": [
                "Check status bar - shows current Python interpreter",
                "Run 'Python: Select Interpreter' from command palette",
                "Verify virtual environment is activated in terminal"
            ],
            "solutions": [
                "Click interpreter in status bar to change",
                "Set python.defaultInterpreterPath in settings",
                "Create .vscode/settings.json with python.pythonPath",
                "Reload window after creating new virtual environment"
            ],
            "common_issues": ["Virtual env created after VS Code opened", "Conda environment not showing up"]
        }
    },
    {
        "instruction": "Terminal won't start or immediately closes",
        "error_type": "terminal_failure",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Check Output panel > Terminal for error messages",
                "Verify shell path in terminal.integrated.defaultProfile",
                "Try creating new terminal with different profile"
            ],
            "common_causes": [
                "Shell executable not found",
                "Shell initialization script has errors",
                "Antivirus blocking shell process",
                "Workspace trust restricting terminal profiles"
            ],
            "solutions": [
                "Reset terminal settings to default",
                "Try different shell: PowerShell, cmd, bash",
                "Disable shell integration temporarily",
                "Check if external terminal works (debugging launch config)"
            ]
        }
    },
    {
        "instruction": "Extension crashes or shows repeated errors",
        "error_type": "extension_crash",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Check Help > Toggle Developer Tools > Console for errors",
                "Look at extension's Output channel",
                "Run 'Developer: Show Running Extensions' to check status"
            ],
            "solutions": [
                "Disable and re-enable the extension",
                "Update extension to latest version",
                "Clear extension's workspace state",
                "Uninstall and reinstall extension",
                "Report issue to extension author with error details"
            ],
            "last_resort": "Use extension bisect to verify it's the culprit"
        }
    },
    {
        "instruction": "Can't connect to remote host via SSH",
        "error_type": "remote_connection",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Check Remote-SSH: Show Log output channel",
                "Verify SSH works from regular terminal first",
                "Check SSH config file syntax"
            ],
            "common_causes": [
                "SSH key passphrase not cached",
                "Firewall blocking connection",
                "Remote host doesn't have required dependencies",
                "VS Code Server installation failed on remote"
            ],
            "solutions": [
                "Run ssh-add to add key to agent",
                "Verify ~/.ssh/config Host entry",
                "Clear remote server: Remote-SSH: Kill VS Code Server on Host",
                "Check remote.SSH.useLocalServer setting"
            ]
        }
    },
    {
        "instruction": "Search finds nothing even though text exists",
        "error_type": "search_failure",
        "response": {
            "status": "needs_investigation",
            "common_causes": [
                "files.exclude or search.exclude hiding the file",
                "File is in .gitignore and search.useIgnoreFiles is true",
                "Search scope limited to current folder",
                "File is binary or very large"
            ],
            "solutions": [
                "Click '...' in search to toggle 'Use Exclude Settings'",
                "Check include/exclude patterns in search",
                "Use 'Search: Toggle Search Details' to see current filters",
                "Try searching with regex disabled"
            ],
            "tip": "Use the 'files to include' field to narrow search scope"
        }
    },
    {
        "instruction": "Code formatting not working or inconsistent",
        "error_type": "formatting",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Check which formatter is set: editor.defaultFormatter",
                "Look for errors when running Format Document",
                "Verify formatter extension is installed and enabled"
            ],
            "common_causes": [
                "Multiple formatters installed - conflicts",
                "No formatter configured for file type",
                "Formatter config file has errors (e.g., .prettierrc)",
                "Format on save disabled"
            ],
            "solutions": [
                "Set editor.defaultFormatter for the language",
                "Right-click > Format Document With... to choose formatter",
                "Check formatter's config file for syntax errors",
                "Enable editor.formatOnSave in settings"
            ]
        }
    },
    {
        "instruction": "Go to Definition/References not working",
        "error_type": "language_navigation",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Check if language service is running (status bar)",
                "Look for language server errors in Output panel",
                "Verify project configuration (tsconfig, pyrightconfig, etc.)"
            ],
            "common_causes": [
                "Language server hasn't finished indexing",
                "File not included in project configuration",
                "Missing type definitions",
                "Language extension not installed"
            ],
            "solutions": [
                "Wait for indexing to complete",
                "Restart language server",
                "Install type definitions (@types packages)",
                "Check include/exclude in project config"
            ]
        }
    },
    {
        "instruction": "Keyboard shortcuts not working",
        "error_type": "keybindings",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Check 'Help > Keyboard Shortcuts Reference' PDF",
                "Open Keyboard Shortcuts (Ctrl+K Ctrl+S) and search for the shortcut",
                "Look for 'when' clause conflicts"
            ],
            "common_causes": [
                "Extension overriding the keybinding",
                "Keybinding has a 'when' clause that's not active",
                "OS intercepting the shortcut",
                "Vim/keyboard mode extension active"
            ],
            "solutions": [
                "Check for conflicting keybindings in settings",
                "Reset keybinding to default",
                "Disable conflicting extension",
                "Check OS keyboard shortcuts (especially on Mac)"
            ]
        }
    },
    {
        "instruction": "Tasks won't run or fail immediately",
        "error_type": "tasks",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Check Terminal > Run Task output",
                "Verify tasks.json syntax is valid JSON",
                "Check if command exists in PATH"
            ],
            "common_causes": [
                "Invalid tasks.json syntax",
                "Command not found - PATH issue",
                "Working directory wrong",
                "Shell not configured correctly"
            ],
            "solutions": [
                "Validate tasks.json in JSON editor",
                "Use absolute paths for commands",
                "Set 'cwd' option explicitly",
                "Check shell configuration in tasks.json"
            ],
            "tip": "Run task in terminal first to debug"
        }
    },
    {
        "instruction": "ESLint/linting errors not showing",
        "error_type": "linting",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Check ESLint Output channel for errors",
                "Verify ESLint extension is enabled for workspace",
                "Look for .eslintrc configuration file"
            ],
            "common_causes": [
                "ESLint extension not installed",
                "No ESLint config file in project",
                "eslint package not in node_modules",
                "File type not included in ESLint"
            ],
            "solutions": [
                "Install ESLint extension and eslint package",
                "Run 'ESLint: Create ESLint configuration'",
                "Check eslint.validate setting for file types",
                "Restart ESLint server"
            ]
        }
    },
    {
        "instruction": "Copilot suggestions not appearing",
        "error_type": "copilot",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Check Copilot icon in status bar",
                "Look at GitHub Copilot Output channel",
                "Verify subscription status"
            ],
            "common_causes": [
                "Not signed in to GitHub",
                "Subscription expired",
                "Disabled for current language",
                "Network/proxy blocking connection"
            ],
            "solutions": [
                "Click status bar icon to check status",
                "Sign out and sign back in",
                "Check github.copilot.enable settings",
                "Configure proxy if behind firewall"
            ]
        }
    },
    {
        "instruction": "Files getting corrupted or showing garbage characters",
        "error_type": "encoding",
        "response": {
            "status": "recoverable",
            "cause": "Usually encoding mismatch between file and VS Code's detection",
            "diagnostic_steps": [
                "Check current encoding in status bar",
                "Look at file's original encoding"
            ],
            "solutions": [
                "Click encoding in status bar > Reopen with Encoding",
                "Try common encodings: UTF-8, UTF-16, Latin-1",
                "If editing, save with correct encoding",
                "Set files.encoding for specific file types"
            ],
            "warnings": ["Be careful - wrong encoding can permanently corrupt files if saved"]
        }
    },
    {
        "instruction": "Workspace won't open or opens blank",
        "error_type": "workspace_corruption",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Try opening folder directly instead of workspace file",
                "Check .code-workspace file syntax",
                "Look at developer console for errors"
            ],
            "solutions": [
                "Validate JSON in .code-workspace file",
                "Clear workspace storage: workspaceStorage folder",
                "Reset VS Code: delete .vscode folder and user settings",
                "Try opening in new window without extensions"
            ],
            "last_resort": "Export settings, uninstall VS Code, reinstall fresh"
        }
    },
    {
        "instruction": "High CPU usage even when idle",
        "error_type": "performance_cpu",
        "response": {
            "status": "needs_investigation",
            "diagnostic_steps": [
                "Open Process Explorer (Help menu)",
                "Check which process uses CPU",
                "Look for extension host activity"
            ],
            "common_causes": [
                "File watcher on too many files",
                "Extension stuck in loop",
                "Language server continuously reindexing",
                "Search indexing large workspace"
            ],
            "solutions": [
                "Add node_modules to files.watcherExclude",
                "Disable suspected extension",
                "Restart extension host: Developer: Restart Extension Host",
                "Limit search/watch scope in settings"
            ]
        }
    },
]

# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def format_tool_response(tool: str, parameters: dict) -> str:
    """Format as tool selection response."""
    return json.dumps({
        "action": "tool_call",
        "tool": tool,
        "parameters": parameters,
        "reasoning": f"Using {tool} to accomplish the requested task"
    }, indent=2)

def format_planning_response(steps: List[str]) -> str:
    """Format as multi-step plan."""
    return json.dumps({
        "action": "multi_step_plan",
        "steps": [{"step": i+1, "action": step} for i, step in enumerate(steps)],
        "requires_confirmation": True
    }, indent=2)

def format_error_response(error_data: dict) -> str:
    """Format error/guardrail response."""
    return json.dumps(error_data, indent=2)

def generate_tool_examples() -> List[Dict]:
    """Generate tool selection training examples."""
    examples = []
    
    all_tasks = BASIC_IDE_TASKS + ADVANCED_IDE_TASKS + DEBUGGING_TASKS
    
    for task in all_tasks:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_tool_response(task["tool"], task["parameters"])
        })
    
    return examples

def generate_planning_examples() -> List[Dict]:
    """Generate multi-step planning examples."""
    examples = []
    
    for task in PLANNING_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_planning_response(task["steps"])
        })
    
    return examples

def generate_concept_examples() -> List[Dict]:
    """Generate concept Q&A examples."""
    examples = []
    
    for concept in BASIC_CONCEPTS + ADVANCED_CONCEPTS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": concept["question"],
            "response": concept["answer"]
        })
    
    return examples

def generate_error_examples() -> List[Dict]:
    """Generate error handling examples."""
    examples = []
    
    for scenario in ERROR_SCENARIOS:
        response = scenario["response"].copy()
        response["error_type"] = scenario["error_type"]
        
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": scenario["instruction"],
            "response": format_error_response(response)
        })
    
    return examples

def generate_variations() -> List[Dict]:
    """Generate additional variations for diversity."""
    variations = []
    
    # Keybinding variations - Expanded
    keybinding_queries = [
        ("What's the shortcut to open terminal?", "Ctrl+` (backtick) opens the integrated terminal. You can also use Ctrl+Shift+` to create a new terminal."),
        ("How do I quickly switch between open files?", "Ctrl+Tab cycles through open editors. Ctrl+P opens Quick Open for fuzzy file search. Alt+Left/Right navigates editor history."),
        ("Shortcut for find and replace?", "Ctrl+H opens Find and Replace in current file. Ctrl+Shift+H opens Find and Replace across files."),
        ("How to duplicate a line?", "Shift+Alt+Down duplicates the line below, Shift+Alt+Up duplicates above. Works with multiple lines selected too."),
        ("Quick way to comment code?", "Ctrl+/ toggles line comment. Ctrl+Shift+A toggles block comment (where supported)."),
        ("How to move a line up or down?", "Alt+Up moves the current line up, Alt+Down moves it down. Works with multiple lines selected."),
        ("Shortcut to delete entire line?", "Ctrl+Shift+K deletes the entire current line. Works faster than selecting and deleting."),
        ("How to select all occurrences?", "Ctrl+Shift+L selects all occurrences of current selection. Ctrl+D adds next occurrence to selection one at a time."),
        ("Quick way to go to line number?", "Ctrl+G opens 'Go to Line' dialog. Type line number and press Enter to jump."),
        ("How to fold/collapse code blocks?", "Ctrl+Shift+[ folds current region, Ctrl+Shift+] unfolds. Ctrl+K Ctrl+0 folds all, Ctrl+K Ctrl+J unfolds all."),
        ("Shortcut to open settings?", "Ctrl+, opens Settings UI. Use Ctrl+Shift+P then 'Open Settings (JSON)' for raw JSON editing."),
        ("How to split editor?", "Ctrl+\\ splits editor right. Ctrl+K Ctrl+\\ splits down. Drag tabs to create splits manually."),
        ("Quick file rename?", "F2 renames file in Explorer (same as symbol rename). Right-click also shows rename option."),
        ("How to jump to matching bracket?", "Ctrl+Shift+\\ jumps to matching bracket. Useful for navigating deeply nested code."),
        ("Shortcut for zen mode?", "Ctrl+K Z enters Zen Mode - fullscreen focused editing. Press Esc twice to exit."),
        ("How to trigger suggestions manually?", "Ctrl+Space triggers IntelliSense suggestions. Ctrl+Shift+Space shows parameter hints."),
        ("Quick way to close all editors?", "Ctrl+K W closes all editors in current group. Ctrl+K Ctrl+W closes all editors everywhere."),
        ("How to navigate to symbol?", "Ctrl+Shift+O opens symbol outline in current file. Ctrl+T searches symbols across workspace."),
        ("Shortcut for peek definition?", "Alt+F12 peeks definition inline without leaving current file. F12 goes to definition."),
        ("How to expand/shrink selection?", "Shift+Alt+Right expands selection to enclosing scope. Shift+Alt+Left shrinks it back."),
    ]
    
    for query, answer in keybinding_queries:
        variations.append({
            "system": SYSTEM_PROMPT,
            "instruction": query,
            "response": answer
        })
    
    # Extension recommendations - Expanded
    extension_queries = [
        ("Best extensions for Python development?", "Essential Python extensions: 1) Python (Microsoft) - IntelliSense, debugging, linting, 2) Pylance - fast, feature-rich language server, 3) Black Formatter - code formatting, 4) Python Docstring Generator, 5) Python Test Explorer. Consider also: autoDocstring, Python Indent."),
        ("What extensions do I need for React?", "Key React extensions: 1) ES7+ React/Redux snippets - component snippets, 2) Prettier - code formatting, 3) ESLint - linting, 4) Auto Import, 5) vscode-styled-components if using styled-components. Also useful: Simple React Snippets, React PropTypes Intellisense."),
        ("Extensions for working with Docker?", "Docker extensions: 1) Docker (Microsoft) - container management, Dockerfile IntelliSense, 2) Docker Compose - compose file support, 3) Remote - Containers - develop inside containers, 4) hadolint - Dockerfile linting. The Docker extension provides excellent container visibility and management from VS Code."),
        ("Best extensions for Go development?", "Essential Go extensions: 1) Go (golang.go) - official extension with gopls, debugging, testing, 2) Go Test Explorer - test integration, 3) Go Doc - documentation viewer. The official Go extension provides IntelliSense, formatting, linting, and debugging out of the box."),
        ("Extensions for Rust development?", "Rust extensions: 1) rust-analyzer - fast, feature-rich language server (preferred over RLS), 2) Even Better TOML - Cargo.toml support, 3) CodeLLDB - debugging, 4) crates - dependency management in Cargo.toml."),
        ("Best extensions for Java?", "Java extensions: 1) Extension Pack for Java (Microsoft) - includes Language Support, Debugger, Maven, 2) Spring Boot Extension Pack for Spring development, 3) Lombok Annotations Support, 4) Java Test Runner. The Extension Pack provides a complete Java IDE experience."),
        ("Extensions for working with databases?", "Database extensions: 1) SQLTools - multi-database client with query execution, 2) Database Client - another popular option, 3) MongoDB for VS Code - MongoDB specific, 4) PostgreSQL - Postgres specific. These provide query editing, result viewing, and connection management."),
        ("Best Git extensions?", "Git extensions: 1) GitLens - blame, history, comparisons, authorship, 2) Git Graph - visual branch history, 3) Git History - file/line history viewing. GitLens is particularly powerful for understanding code changes and contributors."),
        ("Extensions for Kubernetes?", "Kubernetes extensions: 1) Kubernetes (Microsoft) - cluster management, 2) YAML - for manifest editing, 3) Helm Intellisense - Helm chart support, 4) Bridge to Kubernetes - local debugging. These provide cluster exploration, deployment management, and manifest editing."),
        ("Best extensions for web development?", "Web development essentials: 1) Live Server - local dev server with hot reload, 2) Prettier - code formatting, 3) ESLint - JavaScript linting, 4) Auto Rename Tag - syncs HTML tag renaming, 5) CSS Peek - peek CSS definitions, 6) Path Intellisense - file path autocomplete."),
        ("Extensions for C# .NET development?", "C# extensions: 1) C# Dev Kit (Microsoft) - full IDE experience with project management, 2) C# (OmniSharp) - IntelliSense and debugging, 3) NuGet Gallery - package management, 4) .NET Core Test Explorer - test integration. C# Dev Kit is the newer, recommended option."),
        ("Best Markdown extensions?", "Markdown extensions: 1) Markdown All in One - shortcuts, TOC, preview, 2) Markdown Preview Enhanced - advanced preview features, 3) markdownlint - linting, 4) Paste Image - paste images from clipboard. These make VS Code a great Markdown editor."),
        ("Extensions for Vue.js?", "Vue extensions: 1) Volar - official Vue 3 language support (replaces Vetur for Vue 3), 2) Vue VSCode Snippets - component snippets, 3) ESLint with Vue plugin, 4) Prettier. For Vue 2, use Vetur instead of Volar."),
        ("Extensions for Angular development?", "Angular extensions: 1) Angular Language Service - official Angular support, 2) Angular Snippets - component/service snippets, 3) Angular Console - project management UI. These provide IntelliSense, navigation, and code generation for Angular projects."),
        ("Best extensions for testing?", "Testing extensions: 1) Test Explorer UI - unified test viewer, 2) Jest (for JavaScript/TypeScript), 3) Python Test Explorer, 4) Test Adapter Converter - adapts old extensions. Coverage Gutters shows code coverage inline."),
    ]
    
    for query, answer in extension_queries:
        variations.append({
            "system": SYSTEM_PROMPT,
            "instruction": query,
            "response": answer
        })
    
    # Settings customization - Expanded
    settings_queries = [
        ("How do I change the font size?", "Go to Settings (Ctrl+,) and search for 'font size'. Key settings: editor.fontSize (default 14), terminal.integrated.fontSize, editor.lineHeight. You can also use Ctrl++ and Ctrl+- to zoom the entire window."),
        ("How to enable auto-save?", "Settings > search 'auto save'. Set files.autoSave to: 'afterDelay' (saves after delay), 'onFocusChange' (saves when switching files), or 'onWindowChange' (saves when switching apps). files.autoSaveDelay controls the delay in milliseconds."),
        ("How do I change the color theme?", "Ctrl+K Ctrl+T opens theme picker, or File > Preferences > Color Theme. Popular themes: One Dark Pro, Dracula, GitHub Theme, Material Theme. You can also customize colors in settings.json with workbench.colorCustomizations."),
        ("How to hide the minimap?", "Settings > search 'minimap' > set editor.minimap.enabled to false. Or click the minimap context menu > Hide Minimap."),
        ("How to change tab size?", "Settings > search 'tab size'. editor.tabSize sets spaces per tab (default 4). editor.insertSpaces converts tabs to spaces. editor.detectIndentation auto-detects from file content."),
        ("How to enable bracket pair colorization?", "Settings > search 'bracket pair'. editor.bracketPairColorization.enabled = true (now default). editor.guides.bracketPairs shows vertical guides between brackets."),
        ("How to configure format on save?", "Settings > search 'format on save'. Enable editor.formatOnSave. Set editor.defaultFormatter to your preferred formatter. You can also format on paste with editor.formatOnPaste."),
        ("How to exclude files from search?", "Settings > search 'exclude'. search.exclude hides from search, files.exclude hides from Explorer too. Add patterns like '**/node_modules': true. Use glob patterns for flexibility."),
        ("How to enable word wrap?", "Settings > search 'word wrap'. editor.wordWrap options: 'off', 'on' (viewport width), 'wordWrapColumn', 'bounded'. Alt+Z toggles word wrap quickly."),
        ("How to change the default terminal?", "Settings > search 'default profile'. terminal.integrated.defaultProfile.windows/linux/osx sets the default shell. You can create custom terminal profiles with different configurations."),
        ("How to enable sticky scroll?", "Settings > search 'sticky scroll'. editor.stickyScroll.enabled shows enclosing scopes at top of editor. Helpful for navigating large files and understanding context."),
        ("How to configure file associations?", "Settings > search 'file associations'. files.associations maps extensions to languages: {'*.xyz': 'javascript'}. Useful for non-standard file extensions."),
        ("How to enable inlay hints?", "Settings > search 'inlay hints'. editor.inlayHints.enabled = true. Language-specific: typescript.inlayHints.*, python.analysis.inlayHints.*. Shows parameter names, types inline."),
        ("How to configure Git autofetch?", "Settings > search 'autofetch'. git.autofetch = true fetches from remotes periodically. git.autofetch.period controls frequency in seconds (default 180)."),
        ("How to change editor cursor style?", "Settings > search 'cursor'. editor.cursorStyle: 'line', 'block', 'underline'. editor.cursorBlinking: 'blink', 'smooth', 'phase', 'expand', 'solid'. editor.cursorWidth for line cursor."),
    ]
    
    for query, answer in settings_queries:
        variations.append({
            "system": SYSTEM_PROMPT,
            "instruction": query,
            "response": answer
        })
    
    # Workflow tips - NEW SECTION
    workflow_tips = [
        ("How to use VS Code for pair programming?", "VS Code Live Share extension enables real-time collaboration. Start session from status bar or command palette. Participants can edit, debug, use terminals together. Works across different editors (VS/VS Code). Free for basic use."),
        ("How to work with monorepos in VS Code?", "Use multi-root workspaces to include multiple packages. Configure TypeScript/ESLint with project references. Use workspace search exclude to improve performance. Consider extensions like Nx Console for build orchestration."),
        ("Best way to manage multiple projects?", "Use workspaces (.code-workspace files) for related projects. Recent workspaces accessible via File > Open Recent. Profiles let you have different extension sets for different types of projects."),
        ("How to improve VS Code startup time?", "Disable unused extensions, especially those with '*' activation. Use workspace-specific extensions when possible. Check startup time with 'Developer: Show Running Extensions'. Consider using Profiles for lighter configurations."),
        ("How to work offline with VS Code?", "VS Code works fully offline after initial install. Pre-install needed extensions. Be aware: some extensions require internet (Copilot, Remote). Settings Sync won't work offline. Language servers work offline."),
        ("How to use VS Code with WSL?", "Install Remote - WSL extension. Click green icon in bottom-left > 'New WSL Window'. Full Linux development environment with Windows VS Code UI. Files stored in Linux filesystem for best performance."),
        ("How to debug memory leaks in Node.js?", "Use launch.json with 'runtimeArgs': ['--inspect']. Chrome DevTools: Debug > Attach to Node. Take heap snapshots, compare allocations. VS Code's Memory tab shows live allocations during debug."),
        ("How to set up code snippets for team?", "Create project .vscode/project.code-snippets file - shared via git. Define snippets with prefix, body, description. Use tabstops ($1, $2) and variables ($TM_FILENAME). Team members get snippets automatically."),
        ("How to handle merge conflicts in VS Code?", "VS Code shows conflicts inline with Accept Current/Incoming/Both buttons. Use 'Compare Changes' to see side-by-side diff. Source Control view lists all conflicted files. After resolving, stage and commit."),
        ("How to use tasks for build automation?", "Create .vscode/tasks.json. Define build/test/watch tasks. Use Ctrl+Shift+B for build task. Problem matchers parse output for errors. Tasks can depend on each other for complex workflows."),
    ]
    
    for query, answer in workflow_tips:
        variations.append({
            "system": SYSTEM_PROMPT,
            "instruction": query,
            "response": answer
        })
    
    # Debugging tips - NEW SECTION
    debugging_tips = [
        ("How to debug Node.js in VS Code?", "Create launch.json, select Node.js. Set 'program' to your entry file. Use 'runtimeArgs' for flags like --experimental-modules. Set breakpoints, press F5. Debug Console for REPL. Watch variables and call stack."),
        ("How to debug Python in VS Code?", "Python extension required. Create launch.json > Python. Options: current file, module, attach to remote, Django/Flask. Use 'justMyCode': false to step into libraries. Debug Console supports Python REPL."),
        ("How to debug browser JavaScript?", "Use 'Chrome' or 'Edge' launch type. Set 'webRoot' to your static files. Enable source maps in build. Use 'url' for dev server. Browser opens automatically with debugging attached."),
        ("How to use conditional breakpoints?", "Right-click breakpoint > Edit Breakpoint. Choose: Expression (break when true), Hit Count (break after N hits), or Log Message (logpoint - prints without stopping). Powerful for debugging loops."),
        ("How to debug tests?", "Most test extensions provide 'Debug Test' action. Click debug icon next to test. Or create launch.json config with test runner command. Breakpoints work in test files and source code."),
        ("How to debug Docker containers?", "Use Remote - Containers for dev containers. For existing containers, configure debug adapter to attach. Node.js: expose debug port. Python: use debugpy attach. Map source paths correctly."),
        ("How to see variable values while debugging?", "Multiple options: hover over variable, use Variables panel, add to Watch panel, use Debug Console for expressions. Data tips show current values inline in editor."),
        ("How to step through async code?", "Modern debuggers handle async/await. Use 'Step Into' (F11) to follow async calls. Call Stack shows async frames. Some debuggers support 'Step into Target' for choosing which function to enter."),
        ("How to use logpoints instead of console.log?", "Right-click gutter > Add Logpoint. Enter message with {expressions} for values. Logs without stopping execution. No code changes needed. Remove when done debugging."),
        ("How to debug remote processes?", "Use 'attach' instead of 'launch' configuration. Specify host and port. Start process with debug flag (--inspect for Node, -m debugpy for Python). Configure SSH tunneling if needed."),
    ]
    
    for query, answer in debugging_tips:
        variations.append({
            "system": SYSTEM_PROMPT,
            "instruction": query,
            "response": answer
        })
    
    # Git workflow variations - NEW SECTION
    git_variations = [
        ("How to stage partial changes in VS Code?", "In Source Control, click file to see diff. Click '+' on individual lines or sections to stage specific changes. Called 'staging hunks'. Great for splitting work into logical commits."),
        ("How to view file history?", "GitLens extension: right-click > Open File History. Or Timeline view in Explorer sidebar shows commits affecting current file. Click commit to see diff."),
        ("How to compare branches?", "GitLens: click branch > Compare with... Or use Git Graph extension for visual comparison. Command palette: 'Git: Checkout to...' shows branch list."),
        ("How to undo last commit?", "Command palette: 'Git: Undo Last Commit'. Keeps changes staged. To completely remove: use terminal 'git reset --hard HEAD~1' (destructive!). GitLens provides UI for this."),
        ("How to view blame annotations?", "GitLens shows blame in gutter automatically. Hover for details. Toggle with GitLens commands. Shows who changed each line and when. Click to see commit details."),
        ("How to resolve merge conflicts?", "VS Code shows conflict markers with Accept buttons. Use 'Accept Current Change', 'Accept Incoming Change', 'Accept Both', or edit manually. After resolving, stage the file."),
        ("How to create a branch in VS Code?", "Click branch name in status bar > Create new branch. Or Command palette: 'Git: Create Branch'. Name it, press Enter. You're automatically switched to it."),
        ("How to stash changes?", "Command palette: 'Git: Stash'. To retrieve: 'Git: Pop Stash' or 'Git: Apply Stash'. Stash includes staged and unstaged changes. Useful for quick context switching."),
        ("How to cherry-pick a commit?", "GitLens or Git Graph: find commit > Cherry Pick. Or terminal: git cherry-pick <sha>. Applies specific commit to current branch. May need conflict resolution."),
        ("How to sign commits in VS Code?", "Configure git.enableCommitSigning in settings. Need GPG key set up in Git. git.path may need to point to GPG-enabled git. Signed commits show verified badge on GitHub."),
    ]
    
    for query, answer in git_variations:
        variations.append({
            "system": SYSTEM_PROMPT,
            "instruction": query,
            "response": answer
        })
    
    # Performance and productivity - NEW SECTION
    productivity_tips = [
        ("How to navigate large codebases?", "Use Ctrl+T for workspace symbol search. Ctrl+Shift+O for file symbols. Breadcrumbs show context. Go to Definition (F12), Find References (Shift+F12). Use outline view for structure overview."),
        ("How to search and replace with regex?", "Open Search (Ctrl+Shift+F), click .* to enable regex. Use capture groups: find '(\\w+):(\\w+)', replace '$2:$1' to swap. Preview changes before applying."),
        ("How to use emmet in VS Code?", "Emmet is built-in for HTML/CSS. Type abbreviation, press Tab. Examples: div.class#id, ul>li*5, div+p+span. Customize with emmet.* settings. Works in JSX with config."),
        ("How to quickly fix code issues?", "Ctrl+. shows Quick Fix menu (lightbulb). Includes: import suggestions, refactorings, linting fixes. Also available via right-click > Quick Fix. Some fixes apply to whole file."),
        ("How to use code actions?", "Lightbulb icon (Ctrl+.) shows available actions: quick fixes, refactorings, source actions. 'Preferred' action can be triggered with Ctrl+Shift+. Source actions include organize imports, generate getters."),
        ("How to refactor code in VS Code?", "Select code, right-click > Refactor or Ctrl+Shift+R. Options depend on language: extract method/variable, rename symbol (F2), move to new file. Preview changes before applying."),
        ("How to use multi-root workspaces effectively?", "Add folders via File > Add Folder to Workspace. Each folder can have own settings in .code-workspace file. Search/tasks/debug work across all roots. Use folder-specific settings for different configs."),
        ("How to use the Timeline view?", "Timeline in Explorer sidebar shows: local file history (Auto Save snapshots), Git commits affecting file. Click entry to diff with current. Restore old versions easily."),
        ("How to use bookmarks in VS Code?", "Install Bookmarks extension. Toggle bookmark: Ctrl+Alt+K. Jump between: Ctrl+Alt+L/J. List all: Bookmarks view in Activity Bar. Bookmarks persist across sessions."),
        ("How to preview Markdown?", "Ctrl+Shift+V opens preview in new tab. Ctrl+K V opens side-by-side preview. Preview updates live as you type. Right-click for more options. Install extensions for enhanced preview."),
    ]
    
    for query, answer in productivity_tips:
        variations.append({
            "system": SYSTEM_PROMPT,
            "instruction": query,
            "response": answer
        })
    
    return variations

def main():
    """Generate all VS Code training data."""
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating VS Code & IDE Workflows Training Data")
    print("=" * 60)
    
    all_examples = []
    
    # Generate each category
    print("\n1. Generating tool selection examples...")
    tool_examples = generate_tool_examples()
    all_examples.extend(tool_examples)
    print(f"   Generated {len(tool_examples)} examples")
    
    print("\n2. Generating planning examples...")
    planning_examples = generate_planning_examples()
    all_examples.extend(planning_examples)
    print(f"   Generated {len(planning_examples)} examples")
    
    print("\n3. Generating concept Q&A...")
    concept_examples = generate_concept_examples()
    all_examples.extend(concept_examples)
    print(f"   Generated {len(concept_examples)} examples")
    
    print("\n4. Generating error/guardrail scenarios...")
    error_examples = generate_error_examples()
    all_examples.extend(error_examples)
    print(f"   Generated {len(error_examples)} examples")
    
    print("\n5. Generating variations...")
    variations = generate_variations()
    all_examples.extend(variations)
    print(f"   Generated {len(variations)} examples")
    
    # Shuffle for training
    random.shuffle(all_examples)
    
    # Save to JSONL
    output_file = output_dir / "vscode_ide_workflows.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_examples)} examples to {output_file}")
    
    # Summary
    print("\n" + "=" * 60)
    print("VS Code Training Data Generation Complete!")
    print("=" * 60)
    print(f"Total examples: {len(all_examples)}")
    print(f"  Tool selection: {len(tool_examples)}")
    print(f"  Planning: {len(planning_examples)}")
    print(f"  Concepts: {len(concept_examples)}")
    print(f"  Error handling: {len(error_examples)}")
    print(f"  Variations: {len(variations)}")

if __name__ == "__main__":
    main()
