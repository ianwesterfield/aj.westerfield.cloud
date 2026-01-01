# Mesosync System Overview

> **Knowledge-Centric AI Infrastructure**

```mermaid
flowchart TB
    subgraph UserLayer["User Layer"]
        User["👤 User"]
        OpenWebUI["Open-WebUI<br/>AJ Persona"]
    end

    subgraph MesosyncCore["Mesosync Core (Docker)"]
        direction TB

        subgraph Routing["Intent Routing"]
            Filter["aj.filter.py"]
            Pragmatics["Pragmatics<br/>Intent Classifier"]
        end

        subgraph Reasoning["Reasoning Layer"]
            Orchestrator["Orchestrator<br/>ReasoningEngine"]
            State["WorkspaceState<br/>Ground Truth"]
        end

        subgraph Execution["Execution Layer"]
            Dispatcher["ToolDispatcher"]
            FileHandler["FileHandler"]
            ShellHandler["ShellHandler"]
            PolyglotHandler["PolyglotHandler"]
        end

        subgraph Knowledge["Knowledge Layer"]
            Memory["Memory API"]
            Qdrant[("Qdrant<br/>Vector DB")]
        end

        subgraph Extraction["Extraction Layer"]
            Extractor["Extractor API"]
            LLaVA["LLaVA<br/>Vision"]
            Whisper["Whisper<br/>Audio"]
        end
    end

    subgraph FunnelCloudLayer["FunnelCloud Agents (Planned)"]
        direction LR
        Discovery["Discovery<br/>UDP Broadcast"]

        Agent1["🖥️ dev-workstation<br/>Windows"]
        Agent2["🐧 build-server<br/>Linux"]
        Agent3["📦 nas-server<br/>TrueNAS"]
    end

    subgraph Infrastructure["Infrastructure"]
        Ollama["Ollama<br/>LLM Inference"]
        Workspace[("Workspace<br/>Mounted Volume")]
        AuthEndpoint["auth.aj.westerfield.cloud<br/>Credential Input"]
    end

    %% User flow
    User --> OpenWebUI
    OpenWebUI --> Filter
    Filter --> Pragmatics
    Pragmatics --> Filter

    %% Intent routing
    Filter -->|"task"| Orchestrator
    Filter -->|"save/recall"| Memory

    %% Orchestrator flow
    Orchestrator --> State
    Orchestrator --> Dispatcher
    Orchestrator --> Ollama
    Orchestrator -->|"patterns"| Memory

    %% Tool execution
    Dispatcher --> FileHandler
    Dispatcher --> ShellHandler
    Dispatcher --> PolyglotHandler
    FileHandler --> Workspace
    ShellHandler --> Workspace

    %% Knowledge flow
    Memory --> Qdrant

    %% Extraction
    Extractor --> LLaVA
    Extractor --> Whisper

    %% FunnelCloud (planned)
    Orchestrator -.->|"planned"| Discovery
    Discovery -.-> Agent1
    Discovery -.-> Agent2
    Discovery -.-> Agent3
    Agent1 -.->|"mTLS"| Orchestrator
    Agent2 -.->|"mTLS"| Orchestrator
    Agent3 -.->|"mTLS"| Orchestrator

    %% Auth fallback
    Agent1 -.->|"elevation required"| AuthEndpoint
    Agent2 -.->|"elevation required"| AuthEndpoint
    Agent3 -.->|"elevation required"| AuthEndpoint

    style Knowledge fill:#e3f2fd
    style FunnelCloudLayer fill:#fff8e1,stroke-dasharray: 5 5
    style AuthEndpoint fill:#ffebee
```

## The Goal: Knowledge

The entire system exists to serve one purpose: **accumulate and recall knowledge**.

| Layer                  | Knowledge Contribution                                    |
| ---------------------- | --------------------------------------------------------- |
| **Memory API**         | Stores facts, preferences, and context from conversations |
| **WorkspaceState**     | Tracks file structure, project types, observations        |
| **FunnelCloud Agents** | Learn about remote systems, software, capabilities        |
| **Qdrant**             | Persists all knowledge for semantic recall                |

When a user asks "What's in my project?" or "What servers do I have?", the system should recall — not re-discover.

## Naming Quick Reference

| Name            | What It Is                | Where It Lives                   |
| --------------- | ------------------------- | -------------------------------- |
| **AJ**          | User-facing persona       | Open-WebUI chat interface        |
| **Mesosync**    | Coordination backbone     | Docker services (Python/FastAPI) |
| **FunnelCloud** | Distributed agents        | User machines (.NET 8)           |
| **Knowledge**   | Accumulated understanding | Qdrant vector database           |

## Service Ports

| Port  | Service          | Purpose                                    |
| ----- | ---------------- | ------------------------------------------ |
| 8000  | memory_api       | Semantic memory (Qdrant + embeddings)      |
| 8001  | pragmatics_api   | Intent classification (4-class DistilBERT) |
| 8002  | extractor_api    | Media extraction (LLaVA, Whisper)          |
| 8004  | orchestrator_api | Reasoning engine + tool execution          |
| 6333  | qdrant           | Vector database                            |
| 11434 | ollama           | LLM inference                              |
| 8180  | open-webui       | Chat UI                                    |

## Data Flows

### Task Execution (Current)

```mermaid
sequenceDiagram
    participant U as User
    participant F as Filter
    participant P as Pragmatics
    participant O as Orchestrator
    participant D as ToolDispatcher
    participant W as Workspace
    participant M as Memory

    U->>F: "List files in my project"
    F->>P: Classify intent
    P-->>F: task (0.95)

    F->>O: POST /run-task (SSE)
    O->>O: Generate step via LLM
    O->>D: dispatch("scan_workspace", {path: "."})
    D->>W: List directory
    W-->>D: File listing
    D-->>O: Result

    O-->>F: SSE: status, result
    O->>M: Save workspace knowledge
    F-->>U: Display results
```

### Knowledge Recall

```mermaid
sequenceDiagram
    participant U as User
    participant F as Filter
    participant P as Pragmatics
    participant M as Memory
    participant Q as Qdrant

    U->>F: "What's in my aj project?"
    F->>P: Classify intent
    P-->>F: recall (0.88)

    F->>M: POST /search
    M->>Q: Vector search (768-dim)
    Q-->>M: Workspace knowledge (0.82 similarity)
    M-->>F: Retrieved context

    F->>F: Inject into LLM prompt
    F-->>U: "Your aj.westerfield.cloud project has..."
```

### FunnelCloud Execution (Planned)

```mermaid
sequenceDiagram
    participant U as User
    participant O as Orchestrator
    participant D as Discovery
    participant A as Agent: build-server
    participant Auth as auth.aj.westerfield.cloud
    participant CC as Credential Cache

    U->>O: "Deploy to build server"
    O->>D: Discover agents (UDP broadcast)
    D->>A: Who's there?
    A-->>D: {capabilities, cert_fingerprint}
    D-->>O: [build-server] available

    O->>A: Execute: apt install docker (mTLS)
    A-->>O: ELEVATION_REQUIRED

    O-->>U: "🔐 Need credentials"
    O-->>U: "[Click to authenticate](https://auth.aj...)"

    U->>Auth: Open link
    Auth-->>U: Credential form
    U->>Auth: Submit sudo password
    Auth->>CC: Store (session + agent scoped)

    O->>A: Retry with credentials
    A->>A: sudo apt install docker
    A-->>O: Success
    O-->>U: "Docker installed"
```

## Related Documentation

- [ARCHITECTURE.md](../ARCHITECTURE.md) — Detailed service architecture
- [FunnelCloud-Design.md](FunnelCloud-Design.md) — FunnelCloud agent design
- [.github/copilot-instructions.md](../.github/copilot-instructions.md) — Developer guidance
