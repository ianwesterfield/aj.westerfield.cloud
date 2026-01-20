# AJ Fine-Tuned Models

Fine-tuned LLMs for AJ agent workloads using QLoRA (4-bit quantization) and Unsloth (2x faster training).

## Current Model

| Model          | Base                        | Purpose                         | Ollama Name     |
| -------------- | --------------------------- | ------------------------------- | --------------- |
| **Granite-AJ** | IBM Granite 3.1-8B-Instruct | Agentic tool-use (bash-centric) | `granite-aj:8b` |

**Why Granite 3.1-8B?**

- **Agentic Focus**: Native function-calling capabilities from IBM's research
- **Efficient**: 8B parameters fits comfortably in 24GB VRAM with room for longer context
- **Open Source**: Apache 2.0 license for commercial use
- **Fast Inference**: Smaller model = faster responses = better UX

## Overview

- **Base Model**: IBM Granite 3.1-8B-Instruct (Apache 2.0)
- **Training Method**: QLoRA with 4-bit quantization + Unsloth (2x faster)
- **Agentic Data**: Glaive (113K) + AgentInstruct (1.8M) + Toucan MCP (519K) + custom (5K)
- **Tool Schema**: 6 tools (`bash`, `remote_bash`, `remote_bash_all`, `list_agents`, `think`, `complete`)
- **Hardware**: RTX 4090 (24GB) via WSL2
- **Training Time**: ~24-48 hours with full datasets
- **Training Pipeline**: `train_pipeline.py` handles everything end-to-end

## Directory Structure

```
training/
├── data/                    # Training datasets
│   ├── all_training_data.jsonl    # Combined dataset
│   ├── dataset_stats.json         # Statistics by domain
│   └── [domain].jsonl             # 45+ domain-specific files
├── scripts/                 # Training & generation scripts
│   ├── train_pipeline.py          # ★ Master pipeline (run this!)
│   ├── prepare_agentic_datasets.py # Download Glaive/AgentInstruct
│   ├── generate_all.py            # Run all domain generators
│   ├── generate_*.py              # 43+ domain generators
│   ├── train_qlora.py             # QLoRA training (PEFT/TRL)
│   └── merge_and_export.py        # Merge LoRA + export
├── agentic/                 # Agentic training data
│   ├── schemas/                   # JSON schemas for tool-use
│   ├── generators/                # Trajectory generators
│   ├── converters/                # Convert external datasets
│   ├── data/                      # Generated trajectories
│   └── tasks/                     # Task prompt templates
├── configs/                 # Training configurations
│   ├── qlora_config.yaml          # ★ RTX 4090 optimized config
│   └── qlora_config_chat.yaml     # Chat format config
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

## Quick Start (Recommended)

### Run Full Training Pipeline

The easiest way to train is using the master pipeline:

```bash
# In WSL2 (recommended for CUDA compatibility)
cd /mnt/c/Code/aj.westerfield.cloud/training
source venv/bin/activate

# Run full pipeline - downloads ALL examples by default
python scripts/train_pipeline.py -y

# Or limit dataset sizes for faster training
python scripts/train_pipeline.py --xlam-target 50000 --toucan-target 100000 -y
```

The pipeline handles everything:

1. ✅ Checks requirements (torch, CUDA, Unsloth, etc.)
2. ✅ Downloads agentic datasets (Glaive, AgentInstruct, Toucan-1.5M)
3. ✅ Merges with custom AJ training examples
4. ✅ Runs QLoRA fine-tuning with Unsloth (2x faster)
5. ✅ Saves checkpoints for Ollama export

The `-y` flag skips confirmation prompts for unattended training.

### Manual Steps (Alternative)

#### Generate Training Data

```bash
# Generate all training data (runs 43+ generators)
python scripts/generate_all.py

# Download agentic datasets (all examples by default)
python scripts/prepare_agentic_datasets.py -y

# Or limit to specific counts
python scripts/prepare_agentic_datasets.py --xlam-target 50000 --toucan-target 100000 -y
```

#### Run Training

```bash
# QLoRA training with config
python scripts/train_qlora.py --config configs/qlora_config.yaml
```

### Export to Ollama

After training completes, export to Ollama:

```bash
# 1. Merge LoRA with base model
python scripts/merge_and_export.py

# 2. Convert to GGUF (requires llama.cpp)
python /path/to/llama.cpp/convert_hf_to_gguf.py ./merged-model --outfile granite-aj.bf16.gguf --outtype bf16

# 3. Quantize to Q4_K_M (~5GB for 8B model)
/path/to/llama.cpp/build/bin/llama-quantize granite-aj.bf16.gguf granite-aj-q4_k_m.gguf Q4_K_M

# 4. Import to Ollama
ollama create granite-aj:8b -f Modelfile
```

## Training Configuration (RTX 4090)

Optimized settings in `configs/qlora_config.yaml`:

| Parameter              | Value                               | Notes                         |
| ---------------------- | ----------------------------------- | ----------------------------- |
| Base Model             | ibm-granite/granite-3.1-8b-instruct | Apache 2.0 license            |
| Epochs                 | 2-3                                 | Depends on dataset size       |
| Batch Size             | 2                                   | 8B model fits more in VRAM    |
| Gradient Accumulation  | 4                                   | Effective batch = 8           |
| Learning Rate          | 2e-4                                | With cosine scheduler         |
| LoRA Rank              | 64                                  | Higher rank for complex tasks |
| LoRA Alpha             | 128                                 | Scaling factor (2x rank)      |
| Quantization           | 4-bit NF4                           | BitsAndBytes config           |
| Max Seq Length         | 8192                                | Granite supports up to 128k   |
| Optimizer              | paged_adamw_8bit                    | Memory efficient              |
| Gradient Checkpointing | true                                | Reduces VRAM usage            |

## External Datasets: Agentic Tool-Use

The pipeline downloads function-calling and agentic reasoning datasets (all examples by default):

**Glaive Function-Calling v2** (glaiveai/glaive-function-calling-v2)

- ~113K function-calling examples with tool schemas
- Diverse tool categories: search, math, file ops, APIs

**AgentInstruct** (THUDM/AgentInstruct)

- ~1.8M multi-turn agentic reasoning examples
- Planning, execution, error recovery patterns
- Categories: OS, DB, ALFWorld, WebShop, KG, Mind2Web

**Toucan-1.5M** (Agent-Ark/Toucan-1.5M)

- ~519K real MCP tool-use trajectories (Kimi-K2 subset)
- Synthesized from 495 real-world Model Context Protocols
- 2,000+ tools across diverse categories
- Quality-assessed with LLM-as-judge

**Custom AJ Data** (local)

- Domain-specific training (43+ generators, 5K+ examples)
- FunnelCloud agent integration examples
- Shutdown safety & target disambiguation

## Requirements

- **Python**: 3.10+ (3.13 works in WSL)
- **CUDA**: 12.0+ (cuDNN 8.9+)
- **VRAM**: 24GB recommended (RTX 4090 or better)
- **System RAM**: 32GB+ recommended
- **Storage**: ~100GB (model cache + checkpoints)
- **Platform**: WSL2 recommended for Windows (better CUDA support)

### Python Dependencies

```bash
pip install torch>=2.1.0 transformers>=4.36.0 peft>=0.7.0 trl>=0.7.0 \
    bitsandbytes>=0.41.0 accelerate>=0.25.0 datasets>=2.16.0 \
    sentencepiece tiktoken pyyaml
```

### Unsloth (Recommended - 2x Faster Training)

Unsloth provides optimized training with 2x speed and 50% less VRAM. Install in WSL2:

```bash
# Install Unsloth (requires Linux/WSL2 - won't work on native Windows)
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

# Or with conda (alternative)
conda install -c conda-forge unsloth
```

The training script automatically uses Unsloth when available, falling back to standard PEFT if not.

**Unsloth Benefits:**

- 2x faster training speed
- 50% less VRAM usage
- Better gradient checkpointing
- Works great on RTX 4090

### WSL2 Setup (Recommended for Windows)

Training works best in WSL2 due to better CUDA/bitsandbytes/unsloth support:

```bash
# In WSL terminal
cd /mnt/c/Code/aj.westerfield.cloud/training

# Create venv and install
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install PyTorch with CUDA
pip install torch --index-url https://download.pytorch.org/whl/cu121

# Install training dependencies (including unsloth for 2x speed)
pip install transformers datasets peft trl bitsandbytes accelerate sentencepiece tiktoken pyyaml
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

# Verify GPU
python -c "import torch; print(torch.cuda.get_device_name(0))"

# Verify Unsloth
python -c "from unsloth import FastLanguageModel; print('Unsloth OK')"
```

## Cloud Training (Faster)

For faster training, consider cloud GPU options:

| Provider    | GPU       | Est. Time | Est. Cost |
| ----------- | --------- | --------- | --------- |
| RunPod      | A100 80GB | 3-4 hours | $8-12     |
| Lambda Labs | A100 80GB | 3-4 hours | $8-12     |
| RunPod      | H100      | 2 hours   | $6-10     |

Upload `train_pipeline.py`, `scripts/`, `configs/`, and `data/`, then run.

## Monitoring Training

Training outputs to console with progress bars. Key metrics:

- **Loss**: Should decrease from ~1.5 to ~0.5
- **Speed**: ~5-8 it/s on RTX 4090 with Unsloth (8B model)
- **TF32**: Enabled automatically for 10-15% speed boost

Checkpoints saved to `checkpoints/` every 500 steps.

## Troubleshooting

### Out of Memory

- Reduce `per_device_train_batch_size` to 1
- Increase `gradient_accumulation_steps`
- Enable `gradient_checkpointing=True`

### torchao/TF32 Warnings

The pipeline suppresses these automatically. If you see warnings about `torch.int1`, they're harmless.

### Model Download Slow

- Model (~16GB for 8B) is cached after first download
- Check `~/.cache/huggingface/hub/`

### Unsloth Not Available

Falls back to standard PEFT automatically. Training will be slower but still works.

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
