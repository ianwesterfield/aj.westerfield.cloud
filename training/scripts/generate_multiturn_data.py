#!/usr/bin/env python3
"""
Generate multi-turn conversation training examples.

Focuses on conversational context - follow-up questions, iterative refinement,
debugging sessions, and progressive complexity building.
"""

import json
from pathlib import Path
from typing import List, Dict

# Output path
OUTPUT_DIR = Path(__file__).parent.parent / "data"

SYSTEM_PROMPT = """You are AJ, a technical AI assistant created by AJ Westerfield. You maintain context across conversation turns, remember what you've discussed, and can iteratively refine solutions based on follow-up requests. You reference previous code you've provided when asked to modify or extend it."""

# Multi-turn conversation examples
# Each example contains multiple turns to simulate ongoing conversation
MULTITURN_CONVERSATIONS: List[Dict] = [
    # Follow-up refinement pattern
    {
        "context": "User asks for a function, then requests modifications",
        "turns": [
            {
                "instruction": "Write a Python function to fetch data from a URL",
                "response": {
                    "action": "provide_code",
                    "language": "python",
                    "code": '''import requests

def fetch_data(url: str) -> dict:
    """Fetch JSON data from a URL."""
    response = requests.get(url)
    response.raise_for_status()
    return response.json()''',
                    "explanation": "Simple function using requests library to fetch JSON data."
                }
            },
            {
                "instruction": "Can you add timeout and retry logic?",
                "response": {
                    "action": "provide_code",
                    "language": "python",
                    "code": '''import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def fetch_data(url: str, timeout: int = 30, max_retries: int = 3) -> dict:
    """Fetch JSON data from a URL with timeout and retry logic."""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()''',
                    "explanation": "Added configurable timeout and retry with exponential backoff for transient failures."
                }
            },
            {
                "instruction": "Now make it async",
                "response": {
                    "action": "provide_code",
                    "language": "python",
                    "code": '''import httpx
import asyncio
from typing import Optional

async def fetch_data(
    url: str,
    timeout: int = 30,
    max_retries: int = 3,
    backoff_factor: float = 1.0
) -> dict:
    """Fetch JSON data asynchronously with timeout and retry logic."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        last_exception: Optional[Exception] = None
        
        for attempt in range(max_retries):
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = backoff_factor * (2 ** attempt)
                    await asyncio.sleep(wait_time)
        
        raise last_exception''',
                    "explanation": "Converted to async using httpx with manual retry loop for full control over backoff."
                }
            }
        ]
    },
    
    # Debugging session pattern
    {
        "context": "User encounters an error and needs help debugging",
        "turns": [
            {
                "instruction": "My Flask app is crashing with 'Working outside of application context'. Here's my code:\n\n```python\nfrom flask import Flask, g\nfrom models import db\n\napp = Flask(__name__)\napp.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'\ndb.init_app(app)\n\ndef get_user(user_id):\n    return db.session.query(User).get(user_id)\n```",
                "response": {
                    "action": "concepts",
                    "diagnosis": "The error occurs because `db.session.query()` is called outside a request context. Flask-SQLAlchemy needs an active application context to access the database.",
                    "solution": "You need to wrap database operations in an application context, or ensure they're called during a request.",
                    "code_fix": '''# Option 1: Use app context for standalone operations
def get_user(user_id):
    with app.app_context():
        return db.session.query(User).get(user_id)

# Option 2: Better - call from within a route
@app.route('/user/<int:user_id>')
def show_user(user_id):
    user = db.session.query(User).get(user_id)  # Works here
    return jsonify(user.to_dict())

# Option 3: For CLI commands or scripts
if __name__ == '__main__':
    with app.app_context():
        user = get_user(1)'''
                }
            },
            {
                "instruction": "That fixed it. But now I'm getting a different error: 'DetachedInstanceError' when I try to access user.orders after the request",
                "response": {
                    "action": "concepts",
                    "diagnosis": "DetachedInstanceError occurs when you try to access lazy-loaded relationships on an object after the session that loaded it has closed. The `user` object became 'detached' from the session.",
                    "solutions": [
                        "Eager load relationships in the original query",
                        "Access relationships while still in the session",
                        "Use `session.expire_on_commit = False`",
                        "Convert to dict before returning"
                    ],
                    "code_fix": '''from sqlalchemy.orm import joinedload

# Option 1: Eager load relationships
def get_user_with_orders(user_id):
    return db.session.query(User).options(
        joinedload(User.orders)
    ).get(user_id)

# Option 2: Access everything in route, return dict
@app.route('/user/<int:user_id>')
def show_user(user_id):
    user = db.session.query(User).options(
        joinedload(User.orders)
    ).get(user_id)
    
    # Access relationships while session is active
    return jsonify({
        'id': user.id,
        'name': user.name,
        'orders': [{'id': o.id, 'total': o.total} for o in user.orders]
    })'''
                }
            },
            {
                "instruction": "Perfect! One more thing - how do I handle the case where the user doesn't exist?",
                "response": {
                    "action": "provide_code",
                    "language": "python",
                    "code": '''from flask import Flask, jsonify, abort
from sqlalchemy.orm import joinedload

@app.route('/user/<int:user_id>')
def show_user(user_id):
    user = db.session.query(User).options(
        joinedload(User.orders)
    ).get(user_id)
    
    if user is None:
        abort(404, description=f"User {user_id} not found")
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'orders': [{'id': o.id, 'total': o.total} for o in user.orders]
    })

# Or use get_or_404 shorthand
@app.route('/user/<int:user_id>')
def show_user(user_id):
    user = User.query.options(
        joinedload(User.orders)
    ).get_or_404(user_id, description=f"User {user_id} not found")
    
    return jsonify(user.to_dict())''',
                    "explanation": "Use `abort(404)` or the convenient `get_or_404()` method to handle missing resources with proper HTTP status codes."
                }
            }
        ]
    },
    
    # Progressive complexity building
    {
        "context": "Building a feature from simple to complex",
        "turns": [
            {
                "instruction": "I need a simple logger for my Python app",
                "response": {
                    "action": "provide_code",
                    "language": "python",
                    "code": '''import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Usage:
logger.info("Application started")
logger.error("Something went wrong", exc_info=True)''',
                    "explanation": "Basic logging setup with timestamp and level formatting."
                }
            },
            {
                "instruction": "Can you make it write to a file too?",
                "response": {
                    "action": "provide_code",
                    "language": "python",
                    "code": '''import logging
from pathlib import Path

def setup_logger(name: str, log_file: str = "app.log") -> logging.Logger:
    """Set up logger with console and file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # File handler
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger(__name__)''',
                    "explanation": "Added file handler with separate log levels - DEBUG to file, INFO to console."
                }
            },
            {
                "instruction": "I need log rotation so files don't get too big",
                "response": {
                    "action": "provide_code",
                    "language": "python",
                    "code": '''import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path

def setup_logger(
    name: str,
    log_dir: str = "logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """Set up logger with rotating file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Rotating file handler (by size)
    file_handler = RotatingFileHandler(
        log_path / "app.log",
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Daily rotating handler for errors
    error_handler = TimedRotatingFileHandler(
        log_path / "error.log",
        when="midnight",
        interval=1,
        backupCount=30  # Keep 30 days
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger''',
                    "explanation": "Added RotatingFileHandler for size-based rotation and TimedRotatingFileHandler for daily error logs."
                }
            },
            {
                "instruction": "Now I want JSON formatted logs for production",
                "response": {
                    "action": "provide_code",
                    "language": "python",
                    "code": '''import logging
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)

class ContextLogger(logging.LoggerAdapter):
    """Logger adapter that adds context to all messages."""
    
    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        extra["extra_fields"] = {**self.extra, **extra.get("extra_fields", {})}
        kwargs["extra"] = extra
        return msg, kwargs

def setup_json_logger(
    name: str,
    log_dir: str = "logs",
    context: Dict[str, Any] = None
) -> ContextLogger:
    """Set up JSON logger with context support."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # JSON file handler
    json_handler = RotatingFileHandler(
        log_path / "app.json.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    json_handler.setFormatter(JSONFormatter())
    logger.addHandler(json_handler)
    
    # Pretty console for development
    if __debug__:
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter(
            '%(levelname)s: %(message)s'
        ))
        logger.addHandler(console)
    
    return ContextLogger(logger, context or {})

# Usage:
logger = setup_json_logger("myapp", context={"service": "api", "version": "1.0"})
logger.info("User logged in", extra={"extra_fields": {"user_id": 123}})''',
                    "explanation": "Full JSON logging with custom formatter, context support, and structured extra fields for log aggregation systems."
                }
            }
        ]
    },
    
    # Iterative requirements clarification
    {
        "context": "Clarifying requirements through conversation",
        "turns": [
            {
                "instruction": "I need a function to validate user input",
                "response": {
                    "action": "concepts",
                    "clarification_needed": True,
                    "questions": [
                        "What kind of input? (form data, JSON payload, CLI arguments?)",
                        "What fields need validation? (email, password, age, custom fields?)",
                        "What framework are you using? (Flask, FastAPI, Django, plain Python?)",
                        "Do you need to return error messages or raise exceptions?"
                    ],
                    "initial_suggestion": "Here's a basic example while you clarify - a simple dict validator:\n\n```python\ndef validate_user(data: dict) -> tuple[bool, list[str]]:\n    errors = []\n    if not data.get('email'):\n        errors.append('Email is required')\n    if not data.get('password'):\n        errors.append('Password is required')\n    return len(errors) == 0, errors\n```"
                }
            },
            {
                "instruction": "It's for a FastAPI endpoint. I need to validate email format, password strength (8+ chars, number, special char), and age (18+)",
                "response": {
                    "action": "provide_code",
                    "language": "python",
                    "code": '''from pydantic import BaseModel, EmailStr, Field, validator
import re

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    age: int = Field(..., ge=18)
    
    @validator('password')
    def validate_password_strength(cls, v):
        if not re.search(r'\\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

# FastAPI endpoint
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.post("/users")
async def create_user(user: UserCreate):
    # Validation happens automatically!
    # If validation fails, FastAPI returns 422 with error details
    return {"email": user.email, "age": user.age}''',
                    "explanation": "Using Pydantic models with FastAPI gives you automatic validation, clear error messages, and request documentation."
                }
            },
            {
                "instruction": "Can you also check that the email isn't already taken?",
                "response": {
                    "action": "provide_code",
                    "language": "python",
                    "code": '''from pydantic import BaseModel, EmailStr, Field, validator
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
import re

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    age: int = Field(..., ge=18)
    
    @validator('password')
    def validate_password_strength(cls, v):
        if not re.search(r'\\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def validate_unique_email(email: str, db: Session) -> None:
    """Check if email is already registered."""
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

@app.post("/users", status_code=201)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check uniqueness (can't do in Pydantic - needs DB)
    await validate_unique_email(user.email, db)
    
    # Create user
    db_user = User(
        email=user.email,
        password_hash=hash_password(user.password),
        age=user.age
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {"id": db_user.id, "email": db_user.email}''',
                    "explanation": "Database validation must happen in the endpoint since Pydantic validators can't access the database. Using HTTPException with 409 Conflict for duplicate emails."
                }
            }
        ]
    },
    
    # Code extension pattern
    {
        "context": "User asks to extend previously provided code",
        "turns": [
            {
                "instruction": "Write a simple React component for a todo list",
                "response": {
                    "action": "provide_code",
                    "language": "tsx",
                    "code": '''import { useState } from 'react';

interface Todo {
    id: number;
    text: string;
    completed: boolean;
}

function TodoList() {
    const [todos, setTodos] = useState<Todo[]>([]);
    const [input, setInput] = useState('');

    const addTodo = () => {
        if (input.trim()) {
            setTodos([...todos, {
                id: Date.now(),
                text: input.trim(),
                completed: false
            }]);
            setInput('');
        }
    };

    const toggleTodo = (id: number) => {
        setTodos(todos.map(todo =>
            todo.id === id ? { ...todo, completed: !todo.completed } : todo
        ));
    };

    return (
        <div>
            <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Add todo..."
            />
            <button onClick={addTodo}>Add</button>
            <ul>
                {todos.map(todo => (
                    <li
                        key={todo.id}
                        onClick={() => toggleTodo(todo.id)}
                        style={{ textDecoration: todo.completed ? 'line-through' : 'none' }}
                    >
                        {todo.text}
                    </li>
                ))}
            </ul>
        </div>
    );
}''',
                    "explanation": "Basic todo list with add and toggle functionality."
                }
            },
            {
                "instruction": "Add delete functionality and a filter to show all/active/completed",
                "response": {
                    "action": "provide_code",
                    "language": "tsx",
                    "code": '''import { useState, useMemo } from 'react';

interface Todo {
    id: number;
    text: string;
    completed: boolean;
}

type Filter = 'all' | 'active' | 'completed';

function TodoList() {
    const [todos, setTodos] = useState<Todo[]>([]);
    const [input, setInput] = useState('');
    const [filter, setFilter] = useState<Filter>('all');

    const addTodo = () => {
        if (input.trim()) {
            setTodos([...todos, {
                id: Date.now(),
                text: input.trim(),
                completed: false
            }]);
            setInput('');
        }
    };

    const toggleTodo = (id: number) => {
        setTodos(todos.map(todo =>
            todo.id === id ? { ...todo, completed: !todo.completed } : todo
        ));
    };

    const deleteTodo = (id: number) => {
        setTodos(todos.filter(todo => todo.id !== id));
    };

    const filteredTodos = useMemo(() => {
        switch (filter) {
            case 'active':
                return todos.filter(t => !t.completed);
            case 'completed':
                return todos.filter(t => t.completed);
            default:
                return todos;
        }
    }, [todos, filter]);

    const activeCount = todos.filter(t => !t.completed).length;

    return (
        <div>
            <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addTodo()}
                placeholder="Add todo..."
            />
            <button onClick={addTodo}>Add</button>

            <div className="filters">
                {(['all', 'active', 'completed'] as Filter[]).map(f => (
                    <button
                        key={f}
                        onClick={() => setFilter(f)}
                        className={filter === f ? 'active' : ''}
                    >
                        {f.charAt(0).toUpperCase() + f.slice(1)}
                    </button>
                ))}
            </div>

            <ul>
                {filteredTodos.map(todo => (
                    <li key={todo.id}>
                        <span
                            onClick={() => toggleTodo(todo.id)}
                            style={{ textDecoration: todo.completed ? 'line-through' : 'none' }}
                        >
                            {todo.text}
                        </span>
                        <button onClick={() => deleteTodo(todo.id)}>×</button>
                    </li>
                ))}
            </ul>

            <p>{activeCount} items left</p>
        </div>
    );
}''',
                    "explanation": "Added delete with filter button, filter state, useMemo for filtered list, Enter key support, and item count."
                }
            },
            {
                "instruction": "Now persist to localStorage so it survives refresh",
                "response": {
                    "action": "provide_code",
                    "language": "tsx",
                    "code": '''import { useState, useMemo, useEffect, useCallback } from 'react';

interface Todo {
    id: number;
    text: string;
    completed: boolean;
}

type Filter = 'all' | 'active' | 'completed';

const STORAGE_KEY = 'todos';

function useTodos() {
    const [todos, setTodos] = useState<Todo[]>(() => {
        // Initialize from localStorage
        const stored = localStorage.getItem(STORAGE_KEY);
        return stored ? JSON.parse(stored) : [];
    });

    // Persist to localStorage on change
    useEffect(() => {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(todos));
    }, [todos]);

    const addTodo = useCallback((text: string) => {
        if (text.trim()) {
            setTodos(prev => [...prev, {
                id: Date.now(),
                text: text.trim(),
                completed: false
            }]);
        }
    }, []);

    const toggleTodo = useCallback((id: number) => {
        setTodos(prev => prev.map(todo =>
            todo.id === id ? { ...todo, completed: !todo.completed } : todo
        ));
    }, []);

    const deleteTodo = useCallback((id: number) => {
        setTodos(prev => prev.filter(todo => todo.id !== id));
    }, []);

    const clearCompleted = useCallback(() => {
        setTodos(prev => prev.filter(todo => !todo.completed));
    }, []);

    return { todos, addTodo, toggleTodo, deleteTodo, clearCompleted };
}

function TodoList() {
    const { todos, addTodo, toggleTodo, deleteTodo, clearCompleted } = useTodos();
    const [input, setInput] = useState('');
    const [filter, setFilter] = useState<Filter>('all');

    const handleAdd = () => {
        addTodo(input);
        setInput('');
    };

    const filteredTodos = useMemo(() => {
        switch (filter) {
            case 'active':
                return todos.filter(t => !t.completed);
            case 'completed':
                return todos.filter(t => t.completed);
            default:
                return todos;
        }
    }, [todos, filter]);

    const activeCount = todos.filter(t => !t.completed).length;
    const hasCompleted = todos.some(t => t.completed);

    return (
        <div className="todo-app">
            <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAdd()}
                placeholder="What needs to be done?"
            />
            <button onClick={handleAdd}>Add</button>

            <div className="filters">
                {(['all', 'active', 'completed'] as Filter[]).map(f => (
                    <button
                        key={f}
                        onClick={() => setFilter(f)}
                        className={filter === f ? 'active' : ''}
                    >
                        {f.charAt(0).toUpperCase() + f.slice(1)}
                    </button>
                ))}
            </div>

            <ul>
                {filteredTodos.map(todo => (
                    <li key={todo.id}>
                        <input
                            type="checkbox"
                            checked={todo.completed}
                            onChange={() => toggleTodo(todo.id)}
                        />
                        <span style={{ textDecoration: todo.completed ? 'line-through' : 'none' }}>
                            {todo.text}
                        </span>
                        <button onClick={() => deleteTodo(todo.id)}>×</button>
                    </li>
                ))}
            </ul>

            <footer>
                <span>{activeCount} items left</span>
                {hasCompleted && (
                    <button onClick={clearCompleted}>Clear completed</button>
                )}
            </footer>
        </div>
    );
}

export default TodoList;''',
                    "explanation": "Extracted todo logic into custom hook `useTodos` with localStorage persistence. Added lazy initialization, useCallback for stable references, checkbox inputs, and clear completed button."
                }
            }
        ]
    },
    
    # Error investigation pattern  
    {
        "context": "Step-by-step troubleshooting",
        "turns": [
            {
                "instruction": "My Docker container exits immediately after starting. The logs just show 'Exited (1)'",
                "response": {
                    "action": "multi_step_plan",
                    "diagnosis_steps": [
                        "Get the container logs: `docker logs <container_id>`",
                        "Check exit code meaning: `docker inspect <container_id> --format='{{.State.ExitCode}}'`",
                        "Review Dockerfile CMD/ENTRYPOINT",
                        "Try running interactively: `docker run -it <image> /bin/sh`"
                    ],
                    "common_causes": [
                        "Process crashes on startup (check logs)",
                        "No foreground process (container exits when main process ends)",
                        "Missing environment variables",
                        "Permission issues",
                        "Missing dependencies"
                    ],
                    "initial_commands": "```bash\n# Get detailed exit info\ndocker logs --tail 100 <container_id>\n\n# Check what command was run\ndocker inspect <container_id> --format='{{.Config.Cmd}}'\n```"
                }
            },
            {
                "instruction": "The logs show 'exec /app/start.sh: no such file or directory' but the file is definitely there in my Dockerfile",
                "response": {
                    "action": "concepts",
                    "diagnosis": "This error usually means one of two things:\n1. The file exists but has wrong line endings (CRLF instead of LF)\n2. The shebang points to a non-existent interpreter",
                    "likely_cause": "If you're developing on Windows, your start.sh probably has Windows line endings (CRLF). Linux interprets the shebang as `#!/bin/bash\\r` and can't find that interpreter.",
                    "solutions": [
                        "Convert to Unix line endings in your editor",
                        "Add dos2unix to your Dockerfile",
                        "Use .gitattributes to enforce LF"
                    ],
                    "code_fix": '''# Option 1: Fix in Dockerfile
RUN apt-get update && apt-get install -y dos2unix
COPY start.sh /app/start.sh
RUN dos2unix /app/start.sh && chmod +x /app/start.sh

# Option 2: Fix with sed (no extra package)
COPY start.sh /app/start.sh
RUN sed -i 's/\\r$//' /app/start.sh && chmod +x /app/start.sh

# Option 3: Prevent in .gitattributes
# Add to .gitattributes:
*.sh text eol=lf'''
                }
            },
            {
                "instruction": "That was it! The dos2unix fix worked. Now the container starts but my Node app says 'EADDRINUSE: address already in use :::3000'",
                "response": {
                    "action": "concepts",
                    "diagnosis": "EADDRINUSE means port 3000 is already bound. In Docker context, this usually means:\n1. Multiple processes in the container trying to use the same port\n2. Your start script is running the app multiple times\n3. A previous container instance is still running",
                    "solutions": [
                        "Check if another container is using port 3000: `docker ps`",
                        "Check for multiple processes: review start.sh",
                        "Use different host port: `docker run -p 3001:3000`",
                        "Stop conflicting containers: `docker stop $(docker ps -q)`"
                    ],
                    "commands": '''# Check what's using the port on host
# Linux/Mac:
lsof -i :3000

# Windows:
netstat -ano | findstr :3000

# Kill conflicting container
docker ps -a | grep 3000
docker stop <container_id>
docker rm <container_id>

# Run with different host port
docker run -p 8080:3000 myapp'''
                }
            }
        ]
    },
    
    # Clarification and alternatives
    {
        "context": "User needs to choose between approaches",
        "turns": [
            {
                "instruction": "What's the best way to handle state in React?",
                "response": {
                    "action": "concepts",
                    "answer": "It depends on your needs. Let me break down the options:",
                    "options": {
                        "useState": "Simple component-local state. Good for: form inputs, toggles, local UI state.",
                        "useReducer": "Complex state with multiple sub-values or state that depends on previous state. Good for: forms with many fields, undo/redo.",
                        "Context + useReducer": "App-wide state without prop drilling. Good for: themes, auth, settings.",
                        "Zustand": "Simple global state with minimal boilerplate. Good for: medium apps wanting simpler than Redux.",
                        "Redux Toolkit": "Full-featured state management with devtools, middleware, time-travel debugging. Good for: large apps, complex async flows.",
                        "React Query/TanStack Query": "Server state management with caching. Good for: data fetching, API state."
                    },
                    "recommendation": "For most apps, start with useState/useReducer. Add Context for shared state. Consider React Query for server data. Only reach for Redux if you need its specific features."
                }
            },
            {
                "instruction": "I have a medium-sized app with lots of API calls. Users can edit data and I need optimistic updates. What would you recommend?",
                "response": {
                    "action": "concepts",
                    "recommendation": "For your use case (medium app, lots of API calls, optimistic updates), I'd recommend **TanStack Query (React Query)** combined with **Zustand** for client-only state.",
                    "reasoning": [
                        "React Query handles all server state: caching, refetching, optimistic updates, mutations",
                        "Zustand is minimal for any client-only state you need (UI preferences, etc.)",
                        "Both have excellent DevTools",
                        "Much less boilerplate than Redux"
                    ],
                    "example": '''// React Query for server state with optimistic updates
import { useMutation, useQueryClient } from '@tanstack/react-query';

function useUpdateTodo() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: (todo) => api.updateTodo(todo),
        
        // Optimistic update
        onMutate: async (newTodo) => {
            await queryClient.cancelQueries({ queryKey: ['todos'] });
            const previous = queryClient.getQueryData(['todos']);
            
            queryClient.setQueryData(['todos'], (old) =>
                old.map(t => t.id === newTodo.id ? newTodo : t)
            );
            
            return { previous };
        },
        
        // Rollback on error
        onError: (err, newTodo, context) => {
            queryClient.setQueryData(['todos'], context.previous);
        },
        
        // Refetch on success
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: ['todos'] });
        },
    });
}'''
                }
            },
            {
                "instruction": "Can you show me how to set that up from scratch?",
                "response": {
                    "action": "multi_step_plan",
                    "steps": [
                        {
                            "step": 1,
                            "title": "Install dependencies",
                            "command": "npm install @tanstack/react-query zustand"
                        },
                        {
                            "step": 2,
                            "title": "Set up Query Client",
                            "code": '''// src/lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 1000 * 60 * 5, // 5 minutes
            retry: 1,
        },
    },
});'''
                        },
                        {
                            "step": 3,
                            "title": "Wrap app with provider",
                            "code": '''// src/App.tsx
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from './lib/queryClient';

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <YourApp />
            <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
    );
}'''
                        },
                        {
                            "step": 4,
                            "title": "Create Zustand store for client state",
                            "code": '''// src/stores/uiStore.ts
import { create } from 'zustand';

interface UIState {
    sidebarOpen: boolean;
    toggleSidebar: () => void;
    theme: 'light' | 'dark';
    setTheme: (theme: 'light' | 'dark') => void;
}

export const useUIStore = create<UIState>((set) => ({
    sidebarOpen: true,
    toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
    theme: 'light',
    setTheme: (theme) => set({ theme }),
}));'''
                        },
                        {
                            "step": 5,
                            "title": "Use in components",
                            "code": '''// Using React Query for server state
function TodoList() {
    const { data: todos, isLoading } = useQuery({
        queryKey: ['todos'],
        queryFn: () => api.getTodos(),
    });

    if (isLoading) return <Spinner />;
    return <ul>{todos.map(t => <TodoItem key={t.id} todo={t} />)}</ul>;
}

// Using Zustand for UI state
function Sidebar() {
    const { sidebarOpen, toggleSidebar } = useUIStore();
    
    return sidebarOpen ? <nav>...</nav> : null;
}'''
                        }
                    ]
                }
            }
        ]
    },
    
    # API design iteration
    {
        "context": "Designing an API endpoint iteratively",
        "turns": [
            {
                "instruction": "I need a REST endpoint for user search",
                "response": {
                    "action": "provide_code",
                    "language": "python",
                    "code": '''from fastapi import FastAPI, Query
from typing import List
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    id: int
    name: str
    email: str

@app.get("/users/search")
async def search_users(q: str = Query(..., min_length=2)) -> List[User]:
    """Search users by name or email."""
    results = await db.search_users(q)
    return results''',
                    "explanation": "Basic search endpoint with query parameter validation."
                }
            },
            {
                "instruction": "I need pagination too",
                "response": {
                    "action": "provide_code",
                    "language": "python",
                    "code": '''from fastapi import FastAPI, Query
from typing import List, Generic, TypeVar
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar('T')

class PaginatedResponse(GenericModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    per_page: int
    pages: int

class User(BaseModel):
    id: int
    name: str
    email: str

@app.get("/users/search")
async def search_users(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
) -> PaginatedResponse[User]:
    """Search users with pagination."""
    total, results = await db.search_users(q, page, per_page)
    
    return PaginatedResponse(
        items=results,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page
    )''',
                    "explanation": "Added generic paginated response with page/per_page parameters and metadata."
                }
            },
            {
                "instruction": "Can I also filter by role and sort by different fields?",
                "response": {
                    "action": "provide_code",
                    "language": "python",
                    "code": '''from fastapi import FastAPI, Query, Depends
from typing import List, Optional, Literal
from pydantic import BaseModel
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"

class SortField(str, Enum):
    NAME = "name"
    EMAIL = "email"
    CREATED_AT = "created_at"

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class SearchParams(BaseModel):
    """Search parameters - using a model for cleaner dependency injection."""
    q: str
    role: Optional[UserRole] = None
    sort_by: SortField = SortField.NAME
    sort_order: SortOrder = SortOrder.ASC
    page: int = 1
    per_page: int = 20

    class Config:
        use_enum_values = True

def get_search_params(
    q: str = Query(..., min_length=2, description="Search query"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    sort_by: SortField = Query(SortField.NAME, description="Sort field"),
    sort_order: SortOrder = Query(SortOrder.ASC, description="Sort direction"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page")
) -> SearchParams:
    return SearchParams(
        q=q, role=role, sort_by=sort_by, 
        sort_order=sort_order, page=page, per_page=per_page
    )

@app.get("/users/search")
async def search_users(
    params: SearchParams = Depends(get_search_params)
) -> PaginatedResponse[User]:
    """Search users with filtering, sorting, and pagination."""
    query = db.users.search(params.q)
    
    if params.role:
        query = query.filter(role=params.role)
    
    query = query.order_by(params.sort_by, params.sort_order)
    
    total = await query.count()
    results = await query.paginate(params.page, params.per_page)
    
    return PaginatedResponse(
        items=results,
        total=total,
        page=params.page,
        per_page=params.per_page,
        pages=(total + params.per_page - 1) // params.per_page
    )''',
                    "explanation": "Added role filter with enum, sort field/order enums, and extracted params to dependency for reusability and cleaner code."
                }
            }
        ]
    },
    
    # Testing guidance conversation
    {
        "context": "Learning about testing through conversation",
        "turns": [
            {
                "instruction": "How should I test this function?\n\n```python\ndef calculate_discount(price: float, user_type: str, coupon: str = None) -> float:\n    discount = 0\n    if user_type == 'premium':\n        discount += 0.1\n    if coupon == 'SAVE20':\n        discount += 0.2\n    return price * (1 - min(discount, 0.3))\n```",
                "response": {
                    "action": "concepts",
                    "test_strategy": "This function has multiple conditions that combine. You should test:\n\n1. **Base cases**: No discount applied\n2. **Individual conditions**: Premium only, coupon only\n3. **Combined conditions**: Premium + coupon\n4. **Edge cases**: Max discount cap, zero/negative prices\n5. **Invalid inputs**: Unknown user types, invalid coupons",
                    "code": '''import pytest
from your_module import calculate_discount

class TestCalculateDiscount:
    """Test discount calculation with various user types and coupons."""
    
    # Base case - no discounts
    def test_regular_user_no_coupon(self):
        assert calculate_discount(100, 'regular') == 100
    
    # Premium user discount (10%)
    def test_premium_user_discount(self):
        assert calculate_discount(100, 'premium') == 90
    
    # Coupon discount (20%)
    def test_coupon_discount(self):
        assert calculate_discount(100, 'regular', 'SAVE20') == 80
    
    # Combined - should cap at 30%
    def test_premium_with_coupon_caps_at_30_percent(self):
        # Premium (10%) + coupon (20%) = 30%, not 30%
        assert calculate_discount(100, 'premium', 'SAVE20') == 70
    
    # Edge cases
    def test_zero_price(self):
        assert calculate_discount(0, 'premium', 'SAVE20') == 0
    
    def test_invalid_coupon_no_discount(self):
        assert calculate_discount(100, 'regular', 'INVALID') == 100
    
    # Unknown user type - currently gets no discount
    def test_unknown_user_type(self):
        assert calculate_discount(100, 'unknown') == 100'''
                }
            },
            {
                "instruction": "Should I use parametrize instead of all these separate tests?",
                "response": {
                    "action": "concepts",
                    "answer": "Both approaches have merit. Here's when to use each:\n\n**Separate tests when:**\n- Each case has different setup/teardown\n- Failure messages need to be very specific\n- Tests represent distinct business scenarios\n\n**Parametrize when:**\n- Testing the same behavior with different inputs\n- You have many simple input/output pairs\n- The test logic is identical, only data differs",
                    "refactored": '''import pytest
from your_module import calculate_discount

class TestCalculateDiscount:
    
    @pytest.mark.parametrize("price,user_type,coupon,expected", [
        # Base case - no discounts
        (100, 'regular', None, 100),
        
        # Premium discount only (10%)
        (100, 'premium', None, 90),
        (200, 'premium', None, 180),
        
        # Coupon discount only (20%)
        (100, 'regular', 'SAVE20', 80),
        
        # Combined - capped at 30%
        (100, 'premium', 'SAVE20', 70),
        (50, 'premium', 'SAVE20', 35),
        
        # Edge cases
        (0, 'premium', 'SAVE20', 0),
        (100, 'regular', 'INVALID', 100),
        (100, 'unknown', None, 100),
    ])
    def test_discount_calculation(self, price, user_type, coupon, expected):
        assert calculate_discount(price, user_type, coupon) == expected
    
    # Keep complex scenarios as separate tests
    def test_discount_never_exceeds_30_percent(self):
        """Verify the 30% cap regardless of accumulated discounts."""
        # If business logic changes to allow more discount types,
        # this test documents the cap behavior
        result = calculate_discount(100, 'premium', 'SAVE20')
        assert result >= 70, "Discount should never exceed 30%"'''
                }
            },
            {
                "instruction": "What about testing floats? I've heard that can cause issues",
                "response": {
                    "action": "concepts",
                    "explanation": "Great catch! Floating point comparison can be tricky due to precision errors. For example, `0.1 + 0.2` doesn't exactly equal `0.3` in floating point.",
                    "solutions": [
                        "Use `pytest.approx()` for approximate comparison",
                        "Use `Decimal` for financial calculations",
                        "Compare with tolerance"
                    ],
                    "code": '''import pytest
from decimal import Decimal
from your_module import calculate_discount

class TestCalculateDiscount:
    
    @pytest.mark.parametrize("price,user_type,coupon,expected", [
        (100, 'premium', 'SAVE20', 70),
        (99.99, 'premium', None, 89.991),  # Could have precision issues
        (33.33, 'regular', 'SAVE20', 26.664),
    ])
    def test_discount_with_approx(self, price, user_type, coupon, expected):
        # Use pytest.approx for floating point comparison
        result = calculate_discount(price, user_type, coupon)
        assert result == pytest.approx(expected, rel=1e-9)
    
    def test_floating_point_precision(self):
        # This test documents potential precision issues
        result = calculate_discount(33.33, 'premium', 'SAVE20')
        # Don't compare exactly - use approx
        assert result == pytest.approx(23.331, abs=0.001)


# BETTER APPROACH: Use Decimal for money
from decimal import Decimal, ROUND_HALF_UP

def calculate_discount_decimal(
    price: Decimal, 
    user_type: str, 
    coupon: str = None
) -> Decimal:
    """Financial-safe discount calculation using Decimal."""
    discount = Decimal('0')
    
    if user_type == 'premium':
        discount += Decimal('0.10')
    if coupon == 'SAVE20':
        discount += Decimal('0.20')
    
    discount = min(discount, Decimal('0.30'))
    result = price * (1 - discount)
    return result.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

# Test with exact decimal comparison
def test_decimal_precision():
    price = Decimal('99.99')
    result = calculate_discount_decimal(price, 'premium', 'SAVE20')
    assert result == Decimal('69.99')  # Exact comparison works!''',
                    "recommendation": "For financial calculations, always use Decimal. For other float tests, use pytest.approx."
                }
            }
        ]
    },
    
    # Git workflow assistance
    {
        "context": "Helping with git operations over multiple turns",
        "turns": [
            {
                "instruction": "I accidentally committed sensitive data. The commit is already pushed. How do I fix this?",
                "response": {
                    "action": "multi_step_plan",
                    "warning": "⚠️ IMPORTANT: Once pushed, assume the data is compromised. Rotate any secrets immediately!",
                    "steps": [
                        {
                            "step": 1,
                            "title": "Rotate compromised credentials NOW",
                            "description": "Change passwords, regenerate API keys, rotate secrets. Don't wait."
                        },
                        {
                            "step": 2,
                            "title": "Remove from history with BFG or git filter-repo",
                            "command": "# Install BFG (faster than filter-branch)\nbrew install bfg\n\n# Remove file from all history\nbfg --delete-files secrets.env\n\n# Or replace specific text\necho 'your-api-key-here' > passwords.txt\nbfg --replace-text passwords.txt"
                        },
                        {
                            "step": 3,
                            "title": "Clean up and force push",
                            "command": "git reflog expire --expire=now --all\ngit gc --prune=now --aggressive\ngit push --force --all\ngit push --force --tags"
                        },
                        {
                            "step": 4,
                            "title": "Notify collaborators",
                            "description": "Anyone with a clone needs to re-clone or rebase. Their local copies still have the data."
                        }
                    ],
                    "prevention": "Add to .gitignore: `.env`, `*.pem`, `secrets/`. Use git-secrets or pre-commit hooks to catch this."
                }
            },
            {
                "instruction": "The file is gone now, but I still see it in the GitHub web interface when I look at old commits",
                "response": {
                    "action": "concepts",
                    "explanation": "GitHub caches commit data. Even after force push, old commits may be accessible via direct URL or in pull requests. You need to contact GitHub support to fully purge it.",
                    "steps": [
                        {
                            "step": 1,
                            "title": "Request GitHub cache purge",
                            "description": "Go to https://support.github.com and submit a request to remove cached data. Provide the repository and commit SHAs that need purging."
                        },
                        {
                            "step": 2,
                            "title": "Close and delete any PRs",
                            "description": "Pull requests keep references to old commits. Close and delete any PRs that might reference the sensitive data."
                        },
                        {
                            "step": 3,
                            "title": "Delete and recreate forks",
                            "description": "Forks may also retain the history. Ask fork owners to delete and re-fork."
                        }
                    ],
                    "timeline": "GitHub usually processes purge requests within 24-48 hours."
                }
            },
            {
                "instruction": "How do I prevent this in the future? We have a team and people keep accidentally committing .env files",
                "response": {
                    "action": "multi_step_plan",
                    "title": "Team-wide secret protection strategy",
                    "steps": [
                        {
                            "step": 1,
                            "title": "Global gitignore template",
                            "code": '''# .gitignore - Add to repo root
.env
.env.*
*.pem
*.key
secrets/
credentials.json
**/config/local.json'''
                        },
                        {
                            "step": 2,
                            "title": "Pre-commit hooks with git-secrets",
                            "command": '''# Install git-secrets (run once per machine)
brew install git-secrets  # or: pip install git-secrets

# Set up in repo
cd your-repo
git secrets --install
git secrets --register-aws  # Catches AWS keys

# Add custom patterns
git secrets --add 'password\\s*=\\s*.+'
git secrets --add 'api[_-]?key\\s*=\\s*.+'
git secrets --add 'PRIVATE KEY'

# Add to all new repos automatically
git secrets --install ~/.git-templates/hooks
git config --global init.templateDir ~/.git-templates'''
                        },
                        {
                            "step": 3,
                            "title": "Pre-commit framework (recommended)",
                            "code": '''# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: detect-private-key
      - id: detect-aws-credentials
  
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
  
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.16.1
    hooks:
      - id: gitleaks''',
                            "command": "# Install and set up\npip install pre-commit\npre-commit install\n\n# Run against all files initially\npre-commit run --all-files"
                        },
                        {
                            "step": 4,
                            "title": "CI/CD secret scanning",
                            "code": '''# GitHub Actions workflow
name: Security Scan

on: [push, pull_request]

jobs:
  secrets:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Gitleaks scan
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}'''
                        },
                        {
                            "step": 5,
                            "title": "Use secret management tools",
                            "description": "Replace local .env files with proper secret management: AWS Secrets Manager, HashiCorp Vault, or 1Password for development."
                        }
                    ]
                }
            }
        ]
    },
    
    # Architecture discussion
    {
        "context": "Discussing architecture decisions across turns",
        "turns": [
            {
                "instruction": "Should I use microservices or a monolith for my new project?",
                "response": {
                    "action": "concepts",
                    "answer": "The answer depends on your context. Here's a framework for deciding:",
                    "factors": {
                        "team_size": "Microservices add coordination overhead. Small teams (<5 devs) often move faster with a monolith.",
                        "domain_clarity": "Microservices need clear bounded contexts. If your domain is evolving, a monolith lets you refactor easily.",
                        "scale_requirements": "Different components need different scaling? Microservices help. Uniform load? Monolith is simpler.",
                        "deployment_complexity": "Can your team handle Kubernetes, service mesh, distributed tracing? If not, start simpler."
                    },
                    "recommendation": "For most new projects: Start with a **modular monolith**. Design with clear boundaries internally. Extract services later when you have a proven need.",
                    "questions": [
                        "How large is your team?",
                        "What's your deployment infrastructure?",
                        "Do you have clear, stable domain boundaries?",
                        "What's your timeline?"
                    ]
                }
            },
            {
                "instruction": "Team of 4, we're using AWS, building an e-commerce platform. Timeline is 3 months to MVP",
                "response": {
                    "action": "concepts",
                    "recommendation": "For a 4-person team with 3-month MVP timeline, definitely go with a **modular monolith**. You can always extract services later.",
                    "reasoning": [
                        "4 devs means microservices coordination overhead will slow you down significantly",
                        "3 months is tight - you need to focus on features, not infrastructure",
                        "E-commerce domains are well-understood, so you can design good module boundaries",
                        "AWS makes it easy to scale a monolith initially (larger instances, read replicas)"
                    ],
                    "suggested_architecture": '''**Modular Monolith Structure:**
```
src/
├── modules/
│   ├── catalog/        # Products, categories, inventory
│   │   ├── api/
│   │   ├── domain/
│   │   └── infrastructure/
│   ├── orders/         # Cart, checkout, order management
│   ├── customers/      # Auth, profiles, addresses
│   ├── payments/       # Payment processing
│   └── shipping/       # Shipping calculation, tracking
├── shared/
│   ├── kernel/         # Shared domain primitives
│   └── infrastructure/ # Database, events, etc.
└── api/               # Public REST/GraphQL API
```

Each module:
- Has its own internal layers (API, Domain, Infrastructure)
- Communicates via in-process events or explicit interfaces
- Has clear database schema ownership (can use schema prefixes)
- Can be extracted to a service later with minimal changes''',
                    "next_step": "Want me to show you how to structure one of these modules in detail?"
                }
            },
            {
                "instruction": "Yes, show me the catalog module structure",
                "response": {
                    "action": "provide_code",
                    "language": "python",
                    "description": "Here's a full catalog module structure following clean architecture principles:",
                    "code": '''# src/modules/catalog/
# 
# ├── __init__.py
# ├── api/
# │   ├── __init__.py
# │   ├── routes.py
# │   └── schemas.py
# ├── domain/
# │   ├── __init__.py
# │   ├── entities.py
# │   ├── value_objects.py
# │   ├── events.py
# │   └── services.py
# └── infrastructure/
#     ├── __init__.py
#     ├── repositories.py
#     └── queries.py

# === domain/entities.py ===
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
from datetime import datetime
from shared.kernel import Entity, AggregateRoot

@dataclass
class ProductId:
    value: str

@dataclass  
class Product(AggregateRoot):
    id: ProductId
    name: str
    description: str
    price: Decimal
    category_id: str
    inventory_count: int
    status: str  # 'draft', 'active', 'archived'
    images: List[str]
    created_at: datetime
    updated_at: datetime
    
    def publish(self) -> None:
        if not self.name or not self.price:
            raise ValueError("Product must have name and price to publish")
        self.status = 'active'
        self.add_event(ProductPublished(self.id))
    
    def update_inventory(self, quantity: int) -> None:
        if quantity < 0:
            raise ValueError("Inventory cannot be negative")
        self.inventory_count = quantity
        if quantity == 0:
            self.add_event(ProductOutOfStock(self.id))

# === domain/events.py ===
from dataclasses import dataclass
from shared.kernel import DomainEvent

@dataclass
class ProductPublished(DomainEvent):
    product_id: ProductId

@dataclass
class ProductOutOfStock(DomainEvent):
    product_id: ProductId

# === domain/services.py ===
from typing import Protocol, List

class ProductRepository(Protocol):
    """Port - implemented by infrastructure."""
    async def get(self, id: ProductId) -> Optional[Product]: ...
    async def save(self, product: Product) -> None: ...
    async def search(self, query: str, category: str = None) -> List[Product]: ...

class CatalogService:
    """Application service - orchestrates use cases."""
    
    def __init__(self, products: ProductRepository, events: EventPublisher):
        self.products = products
        self.events = events
    
    async def publish_product(self, product_id: str) -> Product:
        product = await self.products.get(ProductId(product_id))
        if not product:
            raise NotFoundError(f"Product {product_id} not found")
        
        product.publish()
        await self.products.save(product)
        await self.events.publish_all(product.collect_events())
        
        return product

# === api/schemas.py ===
from pydantic import BaseModel
from decimal import Decimal
from typing import List, Optional

class ProductCreate(BaseModel):
    name: str
    description: str
    price: Decimal
    category_id: str
    images: List[str] = []

class ProductResponse(BaseModel):
    id: str
    name: str
    description: str
    price: Decimal
    category_id: str
    inventory_count: int
    status: str
    images: List[str]
    
    class Config:
        from_attributes = True

# === api/routes.py ===
from fastapi import APIRouter, Depends, HTTPException
from .schemas import ProductCreate, ProductResponse
from ..domain.services import CatalogService

router = APIRouter(prefix="/catalog", tags=["catalog"])

@router.post("/products", response_model=ProductResponse, status_code=201)
async def create_product(
    data: ProductCreate,
    service: CatalogService = Depends(get_catalog_service)
):
    product = await service.create_product(data)
    return ProductResponse.from_orm(product)

@router.post("/products/{product_id}/publish")
async def publish_product(
    product_id: str,
    service: CatalogService = Depends(get_catalog_service)
):
    await service.publish_product(product_id)
    return {"status": "published"}''',
                    "explanation": "This structure keeps domain logic pure, uses ports/adapters for infrastructure, and exposes a clean API. Each module follows this pattern, making future extraction straightforward."
                }
            }
        ]
    },
    
    # TypeScript type refinement
    {
        "context": "Iteratively improving TypeScript types",
        "turns": [
            {
                "instruction": "I have this API response type but it feels too loose:\n\n```typescript\ninterface ApiResponse {\n  data: any;\n  error: any;\n  status: number;\n}\n```",
                "response": {
                    "action": "provide_code",
                    "language": "typescript",
                    "code": '''// First improvement: Generic data, typed error
interface ApiResponse<T> {
  data: T | null;
  error: ApiError | null;
  status: number;
}

interface ApiError {
  code: string;
  message: string;
  details?: Record<string, string>;
}

// Usage
const response: ApiResponse<User> = await fetchUser(id);
if (response.error) {
  console.log(response.error.message);
} else {
  console.log(response.data?.name); // Type safe!
}''',
                    "explanation": "Added generic for data type and structured error type. But there's still an issue - data and error shouldn't both be nullable independently."
                }
            },
            {
                "instruction": "Right, if there's an error, data should be null, and vice versa. Can you fix that?",
                "response": {
                    "action": "provide_code",
                    "language": "typescript",
                    "code": '''// Discriminated union - success OR error, never both
type ApiResponse<T> = 
  | { success: true; data: T; status: number }
  | { success: false; error: ApiError; status: number };

interface ApiError {
  code: string;
  message: string;
  details?: Record<string, string>;
}

// Usage - TypeScript now knows the exact shape
function handleResponse<T>(response: ApiResponse<T>) {
  if (response.success) {
    // TypeScript knows: response.data exists, response.error doesn't
    console.log(response.data);
  } else {
    // TypeScript knows: response.error exists, response.data doesn't
    console.log(response.error.message);
  }
}

// Type narrows correctly
const response: ApiResponse<User> = await fetchUser(id);
if (response.success) {
  // response.data is User, not User | null
  const userName = response.data.name;
}''',
                    "explanation": "Using a discriminated union with `success` as the discriminant. TypeScript can now narrow the type correctly."
                }
            },
            {
                "instruction": "Can you also add different error types for different HTTP status codes?",
                "response": {
                    "action": "provide_code",
                    "language": "typescript",
                    "code": '''// Comprehensive API response types with status-specific errors

interface ValidationError {
  type: 'validation';
  code: 'VALIDATION_ERROR';
  message: string;
  fields: Record<string, string[]>;
}

interface NotFoundError {
  type: 'not_found';
  code: 'NOT_FOUND';
  message: string;
  resource: string;
  id: string;
}

interface AuthError {
  type: 'auth';
  code: 'UNAUTHORIZED' | 'FORBIDDEN';
  message: string;
}

interface ServerError {
  type: 'server';
  code: 'INTERNAL_ERROR';
  message: string;
  traceId?: string;
}

type ApiError = ValidationError | NotFoundError | AuthError | ServerError;

// Response type with status codes
type ApiResponse<T> =
  | { success: true; status: 200 | 201; data: T }
  | { success: false; status: 400; error: ValidationError }
  | { success: false; status: 401 | 403; error: AuthError }
  | { success: false; status: 404; error: NotFoundError }
  | { success: false; status: 500; error: ServerError };

// Type-safe error handling
function handleApiError(error: ApiError): void {
  switch (error.type) {
    case 'validation':
      // TypeScript knows: error.fields exists
      Object.entries(error.fields).forEach(([field, messages]) => {
        console.log(`${field}: ${messages.join(', ')}`);
      });
      break;
    
    case 'not_found':
      // TypeScript knows: error.resource and error.id exist
      console.log(`${error.resource} with id ${error.id} not found`);
      break;
    
    case 'auth':
      if (error.code === 'UNAUTHORIZED') {
        redirectToLogin();
      } else {
        showForbiddenMessage();
      }
      break;
    
    case 'server':
      // TypeScript knows: error.traceId might exist
      console.error(`Server error. Trace: ${error.traceId ?? 'unknown'}`);
      break;
  }
}

// Helper to create typed responses
const ApiResponse = {
  success: <T>(data: T, status: 200 | 201 = 200): ApiResponse<T> => ({
    success: true,
    status,
    data
  }),
  
  validationError: (fields: Record<string, string[]>): ApiResponse<never> => ({
    success: false,
    status: 400,
    error: {
      type: 'validation',
      code: 'VALIDATION_ERROR',
      message: 'Validation failed',
      fields
    }
  }),
  
  notFound: (resource: string, id: string): ApiResponse<never> => ({
    success: false,
    status: 404,
    error: {
      type: 'not_found',
      code: 'NOT_FOUND',
      message: `${resource} not found`,
      resource,
      id
    }
  }),
};''',
                    "explanation": "Full discriminated union with status-code-specific error types. Each error type has its own shape, and TypeScript can narrow the type based on `type` or `status`."
                }
            }
        ]
    },
    
    # Performance optimization conversation
    {
        "context": "Diagnosing and fixing performance issues iteratively",
        "turns": [
            {
                "instruction": "My React app is slow when rendering a list of 1000 items. How do I fix it?",
                "response": {
                    "action": "concepts",
                    "diagnosis": "Rendering 1000 items at once is expensive. Common issues:\n1. Re-rendering all items when any state changes\n2. Creating new function/object references on each render\n3. Actually rendering 1000 DOM nodes",
                    "solutions": [
                        "**Virtualization** - Only render visible items (react-window, react-virtualized)",
                        "**Memoization** - Prevent unnecessary re-renders (React.memo, useMemo)",
                        "**Key optimization** - Ensure stable keys"
                    ],
                    "first_step": "Let's start with virtualization - it'll have the biggest impact:\n\n```tsx\nimport { FixedSizeList as List } from 'react-window';\n\nfunction VirtualList({ items }) {\n  const Row = ({ index, style }) => (\n    <div style={style}>{items[index].name}</div>\n  );\n\n  return (\n    <List\n      height={600}\n      width={400}\n      itemCount={items.length}\n      itemSize={50}\n    >\n      {Row}\n    </List>\n  );\n}\n```"
                }
            },
            {
                "instruction": "I added react-window but it's still slow when I type in a search box that filters the list",
                "response": {
                    "action": "concepts",
                    "diagnosis": "The search is triggering re-renders too frequently. Each keystroke filters the list and re-renders. Let's fix that:",
                    "solutions": [
                        "**Debounce** the search input",
                        "**useMemo** the filtered results",
                        "**Memoize** the row component"
                    ],
                    "code": '''import { useState, useMemo, useCallback } from 'react';
import { FixedSizeList as List } from 'react-window';
import { useDebouncedValue } from '@mantine/hooks'; // or write your own

function SearchableList({ items }) {
  const [search, setSearch] = useState('');
  
  // Debounce search - wait 300ms after user stops typing
  const [debouncedSearch] = useDebouncedValue(search, 300);
  
  // Memoize filtered results - only recalculate when items or search changes
  const filteredItems = useMemo(() => {
    if (!debouncedSearch) return items;
    const lower = debouncedSearch.toLowerCase();
    return items.filter(item => 
      item.name.toLowerCase().includes(lower)
    );
  }, [items, debouncedSearch]);
  
  // Memoize row renderer
  const Row = useCallback(({ index, style }) => (
    <div style={style}>
      {filteredItems[index].name}
    </div>
  ), [filteredItems]);
  
  return (
    <div>
      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search..."
      />
      <List
        height={600}
        width={400}
        itemCount={filteredItems.length}
        itemSize={50}
      >
        {Row}
      </List>
    </div>
  );
}''',
                    "explanation": "Debouncing prevents filtering on every keystroke. useMemo prevents recalculating the filtered list unless inputs change."
                }
            },
            {
                "instruction": "Better! But when I click on an item to select it, the whole list still re-renders",
                "response": {
                    "action": "provide_code",
                    "language": "tsx",
                    "code": '''import { useState, useMemo, useCallback, memo } from 'react';
import { FixedSizeList as List, areEqual } from 'react-window';

interface Item {
  id: string;
  name: string;
}

interface RowProps {
  index: number;
  style: React.CSSProperties;
  data: {
    items: Item[];
    selectedId: string | null;
    onSelect: (id: string) => void;
  };
}

// Memoized row component - only re-renders if its props change
const Row = memo(({ index, style, data }: RowProps) => {
  const { items, selectedId, onSelect } = data;
  const item = items[index];
  const isSelected = item.id === selectedId;
  
  return (
    <div 
      style={{
        ...style,
        backgroundColor: isSelected ? '#e0e0ff' : 'white'
      }}
      onClick={() => onSelect(item.id)}
    >
      {item.name}
    </div>
  );
}, areEqual); // Use react-window's areEqual for proper comparison

function SearchableList({ items }: { items: Item[] }) {
  const [search, setSearch] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  
  const [debouncedSearch] = useDebouncedValue(search, 300);
  
  const filteredItems = useMemo(() => {
    if (!debouncedSearch) return items;
    const lower = debouncedSearch.toLowerCase();
    return items.filter(item => 
      item.name.toLowerCase().includes(lower)
    );
  }, [items, debouncedSearch]);
  
  // Stable callback reference
  const handleSelect = useCallback((id: string) => {
    setSelectedId(id);
  }, []);
  
  // Memoize itemData to prevent unnecessary Row re-renders
  const itemData = useMemo(() => ({
    items: filteredItems,
    selectedId,
    onSelect: handleSelect
  }), [filteredItems, selectedId, handleSelect]);
  
  return (
    <div>
      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search..."
      />
      <List
        height={600}
        width={400}
        itemCount={filteredItems.length}
        itemSize={50}
        itemData={itemData}  // Pass data through itemData prop
      >
        {Row}
      </List>
    </div>
  );
}''',
                    "explanation": "Key optimizations:\n1. `Row` is wrapped in `memo` with `areEqual` - only re-renders when its specific props change\n2. `handleSelect` uses `useCallback` for stable reference\n3. `itemData` is memoized - only the selected row gets the `isSelected` change\n4. Using `itemData` pattern keeps Row component pure"
                }
            }
        ]
    },
    
    # Database query optimization
    {
        "context": "Optimizing SQL queries through conversation",
        "turns": [
            {
                "instruction": "This query is slow:\n\n```sql\nSELECT * FROM orders \nWHERE customer_id = 12345 \nAND created_at > '2024-01-01'\nORDER BY created_at DESC\n```",
                "response": {
                    "action": "concepts",
                    "initial_analysis": "A few things could be slow here. Let's diagnose:",
                    "diagnostic_queries": '''-- Check the execution plan
EXPLAIN ANALYZE SELECT * FROM orders 
WHERE customer_id = 12345 
AND created_at > '2024-01-01'
ORDER BY created_at DESC;

-- Check existing indexes
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'orders';

-- Check table size
SELECT pg_size_pretty(pg_total_relation_size('orders'));''',
                    "common_issues": [
                        "Missing index on customer_id",
                        "Missing index on created_at", 
                        "SELECT * fetching unnecessary columns",
                        "No composite index for both conditions"
                    ],
                    "question": "Can you run EXPLAIN ANALYZE and share the output?"
                }
            },
            {
                "instruction": "Here's the output:\n\n```\nSort  (cost=15234.12..15234.56 rows=176 width=524) (actual time=1523.432..1523.445 rows=89 loops=1)\n  Sort Key: created_at DESC\n  Sort Method: quicksort  Memory: 45kB\n  ->  Seq Scan on orders  (cost=0.00..15227.00 rows=176 width=524) (actual time=0.023..1522.123 rows=89 loops=1)\n        Filter: ((customer_id = 12345) AND (created_at > '2024-01-01'))\n        Rows Removed by Filter: 523411\n```",
                "response": {
                    "action": "concepts",
                    "diagnosis": "I see the problem! **Seq Scan** means it's scanning all 523,500 rows. No index is being used.",
                    "key_metrics": {
                        "total_rows_scanned": "523,500 (523,411 removed + 89 returned)",
                        "time": "1.5 seconds",
                        "operation": "Sequential scan (full table scan)"
                    },
                    "solution": "Create a composite index on (customer_id, created_at):",
                    "code": '''-- Create composite index (order matters!)
-- customer_id first because it's the equality condition
-- created_at second for the range condition and sorting
CREATE INDEX CONCURRENTLY idx_orders_customer_created 
ON orders (customer_id, created_at DESC);

-- The DESC matches your ORDER BY, enabling index-only sort''',
                    "expected_improvement": "Should go from 1.5s to <10ms. The index will satisfy both the WHERE and ORDER BY."
                }
            },
            {
                "instruction": "Much better! Now I need to do the same query but for multiple customer IDs:\n\n```sql\nSELECT * FROM orders \nWHERE customer_id IN (12345, 12346, 12347, 12348, 12349)\nAND created_at > '2024-01-01'\nORDER BY created_at DESC\nLIMIT 100\n```",
                "response": {
                    "action": "concepts",
                    "analysis": "The composite index will still help, but there are considerations:",
                    "approaches": {
                        "current_index_works": "Your index (customer_id, created_at DESC) will do 5 index scans and merge results. Usually fine for small IN lists.",
                        "for_many_ids": "If the IN list grows large (100+ IDs), consider using a join with a temp table or VALUES clause."
                    },
                    "optimization": '''-- For larger IN lists, this can be more efficient:
WITH customer_list AS (
  SELECT unnest(ARRAY[12345, 12346, 12347, 12348, 12349]) AS customer_id
)
SELECT o.* 
FROM orders o
JOIN customer_list c ON o.customer_id = c.customer_id
WHERE o.created_at > '2024-01-01'
ORDER BY o.created_at DESC
LIMIT 100;

-- Or if you're filtering by a subquery anyway:
SELECT o.* 
FROM orders o
WHERE o.customer_id IN (
  SELECT id FROM customers WHERE region = 'west'
)
AND o.created_at > '2024-01-01'
ORDER BY o.created_at DESC
LIMIT 100;''',
                    "tip": "With LIMIT 100, the query might not need to sort all results. PostgreSQL can use the index to return already-sorted results and stop early."
                }
            },
            {
                "instruction": "What if I also need to filter by order status? The query keeps getting more complex",
                "response": {
                    "action": "provide_code",
                    "language": "sql",
                    "code": '''-- Analyze your most common query patterns first
-- Let's say you often filter by: customer_id, created_at, status

-- Option 1: Extend the composite index (if status has low cardinality)
CREATE INDEX CONCURRENTLY idx_orders_customer_status_created 
ON orders (customer_id, status, created_at DESC)
WHERE status != 'cancelled';  -- Partial index excludes cancelled orders

-- Option 2: Separate indexes for different query patterns
CREATE INDEX CONCURRENTLY idx_orders_customer_created 
ON orders (customer_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_orders_status_created 
ON orders (status, created_at DESC)
WHERE status IN ('pending', 'processing');  -- Hot statuses only

-- Option 3: Covering index to avoid table lookups entirely
-- Include columns you SELECT to enable index-only scans
CREATE INDEX CONCURRENTLY idx_orders_covering
ON orders (customer_id, created_at DESC)
INCLUDE (status, total_amount, shipping_address_id);

-- Your query can now be:
SELECT customer_id, created_at, status, total_amount 
FROM orders 
WHERE customer_id IN (12345, 12346)
AND created_at > '2024-01-01'
AND status = 'completed'
ORDER BY created_at DESC
LIMIT 100;

-- Check if it's using index-only scan:
EXPLAIN (ANALYZE, BUFFERS) 
SELECT customer_id, created_at, status, total_amount 
FROM orders 
WHERE customer_id = 12345
AND created_at > '2024-01-01';
-- Look for "Index Only Scan" in output''',
                    "guidance": '''**Index Strategy Tips:**
1. Put equality conditions first in composite indexes (customer_id =, status =)
2. Put range conditions last (created_at >)
3. Use partial indexes to exclude irrelevant rows (cancelled, archived)
4. Use covering indexes (INCLUDE) to avoid table lookups
5. Don't over-index - each index slows writes

**Monitor index usage:**
```sql
SELECT indexrelname, idx_scan, idx_tup_read 
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```'''
                }
            }
        ]
    },
    
    # CSS/styling iteration
    {
        "context": "Building styles iteratively",
        "turns": [
            {
                "instruction": "How do I center a div vertically and horizontally?",
                "response": {
                    "action": "provide_code",
                    "language": "css",
                    "code": '''/* Modern approach - Flexbox */
.container {
  display: flex;
  justify-content: center;  /* horizontal */
  align-items: center;      /* vertical */
  min-height: 100vh;        /* full viewport height */
}

/* Alternative - Grid (even simpler) */
.container {
  display: grid;
  place-items: center;
  min-height: 100vh;
}''',
                    "explanation": "Flexbox or Grid are the modern solutions. Both work great."
                }
            },
            {
                "instruction": "Now I want to center multiple cards in a responsive grid",
                "response": {
                    "action": "provide_code",
                    "language": "css",
                    "code": '''/* Responsive card grid */
.card-grid {
  display: grid;
  /* Auto-fit creates as many columns as will fit */
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  padding: 1.5rem;
  max-width: 1200px;
  margin: 0 auto;  /* center the grid itself */
}

.card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}''',
                    "explanation": "`auto-fit` with `minmax()` creates a responsive grid without media queries. Cards are at least 300px wide, and expand to fill available space."
                }
            },
            {
                "instruction": "The cards have different amounts of content and look uneven. Can you fix that?",
                "response": {
                    "action": "provide_code",
                    "language": "css",
                    "code": '''/* Equal height cards with flexbox inside */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  padding: 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
}

.card {
  display: flex;
  flex-direction: column;  /* Stack content vertically */
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  /* Grid automatically makes all cards same height in a row */
}

.card-header {
  /* Fixed height header area */
}

.card-body {
  flex: 1;  /* Takes remaining space - pushes footer down */
}

.card-footer {
  margin-top: auto;  /* Alternative: sticks to bottom */
  padding-top: 1rem;
  border-top: 1px solid #eee;
}''',
                    "html_example": '''<div class="card-grid">
  <article class="card">
    <header class="card-header">
      <h2>Card Title</h2>
    </header>
    <div class="card-body">
      <p>Variable amount of content here...</p>
    </div>
    <footer class="card-footer">
      <button>Action</button>
    </footer>
  </article>
</div>''',
                    "explanation": "Using `flex: 1` on the body makes it expand, pushing the footer to the bottom regardless of content length. Grid already equalizes row heights."
                }
            },
            {
                "instruction": "Perfect. Now I want to add a subtle hover effect on the cards",
                "response": {
                    "action": "provide_code",
                    "language": "css",
                    "code": '''/* Cards with smooth hover effect */
.card {
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  
  /* Smooth transition for hover effects */
  transition: 
    transform 0.2s ease-out,
    box-shadow 0.2s ease-out;
}

.card:hover {
  transform: translateY(-4px);  /* Slight lift */
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.15),
    0 2px 4px rgba(0, 0, 0, 0.1);  /* Deeper shadow */
}

/* Optional: Add subtle border highlight */
.card {
  border: 1px solid transparent;
}

.card:hover {
  border-color: rgba(59, 130, 246, 0.3);  /* Light blue hint */
}

/* For keyboard/focus accessibility */
.card:focus-within {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Reduce motion for users who prefer it */
@media (prefers-reduced-motion: reduce) {
  .card {
    transition: none;
  }
  .card:hover {
    transform: none;
  }
}''',
                    "explanation": "Smooth lift + shadow deepening creates a polished hover effect. Added `prefers-reduced-motion` for accessibility."
                }
            }
        ]
    },
]


def flatten_conversations_to_examples() -> List[Dict]:
    """
    Flatten multi-turn conversations into individual training examples.
    Each turn becomes a separate example, with prior turns as context.
    """
    examples = []
    
    for conversation in MULTITURN_CONVERSATIONS:
        context = conversation.get("context", "")
        turns = conversation["turns"]
        
        # Build conversation history as we go
        history = []
        
        for turn_idx, turn in enumerate(turns):
            instruction = turn["instruction"]
            response = turn["response"]
            
            # For follow-up turns, include conversation history in the instruction
            if history:
                # Format prior turns as context
                history_text = "\n\n---\n\n".join([
                    f"[Previous message]: {h['instruction']}\n\n[My response]: {json.dumps(h['response'], indent=2)}"
                    for h in history[-3:]  # Include last 3 turns max
                ])
                full_instruction = f"[Conversation context: {context}]\n\n{history_text}\n\n---\n\n[Current message]: {instruction}"
            else:
                full_instruction = instruction
            
            examples.append({
                "system": SYSTEM_PROMPT,
                "instruction": full_instruction,
                "response": json.dumps(response, indent=2)
            })
            
            # Add this turn to history
            history.append({
                "instruction": instruction,
                "response": response
            })
    
    return examples


def generate_examples() -> List[Dict]:
    """Generate all multi-turn conversation training examples."""
    return flatten_conversations_to_examples()


def save_examples(examples: List[Dict], filename: str = "multiturn_conversations.jsonl"):
    """Save examples to JSONL file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"Generated {len(examples)} multi-turn examples -> {output_path}")
    return examples


if __name__ == "__main__":
    examples = generate_examples()
    save_examples(examples)
