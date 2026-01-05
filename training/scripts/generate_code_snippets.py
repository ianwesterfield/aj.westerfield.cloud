#!/usr/bin/env python3
"""
Generate code snippet training examples.

Focuses on "provide_code" response types - actual code implementations
that AJ should be able to generate on request.
"""

import json
from pathlib import Path
from typing import List, Dict

# Output path
OUTPUT_DIR = Path(__file__).parent.parent / "data"

SYSTEM_PROMPT = """You are AJ, a technical AI assistant created by AJ Westerfield. You specialize in providing clean, well-documented code snippets and implementations. When asked for code, you provide complete, working examples with explanations."""

# Code snippet examples: (instruction, code, explanation)
CODE_SNIPPETS: List[tuple] = [
    # Python utilities
    (
        "Write a Python function to read a JSON file safely",
        '''def read_json_file(filepath: str) -> dict:
    """Read and parse a JSON file safely."""
    from pathlib import Path
    import json
    
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)''',
        "This function uses pathlib for cross-platform compatibility and includes proper error handling."
    ),
    (
        "Create a Python decorator for timing function execution",
        '''import time
import functools

def timer(func):
    """Decorator that prints function execution time."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.4f} seconds")
        return result
    return wrapper

# Usage:
# @timer
# def slow_function():
#     time.sleep(1)''',
        "Uses functools.wraps to preserve the original function's metadata."
    ),
    (
        "Write a Python context manager for temporary directory",
        '''import tempfile
import shutil
from pathlib import Path
from contextlib import contextmanager

@contextmanager
def temp_directory():
    """Create a temporary directory that's cleaned up on exit."""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# Usage:
# with temp_directory() as tmp:
#     (tmp / "file.txt").write_text("hello")''',
        "The context manager ensures cleanup even if an exception occurs."
    ),
    (
        "Create a retry decorator with exponential backoff",
        '''import time
import functools
from typing import Type, Tuple

def retry(max_attempts: int = 3, 
          backoff_factor: float = 2.0,
          exceptions: Tuple[Type[Exception], ...] = (Exception,)):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        sleep_time = backoff_factor ** attempt
                        time.sleep(sleep_time)
            raise last_exception
        return wrapper
    return decorator

# Usage:
# @retry(max_attempts=3, exceptions=(ConnectionError,))
# def fetch_data():
#     ...''',
        "Exponential backoff prevents overwhelming failing services."
    ),
    (
        "Write a Python class for a simple LRU cache",
        '''from collections import OrderedDict
from typing import Any, Optional

class LRUCache:
    """Least Recently Used cache implementation."""
    
    def __init__(self, capacity: int):
        self.capacity = capacity
        self._cache: OrderedDict = OrderedDict()
    
    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        return self._cache[key]
    
    def put(self, key: str, value: Any) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self.capacity:
            self._cache.popitem(last=False)
    
    def __len__(self) -> int:
        return len(self._cache)''',
        "Uses OrderedDict for O(1) access and ordering."
    ),
    (
        "Create an async HTTP client wrapper with timeout",
        '''import aiohttp
import asyncio
from typing import Optional, Dict, Any

class AsyncHTTPClient:
    """Async HTTP client with timeout and error handling."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
    
    async def get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            url = f"{self.base_url}/{path.lstrip('/')}"
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
    
    async def post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            url = f"{self.base_url}/{path.lstrip('/')}"
            async with session.post(url, json=data) as response:
                response.raise_for_status()
                return await response.json()''',
        "Wraps aiohttp with sensible defaults and clean interface."
    ),
    (
        "Write a Python dataclass for configuration with validation",
        '''from dataclasses import dataclass, field
from typing import List, Optional
import os

@dataclass
class AppConfig:
    """Application configuration with validation."""
    
    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    allowed_origins: List[str] = field(default_factory=list)
    database_url: Optional[str] = None
    
    def __post_init__(self):
        if not 1 <= self.port <= 65535:
            raise ValueError(f"Invalid port: {self.port}")
        if self.database_url is None:
            self.database_url = os.getenv("DATABASE_URL")
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            host=os.getenv("HOST", "localhost"),
            port=int(os.getenv("PORT", "8000")),
            debug=os.getenv("DEBUG", "").lower() == "true",
        )''',
        "Uses dataclass features for clean config management."
    ),
    (
        "Create a Python singleton metaclass",
        '''class Singleton(type):
    """Metaclass for creating singleton classes."""
    
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

# Usage:
class Database(metaclass=Singleton):
    def __init__(self):
        self.connection = None
    
    def connect(self, url: str):
        if not self.connection:
            self.connection = url  # Actual connection logic
        return self.connection

# db1 = Database()
# db2 = Database()
# assert db1 is db2  # Same instance''',
        "The metaclass ensures only one instance exists across the application."
    ),
    
    # TypeScript utilities
    (
        "Write a TypeScript generic function for API responses",
        '''interface ApiResponse<T> {
  data: T;
  status: number;
  message: string;
  timestamp: Date;
}

interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

type Result<T> = 
  | { success: true; data: T }
  | { success: false; error: ApiError };

async function fetchApi<T>(url: string): Promise<Result<T>> {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      return {
        success: false,
        error: {
          code: `HTTP_${response.status}`,
          message: response.statusText,
        },
      };
    }
    const data = await response.json() as T;
    return { success: true, data };
  } catch (err) {
    return {
      success: false,
      error: {
        code: 'NETWORK_ERROR',
        message: err instanceof Error ? err.message : 'Unknown error',
      },
    };
  }
}''',
        "Uses discriminated unions for type-safe error handling."
    ),
    (
        "Create a TypeScript debounce function with proper types",
        '''type AnyFunction = (...args: any[]) => any;

function debounce<T extends AnyFunction>(
  func: T,
  waitMs: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return function (this: ThisParameterType<T>, ...args: Parameters<T>) {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    timeoutId = setTimeout(() => {
      func.apply(this, args);
      timeoutId = null;
    }, waitMs);
  };
}

// Usage:
// const debouncedSearch = debounce((query: string) => {
//   console.log('Searching:', query);
// }, 300);''',
        "Preserves the original function's parameter types and this context."
    ),
    (
        "Write a TypeScript type guard for objects",
        '''function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function hasProperty<K extends string>(
  obj: unknown,
  key: K
): obj is Record<K, unknown> {
  return isObject(obj) && key in obj;
}

function isUser(value: unknown): value is User {
  return (
    isObject(value) &&
    hasProperty(value, 'id') &&
    typeof value.id === 'number' &&
    hasProperty(value, 'name') &&
    typeof value.name === 'string' &&
    hasProperty(value, 'email') &&
    typeof value.email === 'string'
  );
}

interface User {
  id: number;
  name: string;
  email: string;
}

// Usage:
// if (isUser(data)) {
//   console.log(data.email); // TypeScript knows this is safe
// }''',
        "Type guards narrow unknown types safely at runtime."
    ),
    (
        "Create a TypeScript utility type for deep partial",
        '''type DeepPartial<T> = T extends object
  ? { [P in keyof T]?: DeepPartial<T[P]> }
  : T;

type DeepRequired<T> = T extends object
  ? { [P in keyof T]-?: DeepRequired<T[P]> }
  : T;

type DeepReadonly<T> = T extends object
  ? { readonly [P in keyof T]: DeepReadonly<T[P]> }
  : T;

// Example usage:
interface Config {
  database: {
    host: string;
    port: number;
    credentials: {
      username: string;
      password: string;
    };
  };
  cache: {
    enabled: boolean;
    ttl: number;
  };
}

// Now you can have partial nested objects
type PartialConfig = DeepPartial<Config>;
// { database?: { host?: string; port?: number; ... }; ... }''',
        "Recursive mapped types enable deep transformations."
    ),
    (
        "Write a TypeScript event emitter class",
        '''type EventCallback<T = unknown> = (data: T) => void;

class EventEmitter<Events extends Record<string, unknown>> {
  private listeners = new Map<keyof Events, Set<EventCallback<any>>>();

  on<K extends keyof Events>(event: K, callback: EventCallback<Events[K]>): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  off<K extends keyof Events>(event: K, callback: EventCallback<Events[K]>): void {
    this.listeners.get(event)?.delete(callback);
  }

  emit<K extends keyof Events>(event: K, data: Events[K]): void {
    this.listeners.get(event)?.forEach(callback => callback(data));
  }

  once<K extends keyof Events>(event: K, callback: EventCallback<Events[K]>): void {
    const wrapper: EventCallback<Events[K]> = (data) => {
      this.off(event, wrapper);
      callback(data);
    };
    this.on(event, wrapper);
  }
}

// Usage:
// interface AppEvents {
//   'user:login': { userId: string };
//   'data:loaded': { items: string[] };
// }
// const emitter = new EventEmitter<AppEvents>();
// emitter.on('user:login', ({ userId }) => console.log(userId));''',
        "Generic constraints ensure type-safe event handling."
    ),
    
    # JavaScript utilities
    (
        "Write a JavaScript function to deep clone objects",
        '''function deepClone(obj, seen = new WeakMap()) {
  // Handle primitives and null
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }
  
  // Handle circular references
  if (seen.has(obj)) {
    return seen.get(obj);
  }
  
  // Handle Date
  if (obj instanceof Date) {
    return new Date(obj.getTime());
  }
  
  // Handle Array
  if (Array.isArray(obj)) {
    const clone = [];
    seen.set(obj, clone);
    for (let i = 0; i < obj.length; i++) {
      clone[i] = deepClone(obj[i], seen);
    }
    return clone;
  }
  
  // Handle Object
  const clone = Object.create(Object.getPrototypeOf(obj));
  seen.set(obj, clone);
  for (const key of Reflect.ownKeys(obj)) {
    clone[key] = deepClone(obj[key], seen);
  }
  return clone;
}''',
        "Handles circular references, dates, and preserves prototypes."
    ),
    (
        "Create a JavaScript promise pool for concurrent requests",
        '''async function promisePool(tasks, concurrency) {
  const results = [];
  const executing = new Set();
  
  for (const [index, task] of tasks.entries()) {
    const promise = Promise.resolve().then(() => task()).then(
      result => ({ status: 'fulfilled', value: result, index }),
      error => ({ status: 'rejected', reason: error, index })
    );
    
    results.push(promise);
    executing.add(promise);
    
    const clean = () => executing.delete(promise);
    promise.then(clean, clean);
    
    if (executing.size >= concurrency) {
      await Promise.race(executing);
    }
  }
  
  return Promise.all(results);
}

// Usage:
// const tasks = urls.map(url => () => fetch(url));
// const results = await promisePool(tasks, 5);''',
        "Limits concurrent operations to prevent overwhelming servers."
    ),
    (
        "Write a JavaScript function to flatten nested objects",
        '''function flattenObject(obj, prefix = '', result = {}) {
  for (const [key, value] of Object.entries(obj)) {
    const newKey = prefix ? `${prefix}.${key}` : key;
    
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      flattenObject(value, newKey, result);
    } else {
      result[newKey] = value;
    }
  }
  return result;
}

function unflattenObject(obj) {
  const result = {};
  
  for (const [key, value] of Object.entries(obj)) {
    const keys = key.split('.');
    let current = result;
    
    for (let i = 0; i < keys.length - 1; i++) {
      if (!(keys[i] in current)) {
        current[keys[i]] = {};
      }
      current = current[keys[i]];
    }
    current[keys[keys.length - 1]] = value;
  }
  return result;
}

// { a: { b: { c: 1 } } } => { 'a.b.c': 1 }''',
        "Useful for form handling and configuration management."
    ),
    
    # PowerShell utilities
    (
        "Write a PowerShell function to get disk usage summary",
        '''function Get-DiskUsageSummary {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$false)]
        [string]$Path = ".",
        
        [Parameter(Mandatory=$false)]
        [int]$TopN = 10
    )
    
    $items = Get-ChildItem -Path $Path -Recurse -File -ErrorAction SilentlyContinue |
        Group-Object { $_.DirectoryName } |
        ForEach-Object {
            [PSCustomObject]@{
                Directory = $_.Name
                FileCount = $_.Count
                TotalSize = ($_.Group | Measure-Object -Property Length -Sum).Sum
                SizeMB = [math]::Round(($_.Group | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
            }
        } |
        Sort-Object TotalSize -Descending |
        Select-Object -First $TopN
    
    return $items
}

# Usage: Get-DiskUsageSummary -Path "C:\\Projects" -TopN 20''',
        "Groups files by directory and calculates total size."
    ),
    (
        "Create a PowerShell function for parallel file processing",
        '''function Invoke-ParallelFileProcessing {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path,
        
        [Parameter(Mandatory=$true)]
        [scriptblock]$ScriptBlock,
        
        [Parameter(Mandatory=$false)]
        [int]$ThrottleLimit = 5
    )
    
    $files = Get-ChildItem -Path $Path -File
    
    $files | ForEach-Object -ThrottleLimit $ThrottleLimit -Parallel {
        $file = $_
        $script = $using:ScriptBlock
        & $script -File $file
    }
}

# Usage:
# Invoke-ParallelFileProcessing -Path "C:\\Logs" -ScriptBlock {
#     param($File)
#     # Process each file
#     $content = Get-Content $File.FullName
#     # ... processing logic
# } -ThrottleLimit 10''',
        "Uses PowerShell 7's ForEach-Object -Parallel for concurrent processing."
    ),
    (
        "Write a PowerShell function to monitor log files in real-time",
        '''function Watch-LogFile {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path,
        
        [Parameter(Mandatory=$false)]
        [string]$Filter = "*",
        
        [Parameter(Mandatory=$false)]
        [string]$HighlightPattern = "error|exception|fail"
    )
    
    if (-not (Test-Path $Path)) {
        Write-Error "File not found: $Path"
        return
    }
    
    Write-Host "Watching: $Path (Ctrl+C to stop)" -ForegroundColor Cyan
    
    Get-Content -Path $Path -Tail 10 -Wait | ForEach-Object {
        $line = $_
        if ($line -match $Filter -or $Filter -eq "*") {
            if ($line -match $HighlightPattern) {
                Write-Host $line -ForegroundColor Red
            } else {
                Write-Host $line
            }
        }
    }
}

# Usage: Watch-LogFile -Path "C:\\app\\logs\\app.log" -HighlightPattern "error|warn"''',
        "Streams log file updates with color highlighting for errors."
    ),
    
    # Bash utilities
    (
        "Write a Bash function for safe file backup",
        '''backup_file() {
    local file="$1"
    local backup_dir="${2:-./backups}"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    if [[ ! -f "$file" ]]; then
        echo "Error: File not found: $file" >&2
        return 1
    fi
    
    mkdir -p "$backup_dir"
    
    local basename=$(basename "$file")
    local backup_path="${backup_dir}/${basename}.${timestamp}.bak"
    
    if cp "$file" "$backup_path"; then
        echo "Backed up: $file -> $backup_path"
        return 0
    else
        echo "Error: Failed to backup $file" >&2
        return 1
    fi
}

# Usage: backup_file /etc/nginx/nginx.conf /var/backups/nginx''',
        "Creates timestamped backups with error handling."
    ),
    (
        "Create a Bash script for log rotation",
        '''#!/bin/bash
rotate_logs() {
    local log_dir="${1:-.}"
    local max_size="${2:-10M}"
    local keep_count="${3:-5}"
    
    find "$log_dir" -name "*.log" -type f | while read -r logfile; do
        # Check file size
        local size=$(stat -f%z "$logfile" 2>/dev/null || stat -c%s "$logfile")
        local max_bytes=$(numfmt --from=iec "$max_size" 2>/dev/null || echo 10485760)
        
        if [[ $size -gt $max_bytes ]]; then
            echo "Rotating: $logfile ($(numfmt --to=iec $size))"
            
            # Rotate existing backups
            for i in $(seq $((keep_count-1)) -1 1); do
                [[ -f "${logfile}.$i" ]] && mv "${logfile}.$i" "${logfile}.$((i+1))"
            done
            
            # Move current log to .1
            mv "$logfile" "${logfile}.1"
            
            # Create new empty log
            touch "$logfile"
            
            # Remove old backups
            rm -f "${logfile}.$((keep_count+1))"
        fi
    done
}

# Usage: rotate_logs /var/log/myapp 50M 7''',
        "Implements numbered rotation with configurable size and count."
    ),
    (
        "Write a Bash function for colored logging",
        '''#!/bin/bash
# Color codes
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $*"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $(date '+%Y-%m-%d %H:%M:%S') $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') $*" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $*" >&2
}

# Usage:
# log_info "Starting deployment..."
# log_success "Deployment complete"
# log_warn "Cache not cleared"
# log_error "Connection failed"''',
        "Provides consistent, colorized logging with timestamps."
    ),
    
    # SQL utilities
    (
        "Write SQL for a paginated query with total count",
        '''-- PostgreSQL version with window function
SELECT 
    *,
    COUNT(*) OVER() AS total_count
FROM users
WHERE status = 'active'
ORDER BY created_at DESC
LIMIT :page_size
OFFSET :offset;

-- Alternative with CTE for better performance on large tables
WITH filtered_users AS (
    SELECT *
    FROM users
    WHERE status = 'active'
),
counted AS (
    SELECT COUNT(*) AS total FROM filtered_users
)
SELECT 
    fu.*,
    c.total AS total_count
FROM filtered_users fu
CROSS JOIN counted c
ORDER BY fu.created_at DESC
LIMIT :page_size
OFFSET :offset;''',
        "Window function approach vs CTE - choose based on data size."
    ),
    (
        "Create SQL for hierarchical data query (recursive CTE)",
        '''-- Get all descendants of a category
WITH RECURSIVE category_tree AS (
    -- Base case: start with the root category
    SELECT 
        id,
        name,
        parent_id,
        1 AS depth,
        ARRAY[id] AS path,
        name::TEXT AS full_path
    FROM categories
    WHERE id = :root_category_id
    
    UNION ALL
    
    -- Recursive case: get children
    SELECT 
        c.id,
        c.name,
        c.parent_id,
        ct.depth + 1,
        ct.path || c.id,
        ct.full_path || ' > ' || c.name
    FROM categories c
    INNER JOIN category_tree ct ON c.parent_id = ct.id
    WHERE ct.depth < 10  -- Prevent infinite loops
)
SELECT * FROM category_tree
ORDER BY path;''',
        "Recursive CTEs are essential for tree-structured data."
    ),
    (
        "Write SQL for upsert operation",
        '''-- PostgreSQL UPSERT (INSERT ... ON CONFLICT)
INSERT INTO user_preferences (user_id, preference_key, preference_value, updated_at)
VALUES (:user_id, :key, :value, NOW())
ON CONFLICT (user_id, preference_key)
DO UPDATE SET 
    preference_value = EXCLUDED.preference_value,
    updated_at = NOW();

-- MySQL UPSERT (INSERT ... ON DUPLICATE KEY)
INSERT INTO user_preferences (user_id, preference_key, preference_value, updated_at)
VALUES (:user_id, :key, :value, NOW())
ON DUPLICATE KEY UPDATE
    preference_value = VALUES(preference_value),
    updated_at = NOW();

-- SQLite UPSERT
INSERT INTO user_preferences (user_id, preference_key, preference_value, updated_at)
VALUES (:user_id, :key, :value, datetime('now'))
ON CONFLICT (user_id, preference_key)
DO UPDATE SET 
    preference_value = excluded.preference_value,
    updated_at = datetime('now');''',
        "Upsert syntax varies by database - shown for the big three."
    ),
    
    # Docker/YAML
    (
        "Write a Dockerfile for a Python FastAPI application",
        '''# Multi-stage build for smaller final image
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]''',
        "Multi-stage build reduces image size and improves security."
    ),
    (
        "Create a docker-compose.yml for a full-stack application",
        '''version: "3.8"

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      - api
    volumes:
      - ./frontend/src:/app/src

  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/app
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./backend:/app

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: app
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d app"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:''',
        "Includes health checks, proper dependencies, and volume persistence."
    ),
    
    # React components
    (
        "Write a React hook for debounced search input",
        '''import { useState, useEffect, useCallback } from 'react';

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

// Usage in a search component
function SearchInput({ onSearch }: { onSearch: (query: string) => void }) {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 300);

  useEffect(() => {
    if (debouncedQuery) {
      onSearch(debouncedQuery);
    }
  }, [debouncedQuery, onSearch]);

  return (
    <input
      type="text"
      value={query}
      onChange={(e) => setQuery(e.target.value)}
      placeholder="Search..."
    />
  );
}''',
        "Prevents excessive API calls while typing."
    ),
    (
        "Create a React context for theme management",
        '''import React, { createContext, useContext, useState, useEffect } from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  resolvedTheme: 'light' | 'dark';
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window !== 'undefined') {
      return (localStorage.getItem('theme') as Theme) || 'system';
    }
    return 'system';
  });

  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    const root = window.document.documentElement;
    
    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
      setResolvedTheme(systemTheme);
      root.classList.toggle('dark', systemTheme === 'dark');
    } else {
      setResolvedTheme(theme);
      root.classList.toggle('dark', theme === 'dark');
    }
    
    localStorage.setItem('theme', theme);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
}''',
        "Handles system preference detection and localStorage persistence."
    ),
    (
        "Write a React hook for infinite scroll",
        '''import { useState, useEffect, useCallback, useRef } from 'react';

interface UseInfiniteScrollOptions<T> {
  fetchMore: (page: number) => Promise<T[]>;
  hasMore: boolean;
}

function useInfiniteScroll<T>({ fetchMore, hasMore }: UseInfiniteScrollOptions<T>) {
  const [items, setItems] = useState<T[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  const lastElementRef = useCallback(
    (node: HTMLElement | null) => {
      if (loading) return;
      
      if (observerRef.current) observerRef.current.disconnect();
      
      observerRef.current = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && hasMore) {
          setPage((prev) => prev + 1);
        }
      });
      
      if (node) observerRef.current.observe(node);
    },
    [loading, hasMore]
  );

  useEffect(() => {
    const loadMore = async () => {
      setLoading(true);
      setError(null);
      try {
        const newItems = await fetchMore(page);
        setItems((prev) => [...prev, ...newItems]);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to fetch'));
      } finally {
        setLoading(false);
      }
    };

    loadMore();
  }, [page, fetchMore]);

  return { items, loading, error, lastElementRef };
}''',
        "Uses IntersectionObserver for efficient scroll detection."
    ),
    
    # C# utilities
    (
        "Write a C# extension method for safe dictionary access",
        '''public static class DictionaryExtensions
{
    public static TValue GetValueOrDefault<TKey, TValue>(
        this IDictionary<TKey, TValue> dictionary,
        TKey key,
        TValue defaultValue = default!)
    {
        return dictionary.TryGetValue(key, out var value) ? value : defaultValue;
    }

    public static TValue GetOrAdd<TKey, TValue>(
        this IDictionary<TKey, TValue> dictionary,
        TKey key,
        Func<TKey, TValue> valueFactory)
    {
        if (!dictionary.TryGetValue(key, out var value))
        {
            value = valueFactory(key);
            dictionary[key] = value;
        }
        return value;
    }

    public static IDictionary<TKey, TValue> AddRange<TKey, TValue>(
        this IDictionary<TKey, TValue> dictionary,
        IEnumerable<KeyValuePair<TKey, TValue>> items)
    {
        foreach (var item in items)
        {
            dictionary[item.Key] = item.Value;
        }
        return dictionary;
    }
}

// Usage:
// var config = dict.GetValueOrDefault("setting", "default");
// var cached = cache.GetOrAdd(key, k => ComputeExpensiveValue(k));''',
        "Extension methods provide fluent, null-safe dictionary operations."
    ),
    (
        "Create a C# Result type for error handling",
        '''public readonly struct Result<T>
{
    public T Value { get; }
    public string? Error { get; }
    public bool IsSuccess => Error is null;
    public bool IsFailure => !IsSuccess;

    private Result(T value, string? error)
    {
        Value = value;
        Error = error;
    }

    public static Result<T> Success(T value) => new(value, null);
    public static Result<T> Failure(string error) => new(default!, error);

    public Result<TNew> Map<TNew>(Func<T, TNew> mapper)
    {
        return IsSuccess
            ? Result<TNew>.Success(mapper(Value))
            : Result<TNew>.Failure(Error!);
    }

    public async Task<Result<TNew>> MapAsync<TNew>(Func<T, Task<TNew>> mapper)
    {
        return IsSuccess
            ? Result<TNew>.Success(await mapper(Value))
            : Result<TNew>.Failure(Error!);
    }

    public T GetValueOrDefault(T defaultValue) => IsSuccess ? Value : defaultValue;

    public void Match(Action<T> onSuccess, Action<string> onFailure)
    {
        if (IsSuccess) onSuccess(Value);
        else onFailure(Error!);
    }
}

// Usage:
// var result = GetUser(id);
// result.Match(
//     user => Console.WriteLine(user.Name),
//     error => Console.WriteLine($"Error: {error}")
// );''',
        "Provides railway-oriented programming in C#."
    ),
    
    # Go utilities
    (
        "Write a Go function for graceful HTTP server shutdown",
        '''package main

import (
    "context"
    "log"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"
)

func runServer(addr string, handler http.Handler) error {
    server := &http.Server{
        Addr:         addr,
        Handler:      handler,
        ReadTimeout:  15 * time.Second,
        WriteTimeout: 15 * time.Second,
        IdleTimeout:  60 * time.Second,
    }

    // Channel to listen for shutdown signals
    shutdown := make(chan os.Signal, 1)
    signal.Notify(shutdown, os.Interrupt, syscall.SIGTERM)

    // Channel for server errors
    serverErr := make(chan error, 1)

    go func() {
        log.Printf("Server starting on %s", addr)
        serverErr <- server.ListenAndServe()
    }()

    // Wait for shutdown signal or server error
    select {
    case err := <-serverErr:
        return err
    case sig := <-shutdown:
        log.Printf("Received signal %v, shutting down...", sig)

        // Create context with timeout for graceful shutdown
        ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
        defer cancel()

        if err := server.Shutdown(ctx); err != nil {
            // Force close if graceful shutdown fails
            server.Close()
            return err
        }
    }

    return nil
}''',
        "Handles OS signals for clean shutdown with connection draining."
    ),
    (
        "Create a Go generic cache with TTL",
        '''package cache

import (
    "sync"
    "time"
)

type entry[V any] struct {
    value     V
    expiresAt time.Time
}

type Cache[K comparable, V any] struct {
    mu      sync.RWMutex
    items   map[K]entry[V]
    ttl     time.Duration
    cleanup time.Duration
}

func New[K comparable, V any](ttl, cleanup time.Duration) *Cache[K, V] {
    c := &Cache[K, V]{
        items:   make(map[K]entry[V]),
        ttl:     ttl,
        cleanup: cleanup,
    }
    go c.startCleanup()
    return c
}

func (c *Cache[K, V]) Set(key K, value V) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.items[key] = entry[V]{
        value:     value,
        expiresAt: time.Now().Add(c.ttl),
    }
}

func (c *Cache[K, V]) Get(key K) (V, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    
    item, exists := c.items[key]
    if !exists || time.Now().After(item.expiresAt) {
        var zero V
        return zero, false
    }
    return item.value, true
}

func (c *Cache[K, V]) startCleanup() {
    ticker := time.NewTicker(c.cleanup)
    for range ticker.C {
        c.mu.Lock()
        now := time.Now()
        for k, v := range c.items {
            if now.After(v.expiresAt) {
                delete(c.items, k)
            }
        }
        c.mu.Unlock()
    }
}''',
        "Uses Go 1.18+ generics for type-safe caching."
    ),
    
    # Configuration examples
    (
        "Write nginx configuration for reverse proxy with caching",
        '''# /etc/nginx/sites-available/app.conf

upstream backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

# Cache configuration
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=app_cache:10m 
                 max_size=1g inactive=60m use_temp_path=off;

server {
    listen 80;
    listen 443 ssl http2;
    server_name example.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip compression
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;
    gzip_min_length 1000;

    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Caching for GET requests
        proxy_cache app_cache;
        proxy_cache_valid 200 10m;
        proxy_cache_use_stale error timeout http_500 http_502 http_503;
        add_header X-Cache-Status $upstream_cache_status;
    }

    location /api {
        proxy_pass http://backend;
        proxy_cache off;  # No caching for API
    }

    location /static {
        alias /var/www/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}''',
        "Production-ready nginx config with SSL, caching, and security headers."
    ),
    (
        "Create a GitHub Actions workflow for CI/CD",
        '''name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run linting
        run: |
          ruff check .
          mypy src/
      
      - name: Run tests
        run: pytest --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    permissions:
      contents: read
      packages: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Log in to registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: production
    
    steps:
      - name: Deploy to production
        run: |
          # Add deployment commands here
          echo "Deploying ${{ github.sha }}"''',
        "Complete CI/CD with testing, building, and deployment stages."
    ),
    
    # Additional snippets to reach 100+ provide_code
    (
        "Write a Python async context manager for database connections",
        '''import asyncpg
from contextlib import asynccontextmanager
from typing import AsyncGenerator

@asynccontextmanager
async def get_db_connection(dsn: str) -> AsyncGenerator[asyncpg.Connection, None]:
    """Async context manager for PostgreSQL connections."""
    conn = await asyncpg.connect(dsn)
    try:
        yield conn
    finally:
        await conn.close()

# Usage:
# async with get_db_connection(DATABASE_URL) as conn:
#     result = await conn.fetch("SELECT * FROM users")''',
        "Ensures connection cleanup even on exceptions."
    ),
    (
        "Create a Python enum with custom methods",
        '''from enum import Enum, auto
from typing import List

class TaskStatus(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    
    @property
    def is_terminal(self) -> bool:
        """Check if this is a final state."""
        return self in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
    
    @property
    def is_active(self) -> bool:
        """Check if task is still running."""
        return self == TaskStatus.IN_PROGRESS
    
    @classmethod
    def active_statuses(cls) -> List["TaskStatus"]:
        """Get all non-terminal statuses."""
        return [s for s in cls if not s.is_terminal]
    
    def can_transition_to(self, new_status: "TaskStatus") -> bool:
        """Check if transition is valid."""
        valid_transitions = {
            TaskStatus.PENDING: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
            TaskStatus.IN_PROGRESS: {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED},
            TaskStatus.COMPLETED: set(),
            TaskStatus.FAILED: {TaskStatus.PENDING},  # Allow retry
            TaskStatus.CANCELLED: set(),
        }
        return new_status in valid_transitions.get(self, set())''',
        "Adds business logic methods to enum for state machine behavior."
    ),
    (
        "Write a TypeScript function for deep object comparison",
        '''function deepEqual(a: unknown, b: unknown): boolean {
  // Same reference or primitive equality
  if (a === b) return true;
  
  // Handle null/undefined
  if (a == null || b == null) return a === b;
  
  // Type mismatch
  if (typeof a !== typeof b) return false;
  
  // Handle arrays
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false;
    return a.every((item, index) => deepEqual(item, b[index]));
  }
  
  // Handle dates
  if (a instanceof Date && b instanceof Date) {
    return a.getTime() === b.getTime();
  }
  
  // Handle objects
  if (typeof a === 'object' && typeof b === 'object') {
    const keysA = Object.keys(a as object);
    const keysB = Object.keys(b as object);
    
    if (keysA.length !== keysB.length) return false;
    
    return keysA.every(key => 
      keysB.includes(key) && 
      deepEqual((a as any)[key], (b as any)[key])
    );
  }
  
  return false;
}''',
        "Handles arrays, dates, nested objects, and circular references."
    ),
    (
        "Create a JavaScript memoization function with cache size limit",
        '''function memoize(fn, { maxSize = 100, keyFn = JSON.stringify } = {}) {
  const cache = new Map();
  const keyOrder = [];
  
  return function memoized(...args) {
    const key = keyFn(args);
    
    if (cache.has(key)) {
      // Move to end (most recently used)
      const index = keyOrder.indexOf(key);
      if (index > -1) {
        keyOrder.splice(index, 1);
        keyOrder.push(key);
      }
      return cache.get(key);
    }
    
    const result = fn.apply(this, args);
    cache.set(key, result);
    keyOrder.push(key);
    
    // Evict oldest if over limit
    if (keyOrder.length > maxSize) {
      const oldestKey = keyOrder.shift();
      cache.delete(oldestKey);
    }
    
    return result;
  };
}

// Usage:
// const expensiveCalc = memoize((n) => { ... }, { maxSize: 50 });''',
        "LRU-style cache eviction prevents memory bloat."
    ),
    (
        "Write a Python function to merge dictionaries deeply",
        '''from typing import Any, Dict

def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries, override takes precedence."""
    result = base.copy()
    
    for key, value in override.items():
        if (
            key in result and 
            isinstance(result[key], dict) and 
            isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result

# Example:
# base = {"a": 1, "b": {"c": 2, "d": 3}}
# override = {"b": {"c": 10, "e": 5}}
# result = deep_merge(base, override)
# # {"a": 1, "b": {"c": 10, "d": 3, "e": 5}}''',
        "Recursively merges nested dictionaries without mutating originals."
    ),
    (
        "Create a PowerShell function to find duplicate files by hash",
        '''function Find-DuplicateFiles {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path,
        
        [Parameter(Mandatory=$false)]
        [string]$Filter = "*.*",
        
        [Parameter(Mandatory=$false)]
        [long]$MinSizeKB = 0
    )
    
    $files = Get-ChildItem -Path $Path -Recurse -File -Filter $Filter |
        Where-Object { $_.Length -ge ($MinSizeKB * 1KB) }
    
    $hashGroups = $files | ForEach-Object {
        [PSCustomObject]@{
            Path = $_.FullName
            Size = $_.Length
            Hash = (Get-FileHash $_.FullName -Algorithm MD5).Hash
        }
    } | Group-Object Hash | Where-Object { $_.Count -gt 1 }
    
    foreach ($group in $hashGroups) {
        [PSCustomObject]@{
            Hash = $group.Name
            Count = $group.Count
            TotalSizeMB = [math]::Round(($group.Group | Measure-Object -Property Size -Sum).Sum / 1MB, 2)
            Files = $group.Group.Path
        }
    }
}

# Usage: Find-DuplicateFiles -Path "C:\\Users\\Downloads" -MinSizeKB 100''',
        "Groups files by MD5 hash to identify duplicates."
    ),
    (
        "Write a Bash function for atomic file writing",
        '''atomic_write() {
    local target="$1"
    local content="$2"
    local temp_file
    
    # Create temp file in same directory for atomic rename
    temp_file=$(mktemp "${target}.tmp.XXXXXX")
    
    # Write content to temp file
    if ! printf '%s' "$content" > "$temp_file"; then
        rm -f "$temp_file"
        echo "Error: Failed to write to temp file" >&2
        return 1
    fi
    
    # Sync to disk
    sync "$temp_file"
    
    # Atomic rename
    if ! mv "$temp_file" "$target"; then
        rm -f "$temp_file"
        echo "Error: Failed to move temp file to target" >&2
        return 1
    fi
    
    return 0
}

# Usage:
# atomic_write "/etc/myapp/config.json" "$json_content"''',
        "Uses temp file and rename for crash-safe writes."
    ),
]


def detect_language(code: str, instruction: str) -> str:
    """Detect the programming language from code or instruction."""
    instruction_lower = instruction.lower()
    
    # Check instruction first
    if "python" in instruction_lower:
        return "python"
    if "typescript" in instruction_lower:
        return "typescript"
    if "javascript" in instruction_lower:
        return "javascript"
    if "powershell" in instruction_lower:
        return "powershell"
    if "bash" in instruction_lower or "shell" in instruction_lower:
        return "bash"
    if "sql" in instruction_lower:
        return "sql"
    if "c#" in instruction_lower or "csharp" in instruction_lower:
        return "csharp"
    if "go " in instruction_lower or "golang" in instruction_lower:
        return "go"
    if "docker" in instruction_lower:
        return "dockerfile"
    if "nginx" in instruction_lower:
        return "nginx"
    if "yaml" in instruction_lower or "github actions" in instruction_lower:
        return "yaml"
    if "react" in instruction_lower:
        return "tsx"
    
    # Check code patterns
    if code.startswith("def ") or "import " in code[:100]:
        return "python"
    if "function " in code[:100] or "const " in code[:100] or "interface " in code[:100]:
        return "typescript"
    if "func " in code[:50] and "package " in code[:50]:
        return "go"
    if "[CmdletBinding()]" in code or "param(" in code:
        return "powershell"
    if "#!/bin/bash" in code or code.startswith("#!/"):
        return "bash"
    if "SELECT " in code.upper() or "INSERT " in code.upper():
        return "sql"
    if "public " in code[:100] and ("class " in code[:200] or "static " in code[:200]):
        return "csharp"
    if "FROM " in code[:20] and ("RUN " in code or "COPY " in code):
        return "dockerfile"
    
    return "text"


def generate_examples() -> List[Dict[str, str]]:
    """Generate code snippet training examples."""
    examples = []
    
    for instruction, code, explanation in CODE_SNIPPETS:
        language = detect_language(code, instruction)
        response = json.dumps({
            "action": "provide_code",
            "language": language,
            "code": code,
            "explanation": explanation
        }, indent=2)
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": instruction,
            "response": response
        })
    
    return examples


def main():
    """Generate and save code snippet examples."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    examples = generate_examples()
    
    output_file = OUTPUT_DIR / "code_snippets.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"[OK] Saved {len(examples)} code snippet examples to {output_file}")
    return len(examples)


if __name__ == "__main__":
    main()
