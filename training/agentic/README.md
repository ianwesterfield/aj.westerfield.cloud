# Agentic Training Pipeline

## Overview

Train AJ to use the "All You Need is Bash" tool philosophy:

```
User: "List files in the project"
AJ: → bash: ls -la /path/to/project

User: "Restart nginx on webprod01"
AJ: → remote_bash: (webprod01) sudo systemctl restart nginx

User: "Deploy to all prod servers"
AJ: → remote_bash_all: (prod-*) ./deploy.sh
```

## Tool Schema

AJ uses 6 core tools:

| Tool              | Purpose                   | Example                 |
| ----------------- | ------------------------- | ----------------------- |
| `bash`            | Local command execution   | `ls -la`, `docker ps`   |
| `remote_bash`     | Single agent execution    | Execute on `webprod01`  |
| `remote_bash_all` | Multi-agent execution     | Execute on all `prod-*` |
| `list_agents`     | Discover available agents | Show FunnelCloud agents |
| `think`           | Reasoning step (internal) | Plan before execution   |
| `complete`        | Task completion signal    | Mark task finished      |

## Data Sources

### 1. Glaive Function-Calling (~113K examples)

Downloaded automatically by `train_pipeline.py`.

### 2. AgentInstruct (~1.8M examples)

Planning and execution patterns from THUDM's dataset.

### 3. Toucan-1.5M (~519K examples)

Real MCP tool-use trajectories from Agent-Ark:

- Synthesized from 495 real-world Model Context Protocols
- 2,000+ tools across diverse categories
- Quality-assessed with LLM-as-judge

### 4. Custom AJ Data (5K+ examples)

Domain-specific training from 43+ generators in `../data/`.

### 5. Shutdown Safety Trajectories (20 examples)

Carefully crafted examples for target disambiguation and confirmation.

## Quick Start

The main training pipeline handles everything:

```bash
cd /mnt/c/Code/aj.westerfield.cloud/training
source venv/bin/activate

# Full pipeline with agentic datasets
python scripts/train_pipeline.py -y
```

### Manual Data Generation

```bash
# Generate shutdown safety trajectories (uses Claude API)
python generators/generate_trajectories.py --count 20 --category shutdown

# Load open datasets (Toucan, Glaive, etc.)
python generators/generate_trajectories.py --load-dataset glaive --sample 5000

# Validate generated data
python utils/validate_dataset.py --data-dir data/
```

## Data Format

Training examples use ChatML format with tool calls:

```json
{
  "messages": [
    { "role": "system", "content": "You are AJ..." },
    { "role": "user", "content": "List running containers" },
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        { "name": "bash", "arguments": { "command": "docker ps" } }
      ]
    },
    { "role": "tool", "content": "CONTAINER ID  IMAGE  ..." },
    { "role": "assistant", "content": "Here are the running containers..." }
  ]
}
```

## Cost (Local Training)

| Component   | Cost     | Notes                                       |
| ----------- | -------- | ------------------------------------------- |
| Datasets    | Free     | Open-source (Glaive, AgentInstruct, Toucan) |
| Hardware    | ~$0      | RTX 4090 (already owned)                    |
| Time        | 24-48h   | With full datasets (~2.4M examples)         |
| Electricity | ~$10     | 450W × 48h                                  |
| **Total**   | **~$10** | Just electricity                            |

## Data Format Specs

See `schemas/` for JSON schemas and `generators/README.md` for open dataset guides.
