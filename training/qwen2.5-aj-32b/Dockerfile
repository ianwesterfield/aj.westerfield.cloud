# Training container for Qwen 2.5 AJ 32B
# Requires NVIDIA GPU with ~24GB VRAM

FROM nvidia/cuda:12.1-devel-ubuntu22.04

# Set environment
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
  python3.10 \
  python3-pip \
  python3.10-venv \
  git \
  wget \
  cmake \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Install Python dependencies
RUN pip3 install --upgrade pip

# Install PyTorch with CUDA
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install Unsloth (optimized for QLoRA training)
RUN pip3 install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

# Install other training dependencies
RUN pip3 install \
  transformers>=4.36.0 \
  datasets>=2.15.0 \
  accelerate>=0.25.0 \
  peft>=0.7.0 \
  trl>=0.7.0 \
  bitsandbytes>=0.41.0 \
  scipy \
  sentencepiece \
  protobuf \
  pyyaml

# Install llama.cpp for GGUF conversion
RUN git clone https://github.com/ggerganov/llama.cpp.git /opt/llama.cpp && \
  cd /opt/llama.cpp && \
  cmake -B build -DGGML_CUDA=ON && \
  cmake --build build --config Release -j$(nproc)

# Add llama.cpp to PATH
ENV PATH="/opt/llama.cpp/build/bin:${PATH}"

# Copy training files
COPY configs/ /app/configs/
COPY scripts/ /app/scripts/
COPY data/ /app/data/

# Default command
CMD ["python3", "scripts/train_qlora.py"]
