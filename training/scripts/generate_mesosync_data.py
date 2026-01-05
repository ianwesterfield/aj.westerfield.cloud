"""
Mesosync/AJ Workspace Knowledge Generator

Generates training data from the actual Mesosync architecture so the model
understands the user's specific project structure, components, and patterns.

This is DOMAIN-SPECIFIC training - teaching the model about THIS workspace.
"""

import json
import random
from pathlib import Path
from typing import List, Dict

# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """You are AJ, an expert AI assistant with deep knowledge of the Mesosync platform architecture. You understand the full system including the AJ filter, orchestrator, memory service, pragmatics intent classifier, and FunnelCloud distributed agents. You help with development, debugging, and extending the Mesosync platform."""

# =============================================================================
# MESOSYNC ARCHITECTURE KNOWLEDGE
# =============================================================================

ARCHITECTURE_KNOWLEDGE = [
    {
        "question": "What is Mesosync and what problem does it solve?",
        "answer": "Mesosync is a knowledge-centric AI platform for Open-WebUI that solves the 'AI amnesia' problem - traditional AI assistants forget everything between conversations. Mesosync accumulates knowledge about your workspace, patterns, and history in a semantic vector database (Qdrant), then recalls that knowledge when relevant. It plans intelligently, shows progress during multi-step tasks, adapts based on feedback, and improves with every interaction. The core principle: an agentic AI assistant that remembers you as you go."
    },
    {
        "question": "What is AJ and how does it relate to Mesosync?",
        "answer": "AJ (Agent Journalist) is the user-facing persona of Mesosync. It's implemented as an Open-WebUI filter (aj.filter.py, ~1364 lines) that sits between the user and the LLM. AJ handles intent classification, routes to appropriate services, manages semantic memory, orchestrates workspace operations, and provides a streaming UX. The naming hierarchy: AJ (user-facing filter) → Mesosync (agent coordination backbone) → FunnelCloud (distributed agents) → Knowledge (Qdrant vectors)."
    },
    {
        "question": "What are the main components of the Mesosync architecture?",
        "answer": "Mesosync has 6 main services: 1) AJ Filter (Open-WebUI entry point, intent routing), 2) Pragmatics API (port 8001, DistilBERT 4-class intent classifier), 3) Orchestrator API (port 8004, reasoning engine + tool dispatch), 4) Memory API (port 8000, semantic storage with Qdrant), 5) Extractor API (port 8002, media processing with LLaVA/Whisper), 6) Qdrant (port 6333/5100, vector database). All services communicate over the webtools_network Docker network."
    },
    {
        "question": "How does intent classification work in Mesosync?",
        "answer": "All user input flows through a 4-class DistilBERT intent classifier in the Pragmatics API. Classes: 'casual' (chat, no tools), 'save' (store in semantic memory), 'recall' (search memory), 'task' (orchestrate multi-step work). The model is 4M parameters, achieves <100ms latency and 95%+ accuracy. Key principle: NO hardcoded pattern matching in the filter - all classification is pure ML. To add new intents, add training data to layers/pragmatics/static/examples/, then retrain."
    },
    {
        "question": "What is the request flow through Mesosync?",
        "answer": "Request flow: User (Open-WebUI) → AJ Filter (aj.filter.py) → Pragmatics API (classify intent) → Based on intent: casual→LLM direct, save→Memory API store, recall→Memory API search, task→Orchestrator API. For tasks: Orchestrator (ReasoningEngine) → WorkspaceState (ground truth) → ToolDispatcher → Handlers (File/Shell/Polyglot/gRPC) → Results streamed via SSE → Filter displays verbatim → User sees response."
    },
    {
        "question": "What is the Orchestrator and what does it do?",
        "answer": "The Orchestrator (port 8004) is the reasoning engine and brain of Mesosync. Key components: ReasoningEngine (LLM coordination, <think> block parsing), TaskPlanner (decomposes intents into steps), ParallelExecutor (asyncio.gather for batches), WorkspaceState (external ground truth), ToolDispatcher (unified routing to handlers), MemoryConnector (pattern retrieval/storage). The Orchestrator decides WHAT tools to use based on intent, workspace state, and history - the filter NEVER hardcodes tool selection."
    },
    {
        "question": "How does the ToolDispatcher work?",
        "answer": "ToolDispatcher (tool_dispatcher.py, ~536 lines) is the unified routing layer for all tool execution. It routes to singleton handlers: FileHandler (read/write/scan), ShellHandler (PowerShell/Bash), PolyglotHandler (Python/Node/Go), gRPCClient (FunnelCloud remote agents). Key principle: one dispatcher, many handlers. To add a new tool: 1) Implement handler, 2) Register in dispatcher dispatch table, 3) Add to AVAILABLE_TOOLS in reasoning_engine.py. No if/then pattern matching needed."
    },
    {
        "question": "What is WorkspaceState and why is it important?",
        "answer": "WorkspaceState (workspace_state.py) maintains external ground truth about the workspace. Critical principle: workspace state is authoritative, NOT the LLM's guess. This prevents 'LLM drift' where the model hallucinates or uses outdated training data. When asked 'what files exist?', the Orchestrator scans the actual filesystem, not guesses from training. WorkspaceState tracks: file metadata, recent operations, extracted values via ledger.extract_value(). This is knowledge accumulation in action."
    },
    {
        "question": "What is FunnelCloud?",
        "answer": "FunnelCloud extends Mesosync beyond Docker containers to any machine the user controls. It's a distributed agent system built in .NET 8 with PowerShell Core execution. Trust model: mTLS + fingerprint pinning (cryptographic identity, not UUIDs), build-time CA embedding, certificate revocation. Discovery: per-conversation UDP broadcast, lazy re-discovery on failure, capability advertisement. Communication: gRPC over mTLS. Goal: build a Knowledge Network where AJ can discover, execute, and accumulate knowledge across the user's infrastructure."
    },
    {
        "question": "How does semantic memory work in Mesosync?",
        "answer": "Memory API (port 8000) provides semantic storage and retrieval via Qdrant vector database. When intent='save', the filter extracts facts/docs/notes and stores them with embeddings (sentence_transformers, 768-dim). When intent='recall', semantic search finds relevant memories based on meaning, not keywords. Each user has isolated memory. Over time, the system builds a knowledge graph: entity extraction, relationship mapping, pattern detection. The LLM recalls without re-scanning because knowledge persists."
    },
    {
        "question": "What is the Verbatim Output Contract?",
        "answer": "Critical principle: when ANY tool produces output (stdout, stderr, file reads), show the raw output FIRST in a fenced code block. Rules: 1) EXACTLY as received (no summarize, paraphrase, reformat, reorder, trim), 2) No interpretation BEFORE output (status lines OK, prose not), 3) AFTER output, MAY add brief commentary (max 3 lines) for next steps/errors/completion, 4) Multiple outputs in chronological order as separate blocks, 5) stdout first, then stderr. This ensures users see exactly what tools produced."
    },
    {
        "question": "Why does Mesosync use DistilBERT instead of the main LLM for intent classification?",
        "answer": "Using DistilBERT (4M params) vs Llama70B (70B params) for intent classification is intentional: 1) Latency: 50-100ms vs 500ms-2s, 2) VRAM: 2GB vs 40GB, 3) Specialization: purpose-built for classification vs generalist, 4) Cost: ~5x cheaper per request, 5) Separation: no single point of failure. DistilBERT achieves 95%+ accuracy on 4 classes. The principle: small model for small job beats big model for everything. Specialized tools for each job."
    },
]

# =============================================================================
# SERVICE-SPECIFIC KNOWLEDGE
# =============================================================================

SERVICE_KNOWLEDGE = [
    {
        "question": "How do I start all Mesosync services?",
        "answer": "Run: docker compose up -d --build. This starts: ollama (11434), qdrant (6333/5100), memory_api (8000), pragmatics_api (8001), extractor_api (8002), orchestrator_api (8004). Verify with: docker compose ps. For single service rebuild: docker compose up -d --build orchestrator_api. Services connect via webtools_network (external Docker network)."
    },
    {
        "question": "How do I sync the AJ filter to Open-WebUI?",
        "answer": "The filter lives in Open-WebUI's database, not Docker. Sync with PowerShell:\n$apiKey = (Get-Content 'secrets/webui_admin_api_key.txt' -Raw).Trim()\n$filterCode = Get-Content 'filters/aj.filter.py' -Encoding utf-8\n$body = @{ id = 'api'; name = 'AJ'; content = $filterCode; meta = @{ toggle = $true } } | ConvertTo-Json\nInvoke-RestMethod -Uri 'http://localhost:8180/api/v1/functions/id/api/update' -Method Post -Headers @{ Authorization = \"Bearer $apiKey\" } -ContentType 'application/json' -Body $body"
    },
    {
        "question": "How do I retrain the intent classifier?",
        "answer": "1) Add examples to layers/pragmatics/static/examples/{intent}_examples.py (e.g., TASK_EXAMPLES = ['list files', 'find python files']). 2) Run training: cd layers/pragmatics/static && python train_intent_classifier.py (takes 2-5 minutes). 3) Rebuild service: docker compose up -d --build pragmatics_api. New intents require training data, not code changes - this is ML-driven classification."
    },
    {
        "question": "How do I test the Pragmatics intent classifier?",
        "answer": "PowerShell test:\n$body = @{ text = 'save this to memory' } | ConvertTo-Json\nInvoke-RestMethod -Uri 'http://localhost:8001/api/pragmatics/classify' -Method Post -ContentType 'application/json' -Body $body\nExpected response: {intent: 'save', confidence: 0.87}. Health check: Invoke-RestMethod http://localhost:8001/health"
    },
    {
        "question": "How do I test the Memory API?",
        "answer": "Search memory:\n$query = @{ user_id = 'test'; query_text = 'my name'; top_k = 5 } | ConvertTo-Json\nInvoke-RestMethod -Uri 'http://localhost:8000/api/memory/search' -Method Post -ContentType 'application/json' -Body $query\nCheck Qdrant: Invoke-RestMethod http://localhost:6333/health and http://localhost:6333/collections. Qdrant UI at http://localhost:5100."
    },
    {
        "question": "How do I add a new tool to the Orchestrator?",
        "answer": "1) Implement handler in appropriate service file: file ops → file_handler.py, shell → shell_handler.py, code → polyglot_handler.py, remote → grpc_client.py. 2) Register in tool_dispatcher.py dispatch table: HANDLERS = {'new_tool': NewHandler()}. 3) Add to AVAILABLE_TOOLS in reasoning_engine.py. 4) Document in architecture diagram. No if/then logic needed - dispatcher routes by name."
    },
    {
        "question": "What's the logging architecture in Mesosync?",
        "answer": "Centralized logging in layers/shared/logging_utils.py (364 lines). Components: LogLevel enum (20 values: SUCCESS, RUNNING, ERROR, etc.), LogCategory enum (16 values: FILTER, ORCHESTRATOR, etc.), ICON_MAP (70+ entries mapping (category,level)→emoji). Functions: log_message(), create_status_dict(), get_icon(). Three copies exist: shared/ (source of truth), filters/logging_utils.py (compatibility), aj.filter.py inline (Open-WebUI requires self-contained code)."
    },
    {
        "question": "What are the key files in the Mesosync codebase?",
        "answer": "Key files: filters/aj.filter.py (1364 lines, Open-WebUI entry point), layers/shared/logging_utils.py (364 lines, centralized logging), layers/orchestrator/services/tool_dispatcher.py (536 lines, unified routing), layers/orchestrator/services/reasoning_engine.py (LLM coordination), layers/orchestrator/services/workspace_state.py (ground truth), layers/pragmatics/services/classifier.py (DistilBERT intent), layers/memory/api/memory.py (semantic memory)."
    },
]

# =============================================================================
# DEVELOPMENT PATTERNS
# =============================================================================

DEVELOPMENT_PATTERNS = [
    {
        "question": "What's the correct way to use logging in Mesosync services?",
        "answer": "Import from shared:\nfrom shared.logging_utils import log_message, LogCategory, LogLevel, create_status_dict\n\nFor logging: msg = log_message('Processing files', LogCategory.ORCHESTRATOR, LogLevel.SCANNING)\nlogger.info(msg)  # Returns: '🔍 Processing files'\n\nFor event emitter (filter): await __event_emitter__(create_status_dict('Task complete', LogCategory.ORCHESTRATOR, LogLevel.SUCCESS, done=True))"
    },
    {
        "question": "How should I handle workspace state in the Orchestrator?",
        "answer": "Use workspace_state.py for external ground truth:\nfrom services.workspace_state import get_workspace_state\nstate = get_workspace_state()\nstate.update_from_scan_result(output)  # Parse file metadata from shell output\nvalue = state.ledger.extract_value('port', '8080')  # Quick lookups\nKey principle: workspace state is authoritative, LLM guesses are not. Always scan actual filesystem for current state."
    },
    {
        "question": "What are the naming conventions in Mesosync?",
        "answer": "Conventions: 1) Internal tool names (e.g., 'scan_workspace') → NEVER shown to users, 2) LLM-facing text → natural language ('look at your workspace files'), 3) Python variables → snake_case, 4) gRPC fields → camelCase, 5) Enums → always inherit from (str, Enum) for JSON serialization. Anti-pattern: exposing internal tool names to users."
    },
    {
        "question": "What's the tool output contract in Mesosync?",
        "answer": "Tools produce raw, unformatted output. The LLM MUST display tool output UNCHANGED before any commentary. Rule: 'Show the output, then explain'. Anti-pattern: editing tool output to look prettier. This ensures users see exactly what executed and can verify results. After showing verbatim output, brief commentary (max 3 lines) is allowed for next steps or error handling."
    },
    {
        "question": "How do I troubleshoot services not starting?",
        "answer": "Debug steps: 1) Check logs: docker compose logs -f orchestrator_api, 2) Verify network: docker network ls && docker network inspect webtools_network, 3) Rebuild: docker compose up -d --build, 4) Check port conflicts: netstat -ano | findstr :8004. Common issues: network not created (create webtools_network first), port already in use, volume mount permissions."
    },
    {
        "question": "How do I debug intent classification issues?",
        "answer": "Debug steps: 1) Test classification directly: Invoke-RestMethod http://localhost:8001/api/pragmatics/classify -Method Post -Body (@{text='test'} | ConvertTo-Json) -ContentType 'application/json'. 2) Check confidence score (should be >0.7 for reliable classification). 3) Review training examples in layers/pragmatics/static/examples/. 4) Retrain if needed. Common issue: new intent types need training data, not code patterns."
    },
]

# =============================================================================
# ARCHITECTURE PRINCIPLES
# =============================================================================

ARCHITECTURE_PRINCIPLES = [
    {
        "question": "What are the core architecture principles in Mesosync?",
        "answer": "5 core principles: 1) Knowledge First - accumulate and recall what the system learns, 2) Reasoning Owns Tools - Orchestrator decides execution, no hardcoded rules in filter, 3) Ground Truth Outside - workspace state is authoritative, not LLM, 4) Verbatim Output - tools produce raw output, LLM shows unchanged, 5) Specialization Over Generalization - small models for specific jobs beat big models for everything."
    },
    {
        "question": "Why does Mesosync separate the filter from the orchestrator?",
        "answer": "Separation of concerns: Filter (aj.filter.py) handles Open-WebUI integration, intent routing, and UX streaming. Orchestrator handles reasoning, tool selection, and execution. Benefits: 1) Filter stays simple (route by intent), 2) Orchestrator can evolve independently, 3) No hardcoded patterns in filter, 4) Clean HTTP/SSE boundary, 5) Easier testing. Anti-pattern: putting tool selection logic in the filter."
    },
    {
        "question": "What is 'external ground truth' and why does it matter?",
        "answer": "External ground truth means the workspace state is authoritative, not the LLM's training data or guesses. Traditional LLM: 'What files exist?' → guesses from training data → hallucinated/outdated info. Mesosync: 'What files exist?' → Orchestrator scans filesystem → actual state → accurate response. This prevents LLM drift where models confidently assert wrong information about the current workspace."
    },
    {
        "question": "Why use ML-based intent classification instead of regex patterns?",
        "answer": "ML (DistilBERT) advantages: 1) Handles synonyms and paraphrasing automatically, 2) No maintenance of pattern lists, 3) Generalizes to unseen phrasings, 4) Easy to extend with training data, 5) Confidence scores enable fallback logic. Regex/keyword patterns: brittle, require constant updates, miss edge cases, can't handle typos. Every new intent = training data, not code changes."
    },
    {
        "question": "How does Mesosync handle knowledge accumulation?",
        "answer": "Knowledge accumulation loop: 1) User interaction triggers task, 2) Orchestrator executes and observes results, 3) Results stored in semantic memory (Qdrant vectors), 4) Next request retrieves relevant context, 5) System improves over time. Example: first time 'What is project structure?' → full scan → stored. Next time → instant recall. Long-term: entity extraction, relationship mapping, pattern detection."
    },
]

# =============================================================================
# TROUBLESHOOTING SCENARIOS
# =============================================================================

TROUBLESHOOTING = [
    {
        "question": "Memory not persisting between restarts - how do I fix this?",
        "answer": "Check Qdrant persistence: 1) Verify volume mount in docker-compose.yaml: volumes: - C:/docker-data/qdrant/storage:/qdrant/storage. 2) Check Qdrant health: Invoke-RestMethod http://localhost:6333/health. 3) List collections: Invoke-RestMethod http://localhost:6333/collections. 4) Ensure graceful shutdown (stop_grace_period: 30s in compose). 5) Check for WAL corruption: QDRANT__STORAGE__OPTIMIZERS__FLUSH_INTERVAL_SEC=1 helps."
    },
    {
        "question": "Orchestrator not responding - how do I debug?",
        "answer": "Debug steps: 1) Check service: docker compose ps orchestrator_api. 2) View logs: docker compose logs -f orchestrator_api. 3) Test health: Invoke-RestMethod http://localhost:8004/health. 4) Check LLM warmup (may take minutes on first start). 5) Verify Ollama running: Invoke-RestMethod http://localhost:11434/api/tags. 6) Check network: docker network inspect webtools_network. Common: LLM warmup timeout, Ollama not ready."
    },
    {
        "question": "Intent classifier returning wrong intents - what should I check?",
        "answer": "Debug intent classification: 1) Test directly with known inputs: @{text='save this'} should return 'save'. 2) Check confidence score - below 0.5 is unreliable. 3) Review training examples in layers/pragmatics/static/examples/. 4) Ensure model is loaded: docker compose logs pragmatics_api. 5) Retrain with more diverse examples. 6) Check for class imbalance in training data. The model needs varied examples per intent."
    },
    {
        "question": "Filter not syncing to Open-WebUI - what's wrong?",
        "answer": "Filter sync issues: 1) Verify API key: Get-Content secrets/webui_admin_api_key.txt. 2) Check Open-WebUI URL (default http://localhost:8180). 3) Ensure filter toggle is enabled: meta = @{ toggle = $true }. 4) Check response from update API for error messages. 5) Verify filter ID matches ('api'). 6) Check Open-WebUI logs for Python syntax errors in filter code."
    },
    {
        "question": "Tool execution returning empty results - how do I troubleshoot?",
        "answer": "Empty tool results: 1) Check workspace path is set: POST /api/orchestrate/set-workspace. 2) Verify file permissions in container. 3) Check handler logs: docker compose logs orchestrator_api | grep -i handler. 4) Test handler directly (not through LLM). 5) Verify tool registered in AVAILABLE_TOOLS. 6) Check for shell command errors (stderr). 7) Ensure workspace mounted correctly in docker-compose.yaml volumes."
    },
]

# =============================================================================
# FUNNELCLOUD SPECIFIC
# =============================================================================

FUNNELCLOUD_KNOWLEDGE = [
    {
        "question": "What is the FunnelCloud trust model?",
        "answer": "FunnelCloud uses mTLS + fingerprint pinning for cryptographic identity. Build-time: 1) Generate CA (internal), 2) For each agent: generate keypair, sign with CA, 3) Bake cert + key + CA fingerprint into agent. Runtime: 1) TLS handshake, 2) Agent validates SHA256(server cert) == baked fingerprint, 3) Mesosync validates agent cert signed by our CA. Why not UUID? UUIDs can be stolen, private keys cannot. Each agent has unique cryptographic identity."
    },
    {
        "question": "How does FunnelCloud agent discovery work?",
        "answer": "Discovery is per-conversation, not continuous. Steps: 1) UDP broadcast at conversation start, 2) Agents respond with capabilities, 3) Orchestrator caches discovered agents for session, 4) Lazy re-discovery only when agent fails. Benefits: minimal network chatter, fresh discovery per session, graceful degradation. Agents advertise capabilities (what tools they support), Orchestrator selects best agent for each task."
    },
    {
        "question": "How do I generate certificates for FunnelCloud agents?",
        "answer": "Use scripts in FunnelCloud/scripts/: 1) Generate CA: .\\New-CACertificate.ps1 (creates ca.crt, ca.key, ca-fingerprint.txt). 2) Generate agent cert: .\\New-AgentCertificate.ps1 -AgentName 'dev-workstation' (signs with CA). 3) Copy to agent: ca-fingerprint.txt + agent.crt + agent.key. 4) Build agent with embedded certs. CA fingerprint is baked in at build time - cannot be changed at runtime."
    },
    {
        "question": "What's the FunnelCloud credential elevation model?",
        "answer": "Try-Then-Elevate: assume no elevation needed, prompt only when required. Flow: 1) Execute task with current permissions, 2) If access denied, check cached credentials for this agent+session, 3) If not cached, prompt user (via auth URL or inline), 4) Cache credentials for session. Scoped: credentials are session + agent scoped (not global). Fallback: https://auth.aj.westerfield.cloud/agent/{agent_id} for web-based auth."
    },
]

# =============================================================================
# CODE EXAMPLES
# =============================================================================

CODE_EXAMPLES = [
    {
        "question": "Show me how to implement a new handler for the Orchestrator",
        "answer": """Here's how to add a new tool handler:

```python
# In layers/orchestrator/services/handlers.py (or new file)
from shared.logging_utils import log_message, LogCategory, LogLevel

class CustomToolHandler:
    \"\"\"Handler for custom tool operations.\"\"\"
    
    async def execute(self, params: dict) -> dict:
        \"\"\"Execute the custom tool.\"\"\"
        action = params.get('action')
        target = params.get('target')
        
        log_message(f"Executing {action} on {target}", 
                   LogCategory.DISPATCHER, LogLevel.EXECUTING)
        
        # Your implementation here
        result = await self._do_work(action, target)
        
        return {
            'success': True,
            'output': result,
            'tool': 'custom_tool'
        }

# In tool_dispatcher.py, add to HANDLERS dict:
HANDLERS = {
    'file': FileHandler(),
    'shell': ShellHandler(),
    'custom_tool': CustomToolHandler(),  # Add here
}

# In reasoning_engine.py, add to AVAILABLE_TOOLS:
AVAILABLE_TOOLS = ['file', 'shell', 'polyglot', 'custom_tool']
```"""
    },
    {
        "question": "Show me how to add a new intent type to the classifier",
        "answer": """Add a new intent (e.g., 'schedule') to the Pragmatics classifier:

1. Create training examples in layers/pragmatics/static/examples/schedule_examples.py:
```python
SCHEDULE_EXAMPLES = [
    "remind me to check email at 3pm",
    "schedule a meeting for tomorrow",
    "set an alarm for 6am",
    "add this to my calendar",
    "when should I follow up on this?",
    "create a recurring task every Monday",
    # Add 50+ diverse examples for good accuracy
]
```

2. Update the training script to include new intent:
```python
# In train_intent_classifier.py
from examples.schedule_examples import SCHEDULE_EXAMPLES

INTENT_EXAMPLES = {
    'casual': CASUAL_EXAMPLES,
    'save': SAVE_EXAMPLES,
    'recall': RECALL_EXAMPLES,
    'task': TASK_EXAMPLES,
    'schedule': SCHEDULE_EXAMPLES,  # New intent
}
```

3. Retrain:
```powershell
cd layers/pragmatics/static
python train_intent_classifier.py
docker compose up -d --build pragmatics_api
```

4. Update filter routing in aj.filter.py to handle new intent."""
    },
    {
        "question": "Show me how to query semantic memory from the Orchestrator",
        "answer": """Query semantic memory using the memory connector:

```python
# In orchestrator service code
from services.memory_connector import MemoryConnector

async def retrieve_relevant_context(user_id: str, query: str) -> list:
    \"\"\"Retrieve relevant memories for the current task.\"\"\"
    connector = MemoryConnector()
    
    # Search semantic memory
    results = await connector.search(
        user_id=user_id,
        query_text=query,
        top_k=5,
        min_score=0.7  # Only high-relevance results
    )
    
    # Format for LLM context injection
    context_items = []
    for result in results:
        context_items.append({
            'content': result['payload']['text'],
            'score': result['score'],
            'metadata': result['payload'].get('metadata', {})
        })
    
    return context_items

# Usage in reasoning engine:
context = await retrieve_relevant_context(user_id, user_query)
if context:
    prompt = f\"\"\"Relevant context from memory:
{json.dumps(context, indent=2)}

User query: {user_query}\"\"\"
```"""
    },
]

# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def generate_architecture_examples() -> List[Dict]:
    """Generate architecture knowledge examples."""
    examples = []
    
    all_knowledge = (
        ARCHITECTURE_KNOWLEDGE + 
        SERVICE_KNOWLEDGE + 
        ARCHITECTURE_PRINCIPLES +
        FUNNELCLOUD_KNOWLEDGE
    )
    
    for item in all_knowledge:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"]
        })
    
    return examples

def generate_development_examples() -> List[Dict]:
    """Generate development pattern examples."""
    examples = []
    
    for item in DEVELOPMENT_PATTERNS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"]
        })
    
    return examples

def generate_troubleshooting_examples() -> List[Dict]:
    """Generate troubleshooting examples."""
    examples = []
    
    for item in TROUBLESHOOTING:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"]
        })
    
    return examples

def generate_code_examples() -> List[Dict]:
    """Generate code example training data."""
    examples = []
    
    for item in CODE_EXAMPLES:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"]
        })
    
    return examples


def main():
    """Generate all Mesosync workspace training data."""
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Generating Mesosync Workspace Knowledge Training Data")
    print("=" * 60)
    
    all_examples = []
    
    # Generate each category
    print("\n1. Generating architecture knowledge...")
    arch_examples = generate_architecture_examples()
    all_examples.extend(arch_examples)
    print(f"   Generated {len(arch_examples)} examples")
    
    print("\n2. Generating development patterns...")
    dev_examples = generate_development_examples()
    all_examples.extend(dev_examples)
    print(f"   Generated {len(dev_examples)} examples")
    
    print("\n3. Generating troubleshooting scenarios...")
    trouble_examples = generate_troubleshooting_examples()
    all_examples.extend(trouble_examples)
    print(f"   Generated {len(trouble_examples)} examples")
    
    print("\n4. Generating code examples...")
    code_ex = generate_code_examples()
    all_examples.extend(code_ex)
    print(f"   Generated {len(code_ex)} examples")
    
    # Shuffle for training
    random.shuffle(all_examples)
    
    # Save to JSONL
    output_file = output_dir / "mesosync_workspace.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"\nSaved {len(all_examples)} examples to {output_file}")
    
    print("\n" + "=" * 60)
    print("Mesosync Workspace Knowledge Generation Complete!")
    print("=" * 60)
    print(f"Total examples: {len(all_examples)}")
    print(f"  Architecture: {len(arch_examples)}")
    print(f"  Development: {len(dev_examples)}")
    print(f"  Troubleshooting: {len(trouble_examples)}")
    print(f"  Code examples: {len(code_ex)}")
    
    return all_examples


if __name__ == "__main__":
    main()
