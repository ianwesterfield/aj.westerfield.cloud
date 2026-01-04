# Qwen 2.5 AJ 32B Training

Fine-tuning Qwen 2.5 32B-Instruct for AJ/Mesosync agent workloads using QLoRA (4-bit quantization).

## Overview

- **Base Model**: Qwen/Qwen2.5-32B-Instruct (33.3B parameters)
- **Training Method**: QLoRA with 4-bit quantization (~537M trainable params, 1.6%)
- **Total Examples**: 3,790 across 38+ domains
- **Hardware**: NVIDIA RTX 4090 (24GB) or equivalent; ~7GB system RAM overflow expected
- **Training Time**: ~7 days on RTX 4090, ~4-6 hours on A100, ~2-3 hours on H100

## Directory Structure

```
training/qwen2.5-aj-32b/
├── data/                    # Training datasets (45 JSONL files)
│   ├── all_training_data.jsonl    # Combined dataset (3,790 examples)
│   ├── dataset_stats.json         # Statistics by domain
│   └── [domain].jsonl             # Individual domain files
├── scripts/                 # Training & generation scripts
│   ├── generate_all.py            # Master generator (runs all)
│   ├── generate_*.py              # 38+ domain generators
│   ├── train_standard.py          # QLoRA training (PEFT/TRL)
│   ├── train_qlora.py             # Alternative Unsloth trainer
│   └── export_ollama.py           # Export to Ollama format
├── configs/                 # Training configurations
│   └── qlora_config.yaml
├── checkpoints/             # Training checkpoints (auto-saved)
├── output/                  # Final model artifacts
├── Modelfile               # Ollama model definition
└── Dockerfile              # Container for training
```

## Training Data Domains (38 Generators, 3,790 Examples)

| Domain              | Examples | Description                                |
| ------------------- | -------- | ------------------------------------------ |
| Git Version Control | 302      | Git operations, workflows, troubleshooting |
| VS Code IDE         | 242      | Editor workflows, extensions, settings     |
| Windows Admin       | 225      | PowerShell, system admin, WSL              |
| Cloud/DevOps        | 196      | AWS, Azure, GCP, Terraform                 |
| Linux Admin         | 179      | System administration, services            |
| Python Development  | 168      | Libraries, debugging, best practices       |
| Docker              | 139      | Containers, compose, orchestration         |
| Database/SQL        | 131      | PostgreSQL, MySQL, query optimization      |
| Networking          | 129      | TCP/IP, DNS, troubleshooting               |
| Node.js             | 127      | Express, npm, async patterns               |
| Security            | 110      | Authentication, encryption, hardening      |
| AI/ML/LLM           | 107      | Model training, inference, RAG             |
| Angular             | 101      | Components, services, RxJS                 |
| Multistep Workflows | 99       | Complex task orchestration                 |
| TypeScript          | 97       | Types, generics, patterns                  |
| React               | 96       | Hooks, state, components                   |
| Firewalla/Storage   | 94       | Network security appliance                 |
| .NET/C#             | 92       | ASP.NET, Entity Framework                  |
| API Development     | 89       | REST, GraphQL, OpenAPI                     |
| Memory/Qdrant       | 78       | Vector storage, semantic search            |
| And 18 more...      | ~600     | See `data/dataset_stats.json`              |

## Quick Start

### Generate Training Data

```bash
# Generate all training data (runs 38+ generators)
python scripts/generate_all.py

# Or run individual generators
python scripts/generate_python_data.py
python scripts/generate_docker_data.py
```

### Run Training

```bash
# Standard training with PEFT/TRL (recommended for Windows)
python scripts/train_standard.py

# Alternative: Unsloth trainer (Linux only, faster)
python scripts/train_qlora.py
```

### Export to Ollama

```bash
# After training completes
python scripts/export_ollama.py

# Test the model
ollama run qwen2.5-aj:32b-q4
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
