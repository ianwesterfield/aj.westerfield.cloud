#!/usr/bin/env python3
"""
This script orchestrates the full training workflow:
1. Download/prepare agentic datasets (xLAM, AgentInstruct)
2. Merge with existing training data
3. Run QLoRA fine-tuning
4. Export to Ollama format

Optimized for RTX 4090 (24GB VRAM).
"""

import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
CONFIG_DIR = PROJECT_DIR / "configs"
CHECKPOINT_DIR = PROJECT_DIR / "checkpoints"
OUTPUT_DIR = PROJECT_DIR / "output"


def check_requirements():
    """Check that required packages are installed."""
    print("\n" + "=" * 60)
    print("Checking requirements...")
    print("=" * 60)
    
    # Suppress torchao warnings that can interfere with imports
    import warnings
    import os
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    warnings.filterwarnings("ignore", message=".*torchao.*")
    warnings.filterwarnings("ignore", message=".*torch.int1.*")
    
    requirements = {
        "torch": "PyTorch (CUDA)",
        "transformers": "HuggingFace Transformers",
        "datasets": "HuggingFace Datasets",
        "peft": "Parameter-Efficient Fine-Tuning",
        "trl": "Transformer Reinforcement Learning",
        "bitsandbytes": "8-bit optimizers",
        "accelerate": "HuggingFace Accelerate",
    }
    
    missing = []
    for pkg, desc in requirements.items():
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                __import__(pkg)
            print(f"  ✓ {desc}")
        except ImportError as e:
            print(f"  ✗ {desc} - NOT INSTALLED")
            missing.append(pkg)
        except Exception as e:
            # Package exists but has import issues (likely torchao warnings)
            # Check if it's actually installed via pip
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", pkg],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"  ✓ {desc} (with warnings)")
            else:
                print(f"  ✗ {desc} - IMPORT ERROR: {str(e)[:40]}...")
                missing.append(pkg)
    
    # Check for unsloth (optional - has Windows compatibility issues)
    
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from unsloth import FastLanguageModel
            
        print(f"  ✓ Unsloth (2x faster training)")
    except Exception as e:
        print(f"  ⚠ Unsloth not available (optional): {str(e)[:50]}...")
        print(f"    Will use standard PEFT training instead")
    
    # Check CUDA
    import torch
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"\n  GPU: {gpu_name}")
        print(f"  VRAM: {vram_gb:.1f} GB")
        
        if vram_gb < 20:
            print("  ⚠ WARNING: Low VRAM. Training may be slow or fail.")
    else:
        print("\n  ✗ No CUDA GPU detected!")
        missing.append("CUDA")
    
    if missing:
        print(f"\n❌ Missing requirements: {', '.join(missing)}")
        print("\nInstall with:")
        print("  pip install torch transformers datasets peft trl bitsandbytes accelerate")
        return False
    
    print("\n✓ All requirements satisfied!")
    return True


def prepare_agentic_datasets(xlam_target: int = 60000, agent_target: int = 1800000, 
                             toucan_target: int = 50000, skip_prompts: bool = False):
    """Download and prepare agentic training datasets (xLAM, AgentInstruct, Toucan)."""
    print("\n" + "=" * 60)
    print("Step 1: Preparing Agentic Training Datasets")
    print("=" * 60)
    
    xlam_file = DATA_DIR / "xlam_function_calling.jsonl"
    agent_file = DATA_DIR / "agent_instruct.jsonl"
    toucan_file = DATA_DIR / "toucan_trajectories.jsonl"
    
    # Check if all exist
    existing = []
    if xlam_file.exists():
        with open(xlam_file, 'r', encoding='utf-8', errors='ignore') as f:
            count = sum(1 for _ in f)
        existing.append(f"xLAM: {count}")
    if agent_file.exists():
        with open(agent_file, 'r', encoding='utf-8', errors='ignore') as f:
            count = sum(1 for _ in f)
        existing.append(f"AgentInstruct: {count}")
    if toucan_file.exists():
        with open(toucan_file, 'r', encoding='utf-8', errors='ignore') as f:
            count = sum(1 for _ in f)
        existing.append(f"Toucan: {count}")
    
    if existing and not skip_prompts:
        print(f"\n  Existing datasets: {', '.join(existing)}")
        response = input("  Re-download? [y/N]: ").strip().lower()
        if response != 'y':
            print("  Skipping download.")
            return True
    elif existing:
        print(f"\n  Using existing datasets: {', '.join(existing)}")
        return True
    
    # Run preparation script
    print(f"\n  Downloading agentic datasets...")
    print(f"  xLAM target: {xlam_target} examples")
    print(f"  AgentInstruct target: {agent_target} examples")
    print(f"  Toucan target: {toucan_target} examples (MCP tool-use)")
    
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "prepare_agentic_datasets.py"),
        "--xlam-target", str(xlam_target),
        "--agent-target", str(agent_target),
        "--toucan-target", str(toucan_target),
    ]
    
    if skip_prompts:
        cmd.append("-y")
    
    result = subprocess.run(cmd, cwd=str(PROJECT_DIR))
    
    if result.returncode != 0:
        print("  ⚠ Some agentic datasets may have failed")
        # Continue anyway - we have local data
        return True
    
    print("  ✓ Agentic datasets ready!")
    return True


def merge_datasets(force: bool = False):
    """Merge all training datasets and deduplicate."""
    print("\n" + "=" * 60)
    print("Step 2: Merging Training Datasets")
    print("=" * 60)
    
    output_file = DATA_DIR / "all_training_data_merged.jsonl"
    
    # Check if merged file already exists and is recent
    if output_file.exists() and not force:
        file_size_mb = output_file.stat().st_size / 1024 / 1024
        # Quick count of lines without loading into memory
        with open(output_file, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        
        print(f"  Merged file already exists:")
        print(f"    File: {output_file.name}")
        print(f"    Size: {file_size_mb:.1f} MB")
        print(f"    Examples: {line_count:,}")
        print(f"  ✓ Skipping merge (use --force-merge to rebuild)")
        return line_count
    
    all_examples = []
    seen_hashes = set()
    files_loaded = 0
    
    # Files to exclude from merging (the output file itself and old combined files)
    exclude_files = {"all_training_data.jsonl", "all_training_data_merged.jsonl", "merged_training.jsonl"}
    
    # Load all JSONL files
    for filepath in sorted(DATA_DIR.glob("*.jsonl")):
        if filepath.name in exclude_files:
            continue  # Skip combined/merged files
        
        count_before = len(all_examples)
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    example = json.loads(line)
                    # Create hash for deduplication
                    hash_key = hash((
                        example.get("instruction", "")[:200],
                        example.get("response", "")[:200]
                    ))
                    if hash_key not in seen_hashes:
                        seen_hashes.add(hash_key)
                        all_examples.append(example)
                except json.JSONDecodeError:
                    continue
        
        added = len(all_examples) - count_before
        if added > 0:
            print(f"  + {filepath.name}: {added} examples")
            files_loaded += 1
    
    print(f"\n  Total files: {files_loaded}")
    print(f"  Total unique examples: {len(all_examples)}")
    
    # Save merged dataset
    output_file = DATA_DIR / "all_training_data_merged.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f:
        for ex in all_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')
    
    print(f"  Saved to: {output_file}")
    print(f"  File size: {output_file.stat().st_size / 1024 / 1024:.1f} MB")
    
    # Update stats
    stats = {
        "generated_at": datetime.now().isoformat(),
        "total_examples": len(all_examples),
        "by_domain": {},
    }
    for ex in all_examples:
        domain = ex.get("domain", "unknown")
        stats["by_domain"][domain] = stats["by_domain"].get(domain, 0) + 1
    
    with open(DATA_DIR / "merged_stats.json", 'w') as f:
        json.dump(stats, f, indent=2)
    
    print("  ✓ Datasets merged!")
    return len(all_examples)


def estimate_training_time(num_examples: int, epochs: int = 2):
    """Estimate training time based on dataset size."""
    # Rough estimates for RTX 4090 with 32B model, QLoRA, batch=1, grad_accum=8
    # ~1.5 seconds per training step (8 examples)
    steps_per_epoch = num_examples // 8
    total_steps = steps_per_epoch * epochs
    seconds = total_steps * 1.5
    
    hours = seconds / 3600
    
    print(f"\n  📊 Training Estimate:")
    print(f"     Examples: {num_examples:,}")
    print(f"     Epochs: {epochs}")
    print(f"     Steps: {total_steps:,}")
    print(f"     Estimated time: {hours:.1f} hours")
    
    return hours


def run_training(config_file: str = "qlora_config_4090.yaml", resume: bool = False):
    """Run QLoRA fine-tuning."""
    print("\n" + "=" * 60)
    print("Step 3: QLoRA Fine-Tuning")
    print("=" * 60)
    
    config_path = CONFIG_DIR / config_file
    if not config_path.exists():
        print(f"  ❌ Config not found: {config_path}")
        return False
    
    print(f"  Config: {config_path}")
    
    # Create checkpoint directory
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check for existing checkpoint
    if resume:
        checkpoints = list(CHECKPOINT_DIR.glob("checkpoint-*"))
        if checkpoints:
            latest = max(checkpoints, key=lambda p: int(p.name.split("-")[1]))
            print(f"  Resuming from: {latest}")
    
    # Run training
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "train_qlora.py"),
        "--config", str(config_path),
    ]
    
    if resume:
        cmd.append("--resume")
    
    print(f"\n  Starting training...")
    print(f"  Logs: tensorboard --logdir {CHECKPOINT_DIR}")
    print("\n" + "-" * 60)
    
    result = subprocess.run(cmd, cwd=str(PROJECT_DIR))
    
    if result.returncode != 0:
        print("  ❌ Training failed")
        return False
    
    print("  ✓ Training complete!")
    return True


def export_to_ollama():
    """Export trained model to Ollama format."""
    print("\n" + "=" * 60)
    print("Step 4: Exporting to Ollama")
    print("=" * 60)
    
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "merge_and_export.py"),
    ]
    
    result = subprocess.run(cmd, cwd=str(PROJECT_DIR))
    
    if result.returncode != 0:
        print("  ❌ Export failed")
        return False
    
    print("  ✓ Model exported!")
    print("\n  To load in Ollama:")
    print("    ollama create granite-aj:32b-4k -f output/Modelfile")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Master training pipeline for AJ Granite 3.1-8B"
    )
    parser.add_argument("--skip-agentic", action="store_true",
                        help="Skip agentic dataset download (xLAM, AgentInstruct, Toucan)")
    parser.add_argument("--skip-merge", action="store_true",
                        help="Skip dataset merging")
    parser.add_argument("--force-merge", action="store_true",
                        help="Force re-merge even if merged file exists")
    parser.add_argument("--skip-train", action="store_true",
                        help="Skip training (useful for just exporting)")
    parser.add_argument("--skip-export", action="store_true",
                        help="Skip Ollama export")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from latest checkpoint")
    parser.add_argument("--xlam-target", type=int, default=0,
                        help="Target xLAM examples (0 = all, default: all)")
    parser.add_argument("--agent-target", type=int, default=0,
                        help="Target AgentInstruct examples (0 = all, default: all)")
    parser.add_argument("--toucan-target", type=int, default=0,
                        help="Target Toucan-1.5M examples (0 = all, default: all)")
    parser.add_argument("--config", type=str, default="qlora_config.yaml",
                        help="Training config file")
    parser.add_argument("--check-only", action="store_true",
                        help="Only check requirements, don't train")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="Auto-confirm training start (non-interactive)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AJ Granite 3.1-8B - Master Training Pipeline")
    print("=" * 60)
    print(f"Base Model: IBM Granite 3.1-8B-Instruct (8B params, 128K context)")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    if args.check_only:
        print("\n✓ Requirements check complete.")
        sys.exit(0)
    
    # Step 1: Prepare agentic datasets
    if not args.skip_agentic:
        if not prepare_agentic_datasets(args.xlam_target, args.agent_target, 
                                        args.toucan_target, skip_prompts=args.yes):
            print("\n⚠ Continuing with local data only...")
    
    # Step 2: Merge datasets
    if not args.skip_merge:
        num_examples = merge_datasets(force=args.force_merge)
        estimate_training_time(num_examples)
    
    # Confirm before training
    if not args.skip_train:
        if not args.yes:
            print("\n" + "=" * 60)
            response = input("Start training? [Y/n]: ").strip().lower()
            if response == 'n':
                print("Training cancelled.")
                sys.exit(0)
        
        # Step 3: Train
        if not run_training(args.config, args.resume):
            sys.exit(1)
    
    # Step 4: Export
    if not args.skip_export:
        if not export_to_ollama():
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ Pipeline complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
