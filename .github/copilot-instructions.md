# Mesosync (AJ) Copilot Instructions

## System Overview

Mesosync is a **Knowledge-centric AI platform** for Open-WebUI. The goal is to accumulate knowledge about workspaces, systems, and patterns — then recall that knowledge when relevant.

### Naming

| Name            | Role                                                                                        |
| --------------- | ------------------------------------------------------------------------------------------- |
| **AJ**          | User-facing persona (Open-WebUI filter only)                                                |
| **Mesosync**    | Agent coordination backbone — discovers, authenticates, and orchestrates FunnelCloud agents |
| **FunnelCloud** | .NET 8 distributed execution agents deployed on user machines                               |
| **Knowledge**   | The accumulated understanding stored in Qdrant                                              |

**Request flow:** User → `aj.filter.py` (Open-WebUI) → Pragmatics (intent) → Orchestrator (reasoning + execution) → Response

## Architecture Principles

- **Knowledge accumulation** — System learns about workspaces and recalls that knowledge later
- **Orchestrator owns all reasoning** — Filter routes by intent but NEVER hardcodes tool selection patterns
- **Executor merged into Orchestrator** — No HTTP hop; `tool_dispatcher.py` routes to singleton handlers
- **External state tracking** — `workspace_state.py` maintains ground truth, NOT the LLM (prevents drift)
- **Verbatim output contract** — Tools produce raw output; LLM must show it unchanged before any commentary

## Service Ports

| Service            | Port | Purpose                               |
| ------------------ | ---- | ------------------------------------- |
| `memory_api`       | 8000 | Semantic memory (Qdrant + embeddings) |
| `pragmatics_api`   | 8001 | 4-class DistilBERT intent classifier  |
| `extractor_api`    | 8002 | Media extraction (LLaVA, Whisper)     |
| `orchestrator_api` | 8004 | Reasoning engine + tool execution     |

## Key Files

- [filters/aj.filter.py](../filters/aj.filter.py) — Open-WebUI filter (lives in DB, sync via API)
- [layers/orchestrator/services/tool_dispatcher.py](../layers/orchestrator/services/tool_dispatcher.py) — Unified tool routing (DRY)
- [layers/orchestrator/services/reasoning_engine.py](../layers/orchestrator/services/reasoning_engine.py) — LLM coordination, `<think>` parsing
- [layers/orchestrator/services/workspace_state.py](../layers/orchestrator/services/workspace_state.py) — External state manager
- [layers/pragmatics/static/examples/](../layers/pragmatics/static/examples/) — Intent classifier training data

## Developer Workflows

### Rebuild after code changes

```powershell
docker compose up -d --build orchestrator_api   # Single service
docker compose up -d --build                    # All services
```

### Sync filter to Open-WebUI (filter stored in DB, not mounted)

```powershell
$apiKey = (Get-Content "secrets/webui_admin_api_key.txt" -Raw).Trim()
python -c "import requests; f=open('filters/aj.filter.py',encoding='utf-8-sig').read(); r=requests.post('http://localhost:8180/api/v1/functions/id/api/update', headers={'Authorization':'Bearer $apiKey'}, json={'id':'api','name':'AJ','content':f,'meta':{'toggle':True}}, timeout=10); print(r.status_code)"
```

### Rebuild base images (when requirements.txt changes)

```powershell
.\scripts\build-base-images.ps1 -Services "memory","pragmatics" -Force
```

### Retrain intent classifier

```powershell
cd layers/pragmatics/static
python train_intent_classifier.py
# Then rebuild: docker compose up -d --build pragmatics_api
```

## Code Patterns

### Adding a new tool

1. Add handler method in appropriate `*_handler.py` (file/shell/polyglot)
2. Register in `tool_dispatcher.py` dispatch table
3. Add to `AVAILABLE_TOOLS` in `reasoning_engine.py`
4. Add status icon mapping in `aj.filter.py` `TOOL_ICONS`

### Workspace state updates

```python
# After tool execution, update state (not LLM memory)
from services.workspace_state import get_workspace_state
state = get_workspace_state()
state.update_from_scan_result(output)  # Parses and caches file metadata
state.ledger.extract_value("ip_address", "192.168.1.1")  # Quick reference
```

### Intent classifier training data

Add examples to `layers/pragmatics/static/examples/{intent}_examples.py`:

```python
# task_examples.py
TASK_EXAMPLES = [
    "list files in the workspace",
    "which files did you find?",  # Follow-up questions are TASK intent
]
```

## Conventions

- **File edits**: Prefer `replace_in_file`, `insert_in_file`, `append_to_file` over `write_file`
- **Shell commands**: Tokenized via `shlex.split()`, never `shell=True`
- **Streaming**: Orchestrator uses SSE; filter consumes and relays status events
- **State injection**: Workspace state formatted into LLM prompt, not stored in conversation history
- **Anti-jargon**: LLM must never mention tool names (`scan_workspace`) to users; use natural language

## FunnelCloud (Planned)

Distributed execution agents for machines outside the Docker environment.

- **Tech stack**: .NET 8 Core, PowerShell Core (`System.Management.Automation`)
- **Trust**: mTLS + build-time CA fingerprint pinning (not UUID — can be stolen)
- **Discovery**: UDP broadcast per-conversation, lazy re-discover on agent failure
- **Credentials**: Session + Agent ID scoped, try-then-elevate on permission failure
- **Auth fallback**: `https://auth.aj.westerfield.cloud/agent/{agent_id}` for credential input
- **Source**: `FunnelCloud/` directory (private, gitignored) — separate private repo

See [docs/FunnelCloud-Design.md](../docs/FunnelCloud-Design.md) for full design.

## Testing Endpoints

```powershell
# Intent classification
Invoke-RestMethod -Uri 'http://localhost:8001/api/pragmatics/classify' -Method Post -ContentType 'application/json' -Body '{"text":"add credits to readme"}'

# Orchestrator health
Invoke-RestMethod -Uri 'http://localhost:8004/health'

# Memory search
Invoke-RestMethod -Uri 'http://localhost:8000/api/memory/search' -Method Post -ContentType 'application/json' -Body '{"user_id":"test","query_text":"my name","top_k":5}'
```
