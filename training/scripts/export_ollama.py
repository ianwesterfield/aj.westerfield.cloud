#!/usr/bin/env python3
"""
Export fine-tuned Qwen 2.5 32B to Ollama format.

This script:
1. Merges LoRA weights with base model
2. Quantizes to Q4_K_M for efficient inference
3. Creates Ollama Modelfile
4. Builds the Ollama model
"""

import os
import subprocess
import shutil
from pathlib import Path
import yaml

try:
    from unsloth import FastLanguageModel
    UNSLOTH_AVAILABLE = True
except ImportError:
    UNSLOTH_AVAILABLE = False

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CONFIG_PATH = PROJECT_DIR / "configs" / "qlora_config.yaml"
OUTPUT_DIR = PROJECT_DIR / "output"
LORA_DIR = OUTPUT_DIR / "lora_adapter"
MERGED_DIR = OUTPUT_DIR / "merged_model"
GGUF_DIR = OUTPUT_DIR / "gguf"


def load_config():
    """Load training configuration."""
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)


def merge_lora_weights(config):
    """Merge LoRA adapter with base model."""
    print("\n1. Merging LoRA weights with base model...")
    
    if not UNSLOTH_AVAILABLE:
        print("ERROR: Unsloth required. Install with: pip install unsloth")
        return False
    
    # Load the fine-tuned model
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(LORA_DIR),
        max_seq_length=config["model"]["max_seq_length"],
        dtype=None,
        load_in_4bit=True,
    )
    
    # Merge and save in 16-bit
    print("   Merging weights (this may take a while)...")
    model.save_pretrained_merged(
        str(MERGED_DIR),
        tokenizer,
        save_method="merged_16bit",
    )
    
    print(f"   Merged model saved to: {MERGED_DIR}")
    return True


def convert_to_gguf(config):
    """Convert merged model to GGUF format."""
    print("\n2. Converting to GGUF format...")
    
    GGUF_DIR.mkdir(parents=True, exist_ok=True)
    
    # Use llama.cpp's convert script
    # This requires llama.cpp to be installed
    convert_script = shutil.which("convert-hf-to-gguf.py")
    
    if not convert_script:
        # Try common locations
        possible_paths = [
            Path.home() / "llama.cpp" / "convert-hf-to-gguf.py",
            Path("/opt/llama.cpp/convert-hf-to-gguf.py"),
        ]
        for p in possible_paths:
            if p.exists():
                convert_script = str(p)
                break
    
    if not convert_script:
        print("   WARNING: llama.cpp convert script not found.")
        print("   Install llama.cpp and ensure convert-hf-to-gguf.py is in PATH")
        print("   Or manually convert using: python convert-hf-to-gguf.py <model_dir>")
        return False
    
    output_file = GGUF_DIR / "qwen2.5-aj-32b-f16.gguf"
    
    cmd = [
        "python", convert_script,
        str(MERGED_DIR),
        "--outfile", str(output_file),
        "--outtype", "f16"
    ]
    
    print(f"   Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"   ERROR: {result.stderr}")
        return False
    
    print(f"   GGUF model saved to: {output_file}")
    return True


def quantize_gguf(config):
    """Quantize GGUF to Q4_K_M."""
    print("\n3. Quantizing to Q4_K_M...")
    
    quantize_bin = shutil.which("llama-quantize")
    
    if not quantize_bin:
        possible_paths = [
            Path.home() / "llama.cpp" / "build" / "bin" / "llama-quantize",
            Path("/opt/llama.cpp/build/bin/llama-quantize"),
        ]
        for p in possible_paths:
            if p.exists():
                quantize_bin = str(p)
                break
    
    if not quantize_bin:
        print("   WARNING: llama-quantize not found.")
        print("   Build llama.cpp to get the quantize tool.")
        return False
    
    input_file = GGUF_DIR / "qwen2.5-aj-32b-f16.gguf"
    output_file = GGUF_DIR / "qwen2.5-aj-32b-q4_k_m.gguf"
    
    cmd = [quantize_bin, str(input_file), str(output_file), "Q4_K_M"]
    
    print(f"   Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"   ERROR: {result.stderr}")
        return False
    
    print(f"   Quantized model saved to: {output_file}")
    
    # Clean up f16 version to save space
    if input_file.exists() and output_file.exists():
        print("   Removing f16 version to save space...")
        input_file.unlink()
    
    return True


def create_modelfile(config):
    """Create Ollama Modelfile."""
    print("\n4. Creating Ollama Modelfile...")
    
    modelfile_content = '''# Qwen 2.5 AJ 32B - Fine-tuned for AJ Agent Workloads
FROM ./gguf/qwen2.5-aj-32b-q4_k_m.gguf

# Model parameters optimized for agent tasks
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"

# System prompt for AJ
SYSTEM """You are AJ, an intelligent AI assistant specialized in:
- Breaking down complex tasks into executable steps (OODA loop)
- Selecting appropriate tools for each step
- Managing workspace files and remote execution
- Maintaining safety guardrails

You have access to tools for:
- Workspace: scan_workspace, read_file, write_file, append_to_file, delete_file
- Remote: list_agents, remote_execute
- Local: execute_shell
- Control: complete, none

Always verify agent availability before remote execution.
Never fabricate results - if something fails, report it honestly.
Stop if you detect you're in a loop."""

TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
{{ .Response }}<|im_end|>"""

LICENSE """Apache 2.0 - Fine-tuned from Qwen 2.5 32B for AJ project."""
'''
    
    modelfile_path = PROJECT_DIR / "Modelfile"
    with open(modelfile_path, 'w') as f:
        f.write(modelfile_content)
    
    print(f"   Modelfile saved to: {modelfile_path}")
    return True


def build_ollama_model(config):
    """Build Ollama model from Modelfile."""
    print("\n5. Building Ollama model...")
    
    model_name = config["export"]["ollama_model_name"]
    modelfile_path = PROJECT_DIR / "Modelfile"
    
    # Check if ollama is available
    if not shutil.which("ollama"):
        print("   WARNING: ollama not found in PATH.")
        print(f"   To build manually, run:")
        print(f"   cd {PROJECT_DIR} && ollama create {model_name} -f Modelfile")
        return False
    
    cmd = ["ollama", "create", model_name, "-f", str(modelfile_path)]
    
    print(f"   Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_DIR), capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"   ERROR: {result.stderr}")
        return False
    
    print(f"   Successfully created: {model_name}")
    return True


def main():
    """Main export pipeline."""
    print("=" * 60)
    print("Export Qwen 2.5 AJ 32B to Ollama")
    print("=" * 60)
    
    config = load_config()
    
    # Check for LoRA adapter
    if not LORA_DIR.exists():
        print(f"\nERROR: No trained model found at {LORA_DIR}")
        print("Run train_qlora.py first to fine-tune the model.")
        return
    
    # Pipeline steps
    steps = [
        ("Merge LoRA weights", lambda: merge_lora_weights(config)),
        ("Convert to GGUF", lambda: convert_to_gguf(config)),
        ("Quantize to Q4_K_M", lambda: quantize_gguf(config)),
        ("Create Modelfile", lambda: create_modelfile(config)),
        ("Build Ollama model", lambda: build_ollama_model(config)),
    ]
    
    for step_name, step_fn in steps:
        success = step_fn()
        if not success:
            print(f"\n⚠️  Step '{step_name}' had issues. Check output above.")
            # Continue anyway - some steps can be done manually
    
    print("\n" + "=" * 60)
    print("Export Complete!")
    print("=" * 60)
    print("\nTo use the model:")
    print(f"  ollama run {config['export']['ollama_model_name']}")
    print("\nTo update your docker-compose.yaml:")
    print(f"  Change OLLAMA_MODEL to: {config['export']['ollama_model_name']}")


if __name__ == "__main__":
    main()
