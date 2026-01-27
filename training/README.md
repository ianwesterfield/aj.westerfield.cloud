# AJ Training Infrastructure

> **Current Approach**: Single-GPU LoRA fine-tuning for conversational AI agents

Train DeepSeek-R1-Distill-Qwen-32B for agentic intent logic with conversational adaptability. Optimize model reasoning while preserving base capabilities through parameter-efficient LoRA adaptation.

---

## Versioning

See [datasets/README.md](datasets/README.md) for full versioning scheme.

```
AJ-DeepSeekR1Qwen32B-v{major.minor.patch-suffix}
│          │             │     │     │       └── lora, merged, q4km, q8
│          │             │     │     └────────── Patch: hyperparameter tweaks
│          │             │     └──────────────── Minor: dataset mix adjustments
│          │             └─────────────────── Major: new base model or architecture
│          └──────────────────────────── Base model code
└──────────────────────────────── Project name
```

### Active Training Runs

| Version       | Dataset  | Status      | Notes                                |
| ------------- | -------- | ----------- | ------------------------------------ |
| `v2.0.0-lora` | Mixed-v1 | ⏳ Training | Conversational + Plants + Apothecary |

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TRAINING PIPELINE                            │
│                                                                     │
│  High-Memory GPU (140GB+ VRAM)                                     │
│  └── DeepSeek-R1-Distill-Qwen-32B (32.76B params)                  │
│      └── LoRA (r=64, ~536M trainable = 1.61%)                      │
│          └── Mixed Dataset (300K examples)                         │
│              ├── 50% Conversational (WildChat + UltraChat)         │
│              ├── 40% Domain Knowledge (~26K from training/data/)   │
│              │   ├── CLI (Linux, Windows, cross-platform)          │
│              │   ├── Development (Python, TS, Node, .NET, etc.)    │
│              │   ├── Infrastructure (Docker, Cloud, Security)      │
│              │   ├── Agentic (AJ persona, Guardrails, Intent)      │
│              │   └── Specialized
│              └── 10% Strategic Reasoning (Skein text adventures)   │
│                                                                     │
│  Output: Quantized GGUF for deployment                             │
└─────────────────────────────────────────────────────────────────────┘
```

### Why This Setup?

| Decision                 | Rationale                                                                        |
| ------------------------ | -------------------------------------------------------------------------------- |
| **Single-GPU LoRA**      | High-VRAM GPU fits 32B model in bf16 + LoRA. No distributed training complexity  |
| **LoRA (not full FT)**   | 99% fewer trainable params. Preserves base model reasoning                       |
| **Mixed datasets**       | Conversational breadth + domain knowledge (plants, apothecary, agriculture)      |
| **Server-side download** | Avoid large local uploads; fetch 5MB scripts only, download 300K examples on GPU |

---

## Quick Start

### 1. Provision GPU Instance

Use any cloud provider with high-VRAM GPU availability (RunPod, Lambda Labs, Vast.ai, etc.):

```bash
# Requirements:
# - 1x NVIDIA H100/H200 (140GB+ VRAM)
# - 20+ vCPU, 200GB+ RAM
# - 500GB+ SSD for datasets and outputs
```

### 2. Setup Training Environment

SSH into your droplet and run:

```bash
# Clone repo
git clone https://github.com/your-org/aj.westerfield.cloud
cd aj.westerfield.cloud/training

# Run pipeline (5 automatic steps)
bash setup_and_train_v2.sh

# Monitor training
tail -f training_*.log
```

### Start Training (Automated)

The `setup_and_train_v2.sh` script handles everything:

1. Downloads datasets
2. Prepares mixed dataset
3. Starts training
4. Logs to `training_YYYYMMDD_HHMMSS.log`

**No manual steps needed!**

---

## Training Configuration

### Hardware Requirements

| Component   | Spec        | Notes                             |
| ----------- | ----------- | --------------------------------- |
| **GPU**     | 140GB+ VRAM | H100/H200 recommended, single GPU |
| **CPU**     | 20+ cores   | For data loading and dataset prep |
| **RAM**     | 200GB+      | Model loading and merging         |
| **Storage** | 500GB+ SSD  | Datasets, checkpoints, outputs    |

### LoRA Configuration

```yaml
lora_r: 64
lora_alpha: 128
lora_dropout: 0.05
target_modules:
  - q_proj, k_proj, v_proj, o_proj # Attention
  - gate_proj, up_proj, down_proj # MLP

# Results in ~536M trainable params (1.61% of 32.76B)
```

### Training Hyperparameters

```yaml
# Batch
batch_size: 2
gradient_accumulation_steps: 8
effective_batch_size: 16

# Duration
max_steps: 5000
max_seq_length: 2048

# Optimizer
learning_rate: 2e-5
weight_decay: 0.01
warmup_steps: 100
lr_scheduler: cosine

# Precision
bf16: true
tf32: true
gradient_checkpointing: true
```

---

## Time Estimate

| Phase                 | Duration      | Notes                         |
| --------------------- | ------------- | ----------------------------- |
| Data Download         | ~10 min       | 7 HuggingFace datasets (~2GB) |
| Dataset Preparation   | ~5 min        | Merging 127K examples         |
| Training (5000 steps) | ~11 hours     | ~2.2s/step on H100/H200       |
| Model Merge + Convert | ~1 hour       | LoRA adapter + quantization   |
| **Total**             | **~12 hours** | Start-to-finish on GPU        |

---

## Dataset: Mixed v1.0 (v2.0.0 Training)

Combines 7 curated datasets for conversational breadth + domain knowledge:

```
127,366 total examples (99:1 train/eval split):
├── 50% Conversational (82K WildChat + 45K UltraChat)
├── 15% Plant/Farming (25K Agriculture + Gardening + StackExchange)
├── 10% Strategic (14.6K Skein text adventures)
├── 10% Western Apothecary (89 public domain herbalism Q&A)
└── 15% Custom AJ Data (45K domain-specific conversations)
```

**Format**: ChatML multi-turn conversations with tool calls

**Example**:

```json
{
  "messages": [
    { "role": "system", "content": "You are AJ..." },
    { "role": "user", "content": "List running containers" },
    {
      "role": "assistant",
      "tool_calls": [
        { "name": "bash", "arguments": { "command": "docker ps" } }
      ]
    },
    { "role": "tool", "content": "CONTAINER ID  IMAGE  ..." },
    { "role": "assistant", "content": "Here are 3 running containers..." }
  ]
}
```

---

## File Structure

```
training/
├── scripts/
│   ├── train_mixed_h200.py     # Main v2.0.0 training script
│   └── merge_adapters.py       # Merge LoRA → full model
├── configs/
│   ├── mixed_v1_h200.yaml      # v2.0.0 training config
│   └── merge_config.yaml       # Merge configuration
├── datasets/
│   ├── download_datasets.py    # HuggingFace dataset loader
│   ├── prepare_mixed_v1.py     # Build 300K mixed dataset
│   ├── extract_apothecary.py   # Parse public domain herbalism texts
│   └── raw/ & processed/       # Dataset cache
└── data/
    └── *.jsonl                 # Custom AJ training data
```

---

## Scripts Reference

### train_mixed_h200.py

Main training script for v2.0.0 mixed dataset:

```bash
# Automatically called by setup_and_train_v2.sh
python scripts/train_mixed_h200.py --config configs/mixed_v1_h200.yaml

# Resume from checkpoint if needed
python scripts/train_mixed_h200.py --config configs/mixed_v1_h200.yaml \
    --resume ./mixed-v1-output/checkpoint-2500
```

**Output**: `mixed-v1-output/` with LoRA adapter files

### merge_adapters.py

Merge LoRA adapters back into base model:

```bash
python scripts/merge_adapters.py \
    --base-model deepseek-ai/DeepSeek-R1-Distill-Qwen-32B \
    --adapter-path ./mixed-v1-output \
    --output-path ./aj-dsr1q32b-v2.0.0-merged
```

---

## Troubleshooting

### Out of Memory

If you see CUDA OOM errors:

1. **Reduce batch size** in `configs/mixed_v1.yaml`:

   ```yaml
   batch_size: 1 # Down from 2
   gradient_accumulation_steps: 16 # Double to maintain effective batch
   ```

2. **Reduce sequence length**:
   ```yaml
   max_seq_length: 1024 # Down from 2048
   ```

### Training Stalls

If loss stops decreasing:

1. Check learning rate isn't too high/low
2. Verify data loading (watch GPU utilization)
3. Review gradient norms in logs

### Connection Lost

If SSH disconnects:

1. Use `tmux` or `screen` before training
2. Resume from latest checkpoint with `--resume`

```bash
# Before training
tmux new -s training
python scripts/train_mixed.py ...

# Detach: Ctrl+B, then D
# Reattach after reconnect:
tmux attach -t training
```

---

## Reference: Tool Schema

AJ uses 6 core tools for the "All You Need is Bash" philosophy:

| Tool              | Purpose                   | Example                 |
| ----------------- | ------------------------- | ----------------------- |
| `bash`            | Local command execution   | `ls -la`, `docker ps`   |
| `remote_bash`     | Single agent execution    | Execute on `webprod01`  |
| `remote_bash_all` | Multi-agent execution     | Execute on all `prod-*` |
| `list_agents`     | Discover available agents | Show FunnelCloud agents |
| `think`           | Reasoning step (internal) | Plan before execution   |
| `complete`        | Task completion signal    | Mark task finished      |

### Data Sources

| Source                  | Size  | Content                                  |
| ----------------------- | ----- | ---------------------------------------- |
| Conversational datasets | 127K  | WildChat + UltraChat (HuggingFace)       |
| Plant/Farming datasets  | 70K   | Agriculture QA + Gardening (HuggingFace) |
| Strategic/Adventure     | 14.6K | Skein text adventures (HuggingFace)      |
| Western Apothecary      | 89    | Public domain herbalism texts            |
| Custom AJ Data          | 45K+  | Domain-specific conversational data      |

### Generate Custom Data

```bash
# The v2.0.0 pipeline downloads and prepares datasets automatically
# No manual data generation needed for basic training
cd training
bash setup_and_train_v2.sh
```

---

## Local Development (RTX 4090)

For experimentation on local hardware:

### WSL2 Setup (Windows)

```powershell
# Enable WSL2
wsl --install -d Ubuntu-22.04

# Inside WSL
sudo apt update && sudo apt install -y python3-pip python3-venv
cd /mnt/c/Code/aj.westerfield.cloud/training
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Limitations

RTX 4090 (24GB) cannot train 32B models even with LoRA. Use it for:

- Testing training scripts with smaller models (7B)
- Running inference on quantized models
- Data preprocessing and validation

---

## Previous Approaches (Historical)

Earlier iterations tried different approaches that proved less reliable:

1. **4x H100 + DeepSpeed ZeRO-3** (alternative providers): Complex distributed training, frequent crashes
2. **FSDP + LoRA**: Optimizer state sharding incompatible with LoRA
3. **Full Fine-tuning**: Required 8+ GPUs, expensive

The single-GPU high-memory approach eliminates distributed training complexity while remaining cost-effective.
