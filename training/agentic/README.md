# Agentic Training Pipeline

## Overview

Transform from instruction-following to agentic reasoning:

```
Current: "How do I X?" → "Here's how to X"
Target:  "Do X" → [thought → action → observation → thought → ...]
```

## Data Structure

### Phase 1: Supervised Fine-Tuning (SFT)

```
data/
├── trajectories/           # Tool-use traces (50K target)
│   ├── coding_tasks.jsonl
│   ├── debugging_tasks.jsonl
│   ├── refactoring_tasks.jsonl
│   └── devops_tasks.jsonl
├── reasoning/              # Chain-of-thought (20K target)
│   ├── problem_solving.jsonl
│   ├── architecture_decisions.jsonl
│   └── tradeoff_analysis.jsonl
├── domain/                 # Knowledge base (10K - your current data, expanded)
│   └── ... (existing domains)
└── conversations/          # Multi-turn agentic (5K target)
    └── coding_sessions.jsonl
```

### Phase 2: Direct Preference Optimization (DPO)

```
preferences/
├── code_quality.jsonl      # Better vs worse implementations
├── efficiency.jsonl        # Optimal vs suboptimal solutions
└── safety.jsonl            # Safe vs risky approaches
```

## Training Phases

### Phase 1: SFT (3-5 days on 8xH100)

- Full fine-tune Qwen2.5-32B (or 72B)
- ~85K examples total
- Learn tool use, reasoning patterns, domain knowledge

### Phase 2: DPO (1-2 days)

- 10K preference pairs
- Polish output quality
- Align with desired behavior

## Quick Start

```bash
# 1. Generate trajectory data (uses Claude API)
python generators/generate_trajectories.py --count 10000 --category coding

# 2. Convert existing data to new format
python converters/upgrade_domain_data.py --input ../data --output data/domain/

# 3. Generate preferences
python generators/generate_preferences.py --count 5000

# 4. Validate dataset
python utils/validate_dataset.py --data-dir data/

# 5. Train (see configs/)
python train_sft.py --config configs/sft_32b.yaml
python train_dpo.py --config configs/dpo_32b.yaml
```

## Cost Estimates

| Phase     | Hardware  | Time        | Est. Cost       |
| --------- | --------- | ----------- | --------------- |
| Data Gen  | API calls | 2-3 days    | $500-2000       |
| SFT       | 8xH100    | 3-5 days    | $3000-6000      |
| DPO       | 8xH100    | 1-2 days    | $1000-2000      |
| **Total** |           | **~1 week** | **$4500-10000** |

## Data Format Specs

See `schemas/` for JSON schemas and examples.
