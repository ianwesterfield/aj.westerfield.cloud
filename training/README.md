# AJ Fine-Tuned Models

Fine-tuned LLMs for AJ agent workloads using QLoRA (4-bit quantization).

## Available Models

| Model             | Base                         | Purpose                       | Ollama Name         |
| ----------------- | ---------------------------- | ----------------------------- | ------------------- |
| **R1-Distill-AJ** | DeepSeek-R1-Distill-Qwen-32B | Reasoning with `<think>` tags | `r1-distill-aj:32b` |
| **Qwen2.5-AJ**    | Qwen2.5-32B-Instruct         | Direct answers, fast          | `qwen2.5-aj:32b`    |

Each model has context window variants: `-2k`, `-4k`, `-8k`, and default (32k).

**Default model**: `r1-distill-aj:32b-4k` — reasoning + balanced context

## Overview

- **Training Method**: QLoRA with 4-bit quantization (~537M trainable params, 1.6%)
- **Total Examples**: 5,205 across 43 domains
- **Hardware**: Vast.ai A100-SXM4-80GB (recommended) or RTX 4090 (slower)
- **Training Time**: ~4 hours on A100, ~7 days on RTX 4090
- **Next Phase**: Agentic training with trajectory format (see [agentic/README.md](agentic/README.md))

## Directory Structure

```
training/
├── data/                    # Training datasets (45 JSONL files)
│   ├── all_training_data.jsonl    # Combined dataset (5,205 examples)
│   ├── dataset_stats.json         # Statistics by domain
│   └── [domain].jsonl             # Individual domain files
├── scripts/                 # Training & generation scripts
│   ├── generate_all.py            # Master generator (runs all)
│   ├── generate_*.py              # 43 domain generators
│   ├── bulk_expand.py             # Expand domains to target count
│   ├── train_qlora.py             # QLoRA training (PEFT/TRL)
│   └── merge_and_export.py        # Merge LoRA + export
├── agentic/                 # Agentic training (trajectory format)
│   ├── schemas/                   # JSON schemas for trajectories
│   ├── generators/                # Trajectory & preference generators
│   ├── converters/                # Convert existing data
│   ├── configs/                   # SFT + DPO training configs
│   └── tasks/                     # Task prompts for generation
├── configs/                 # Training configurations
│   └── qlora_config.yaml
├── checkpoints/             # Training checkpoints (auto-saved)
└── output/                  # Final model artifacts
```

**Note**: GGUF conversion requires llama.cpp (build on training server or use pre-built binaries).

## Training Data Domains (43 Generators, 5,205 Examples)

| Domain              | Examples | Description                                |
| ------------------- | -------- | ------------------------------------------ |
| Git Version Control | 302      | Git operations, workflows, troubleshooting |
| Windows Admin       | 275      | PowerShell, system admin, WSL              |
| VS Code IDE         | 242      | Editor workflows, extensions, settings     |
| Cloud/DevOps        | 196      | AWS, Azure, GCP, Terraform                 |
| Linux Admin         | 179      | System administration, services            |
| Python Development  | 168      | Libraries, debugging, best practices       |
| Angular             | 151      | Components, services, RxJS                 |
| Docker              | 139      | Containers, compose, orchestration         |
| Database/SQL        | 131      | PostgreSQL, MySQL, query optimization      |
| Networking          | 129      | TCP/IP, DNS, troubleshooting               |
| Node.js             | 127      | Express, npm, async patterns               |
| Security            | 110      | Authentication, encryption, hardening      |
| AI/ML/LLM           | 107      | Model training, inference, RAG             |
| Firewalla/Storage   | 100      | Network security appliance                 |
| Multistep Workflows | 100      | Complex task orchestration                 |
| TypeScript          | 100      | Types, generics, patterns                  |
| .NET/C#             | 100      | ASP.NET, Entity Framework                  |
| API Development     | 100      | REST, GraphQL, OpenAPI                     |
| And 25 more...      | ~2,500   | See `data/dataset_stats.json`              |

All domains now have 100+ examples for balanced training coverage.

## Quick Start

### Generate Training Data

```bash
# Generate all training data (runs 43 generators)
python scripts/generate_all.py

# Expand all domains to 100+ examples
python scripts/bulk_expand.py

# Or run individual generators
python scripts/generate_python_data.py
python scripts/generate_docker_data.py
```

### Run Training

```bash
# QLoRA training with config
python scripts/train_qlora.py --config configs/qlora_config.yaml
```

### Export to Ollama

GGUF conversion requires llama.cpp. On a cloud GPU instance:

```bash
# 1. Merge LoRA with base model
python scripts/merge_and_export.py

# 2. Convert to GGUF (requires llama.cpp)
python /path/to/llama.cpp/convert_hf_to_gguf.py ./merged-model --outfile model.bf16.gguf --outtype bf16

# 3. Quantize to Q4_K_M (~19GB)
/path/to/llama.cpp/build/bin/llama-quantize model.bf16.gguf model-q4_k_m.gguf Q4_K_M

# 4. Download and import to Ollama
scp model-q4_k_m.gguf local:/path/to/ollama/
ollama create model-name:32b -f Modelfile
```

## Training Configuration

Default settings in `train_standard.py`:

| Parameter             | Value     | Notes                               |
| --------------------- | --------- | ----------------------------------- |
| Epochs                | 3         | Full passes through data            |
| Batch Size            | 1         | Limited by VRAM                     |
| Gradient Accumulation | 8         | Effective batch = 8                 |
| Learning Rate         | 2e-4      | With cosine scheduler               |
| LoRA Rank             | 16        | Low-rank adaptation                 |
| LoRA Alpha            | 32        | Scaling factor                      |
| Quantization          | 4-bit NF4 | BitsAndBytes config                 |
| Attention             | SDPA      | PyTorch native (Windows compatible) |
| Max Seq Length        | 2048      | Context window                      |

## Requirements

- **Python**: 3.10+
- **CUDA**: 12.0+ (cuDNN 8.9+)
- **VRAM**: 24GB recommended (uses VRAM + system RAM overflow)
- **System RAM**: 32GB+ recommended
- **Storage**: ~100GB (model cache + checkpoints)

### Python Dependencies

```bash
pip install torch>=2.1.0 transformers>=4.36.0 peft>=0.7.0 trl>=0.7.0 \
    bitsandbytes>=0.41.0 accelerate>=0.25.0 datasets>=2.16.0 \
    sentencepiece tiktoken
```

## Cloud Training (Faster)

For faster training, consider cloud GPU options:

| Provider    | GPU       | Est. Time | Est. Cost |
| ----------- | --------- | --------- | --------- |
| RunPod      | A100 80GB | 4-6 hours | $8-12     |
| Lambda Labs | A100 80GB | 4-6 hours | $8-12     |
| RunPod      | H100      | 2-3 hours | $6-10     |

Upload `train_standard.py`, `data/all_training_data.jsonl`, and run.

## Monitoring Training

Training outputs to console with progress bars. Key metrics:

- **Loss**: Should decrease from ~1.5 to ~0.5
- **Steps**: 1,278 total (3 epochs × 426 steps)
- **Speed**: ~8-10 min/step on RTX 4090

Checkpoints saved to `checkpoints/` every 100 steps.

## Troubleshooting

### Out of Memory

- Reduce `per_device_train_batch_size` to 1
- Increase `gradient_accumulation_steps`
- Enable `gradient_checkpointing=True`

### Flash Attention Not Available (Windows)

- Use `attn_implementation="sdpa"` (PyTorch native)
- SDPA is default in `train_standard.py`

### Model Download Slow

- Model (~65GB) is cached after first download
- Check `~/.cache/huggingface/hub/`

## Using Docker

```bash
# Build training container
docker build -t aj-training .

# Run with GPU passthrough
docker run --gpus all \
    -v $(pwd)/output:/app/output \
    -v $(pwd)/checkpoints:/app/checkpoints \
    aj-training
```
