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

# Enable TF32 for better performance on Ampere/Ada GPUs (RTX 30xx/40xx)
torch.set_float32_matmul_precision('high')

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
    """Load training data from merged file or all JSONL files.
    
    Uses memory-efficient streaming to avoid OOM on large datasets.
    Handles heterogeneous schemas by only keeping required columns.
    """
    from datasets import load_dataset
    
    # Required columns for training - all others are optional metadata
    REQUIRED_COLUMNS = {"instruction", "response"}
    OPTIONAL_COLUMNS = {"system", "category", "source"}  # Keep these if present
    
    def normalize_example(example):
        """Extract only the columns we need, handling schema variations."""
        return {
            "system": example.get("system", "You are a helpful assistant."),
            "instruction": example.get("instruction", ""),
            "response": example.get("response", ""),
        }
    
    # Prefer merged file if it exists
    if merged_file and merged_file.exists():
        print(f"  Loading merged dataset: {merged_file.name}")
        print(f"  (Using memory-efficient chunked loader for heterogeneous schemas)")
        
        # For files with inconsistent schemas, we need to load line-by-line
        # but in a memory-efficient way using generators
        def generate_examples():
            with open(merged_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            example = json.loads(line)
                            # Only keep if it has the required fields
                            if example.get("instruction") and example.get("response"):
                                yield normalize_example(example)
                        except json.JSONDecodeError:
                            continue
        
        # Load in chunks to avoid memory issues
        print(f"  Counting examples...")
        chunk_size = 100_000
        all_chunks = []
        current_chunk = []
        total_count = 0
        
        for example in generate_examples():
            current_chunk.append(example)
            total_count += 1
            
            if len(current_chunk) >= chunk_size:
                all_chunks.append(Dataset.from_list(current_chunk))
                print(f"    Loaded {total_count:,} examples...", end='\r')
                current_chunk = []
        
        # Don't forget the last chunk
        if current_chunk:
            all_chunks.append(Dataset.from_list(current_chunk))
        
        print(f"  Loaded {total_count:,} examples total    ")
        
        # Concatenate all chunks
        if len(all_chunks) == 1:
            return all_chunks[0]
        else:
            from datasets import concatenate_datasets
            return concatenate_datasets(all_chunks)
    
    # Fall back to loading all JSONL files
    jsonl_files = sorted(DATA_DIR.glob("*.jsonl"))
    
    # Exclude combined/merged files to avoid duplicates
    exclude_patterns = ["all_training_data.jsonl", "all_training_data_merged.jsonl", "merged_training.jsonl"]
    jsonl_files = [f for f in jsonl_files if f.name not in exclude_patterns]
    
    if not jsonl_files:
        raise FileNotFoundError(
            f"No training data found in {DATA_DIR}. "
            "Run the pipeline to generate data first."
        )
    
    print(f"  Loading {len(jsonl_files)} JSONL files...")
    
    # Load each file and normalize schemas
    all_examples = []
    for filepath in jsonl_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        example = json.loads(line)
                        if example.get("instruction") and example.get("response"):
                            all_examples.append(normalize_example(example))
                    except json.JSONDecodeError:
                        continue
    
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
    parser = argparse.ArgumentParser(description="QLoRA fine-tuning for Granite")
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
    print("AJ Granite - QLoRA Fine-tuning")
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
    print(f"\n2. Loading {config['model']['base_model']} with 4-bit quantization...")
    if use_unsloth:
        model, tokenizer = load_model_unsloth(config)
    else:
        model, tokenizer = load_model_standard(config)
    
    # Load training data
    print("\n3. Loading training data...")
    # Try multiple possible merged file names in order of preference
    if args.data:
        merged_file = Path(args.data)
    else:
        possible_files = [
            DATA_DIR / "all_training_data_merged.jsonl",  # Pipeline output
            DATA_DIR / "merged_training.jsonl",           # Legacy name
            DATA_DIR / "all_training_data.jsonl",         # Alternative
        ]
        merged_file = next((f for f in possible_files if f.exists()), None)
    
    dataset = load_training_data(merged_file)
    
    # Split train/eval FIRST (before formatting) to reduce memory pressure
    print("\n4. Splitting train/eval sets...")
    eval_split = config.get("data", {}).get("eval_split", 0.05)
    seed = config.get("data", {}).get("seed", 42)
    split = dataset.train_test_split(test_size=eval_split, seed=seed)
    
    # Clear the full dataset from memory
    del dataset
    import gc
    gc.collect()
    
    print(f"   Train examples: {len(split['train']):,}")
    print(f"   Eval examples: {len(split['test']):,}")
    
    # Format datasets with memory-efficient settings
    print("\n5. Formatting datasets for Granite chat format...")
    print("   (Using batched processing to reduce memory)")
    
    map_kwargs = {
        "remove_columns": split["train"].column_names,
        "desc": "Formatting train",
        "batched": True,
        "batch_size": 1000,
        "num_proc": 1,  # Single process to avoid memory duplication
        "writer_batch_size": 1000,  # Flush to disk frequently
        "load_from_cache_file": True,  # Use cache if available
    }
    
    def format_batch(examples, tokenizer):
        """Format a batch of examples for Granite chat format."""
        texts = []
        for i in range(len(examples["instruction"])):
            messages = [
                {"role": "system", "content": examples.get("system", ["You are a helpful assistant."] * len(examples["instruction"]))[i] or "You are a helpful assistant."},
                {"role": "user", "content": examples["instruction"][i]},
                {"role": "assistant", "content": examples["response"][i]},
            ]
            text = tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=False
            )
            texts.append(text)
        return {"text": texts}
    
    train_dataset = split["train"].map(
        lambda x: format_batch(x, tokenizer),
        **map_kwargs
    )
    
    map_kwargs["desc"] = "Formatting eval"
    map_kwargs["remove_columns"] = split["test"].column_names
    eval_dataset = split["test"].map(
        lambda x: format_batch(x, tokenizer),
        **map_kwargs
    )
    
    # Clear split from memory
    del split
    gc.collect()
    
    # Training arguments
    print("\n5. Configuring training...")
    output_dir = str(PROJECT_DIR / config["training"]["output_dir"])
    
    # Reduce dataloader workers for very large datasets to save memory
    # Each worker loads data into separate memory space
    num_workers = config["training"].get("dataloader_num_workers", 4)
    if len(train_dataset) > 500_000:
        num_workers = min(num_workers, 2)
        print(f"   Large dataset detected - using {num_workers} dataloader workers to save memory")
    
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
        dataloader_num_workers=num_workers,
        dataloader_pin_memory=config["training"].get("dataloader_pin_memory", True),
        dataloader_prefetch_factor=2 if num_workers > 0 else None,  # Limit memory buffering
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
    print("  3. Import to Ollama: ollama create granite-aj:8b -f Modelfile")


if __name__ == "__main__":
    main()
