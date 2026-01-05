#!/usr/bin/env python3
"""
Memory & Performance Training Data Generator
Generates training examples for memory management, profiling, optimization, and performance tuning.
"""

import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

SYSTEM_PROMPT = """You are AJ, an AI assistant for developers. You help with memory management, performance profiling, optimization, resource monitoring, and debugging memory-related issues. Respond in JSON format for actionable requests or plain text for conceptual questions."""

# ============================================================================
# MEMORY MONITORING TASKS
# ============================================================================

LINUX_MEMORY_TASKS = {
    "check memory usage": {
        "tool": "terminal",
        "command": "free -h",
        "explanation": "Display memory usage in human-readable format"
    },
    "show detailed memory statistics": {
        "tool": "terminal",
        "command": "cat /proc/meminfo",
        "explanation": "Display detailed memory information from kernel"
    },
    "find processes using the most memory": {
        "tool": "terminal",
        "command": "ps aux --sort=-%mem | head -20",
        "explanation": "List top 20 processes by memory usage"
    },
    "monitor memory in real-time with htop": {
        "tool": "terminal",
        "command": "htop --sort-key PERCENT_MEM",
        "explanation": "Interactive process viewer sorted by memory"
    },
    "show memory usage per process with detailed breakdown": {
        "tool": "terminal",
        "command": "smem -tk -s pss",
        "explanation": "Show proportional set size (PSS) per process"
    },
    "check for memory leaks with valgrind": {
        "tool": "terminal",
        "command": "valgrind --leak-check=full --show-leak-kinds=all ./program",
        "explanation": "Run program with memory leak detection"
    },
    "view memory mapping of a process": {
        "tool": "terminal",
        "command": "pmap -x $(pgrep process_name)",
        "explanation": "Display memory map of a running process"
    },
    "check swap usage": {
        "tool": "terminal",
        "command": "swapon --show && cat /proc/swaps",
        "explanation": "Display swap devices and their usage"
    },
    "view OOM killer logs": {
        "tool": "terminal",
        "command": "dmesg | grep -i 'out of memory\\|oom'",
        "explanation": "Check if OOM killer has terminated any processes"
    },
    "check huge pages allocation": {
        "tool": "terminal",
        "command": "grep -i huge /proc/meminfo",
        "explanation": "Display huge pages memory information"
    },
    "monitor cache and buffer usage": {
        "tool": "terminal",
        "command": "vmstat 1 5",
        "explanation": "Show virtual memory statistics over 5 seconds"
    },
    "clear system caches": {
        "tool": "terminal",
        "command": "sync; echo 3 | sudo tee /proc/sys/vm/drop_caches",
        "explanation": "Drop page cache, dentries and inodes (for testing)"
    },
    "analyze memory fragmentation": {
        "tool": "terminal",
        "command": "cat /proc/buddyinfo",
        "explanation": "Show memory fragmentation information"
    },
    "check NUMA memory allocation": {
        "tool": "terminal",
        "command": "numastat -m",
        "explanation": "Display NUMA memory statistics per node"
    }
}

WINDOWS_MEMORY_TASKS = {
    "check memory usage": {
        "tool": "terminal",
        "command": "Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 20 Name, @{N='MemoryMB';E={[math]::Round($_.WorkingSet64/1MB,2)}}, CPU",
        "explanation": "List top 20 processes by memory usage"
    },
    "view system memory info": {
        "tool": "terminal",
        "command": "Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory, TotalVirtualMemorySize, FreeVirtualMemory",
        "explanation": "Display system memory statistics"
    },
    "check page file usage": {
        "tool": "terminal",
        "command": "Get-CimInstance Win32_PageFileUsage | Select-Object Name, CurrentUsage, PeakUsage, AllocatedBaseSize",
        "explanation": "Show page file usage statistics"
    },
    "monitor memory performance counters": {
        "tool": "terminal",
        "command": "Get-Counter '\\Memory\\Available MBytes', '\\Memory\\% Committed Bytes In Use', '\\Memory\\Pages/sec' -SampleInterval 1 -MaxSamples 5",
        "explanation": "Monitor memory performance metrics"
    },
    "view process memory details": {
        "tool": "terminal",
        "command": "Get-Process -Name 'process_name' | Select-Object Name, WorkingSet64, PrivateMemorySize64, VirtualMemorySize64, HandleCount",
        "explanation": "Get detailed memory info for specific process"
    },
    "check for memory leaks using handles": {
        "tool": "terminal",
        "command": "Get-Process | Where-Object {$_.HandleCount -gt 1000} | Sort-Object HandleCount -Descending | Select-Object Name, HandleCount, WorkingSet64",
        "explanation": "Find processes with high handle counts (potential leaks)"
    },
    "analyze memory with RAMMap": {
        "tool": "terminal",
        "command": "Start-Process 'https://docs.microsoft.com/sysinternals/downloads/rammap'",
        "explanation": "Download RAMMap for detailed Windows memory analysis"
    },
    "check standby list size": {
        "tool": "terminal",
        "command": "Get-Counter '\\Memory\\Standby Cache Normal Priority Bytes', '\\Memory\\Standby Cache Reserve Bytes'",
        "explanation": "View standby cache memory distribution"
    }
}

# ============================================================================
# PERFORMANCE PROFILING TASKS
# ============================================================================

PROFILING_TASKS = {
    "profile Python code with cProfile": {
        "tool": "terminal",
        "command": "python -m cProfile -s cumulative script.py > profile.txt",
        "explanation": "Profile Python script and sort by cumulative time"
    },
    "generate Python flamegraph with py-spy": {
        "tool": "terminal",
        "command": "py-spy record -o flamegraph.svg -- python script.py",
        "explanation": "Create interactive flamegraph of Python execution"
    },
    "profile running Python process": {
        "tool": "terminal",
        "command": "py-spy top --pid $(pgrep -f python)",
        "explanation": "Live top-like view of Python process"
    },
    "memory profile Python script": {
        "tool": "terminal",
        "command": "python -m memory_profiler script.py",
        "explanation": "Profile memory usage line-by-line"
    },
    "profile Node.js with 0x": {
        "tool": "terminal",
        "command": "npx 0x app.js",
        "explanation": "Generate flamegraph for Node.js application"
    },
    "Node.js heap snapshot": {
        "tool": "terminal",
        "command": "node --inspect app.js",
        "explanation": "Start Node with inspector for heap snapshots"
    },
    "profile .NET application": {
        "tool": "terminal",
        "command": "dotnet trace collect --process-id PID --providers Microsoft-DotNETCore-SampleProfiler",
        "explanation": "Collect CPU sampling trace for .NET app"
    },
    "Linux perf CPU profiling": {
        "tool": "terminal",
        "command": "sudo perf record -g -p $(pgrep process_name) -- sleep 30; sudo perf report",
        "explanation": "Record 30 seconds of CPU samples with call graphs"
    },
    "generate flamegraph from perf": {
        "tool": "terminal",
        "command": "sudo perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg",
        "explanation": "Create flamegraph from perf data"
    },
    "trace system calls": {
        "tool": "terminal",
        "command": "strace -c -p $(pgrep process_name)",
        "explanation": "Count system calls by type for a process"
    },
    "profile I/O latency with BPF": {
        "tool": "terminal",
        "command": "sudo biolatency -m",
        "explanation": "Show block I/O latency distribution using BPF"
    },
    "cache miss analysis with perf": {
        "tool": "terminal",
        "command": "sudo perf stat -e cache-misses,cache-references,instructions,cycles ./program",
        "explanation": "Analyze cache performance of a program"
    }
}

# ============================================================================
# OPTIMIZATION CODE EXAMPLES
# ============================================================================

CODE_EXAMPLES = {
    "Python memory-efficient generator": {
        "tool": "create_file",
        "language": "python",
        "code": '''"""Memory-efficient data processing with generators."""

def read_large_file(file_path: str):
    """Read large file line by line without loading into memory."""
    with open(file_path, 'r') as f:
        for line in f:
            yield line.strip()


def process_in_chunks(data: list, chunk_size: int = 1000):
    """Process data in chunks to limit memory usage."""
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]


def memory_efficient_csv_processing(file_path: str):
    """Process CSV without loading entire file."""
    import csv
    
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Process one row at a time
            yield process_row(row)


def process_row(row: dict) -> dict:
    """Transform a single row."""
    return {k: v.strip().lower() for k, v in row.items()}


# Using __slots__ to reduce memory per object
class OptimizedDataClass:
    """Class using __slots__ for memory efficiency."""
    __slots__ = ['id', 'name', 'value']
    
    def __init__(self, id: int, name: str, value: float):
        self.id = id
        self.name = name
        self.value = value


# Example usage
if __name__ == "__main__":
    # Instead of: lines = open('huge.txt').readlines()  # Loads all into memory
    # Use: 
    for line in read_large_file('huge.txt'):
        process(line)  # One line at a time
''',
        "explanation": "Generators and __slots__ for memory-efficient Python"
    },
    "Python object pool pattern": {
        "tool": "create_file",
        "language": "python",
        "code": '''"""Object pooling to reduce allocation overhead."""
from typing import Generic, TypeVar, List
from threading import Lock

T = TypeVar('T')


class ObjectPool(Generic[T]):
    """Thread-safe object pool to reuse expensive objects."""
    
    def __init__(self, factory, max_size: int = 100):
        self._factory = factory
        self._pool: List[T] = []
        self._max_size = max_size
        self._lock = Lock()
    
    def acquire(self) -> T:
        """Get object from pool or create new one."""
        with self._lock:
            if self._pool:
                return self._pool.pop()
        return self._factory()
    
    def release(self, obj: T) -> None:
        """Return object to pool for reuse."""
        with self._lock:
            if len(self._pool) < self._max_size:
                self._pool.append(obj)


# Example: Pool expensive database connections
class DatabaseConnection:
    def __init__(self):
        # Expensive initialization
        print("Creating new connection...")
    
    def reset(self):
        # Reset state for reuse
        pass


# Usage
conn_pool = ObjectPool(DatabaseConnection, max_size=10)

# Get connection
conn = conn_pool.acquire()
try:
    # Use connection
    pass
finally:
    conn.reset()
    conn_pool.release(conn)  # Return to pool
''',
        "explanation": "Object pooling pattern for reusing expensive objects"
    },
    "TypeScript memory-conscious patterns": {
        "tool": "create_file",
        "language": "typescript",
        "code": '''/**
 * Memory-efficient TypeScript patterns
 */

// Use TypedArrays for numeric data
function processNumericData(data: number[]): Float64Array {
  // TypedArrays are more memory efficient and faster
  const buffer = new Float64Array(data.length);
  for (let i = 0; i < data.length; i++) {
    buffer[i] = data[i] * 2;
  }
  return buffer;
}

// WeakMap for caching without preventing garbage collection
const cache = new WeakMap<object, any>();

function expensiveComputation(obj: object): any {
  if (cache.has(obj)) {
    return cache.get(obj);
  }
  
  const result = /* expensive work */ {};
  cache.set(obj, result);
  return result;
}

// Stream processing with async generators
async function* processLargeDataset(
  source: AsyncIterable<string>
): AsyncGenerator<ProcessedItem> {
  for await (const chunk of source) {
    yield processChunk(chunk);
  }
}

interface ProcessedItem {
  id: string;
  data: any;
}

function processChunk(chunk: string): ProcessedItem {
  return { id: chunk.slice(0, 10), data: JSON.parse(chunk) };
}

// Object pooling for frequently allocated objects
class Vector3Pool {
  private static pool: Vector3[] = [];
  
  static acquire(x = 0, y = 0, z = 0): Vector3 {
    const v = this.pool.pop() || new Vector3();
    v.set(x, y, z);
    return v;
  }
  
  static release(v: Vector3): void {
    this.pool.push(v);
  }
}

class Vector3 {
  x = 0; y = 0; z = 0;
  set(x: number, y: number, z: number) {
    this.x = x; this.y = y; this.z = z;
    return this;
  }
}
''',
        "explanation": "Memory-efficient TypeScript patterns including TypedArrays and object pooling"
    },
    "C# memory optimization": {
        "tool": "create_file",
        "language": "csharp",
        "code": '''using System;
using System.Buffers;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

/// <summary>
/// Memory-efficient patterns in C#
/// </summary>
public static class MemoryPatterns
{
    // Use Span<T> to avoid heap allocations
    public static int SumWithSpan(ReadOnlySpan<int> numbers)
    {
        int sum = 0;
        foreach (var n in numbers)
            sum += n;
        return sum;
    }

    // ArrayPool for reusable buffers
    public static void ProcessWithPooledBuffer(Stream input)
    {
        // Rent buffer from pool instead of allocating
        byte[] buffer = ArrayPool<byte>.Shared.Rent(4096);
        try
        {
            int bytesRead;
            while ((bytesRead = input.Read(buffer, 0, buffer.Length)) > 0)
            {
                // Process buffer[0..bytesRead]
            }
        }
        finally
        {
            ArrayPool<byte>.Shared.Return(buffer);
        }
    }

    // Struct instead of class for value semantics
    [StructLayout(LayoutKind.Sequential)]
    public readonly struct Point3D
    {
        public readonly float X, Y, Z;
        
        public Point3D(float x, float y, float z)
        {
            X = x; Y = y; Z = z;
        }
        
        // Avoid boxing with specific overloads
        public bool Equals(Point3D other) => 
            X == other.X && Y == other.Y && Z == other.Z;
    }

    // RecordStruct for immutable data (C# 10+)
    public readonly record struct Transaction(
        long Id,
        decimal Amount,
        DateTime Timestamp
    );

    // stackalloc for small temporary buffers
    public static unsafe void ProcessSmallData()
    {
        Span<int> buffer = stackalloc int[128];
        // Use buffer - allocated on stack, no GC pressure
    }
}

// Object pool for expensive objects
public class ConnectionPool<T> where T : class, new()
{
    private readonly System.Collections.Concurrent.ConcurrentBag<T> _pool = new();
    private readonly int _maxSize;

    public ConnectionPool(int maxSize = 100) => _maxSize = maxSize;

    public T Rent() => _pool.TryTake(out var item) ? item : new T();

    public void Return(T item)
    {
        if (_pool.Count < _maxSize)
            _pool.Add(item);
    }
}
''',
        "explanation": "C# memory patterns: Span<T>, ArrayPool, stackalloc, and structs"
    },
    "Python memory profiling decorator": {
        "tool": "create_file",
        "language": "python",
        "code": '''"""Memory profiling utilities for Python."""
import functools
import tracemalloc
import gc
from typing import Callable, TypeVar
import psutil
import os

T = TypeVar('T')


def memory_profile(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to profile memory usage of a function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        gc.collect()
        tracemalloc.start()
        
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024
        
        result = func(*args, **kwargs)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        mem_after = process.memory_info().rss / 1024 / 1024
        
        print(f"Function: {func.__name__}")
        print(f"  Memory before: {mem_before:.2f} MB")
        print(f"  Memory after:  {mem_after:.2f} MB")
        print(f"  Memory delta:  {mem_after - mem_before:.2f} MB")
        print(f"  Peak traced:   {peak / 1024 / 1024:.2f} MB")
        
        return result
    return wrapper


def track_memory_leaks(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to detect potential memory leaks."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        gc.collect()
        tracemalloc.start()
        
        # Take snapshot before
        snapshot1 = tracemalloc.take_snapshot()
        
        result = func(*args, **kwargs)
        
        gc.collect()  # Force collection
        
        # Take snapshot after
        snapshot2 = tracemalloc.take_snapshot()
        
        # Compare snapshots
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        print(f"\\nMemory changes in {func.__name__}:")
        print("Top 10 memory allocations:")
        for stat in top_stats[:10]:
            print(f"  {stat}")
        
        tracemalloc.stop()
        return result
    return wrapper


# Usage example
@memory_profile
def process_large_data():
    data = [i ** 2 for i in range(1_000_000)]
    return sum(data)


if __name__ == "__main__":
    result = process_large_data()
''',
        "explanation": "Decorators for profiling memory usage and detecting leaks"
    }
}

# ============================================================================
# PLANNING TASKS
# ============================================================================

PLANNING_TASKS = [
    {
        "instruction": "Help me diagnose and fix a memory leak in my Python web application",
        "response": {
            "action": "multi_step_plan",
            "plan": [
                {"step": 1, "action": "Monitor baseline memory", "command": "watch -n 1 'ps aux | grep python'", "checkpoint": "Note starting memory"},
                {"step": 2, "action": "Enable memory tracking", "command": "Add tracemalloc.start() at app startup", "checkpoint": "Tracking enabled"},
                {"step": 3, "action": "Reproduce the leak", "note": "Generate load that triggers leak (run requests in loop)"},
                {"step": 4, "action": "Take memory snapshots", "command": "tracemalloc.take_snapshot() before/after", "checkpoint": "Snapshots captured"},
                {"step": 5, "action": "Analyze top allocators", "command": "snapshot.compare_to().statistics('traceback')", "checkpoint": "Top allocators identified"},
                {"step": 6, "action": "Use objgraph for reference cycles", "command": "pip install objgraph; objgraph.show_growth()", "checkpoint": "Growth patterns visible"},
                {"step": 7, "action": "Profile with memory_profiler", "command": "@profile decorator on suspected functions", "checkpoint": "Line-by-line analysis"},
                {"step": 8, "action": "Check for common leak patterns", "checklist": ["Unclosed connections", "Growing caches", "Event handlers not removed", "Circular references"]},
                {"step": 9, "action": "Implement fix", "common_fixes": ["Add context managers", "Use weakref for caches", "Clear timers/handlers", "Break circular refs"]},
                {"step": 10, "action": "Verify fix under load", "command": "Load test and monitor memory stabilization", "checkpoint": "Memory stable"}
            ],
            "notes": "Common leak sources: SQLAlchemy sessions, global caches, event listeners, threads holding references"
        }
    },
    {
        "instruction": "My application is using too much memory, help me optimize it",
        "response": {
            "action": "multi_step_plan",
            "plan": [
                {"step": 1, "action": "Profile current memory usage", "command": "py-spy dump --pid PID or memory_profiler", "checkpoint": "Baseline established"},
                {"step": 2, "action": "Identify memory hotspots", "command": "tracemalloc snapshot analysis", "checkpoint": "Top allocators found"},
                {"step": 3, "action": "Analyze data structures", "check": "Are lists/dicts larger than needed? Consider generators"},
                {"step": 4, "action": "Replace large lists with generators", "example": "Change [x for x in items] to (x for x in items)", "checkpoint": "Generators implemented"},
                {"step": 5, "action": "Use __slots__ for classes", "example": "Add __slots__ = ['attr1', 'attr2'] to data classes", "checkpoint": "Slots added"},
                {"step": 6, "action": "Implement object pooling", "example": "Pool frequently created/destroyed objects", "checkpoint": "Pooling active"},
                {"step": 7, "action": "Use memory-mapped files for large data", "command": "mmap or numpy memmap for large arrays", "checkpoint": "mmap in place"},
                {"step": 8, "action": "Consider more efficient data types", "examples": ["numpy arrays vs lists", "array module", "struct for binary"], "checkpoint": "Types optimized"},
                {"step": 9, "action": "Add cache limits", "example": "@functools.lru_cache(maxsize=1000)", "checkpoint": "Caches bounded"},
                {"step": 10, "action": "Measure improvement", "command": "Before/after memory comparison under load", "checkpoint": "Improvement quantified"}
            ],
            "quick_wins": ["Use generators for large iterations", "Add __slots__ to data classes", "Bound all caches", "Use streaming for file I/O"]
        }
    },
    {
        "instruction": "Set up comprehensive performance monitoring for a production system",
        "response": {
            "action": "multi_step_plan",
            "plan": [
                {"step": 1, "action": "Install monitoring stack", "command": "docker-compose up -d prometheus grafana", "checkpoint": "Stack running"},
                {"step": 2, "action": "Deploy node_exporter on hosts", "command": "Install node_exporter for system metrics", "checkpoint": "System metrics exposed"},
                {"step": 3, "action": "Configure application metrics", "options": ["Prometheus client library", "StatsD", "OpenTelemetry"], "checkpoint": "App metrics exported"},
                {"step": 4, "action": "Set up key dashboards", "metrics": ["CPU/Memory/Disk", "Request rate/latency", "Error rates", "GC pauses"], "checkpoint": "Dashboards created"},
                {"step": 5, "action": "Configure alerting rules", "alerts": ["High memory usage >80%", "OOM killer activity", "High latency p99", "Error rate spike"], "checkpoint": "Alerts configured"},
                {"step": 6, "action": "Set up distributed tracing", "tool": "Jaeger or Zipkin with OpenTelemetry", "checkpoint": "Tracing active"},
                {"step": 7, "action": "Add profiling endpoint", "example": "/debug/pprof for Go or py-spy for Python", "checkpoint": "Profiling available"},
                {"step": 8, "action": "Configure log aggregation", "tool": "Loki/ELK for correlating metrics with logs", "checkpoint": "Logs aggregated"},
                {"step": 9, "action": "Create runbooks", "include": ["High memory investigation", "Latency spike diagnosis", "OOM recovery"], "checkpoint": "Runbooks documented"},
                {"step": 10, "action": "Schedule regular review", "cadence": "Weekly performance review of dashboards", "checkpoint": "Process established"}
            ],
            "recommended_metrics": {
                "USE_method": "Utilization, Saturation, Errors for each resource",
                "RED_method": "Rate, Errors, Duration for services",
                "four_golden_signals": "Latency, Traffic, Errors, Saturation"
            }
        }
    },
    {
        "instruction": "My database queries are slow, help me optimize the performance",
        "response": {
            "action": "multi_step_plan",
            "plan": [
                {"step": 1, "action": "Enable slow query logging", "postgres": "log_min_duration_statement = 500", "mysql": "slow_query_log = ON", "checkpoint": "Slow queries logged"},
                {"step": 2, "action": "Identify slowest queries", "command": "pg_stat_statements or MySQL slow log analysis", "checkpoint": "Top queries found"},
                {"step": 3, "action": "Analyze query execution plan", "command": "EXPLAIN (ANALYZE, BUFFERS) SELECT ...", "checkpoint": "Plans analyzed"},
                {"step": 4, "action": "Check for missing indexes", "look_for": "Sequential scans on large tables", "checkpoint": "Index candidates identified"},
                {"step": 5, "action": "Add appropriate indexes", "command": "CREATE INDEX CONCURRENTLY idx_name ON table(column)", "checkpoint": "Indexes created"},
                {"step": 6, "action": "Optimize query structure", "techniques": ["Remove SELECT *", "Add WHERE clauses", "Use JOINs efficiently"], "checkpoint": "Queries rewritten"},
                {"step": 7, "action": "Check connection pooling", "ensure": "Using PgBouncer, HikariCP, or similar", "checkpoint": "Pooling configured"},
                {"step": 8, "action": "Tune database parameters", "postgres_key": "shared_buffers, work_mem, effective_cache_size", "checkpoint": "Parameters tuned"},
                {"step": 9, "action": "Consider caching layer", "options": ["Redis for frequent queries", "Materialized views", "Application-level cache"], "checkpoint": "Caching implemented"},
                {"step": 10, "action": "Monitor and iterate", "command": "Compare query times before/after", "checkpoint": "Improvement verified"}
            ],
            "index_tips": [
                "Index columns used in WHERE, JOIN, ORDER BY",
                "Consider composite indexes for multi-column filters",
                "Partial indexes for commonly filtered subsets",
                "Don't over-index - hurts write performance"
            ]
        }
    }
]

# ============================================================================
# CONCEPT Q&A
# ============================================================================

CONCEPT_QA = [
    {
        "instruction": "Explain the difference between stack and heap memory",
        "response": """**Stack vs Heap Memory:**

**Stack Memory:**
- **Allocation:** Automatic (LIFO - Last In First Out)
- **Speed:** Very fast (just move stack pointer)
- **Size:** Limited (typically 1-8 MB per thread)
- **Lifetime:** Automatically freed when function returns
- **What goes here:** Local variables, function parameters, return addresses
- **Thread safety:** Each thread has its own stack

```c
void function() {
    int x = 10;      // Stack allocation
    char buffer[100]; // Stack allocation
    // Automatically freed when function returns
}
```

**Heap Memory:**
- **Allocation:** Manual (malloc/new) or GC-managed
- **Speed:** Slower (memory manager overhead)
- **Size:** Large (limited by available RAM)
- **Lifetime:** Until explicitly freed or garbage collected
- **What goes here:** Dynamic data, objects, large allocations
- **Thread safety:** Shared between threads (needs synchronization)

```c
void function() {
    int* ptr = malloc(sizeof(int));  // Heap allocation
    *ptr = 10;
    // Must call free(ptr) or memory leaks!
}
```

**Key Differences:**
| Aspect | Stack | Heap |
|--------|-------|------|
| Speed | ⚡ Fast | 🐢 Slower |
| Size | Fixed/Small | Large/Flexible |
| Management | Automatic | Manual/GC |
| Fragmentation | None | Possible |
| Access | Sequential | Random |

**Best Practice:** Use stack for small, short-lived data; heap for large/dynamic data."""
    },
    {
        "instruction": "What is garbage collection and how does it work?",
        "response": """**Garbage Collection (GC)** automatically frees memory that's no longer reachable by the program.

**How GC Works:**

**1. Reference Counting (Python, Swift):**
- Each object tracks how many references point to it
- When count reaches 0, object is freed
- **Problem:** Circular references can leak

```python
a = []
b = []
a.append(b)  # b refs: 2
b.append(a)  # a refs: 2
del a, b     # Both still ref count 1 - LEAK!
```

**2. Mark and Sweep (JavaScript, Go, Java):**
- **Mark:** Start from "roots" (globals, stack), mark all reachable objects
- **Sweep:** Free all unmarked objects
- Handles circular references
- Causes "stop the world" pauses

**3. Generational GC (Java, .NET, Python):**
- Objects divided into generations (young, old)
- Young gen collected frequently (most objects die young)
- Old gen collected less often
- Reduces pause times

**GC Generations:**
```
Gen 0: New objects (collected most frequently)
Gen 1: Survived one collection
Gen 2: Long-lived objects (collected rarely)
```

**4. Concurrent/Incremental GC:**
- Runs alongside application
- Minimizes pauses (G1, ZGC, Shenandoah)

**GC Trade-offs:**

| Algorithm | Throughput | Latency | Memory |
|-----------|------------|---------|--------|
| Serial | High | High pauses | Low |
| Parallel | Higher | Medium | Medium |
| G1 | Good | Low | Medium |
| ZGC | Good | <1ms | Higher |

**GC Tuning Tips:**
- Reduce allocation rate (object pooling)
- Avoid creating garbage in hot paths
- Size generations appropriately
- Monitor GC logs for issues"""
    },
    {
        "instruction": "What causes memory leaks and how can I prevent them?",
        "response": """**Memory Leaks** occur when allocated memory is no longer needed but not released.

**Common Causes by Language:**

**All Languages:**
1. **Forgotten references** - Objects stored but never removed
2. **Event listeners** - Handlers not unregistered
3. **Caches without limits** - Unbounded growth
4. **Closures capturing variables** - Holding references longer than needed

**Python:**
```python
# LEAK: Growing list never cleared
cache = []
def process(item):
    cache.append(item)  # Never removed!

# FIX: Use bounded cache
from functools import lru_cache
@lru_cache(maxsize=1000)
def process(item): ...
```

**JavaScript:**
```javascript
// LEAK: Event listener not removed
element.addEventListener('click', handler);
// When element is removed, handler still holds reference

// FIX: Remove listener
element.removeEventListener('click', handler);
// Or use AbortController for fetch
```

**C/C++:**
```c
// LEAK: malloc without free
void process() {
    char* buffer = malloc(1024);
    // Missing: free(buffer);
}

// FIX: RAII in C++
std::unique_ptr<char[]> buffer(new char[1024]);
// Automatically freed when scope exits
```

**Prevention Strategies:**

1. **Use weak references** for caches
2. **Bound all caches** with max size
3. **Unsubscribe from events** on cleanup
4. **Use context managers** (with statements)
5. **Profile regularly** with memory tools
6. **Code review** for resource cleanup

**Detection Tools:**
- Python: tracemalloc, objgraph, memory_profiler
- JavaScript: Chrome DevTools Memory tab
- Java: VisualVM, Eclipse MAT
- C/C++: Valgrind, AddressSanitizer

**Red Flags:**
- Memory growing over time under steady load
- Objects accumulating in heap dumps
- High GC frequency with little freed"""
    },
    {
        "instruction": "Explain CPU cache and why it matters for performance",
        "response": """**CPU Cache** is small, fast memory between CPU and RAM that stores frequently accessed data.

**Cache Hierarchy:**
```
CPU Core
  └── L1 Cache (32-64 KB) - ~4 cycles, per core
       └── L2 Cache (256 KB-1 MB) - ~10 cycles, per core
            └── L3 Cache (8-64 MB) - ~40 cycles, shared
                 └── RAM - ~100+ cycles
```

**Cache Line:**
- CPU loads data in blocks (typically 64 bytes)
- Even accessing 1 byte loads entire cache line
- Adjacent data gets loaded "for free"

**Why Performance Matters:**

**Memory Access Pattern Impact:**
```c
// GOOD: Sequential access - cache friendly
for (int i = 0; i < N; i++)
    sum += array[i];  // Predictable, prefetchable

// BAD: Random access - cache hostile  
for (int i = 0; i < N; i++)
    sum += array[random_indices[i]];  // Cache misses
```

**Array of Structs vs Struct of Arrays:**
```c
// AoS - Bad if only accessing x,y (loads unused data)
struct Point { float x, y, z; } points[1000];

// SoA - Good if accessing x,y together
struct Points {
    float x[1000];
    float y[1000];
    float z[1000];
} points;
```

**Cache-Friendly Patterns:**

1. **Sequential access** - Iterate arrays linearly
2. **Spatial locality** - Keep related data together
3. **Temporal locality** - Reuse data while it's hot
4. **Avoid false sharing** - Pad data accessed by different threads
5. **Keep hot data small** - Fit working set in cache

**False Sharing Example:**
```c
// BAD: Two threads writing adjacent data
struct { int counter1; int counter2; } shared;
// Both on same cache line - thrashing!

// GOOD: Pad to separate cache lines
struct { int counter1; char pad[60]; int counter2; } shared;
```

**Measuring Cache Performance:**
```bash
perf stat -e cache-misses,cache-references ./program
```

**Impact:** Cache-optimized code can be 10-100x faster!"""
    },
    {
        "instruction": "What is memory fragmentation and how do I handle it?",
        "response": """**Memory Fragmentation** occurs when free memory is broken into small, non-contiguous blocks.

**Types of Fragmentation:**

**1. External Fragmentation:**
- Free memory exists but is scattered
- Can't allocate large contiguous blocks
- Common with malloc/free patterns

```
Memory: [USED][FREE][USED][FREE][USED][FREE]
                    ^
Total free: 30KB, but largest block: 10KB
Can't allocate 15KB even though 30KB is free!
```

**2. Internal Fragmentation:**
- Allocated blocks larger than needed
- Waste inside allocated regions
- Common with fixed-size allocators

```
Requested: 65 bytes
Allocated: 128 bytes (next power of 2)
Wasted: 63 bytes
```

**Causes:**
- Variable-size allocations
- Frequent alloc/free cycles
- Long-running processes
- Poor allocation patterns

**Solutions:**

**1. Memory Pools / Slab Allocators:**
```c
// Pre-allocate fixed-size blocks
struct Pool {
    void* blocks[1000];
    int free_count;
};
// Fast allocation, no fragmentation
```

**2. Compacting GC:**
- Moves objects to eliminate gaps
- Used by JVM, .NET
- Requires updating all references

**3. Arena/Bump Allocators:**
```c
// Allocate from contiguous region
char arena[1024*1024];
size_t offset = 0;

void* alloc(size_t size) {
    void* ptr = arena + offset;
    offset += size;
    return ptr;
}
// Free everything at once
```

**4. Object Pooling:**
- Reuse objects instead of freeing
- Eliminates fragmentation for pooled types

**Detection:**
```bash
# Linux - check memory fragmentation
cat /proc/buddyinfo

# Process memory map
pmap -x PID
```

**Prevention Best Practices:**
1. Use object pools for frequent allocations
2. Allocate similar-sized objects together
3. Batch allocations when possible
4. Consider arena allocation for request handling
5. Restart long-running processes periodically"""
    },
    {
        "instruction": "Explain profiling and the different types of profilers",
        "response": """**Profiling** measures program performance to identify optimization opportunities.

**Types of Profilers:**

**1. CPU Sampling Profiler:**
- Periodically samples the call stack
- Low overhead (1-5%)
- Shows where time is spent
- Tools: py-spy, perf, async-profiler

```bash
# Python sampling
py-spy record -o profile.svg -- python app.py

# Linux perf
perf record -g ./program
perf report
```

**2. Instrumentation Profiler:**
- Adds timing code to every function
- High accuracy, high overhead (10-100x slower)
- Exact call counts and times
- Tools: cProfile, gprof, callgrind

```python
python -m cProfile -s cumulative script.py
```

**3. Memory Profiler:**
- Tracks allocations and memory usage
- Identifies memory leaks
- Tools: Valgrind, tracemalloc, heaptrack

```python
from memory_profiler import profile
@profile
def my_function(): ...
```

**4. Tracing Profiler:**
- Records all events chronologically
- Useful for understanding execution flow
- Tools: strace, dtrace, bpftrace

```bash
strace -c ./program  # System call summary
```

**5. GPU Profiler:**
- CUDA, OpenCL performance
- Tools: nvprof, Nsight, rocprof

**Profiler Output Formats:**

| Format | Description |
|--------|-------------|
| **Flamegraph** | Visualization of stack samples |
| **Call tree** | Hierarchical call relationships |
| **Flat profile** | Functions sorted by time |
| **Timeline** | Events over time |

**Profiling Workflow:**

1. **Identify bottleneck type** (CPU? Memory? I/O?)
2. **Choose appropriate profiler**
3. **Profile under realistic load**
4. **Find hotspots** (functions using most time)
5. **Optimize hotspots first** (Amdahl's Law)
6. **Measure improvement**
7. **Repeat**

**Golden Rules:**
- Always profile before optimizing
- Profile in production-like environment
- Focus on the biggest bottlenecks first
- Re-profile after changes"""
    },
    {
        "instruction": "What are memory-mapped files and when should I use them?",
        "response": """**Memory-Mapped Files** map a file's contents directly into virtual memory, allowing file I/O through memory operations.

**How It Works:**
```
Virtual Memory ←→ File on Disk
Process sees file as array in memory
OS handles loading/saving pages automatically
```

**Benefits:**

1. **Simplified I/O** - Read/write like array access
2. **Automatic caching** - OS manages page cache
3. **Zero-copy sharing** - Multiple processes share same mapping
4. **Lazy loading** - Pages loaded on demand
5. **Large file support** - Map files larger than RAM

**Python Example:**
```python
import mmap

# Read file with mmap
with open('large_file.bin', 'r+b') as f:
    mm = mmap.mmap(f.fileno(), 0)
    
    # Access like bytes
    data = mm[1000:2000]
    
    # Search efficiently
    pos = mm.find(b'pattern')
    
    # Modify directly
    mm[0:4] = b'NEW!'
    
    mm.close()
```

**NumPy Memory Mapping:**
```python
import numpy as np

# Create memory-mapped array
arr = np.memmap('data.npy', dtype='float64', 
                mode='w+', shape=(1000000, 100))

# Use like normal array
arr[0] = [1, 2, 3, ...]
result = arr.mean(axis=0)  # Processes in chunks automatically
```

**When to Use:**

✅ **Good Use Cases:**
- Large files that don't fit in RAM
- Random access to file contents
- Sharing data between processes
- Database implementations
- Search/indexing large files

❌ **Avoid When:**
- File smaller than a few pages
- Strictly sequential access (regular I/O is fine)
- File on network storage (latency issues)
- Need atomic operations (use proper DB)

**Platform Differences:**

| Aspect | Linux | Windows |
|--------|-------|---------|
| Max mapping | Address space | 2GB per mapping |
| Sharing | mmap(MAP_SHARED) | CreateFileMapping |
| Anonymous | mmap(MAP_ANON) | CreateFileMapping(INVALID_HANDLE) |

**Caveats:**
- Changes may not be immediately written to disk (use `flush()`)
- Error handling is different (SIGBUS on Linux)
- File must exist and be seekable"""
    },
    {
        "instruction": "How do I optimize Python code for better performance?",
        "response": """**Python Performance Optimization Guide:**

**1. Profile First!**
```python
python -m cProfile -s cumulative script.py
# Or for line-by-line:
pip install line_profiler
kernprof -l -v script.py
```

**2. Algorithm Optimization (Biggest Impact)**
```python
# BAD: O(n²) - checking membership in list
if item in list_of_items:  # Scans entire list

# GOOD: O(1) - use set
item_set = set(list_of_items)
if item in item_set:  # Hash lookup
```

**3. Use Built-in Functions**
```python
# SLOW: Manual loop
total = 0
for x in items:
    total += x

# FAST: Built-in sum() is C-optimized
total = sum(items)

# Other fast builtins: map(), filter(), sorted(), any(), all()
```

**4. List Comprehensions > Loops**
```python
# SLOWER
result = []
for x in items:
    result.append(x * 2)

# FASTER (allocates right-sized list)
result = [x * 2 for x in items]

# FASTEST for huge data (generator)
result = (x * 2 for x in items)
```

**5. Use NumPy for Numeric Operations**
```python
import numpy as np

# SLOW: Python loop
result = [x * 2 for x in range(1000000)]

# 100x FASTER: NumPy vectorized
arr = np.arange(1000000)
result = arr * 2
```

**6. String Operations**
```python
# SLOW: String concatenation in loop
result = ""
for s in strings:
    result += s  # Creates new string each time

# FAST: Join
result = "".join(strings)
```

**7. Use Local Variables**
```python
# SLOWER: Global lookup each iteration
import math
def calculate(values):
    return [math.sqrt(v) for v in values]

# FASTER: Local reference
def calculate(values):
    sqrt = math.sqrt  # Cache lookup
    return [sqrt(v) for v in values]
```

**8. Slots for Memory and Speed**
```python
class Point:
    __slots__ = ['x', 'y']  # 40% less memory, faster attribute access
    def __init__(self, x, y):
        self.x = x
        self.y = y
```

**9. Use functools.lru_cache**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def expensive_calculation(n):
    # Cached results
    return n ** n
```

**10. Consider Cython/PyPy**
- Cython: Compile Python to C (10-100x speedup)
- PyPy: JIT-compiled Python (often 5-10x faster)

**Quick Reference:**
| Operation | Speed Improvement |
|-----------|-------------------|
| set vs list membership | 100x+ |
| NumPy vs Python loops | 50-100x |
| Local vs global lookup | 2-3x |
| join vs += for strings | 10x+ |
| __slots__ | 40% memory |"""
    },
    # === EXPANDED MEMORY/PERFORMANCE CONCEPTS ===
    {
        "instruction": "What is virtual memory and how does it work?",
        "response": """**Virtual Memory** is an abstraction that gives each process the illusion of having its own contiguous address space.

**How It Works:**
```
Virtual Address → Page Table → Physical Address
Process sees 0x7fff0000 → Maps to → RAM at 0x12340000 (or disk!)
```

**Key Components:**

**1. Page Table:**
- Maps virtual pages to physical frames
- One per process
- Contains: physical frame, present bit, dirty bit, permissions

**2. Memory Management Unit (MMU):**
- Hardware that performs address translation
- Uses Translation Lookaside Buffer (TLB) for speed

**3. Page Fault Handling:**
```
1. Process accesses virtual address
2. If page not in RAM (present=0)
3. Page fault trap to kernel
4. OS finds page on disk (swap)
5. Loads page into RAM
6. Updates page table
7. Restarts instruction
```

**Benefits:**
- **Isolation:** Processes can't access each other's memory
- **Memory overcommit:** Use more memory than physically available
- **Shared memory:** Map same physical page to multiple processes
- **Memory-mapped files:** Files appear as memory

**Virtual Address Layout (Linux x64):**
```
0xFFFFFFFF_FFFFFFFF ┌─────────────────┐
                    │   Kernel Space  │  128 TB
0xFFFF8000_00000000 ├─────────────────┤
                    │   Hole          │
0x00007FFF_FFFFFFFF ├─────────────────┤
                    │   Stack         │  Grows down
                    │   ...           │
                    │   Heap          │  Grows up
                    │   BSS/Data      │
                    │   Text (code)   │
0x00000000_00400000 └─────────────────┘
```

**Performance Considerations:**
- TLB misses are expensive
- Large pages (2MB, 1GB) reduce TLB pressure
- NUMA-aware allocation for multi-socket systems"""
    },
    {
        "instruction": "What is NUMA and how does it affect performance?",
        "response": """**NUMA (Non-Uniform Memory Access)** is a memory architecture where memory access time depends on memory location relative to the processor.

**Architecture:**
```
┌─────────────┐     ┌─────────────┐
│   CPU 0     │     │   CPU 1     │
│ ┌─────────┐ │     │ ┌─────────┐ │
│ │ Cores   │ │     │ │ Cores   │ │
│ └─────────┘ │     │ └─────────┘ │
│      ↓      │     │      ↓      │
│ ┌─────────┐ │     │ ┌─────────┐ │
│ │ Local   │←┼─────┼→│ Local   │ │
│ │ Memory  │ │QPI  │ │ Memory  │ │
│ └─────────┘ │     │ └─────────┘ │
└─────────────┘     └─────────────┘
  Local: ~80ns        Remote: ~150ns
```

**Why It Matters:**
- **Local access:** ~80ns latency
- **Remote access:** ~150ns+ (almost 2x slower!)
- Bandwidth is also lower for remote access

**Checking NUMA:**
```bash
# View NUMA topology
numactl --hardware

# Memory per node
numastat -m

# Process memory distribution
numastat -p PID
```

**NUMA-Aware Programming:**

**1. Memory Allocation:**
```bash
# Allocate memory on specific node
numactl --membind=0 ./application

# Interleave across nodes
numactl --interleave=all ./application
```

**2. CPU Pinning:**
```bash
# Pin process to CPUs on node 0
numactl --cpunodebind=0 --membind=0 ./application
```

**3. In Code (Linux):**
```c
#include <numa.h>
numa_set_preferred(node);  // Prefer allocations on node
numa_alloc_onnode(size, node);  // Explicit node allocation
```

**Best Practices:**
- Keep data close to the threads that use it
- Avoid sharing data structures across NUMA nodes
- Use local allocation for performance-critical data
- Consider NUMA for VMs and containers (isolate by node)

**Database Considerations:**
- PostgreSQL: huge_pages, NUMA interleaving
- MySQL: innodb_numa_interleave = ON"""
    },
    {
        "instruction": "What are copy-on-write semantics and why are they used?",
        "response": """**Copy-on-Write (CoW)** delays copying data until a write occurs, sharing read-only data until modification.

**How It Works:**
```
Initial:
Process A ─┐
           ├─→ [Shared Page] (Read-only)
Process B ─┘

After A writes:
Process A ───→ [Copied Page] (Read-write)
Process B ───→ [Original Page] (Read-only now just for B)
```

**Key Uses:**

**1. Process Fork:**
```c
pid_t pid = fork();
// Child doesn't copy all parent memory
// Pages marked CoW, copied only on write
// exec() replaces anyway, so often no copy needed!
```

**2. Language Runtimes:**
```python
# Python string immutability enables CoW-like behavior
s1 = "hello" * 1000000
s2 = s1  # No copy, same reference
s2 = s2 + "!"  # Now s2 gets new allocation
```

**3. File Systems (Btrfs, ZFS):**
```bash
# Btrfs snapshots use CoW
btrfs subvolume snapshot /data /snapshots/data-$(date +%Y%m%d)
# Instant snapshot, shares blocks until modified
```

**4. Databases:**
- MVCC (Multi-Version Concurrency Control)
- Readers don't block writers via versioning

**5. Container Images:**
- Docker layers share base images via overlay CoW

**Implementation (Kernel Level):**
```
1. Mark page as read-only
2. On write: page fault triggers
3. Kernel copies page to new location
4. Update page table for writing process
5. Mark new page read-write
```

**Benefits:**
- **Memory efficiency:** Share identical data
- **Fast fork:** Almost instant process creation
- **Snapshot capabilities:** Instant, space-efficient snapshots
- **Concurrency:** Readers don't block writers

**Caveats:**
- Write after fork can cause memory spike
- Watch for "fork bomb" memory exhaustion
- CoW can hide memory usage until writes occur"""
    },
    {
        "instruction": "Explain memory alignment and why it matters",
        "response": """**Memory Alignment** means placing data at addresses divisible by the data size.

**Natural Alignment Rules:**
```
1-byte (char)   → any address
2-byte (short)  → address divisible by 2
4-byte (int)    → address divisible by 4
8-byte (long)   → address divisible by 8
```

**Why It Matters:**

**1. CPU Performance:**
```
Aligned access (4-byte int at 0x1000):
CPU: Single memory read ✓

Misaligned access (4-byte int at 0x1001):
CPU: Two memory reads + combine = SLOWER
```

**2. Atomic Operations:**
- Misaligned data can't be atomically accessed
- May cause torn reads/writes in multi-threaded code

**3. SIMD Requirements:**
- SSE/AVX often REQUIRE 16/32-byte alignment
- Misalignment causes SIGBUS on some platforms

**Struct Padding Example:**
```c
// Without padding awareness:
struct Bad {
    char a;     // 1 byte + 3 padding
    int b;      // 4 bytes
    char c;     // 1 byte + 3 padding
};  // Total: 12 bytes!

// Optimized ordering:
struct Good {
    int b;      // 4 bytes
    char a;     // 1 byte
    char c;     // 1 byte + 2 padding
};  // Total: 8 bytes!
```

**Checking Alignment:**
```c
#include <stdalign.h>
printf("Alignment of int: %zu\\n", alignof(int));  // 4

// Force alignment
alignas(64) int cache_line_aligned[16];
```

**Platform Differences:**
| Platform | Misaligned Access |
|----------|-------------------|
| x86/x64 | Works but slower |
| ARM | May crash (SIGBUS) |
| MIPS | Crashes |
| RISC-V | Crashes (default) |

**Best Practices:**
- Order struct members by size (largest first)
- Use packed structs for network/disk only
- Use alignas() for SIMD data
- Profile: misalignment can cause 10x slowdown"""
    },
    {
        "instruction": "What is memory pressure and how do I respond to it?",
        "response": """**Memory Pressure** occurs when available memory is low, forcing the system to reclaim memory from caches and applications.

**Memory Pressure Signals:**

**Linux:**
```bash
# Memory pressure indicator (cgroups v2)
cat /sys/fs/cgroup/memory.pressure

# Traditional indicators
free -h  # Look at available column
cat /proc/meminfo | grep -E 'MemAvailable|SwapFree'
```

**macOS:**
```bash
memory_pressure  # Shows current pressure level
vm_stat  # Virtual memory statistics
```

**Pressure Levels:**

| Level | Meaning | System Response |
|-------|---------|-----------------|
| None | Plenty of memory | Normal operation |
| Low | Getting tight | Drop file caches |
| Medium | Significant | Swap out inactive pages |
| Critical | Near OOM | Kill processes |

**Application Response Strategies:**

**1. Monitor and Adapt:**
```python
import psutil

def get_memory_pressure():
    mem = psutil.virtual_memory()
    return 1 - (mem.available / mem.total)  # 0-1 scale

def adjust_cache_size():
    pressure = get_memory_pressure()
    if pressure > 0.8:
        reduce_cache(50)  # Cut cache by 50%
```

**2. Release Memory Proactively:**
```python
# Python: Force GC during pressure
import gc
if memory_pressure > 0.7:
    gc.collect()
```

**3. Avoid Allocation During Pressure:**
```python
# Check before large allocation
if psutil.virtual_memory().available < required_bytes:
    raise MemoryError("Insufficient memory")
```

**4. OS Notifications:**
```objective-c
// macOS memory warning
- (void)didReceiveMemoryWarning {
    [self clearCaches];
}
```

**System Tuning:**
```bash
# Adjust swappiness (0-100)
sysctl vm.swappiness=10  # Prefer keeping in RAM

# Adjust OOM score for critical processes
echo -1000 > /proc/PID/oom_score_adj
```

**Best Practices:**
- Monitor memory metrics continuously
- Implement graceful degradation
- Size caches relative to available memory
- Test behavior under pressure"""
    },
    {
        "instruction": "How do JIT compilers affect memory and performance?",
        "response": """**JIT (Just-In-Time) Compilation** compiles code at runtime, trading memory for performance.

**How JIT Works:**
```
Source Code → Bytecode → [JIT] → Native Machine Code
                            ↓
                      Stored in Code Cache
```

**Memory Impact:**

**Code Cache:**
- JIT-compiled code stored in memory
- Can grow to hundreds of MB
- Examples: JVM -XX:ReservedCodeCacheSize=256m

**Profiling Data:**
- Runtime collects execution statistics
- Hot paths identified for optimization
- Uses additional memory

**Compilation Overhead:**
- Compiler itself needs memory
- Temporary structures during compilation

**JIT Tiers (e.g., HotSpot JVM):**
```
Level 0: Interpreter (no JIT memory)
Level 1: Simple C1 compilation (low memory)
Level 2: Limited profiling C1
Level 3: Full profiling C1
Level 4: C2 optimized (highest memory, best perf)
```

**Tuning JIT Memory:**

**Java:**
```bash
# Code cache size
-XX:ReservedCodeCacheSize=256m

# Compilation threshold (higher = less compiled code)
-XX:CompileThreshold=10000

# Disable tiered compilation (less memory)
-XX:-TieredCompilation
```

**Node.js (V8):**
```bash
# Limit heap and code cache
--max-old-space-size=512
--max-semi-space-size=64
```

**Python (PyPy):**
```bash
# JIT threshold (higher = less JIT)
PYPY_GC_MAX_DELTA=200MB pypy script.py
```

**Trade-offs:**
| Aspect | Interpreter | JIT |
|--------|-------------|-----|
| Startup | Fast | Slow (compilation) |
| Memory | Low | Higher (code cache) |
| Peak Perf | Low | High |
| Warmup | None | Required |

**Best Practices:**
- Size code cache appropriately
- Warm up before benchmarking
- Consider AOT for memory-constrained environments
- Profile JIT behavior with -XX:+PrintCompilation (Java)"""
    },
    {
        "instruction": "What is working set and resident set size?",
        "response": """**Working Set** and **Resident Set Size (RSS)** are key metrics for understanding memory usage.

**Definitions:**

**Resident Set Size (RSS):**
- Memory physically in RAM right now
- What you see in `top` or `ps`
- May be shared with other processes

**Virtual Size (VSZ):**
- Total virtual address space allocated
- Includes mapped files, shared libraries, heap
- Much larger than RSS (can be huge)

**Working Set:**
- Pages actively being used
- What the process needs to run efficiently
- If working set > RAM = thrashing

**Proportional Set Size (PSS):**
- RSS but shared pages divided among sharers
- More accurate for total system impact

**Understanding the Numbers:**
```
Process shows:
  VSZ: 4.5 GB    ← Don't panic, virtual is cheap
  RSS: 800 MB    ← Actually in RAM
  PSS: 450 MB    ← Your "fair share"
  USS: 300 MB    ← Unique memory (yours only)
```

**Checking on Linux:**
```bash
# RSS and VSZ
ps aux | grep process_name

# Detailed memory map with PSS
smem -tk -s pss

# Process-specific breakdown
cat /proc/PID/smaps | grep -E '^(Size|Rss|Pss)'

# Summary
cat /proc/PID/status | grep -E 'VmRSS|VmSize|VmPeak'
```

**Why RSS Can Be Misleading:**
```
Shared library example:
  libc.so mapped by 200 processes
  Each shows 2MB RSS for libc
  But only 2MB actual RAM used!
  
PSS: Each process shows 2MB/200 = 10KB
```

**Performance Implications:**

| Metric | What It Tells You |
|--------|-------------------|
| RSS growing | Possible memory leak |
| RSS >> WSS | Bloated but not active |
| WSS >> RAM | Thrashing, poor performance |
| High PSS | Real memory pressure |

**Best Practices:**
- Monitor PSS for true memory impact
- Track RSS over time for leak detection
- Don't over-react to high VSZ
- Use smem for accurate system-wide view"""
    },
    {
        "instruction": "Explain memory barriers and why they're needed",
        "response": """**Memory Barriers** (fences) prevent CPU and compiler from reordering memory operations, ensuring correct multi-threaded behavior.

**The Problem:**
```c
// Thread 1               // Thread 2
data = 42;               while (!ready) ;
ready = true;            print(data);  // Could print 0!

// Without barriers, CPU/compiler may reorder:
ready = true;            // Happens first!
data = 42;               // Too late
```

**Why Reordering Happens:**

**1. Compiler Optimization:**
- Reorders instructions for efficiency
- Hoists loads out of loops
- Combines memory operations

**2. CPU Optimization:**
- Out-of-order execution
- Store buffers delay writes
- Cache coherency timing

**Memory Ordering Models:**

| Model | Guarantees | Example |
|-------|------------|---------|
| Sequential Consistency | Total order | Slowest, safest |
| Acquire-Release | Sync points | Most common |
| Relaxed | None | Fastest, hardest |

**Types of Barriers:**

**Load Barrier (Acquire):**
- All reads after barrier see values from before
- "Acquire" new data from other threads

**Store Barrier (Release):**
- All writes before barrier visible to others
- "Release" data to other threads

**Full Barrier (SeqCst):**
- Both load and store barrier
- Sequential consistency at that point

**Usage Examples:**

**C++11 Atomics:**
```cpp
std::atomic<bool> ready{false};
int data;

// Producer
data = 42;
ready.store(true, std::memory_order_release);

// Consumer
while (!ready.load(std::memory_order_acquire));
assert(data == 42);  // Guaranteed!
```

**C with Compiler Barrier:**
```c
data = 42;
__asm__ __volatile__("" ::: "memory");  // Compiler barrier
ready = 1;
```

**Java:**
```java
volatile boolean ready = false;  // Volatile = barrier
```

**Best Practices:**
- Use atomics, not raw barriers
- Prefer acquire-release over seq_cst
- Relaxed only for counters/metrics
- Test on ARM (weaker than x86)"""
    },
    {
        "instruction": "What causes thrashing and how do I prevent it?",
        "response": """**Thrashing** occurs when a system spends more time swapping pages than executing useful work.

**Symptoms:**
- System becomes extremely slow
- Disk constantly busy (high I/O wait)
- CPU appears idle despite load
- Mouse/keyboard unresponsive

**Detecting Thrashing:**
```bash
# Check for high swap activity
vmstat 1
# Look for high si/so (swap in/out)

# Page fault rate
sar -B 1 10
# High pgpgin/pgpgout = thrashing

# I/O wait
top
# Look for high wa%
```

**Root Causes:**

**1. Over-committed Memory:**
- Total process memory > RAM + swap
- OOM killer or thrashing follows

**2. Working Set > RAM:**
- Application needs more active data than fits
- Constant page faults

**3. Memory Leak:**
- Process grows until system thrashes
- Then OOM

**4. Too Many Processes:**
- Each needs its working set
- Combined working sets exceed RAM

**Solutions:**

**Immediate Relief:**
```bash
# Kill largest memory consumer
kill $(ps aux --sort=-%mem | head -2 | tail -1 | awk '{print $2}')

# Reduce swappiness to keep more in RAM
echo 10 | sudo tee /proc/sys/vm/swappiness

# Disable swap entirely (risky)
sudo swapoff -a
```

**Application Level:**
```python
# Process data in chunks
for chunk in pd.read_csv(file, chunksize=10000):
    process(chunk)  # Don't load entire file

# Limit cache sizes
from functools import lru_cache
@lru_cache(maxsize=1000)  # Bounded!
def expensive_function(arg): ...

# Use memory-mapped files
data = np.memmap(file, dtype='float64', mode='r')
```

**System Level:**
```bash
# Add more swap (temporary)
sudo fallocate -l 4G /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Limit process memory
ulimit -v 4000000  # 4GB limit

# Cgroups for memory limits
echo 2G > /sys/fs/cgroup/mygroup/memory.max
```

**Prevention:**
- Monitor memory trends
- Set memory limits for applications
- Size systems appropriately
- Use alerts for memory pressure"""
    },
    {
        "instruction": "How do I analyze memory usage in containers?",
        "response": """**Container Memory Analysis** requires understanding cgroup limits and metrics.

**Container Memory Components:**
```
Container Memory
├── Application heap
├── Application stack
├── Shared libraries (may share with host)
├── File cache (counts against limit!)
├── Tmpfs mounts
└── Kernel data structures
```

**Key Metrics:**

**Docker:**
```bash
# Real-time stats
docker stats container_name

# Detailed memory info
docker inspect container_name | jq '.[0].HostConfig.Memory'

# Inside container
cat /sys/fs/cgroup/memory/memory.stat
```

**Kubernetes:**
```bash
# Pod memory usage
kubectl top pod pod_name

# Detailed container metrics
kubectl exec pod_name -- cat /sys/fs/cgroup/memory/memory.stat
```

**Understanding Container Memory Metrics:**

| Metric | Meaning |
|--------|---------|
| cache | Page cache (can be reclaimed) |
| rss | Anonymous memory (heap, stack) |
| swap | Swap usage (if enabled) |
| working_set | rss + cache that can't be reclaimed |
| limit | Memory limit set |

**cgroup v2 Memory Stats:**
```bash
cat /sys/fs/cgroup/memory.current    # Current usage
cat /sys/fs/cgroup/memory.max        # Limit
cat /sys/fs/cgroup/memory.stat       # Breakdown
```

**Common Issues:**

**1. OOMKilled:**
```bash
# Check if OOM killed
kubectl describe pod | grep -A5 "Last State"
dmesg | grep -i oom

# Causes:
# - Memory limit too low
# - Memory leak in application
# - Large file cache not accounted for
```

**2. Cache Eating Limit:**
```yaml
# Solution: Set memory.high for soft limit
# Lets kernel reclaim cache before OOM
```

**Debugging Tools:**
```bash
# Profile inside container
docker exec -it container sh
apk add py3-pip && pip install memory_profiler

# Heap dump (Java)
docker exec container jcmd 1 GC.heap_dump /tmp/heap.hprof
docker cp container:/tmp/heap.hprof .
```

**Best Practices:**
- Set requests AND limits
- Account for file cache in limits
- Monitor working_set, not just rss
- Test with actual production load"""
    },
]

# ============================================================================
# ERROR & TROUBLESHOOTING SCENARIOS
# ============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "I'm getting 'Out of Memory' errors, what should I do?",
        "response": {
            "status": "error_diagnosis",
            "error": "Out of Memory (OOM)",
            "immediate_actions": [
                "Check which process is consuming memory: ps aux --sort=-%mem | head",
                "Check available memory: free -h",
                "Check OOM logs: dmesg | grep -i 'oom\\|kill'"
            ],
            "diagnosis_steps": [
                {"check": "Is it a memory leak?", "command": "Monitor memory over time with htop"},
                {"check": "Is data too large for RAM?", "command": "Check dataset size vs available memory"},
                {"check": "Are there too many processes?", "command": "Count processes: ps aux | wc -l"},
                {"check": "Is swap configured?", "command": "swapon --show"}
            ],
            "solutions": {
                "memory_leak": "Profile with memory_profiler or tracemalloc to find leak",
                "large_data": ["Use generators instead of lists", "Process data in chunks", "Use memory-mapped files"],
                "insufficient_ram": ["Add swap space", "Increase RAM", "Use streaming processing"],
                "application_tuning": ["Reduce cache sizes", "Use object pooling", "Optimize data structures"]
            },
            "quick_fixes": [
                "Restart the process (temporary)",
                "Add swap: sudo fallocate -l 4G /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile",
                "Limit process memory: ulimit -v 4000000"
            ]
        }
    },
    {
        "instruction": "My application performance degrades over time",
        "response": {
            "status": "diagnosis",
            "error": "Performance degradation over time",
            "likely_causes": [
                "Memory leak (memory usage growing)",
                "Memory fragmentation",
                "Cache pollution",
                "Resource exhaustion (file handles, connections)",
                "GC pressure increasing"
            ],
            "investigation_commands": [
                {"check": "Memory growth", "command": "watch -n 1 'ps -p PID -o rss,vsz'"},
                {"check": "Handle leaks", "command": "ls /proc/PID/fd | wc -l"},
                {"check": "GC activity", "language_specific": "Enable GC logging"},
                {"check": "Connection leaks", "command": "netstat -an | grep ESTABLISHED | wc -l"}
            ],
            "profiling_approach": [
                "Take baseline profile at startup",
                "Run under load for extended period",
                "Take profile when degraded",
                "Compare profiles to find growth"
            ],
            "common_fixes": {
                "memory_leak": "Find and fix with profiler, add resource cleanup",
                "fragmentation": "Use object pooling, consider periodic restart",
                "cache_growth": "Add TTL and max size to caches",
                "handle_leak": "Ensure all resources are closed (use context managers)",
                "gc_pressure": "Reduce allocation rate, increase heap size"
            }
        }
    },
    {
        "instruction": "How do I diagnose high CPU usage?",
        "response": {
            "status": "troubleshooting_guide",
            "error": "High CPU usage",
            "quick_check": "top -c or htop to identify culprit process",
            "diagnosis_workflow": [
                {"step": 1, "action": "Identify process", "command": "top -b -n 1 | head -20"},
                {"step": 2, "action": "Check if waiting on I/O", "command": "iostat -x 1 5", "look_for": "High iowait = I/O bound"},
                {"step": 3, "action": "Profile the process", "python": "py-spy top --pid PID", "general": "perf top -p PID"},
                {"step": 4, "action": "Look for hot functions", "command": "perf record -g -p PID; perf report"},
                {"step": 5, "action": "Check for infinite loops", "look_for": "Single function at 100%"},
                {"step": 6, "action": "Analyze thread activity", "command": "ps -T -p PID"}
            ],
            "common_causes": [
                {"cause": "Infinite loop", "fix": "Review and fix loop condition"},
                {"cause": "Inefficient algorithm", "fix": "Optimize algorithm complexity"},
                {"cause": "Busy waiting", "fix": "Use proper synchronization/sleep"},
                {"cause": "GC thrashing", "fix": "Reduce allocation rate, tune GC"},
                {"cause": "Lock contention", "fix": "Reduce lock scope, use lock-free structures"}
            ],
            "python_specific": "Check for GIL contention if multi-threaded"
        }
    },
    {
        "instruction": "GC pauses are causing latency spikes in my application",
        "response": {
            "status": "gc_tuning",
            "error": "GC-induced latency spikes",
            "diagnosis": [
                "Enable GC logging to see pause times",
                "Identify frequency and duration of pauses",
                "Check heap utilization patterns"
            ],
            "solutions_by_language": {
                "java": {
                    "use_low_latency_gc": "-XX:+UseZGC (JDK 11+) or -XX:+UseShenandoahGC",
                    "tune_heap": "-Xms4g -Xmx4g (equal min/max)",
                    "enable_logging": "-Xlog:gc*:file=gc.log"
                },
                "csharp": {
                    "use_server_gc": "<ServerGarbageCollection enabled=\"true\"/>",
                    "low_latency": "GCSettings.LatencyMode = GCLatencyMode.LowLatency"
                },
                "go": {
                    "reduce_heap": "GOGC=100 (default)",
                    "soft_memory_limit": "GOMEMLIMIT=4GiB"
                },
                "python": {
                    "disable_gc_in_critical": "gc.disable() / gc.enable()",
                    "reduce_allocations": "Object pooling, reuse objects"
                }
            },
            "general_strategies": [
                "Reduce allocation rate (less garbage = fewer GC)",
                "Use object pooling for frequent allocations",
                "Pre-allocate and reuse data structures",
                "Consider off-heap storage for large data",
                "Schedule GC during idle periods"
            ]
        }
    },
    {
        "instruction": "Valgrind reports memory errors in my C/C++ code",
        "response": {
            "status": "memory_error_guide",
            "tool": "Valgrind",
            "common_errors": {
                "Invalid read/write": {
                    "meaning": "Accessing memory outside allocated bounds",
                    "example": "Array index out of bounds",
                    "fix": "Check array bounds, use std::vector with .at()"
                },
                "Use of uninitialized value": {
                    "meaning": "Reading variable before assignment",
                    "example": "int x; if (x > 0)...",
                    "fix": "Always initialize variables"
                },
                "Invalid free": {
                    "meaning": "Freeing memory not allocated or already freed",
                    "example": "Double free, freeing stack memory",
                    "fix": "Set pointers to NULL after free, use smart pointers"
                },
                "Memory leak": {
                    "meaning": "Allocated memory never freed",
                    "example": "malloc without free",
                    "fix": "Match every malloc with free, use RAII/smart pointers"
                },
                "Mismatched free": {
                    "meaning": "Using wrong deallocator",
                    "example": "new[] with delete (not delete[])",
                    "fix": "Match new/delete, new[]/delete[], malloc/free"
                }
            },
            "best_practices": [
                "Use smart pointers (unique_ptr, shared_ptr)",
                "Use std::vector instead of raw arrays",
                "Enable AddressSanitizer in development: -fsanitize=address",
                "Run Valgrind in CI pipeline",
                "Use RAII pattern for all resource management"
            ],
            "command": "valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes ./program"
        }
    },
    {
        "instruction": "Container keeps getting OOMKilled in Kubernetes",
        "response": {
            "status": "k8s_troubleshooting",
            "error": "Container OOMKilled",
            "explanation": "Container exceeded its memory limit and was killed",
            "diagnosis": [
                {"command": "kubectl describe pod <pod-name>", "look_for": "OOMKilled, Last State: Terminated"},
                {"command": "kubectl top pod <pod-name>", "look_for": "Memory usage near limit"},
                {"command": "kubectl logs <pod-name> --previous", "purpose": "See logs before crash"}
            ],
            "solutions": {
                "increase_limits": "resources: limits: memory: 2Gi (if you have capacity)",
                "fix_memory_leak": "Profile application for leaks",
                "set_realistic_requests": "requests should reflect actual baseline usage",
                "use_vertical_pod_autoscaler": "VPA can adjust resources automatically"
            },
            "java_specific": {
                "note": "JVM may not respect container limits",
                "fix": "-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0"
            },
            "prevention": [
                "Set accurate memory limits based on profiling",
                "Use readiness/liveness probes",
                "Implement graceful shutdown handling"
            ]
        }
    },
    {
        "instruction": "Python process consuming much more memory than expected",
        "response": {
            "status": "python_memory_debug",
            "error": "Python high memory usage",
            "common_causes": [
                "Holding references in lists/dicts that grow",
                "Circular references preventing GC",
                "C extension memory leaks",
                "Large pandas DataFrames",
                "Caching without bounds"
            ],
            "debugging_tools": [
                {"tool": "tracemalloc", "purpose": "Track Python memory allocations", "code": "import tracemalloc; tracemalloc.start(); # run code; tracemalloc.get_traced_memory()"},
                {"tool": "memory_profiler", "purpose": "Line-by-line memory usage", "code": "@profile decorator or python -m memory_profiler script.py"},
                {"tool": "objgraph", "purpose": "Find what's holding references", "code": "import objgraph; objgraph.show_most_common_types()"},
                {"tool": "guppy3/pympler", "purpose": "Heap analysis", "code": "from pympler import muppy, summary; summary.print_(summary.summarize(muppy.get_objects()))"}
            ],
            "pandas_specific": [
                "Use appropriate dtypes (int32 vs int64)",
                "Read CSV with usecols to only load needed columns",
                "Use chunking: pd.read_csv(file, chunksize=10000)",
                "Consider dask for larger-than-memory processing"
            ],
            "quick_fixes": [
                "del large_object; gc.collect()",
                "Use generators: (x for x in iterable) instead of [x for x in iterable]",
                "Process data in batches"
            ]
        }
    },
    {
        "instruction": "Node.js heap out of memory error",
        "response": {
            "status": "nodejs_memory",
            "error": "JavaScript heap out of memory",
            "immediate_fix": "node --max-old-space-size=4096 app.js (increase to 4GB)",
            "diagnosis": {
                "check_current_limit": "node -e 'console.log(v8.getHeapStatistics().heap_size_limit / 1024 / 1024)'",
                "enable_heap_dump": "NODE_OPTIONS='--heapsnapshot-signal=SIGUSR2' node app.js; kill -USR2 <pid>",
                "chrome_devtools": "node --inspect app.js; connect Chrome DevTools"
            },
            "common_causes": [
                "Memory leaks from unclosed event listeners",
                "Accumulating objects in module-level arrays",
                "Circular references in closures",
                "Large buffers not released",
                "Too many concurrent requests holding data"
            ],
            "tools": [
                "clinic.js for profiling: clinic doctor -- node app.js",
                "heapdump module for snapshots",
                "Chrome DevTools Memory tab"
            ],
            "fixes": [
                "Remove event listeners: emitter.removeListener()",
                "Use WeakMap/WeakSet for caches",
                "Stream large files instead of loading into memory",
                "Implement proper connection pooling"
            ]
        }
    },
    {
        "instruction": "Linux system swap is being used heavily, how to diagnose?",
        "response": {
            "status": "swap_diagnosis",
            "error": "Heavy swap usage",
            "impact": "Swap usage = slower performance, not necessarily a problem if infrequent",
            "diagnosis_commands": [
                {"command": "free -h", "look_for": "Swap used vs total"},
                {"command": "vmstat 1 5", "look_for": "si/so columns (swap in/out)"},
                {"command": "cat /proc/meminfo | grep -i swap", "purpose": "Detailed swap info"},
                {"command": "for f in /proc/*/status; do cat $f 2>/dev/null | awk '/VmSwap/{print $2}'; done | sort -n | tail", "purpose": "Per-process swap"}
            ],
            "common_causes": [
                "Insufficient RAM for workload",
                "Memory leak in application",
                "Too many processes",
                "swappiness set too high"
            ],
            "solutions": {
                "reduce_swappiness": "sudo sysctl vm.swappiness=10 (prefer RAM)",
                "identify_culprit": "ps aux --sort=-%mem | head -10",
                "add_more_ram": "If consistently swapping under normal load",
                "fix_memory_leak": "Profile and fix leaky application",
                "limit_processes": "Use cgroups or reduce worker count"
            },
            "note": "Some swap usage is normal - kernel swaps inactive pages to keep active pages in RAM"
        }
    },
    {
        "instruction": "Windows Task Manager shows high memory usage but processes don't add up",
        "response": {
            "status": "windows_memory_analysis",
            "error": "Memory accounting mismatch",
            "explanation": "Task Manager shows committed memory, not actual RAM. Some memory is shared, some is for drivers/system",
            "diagnosis_tools": [
                {"tool": "Resource Monitor", "access": "resmon.exe", "tab": "Memory tab shows detailed breakdown"},
                {"tool": "RAMMap", "source": "Sysinternals", "purpose": "Shows physical memory allocation"},
                {"tool": "poolmon", "purpose": "Shows kernel pool memory (driver leaks)"}
            ],
            "common_causes": [
                "NonPaged Pool growth = driver leak",
                "Standby memory (cached, available for use)",
                "Modified memory waiting to be written",
                "Mapped files (shared DLLs)"
            ],
            "solutions": {
                "driver_leak": "Update or remove faulty driver, poolmon to identify",
                "large_standby": "This is normal - Windows uses unused RAM as cache",
                "reduce_superfetch": "Disable if SSD: services.msc -> SysMain -> Disabled"
            },
            "command": "Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10 Name, @{N='RAM(MB)';E={$_.WorkingSet64/1MB}}"
        }
    },
    {
        "instruction": "JVM heap dump analysis - how to find memory leak?",
        "response": {
            "status": "heap_analysis",
            "error": "JVM memory leak investigation",
            "generate_heap_dump": [
                "jmap -dump:live,format=b,file=heap.hprof <pid>",
                "Or on OOM: -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/path/heap.hprof"
            ],
            "analysis_tools": [
                {"tool": "Eclipse MAT", "best_for": "Finding leaks, dominator tree"},
                {"tool": "VisualVM", "best_for": "Real-time monitoring + heap dump analysis"},
                {"tool": "YourKit", "best_for": "Professional profiling"}
            ],
            "mat_analysis_steps": [
                {"step": 1, "action": "Open heap dump in MAT"},
                {"step": 2, "action": "Run Leak Suspects report", "look_for": "Problem Suspect 1"},
                {"step": 3, "action": "Check Dominator Tree", "look_for": "Objects retaining most memory"},
                {"step": 4, "action": "Find GC Roots", "purpose": "See why objects can't be collected"},
                {"step": 5, "action": "Compare heap dumps", "purpose": "See what grew between dumps"}
            ],
            "common_leak_patterns": [
                "Growing collections (ArrayList, HashMap)",
                "Static fields holding references",
                "Listeners not removed",
                "Thread-local variables not cleaned",
                "Custom caches without eviction"
            ]
        }
    },
    {
        "instruction": "Application freezing during full GC",
        "response": {
            "status": "gc_freeze",
            "error": "Stop-the-world GC pauses",
            "explanation": "Full GC stops all application threads - can cause noticeable pauses",
            "diagnosis": {
                "java": "Add -Xlog:gc*:gc.log; look for 'Full GC' events",
                "check_frequency": "If Full GC every few seconds, heap is too small or leak present"
            },
            "solutions": {
                "java": {
                    "switch_to_zgc": "-XX:+UseZGC (JDK 11+) - sub-millisecond pauses",
                    "switch_to_g1": "-XX:+UseG1GC - balanced approach",
                    "tune_g1": "-XX:MaxGCPauseMillis=200 -XX:+UseStringDeduplication",
                    "increase_heap": "More heap = less frequent Full GC"
                },
                "general": [
                    "Reduce allocation rate",
                    "Fix memory leaks to prevent heap filling",
                    "Use concurrent GC collectors",
                    "Consider off-heap data structures"
                ]
            },
            "monitoring": "Track GC pause times as key metric, alert if exceeds threshold"
        }
    },
    {
        "instruction": "Docker container memory limit not working",
        "response": {
            "status": "container_memory",
            "error": "Memory limit not enforced",
            "common_issues": {
                "jvm_ignoring_limit": {
                    "problem": "Old JVMs don't see cgroup limits",
                    "fix": "-XX:+UseContainerSupport (JDK 10+, default) or manual -Xmx"
                },
                "wrong_cgroup_version": {
                    "check": "stat -fc %T /sys/fs/cgroup/",
                    "v1": "Memory limit in /sys/fs/cgroup/memory/",
                    "v2": "Memory limit in /sys/fs/cgroup/"
                },
                "limit_not_set": {
                    "check": "docker inspect <container> | grep Memory",
                    "ensure": "docker run -m 2g or resources.limits.memory in K8s"
                }
            },
            "verification": [
                "Inside container: cat /sys/fs/cgroup/memory/memory.limit_in_bytes (v1)",
                "Inside container: cat /sys/fs/cgroup/memory.max (v2)",
                "docker stats <container>"
            ],
            "note": "Memory limit includes both heap and native memory - set heap lower than container limit"
        }
    },
    {
        "instruction": "BufferOverflowException in my network application",
        "response": {
            "status": "buffer_management",
            "error": "Buffer overflow/underflow",
            "common_causes": [
                "Fixed-size buffer too small for data",
                "Not checking data size before read",
                "Off-by-one errors in buffer indexing",
                "Forgetting to flip() ByteBuffer"
            ],
            "java_nio_specifics": {
                "flip_usage": "buffer.flip() after write, before read",
                "clear_vs_compact": "clear() for full reset, compact() to preserve unread data",
                "position_limit": "position < limit always",
                "remaining_check": "buffer.remaining() before get()"
            },
            "fixes": [
                "Use dynamic buffers that grow: ByteArrayOutputStream",
                "Always check remaining space before write",
                "Validate incoming data size against buffer capacity",
                "Use try-finally or try-with-resources for buffer cleanup"
            ],
            "safe_pattern": "ByteBuffer buffer = ByteBuffer.allocate(1024); if (data.length <= buffer.remaining()) { buffer.put(data); } else { // handle overflow }"
        }
    }
]

# ============================================================================
# GUARDRAIL SCENARIOS
# ============================================================================

GUARDRAILS = [
    {
        "instruction": "Disable swap completely on my server",
        "response": {
            "status": "caution",
            "reason": "Disabling swap removes safety net against OOM",
            "risks": [
                "OOM killer may terminate critical processes",
                "No warning before system becomes unresponsive",
                "Databases may crash instead of slowing down"
            ],
            "alternatives": [
                "Reduce swappiness: sudo sysctl vm.swappiness=10",
                "Use small swap as emergency buffer",
                "Enable memory cgroups for container limits"
            ],
            "if_you_must": {
                "command": "sudo swapoff -a",
                "prerequisites": [
                    "Ensure sufficient RAM for workload + buffer",
                    "Configure memory limits for all services",
                    "Set up monitoring and alerts for memory usage",
                    "Have restart procedures for critical services"
                ]
            }
        }
    },
    {
        "instruction": "Set ulimit -m unlimited for my process",
        "response": {
            "status": "warning",
            "reason": "Unlimited memory can destabilize entire system",
            "risks": [
                "Single process can consume all RAM",
                "May trigger OOM killer on other processes",
                "System may become unresponsive"
            ],
            "better_approaches": [
                "Set reasonable limit based on expected usage",
                "Use cgroups for container memory limits",
                "Profile to understand actual memory needs",
                "Implement graceful degradation in application"
            ],
            "recommended_command": "ulimit -v 4000000  # 4GB limit in KB"
        }
    },
    {
        "instruction": "Run my app with -Xmx set to total system RAM",
        "response": {
            "status": "blocked",
            "reason": "JVM heap at system RAM size will crash the system",
            "explanation": "JVM needs additional memory for metaspace, thread stacks, native memory, and OS needs memory too",
            "safe_guidelines": {
                "max_heap": "50-75% of available RAM",
                "leave_for_os": "Minimum 2GB for OS and buffers",
                "off_heap": "Account for direct buffers, native memory"
            },
            "example": {
                "system_ram": "16GB",
                "recommended_xmx": "-Xmx10g to -Xmx12g",
                "full_command": "java -Xms8g -Xmx12g -XX:MaxMetaspaceSize=256m -jar app.jar"
            }
        }
    }
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_task_response(task_data: dict) -> str:
    """Format a task as JSON response."""
    return json.dumps({
        "action": "execute_command",
        "tool": task_data["tool"],
        "command": task_data["command"],
        "explanation": task_data["explanation"]
    }, indent=2)


def format_code_response(code_data: dict) -> str:
    """Format code example as JSON response."""
    return json.dumps({
        "action": "provide_code",
        "tool": code_data["tool"],
        "language": code_data["language"],
        "code": code_data["code"],
        "explanation": code_data["explanation"]
    }, indent=2)


def format_planning_response(plan_data: dict) -> str:
    """Format planning response."""
    return json.dumps(plan_data, indent=2)


def main():
    DATA_DIR.mkdir(exist_ok=True)
    examples = []
    
    # Linux memory tasks
    for instruction, data in LINUX_MEMORY_TASKS.items():
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": f"[Linux] {instruction}",
            "response": format_task_response(data)
        })
    
    # Windows memory tasks
    for instruction, data in WINDOWS_MEMORY_TASKS.items():
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": f"[Windows PowerShell] {instruction}",
            "response": format_task_response(data)
        })
    
    # Profiling tasks
    for instruction, data in PROFILING_TASKS.items():
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": instruction,
            "response": format_task_response(data)
        })
    
    # Code examples
    for instruction, data in CODE_EXAMPLES.items():
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": f"Show me {instruction}",
            "response": format_code_response(data)
        })
    
    # Planning tasks
    for task in PLANNING_TASKS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": task["instruction"],
            "response": format_planning_response(task["response"])
        })
    
    # Concepts
    for qa in CONCEPT_QA:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": qa["instruction"],
            "response": qa["response"]
        })
    
    # Errors
    for scenario in ERROR_SCENARIOS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": scenario["instruction"],
            "response": json.dumps(scenario["response"], indent=2)
        })
    
    # Guardrails
    for scenario in GUARDRAILS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": scenario["instruction"],
            "response": json.dumps(scenario["response"], indent=2)
        })
    
    # Shuffle and write
    random.shuffle(examples)
    
    output_file = DATA_DIR / "memory_data.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"Generated {len(examples)} memory/performance examples to {output_file}")


if __name__ == "__main__":
    main()
