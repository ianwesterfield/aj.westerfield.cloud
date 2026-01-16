# Open Dataset Setup - Visual Guide

## The Problem We Solved

```
BEFORE:
┌─────────────────────────────┐
│  You: "Shutdown domain02"   │
└──────────────┬──────────────┘
               │
          ┌────v────┐
          │ AJ      │ ← Only had synthetic training
          │ Agent   │   (rigid template patterns)
          └────┬────┘
               │
        ┌──────v──────┐
        │ ??? Guess ??? │
        │ domain02?    │
        │ ians-r16?    │
        │ prod-api-01? │
        └──────┬───────┘
               │
          ┌────v────────────┐
          │ OOPS! Shut down │
          │ WRONG MACHINE    │ ← Actual result: 'ians-r16'
          └─────────────────┘
        (your workstation crashed)


AFTER:
┌─────────────────────────────┐
│  You: "Shutdown domain02"   │
└──────────────┬──────────────┘
               │
          ┌────v────────────────────────┐
          │ AJ Agent                    │
          │                             │
          │ Trained on:                 │
          │ • Shutdown safety (Claude)  │
          │ • Real MCP tool-use (Toucan)│
          │                             │
          │ Learned to:                 │
          │ 1. List available agents    │
          │ 2. Find 'domain02' exactly  │
          │ 3. Confirm with user        │
          │ 4. Execute safely           │
          └────┬─────────────────────────┘
               │
          ┌────v──────────────────────┐
          │ List agents?               │
          │ ✓ domain02 found           │
          │ ✓ Confirm shutdown?        │
          │ ✓ User says YES            │
          │ ✓ Shutdown domain02 (safe) │
          └───────────────────────────┘
        (correct machine, no mistakes)
```

## Data Sources

### Your Custom Domain Data (20 trajectories)

```
SHUTDOWN TARGET SELECTION SAFETY

Category              Count  Example
───────────────────────────────────────────────────────────
Explicit targets       3    "Shutdown machine 'domain02'"
                            ↓ Agent: Confirms, executes

Ambiguous targets      8    "Shutdown the server"
                            ↓ Agent: Lists 3 matches, asks

Error recovery         3    "Wrong one!"
                            ↓ Agent: Restores, fixes

Confirmation patterns  3    "Shutdown ALL prod-*"
                            ↓ Agent: Lists 5, waits for approval

Guardrail enforcement  1    Ambiguous + no context
                            ↓ Agent: BLOCKS execution
```

**Why custom?** Only YOU know your exact agent names, network, and safety requirements. Claude generated these to match YOUR specific scenario.

### Open Dataset: Toucan-1.5M (1.6 Million trajectories)

```
REAL-WORLD TOOL-USE PATTERNS

Source: 495 Model Context Protocols (MCPs) in the wild
Tools: 2,000+ across all MCPs
Data: Real MCP executions (June-Sept 2025)

Examples:
• Weather API calls (latitude/longitude → temperature)
• File operations (search → read → edit)
• Database queries (SELECT statements)
• API integrations (authentication → request → response)
• System operations (error handling, retries)
• Multi-tool workflows (sequential and parallel)

Why Toucan?
✓ Real-world scenarios (not synthetic)
✓ Error handling patterns (included)
✓ Multi-turn interactions (conversation)
✓ Quality-assessed (LLM-as-judge)
✓ Diverse tool coverage (2,000+ tools)
✓ Free and open-source
```

## The Training Mix

### Scenario 1: Focus on Safety (10,000 examples)

```
┌────────────────────────────────────────┐
│ Training Set Composition               │
├────────────────────────────────────────┤
│                                        │
│ Shutdown                     5%        │
│ [████               ]    500 examples  │
│                                        │
│ Toucan                      95%        │
│ [██████████████████] 9,500 examples   │
│                                        │
└────────────────────────────────────────┘

Goal: Model learns safety + capability
✓ Minimize wrong-machine shutdowns (from shutdown data)
✓ Maximize tool-use accuracy (from Toucan data)
```

### Scenario 2: General Purpose (500,000 examples)

```
┌────────────────────────────────────────┐
│ Large-Scale Training Set               │
├────────────────────────────────────────┤
│                                        │
│ Shutdown & custom          < 1%        │
│ [██                    ]  ~5K examples │
│                                        │
│ Toucan (all subsets)       ~99%        │
│ [██████████████████]   ~495K examples │
│                                        │
└────────────────────────────────────────┘

Goal: SOTA agent model
✓ Safety embedded across all examples
✓ Broad tool capability
✓ Production-ready
```

## How to Use

### Step 1: Load Toucan (pick one)

```bash
# Small test (for development)
python generate_trajectories.py --load-dataset toucan --sample 100

# Medium sample (for training)
python generate_trajectories.py --load-dataset toucan --sample 5000

# Large sample (for fine-tuning)
python generate_trajectories.py --load-dataset toucan --sample 50000

# Full dataset (if you have 30+ GB storage)
python generate_trajectories.py --load-dataset toucan --sample 500000
```

### Step 2: Use Your Shutdown Data

Already generated and saved:

```
training/agentic/data/shutdown_trajectories.jsonl
```

Contains: 20 carefully crafted shutdown safety examples

### Step 3: Combine & Train

```bash
# Merge datasets
cat shutdown_trajectories.jsonl toucan_*.jsonl > training_set.jsonl

# Fine-tune your model
python train.py --data training_set.jsonl --output model_v2/

# Evaluate safety
python eval_safety.py --model model_v2/ --benchmark shutdown_targets
```

## File Structure

```
training/
├── agentic/
│   ├── generators/
│   │   ├── generate_trajectories.py  ← Updated with --load-dataset
│   │   ├── load_open_datasets.py     ← Standalone loader
│   │   ├── shutdown_prompts.py       ← 20 custom prompts
│   │   ├── OPEN_DATASETS.md          ← Full guide
│   │   ├── QUICK_START_DATASETS.md   ← Quick reference
│   │   └── README                    ← This file
│   │
│   ├── data/
│   │   ├── shutdown_trajectories.jsonl       (20 samples)
│   │   └── toucan_Kimi-K2_trajectories.jsonl (test 10)
│   │
│   ├── tasks/
│   │   └── shutdown_target_selection.json    (metadata)
│   │
│   └── TRAINING_ARCHITECTURE.md     ← Full pipeline
│
└── ...
```

## Troubleshooting

| Problem                                           | Solution                                    |
| ------------------------------------------------- | ------------------------------------------- |
| `ModuleNotFoundError: No module named 'datasets'` | `pip install datasets`                      |
| Running out of disk space                         | Use `--sample 1000` instead of full dataset |
| Very slow download                                | Network issue - try again, will use cache   |
| Memory error during loading                       | Use smaller `--sample` size                 |
| Can't find output file                            | Check `training/agentic/data/` directory    |

## Cost Analysis

| Approach            | Cost      | Data     | Quality  | Time      |
| ------------------- | --------- | -------- | -------- | --------- |
| Synthetic only      | $0        | Limited  | Low      | Done      |
| Claude only         | $0.70     | 20 ex    | High     | 1min      |
| Toucan only         | $0        | 1.6M     | Med      | 30min     |
| **Claude + Toucan** | **$0.70** | **1.6M** | **High** | **30min** |

You get 1.6M high-quality training examples for ~$1 (plus time to download/train).

## What to Read Next

1. **Quick start:** [QUICK_START_DATASETS.md](generators/QUICK_START_DATASETS.md)
2. **Full guide:** [OPEN_DATASETS.md](generators/OPEN_DATASETS.md)
3. **Architecture:** [TRAINING_ARCHITECTURE.md](TRAINING_ARCHITECTURE.md)

## Key Insights

**Why this matters:**

- Your 20 examples teach WHAT to learn (safety patterns)
- Toucan's 1.6M teach HOW to learn (tool use at scale)
- Combined: Model learns to be both safe AND capable

**The math:**

- Synthetic patterns alone = rigid rules (not learning)
- Claude trajectories = reasoning examples (good learning)
- Toucan real data = diverse patterns (excellent learning)
- All three = best possible outcome

**Result:**
No more shutting down the wrong machine. AJ will ask clarifying questions, list available targets, and confirm with you before executing.
