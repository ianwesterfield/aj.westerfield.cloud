#!/usr/bin/env python3
"""
QLoRA Fine-tuning script for Qwen 2.5 32B.

Uses Unsloth for efficient 4-bit training on consumer GPUs.
Requires ~24GB VRAM with gradient checkpointing.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any

# Check for GPU
import torch
if not torch.cuda.is_available():
    print("WARNING: No CUDA GPU detected. Training will be extremely slow or fail.")
    print("For CPU-only machines, consider using cloud GPU services.")

# Unsloth for efficient fine-tuning
try:
    from unsloth import FastLanguageModel
    from unsloth.chat_templates import get_chat_template
    UNSLOTH_AVAILABLE = True
except ImportError:
    UNSLOTH_AVAILABLE = False
    print("Unsloth not installed. Install with: pip install unsloth")

from transformers import TrainingArguments
from trl import SFTTrainer
from datasets import Dataset, concatenate_datasets

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CONFIG_PATH = PROJECT_DIR / "configs" / "qlora_config.yaml"
DATA_DIR = PROJECT_DIR / "data"


def load_config() -> Dict[str, Any]:
    """Load training configuration."""
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)


def load_training_data() -> Dataset:
    """Load and combine all JSONL training files."""
    all_examples = []
    
    jsonl_files = list(DATA_DIR.glob("*.jsonl"))
    
    if not jsonl_files:
        raise FileNotFoundError(
            f"No training data found in {DATA_DIR}. "
            "Run extract_training_data.py first."
        )
    
    for filepath in jsonl_files:
        print(f"  Loading {filepath.name}...")
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    example = json.loads(line)
                    all_examples.append(example)
    
    print(f"  Total examples: {len(all_examples)}")
    return Dataset.from_list(all_examples)


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
    print("=" * 60)
    print("Qwen 2.5 AJ 32B - QLoRA Fine-tuning")
    print("=" * 60)
    
    if not UNSLOTH_AVAILABLE:
        print("\nERROR: Unsloth is required for efficient training.")
        print("Install with: pip install 'unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git'")
        return
    
    # Load config
    print("\n1. Loading configuration...")
    config = load_config()
    
    # Check VRAM
    if torch.cuda.is_available():
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
        print(f"   VRAM: {vram_gb:.1f} GB")
        
        if vram_gb < 20:
            print("   WARNING: Low VRAM. Consider reducing batch size or using a smaller model.")
    
    # Load model with 4-bit quantization
    print("\n2. Loading Qwen 2.5 32B with 4-bit quantization...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=config["model"]["base_model"],
        max_seq_length=config["model"]["max_seq_length"],
        dtype=None,  # Auto-detect
        load_in_4bit=True,
    )
    
    # Add LoRA adapters
    print("\n3. Adding LoRA adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=config["lora"]["r"],
        lora_alpha=config["lora"]["lora_alpha"],
        lora_dropout=config["lora"]["lora_dropout"],
        target_modules=config["lora"]["target_modules"],
        bias=config["lora"]["bias"],
        use_gradient_checkpointing="unsloth",  # Efficient checkpointing
        random_state=42,
    )
    
    # Load training data
    print("\n4. Loading training data...")
    dataset = load_training_data()
    
    # Format dataset
    print("\n5. Formatting dataset for Qwen...")
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
    
    # Training arguments
    print("\n6. Configuring training...")
    training_args = TrainingArguments(
        output_dir=str(PROJECT_DIR / config["training"]["output_dir"]),
        num_train_epochs=config["training"]["num_train_epochs"],
        per_device_train_batch_size=config["training"]["per_device_train_batch_size"],
        gradient_accumulation_steps=config["training"]["gradient_accumulation_steps"],
        learning_rate=config["training"]["learning_rate"],
        weight_decay=config["training"]["weight_decay"],
        warmup_ratio=config["training"]["warmup_ratio"],
        lr_scheduler_type=config["training"]["lr_scheduler_type"],
        logging_steps=config["training"]["logging_steps"],
        save_steps=config["training"]["save_steps"],
        eval_steps=config["training"]["eval_steps"],
        save_total_limit=config["training"]["save_total_limit"],
        fp16=config["training"]["fp16"],
        bf16=config["training"]["bf16"],
        gradient_checkpointing=config["training"]["gradient_checkpointing"],
        optim=config["training"]["optim"],
        max_grad_norm=config["training"]["max_grad_norm"],
        group_by_length=config["training"]["group_by_length"],
        report_to=config["training"]["report_to"],
        evaluation_strategy="steps",
        load_best_model_at_end=True,
    )
    
    # Trainer
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
    print("\n7. Starting training...")
    print("=" * 60)
    trainer.train()
    
    # Save final model
    print("\n8. Saving final model...")
    output_dir = PROJECT_DIR / config["export"]["output_dir"] / "lora_adapter"
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"LoRA adapter saved to: {output_dir}")
    print("\nNext steps:")
    print("  1. Run export_ollama.py to create Ollama model")
    print("  2. Test with: ollama run qwen2.5-aj:32b-q4")


if __name__ == "__main__":
    main()
