#!/usr/bin/env python3
"""
Open Dataset Loader

Integrates publicly available trajectory datasets from HuggingFace.
Converts them to the internal trajectory format for hybrid training.

Supported datasets:
- Toucan-1.5M (Agent-Ark): 1.6M MCP tool-use trajectories from real MCP environments

Usage:
    python load_open_datasets.py --dataset toucan --output ../data/
    python load_open_datasets.py --dataset toucan --subset Kimi-K2 --sample 1000
"""

import json
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Generator, Any, cast
from dataclasses import dataclass

try:
    from datasets import load_dataset, Dataset
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False
    load_dataset = None  # type: ignore
    Dataset = None  # type: ignore


@dataclass
class OpenDatasetTrajectory:
    """Unified format for trajectories from open datasets."""
    task: str
    messages: List[Dict]  # Chat format messages
    target_tools: List[str]
    source_dataset: str
    source_subset: str
    subset_type: Optional[str] = None  # single-turn-original, multi-turn, etc.
    question_quality: Optional[Dict] = None
    response_quality: Optional[Dict] = None
    metadata: Optional[Dict] = None


class ToucanLoader:
    """
    Load Toucan-1.5M dataset from HuggingFace.
    
    Toucan-1.5M is the largest fully synthetic tool-agent dataset, comprising 
    over 1.5 million trajectories synthesized from 495 real-world Model Context 
    Protocols (MCPs) spanning 2,000+ tools.
    
    Dataset schema (from HuggingFace):
    - uuid: Unique data instance identifier
    - subset: Pipeline annotation (single-turn-original, irrelevant, single-turn-diversify, multi-turn)
    - messages: Trajectory with chat template from original LLM-agent (system prompt includes tools in Hermes format)
    - question: User task crafted to generate the trajectory
    - target_tools: MCP tools used as seeds (format: Server_Name::Tool_Name or just Tool_Name)
    - question_quality_assessment: LLM-as-judge evaluation (quality, difficulty, realism, uniqueness)
    - response_quality_assessment: LLM-as-judge evaluation (completeness, conciseness)
    - metadata: Original MCP server data and LLM annotations
    
    Available subsets:
    - Kimi-K2: 519K trajectories
    - Qwen3-32B: trajectories from Qwen3-32B model
    - GPT-OSS-120B: trajectories from GPT-OSS-120B model
    """
    
    DATASET_ID = "Agent-Ark/Toucan-1.5M"
    AVAILABLE_SUBSETS = ["Kimi-K2", "Qwen3-32B", "GPT-OSS-120B"]
    
    @staticmethod
    def load(subset: str = "Kimi-K2", split: str = "train", 
             sample_size: Optional[int] = None) -> Generator[OpenDatasetTrajectory, None, None]:
        """
        Load Toucan dataset with optional sampling.
        
        Args:
            subset: One of Kimi-K2, Qwen3-32B, GPT-OSS-120B
            split: Dataset split (Toucan-1.5M only has 'train')
            sample_size: If specified, randomly sample this many examples
        
        Yields:
            OpenDatasetTrajectory objects
        """
        if not HAS_DATASETS or load_dataset is None:
            raise ImportError("datasets package required: pip install datasets")
        
        if subset not in ToucanLoader.AVAILABLE_SUBSETS:
            raise ValueError(f"Unknown subset '{subset}'. Available: {ToucanLoader.AVAILABLE_SUBSETS}")
        
        print(f"Loading Toucan-1.5M ({subset})...")
        raw_dataset = load_dataset(ToucanLoader.DATASET_ID, subset, split=split)
        
        # Cast to Dataset for type safety - load_dataset with split returns Dataset
        dataset = cast(Any, raw_dataset)
        
        if sample_size:
            dataset = dataset.shuffle(seed=42).select(range(min(sample_size, len(dataset))))
            print(f"Sampled {len(dataset)} examples from {subset}")
        else:
            print(f"Loaded {len(dataset)} examples from {subset}")
        
        for example in dataset:
            # example is a dict-like object from the dataset
            ex: Dict[str, Any] = dict(example) if not isinstance(example, dict) else example
            
            # Extract fields with proper defaults
            trajectory = OpenDatasetTrajectory(
                task=ex.get("question", ""),
                messages=ex.get("messages", []),
                target_tools=ex.get("target_tools", []),
                source_dataset="Toucan-1.5M",
                source_subset=subset,
                subset_type=ex.get("subset"),  # single-turn-original, multi-turn, etc.
                question_quality=ex.get("question_quality_assessment"),
                response_quality=ex.get("response_quality_assessment"),
                metadata={
                    "uuid": ex.get("uuid"),
                    "original_metadata": ex.get("metadata")
                }
            )
            yield trajectory


def trajectory_to_dict(traj: OpenDatasetTrajectory) -> Dict:
    """Convert trajectory to serializable dictionary."""
    return {
        "task": traj.task,
        "messages": traj.messages,
        "target_tools": traj.target_tools,
        "source_dataset": traj.source_dataset,
        "source_subset": traj.source_subset,
        "subset_type": traj.subset_type,
        "question_quality": traj.question_quality,
        "response_quality": traj.response_quality,
        "metadata": traj.metadata
    }


def main():
    parser = argparse.ArgumentParser(
        description="Load open source trajectory datasets for training",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Load 1000 samples from Toucan Kimi-K2 subset
    python load_open_datasets.py --dataset toucan --subset Kimi-K2 --sample 1000
    
    # Load all Qwen3-32B trajectories
    python load_open_datasets.py --dataset toucan --subset Qwen3-32B
    
    # Custom output directory
    python load_open_datasets.py --dataset toucan --output ./my_data/
"""
    )
    parser.add_argument("--dataset", choices=["toucan"], 
                        default="toucan",
                        help="Which dataset to load (currently only 'toucan' is supported)")
    parser.add_argument("--subset", type=str, default="Kimi-K2",
                        help="Dataset subset (for Toucan: Kimi-K2, Qwen3-32B, GPT-OSS-120B)")
    parser.add_argument("--sample", "-n", type=int, default=None,
                        help="Sample size (if not specified, load all)")
    parser.add_argument("--output", "-o", type=str, default="../data/open_datasets/",
                        help="Output directory")
    parser.add_argument("--format", choices=["jsonl", "json"], default="jsonl",
                        help="Output format (jsonl recommended for large datasets)")
    
    args = parser.parse_args()
    
    # Validate
    if not HAS_DATASETS:
        print("❌ Error: 'datasets' package not installed")
        print("   Install with: pip install datasets")
        return 1
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load dataset
    if args.dataset == "toucan":
        if args.subset not in ToucanLoader.AVAILABLE_SUBSETS:
            print(f"❌ Error: Unknown subset '{args.subset}'")
            print(f"   Available subsets: {ToucanLoader.AVAILABLE_SUBSETS}")
            return 1
        trajectories = ToucanLoader.load(args.subset, sample_size=args.sample)
    else:
        print(f"❌ Error: Unknown dataset '{args.dataset}'")
        return 1
    
    # Save
    output_file = output_dir / f"{args.dataset}_{args.subset}_trajectories.{args.format}"
    saved = 0
    
    print(f"Saving to {output_file}...")
    
    if args.format == "jsonl":
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, traj in enumerate(trajectories):
                f.write(json.dumps(trajectory_to_dict(traj), ensure_ascii=False) + '\n')
                saved += 1
                if (i + 1) % 1000 == 0:
                    print(f"  Progress: {i + 1:,} trajectories saved...")
    
    elif args.format == "json":
        data = [trajectory_to_dict(t) for t in trajectories]
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        saved = len(data)
    
    print(f"\n✅ Saved {saved:,} trajectories to {output_file}")
    print(f"   Size: {output_file.stat().st_size:,} bytes ({output_file.stat().st_size / 1024 / 1024:.1f} MB)")
    return 0


if __name__ == "__main__":
    exit(main())
