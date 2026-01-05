#!/usr/bin/env python3
"""
Standard QLoRA Fine-tuning script for Qwen 2.5 32B.

Uses PEFT + TRL without Unsloth for maximum compatibility.
Requires ~24GB VRAM with gradient checkpointing.
"""

import os
import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Check for GPU
import torch
if not torch.cuda.is_available():
    print("WARNING: No CUDA GPU detected. Training will be extremely slow or fail.")
else:
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig
from datasets import Dataset

# Paths (can be overridden by command line)
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DEFAULT_CONFIG_PATH = PROJECT_DIR / "configs" / "qlora_config.yaml"
DEFAULT_DATA_DIR = PROJECT_DIR / "data"

# Global config path (set by args)
CONFIG_PATH = None
DATA_PATH = None


def load_config() -> Dict[str, Any]:
    """Load training configuration."""
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)


def load_training_data() -> Dataset:
    """Load the combined training data."""
    data_file = Path(DATA_PATH)
    
    if not data_file.exists():
        raise FileNotFoundError(
            f"Training data not found at {data_file}. "
            "Run generate_all.py first."
        )
    
    examples = []
    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    
    print(f"  Loaded {len(examples)} training examples")
    return Dataset.from_list(examples)


def format_for_qwen(example: Dict, tokenizer) -> Dict:
    """Format example using Qwen's ChatML template."""
    messages = [
        {"role": "system", "content": example["system"]},
        {"role": "user", "content": example["instruction"]},
        {"role": "assistant", "content": example["response"]},
    ]
    
    # Use Qwen's chat template
    text = tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=False
    )
    
    return {"text": text}


def main():
    """Main training pipeline."""
    global CONFIG_PATH, DATA_PATH
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="QLoRA Fine-tuning")
    parser.add_argument("--config", type=str, default=str(DEFAULT_CONFIG_PATH), help="Path to config YAML")
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATA_DIR / "all_training_data.jsonl"), help="Path to training data")
    args = parser.parse_args()
    
    CONFIG_PATH = Path(args.config)
    DATA_PATH = Path(args.data)
    
    # Load config first to get model name
    print("\n1. Loading configuration...")
    config = load_config()
    model_name = config["model"]["base_model"]
    
    print("=" * 60)
    print(f"Fine-tuning: {model_name.split('/')[-1]}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"Config: {CONFIG_PATH}")
    print(f"Data: {DATA_PATH}")
    
    # 4-bit quantization config
    print("\n2. Setting up 4-bit quantization...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    
    # Load model
    print("\n3. Loading Qwen 2.5 32B (this may take a few minutes)...")
    model_name = config["model"]["base_model"]
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
        attn_implementation="sdpa",  # Use PyTorch's native scaled dot product attention (Windows compatible)
    )
    
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        padding_side="right",
    )
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Prepare model for k-bit training
    print("\n4. Preparing model for QLoRA...")
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
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # Load training data
    print("\n5. Loading training data...")
    dataset = load_training_data()
    
    # Format dataset
    print("\n6. Formatting dataset for Qwen...")
    dataset = dataset.map(
        lambda x: format_for_qwen(x, tokenizer),
        remove_columns=dataset.column_names
    )
    
    # Split train/eval
    split = dataset.train_test_split(
        test_size=config["data"]["eval_split"],
        seed=config["data"]["seed"]
    )
    train_dataset = split["train"]
    eval_dataset = split["test"]
    
    print(f"   Train examples: {len(train_dataset)}")
    print(f"   Eval examples: {len(eval_dataset)}")
    
    # Output directory
    output_dir = PROJECT_DIR / config["training"]["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Training arguments
    print("\n7. Configuring training...")
    training_args = SFTConfig(
        output_dir=str(output_dir),
        num_train_epochs=config["training"]["num_train_epochs"],
        per_device_train_batch_size=config["training"]["per_device_train_batch_size"],
        gradient_accumulation_steps=config["training"]["gradient_accumulation_steps"],
        learning_rate=config["training"]["learning_rate"],
        weight_decay=config["training"]["weight_decay"],
        warmup_ratio=config["training"]["warmup_ratio"],
        lr_scheduler_type=config["training"]["lr_scheduler_type"],
        logging_steps=config["training"]["logging_steps"],
        save_steps=config["training"]["save_steps"],
        eval_strategy="steps",
        eval_steps=config["training"]["eval_steps"],
        save_total_limit=config["training"]["save_total_limit"],
        fp16=False,
        bf16=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim=config["training"]["optim"],
        max_grad_norm=config["training"]["max_grad_norm"],
        group_by_length=config["training"]["group_by_length"],
        report_to="none",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        dataset_text_field="text",
    )
    
    # Trainer
    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,  # trl 0.26+ uses processing_class instead of tokenizer
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        args=training_args,
    )
    
    # Train!
    print("\n8. Starting training...")
    print("=" * 60)
    print(f"   Epochs: {config['training']['num_train_epochs']}")
    print(f"   Batch size: {config['training']['per_device_train_batch_size']}")
    print(f"   Gradient accumulation: {config['training']['gradient_accumulation_steps']}")
    print(f"   Effective batch: {config['training']['per_device_train_batch_size'] * config['training']['gradient_accumulation_steps']}")
    print(f"   Learning rate: {config['training']['learning_rate']}")
    print("=" * 60)
    
    trainer.train()
    
    # Save final model
    print("\n9. Saving final model...")
    final_output = PROJECT_DIR / config["export"]["output_dir"] / "lora_adapter"
    final_output.mkdir(parents=True, exist_ok=True)
    
    model.save_pretrained(final_output)
    tokenizer.save_pretrained(final_output)
    
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"LoRA adapter saved to: {final_output}")
    print("\nNext steps:")
    print("  1. Run export_ollama.py to create Ollama model")
    print("  2. Test with: ollama run qwen2.5-aj:32b-q4")


if __name__ == "__main__":
    main()
