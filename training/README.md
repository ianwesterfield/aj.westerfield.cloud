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
- **Total Examples**: ~25,000+ (5,000+ custom + 20,000 IBM Granite)
- **Hardware**: RTX 4090 (24GB) via WSL2 or cloud A100
- **Training Time**: ~6-8 hours on RTX 4090, ~3-4 hours on A100
- **Training Pipeline**: `train_pipeline.py` handles everything end-to-end
- **External Data**: IBM Granite 3.1 Language Instruction dataset

## Directory Structure

```
training/
├── data/                    # Training datasets (45+ JSONL files)
│   ├── all_training_data.jsonl    # Combined dataset (5,205 examples)
│   ├── ibm_granite.jsonl          # IBM Granite filtered data (~20K)
│   ├── dataset_stats.json         # Statistics by domain
│   └── [domain].jsonl             # Individual domain files
├── scripts/                 # Training & generation scripts
│   ├── train_pipeline.py          # ★ Master pipeline (run this!)
│   ├── prepare_ibm_granite.py     # Download/filter IBM Granite
│   ├── generate_all.py            # Run all domain generators
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
│   ├── qlora_config_4090.yaml     # ★ RTX 4090 optimized config
│   └── qlora_config.yaml          # Generic config
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

# Run full pipeline (downloads data, merges, trains)
python scripts/train_pipeline.py

# Or with custom settings
python scripts/train_pipeline.py --max-download 100000 --target 30000 --epochs 3
```

The pipeline handles everything:

1. ✅ Checks requirements (torch, CUDA, etc.)
2. ✅ Downloads IBM Granite dataset (if needed)
3. ✅ Merges all training data with deduplication
4. ✅ Runs QLoRA fine-tuning
5. ✅ Saves checkpoints for export

### Manual Steps (Alternative)

#### Generate Training Data

```bash
# Generate all training data (runs 43 generators)
python scripts/generate_all.py

# Expand all domains to 100+ examples
python scripts/bulk_expand.py

# Download IBM Granite dataset
python scripts/prepare_ibm_granite.py --max-download 100000 --target 20000
```

#### Run Training

```bash
# QLoRA training with config
python scripts/train_qlora.py --config configs/qlora_config_4090.yaml
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

## Training Configuration (RTX 4090)

Optimized settings in `configs/qlora_config_4090.yaml`:

| Parameter              | Value            | Notes                               |
| ---------------------- | ---------------- | ----------------------------------- |
| Epochs                 | 2                | Sufficient for instruction tuning   |
| Batch Size             | 1                | Limited by VRAM                     |
| Gradient Accumulation  | 8                | Effective batch = 8                 |
| Learning Rate          | 2e-4             | With cosine scheduler               |
| LoRA Rank              | 64               | Higher rank for complex tasks       |
| LoRA Alpha             | 128              | Scaling factor (2x rank)            |
| Quantization           | 4-bit NF4        | BitsAndBytes config                 |
| Attention              | SDPA             | PyTorch native (Windows compatible) |
| Max Seq Length         | 4096             | Context window                      |
| Optimizer              | paged_adamw_8bit | Memory efficient                    |
| Gradient Checkpointing | true             | Reduces VRAM usage                  |

## External Dataset: IBM Granite

The pipeline downloads [IBM Granite 3.1 Language Instruction](https://huggingface.co/datasets/ibm-granite/granite-3.1-language-instruction):

- **Source**: ~100K high-quality instruction examples
- **Categories**: Coding, reasoning, math, Q&A, instruction-following
- **Filtering**: Prioritizes coding/reasoning, removes duplicates
- **Target**: 20K examples after filtering
- **Format**: Converted to ChatML format for Qwen

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
- **Steps**: ~6,000 total (2 epochs × 25K examples / 8 effective batch)
- **Speed**: ~3-4 it/s on RTX 4090

Checkpoints saved to `checkpoints/` every 500 steps.

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
