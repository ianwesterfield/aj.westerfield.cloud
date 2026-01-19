#!/usr/bin/env python3
"""
QLoRA Fine-tuning script for IBM Granite 4.0-H-Small (32B MoE).

Uses Unsloth for efficient 4-bit training when available (2x faster, 50% less VRAM).
Falls back to standard PEFT/bitsandbytes if Unsloth is not installed.

Granite 4.0-H-Small has:
- 32B total params, 9B active (MoE + Mamba2 hybrid)
- Built-in tool calling via <tool_call> format
- 128K context length
- Apache 2.0 license

Optimized for RTX 4090 (24GB VRAM) in WSL2.
"""

import os
import sys
import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# Check for GPU
import torch
if not torch.cuda.is_available():
    print("WARNING: No CUDA GPU detected. Training will be extremely slow or fail.")
    print("For CPU-only machines, consider using cloud GPU services.")

# Try to import Unsloth (preferred for WSL2/Linux)
UNSLOTH_AVAILABLE = False
try:
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from unsloth import FastLanguageModel
        from unsloth.chat_templates import get_chat_template
    UNSLOTH_AVAILABLE = True
    print("✓ Unsloth available - using optimized training (2x faster)")
except Exception as e:
    print(f"⚠ Unsloth not available: {str(e)[:60]}...")
    print("  Falling back to standard PEFT training")

# Standard imports for fallback
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer
from datasets import Dataset

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load training configuration."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_training_data(merged_file: Optional[Path] = None) -> Dataset:
    """Load training data from merged file or all JSONL files."""
    all_examples = []
    
    # Prefer merged file if it exists
    if merged_file and merged_file.exists():
        print(f"  Loading merged dataset: {merged_file.name}")
        with open(merged_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    all_examples.append(json.loads(line))
        print(f"  Loaded {len(all_examples):,} examples")
        return Dataset.from_list(all_examples)
    
    # Fall back to loading all JSONL files
    jsonl_files = sorted(DATA_DIR.glob("*.jsonl"))
    
    if not jsonl_files:
        raise FileNotFoundError(
            f"No training data found in {DATA_DIR}. "
            "Run the pipeline to generate data first."
        )
    
    for filepath in jsonl_files:
        if filepath.name == "all_training_data.jsonl":
            continue  # Skip combined file when loading individual
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    all_examples.append(json.loads(line))
    
    print(f"  Total examples: {len(all_examples):,}")
    return Dataset.from_list(all_examples)


def format_for_granite(example: Dict, tokenizer) -> Dict:
    """Format example using Granite's chat template.
    
    Granite 4.0 uses: <|start_of_role|>role<|end_of_role|>content<|end_of_text|>
    """
    messages = [
        {"role": "system", "content": example.get("system", "You are a helpful assistant.")},
        {"role": "user", "content": example["instruction"]},
        {"role": "assistant", "content": example["response"]},
    ]
    
    text = tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=False
    )
    
    return {"text": text}


def load_model_unsloth(config: Dict):
    """Load model using Unsloth (optimized)."""
    print("\n  Loading with Unsloth (optimized)...")
    
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=config["model"]["base_model"],
        max_seq_length=config["model"]["max_seq_length"],
        dtype=None,  # Auto-detect (bfloat16 on Ampere+)
        load_in_4bit=True,
    )
    
    # Add LoRA adapters with Unsloth's optimizations
    model = FastLanguageModel.get_peft_model(
        model,
        r=config["lora"]["r"],
        lora_alpha=config["lora"]["lora_alpha"],
        lora_dropout=config["lora"]["lora_dropout"],
        target_modules=config["lora"]["target_modules"],
        bias=config["lora"]["bias"],
        use_gradient_checkpointing="unsloth",  # 30% faster
        random_state=42,
    )
    
    return model, tokenizer


def load_model_standard(config: Dict):
    """Load model using standard PEFT/bitsandbytes (fallback)."""
    print("\n  Loading with standard PEFT (slower)...")
    
    # 4-bit quantization config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    
    # Load base model
    model = AutoModelForCausalLM.from_pretrained(
        config["model"]["base_model"],
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        attn_implementation="sdpa",  # PyTorch native attention
    )
    
    tokenizer = AutoTokenizer.from_pretrained(
        config["model"]["base_model"],
        trust_remote_code=True,
    )
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    # Prepare for k-bit training
    model = prepare_model_for_kbit_training(model)
    
    # LoRA config
    lora_config = LoraConfig(
        r=config["lora"]["r"],
        lora_alpha=config["lora"]["lora_alpha"],
        lora_dropout=config["lora"]["lora_dropout"],
        target_modules=config["lora"]["target_modules"],
        bias=config["lora"]["bias"],
        task_type="CAUSAL_LM",
    )
    
    # Add LoRA adapters
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    return model, tokenizer


def main():
    """Main training pipeline."""
    parser = argparse.ArgumentParser(description="QLoRA fine-tuning for Qwen 2.5")
    parser.add_argument("--config", type=str, default="configs/qlora_config_4090.yaml",
                        help="Path to config file")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from latest checkpoint")
    parser.add_argument("--data", type=str, default=None,
                        help="Path to merged training data file")
    parser.add_argument("--no-unsloth", action="store_true",
                        help="Force standard PEFT even if Unsloth available")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Qwen 2.5 AJ 32B - QLoRA Fine-tuning")
    print("=" * 60)
    
    use_unsloth = UNSLOTH_AVAILABLE and not args.no_unsloth
    print(f"Training backend: {'Unsloth (optimized)' if use_unsloth else 'Standard PEFT'}")
    
    # Load config
    print("\n1. Loading configuration...")
    config_path = PROJECT_DIR / args.config
    if not config_path.exists():
        print(f"   ERROR: Config not found: {config_path}")
        sys.exit(1)
    config = load_config(config_path)
    print(f"   Config: {config_path.name}")
    
    # Check VRAM
    if torch.cuda.is_available():
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
        print(f"   VRAM: {vram_gb:.1f} GB")
        
        if vram_gb < 20:
            print("   ⚠ WARNING: Low VRAM. May need to reduce batch size.")
    
    # Load model
    print("\n2. Loading Qwen 2.5 32B with 4-bit quantization...")
    if use_unsloth:
        model, tokenizer = load_model_unsloth(config)
    else:
        model, tokenizer = load_model_standard(config)
    
    # Load training data
    print("\n3. Loading training data...")
    merged_file = Path(args.data) if args.data else DATA_DIR / "merged_training.jsonl"
    dataset = load_training_data(merged_file)
    
    # Format dataset
    print("\n4. Formatting dataset for Granite chat format...")
    dataset = dataset.map(
        lambda x: format_for_granite(x, tokenizer),
        remove_columns=dataset.column_names,
        desc="Formatting"
    )
    
    # Split train/eval
    eval_split = config.get("data", {}).get("eval_split", 0.05)
    seed = config.get("data", {}).get("seed", 42)
    split = dataset.train_test_split(test_size=eval_split, seed=seed)
    train_dataset = split["train"]
    eval_dataset = split["test"]
    
    print(f"   Train examples: {len(train_dataset):,}")
    print(f"   Eval examples: {len(eval_dataset):,}")
    
    # Training arguments
    print("\n5. Configuring training...")
    output_dir = str(PROJECT_DIR / config["training"]["output_dir"])
    
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=config["training"]["num_train_epochs"],
        per_device_train_batch_size=config["training"]["per_device_train_batch_size"],
        gradient_accumulation_steps=config["training"]["gradient_accumulation_steps"],
        learning_rate=config["training"]["learning_rate"],
        weight_decay=config["training"]["weight_decay"],
        warmup_ratio=config["training"]["warmup_ratio"],
        lr_scheduler_type=config["training"]["lr_scheduler_type"],
        logging_steps=config["training"]["logging_steps"],
        save_steps=config["training"]["save_steps"],
        eval_steps=config["training"].get("eval_steps", 500),
        save_total_limit=config["training"]["save_total_limit"],
        fp16=config["training"]["fp16"],
        bf16=config["training"]["bf16"],
        gradient_checkpointing=config["training"]["gradient_checkpointing"],
        optim=config["training"]["optim"],
        max_grad_norm=config["training"]["max_grad_norm"],
        group_by_length=config["training"]["group_by_length"],
        report_to=config["training"].get("report_to", "tensorboard"),
        eval_strategy="steps",
        load_best_model_at_end=True,
        dataloader_num_workers=config["training"].get("dataloader_num_workers", 4),
        dataloader_pin_memory=config["training"].get("dataloader_pin_memory", True),
    )
    
    # Find checkpoint if resuming
    resume_from = None
    if args.resume:
        checkpoints = list(Path(output_dir).glob("checkpoint-*"))
        if checkpoints:
            resume_from = str(max(checkpoints, key=lambda p: int(p.name.split("-")[1])))
            print(f"   Resuming from: {resume_from}")
    
    # Create trainer (TRL 0.24+ uses processing_class instead of tokenizer)
    import trl
    trl_version = tuple(map(int, trl.__version__.split('.')[:2]))
    
    if trl_version >= (0, 24):
        # New API (TRL 0.24+)
        trainer = SFTTrainer(
            model=model,
            processing_class=tokenizer,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            dataset_text_field="text",
            max_seq_length=config["model"]["max_seq_length"],
            args=training_args,
        )
    else:
        # Old API (TRL < 0.24)
        trainer = SFTTrainer(
            model=model,
            tokenizer=tokenizer,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            dataset_text_field="text",
            max_seq_length=config["model"]["max_seq_length"],
            args=training_args,
        )
    
    # Train!
    print("\n6. Starting training...")
    print("=" * 60)
    
    if resume_from:
        trainer.train(resume_from_checkpoint=resume_from)
    else:
        trainer.train()
    
    # Save final model
    print("\n7. Saving final model...")
    final_dir = PROJECT_DIR / "output" / "lora_adapter"
    final_dir.mkdir(parents=True, exist_ok=True)
    
    model.save_pretrained(final_dir)
    tokenizer.save_pretrained(final_dir)
    
    print("\n" + "=" * 60)
    print("✓ Training Complete!")
    print("=" * 60)
    print(f"LoRA adapter saved to: {final_dir}")
    print("\nNext steps:")
    print("  1. Run merge_and_export.py to create merged model")
    print("  2. Convert to GGUF with llama.cpp")
    print("  3. Import to Ollama: ollama create qwen2.5-aj:32b -f Modelfile")


if __name__ == "__main__":
    main()
