#!/usr/bin/env python3
"""
LoRA Adapter Merge Script

Merges multiple LoRA adapters into a single model with weighted combination.
Supports TIES and linear merging strategies.

Usage:
    python merge_adapters.py --config merge_config.yaml
    python merge_adapters.py --base Qwen/Qwen2.5-32B-Instruct \
        --adapters checkpoints-agent:1.0 checkpoints-chat:0.7 \
        --output merged-model
"""

import os
import argparse
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import torch
from tqdm import tqdm

try:
    from peft import PeftModel, PeftConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    PEFT_AVAILABLE = True
except ImportError:
    PEFT_AVAILABLE = False
    print("PEFT not installed. Install with: pip install peft")

try:
    from huggingface_hub import snapshot_download

    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False


def parse_adapter_spec(spec: str) -> Tuple[str, float]:
    """Parse 'path:weight' or 'path' (default weight 1.0)."""
    if ":" in spec:
        path, weight = spec.rsplit(":", 1)
        return path, float(weight)
    return spec, 1.0


def load_base_model(model_name: str, device_map: str = "auto"):
    """Load base model in fp16/bf16 for merging."""
    print(f"Loading base model: {model_name}")

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map=device_map,
        trust_remote_code=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

    return model, tokenizer


def merge_adapters_linear(
    base_model,
    adapter_paths: List[str],
    weights: List[float],
) -> None:
    """
    Linear merge: weighted sum of adapter deltas.

    merged = base + w1*delta1 + w2*delta2 + ...

    Modifies base_model in place.
    """
    print(f"\nMerging {len(adapter_paths)} adapters (linear)...")
    print(f"  Weights: {list(zip(adapter_paths, weights))}")

    # Accumulate weighted deltas
    merged_deltas = {}

    for adapter_path, weight in zip(adapter_paths, weights):
        print(f"\n  Loading adapter: {adapter_path} (weight={weight})")

        # Load adapter
        peft_model = PeftModel.from_pretrained(base_model, adapter_path)

        # Get the LoRA layers
        for name, param in peft_model.named_parameters():
            if "lora_" in name:
                # Scale by weight
                delta = param.data * weight

                if name in merged_deltas:
                    merged_deltas[name] += delta
                else:
                    merged_deltas[name] = delta.clone()

        # Unload this adapter
        peft_model = peft_model.unload()

    # Apply merged deltas
    print("\n  Applying merged deltas to base model...")

    # Reload as PEFT model with first adapter as template
    peft_model = PeftModel.from_pretrained(base_model, adapter_paths[0])

    for name, param in peft_model.named_parameters():
        if name in merged_deltas:
            param.data = merged_deltas[name]

    # Merge and unload
    merged_model = peft_model.merge_and_unload()

    return merged_model


def merge_adapters_ties(
    base_model,
    adapter_paths: List[str],
    weights: List[float],
    density: float = 0.5,
) -> None:
    """
    TIES merge: Trim, Elect Sign, Merge.

    Better at resolving conflicts between adapters.

    1. Trim: Keep only top-k% of weights by magnitude
    2. Elect: For each param, choose sign by majority vote
    3. Merge: Average magnitudes with elected sign
    """
    print(f"\nMerging {len(adapter_paths)} adapters (TIES, density={density})...")

    all_deltas = []

    # Collect all deltas
    for adapter_path, weight in zip(adapter_paths, weights):
        print(f"  Loading adapter: {adapter_path}")

        peft_model = PeftModel.from_pretrained(base_model, adapter_path)

        adapter_deltas = {}
        for name, param in peft_model.named_parameters():
            if "lora_" in name:
                adapter_deltas[name] = param.data * weight

        all_deltas.append(adapter_deltas)
        peft_model = peft_model.unload()

    # TIES merge
    merged_deltas = {}
    all_names = set()
    for d in all_deltas:
        all_names.update(d.keys())

    for name in tqdm(all_names, desc="  TIES merging"):
        tensors = [d.get(name) for d in all_deltas if name in d]
        if not tensors:
            continue

        stacked = torch.stack(tensors)

        # Trim: zero out smallest values
        if density < 1.0:
            flat = stacked.abs().flatten()
            k = int(len(flat) * density)
            if k > 0:
                threshold = torch.kthvalue(flat, len(flat) - k).values
                mask = stacked.abs() >= threshold
                stacked = stacked * mask

        # Elect sign: majority vote
        signs = torch.sign(stacked)
        sign_sum = signs.sum(dim=0)
        elected_sign = torch.sign(sign_sum)
        elected_sign[elected_sign == 0] = 1  # Break ties

        # Merge: mean of magnitudes with elected sign
        magnitudes = stacked.abs()
        mean_magnitude = magnitudes.mean(dim=0)
        merged_deltas[name] = elected_sign * mean_magnitude

    # Apply to model
    print("  Applying TIES-merged deltas...")
    peft_model = PeftModel.from_pretrained(base_model, adapter_paths[0])

    for name, param in peft_model.named_parameters():
        if name in merged_deltas:
            param.data = merged_deltas[name]

    return peft_model.merge_and_unload()


def save_merged_model(model, tokenizer, output_path: str):
    """Save merged model in HuggingFace format."""
    print(f"\nSaving merged model to: {output_path}")

    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)

    # Save merge info
    info = {
        "merged": True,
        "format": "huggingface",
        "note": "Convert to GGUF with llama.cpp for Ollama",
    }
    with open(output_path / "merge_info.json", "w") as f:
        import json

        json.dump(info, f, indent=2)

    print(
        f"  Saved! Total size: {sum(f.stat().st_size for f in output_path.rglob('*') if f.is_file()) / 1e9:.2f} GB"
    )


def convert_to_gguf(model_path: str, output_path: str, quantization: str = "Q4_K_M"):
    """Convert HuggingFace model to GGUF format for Ollama."""
    print(f"\nConverting to GGUF ({quantization})...")

    import subprocess

    # Check for llama.cpp
    llama_cpp_path = os.environ.get("LLAMA_CPP_PATH", "../llama.cpp")
    convert_script = Path(llama_cpp_path) / "convert_hf_to_gguf.py"
    quantize_bin = Path(llama_cpp_path) / "build" / "bin" / "llama-quantize"

    if not convert_script.exists():
        print(f"  WARNING: llama.cpp not found at {llama_cpp_path}")
        print(f"  Set LLAMA_CPP_PATH environment variable or convert manually:")
        print(
            f"    python convert_hf_to_gguf.py {model_path} --outfile {output_path}.gguf"
        )
        return

    # Convert to f16 GGUF
    f16_path = f"{output_path}-f16.gguf"
    subprocess.run(
        [
            "python",
            str(convert_script),
            model_path,
            "--outfile",
            f16_path,
        ],
        check=True,
    )

    # Quantize
    final_path = f"{output_path}-{quantization}.gguf"
    subprocess.run(
        [
            str(quantize_bin),
            f16_path,
            final_path,
            quantization,
        ],
        check=True,
    )

    print(f"  GGUF saved: {final_path}")

    # Clean up f16
    os.remove(f16_path)


def main():
    parser = argparse.ArgumentParser(description="Merge LoRA adapters")
    parser.add_argument("--config", type=str, help="Path to merge config YAML")
    parser.add_argument("--base", type=str, help="Base model name/path")
    parser.add_argument(
        "--adapters", nargs="+", help="Adapter paths with weights (path:weight)"
    )
    parser.add_argument(
        "--output", type=str, default="merged-model", help="Output path"
    )
    parser.add_argument(
        "--method", choices=["linear", "ties"], default="linear", help="Merge method"
    )
    parser.add_argument(
        "--ties-density", type=float, default=0.5, help="TIES trim density"
    )
    parser.add_argument("--to-gguf", action="store_true", help="Also convert to GGUF")
    parser.add_argument(
        "--gguf-quant", type=str, default="Q4_K_M", help="GGUF quantization"
    )

    args = parser.parse_args()

    # Load from config or args
    if args.config:
        with open(args.config) as f:
            config = yaml.safe_load(f)
        base_model = config["base_model"]
        adapters = config["adapters"]  # List of {path, weight}
        output = config.get("output", "merged-model")
        method = config.get("method", "linear")
        density = config.get("ties_density", 0.5)
    else:
        if not args.base or not args.adapters:
            parser.error("Either --config or --base and --adapters required")
        base_model = args.base
        adapters = [parse_adapter_spec(a) for a in args.adapters]
        output = args.output
        method = args.method
        density = args.ties_density

    # Parse adapters if from config
    if isinstance(adapters[0], dict):
        adapter_paths = [a["path"] for a in adapters]
        weights = [a.get("weight", 1.0) for a in adapters]
    else:
        adapter_paths, weights = zip(*adapters)
        adapter_paths, weights = list(adapter_paths), list(weights)

    if not PEFT_AVAILABLE:
        print("ERROR: PEFT library required. Install with: pip install peft")
        return 1

    # Load base model
    model, tokenizer = load_base_model(base_model)

    # Merge
    if method == "ties":
        merged = merge_adapters_ties(model, adapter_paths, weights, density)
    else:
        merged = merge_adapters_linear(model, adapter_paths, weights)

    # Save
    save_merged_model(merged, tokenizer, output)

    # Convert to GGUF if requested
    if args.to_gguf:
        convert_to_gguf(output, output, args.gguf_quant)

    print("\n✅ Merge complete!")
    print(f"\nNext steps:")
    print(f"  1. Convert to GGUF (if not done):")
    print(f"     python llama.cpp/convert_hf_to_gguf.py {output}")
    print(f"  2. Create Ollama model:")
    print(f"     ollama create qwen2.5-aj:32b-merged -f Modelfile")


if __name__ == "__main__":
    main()
