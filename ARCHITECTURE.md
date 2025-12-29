# AJ Architecture Documentation

## Overview

AJ is an agentic-capable AI-based assistant for Open-WebUI that provides:

- **Semantic Memory** — Stores and retrieves conversation context from Qdrant using intent classification (4-class: casual/save/recall/task)
- **(WIP!!) Workspace Operations** — Read, list, and edit files in mounted workspace
- **(WIP!!) Surgical File Editing** — Replace, insert, append operations

---

## Model Architecture (Consolidated)

AJ uses a streamlined 3-component model setup optimized for RTX 4090 (24GB VRAM):

| Component  | Model                   | Location       | Purpose                                      | Memory           |
| ---------- | ----------------------- | -------------- | -------------------------------------------- | ---------------- |
| **LLM**    | Qwen2.5:14b             | Ollama         | Reasoning, summarization, embeddings, vision | ~10GB VRAM       |
| **Intent** | DistilBERT (fine-tuned) | Pragmatics API | 4-class intent classification                | ~250MB CPU       |
| **Audio**  | Whisper large-v3        | Extractor API  | Audio transcription                          | ~3GB (on-demand) |

**Ollama handles:**

- LLM reasoning (Orchestrator)
- Text embeddings via `nomic-embed-text`
- Image descriptions via `llava` multimodal
- Text summarization

**Why DistilBERT stays separate:**

- 10ms classification vs 200-500ms LLM prompt
- CPU-only, doesn't compete for VRAM
- Already fine-tuned on intent-specific data

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Open-WebUI (8180)                             │
│                                 │                                       │
│                    ┌────────────┴──────────────┐                        │
│                    │           AJ              │                        │
│                    │        aj.filter.py       │                        │
│                    │    (inlet/outlet hooks)   │                        │
│                    └────────────┬──────────────┘                        │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
           ┌──────────────────────┼──────────────────────┐
           │                      │                      │
           ▼                      ▼                      ▼
    ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
    │ Pragmatics  │       │    Memory   │       │  Executor   │
    │    8001     │       │    8000     │       │    8005     │
    │             │       │             │       │             │
    │   Intent    │       │ Memory API  │       │ File Ops    │
    │  Classifier │       │ /save       │       │ /tool       │
    │             │       │ /search     │       │ /file       │
    └─────────────┘       └──────┬──────┘       └─────────────┘
                                 │
                                 ▼
                          ┌─────────────┐
                          │   Qdrant    │
                          │    6333     │
                          │             │
                          │ Vector DB   │
                          │ 768-dim     │
                          └─────────────┘
```

---

## Services

### 1. AJ Filter (filters/aj.filter.py)

The main entry point running inside Open-WebUI.

**Responsibilities:**

- Classify user intent via Pragmatics API
- Delegate all task intents to Orchestrator for reasoning
- Execute tool calls via Executor API
- **Feed results back to Orchestrator** for multi-step reasoning
- Search memory for relevant context
- Inject context and results into LLM conversation

**Flow (Multi-Step with Feedback Loop):**

```python
1. Classify intent via Pragmatics API
2. If task → Delegate to Orchestrator
3. LOOP (max 10 steps):
   a. Orchestrator reasons with history → returns tool + params
   b. Execute tool via Executor API
   c. Record result in step_history
   d. If tool == "complete" → break
4. Inject all accumulated results into context
```

**Key Feature: Feedback Loop**

The filter tracks execution results and feeds them back to the orchestrator:

- Orchestrator sees success/failure of each step
- Can adjust strategy based on errors
- Can gather information across multiple steps before acting

**Status Icons:**

| Icon | Meaning             |
| ---- | ------------------- |
| ✨   | Thinking/Processing |
| 🔍   | Scanning workspace  |
| 📖   | Reading files       |
| ✏️   | Editing files       |
| ⚙️   | Running code        |
| 💾   | Saving to memory    |
| 📚   | Memories found      |
| ✅   | Ready/Complete      |

---

### 2. Pragmatics API (Port 8001)

4-class intent classification using fine-tuned DistilBERT.

**Classes:**

| Class    | ID  | Description                   | Example                 |
| -------- | --- | ----------------------------- | ----------------------- |
| `casual` | 0   | General chat, no action       | "How are you?"          |
| `save`   | 1   | User sharing info to remember | "My name is Ian"        |
| `recall` | 2   | User asking about past info   | "What's my email?"      |
| `task`   | 3   | User requesting action        | "Add credits to readme" |

**Endpoint:**

```
POST /api/pragmatics/classify
Input:  { "text": "insert a credit in the readme" }
Output: { "intent": "task", "confidence": 0.99, "label": 3 }
```

### 3. Executor API (Port 8005)

Polyglot code execution and file operations with sandbox enforcement.

**File Operations:**

| Tool              | Method                    | Description           |
| ----------------- | ------------------------- | --------------------- |
| `read_file`       | `read(path)`              | Read file contents    |
| `write_file`      | `write(path, content)`    | Overwrite entire file |
| `replace_in_file` | `replace(path, old, new)` | Surgical find/replace |
| `insert_in_file`  | `insert(path, pos, text)` | Insert at position    |
| `append_to_file`  | `append(path, content)`   | Add to end of file    |
| `list_files`      | `list_dir(path)`          | Directory listing     |
| `scan_workspace`  | `scan(path, pattern)`     | Recursive glob search |

**scan_workspace Features:**

- **Gitignore support**: Respects `.gitignore` patterns via `pathspec` library
- **Pretty output**: Unified table with NAME, TYPE, SIZE, MODIFIED columns
- **Hidden files**: Skips dotfiles and `.git` by default
- **Human-readable sizes**: Shows KiB, MiB, etc.

**Positions for insert_in_file:**

- `start` — Beginning of file
- `end` — End of file
- `before` — Before anchor text
- `after` — After anchor text

**Endpoint:**

```
POST /api/execute/tool
Input: {
  "tool": "replace_in_file",
  "params": {
    "path": "/workspace/README.md",
    "old_text": "TODO",
    "new_text": "DONE"
  },
  "workspace_context": {
    "workspace_root": "/workspace",
    "cwd": "/workspace",
    "allow_file_write": true
  }
}
Output: { "success": true, "output": "Replaced 3 occurrence(s)" }
```

**Permission Checks:**

- `allow_file_write` — Required for write/replace/insert/append/delete
- `allow_shell_commands` — Required for shell execution
- `allow_code_execution` — Required for Python/Node/PowerShell

---

### 4. Memory API (Port 8000)

Semantic memory storage and retrieval.

**Components:**

- **Embedder:** Ollama `nomic-embed-text` (768-dim vectors)
- **Storage:** Qdrant vector database (collection: `user_memory_collection`)
- **Fact Extractor:** Pragmatics API `/api/pragmatics/entities` (spaCy NER for names, dates, etc.)

**REST Principles:**

- Each endpoint does ONE thing well
- Caller (AJ filter) decides intent via Pragmatics classification
- `/save` for `save` intents, `/search` for `recall` intents

**Endpoints:**

```
POST /api/memory/save
  - Caller decides when to save (no internal classification)
  - Extract structured facts (names, dates, etc.)
  - Embed with nomic-embed-text via Ollama
  - Upsert to Qdrant with full content + facts
  - Returns: { status, point_id, content_hash }

POST /api/memory/search
  - Embed query with nomic-embed-text
  - Search Qdrant filtered by user_id
  - Returns: list of { user_text, score, source_type, source_name }

POST /api/memory/summaries
  - Get memory summaries for a user

GET /api/agent
  - Serve filter source code (primary)

GET /api/aj/filter
  - Legacy endpoint → redirects to /api/agent
```

---

### 5. Extractor API (Port 8002)

Media-to-text extraction.

**Models:**

- **Image:** Ollama `llava` multimodal (via HTTP API to shared Ollama)
- **Audio:** Whisper large-v3 (loaded locally, GPU-accelerated)
- **PDF:** PyMuPDF (text extraction, no ML)

---

### 6. Orchestrator API (Port 8004)

Multi-step reasoning and task planning using **Qwen2.5:14b**.

**Endpoints:**

```
POST /api/orchestrate/set-workspace   # Set workspace context
POST /api/orchestrate/next-step       # Get next tool + params (with history)
POST /api/orchestrate/execute-batch   # Execute multiple steps
POST /api/orchestrate/run-task        # Full task execution with SSE
```

**Role:** The Orchestrator is the "brain" that decides which tool to use. All task intents are delegated to it - there are no hardcoded patterns in the filter.

**Model Choice: Qwen2.5:14b**

Selected for agentic reasoning because:

- Strong instruction-following capability
- Excellent JSON output formatting
- Good multi-step reasoning
- 32K context window for history tracking
- Balanced performance vs resource usage

**Feedback Loop:**

The orchestrator receives step history with each request:

```json
{
  "task": "user request",
  "history": [
    { "step_id": "step_1", "status": "success", "output": "..." },
    { "step_id": "step_2", "status": "failed", "error": "..." }
  ]
}
```

This allows the model to:

- Adapt strategy based on failures
- Use gathered information in subsequent steps
- Know when to complete vs continue

---

## Data Flow

### Task Request Flow (Always Delegate)

```
User: "list the files in this workspace"
                    │
                    ▼
┌─────────────────────────────────────────┐
│        aj.filter.py inlet()         │
│                                         │
│  1. Classify intent → "task" (99%)      │
│  2. Delegate to Orchestrator            │
│     (no hardcoded patterns)             │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│       Orchestrator API (8004)           │
│                                         │
│  POST /api/orchestrate/next-step        │
│  Reasoning: "User wants workspace tree" │
│  Returns: tool=scan_workspace, path="." │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         Executor API (8005)             │
│                                         │
│  POST /api/execute/tool                 │
│  - Loads .gitignore patterns            │
│  - Scans recursively                    │
│  - Returns pretty table:                │
│    PATH: /workspace/aj              │
│    TOTAL: 105 items (27 dirs, 78 files) │
│    NAME         TYPE  SIZE     MODIFIED │
│    filters      dir            2025-... │
│    README.md    file  8.3 KiB  2025-... │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│        Filter injects result            │
│                                         │
│  "### Workspace Files ###               │
│   <pretty table>                        │
│   ### End Workspace Files ###"          │
└─────────────────────────────────────────┘
                    │
                    ▼
         LLM presents the results
```

### Memory Search Flow

```
User: "What's my name?"
         │
         ▼
┌─────────────────────────────────────────┐
│  1. Classify intent → "recall"          │
│  2. Search memory API                   │
│     query: "what's my name"             │
│     top_k: 5                            │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         Qdrant Search                   │
│                                         │
│  Embed query → 768-dim vector           │
│  Cosine similarity > 0.35               │
│  Filter by user_id                      │
│  Return: "My name is Ian" (score: 0.82) │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Context injected:                      │
│  "### Memories ###                      │
│   - My name is Ian                      │
│   ### End Memories ###"                 │
└─────────────────────────────────────────┘
         │
         ▼
    LLM: "Your name is Ian"
```

---

## Configuration

### Environment Variables

| Variable                      | Service               | Default               | Purpose                         |
| ----------------------------- | --------------------- | --------------------- | ------------------------------- |
| `HOST_WORKSPACE_PATH`         | Orchestrator/Executor | `C:/Code`             | Host directory for /workspace   |
| `OLLAMA_HOST`                 | Memory/Extractor/Orch | `http://ollama:11434` | Ollama server URL               |
| `OLLAMA_MODEL`                | Orchestrator/Memory   | `qwen2.5:14b`         | LLM for reasoning/summarization |
| `EMBEDDING_MODEL`             | Memory API            | `nomic-embed-text`    | Ollama embedding model          |
| `IMAGE_MODEL`                 | Extractor             | `llava`               | Ollama vision model             |
| `WHISPER_MODEL`               | Extractor             | `large-v3`            | Audio transcription model       |
| `QDRANT_HOST`                 | Memory API            | `qdrant`              | Vector DB hostname              |
| `QDRANT_PORT`                 | Memory API            | `6333`                | Vector DB port                  |
| `CLASSIFIER_MODEL`            | Pragmatics            | `distilbert_intent`   | Intent model name               |
| `INTENT_CONFIDENCE_THRESHOLD` | Pragmatics            | `0.50`                | Min confidence for intent       |
| `PRAGMATICS_HOST`             | Memory API            | `pragmatics_api`      | Intent classifier hostname      |
| `PRAGMATICS_PORT`             | Memory API            | `8001`                | Intent classifier port          |

### Docker Compose Services

```yaml
services:
  memory_api: 8000 # Memory + Filter serving
  pragmatics_api: 8001 # Intent classification
  extractor_api: 8002 # Media extraction (GPU)
  orchestrator_api: 8004 # Task planning
  executor_api: 8005 # File ops + code execution
  qdrant: 6333 # Vector database
  ollama: 11434 # LLM inference
  open-webui: 8180 # Chat UI
```

---

## File Structure

```
aj.westerfield.cloud/
├── docker-compose.yaml
├── ARCHITECTURE.md
├── filters/
│   └── aj.filter.py          # Main Open-WebUI filter
├── layers/
│   ├── memory/
│   │   ├── main.py               # FastAPI app
│   │   ├── api/memory.py         # /save, /search endpoints
│   │   └── services/
│   │       ├── embedder.py       # nomic-embed-text via Ollama
│   │       ├── qdrant_client.py  # Qdrant connection
│   │       ├── fact_extractor.py # Entity extraction via Pragmatics
│   │       └── summarizer.py     # LLM summarization via Ollama
│   ├── pragmatics/
│   │   ├── server.py             # FastAPI app
│   │   ├── services/classifier.py # DistilBERT 4-class
│   │   └── static/distilbert_intent/  # Trained model
│   ├── extractor/
│   │   ├── main.py
│   │   └── services/
│   │       ├── image_extractor.py  # LLaVA/Florence
│   │       └── audio_extractor.py  # Whisper
│   ├── orchestrator/
│   │   ├── main.py
│   │   └── services/
│   │       ├── reasoning_engine.py
│   │       └── task_planner.py
│   └── executor/
│       ├── main.py
│       ├── api/executor.py       # /tool endpoint
│       └── services/
│           ├── file_handler.py   # read/write/replace/insert/append
│           ├── polyglot_handler.py # Python/Node/PowerShell
│           └── shell_handler.py
└── .github/
    └── copilot-instructions.md
```

---

## Security

### Workspace Sandbox

- All file operations validate paths against `workspace_root`
- Paths outside workspace are rejected
- Write operations require explicit `allow_file_write: true`

### Permission Flags

```python
class WorkspaceContext:
    workspace_root: str       # Sandbox boundary
    cwd: str                  # Current directory
    allow_file_write: bool    # Enable write operations
    allow_shell_commands: bool # Enable shell execution
    allow_code_execution: bool # Enable code runners
    allowed_languages: List[str] # Permitted languages
```

---

## Development

### Filter Sync

After editing `filters/aj.filter.py`, sync to Open-WebUI:

```powershell
# Push filter to Open-WebUI (requires session login)
python -c @"
import requests
s = requests.Session()
# Login to get session token
s.post('http://localhost:8180/api/v1/auths/signin', json={
    'email': open('secrets/webui_admin_username.txt').read().strip(),
    'password': open('secrets/webui_admin_password.txt').read().strip()
})
# Push filter (use utf-8-sig to strip BOM)
f = open('filters/aj.filter.py', encoding='utf-8-sig').read()
r = s.post('http://localhost:8180/api/v1/functions/id/aj/update', json={
    'id': 'aj', 'name': 'AJ', 'content': f,
    'meta': {'description': 'AJ Filter'}
})
print(r.status_code, r.text[:100] if r.text else '')
"@
```

### Rebuild Services

```powershell
# Rebuild executor after code changes
docker compose build --no-cache executor_api
docker compose up -d executor_api

# Rebuild all
docker compose up -d --build
```

### Test Endpoints

```powershell
# Intent classification
Invoke-RestMethod -Uri 'http://localhost:8001/api/pragmatics/classify' `
  -Method Post -ContentType 'application/json' `
  -Body '{"text":"add credits to readme"}'

# File append
Invoke-RestMethod -Uri 'http://localhost:8005/api/execute/tool' `
  -Method Post -ContentType 'application/json' `
  -Body (@{
    tool='append_to_file'
    params=@{path='/workspace/test.txt';content='Hello'}
    workspace_context=@{workspace_root='/workspace';cwd='/workspace';allow_file_write=$true}
  } | ConvertTo-Json -Depth 5)

# Memory search
Invoke-RestMethod -Uri 'http://localhost:8000/api/memory/search' `
  -Method Post -ContentType 'application/json' `
  -Body '{"user_id":"test","query_text":"my name","top_k":5}'
```
