#!/usr/bin/env python3
"""
Download and prepare IBM Granite instruction dataset for training.

IBM Granite 3.1 Language Instruction dataset:
- High quality instruction-following examples
- Diverse tasks: reasoning, coding, Q&A, etc.
- ~100K+ examples

This script downloads, filters, and converts to our training format.
"""

import os
import json
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_FILE = DATA_DIR / "ibm_granite.jsonl"
STATS_FILE = DATA_DIR / "ibm_granite_stats.json"

# IBM Granite dataset on HuggingFace
DATASET_NAME = "ibm-granite/granite-3.1-language-instruction"

# Default system prompt for instruction-following
DEFAULT_SYSTEM = """You are AJ, an expert AI assistant with deep knowledge across programming, system administration, and technical domains. Provide clear, accurate, and actionable responses."""

# Categories to prioritize for our use case
PRIORITY_CATEGORIES = {
    "coding": 1.5,        # Boost coding examples
    "reasoning": 1.3,     # Boost reasoning
    "math": 1.0,
    "instruction_following": 1.0,
    "general": 0.8,       # Slightly reduce generic
}


@dataclass
class DatasetStats:
    """Track dataset statistics."""
    total_downloaded: int = 0
    total_filtered: int = 0
    total_converted: int = 0
    by_category: Dict[str, int] = None
    avg_instruction_length: float = 0
    avg_response_length: float = 0
    
    def __post_init__(self):
        if self.by_category is None:
            self.by_category = {}


def download_dataset(max_examples: Optional[int] = None, streaming: bool = True):
    """
    Download IBM Granite dataset from HuggingFace.
    
    Args:
        max_examples: Limit number of examples (None = all)
        streaming: Use streaming mode to avoid downloading entire dataset
    
    Returns:
        Iterator of examples
    """
    try:
        from datasets import load_dataset
    except ImportError:
        print("ERROR: datasets library not installed.")
        print("Install with: pip install datasets")
        return None
    
    print(f"Downloading {DATASET_NAME}...")
    print(f"  Mode: {'streaming' if streaming else 'full download'}")
    if max_examples:
        print(f"  Limit: {max_examples} examples")
    
    try:
        if streaming:
            dataset = load_dataset(DATASET_NAME, split="train", streaming=True)
        else:
            dataset = load_dataset(DATASET_NAME, split="train")
        
        return dataset
    except Exception as e:
        print(f"ERROR: Failed to download dataset: {e}")
        print("\nTroubleshooting:")
        print("1. Check internet connection")
        print("2. Try: huggingface-cli login")
        print("3. Verify dataset exists: https://huggingface.co/datasets/ibm-granite/granite-3.1-language-instruction")
        return None


def convert_example(example: Dict) -> Optional[Dict]:
    """
    Convert IBM Granite format to our training format.
    
    IBM format: {"input": "...", "output": "...", "task_type": "..."}
    Our format: {"system": "...", "instruction": "...", "response": "...", "domain": "..."}
    """
    # Extract fields (IBM uses various field names)
    instruction = example.get("input") or example.get("instruction") or example.get("prompt", "")
    response = example.get("output") or example.get("response") or example.get("completion", "")
    task_type = example.get("task_type") or example.get("category") or "general"
    
    # Skip empty or invalid examples
    if not instruction or not response:
        return None
    
    # Skip very short responses (likely low quality)
    if len(response.strip()) < 20:
        return None
    
    # Skip examples that are too long (will be truncated anyway)
    if len(instruction) > 8000 or len(response) > 8000:
        return None
    
    # Map IBM task types to our domains
    domain_map = {
        "coding": "programming_concepts",
        "code": "programming_concepts",
        "python": "python_development",
        "javascript": "nodejs",
        "reasoning": "architecture_qa",
        "math": "programming_concepts",
        "qa": "general_qa",
        "instruction_following": "task_planning",
        "chat": "multiturn_conversations",
        "summarization": "general_qa",
    }
    
    domain = domain_map.get(task_type.lower(), "general_qa")
    
    return {
        "system": DEFAULT_SYSTEM,
        "instruction": instruction.strip(),
        "response": response.strip(),
        "domain": domain,
        "source": "ibm_granite",
    }


def filter_and_sample(
    examples: List[Dict],
    target_count: int = 20000,
    category_weights: Optional[Dict[str, float]] = None
) -> List[Dict]:
    """
    Filter and sample examples with category weighting.
    
    Args:
        examples: All converted examples
        target_count: Target number of examples
        category_weights: Weight multipliers by category
    
    Returns:
        Filtered and sampled list
    """
    if category_weights is None:
        category_weights = PRIORITY_CATEGORIES
    
    # Group by domain
    by_domain = {}
    for ex in examples:
        domain = ex.get("domain", "general_qa")
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(ex)
    
    print(f"\nDistribution by domain:")
    for domain, items in sorted(by_domain.items(), key=lambda x: -len(x[1])):
        print(f"  {domain}: {len(items)}")
    
    # Calculate samples per domain with weights
    total_weight = sum(len(items) * category_weights.get(domain, 1.0) 
                       for domain, items in by_domain.items())
    
    sampled = []
    for domain, items in by_domain.items():
        weight = category_weights.get(domain, 1.0)
        weighted_count = len(items) * weight
        sample_count = int((weighted_count / total_weight) * target_count)
        sample_count = min(sample_count, len(items))
        
        if sample_count > 0:
            sampled.extend(random.sample(items, sample_count))
    
    # Shuffle final list
    random.shuffle(sampled)
    
    return sampled


def save_dataset(examples: List[Dict], output_path: Path):
    """Save examples to JSONL format."""
    print(f"\nSaving {len(examples)} examples to {output_path}...")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + '\n')
    
    print(f"  Done! File size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")


def save_stats(stats: DatasetStats, output_path: Path):
    """Save dataset statistics."""
    with open(output_path, 'w') as f:
        json.dump({
            "total_downloaded": stats.total_downloaded,
            "total_filtered": stats.total_filtered,
            "total_converted": stats.total_converted,
            "by_category": stats.by_category,
            "avg_instruction_length": stats.avg_instruction_length,
            "avg_response_length": stats.avg_response_length,
        }, f, indent=2)


def main(
    max_download: int = 100000,
    target_examples: int = 20000,
    streaming: bool = True,
):
    """
    Main pipeline to download and prepare IBM Granite dataset.
    
    Args:
        max_download: Max examples to download from HuggingFace
        target_examples: Final target count after filtering
        streaming: Use streaming mode
    """
    print("=" * 60)
    print("IBM Granite Dataset Preparation")
    print("=" * 60)
    
    stats = DatasetStats()
    
    # 1. Download
    print("\n1. Downloading dataset...")
    dataset = download_dataset(max_examples=max_download, streaming=streaming)
    
    if dataset is None:
        return
    
    # 2. Convert examples
    print("\n2. Converting to training format...")
    converted = []
    total_inst_len = 0
    total_resp_len = 0
    
    count = 0
    for example in dataset:
        converted_ex = convert_example(example)
        if converted_ex:
            converted.append(converted_ex)
            total_inst_len += len(converted_ex["instruction"])
            total_resp_len += len(converted_ex["response"])
            
            # Track by domain
            domain = converted_ex.get("domain", "unknown")
            stats.by_category[domain] = stats.by_category.get(domain, 0) + 1
        
        count += 1
        if count % 10000 == 0:
            print(f"  Processed {count}... ({len(converted)} valid)")
        
        if max_download and count >= max_download:
            break
    
    stats.total_downloaded = count
    stats.total_converted = len(converted)
    
    if converted:
        stats.avg_instruction_length = total_inst_len / len(converted)
        stats.avg_response_length = total_resp_len / len(converted)
    
    print(f"\n  Downloaded: {stats.total_downloaded}")
    print(f"  Valid conversions: {stats.total_converted}")
    print(f"  Avg instruction length: {stats.avg_instruction_length:.0f} chars")
    print(f"  Avg response length: {stats.avg_response_length:.0f} chars")
    
    # 3. Filter and sample
    print("\n3. Filtering and sampling...")
    final = filter_and_sample(converted, target_count=target_examples)
    stats.total_filtered = len(final)
    
    print(f"  Final count: {len(final)}")
    
    # 4. Save
    print("\n4. Saving dataset...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    save_dataset(final, OUTPUT_FILE)
    save_stats(stats, STATS_FILE)
    
    print("\n" + "=" * 60)
    print("Done! Next steps:")
    print("=" * 60)
    print(f"1. Dataset saved to: {OUTPUT_FILE}")
    print(f"2. Stats saved to: {STATS_FILE}")
    print(f"3. Run training with: python scripts/train_qlora.py")
    print(f"\nTotal examples ready for training: {stats.total_filtered}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Prepare IBM Granite dataset for training")
    parser.add_argument("--max-download", type=int, default=100000,
                        help="Maximum examples to download (default: 100000)")
    parser.add_argument("--target", type=int, default=20000,
                        help="Target examples after filtering (default: 20000)")
    parser.add_argument("--no-streaming", action="store_true",
                        help="Download full dataset instead of streaming")
    
    args = parser.parse_args()
    
    main(
        max_download=args.max_download,
        target_examples=args.target,
        streaming=not args.no_streaming,
    )
