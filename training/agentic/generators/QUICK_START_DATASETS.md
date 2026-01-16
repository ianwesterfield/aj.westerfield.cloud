# Quick Reference: Using Open Datasets

## TL;DR

**Load Toucan-1.5M and save to JSONL:**

```bash
cd training/agentic/generators
python generate_trajectories.py --load-dataset toucan --sample 5000
```

**Combine shutdown + Toucan data:**

```bash
cat ../data/shutdown_trajectories.jsonl ../data/toucan_*.jsonl > ../data/hybrid_training.jsonl
```

## One-Liners

### Sample sizes

```bash
# 100 examples (~70 MB)
python generate_trajectories.py --load-dataset toucan --sample 100

# 1000 examples (~700 MB)
python generate_trajectories.py --load-dataset toucan --sample 1000

# 10000 examples (~7 GB)
python generate_trajectories.py --load-dataset toucan --sample 10000

# 100000 examples (~70 GB) - FULL DATASET
python generate_trajectories.py --load-dataset toucan --sample 100000
```

### Different subsets

```bash
# Kimi-K2 (recommended)
python generate_trajectories.py --load-dataset toucan --dataset-subset Kimi-K2 --sample 5000

# Qwen3-32B
python generate_trajectories.py --load-dataset toucan --dataset-subset Qwen3-32B --sample 5000

# GPT-OSS-120B
python generate_trajectories.py --load-dataset toucan --dataset-subset GPT-OSS-120B --sample 5000
```

### Custom output locations

```bash
python generate_trajectories.py --load-dataset toucan --sample 5000 --output ../../training_data/

# Output will be: ../../training_data/toucan_Kimi-K2_trajectories.jsonl
```

## Files Generated

All data saved to `training/agentic/data/`:

| Dataset          | File                                | Size (10 samples) | Full Size |
| ---------------- | ----------------------------------- | ----------------- | --------- |
| Shutdown (yours) | `shutdown_trajectories.jsonl`       | 61 KB             | -         |
| Toucan           | `toucan_Kimi-K2_trajectories.jsonl` | 300 KB            | 21.8 GB   |

## Processing

### Merge datasets

```bash
cat ../data/*.jsonl > ../data/merged.jsonl
```

### Count trajectories

```bash
wc -l toucan_Kimi-K2_trajectories.jsonl
```

### Filter by source

```bash
# Only Toucan
grep '"source": "Toucan-1.5M"' merged.jsonl > toucan_only.jsonl

# Only shutdown
grep '"source_dataset": "Toucan-1.5M"' merged.jsonl | grep -v '"source": "Toucan-1.5M"' > shutdown_only.jsonl
```

### Filter by difficulty

```bash
# Only hard examples
grep '"difficulty": "hard"' merged.jsonl > hard_only.jsonl
```

## Troubleshooting

**Memory error on large sample:**

```bash
# Reduce sample size
python generate_trajectories.py --load-dataset toucan --sample 1000
```

**Network timeout:**

```bash
# Datasets caches automatically - try again (will use cache)
python generate_trajectories.py --load-dataset toucan --sample 100
```

**"datasets package not found":**

```bash
pip install datasets
```

## Architecture

```
Your System
├── Shutdown trajectories (20) ─┐
└── Toucan trajectories (1.6M) ─┤
                                ├─→ Merge ──→ Hybrid training set
                                ├─→ JSONL format
                                └─→ Fine-tune model
```

## Training Mixture Example

For 10,000 total examples:

- 500 shutdown (5%) - domain-specific safety
- 9,500 Toucan (95%) - general tool-use

```bash
# Generate shutdown
python generate_trajectories.py --category shutdown --use-claude

# Load Toucan
python generate_trajectories.py --load-dataset toucan --sample 9500

# Merge
cat shutdown_trajectories.jsonl toucan_Kimi-K2_trajectories.jsonl > hybrid_10k.jsonl

# Train
python train_model.py --data hybrid_10k.jsonl --output model/
```

## Cost Comparison

| Data Source         | Cost  | Size      | Quality              |
| ------------------- | ----- | --------- | -------------------- |
| Synthetic (free)    | $0    | 20        | Low (rigid patterns) |
| Claude (custom)     | $0.70 | 20        | High (reasoning)     |
| Toucan (1K sampled) | $0    | 1,000     | High (real MCP)      |
| Toucan (full)       | $0    | 1,600,000 | High (1.6M real)     |
| Toucan + Claude     | $0.70 | 1,600,020 | Very High (both)     |

## Links

- [Dataset Loader Code](load_open_datasets.py)
- [Full Documentation](OPEN_DATASETS.md)
- [Toucan HuggingFace](https://huggingface.co/datasets/Agent-Ark/Toucan-1.5M)
- [Toucan Paper](https://arxiv.org/abs/2510.01179)
