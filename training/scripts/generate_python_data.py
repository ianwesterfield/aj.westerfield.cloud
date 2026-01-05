#!/usr/bin/env python3
"""
Python Development Training Data Generator
Target: ~300 examples for Python coding, debugging, packaging, testing
"""

import json
import random
from pathlib import Path
from typing import List, Dict

SYSTEM_PROMPT = """You are AJ, an expert AI assistant for Python development.
You help with Python coding, debugging, package management, testing, and best practices."""

# =============================================================================
# TOOL SELECTION TASKS
# =============================================================================

BASIC_PYTHON_TASKS = [
    {
        "instruction": "Create a virtual environment",
        "command": "python -m venv .venv",
        "explanation": "Creates isolated Python environment in .venv directory"
    },
    {
        "instruction": "Activate the virtual environment",
        "command": ".venv\\Scripts\\activate",
        "explanation": "Activates venv on Windows; use 'source .venv/bin/activate' on Linux/Mac"
    },
    {
        "instruction": "Install packages from requirements.txt",
        "command": "pip install -r requirements.txt",
        "explanation": "Installs all packages listed in requirements.txt"
    },
    {
        "instruction": "Freeze current packages to requirements",
        "command": "pip freeze > requirements.txt",
        "explanation": "Exports installed packages with versions to requirements.txt"
    },
    {
        "instruction": "Install a package",
        "command": "pip install requests",
        "explanation": "Installs the requests package from PyPI"
    },
    {
        "instruction": "Run Python tests",
        "command": "pytest -v",
        "explanation": "Runs pytest with verbose output"
    },
    {
        "instruction": "Run tests with coverage",
        "command": "pytest --cov=src --cov-report=html",
        "explanation": "Runs tests with coverage report for src directory"
    },
    {
        "instruction": "Format Python code",
        "command": "black .",
        "explanation": "Formats all Python files with Black formatter"
    },
    {
        "instruction": "Check code style",
        "command": "flake8 src/",
        "explanation": "Runs flake8 linter on src directory"
    },
    {
        "instruction": "Type check Python code",
        "command": "mypy src/",
        "explanation": "Runs mypy type checker on src directory"
    },
    {
        "instruction": "Run Python script",
        "command": "python main.py",
        "explanation": "Executes main.py with default Python interpreter"
    },
    {
        "instruction": "Install package in development mode",
        "command": "pip install -e .",
        "explanation": "Installs package in editable mode for development"
    },
    # NEW: Additional basic Python tasks
    {
        "instruction": "Upgrade pip to latest version",
        "command": "python -m pip install --upgrade pip",
        "explanation": "Updates pip to the latest version"
    },
    {
        "instruction": "List installed packages",
        "command": "pip list",
        "explanation": "Shows all installed packages and versions"
    },
    {
        "instruction": "Show package details",
        "command": "pip show requests",
        "explanation": "Displays detailed info about a specific package"
    },
    {
        "instruction": "Uninstall a package",
        "command": "pip uninstall requests -y",
        "explanation": "Removes a package without confirmation prompt"
    },
    {
        "instruction": "Check for outdated packages",
        "command": "pip list --outdated",
        "explanation": "Lists packages with newer versions available"
    },
    {
        "instruction": "Upgrade all outdated packages",
        "command": "pip list --outdated --format=freeze | grep -v '^\\-e' | cut -d = -f 1 | xargs -n1 pip install -U",
        "explanation": "Upgrades all outdated packages (Linux/Mac)"
    },
    {
        "instruction": "Run Python in interactive mode",
        "command": "python -i script.py",
        "explanation": "Runs script then stays in interactive mode"
    },
    {
        "instruction": "Check Python version",
        "command": "python --version",
        "explanation": "Displays the Python version"
    },
    {
        "instruction": "Run module as script",
        "command": "python -m http.server 8000",
        "explanation": "Runs a simple HTTP server on port 8000"
    },
    {
        "instruction": "Create requirements with hashes",
        "command": "pip freeze --require-hashes > requirements.txt",
        "explanation": "Creates requirements with hash verification for security"
    },
    {
        "instruction": "Install from git repository",
        "command": "pip install git+https://github.com/user/repo.git",
        "explanation": "Installs package directly from git repository"
    },
    {
        "instruction": "Install specific version",
        "command": "pip install requests==2.28.0",
        "explanation": "Installs a specific version of a package"
    },
    {
        "instruction": "Run unittest",
        "command": "python -m unittest discover -s tests",
        "explanation": "Discovers and runs all tests in tests directory"
    },
    {
        "instruction": "Generate documentation with pydoc",
        "command": "python -m pydoc -w mymodule",
        "explanation": "Generates HTML documentation for a module"
    },
    {
        "instruction": "Start documentation server",
        "command": "python -m pydoc -p 8080",
        "explanation": "Starts pydoc server on port 8080"
    },
    {
        "instruction": "Compile Python to bytecode",
        "command": "python -m compileall src/",
        "explanation": "Pre-compiles all .py files to .pyc"
    },
    {
        "instruction": "Run pylint",
        "command": "pylint src/ --output-format=colorized",
        "explanation": "Runs pylint with colored output"
    },
    {
        "instruction": "Check code complexity",
        "command": "radon cc src/ -a",
        "explanation": "Analyzes cyclomatic complexity of code"
    },
    {
        "instruction": "Run bandit security check",
        "command": "bandit -r src/",
        "explanation": "Scans code for common security issues"
    },
    {
        "instruction": "Create pip.conf for custom index",
        "command": "pip config set global.index-url https://pypi.company.com/simple/",
        "explanation": "Sets custom PyPI index URL"
    },
    {
        "instruction": "Use pip with proxy",
        "command": "pip install --proxy http://proxy:8080 requests",
        "explanation": "Installs package through HTTP proxy"
    },
    {
        "instruction": "Install pre-commit hooks",
        "command": "pre-commit install",
        "explanation": "Installs git pre-commit hooks from .pre-commit-config.yaml"
    },
    {
        "instruction": "Run pre-commit on all files",
        "command": "pre-commit run --all-files",
        "explanation": "Runs pre-commit hooks on all files, not just staged"
    },
    {
        "instruction": "Generate type stubs",
        "command": "stubgen src/ -o stubs/",
        "explanation": "Generates type stub files for a package"
    },
]

ADVANCED_PYTHON_TASKS = [
    {
        "instruction": "Profile Python code performance",
        "command": "python -m cProfile -s cumtime script.py",
        "explanation": "Profiles script, sorted by cumulative time"
    },
    {
        "instruction": "Debug Python script interactively",
        "command": "python -m pdb script.py",
        "explanation": "Starts script in Python debugger"
    },
    {
        "instruction": "Create Python package with poetry",
        "command": "poetry new myproject",
        "explanation": "Creates new Python project with poetry structure"
    },
    {
        "instruction": "Build distributable package",
        "command": "python -m build",
        "explanation": "Builds wheel and sdist packages in dist/"
    },
    {
        "instruction": "Upload package to PyPI",
        "command": "twine upload dist/*",
        "explanation": "Uploads built packages to PyPI (requires credentials)"
    },
    {
        "instruction": "Run async Python REPL",
        "command": "python -m asyncio",
        "explanation": "Starts REPL with async/await support"
    },
    {
        "instruction": "Generate requirements from imports",
        "command": "pipreqs . --force",
        "explanation": "Scans code for imports and generates requirements.txt"
    },
    {
        "instruction": "Check for security vulnerabilities",
        "command": "pip-audit",
        "explanation": "Scans dependencies for known vulnerabilities"
    },
    {
        "instruction": "Sort imports in Python files",
        "command": "isort .",
        "explanation": "Sorts and organizes imports in all Python files"
    },
    {
        "instruction": "Run specific test by name",
        "command": "pytest -k 'test_login' -v",
        "explanation": "Runs tests matching 'test_login' pattern"
    },
    # NEW: Additional advanced Python tasks
    {
        "instruction": "Line profile Python code",
        "command": "kernprof -l -v script.py",
        "explanation": "Profiles line-by-line execution time (requires line_profiler)"
    },
    {
        "instruction": "Memory profile Python script",
        "command": "python -m memory_profiler script.py",
        "explanation": "Shows memory usage line by line"
    },
    {
        "instruction": "Generate memory profile graph",
        "command": "mprof run script.py && mprof plot",
        "explanation": "Creates memory usage over time plot"
    },
    {
        "instruction": "Profile with py-spy",
        "command": "py-spy record -o profile.svg -- python script.py",
        "explanation": "Creates flame graph of Python execution"
    },
    {
        "instruction": "Top processes like tool for Python",
        "command": "py-spy top --pid 1234",
        "explanation": "Real-time view of Python process execution"
    },
    {
        "instruction": "Install poetry package manager",
        "command": "curl -sSL https://install.python-poetry.org | python3 -",
        "explanation": "Installs poetry globally"
    },
    {
        "instruction": "Add dependency with poetry",
        "command": "poetry add requests",
        "explanation": "Adds requests package and updates pyproject.toml"
    },
    {
        "instruction": "Add dev dependency with poetry",
        "command": "poetry add --dev pytest",
        "explanation": "Adds pytest as development dependency"
    },
    {
        "instruction": "Update all dependencies with poetry",
        "command": "poetry update",
        "explanation": "Updates all dependencies to latest allowed versions"
    },
    {
        "instruction": "Export poetry to requirements.txt",
        "command": "poetry export -f requirements.txt --output requirements.txt",
        "explanation": "Exports locked dependencies to requirements.txt"
    },
    {
        "instruction": "Run command in poetry environment",
        "command": "poetry run python script.py",
        "explanation": "Runs command using poetry's virtual environment"
    },
    {
        "instruction": "Use uv for fast package installation",
        "command": "uv pip install requests",
        "explanation": "Ultra-fast pip replacement written in Rust"
    },
    {
        "instruction": "Create venv with uv",
        "command": "uv venv",
        "explanation": "Creates virtual environment much faster than venv"
    },
    {
        "instruction": "Sync dependencies with uv",
        "command": "uv pip sync requirements.txt",
        "explanation": "Installs exact versions, removes unlisted packages"
    },
    {
        "instruction": "Run pytest with markers",
        "command": "pytest -m 'not slow' -v",
        "explanation": "Runs tests not marked as slow"
    },
    {
        "instruction": "Run pytest in parallel",
        "command": "pytest -n auto",
        "explanation": "Runs tests in parallel using all cores (pytest-xdist)"
    },
    {
        "instruction": "Run pytest with reruns",
        "command": "pytest --reruns 3 --reruns-delay 1",
        "explanation": "Retries failed tests 3 times (pytest-rerunfailures)"
    },
    {
        "instruction": "Generate HTML test report",
        "command": "pytest --html=report.html --self-contained-html",
        "explanation": "Creates HTML test report (pytest-html)"
    },
    {
        "instruction": "Run pytest with durations",
        "command": "pytest --durations=10",
        "explanation": "Shows 10 slowest tests"
    },
    {
        "instruction": "Run pytest stopping at first failure",
        "command": "pytest -x",
        "explanation": "Stops after first test failure"
    },
    {
        "instruction": "Run only last failed tests",
        "command": "pytest --lf",
        "explanation": "Reruns only tests that failed last time"
    },
    {
        "instruction": "Run pytest with live output",
        "command": "pytest -s",
        "explanation": "Shows print statements during tests"
    },
    {
        "instruction": "Check minimum coverage",
        "command": "pytest --cov=src --cov-fail-under=80",
        "explanation": "Fails if coverage below 80%"
    },
    {
        "instruction": "Generate coverage XML report",
        "command": "pytest --cov=src --cov-report=xml",
        "explanation": "Creates coverage.xml for CI integration"
    },
    {
        "instruction": "Run tox test environments",
        "command": "tox",
        "explanation": "Runs tests across multiple Python versions"
    },
    {
        "instruction": "Run tox for specific environment",
        "command": "tox -e py311",
        "explanation": "Runs tests only for Python 3.11"
    },
    {
        "instruction": "Recreate tox environments",
        "command": "tox -r",
        "explanation": "Forces recreation of virtual environments"
    },
    {
        "instruction": "Build Sphinx documentation",
        "command": "sphinx-build -b html docs/source docs/build",
        "explanation": "Builds HTML documentation from RST/MD files"
    },
    {
        "instruction": "Auto-generate Sphinx API docs",
        "command": "sphinx-apidoc -o docs/source src/",
        "explanation": "Generates RST files from docstrings"
    },
    {
        "instruction": "Create MkDocs documentation",
        "command": "mkdocs serve",
        "explanation": "Serves documentation with live reload"
    },
    {
        "instruction": "Build MkDocs documentation",
        "command": "mkdocs build",
        "explanation": "Builds static documentation site"
    },
    {
        "instruction": "Upload to Test PyPI",
        "command": "twine upload --repository testpypi dist/*",
        "explanation": "Uploads to test.pypi.org for testing"
    },
    {
        "instruction": "Install from Test PyPI",
        "command": "pip install --index-url https://test.pypi.org/simple/ mypackage",
        "explanation": "Installs package from test PyPI"
    },
    {
        "instruction": "Check package description renders correctly",
        "command": "twine check dist/*",
        "explanation": "Validates package metadata before upload"
    },
    {
        "instruction": "Generate setup.py from pyproject.toml",
        "command": "python -c \"from setuptools import setup; setup()\"",
        "explanation": "Creates setup.py shim for legacy tools"
    },
    {
        "instruction": "Run ruff linter",
        "command": "ruff check . --fix",
        "explanation": "Fast Python linter that auto-fixes issues"
    },
    {
        "instruction": "Run ruff formatter",
        "command": "ruff format .",
        "explanation": "Formats Python code (Black-compatible)"
    },
    {
        "instruction": "Check all code quality tools",
        "command": "black --check . && isort --check . && mypy . && ruff check .",
        "explanation": "Runs all code quality checks without modifying"
    },
    {
        "instruction": "Run doctest",
        "command": "python -m doctest mymodule.py -v",
        "explanation": "Tests code examples in docstrings"
    },
    {
        "instruction": "Run hypothesis property tests",
        "command": "pytest tests/ --hypothesis-show-statistics",
        "explanation": "Runs property-based tests with stats"
    },
    {
        "instruction": "Create Python wheel",
        "command": "pip wheel . -w dist/",
        "explanation": "Creates wheel file in dist directory"
    },
    {
        "instruction": "Install packages with hash checking",
        "command": "pip install --require-hashes -r requirements.txt",
        "explanation": "Verifies package hashes for security"
    },
    {
        "instruction": "Run Jupyter notebook from CLI",
        "command": "jupyter nbconvert --to notebook --execute notebook.ipynb",
        "explanation": "Executes notebook and saves results"
    },
    {
        "instruction": "Convert notebook to Python script",
        "command": "jupyter nbconvert --to script notebook.ipynb",
        "explanation": "Converts .ipynb to .py file"
    },
    {
        "instruction": "Start JupyterLab",
        "command": "jupyter lab",
        "explanation": "Starts JupyterLab IDE in browser"
    },
    {
        "instruction": "Run IPython with autoreload",
        "command": "ipython --InteractiveShellApp.extensions='autoreload' --InteractiveShellApp.exec_lines='%autoreload 2'",
        "explanation": "IPython that auto-reloads modified modules"
    },
    {
        "instruction": "Profile memory with tracemalloc",
        "command": "python -c \"import tracemalloc; tracemalloc.start(); import mymodule; print(tracemalloc.get_traced_memory())\"",
        "explanation": "Traces memory allocations in Python"
    },
    {
        "instruction": "Run asyncio debug mode",
        "command": "PYTHONASYNCIODEBUG=1 python script.py",
        "explanation": "Enables asyncio debugging (slow coroutines, etc.)"
    },
    {
        "instruction": "Check circular dependencies",
        "command": "pydeps src/ --cluster",
        "explanation": "Visualizes module dependencies as graph"
    },
    {
        "instruction": "Generate dependency graph",
        "command": "pydeps src/ -o deps.svg",
        "explanation": "Creates SVG dependency visualization"
    },
]

# =============================================================================
# CODE EXAMPLES
# =============================================================================

CODE_TASKS = [
    {
        "instruction": "Write a function to read JSON from file",
        "code": """import json
from pathlib import Path
from typing import Any

def read_json(filepath: str | Path) -> Any:
    \"\"\"Read and parse JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Parsed JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If invalid JSON
    \"\"\"
    path = Path(filepath)
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)""",
        "explanation": "Type-annotated, handles encoding, uses pathlib"
    },
    {
        "instruction": "Create an async HTTP client class",
        "code": """import aiohttp
from typing import Any
import asyncio

class AsyncHTTPClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None
    
    async def __aenter__(self):
        self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, *args):
        if self._session:
            await self._session.close()
    
    async def get(self, path: str, **kwargs) -> Any:
        async with self._session.get(f"{self.base_url}{path}", **kwargs) as resp:
            resp.raise_for_status()
            return await resp.json()
    
    async def post(self, path: str, data: dict, **kwargs) -> Any:
        async with self._session.post(f"{self.base_url}{path}", json=data, **kwargs) as resp:
            resp.raise_for_status()
            return await resp.json()""",
        "explanation": "Async context manager, configurable timeout, JSON handling"
    },
    {
        "instruction": "Write a decorator for retry logic",
        "code": """import functools
import time
import logging
from typing import TypeVar, Callable, Any

T = TypeVar('T')

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    \"\"\"Decorator to retry function on failure.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch
    \"\"\"
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logging.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            raise last_exception
        return wrapper
    return decorator

# Usage: @retry(max_attempts=3, exceptions=(ConnectionError,))""",
        "explanation": "Configurable retries with exponential backoff, preserves function metadata"
    },
    {
        "instruction": "Create a dataclass with validation",
        "code": """from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import re

@dataclass
class User:
    email: str
    name: str
    age: int
    created_at: datetime = field(default_factory=datetime.now)
    roles: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        # Validate email
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$'
        if not re.match(email_pattern, self.email):
            raise ValueError(f"Invalid email: {self.email}")
        
        # Validate age
        if not 0 < self.age < 150:
            raise ValueError(f"Invalid age: {self.age}")
        
        # Normalize name
        self.name = self.name.strip().title()
    
    @property
    def is_admin(self) -> bool:
        return 'admin' in self.roles""",
        "explanation": "Dataclass with post-init validation, default factory, computed property"
    },
    {
        "instruction": "Write a context manager for database transactions",
        "code": """from contextlib import contextmanager
from typing import Generator
import sqlite3

@contextmanager
def transaction(db_path: str) -> Generator[sqlite3.Cursor, None, None]:
    \"\"\"Context manager for SQLite transactions.
    
    Commits on success, rolls back on exception.
    
    Usage:
        with transaction('my.db') as cursor:
            cursor.execute('INSERT INTO users ...')
    \"\"\"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Dict-like access
    cursor = conn.cursor()
    
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()""",
        "explanation": "Auto commit/rollback, proper resource cleanup, row factory for dict access"
    },
]

# =============================================================================
# MULTI-STEP PLANNING TASKS
# =============================================================================

PLANNING_TASKS = [
    {
        "instruction": "Set up a new Python project with best practices",
        "steps": [
            "Create project directory structure",
            "Initialize git repository",
            "Create virtual environment: python -m venv .venv",
            "Create pyproject.toml with project metadata",
            "Set up src layout: src/mypackage/__init__.py",
            "Create tests/ directory with conftest.py",
            "Add .gitignore for Python",
            "Configure Black, isort, flake8, mypy in pyproject.toml",
            "Set up pre-commit hooks",
            "Create README.md with setup instructions"
        ]
    },
    {
        "instruction": "Debug a Python application that's running slow",
        "steps": [
            "Profile with cProfile: python -m cProfile -o profile.prof script.py",
            "Visualize with snakeviz: snakeviz profile.prof",
            "Identify hotspots (functions taking most time)",
            "Check for N+1 database queries",
            "Look for unnecessary loops or list comprehensions",
            "Check memory usage with memory_profiler",
            "Consider using generators for large datasets",
            "Look for blocking I/O that could be async",
            "Profile specific functions with line_profiler",
            "Implement caching where appropriate"
        ]
    },
    {
        "instruction": "Add type hints to existing Python codebase",
        "steps": [
            "Install mypy: pip install mypy",
            "Start with strict mode on new code",
            "Run mypy to see current state: mypy src/",
            "Add type hints to function signatures first",
            "Use 'reveal_type()' to understand inferred types",
            "Add TypedDict for complex dictionaries",
            "Use Protocol for duck typing",
            "Create type stubs for untyped dependencies",
            "Configure mypy in pyproject.toml",
            "Add mypy to CI pipeline"
        ]
    },
    {
        "instruction": "Package Python application for distribution",
        "steps": [
            "Create pyproject.toml with build system",
            "Define project metadata (name, version, dependencies)",
            "Set up entry points for CLI commands",
            "Create README.md and LICENSE",
            "Build package: python -m build",
            "Test locally: pip install dist/*.whl",
            "Create test PyPI account and upload",
            "Test installation from test PyPI",
            "Upload to production PyPI: twine upload dist/*",
            "Tag release in git"
        ]
    },
    {
        "instruction": "Implement comprehensive testing for Python project",
        "steps": [
            "Install pytest and plugins: pytest-cov, pytest-mock",
            "Create tests/ directory structure mirroring src/",
            "Write unit tests for individual functions",
            "Add integration tests for component interaction",
            "Create fixtures in conftest.py",
            "Use parametrize for multiple test cases",
            "Mock external dependencies (APIs, databases)",
            "Set up coverage requirements (e.g., 80%)",
            "Add pytest to CI pipeline",
            "Generate HTML coverage reports"
        ]
    },
]

# =============================================================================
# CONCEPT Q&A
# =============================================================================

BASIC_CONCEPTS = [
    {
        "question": "What is a Python virtual environment?",
        "answer": "A virtual environment is an isolated Python installation with its own packages, separate from the system Python. Created with 'python -m venv envname'. Each project should have its own venv to avoid dependency conflicts. Activate with 'source envname/bin/activate' (Linux/Mac) or 'envname\\Scripts\\activate' (Windows). Packages installed with pip go only into active venv. Use requirements.txt or pyproject.toml to track dependencies."
    },
    {
        "question": "What's the difference between list and tuple in Python?",
        "answer": "Lists are mutable (can be modified), tuples are immutable (cannot change after creation). Lists use [], tuples use (). Tuples are hashable (can be dict keys), lists aren't. Tuples are slightly faster and use less memory. Use tuples for fixed collections (coordinates, RGB values), lists for dynamic collections. Named tuples add field names. Both support indexing, slicing, and iteration."
    },
    {
        "question": "How do decorators work in Python?",
        "answer": "Decorators are functions that modify other functions. They take a function as input and return a new function. Syntax: @decorator above function definition. Common uses: logging, timing, authentication, caching. Use @functools.wraps to preserve original function metadata. Decorators can take arguments by adding another wrapper layer. Class-based decorators use __call__. Multiple decorators apply bottom-up."
    },
    {
        "question": "What are *args and **kwargs?",
        "answer": "*args collects positional arguments into a tuple: def func(*args) allows func(1, 2, 3). **kwargs collects keyword arguments into a dict: def func(**kwargs) allows func(a=1, b=2). They enable variable-length arguments. Can be used together: def func(*args, **kwargs). When calling, * unpacks iterables, ** unpacks dicts. Common pattern: wrapper functions that pass through arguments."
    },
    {
        "question": "What is a generator in Python?",
        "answer": "Generators are functions that yield values one at a time instead of returning a complete list. They use 'yield' instead of 'return'. Memory-efficient for large datasets - values computed on demand. Generator expressions: (x for x in range(10)). Once exhausted, must recreate. Use for streaming data, infinite sequences, or memory-constrained environments. Supports send() for coroutine-style communication."
    },
    {
        "question": "What is the GIL (Global Interpreter Lock)?",
        "answer": "The GIL is a mutex in CPython that allows only one thread to execute Python bytecode at a time. It simplifies memory management but limits true parallelism for CPU-bound tasks. I/O-bound tasks can benefit from threading since GIL is released during I/O. For CPU parallelism, use multiprocessing (separate processes) or async for I/O. Alternative interpreters (PyPy, Jython) handle GIL differently."
    },
]

ADVANCED_CONCEPTS = [
    {
        "question": "How does Python's garbage collection work?",
        "answer": "Python uses reference counting as primary GC - objects deleted when refcount hits zero. Cyclic garbage collector handles reference cycles (objects referencing each other). GC runs automatically in generations (0, 1, 2) - newer objects collected more frequently. gc module provides manual control: gc.collect(), gc.disable(). Weak references (weakref module) don't increase refcount. __del__ is not guaranteed to run. Use context managers for resource cleanup instead."
    },
    {
        "question": "What are metaclasses in Python?",
        "answer": "Metaclasses are classes of classes - they define how classes behave. type is the default metaclass. Custom metaclass: class Meta(type): def __new__(cls, name, bases, attrs). Use cases: registering classes, adding methods, enforcing interfaces, ORMs. class MyClass(metaclass=Meta) uses custom metaclass. __init_subclass__ is simpler alternative for many use cases. ABCs use metaclasses for abstract method enforcement."
    },
    {
        "question": "How do descriptors work?",
        "answer": "Descriptors are objects with __get__, __set__, or __delete__ methods that customize attribute access. Data descriptors define __set__ or __delete__, non-data only __get__. Powers @property, @classmethod, @staticmethod. Lookup order: data descriptor > instance dict > non-data descriptor > __getattr__. Use for: validation, computed attributes, caching, type checking. Example: class Validated: def __set__(self, obj, value): validate(value)"
    },
    {
        "question": "What is the difference between async/await and threading?",
        "answer": "Threading uses OS threads, has GIL limitations for CPU work, context switches are OS-managed. Async uses single thread with cooperative multitasking - coroutines yield control explicitly. Async is better for many I/O operations (thousands of connections), threading for blocking I/O or CPU-bound in separate processes. Async needs async-compatible libraries. Threading simpler for simple parallelism, async more efficient at scale. Don't mix blocking calls in async code."
    },
    {
        "question": "How do context managers work internally?",
        "answer": "Context managers implement __enter__ and __exit__ methods. __enter__ runs on 'with' start, returns value for 'as' clause. __exit__ runs on block exit, receives exception info (type, value, traceback) or None. Return True from __exit__ to suppress exceptions. @contextmanager decorator creates context managers from generator functions (yield separates enter/exit). contextlib provides utilities: closing, suppress, redirect_stdout. Async version: __aenter__/__aexit__."
    },
    {
        "question": "What are Protocols in Python typing?",
        "answer": "Protocols enable structural subtyping (duck typing with type checking). Define expected interface without inheritance: class Readable(Protocol): def read(self) -> str: .... Any class with matching methods satisfies the protocol. Use @runtime_checkable for isinstance() checks. Unlike ABCs, no registration needed - if it has the methods, it's compatible. Good for typing callback functions, plugins, or any duck-typed code. Introduced in Python 3.8, typing_extensions backports."
    },
]

# =============================================================================
# ERROR/GUARDRAIL SCENARIOS
# =============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "ImportError: No module named 'requests'",
        "error_type": "import_error",
        "response": {
            "status": "recoverable",
            "explanation": "Package not installed in current Python environment",
            "solutions": [
                "Install package: pip install requests",
                "Verify you're in correct virtual environment",
                "Check if package is in requirements.txt",
                "For conda: conda install requests"
            ],
            "diagnostic": "pip list | grep requests to check if installed"
        }
    },
    {
        "instruction": "TypeError: 'NoneType' object is not subscriptable",
        "error_type": "runtime_error",
        "response": {
            "status": "bug_found",
            "explanation": "Trying to index (e.g., x[0]) something that is None",
            "common_causes": [
                "Function returned None instead of expected value",
                "Dictionary .get() returned default None",
                "Variable not assigned in all code paths",
                "API returned null/None"
            ],
            "solutions": [
                "Add None check: if result is not None: result[0]",
                "Use default value: dict.get('key', default)",
                "Check function return values",
                "Add Optional type hint and handle None case"
            ]
        }
    },
    {
        "instruction": "RecursionError: maximum recursion depth exceeded",
        "error_type": "runtime_error",
        "response": {
            "status": "bug_found",
            "explanation": "Function calls itself too many times without base case",
            "common_causes": [
                "Missing or incorrect base case in recursive function",
                "Infinite recursion due to logic error",
                "Data structure has circular references"
            ],
            "solutions": [
                "Add proper base case to recursive function",
                "Convert to iterative approach with loop",
                "Use sys.setrecursionlimit() only if truly needed",
                "Use functools.lru_cache for memoization"
            ],
            "debugging": "Add print at function start to trace calls"
        }
    },
    {
        "instruction": "UnicodeDecodeError when reading file",
        "error_type": "encoding_error",
        "response": {
            "status": "recoverable",
            "explanation": "File encoding doesn't match expected encoding",
            "solutions": [
                "Specify encoding: open(file, encoding='utf-8')",
                "Try different encodings: 'latin-1', 'cp1252', 'utf-16'",
                "Detect encoding: chardet.detect()",
                "Use errors='ignore' or 'replace' as last resort"
            ],
            "best_practice": "Always specify encoding explicitly when opening files"
        }
    },
    {
        "instruction": "MemoryError when processing large file",
        "error_type": "resource_error",
        "response": {
            "status": "needs_optimization",
            "explanation": "Loading entire file into memory exceeds available RAM",
            "solutions": [
                "Read file line by line: for line in open(file)",
                "Use generators instead of lists",
                "Process in chunks: pandas.read_csv(chunksize=10000)",
                "Use memory-mapped files: mmap module",
                "Increase available memory or use 64-bit Python"
            ],
            "pattern": "Prefer streaming/iterating over loading all at once"
        }
    },
    {
        "instruction": "Circular import error",
        "error_type": "import_error",
        "response": {
            "status": "design_issue",
            "explanation": "Module A imports B, and B imports A",
            "solutions": [
                "Move shared code to third module C",
                "Use local imports inside functions",
                "Restructure code to break dependency",
                "Use TYPE_CHECKING guard for type hints only"
            ],
            "type_checking_pattern": "from typing import TYPE_CHECKING\\nif TYPE_CHECKING:\\n    from module import Type"
        }
    },
]

# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def format_command_response(command: str, explanation: str) -> str:
    return json.dumps({
        "action": "execute_command",
        "shell": "bash",
        "command": command,
        "explanation": explanation
    }, indent=2)

def format_code_response(code: str, explanation: str) -> str:
    return json.dumps({
        "action": "provide_code",
        "language": "python",
        "code": code,
        "explanation": explanation
    }, indent=2)

def format_planning_response(steps: List[str]) -> str:
    return json.dumps({
        "action": "multi_step_plan",
        "steps": [{"step": i+1, "action": step} for i, step in enumerate(steps)],
        "requires_confirmation": True
    }, indent=2)

def format_error_response(error_data: dict) -> str:
    return json.dumps(error_data, indent=2)

def generate_tool_examples() -> List[Dict]:
    examples = []
    
    for task in BASIC_PYTHON_TASKS + ADVANCED_PYTHON_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_command_response(task["command"], task["explanation"])
        })
    
    for task in CODE_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_code_response(task["code"], task["explanation"])
        })
    
    return examples

def generate_planning_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": task["instruction"],
        "response": format_planning_response(task["steps"])
    } for task in PLANNING_TASKS]

def generate_concept_examples() -> List[Dict]:
    return [{
        "system": SYSTEM_PROMPT,
        "instruction": concept["question"],
        "response": concept["answer"]
    } for concept in BASIC_CONCEPTS + ADVANCED_CONCEPTS]

def generate_error_examples() -> List[Dict]:
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
    variations = []
    
    python_tips = [
        ("How do I merge two dictionaries?", "Python 3.9+: merged = dict1 | dict2. Earlier: merged = {**dict1, **dict2}. Or dict1.update(dict2) modifies in-place. For nested merge, use dict | or deepmerge library."),
        ("What's the best way to read a CSV file?", "Use pandas: df = pd.read_csv('file.csv'). For simple cases: csv.DictReader(open('file.csv')). Pandas handles types, missing values, large files (chunksize parameter)."),
        ("How do I parse command line arguments?", "Use argparse (stdlib) or click (simpler). argparse: parser = argparse.ArgumentParser(); parser.add_argument('--name'); args = parser.parse_args(). click uses decorators: @click.command() @click.option('--name')."),
        ("How do I make an HTTP request?", "requests library: response = requests.get(url); response.json(). For async: aiohttp or httpx. httpx supports both sync and async. Always use timeout: requests.get(url, timeout=10)."),
        # NEW: Additional Python tips
        ("How do I handle environment variables?", "os.environ['VAR'] raises KeyError if missing. os.getenv('VAR', 'default') returns default. For .env files: python-dotenv library. load_dotenv() loads .env file."),
        ("What's the best way to handle dates?", "datetime module for basic ops. dateutil for parsing: dateutil.parser.parse('2024-01-15'). Arrow or Pendulum for timezone-aware. Always store/transmit in UTC."),
        ("How do I work with JSON?", "json.loads(string) parses string. json.load(file) reads file. json.dumps(obj, indent=2) formats. For datetimes: json.dumps(obj, default=str) or custom encoder."),
        ("How do I create a REST API?", "FastAPI: @app.get('/items/{id}') async def get_item(id: int). Flask: @app.route('/items/<id>'). Django REST Framework for complex APIs. FastAPI has auto-docs at /docs."),
        ("How do I connect to a database?", "SQLAlchemy for ORM: from sqlalchemy import create_engine. For raw SQL: psycopg2 (Postgres), pymysql (MySQL). Use connection pools in production. Always use parameterized queries."),
        ("How do I write async code?", "async def func(): await other_coroutine(). asyncio.run(main()) starts event loop. Use aiohttp for HTTP, asyncpg for Postgres. Don't mix sync blocking calls in async code."),
        ("How do I log in Python?", "import logging; logging.basicConfig(level=logging.INFO); logger = logging.getLogger(__name__). Use logger.info(), logger.error(). Configure handlers for file/console output."),
        ("How do I cache function results?", "@functools.lru_cache(maxsize=128) caches function calls. For time-based: cachetools.TTLCache. Redis for distributed caching. Consider memory impact for large caches."),
        ("How do I validate data?", "Pydantic: class User(BaseModel): name: str; age: int. Auto-validates on instantiation. Cerberus and Marshmallow are alternatives. dataclasses with __post_init__ for simple cases."),
        ("How do I work with files safely?", "Use 'with' statement: with open(path, 'r') as f. pathlib.Path for paths: path.read_text(), path.exists(). Always specify encoding='utf-8'."),
        ("How do I handle exceptions properly?", "Catch specific exceptions: except ValueError as e. Use finally for cleanup. raise from e preserves chain. Create custom exceptions inheriting from Exception."),
        ("How do I structure a Python project?", "src/ layout: src/package/__init__.py. tests/ separate from source. pyproject.toml for config. conftest.py for shared fixtures. Keep __init__.py minimal."),
        ("How do I use type hints?", "def func(name: str) -> int. Use Optional[str] for nullable. List[int], Dict[str, Any]. from typing import TypeVar for generics. Protocols for duck typing."),
        ("How do I work with threads?", "threading.Thread(target=func).start(). ThreadPoolExecutor for pools. Use Lock for shared state. Remember GIL limits CPU parallelism."),
        ("How do I do parallel processing?", "multiprocessing.Pool(4).map(func, items). ProcessPoolExecutor as context manager. Use for CPU-bound tasks. Be careful with shared state."),
        ("How do I profile memory usage?", "tracemalloc.start() in code. memory_profiler @profile decorator. objgraph.show_most_common_types() for object counts. gc.get_objects() for all objects."),
        ("How do I serialize Python objects?", "pickle for Python objects (not secure for untrusted data). json for portable data. joblib for numpy arrays. msgpack for fast binary serialization."),
        ("How do I work with regular expressions?", "import re; re.match(pattern, string). Use r'' raw strings. re.compile() for reuse. re.sub() for replacement. Named groups: (?P<name>pattern)."),
        ("How do I create a CLI tool?", "argparse for simple CLIs. click for complex (groups, colors). typer wraps click with type hints. Rich for beautiful output."),
        ("How do I work with YAML?", "pip install pyyaml. yaml.safe_load(file) is secure. yaml.dump(obj) creates YAML. ruamel.yaml preserves comments and formatting."),
        ("How do I work with SQLite?", "import sqlite3; conn = sqlite3.connect('db.sqlite'). cursor = conn.cursor(); cursor.execute(sql). conn.commit() for changes. Use parameterized queries: cursor.execute('SELECT * WHERE id=?', (id,))."),
        ("How do I send emails?", "smtplib for SMTP: server.sendmail(from, to, msg). email.mime for building messages. yagmail simplifies Gmail. For production: SendGrid, Mailgun APIs."),
        ("How do I work with Excel files?", "openpyxl for xlsx: wb.active.cell(1,1).value. pandas.read_excel() for analysis. xlsxwriter for creating. xlrd for old xls files."),
        ("How do I schedule tasks?", "schedule library: schedule.every(10).seconds.do(job). APScheduler for advanced. For system-level: cron or Windows Task Scheduler."),
        ("How do I create a web scraper?", "requests + BeautifulSoup for simple cases. Selenium/Playwright for JavaScript sites. Scrapy for large scale. Always respect robots.txt and rate limit."),
        ("How do I work with images?", "Pillow: Image.open(path).resize((100,100)).save(out). OpenCV for computer vision. imageio for animation. Always handle orientation exif data."),
        ("How do I debug Python code?", "pdb.set_trace() or breakpoint() in code. python -m pdb script.py. VS Code debugger with breakpoints. ipdb for IPython integration."),
        ("How do I test async code?", "pytest-asyncio: @pytest.mark.asyncio async def test_x(). Use aioresponses for mocking HTTP. pytest.fixture with async for fixtures."),
        ("How do I mock in tests?", "from unittest.mock import Mock, patch. @patch('module.function') decorator. mock.return_value, mock.side_effect. Mock.assert_called_with() for verification."),
        ("How do I create fixtures in pytest?", "@pytest.fixture def client(): return TestClient(app). Scope: function, class, module, session. conftest.py for shared fixtures."),
        ("How do I use dataclasses?", "@dataclass class Person: name: str; age: int = 0. Auto-generates __init__, __repr__. Use field(default_factory=list) for mutable defaults."),
        ("How do I create enums?", "from enum import Enum, auto. class Status(Enum): PENDING = auto(). Access: Status.PENDING, Status['PENDING'], Status(1)."),
        ("How do I use slots?", "__slots__ = ['x', 'y'] saves memory by not using __dict__. Prevents adding new attributes. Good for many instances of same class."),
        ("How do I implement __eq__ properly?", "def __eq__(self, other): if not isinstance(other, MyClass): return NotImplemented; return self.x == other.x. Also implement __hash__ if hashable."),
        ("How do I use contextlib?", "@contextmanager yields value. suppress() ignores exceptions. closing() ensures close(). redirect_stdout() for capturing output."),
        ("How do I work with paths?", "pathlib.Path('dir/file.txt'). path.parent, path.stem, path.suffix. path / 'subdir' for joining. path.glob('*.py') for matching."),
        ("How do I limit API rate?", "ratelimit library: @limits(calls=10, period=60). Or manual: time.sleep() between calls. Token bucket for more control."),
        ("What's the walrus operator?", ":= assigns and returns value. if (n := len(data)) > 10: print(f'{n} items'). while (line := f.readline()): process(line). Python 3.8+."),
        ("How do I use match statement?", "match value: case 1: ...; case [x, y]: ...; case _: default. Python 3.10+. Pattern matching like Rust/Scala."),
        ("How do I use positional-only parameters?", "def func(x, /, y, *, z): ... x is positional-only, z is keyword-only. Python 3.8+. Use for API design."),
    ]
    
    for query, answer in python_tips:
        variations.append({
            "system": SYSTEM_PROMPT,
            "instruction": query,
            "response": answer
        })
    
    return variations

def main():
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating Python Development Training Data")
    print("=" * 60)
    
    all_examples = []
    
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
    
    random.shuffle(all_examples)
    
    output_file = output_dir / "python_development.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_examples)} examples to {output_file}")
    print(f"\nTotal: {len(all_examples)}")

if __name__ == "__main__":
    main()
