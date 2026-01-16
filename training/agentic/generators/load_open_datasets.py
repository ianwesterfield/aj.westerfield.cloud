#!/usr/bin/env python3
"""
Open Dataset Loader

Integrates publicly available trajectory datasets from HuggingFace and other sources.
Converts them to the internal trajectory format for hybrid training.

Supported datasets:
- Toucan-1.5M (Agent-Ark): 1.6M MCP tool-use trajectories
- WebArena (Stanford): Web navigation trajectories  
- GAIA (Benchmark): Multi-domain agent interactions
- AgentBench (THUDM): Diverse agent tasks

Usage:
    python load_open_datasets.py --dataset toucan --output ../data/
    python load_open_datasets.py --dataset toucan --subset Kimi-K2 --sample 1000
"""

import json
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Generator
from dataclasses import dataclass, asdict

try:
    from datasets import load_dataset
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False


@dataclass
class OpenDatasetTrajectory:
    """Unified format for trajectories from open datasets."""
    task: str
    messages: List[Dict]  # Chat format messages
    target_tools: List[str]
    source_dataset: str
    source_subset: str
    question_quality: Optional[Dict] = None
    response_quality: Optional[Dict] = None
    metadata: Optional[Dict] = None


class ToucanLoader:
    """Load Toucan-1.5M dataset from HuggingFace."""
    
    DATASET_ID = "Agent-Ark/Toucan-1.5M"
    AVAILABLE_SUBSETS = ["Kimi-K2", "Qwen3-32B", "GPT-OSS-120B"]
    
    @staticmethod
    def load(subset: str = "Kimi-K2", split: str = "train", 
             sample_size: Optional[int] = None) -> Generator[OpenDatasetTrajectory, None, None]:
        """
        Load Toucan dataset with optional sampling.
        
        Args:
            subset: One of Kimi-K2, Qwen3-32B, GPT-OSS-120B
            split: train/test (note: Toucan-1.5M only has 'train')
            sample_size: If specified, randomly sample this many examples
        
        Yields:
            OpenDatasetTrajectory objects
        """
        if not DATASETS_AVAILABLE:
            raise ImportError("datasets package required: pip install datasets")
        
        if subset not in ToucanLoader.AVAILABLE_SUBSETS:
            raise ValueError(f"Unknown subset. Available: {ToucanLoader.AVAILABLE_SUBSETS}")
        
        print(f"Loading Toucan-1.5M ({subset})...")
        dataset = load_dataset(ToucanLoader.DATASET_ID, subset, split=split)
        
        if sample_size:
            dataset = dataset.shuffle(seed=42).select(range(min(sample_size, len(dataset))))
            print(f"Sampling {sample_size} examples")
        else:
            print(f"Loaded {len(dataset)} examples")
        
        for example in dataset:
            trajectory = OpenDatasetTrajectory(
                task=example.get("question", ""),
                messages=example.get("messages", []),
                target_tools=example.get("target_tools", []),
                source_dataset="Toucan-1.5M",
                source_subset=subset,
                question_quality=example.get("question_quality_assessment"),
                response_quality=example.get("response_quality_assessment"),
                metadata={
                    "uuid": example.get("uuid"),
                    "subset_type": example.get("subset"),  # single-turn-original, multi-turn, etc.
                    "original_metadata": example.get("metadata")
                }
            )
            yield trajectory


class WebArenaLoader:
    """Load WebArena dataset."""
    
    DATASET_ID = "web-arena/web-arena"
    
    @staticmethod
    def load(split: str = "train", sample_size: Optional[int] = None):
        """Load WebArena trajectories."""
        if not DATASETS_AVAILABLE:
            raise ImportError("datasets package required: pip install datasets")
        
        print(f"Loading WebArena ({split})...")
        # Note: Actual WebArena loading would require specific processing
        print("WebArena loader not yet implemented")
        return []


class GAIALoader:
    """Load GAIA benchmark trajectories."""
    
    DATASET_ID = "gaia-benchmark/GAIA"
    
    @staticmethod
    def load(split: str = "train", sample_size: Optional[int] = None):
        """Load GAIA trajectories."""
        if not DATASETS_AVAILABLE:
            raise ImportError("datasets package required: pip install datasets")
        
        print(f"Loading GAIA ({split})...")
        print("GAIA loader not yet implemented")
        return []


def trajectory_to_dict(traj: OpenDatasetTrajectory) -> Dict:
    """Convert to serializable format."""
    return {
        "task": traj.task,
        "messages": traj.messages,
        "target_tools": traj.target_tools,
        "source_dataset": traj.source_dataset,
        "source_subset": traj.source_subset,
        "question_quality": traj.question_quality,
        "response_quality": traj.response_quality,
        "metadata": traj.metadata
    }


def main():
    parser = argparse.ArgumentParser(description="Load open source trajectory datasets")
    parser.add_argument("--dataset", choices=["toucan", "webarena", "gaia"], 
                        default="toucan",
                        help="Which dataset to load")
    parser.add_argument("--subset", type=str, default="Kimi-K2",
                        help="Dataset subset (for Toucan: Kimi-K2, Qwen3-32B, GPT-OSS-120B)")
    parser.add_argument("--sample", "-n", type=int, default=None,
                        help="Sample size (if not specified, load all)")
    parser.add_argument("--output", "-o", type=str, default="../data/open_datasets/",
                        help="Output directory")
    parser.add_argument("--format", choices=["jsonl", "json"], default="jsonl",
                        help="Output format")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load dataset
    trajectories = []
    if args.dataset == "toucan":
        trajectories = ToucanLoader.load(args.subset, sample_size=args.sample)
    elif args.dataset == "webarena":
        trajectories = WebArenaLoader.load(sample_size=args.sample)
    elif args.dataset == "gaia":
        trajectories = GAIALoader.load(sample_size=args.sample)
    
    # Save
    output_file = output_dir / f"{args.dataset}_{args.subset}_trajectories.{args.format}"
    saved = 0
    
    if args.format == "jsonl":
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, traj in enumerate(trajectories):
                f.write(json.dumps(trajectory_to_dict(traj), ensure_ascii=False) + '\n')
                saved += 1
                if (i + 1) % 100 == 0:
                    print(f"  Saved {i + 1}...")
    
    elif args.format == "json":
        data = [trajectory_to_dict(t) for t in trajectories]
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        saved = len(data)
    
    print(f"\n✅ Saved {saved} trajectories to {output_file}")
    print(f"   Size: {output_file.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
