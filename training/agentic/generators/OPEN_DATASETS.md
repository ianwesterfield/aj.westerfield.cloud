# Open Dataset Integration Guide

This directory supports integration of open-source trajectory datasets for training agent models. Currently implemented: **Toucan-1.5M** from HuggingFace.

## Quick Start

### Load Toucan-1.5M Dataset

```bash
# Sample 500 examples from Kimi-K2 subset
python generate_trajectories.py --load-dataset toucan --dataset-subset Kimi-K2 --sample 500 --output ../data/

# Load all examples (1.6M trajectories - ~21.8 GB)
python generate_trajectories.py --load-dataset toucan --dataset-subset Kimi-K2 --output ../data/
```

## Supported Datasets

### 1. **Toucan-1.5M** (Implemented)

- **Source**: [Agent-Ark/Toucan-1.5M](https://huggingface.co/datasets/Agent-Ark/Toucan-1.5M)
- **Size**: 1.6M trajectories from 495 real-world MCPs covering 2,000+ tools
- **Format**: HuggingFace Parquet dataset
- **Subsets**:
  - `Kimi-K2`: Generated with Kimi-K2 model (recommended)
  - `Qwen3-32B`: Generated with Qwen3-32B
  - `GPT-OSS-120B`: Generated with GPT-OSS-120B
- **Features**:
  - Chat-format messages with system prompts
  - Target tools for each trajectory
  - Quality assessments (question & response)
  - Multi-turn, multi-tool, and parallel tool call examples
  - Real-world error scenarios from actual MCP environments

**Schema**:

```json
{
  "uuid": "unique_id",
  "subset": "single-turn-original|multi-turn|irrelevant|single-turn-diversify",
  "messages": [{"role": "...", "content": "..."}],
  "question": "user task",
  "target_tools": ["tool1", "tool2"],
  "question_quality_assessment": {...},
  "response_quality_assessment": {...},
  "metadata": {...}
}
```

### 2. **WebArena** (Planned)

- Source: Web navigation and interaction trajectories
- Status: Loader skeleton created, implementation pending

### 3. **GAIA** (Planned)

- Source: Multi-domain agent interaction benchmarks
- Status: Loader skeleton created, implementation pending

### 4. **AgentBench** (Planned)

- Source: Diverse agent task trajectories
- Status: Loader skeleton created, implementation pending

## Integration Architecture

### Pipeline Flow

```
┌─────────────────────────────────────┐
│   generate_trajectories.py          │
├─────────────────────────────────────┤
│  - Custom task generation (Claude)  │
│  - Shutdown target selection (20)   │
│  - Open dataset loading             │
└────────────┬────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    v                 v
┌─────────────┐  ┌──────────────────┐
│ Generate    │  │ Load Open        │
│ (Claude API)│  │ Datasets (HF)    │
└────────┬────┘  └────────┬─────────┘
         │                │
         │                v
         │        ┌──────────────────┐
         │        │ Toucan-1.5M      │
         │        │ WebArena (TODO)  │
         │        │ GAIA (TODO)      │
         │        │ AgentBench (TODO)│
         │        └────────┬─────────┘
         │                │
         └────────┬───────┘
                  v
         ┌─────────────────────┐
         │ Unified JSONL       │
         │ trajectories format │
         └─────────────────────┘
                  │
                  v
         ┌─────────────────────┐
         │ Fine-tuning pipeline│
         │ DPO alignment       │
         │ Evaluation          │
         └─────────────────────┘
```

## Usage Examples

### Example 1: Load 1000 Toucan trajectories

```bash
python generate_trajectories.py \
  --load-dataset toucan \
  --dataset-subset Kimi-K2 \
  --sample 1000 \
  --output ../data/toucan_samples/
```

Output: `../data/toucan_samples/toucan_Kimi_K2_trajectories.jsonl`

### Example 2: Mix custom shutdown data with open data

```bash
# Generate shutdown trajectories
python generate_trajectories.py \
  --category shutdown \
  --use-claude \
  --output ../data/

# Load Toucan data
python generate_trajectories.py \
  --load-dataset toucan \
  --dataset-subset Kimi-K2 \
  --sample 5000 \
  --output ../data/

# Combined training with both datasets
cat ../data/shutdown_trajectories.jsonl ../data/toucan_Kimi_K2_trajectories.jsonl > ../data/hybrid_training_set.jsonl
```

### Example 3: Generate multiple dataset subsets

```bash
for subset in Kimi-K2 Qwen3-32B GPT-OSS-120B; do
  python generate_trajectories.py \
    --load-dataset toucan \
    --dataset-subset "$subset" \
    --sample 500 \
    --output "../data/toucan_${subset}/"
done
```

## Output Format

All datasets are converted to unified JSONL format:

```json
{
  "task": "User request or question",
  "context": {
    "source": "Toucan-1.5M",
    "subset": "Kimi-K2"
  },
  "trajectory": [
    {
      "step_type": "chat_messages",
      "content": [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
      ]
    }
  ],
  "metadata": {
    "category": "open_dataset",
    "source": "Toucan-1.5M",
    "source_subset": "Kimi-K2",
    "tools_used": ["tool1", "tool2"],
    "difficulty": "medium",
    "uuid": "...",
    "subset_type": "multi-turn",
    "question_quality": {...},
    "response_quality": {...},
    "success": true
  }
}
```

## Requirements

Install HuggingFace datasets library:

```bash
pip install datasets
```

For authenticated access (private datasets):

```bash
huggingface-cli login
```

## Performance Notes

### Download Size & Time

- **Toucan-1.5M (full)**: ~21.8 GB, 1.6M examples
- **Toucan sampled (1000)**: ~13 MB, ~1-2 minutes
- **Toucan sampled (10000)**: ~130 MB, ~5-10 minutes

### Streaming Options

To avoid downloading entire dataset:

```python
# (Future enhancement)
# Load with streaming=True to process on-the-fly
dataset = load_dataset("Agent-Ark/Toucan-1.5M", "Kimi-K2", split="train", streaming=True)
```

## Combining Domains

### Shutdown Target Selection + Toucan Hybrid Training

The recommended approach combines:

1. **Proprietary Domain Data** (20 shutdown trajectories)
   - Custom agent metadata
   - Target disambiguation patterns
   - Guardrail enforcement
2. **General Tool-Use Data** (Toucan-1.5M sampled)
   - Multi-tool reasoning
   - Real-world MCP scenarios
   - Error handling patterns

**Training mixture**:

```
Shutdown trajectories:  5% (500 examples)
Toucan sampled:        95% (9500 examples)
Total: 10,000 trajectories
```

This provides domain-specific safety training while maintaining broad tool-use generalization.

## Troubleshooting

### Dataset not found

```
Error: Can't find 'Agent-Ark/Toucan-1.5M' in HF datasets
```

**Solution**: Ensure internet connection and HuggingFace datasets library is installed:

```bash
pip install --upgrade datasets
```

### Memory issues with full dataset

**Solution**: Use `--sample` flag to load subset:

```bash
python generate_trajectories.py \
  --load-dataset toucan \
  --sample 1000  # Load only 1000 examples
```

### Slow download

**Solution**: Check network connection, or use background download:

```bash
nohup python generate_trajectories.py --load-dataset toucan &
```

## Future Enhancements

- [ ] Streaming dataset loading (avoid full download)
- [ ] Dataset filtering by tool type or difficulty
- [ ] Automatic quality assessment filtering
- [ ] Multi-dataset mixing and balancing
- [ ] Cache management for repeated loads
- [ ] Add WebArena, GAIA, AgentBench loaders

## References

- **Toucan Paper**: [arxiv:2510.01179](https://arxiv.org/abs/2510.01179)
- **Agent-Ark GitHub**: [TheAgentArk/Toucan](https://github.com/TheAgentArk/Toucan)
- **HuggingFace Datasets Docs**: [huggingface.co/docs/datasets](https://huggingface.co/docs/datasets)
