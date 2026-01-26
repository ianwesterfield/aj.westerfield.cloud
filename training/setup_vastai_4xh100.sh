#!/bin/bash
# Vast.ai Setup Script for AJ DeepSeek-R1 Training
# Optimized for 4x H100 SXM GPUs (320GB total VRAM)
#
# Instance: vast.ai 4x H100 SXM @ $6.235/hr (Iowa, US)
# Model: DeepSeek-R1-Distill-Qwen-32B
# Target: Agentic intent + conversational adaptation
# Output: Q4_K_M quantized model for RTX 4090 inference
#
# Usage:
#   1. Rent the 4x H100 SXM instance
#   2. Upload this repo to /workspace/training
#   3. Run: chmod +x setup_vastai_4xh100.sh && ./setup_vastai_4xh100.sh
#
# Expected training time: ~3-4 hours
# Estimated cost: ~$20-25

set -e

echo "============================================================"
echo "AJ DeepSeek-R1 Training - Vast.ai Setup (4x H100 SXM)"
echo "============================================================"
echo "Target: Agentic intent + conversational adaptation"
echo "Model: DeepSeek-R1-Distill-Qwen-32B → Q4_K_M for 4090"
echo ""

# Update system
echo "[1/7] Updating system packages..."
apt-get update -qq
apt-get install -y -qq git-lfs htop nvtop tmux

# Install Python dependencies
echo "[2/7] Installing Python dependencies..."
pip install --upgrade pip --quiet

# Install PyTorch with CUDA 12.4
echo "[3/7] Installing PyTorch (CUDA 12.4)..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124 --quiet

# Install Flash Attention (pre-built for speed)
echo "[4/7] Installing Flash Attention..."
pip install flash-attn --no-build-isolation --quiet

# Install training stack
echo "[5/7] Installing training libraries..."
pip install --quiet \
    transformers>=4.45.0 \
    datasets>=2.14.0 \
    peft>=0.7.0 \
    trl>=0.7.0 \
    bitsandbytes>=0.41.0 \
    accelerate>=0.25.0 \
    tensorboard \
    sentencepiece \
    protobuf \
    wandb \
    deepspeed

# Install Unsloth for 2x training speedup
echo "[6/7] Installing Unsloth..."
pip install "unsloth @ git+https://github.com/unslothai/unsloth.git" --quiet

# Verify GPU setup
echo ""
echo "[7/7] Verifying GPU setup..."
python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU count: {torch.cuda.device_count()}')
total_vram = 0
for i in range(torch.cuda.device_count()):
    props = torch.cuda.get_device_properties(i)
    vram_gb = props.total_memory / 1e9
    total_vram += vram_gb
    print(f'  GPU {i}: {props.name} ({vram_gb:.1f} GB)')
print(f'Total VRAM: {total_vram:.0f} GB')
"

# Download agentic datasets
mkdir -p data
echo ""
echo "============================================================"
echo "Downloading Agentic Training Datasets"
echo "============================================================"
echo "Sources: xLAM (113K) + AgentInstruct (1.8M) + Toucan (1.5M)"
echo ""

# Run dataset prep (this downloads and converts)
python scripts/prepare_agentic_datasets.py -y

# Merge all datasets
echo ""
echo "============================================================"
echo "Merging Training Datasets"
echo "============================================================"
python scripts/train_pipeline.py --skip-agentic --skip-train --skip-export -y

# Verify data
DATA_FILE="data/all_training_data_merged.jsonl"
if [ -f "$DATA_FILE" ]; then
    DATA_SIZE=$(du -h "$DATA_FILE" | cut -f1)
    DATA_LINES=$(wc -l < "$DATA_FILE")
    echo ""
    echo "✅ Training data ready: $DATA_FILE"
    echo "   Size: $DATA_SIZE"
    echo "   Examples: $DATA_LINES"
fi

# Pre-download the model to avoid training startup delay
echo ""
echo "============================================================"
echo "Pre-downloading DeepSeek-R1-Distill-Qwen-32B"
echo "============================================================"
python -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
print('Downloading tokenizer...')
AutoTokenizer.from_pretrained('deepseek-ai/DeepSeek-R1-Distill-Qwen-32B', trust_remote_code=True)
print('Downloading model config (weights will load during training)...')
from transformers import AutoConfig
AutoConfig.from_pretrained('deepseek-ai/DeepSeek-R1-Distill-Qwen-32B', trust_remote_code=True)
print('✅ Model ready')
"

echo ""
echo "============================================================"
echo "✅ Setup complete! Ready to train."
echo "============================================================"
echo ""
echo "To start training (4x H100):"
echo ""
echo "  accelerate launch --multi_gpu --num_processes=4 \\"
echo "    scripts/train_qlora.py --config configs/qlora_config_4xh100.yaml"
echo ""
echo "Or use tmux to keep it running after disconnect:"
echo ""
echo "  tmux new -s train"
echo "  accelerate launch --multi_gpu --num_processes=4 \\"
echo "    scripts/train_qlora.py --config configs/qlora_config_4xh100.yaml"
echo "  # Ctrl+B then D to detach, 'tmux attach -t train' to reconnect"
echo ""
echo "To monitor training:"
echo "  tensorboard --logdir checkpoints-deepseek-r1-4xh100 --bind_all"
echo "  nvtop  # GPU utilization"
echo ""
echo "Estimated time: ~3-4 hours (~\$20-25)"
echo ""
