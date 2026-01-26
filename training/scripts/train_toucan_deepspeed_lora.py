#!/usr/bin/env python3
"""
DeepSpeed ZeRO-3 LoRA Training for DeepSeek-R1-Distill-Qwen-32B
Using Toucan-1.5M Dataset

ZeRO-3 + LoRA:
- Model and optimizer states partitioned across 4 GPUs
- LoRA adapters for parameter efficiency
- Gradient checkpointing for activation memory
- Better compatibility than FSDP + LoRA

4x H100 (320GB VRAM) is sufficient for this configuration
"""

import os
import json
import yaml
import argparse
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
)
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer, SFTConfig


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    return parser.parse_args()


def convert_to_chatml(examples):
    """Convert messages to ChatML format"""
    texts = []
    messages_list = examples['messages']
    
    for item in messages_list:
        # If it's a string, use it directly
        if isinstance(item, str):
            texts.append(item)
            continue
            
        # If it's a list of messages, convert to ChatML
        if isinstance(item, list):
            text_parts = []
            for msg in item:
                if isinstance(msg, dict):
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    if role == 'user':
                        text_parts.append(f"<|im_start|>user\n{content}<|im_end|>")
                    elif role == 'assistant':
                        text_parts.append(f"<|im_start|>assistant\n{content}<|im_end|>")
                    elif role == 'system':
                        text_parts.append(f"<|im_start|>system\n{content}<|im_end|>")
            texts.append("\n".join(text_parts))
        else:
            texts.append(str(item))
    
    return {"text": texts}


def main():
    args = parse_args()
    
    # Load config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    # Get local rank for distributed training
    local_rank = int(os.environ.get("LOCAL_RANK", 0))
    world_size = int(os.environ.get("WORLD_SIZE", 1))
    
    if local_rank == 0:
        print(f"\n{'='*60}")
        print(f"DeepSpeed ZeRO-3 LoRA Training")
        print(f"DeepSeek-R1-Distill-Qwen-32B + Toucan-1.5M")
        print(f"{'='*60}")
        print(f"World size: {world_size} GPUs")
        print(f"ZeRO-3 + LoRA")
        print(f"{'='*60}\n")
    
    model_name = config.get('model_name', 'deepseek-ai/DeepSeek-R1-Distill-Qwen-32B')
    output_dir = config.get('output_dir', './toucan-deepspeed-lora-output')
    
    # Load tokenizer
    if local_rank == 0:
        print(f"Loading tokenizer from {model_name}...")
    
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        padding_side="right"
    )
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load model in full precision (bf16)
    if local_rank == 0:
        print(f"\nLoading model in full precision (bf16)...")
        print(f"This is a 32B model - DeepSpeed ZeRO-3 will partition across {world_size} GPUs")
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        device_map="auto",  # DeepSpeed will manage
        low_cpu_mem_usage=True,
        use_cache=False,  # Required for gradient checkpointing
    )
    
    if local_rank == 0:
        total_params = sum(p.numel() for p in model.parameters())
        print(f"Model loaded! Total parameters: {total_params:,}")
    
    # Configure LoRA
    lora_config = LoraConfig(
        r=int(config.get('lora_r', 64)),
        lora_alpha=int(config.get('lora_alpha', 128)),
        target_modules=config.get('target_modules', [
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"
        ]),
        lora_dropout=float(config.get('lora_dropout', 0.05)),
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    
    # Apply LoRA
    if local_rank == 0:
        print(f"\nApplying LoRA with r={lora_config.r}, alpha={lora_config.lora_alpha}")
    
    model = get_peft_model(model, lora_config)
    
    if local_rank == 0:
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        all_params = sum(p.numel() for p in model.parameters())
        print(f"Trainable parameters: {trainable_params:,} ({100*trainable_params/all_params:.2f}%)")
    
    # Enable gradient checkpointing
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    
    # Load Toucan dataset
    if local_rank == 0:
        print(f"\nLoading Toucan-1.5M SFT dataset...")
    
    dataset = load_dataset(
        "Agent-Ark/Toucan-1.5M",
        name="SFT",
        split="train",
        trust_remote_code=True
    )
    
    # Split into train/eval
    split_dataset = dataset.train_test_split(test_size=0.01, seed=42)
    train_dataset = split_dataset['train']
    eval_dataset = split_dataset['test']
    
    if local_rank == 0:
        print(f"Total examples: {len(dataset):,}")
        print(f"Train: {len(train_dataset):,}, Eval: {len(eval_dataset):,}")
    
    # Convert to ChatML format
    if local_rank == 0:
        print(f"\nConverting to ChatML format...")
    
    train_dataset = train_dataset.map(
        convert_to_chatml,
        batched=True,
        remove_columns=train_dataset.column_names,
        desc="Converting train to ChatML"
    )
    
    eval_dataset = eval_dataset.map(
        convert_to_chatml,
        batched=True,
        remove_columns=eval_dataset.column_names,
        desc="Converting eval to ChatML"
    )
    
    # Filter out empty examples
    train_dataset = train_dataset.filter(lambda x: len(x['text']) > 0)
    eval_dataset = eval_dataset.filter(lambda x: len(x['text']) > 0)
    
    if local_rank == 0:
        print(f"After filtering - Train: {len(train_dataset):,}, Eval: {len(eval_dataset):,}")
    
    # Create DeepSpeed config
    deepspeed_config = {
        "train_batch_size": int(config.get('batch_size', 1)) * world_size,
        "train_micro_batch_size_per_gpu": int(config.get('batch_size', 1)),
        "gradient_accumulation_steps": int(config.get('gradient_accumulation_steps', 8)),
        
        "optimizer": {
            "type": "AdamW",
            "params": {
                "lr": float(config.get('learning_rate', 2e-5)),
                "betas": [0.9, 0.95],
                "eps": 1e-8,
                "weight_decay": float(config.get('weight_decay', 0.01))
            }
        },
        
        "scheduler": {
            "type": "WarmupDecayLR",
            "params": {
                "warmup_min_lr": 0,
                "warmup_max_lr": float(config.get('learning_rate', 2e-5)),
                "warmup_num_steps": int(config.get('warmup_steps', 500)),
                "total_num_steps": int(config.get('max_steps', 5000))
            }
        },
        
        "zero_optimization": {
            "stage": 3,
            "offload_optimizer": {
                "device": "cpu",
                "pin_memory": True
            },
            "offload_param": {
                "device": "cpu",
                "pin_memory": True
            },
            "overlap_comm": True,
            "contiguous_gradients": True,
            "reduce_bucket_size": 2e8,
            "stage3_prefetch_bucket_size": 2e8,
            "stage3_param_persistence_threshold": 1e7,
            "gather_16bit_weights_on_model_save": True,
        },
        
        "gradient_clipping": float(config.get('max_grad_norm', 1.0)),
        "bf16": {"enabled": True},
        "gradient_checkpointing": True,
        "activation_checkpointing": {
            "number_checkpoints": 4,
            "cpu_checkpointing": False,
            "contiguous_memory_optimization": False,
            "synchronize_checkpoint_boundary": False,
            "profile": False
        },
        
        "wall_clock_breakdown": False,
        "steps_per_print": int(config.get('logging_steps', 10)),
    }
    
    # Save DeepSpeed config
    if local_rank == 0:
        with open("./deepspeed_config.json", "w") as f:
            json.dump(deepspeed_config, f, indent=2)
        print(f"\nDeepSpeed config saved")
    
    # Training configuration
    training_config = SFTConfig(
        output_dir=output_dir,
        
        # Batch sizes
        per_device_train_batch_size=int(config.get('batch_size', 1)),
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=int(config.get('gradient_accumulation_steps', 8)),
        
        # Training duration
        num_train_epochs=int(config.get('num_epochs', 1)),
        max_steps=int(config.get('max_steps', 5000)),
        
        # Learning rate - will be overridden by DeepSpeed scheduler
        learning_rate=float(config.get('learning_rate', 2e-5)),
        
        # Precision
        bf16=True,
        tf32=True,
        
        # Memory optimization
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        
        # Logging
        logging_steps=int(config.get('logging_steps', 10)),
        logging_first_step=True,
        report_to="none",
        
        # Checkpointing
        save_strategy="steps",
        save_steps=int(config.get('save_steps', 500)),
        save_total_limit=3,
        
        # Evaluation
        eval_strategy="steps",
        eval_steps=int(config.get('eval_steps', 500)),
        
        # Distributed
        ddp_find_unused_parameters=False,
        dataloader_pin_memory=True,
        dataloader_num_workers=4,
        
        # DeepSpeed
        deepspeed="./deepspeed_config.json",
        remove_unused_columns=False,
        
        # SFT specific
        max_seq_length=int(config.get('max_seq_length', 1024)),
        packing=False,
        dataset_text_field="text",
    )
    
    # Create trainer
    trainer = SFTTrainer(
        model=model,
        args=training_config,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
    )
    
    if local_rank == 0:
        print(f"\n{'='*60}")
        print(f"Starting DeepSpeed ZeRO-3 LoRA Training!")
        print(f"{'='*60}")
        eff_batch = training_config.per_device_train_batch_size * world_size * training_config.gradient_accumulation_steps
        print(f"Effective batch size: {eff_batch}")
        print(f"Max sequence length: {training_config.max_seq_length}")
        print(f"Learning rate: {training_config.learning_rate}")
        print(f"Output: {output_dir}")
        print(f"{'='*60}\n")
    
    # Train
    trainer.train()
    
    # Save final model
    if local_rank == 0:
        print(f"\nTraining complete! Saving model...")
    
    trainer.save_model()
    
    if local_rank == 0:
        print(f"Model saved to {output_dir}")
        print(f"Done!")


if __name__ == "__main__":
    main()
