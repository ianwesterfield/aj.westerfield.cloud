#!/usr/bin/env python3
"""
Merge LoRA adapter with base model and export to GGUF for Ollama.
Run on Vast.ai or any machine with enough VRAM/RAM.
"""

import os
import argparse
import subprocess
from pathlib import Path

def merge_lora(base_model: str, lora_path: str, output_path: str):
    """Merge LoRA adapter with base model using PEFT."""
    print(f"🔄 Loading base model: {base_model}")
    
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    import torch
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(lora_path, trust_remote_code=True)
    
    # Load base model in fp16 to save memory
    print("📦 Loading base model (this will download ~65GB if not cached)...")
    base = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    
    # Load and merge LoRA
    print(f"🔗 Loading LoRA adapter from: {lora_path}")
    model = PeftModel.from_pretrained(base, lora_path)
    
    print("🔀 Merging weights...")
    model = model.merge_and_unload()
    
    # Save merged model
    print(f"💾 Saving merged model to: {output_path}")
    os.makedirs(output_path, exist_ok=True)
    model.save_pretrained(output_path, safe_serialization=True)
    tokenizer.save_pretrained(output_path)
    
    print("✅ Merge complete!")
    return output_path


def convert_to_gguf(model_path: str, output_file: str, quantization: str = "q4_k_m"):
    """Convert HuggingFace model to GGUF format using llama.cpp."""
    print(f"🔄 Converting to GGUF with {quantization} quantization...")
    
    # Check if llama.cpp is available
    llama_cpp_path = Path.home() / "llama.cpp"
    if not llama_cpp_path.exists():
        print("📥 Cloning llama.cpp...")
        subprocess.run([
            "git", "clone", "--depth=1",
            "https://github.com/ggerganov/llama.cpp.git",
            str(llama_cpp_path)
        ], check=True)
    
    convert_script = llama_cpp_path / "convert_hf_to_gguf.py"
    
    # Install requirements if needed
    subprocess.run([
        "pip", "install", "-q", "gguf", "numpy", "sentencepiece"
    ], check=True)
    
    # Convert to GGUF (f16 first, then quantize)
    f16_output = output_file.replace(".gguf", "-f16.gguf")
    print(f"📄 Converting to F16 GGUF: {f16_output}")
    
    subprocess.run([
        "python", str(convert_script),
        model_path,
        "--outfile", f16_output,
        "--outtype", "f16"
    ], check=True)
    
    # Quantize
    print(f"📉 Quantizing to {quantization}: {output_file}")
    quantize_bin = llama_cpp_path / "build" / "bin" / "llama-quantize"
    
    if not quantize_bin.exists():
        # Build llama.cpp
        print("🔨 Building llama.cpp (this may take a few minutes)...")
        build_dir = llama_cpp_path / "build"
        build_dir.mkdir(exist_ok=True)
        subprocess.run(["cmake", "..", "-DGGML_CUDA=ON"], cwd=build_dir, check=True)
        subprocess.run(["cmake", "--build", ".", "--config", "Release", "-j"], cwd=build_dir, check=True)
    
    subprocess.run([
        str(quantize_bin),
        f16_output,
        output_file,
        quantization.upper()
    ], check=True)
    
    # Clean up f16 file to save space
    print(f"🗑️ Removing intermediate F16 file...")
    os.remove(f16_output)
    
    print(f"✅ GGUF created: {output_file}")
    return output_file


def main():
    parser = argparse.ArgumentParser(description="Merge LoRA and export to GGUF")
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-32B-Instruct",
                        help="Base model name or path")
    parser.add_argument("--lora-path", default="/output/lora_adapter",
                        help="Path to LoRA adapter")
    parser.add_argument("--merged-path", default="/output/merged_model",
                        help="Path to save merged model")
    parser.add_argument("--gguf-output", default="/output/qwen2.5-32b-aj-q4_k_m.gguf",
                        help="Output GGUF file path")
    parser.add_argument("--quantization", default="q4_k_m",
                        choices=["q4_0", "q4_k_m", "q5_k_m", "q6_k", "q8_0", "f16"],
                        help="Quantization type")
    parser.add_argument("--skip-merge", action="store_true",
                        help="Skip merge step (use if already merged)")
    parser.add_argument("--skip-convert", action="store_true",
                        help="Skip GGUF conversion")
    
    args = parser.parse_args()
    
    # Step 1: Merge LoRA with base model
    if not args.skip_merge:
        merge_lora(args.base_model, args.lora_path, args.merged_path)
    
    # Step 2: Convert to GGUF
    if not args.skip_convert:
        convert_to_gguf(args.merged_path, args.gguf_output, args.quantization)
    
    print("\n" + "="*60)
    print("🎉 All done! Your model is ready.")
    print(f"📁 GGUF file: {args.gguf_output}")
    print("\nTo use in Ollama:")
    print(f"  1. Download the GGUF to your local machine")
    print(f"  2. Create a Modelfile with:")
    print(f'     FROM ./qwen2.5-32b-aj-q4_k_m.gguf')
    print(f"  3. Run: ollama create qwen2.5-aj:32b -f Modelfile")
    print("="*60)


if __name__ == "__main__":
    main()
