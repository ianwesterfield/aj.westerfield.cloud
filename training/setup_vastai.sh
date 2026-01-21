#!/bin/bash
# Vast.ai Setup Script for AJ Granite Training
# Optimized for 2x H200 GPUs
#
# Usage:
#   1. Upload training scripts/configs + small local JSONL files to vast.ai
#   2. Run: chmod +x setup_vastai.sh && ./setup_vastai.sh
#
# Expected training time: ~4-6 hours

set -e

echo "============================================================"
echo "AJ Granite Training - Vast.ai Setup (2x H200)"
echo "============================================================"

# Update system
echo "Updating system packages..."
apt-get update -qq

# Install Python dependencies in correct order
echo "Installing Python dependencies..."
pip install --upgrade pip

# Install PyTorch FIRST (required for flash-attn)
echo "Installing PyTorch..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Install flash-attn from pre-built wheel (much faster than building)
echo "Installing Flash Attention (pre-built)..."
pip install flash-attn --no-build-isolation

# Install training libraries
echo "Installing training libraries..."
pip install transformers>=4.45.0 datasets>=2.14.0 peft>=0.7.0 trl>=0.7.0
pip install bitsandbytes>=0.41.0 accelerate>=0.25.0
pip install tensorboard sentencepiece protobuf

# Install Unsloth (without the flash-attn dependency since we already have it)
echo "Installing Unsloth..."
pip install "unsloth @ git+https://github.com/unslothai/unsloth.git"

# Verify GPU setup
echo ""
echo "Verifying GPU setup..."
python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU count: {torch.cuda.device_count()}')
for i in range(torch.cuda.device_count()):
    props = torch.cuda.get_device_properties(i)
    print(f'  GPU {i}: {props.name} ({props.total_memory / 1e9:.1f} GB)')
"

# Download agentic datasets if not present
mkdir -p data
echo ""
echo "============================================================"
echo "Downloading Agentic Training Datasets"
echo "============================================================"

# Run the dataset preparation script (downloads xLAM, AgentInstruct, Toucan)
python scripts/prepare_agentic_datasets.py -y

# Merge all datasets
echo ""
echo "============================================================"
echo "Merging Training Datasets"
echo "============================================================"
python scripts/train_pipeline.py --skip-agentic --skip-train --skip-export -y

DATA_FILE="data/all_training_data_merged.jsonl"
if [ -f "$DATA_FILE" ]; then
    DATA_SIZE=$(du -h "$DATA_FILE" | cut -f1)
    DATA_LINES=$(wc -l < "$DATA_FILE")
    echo ""
    echo "Training data: $DATA_FILE"
    echo "  Size: $DATA_SIZE"
    echo "  Examples: $DATA_LINES"
fi

echo ""
echo "============================================================"
echo "Setup complete! Ready to train."
echo "============================================================"
echo ""
echo "To start training:"
echo "  # Single GPU:"
echo "  python scripts/train_qlora.py --config configs/qlora_config_h200.yaml"
echo ""
echo "  # Multi-GPU (recommended for 2x H200):"
echo "  accelerate launch --multi_gpu --num_processes=2 scripts/train_qlora.py --config configs/qlora_config_h200.yaml"
echo ""
echo "To monitor training:"
echo "  tensorboard --logdir checkpoints --bind_all"
echo ""
