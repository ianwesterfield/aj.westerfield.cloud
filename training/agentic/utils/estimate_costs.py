#!/usr/bin/env python3
"""
Cost Estimator for Agentic Training Pipeline

Estimates costs for:
1. Data generation (API calls)
2. SFT training (GPU compute)
3. DPO training (GPU compute)

Usage:
    python estimate_costs.py
    python estimate_costs.py --trajectories 50000 --preferences 10000
"""

import argparse
from dataclasses import dataclass
from typing import Dict


@dataclass
class ComputeProvider:
    name: str
    gpu_type: str
    hourly_rate: float  # USD per GPU-hour
    gpus_per_node: int


# Popular providers (prices as of late 2025, subject to change)
PROVIDERS = {
    "lambda": ComputeProvider("Lambda Labs", "H100 80GB", 2.49, 8),
    "runpod": ComputeProvider("RunPod", "H100 80GB", 2.79, 8),
    "vast": ComputeProvider("Vast.ai", "H100 80GB", 2.50, 8),
    "together": ComputeProvider("Together.ai", "H100 80GB", 2.50, 8),
    "aws_p5": ComputeProvider("AWS p5.48xlarge", "H100 80GB", 98.32, 8),  # On-demand
    "aws_p5_spot": ComputeProvider("AWS p5 Spot", "H100 80GB", 35.00, 8),  # ~65% discount
    "gcp_a3": ComputeProvider("GCP a3-highgpu-8g", "H100 80GB", 85.00, 8),
    "azure_nd": ComputeProvider("Azure ND H100 v5", "H100 80GB", 78.00, 8),
}

# API costs for data generation
API_COSTS = {
    "claude-3-opus": 0.015 + 0.075,  # $15/M input + $75/M output, ~$0.09 per 1K tokens
    "claude-3-sonnet": 0.003 + 0.015,
    "gpt-4-turbo": 0.01 + 0.03,
    "gpt-4o": 0.005 + 0.015,
}


def estimate_data_generation_cost(
    num_trajectories: int,
    tokens_per_trajectory: int = 2000,
    api_model: str = "claude-3-sonnet"
) -> float:
    """Estimate cost of generating trajectory data via API."""
    
    total_tokens = num_trajectories * tokens_per_trajectory
    cost_per_1k = API_COSTS.get(api_model, 0.02)
    
    return (total_tokens / 1000) * cost_per_1k


def estimate_training_cost(
    model_size_b: int,
    num_examples: int,
    epochs: int,
    provider: ComputeProvider,
    training_type: str = "sft"
) -> Dict:
    """Estimate training compute cost."""
    
    # Rough estimates based on model size and data
    # These are approximations - actual times vary based on implementation
    
    if training_type == "sft":
        # Full fine-tune: ~1 hour per billion params per 10K examples per epoch
        base_hours = (model_size_b / 10) * (num_examples / 10000) * epochs
    else:  # DPO
        # DPO is generally faster
        base_hours = (model_size_b / 20) * (num_examples / 10000) * epochs
    
    # 8 GPU cluster
    node_hours = base_hours  # Already accounting for parallelism
    total_cost = node_hours * provider.hourly_rate * provider.gpus_per_node
    
    return {
        "hours": base_hours,
        "node_hours": node_hours,
        "cost": total_cost,
        "provider": provider.name,
        "gpu_type": provider.gpu_type
    }


def main():
    parser = argparse.ArgumentParser(description="Estimate training costs")
    parser.add_argument("--trajectories", type=int, default=50000)
    parser.add_argument("--preferences", type=int, default=10000)
    parser.add_argument("--domain-examples", type=int, default=10000)
    parser.add_argument("--model-size", type=int, default=32, help="Model size in billions")
    parser.add_argument("--provider", type=str, default="lambda", 
                        choices=list(PROVIDERS.keys()))
    
    args = parser.parse_args()
    
    provider = PROVIDERS[args.provider]
    total_sft_examples = args.trajectories + args.domain_examples
    
    print("=" * 60)
    print("AGENTIC TRAINING COST ESTIMATE")
    print("=" * 60)
    print()
    
    # Data generation
    print("📊 DATA GENERATION (API Costs)")
    print("-" * 40)
    
    api_costs = {}
    for model, _ in [("claude-3-sonnet", "Recommended"), ("gpt-4o", "Alternative")]:
        cost = estimate_data_generation_cost(args.trajectories, api_model=model)
        api_costs[model] = cost
        print(f"  {model}: ${cost:,.2f} for {args.trajectories:,} trajectories")
    
    print()
    
    # SFT Training
    print(f"🏋️ SFT TRAINING ({args.model_size}B model)")
    print("-" * 40)
    
    sft = estimate_training_cost(
        args.model_size, 
        total_sft_examples, 
        epochs=3,
        provider=provider,
        training_type="sft"
    )
    print(f"  Examples: {total_sft_examples:,} ({args.trajectories:,} trajectories + {args.domain_examples:,} domain)")
    print(f"  Epochs: 3")
    print(f"  Estimated time: {sft['hours']:.1f} hours ({sft['hours']/24:.1f} days)")
    print(f"  Provider: {provider.name} ({provider.gpu_type})")
    print(f"  Rate: ${provider.hourly_rate}/GPU-hour × {provider.gpus_per_node} GPUs")
    print(f"  Cost: ${sft['cost']:,.2f}")
    
    print()
    
    # DPO Training
    print(f"🎯 DPO TRAINING ({args.model_size}B model)")
    print("-" * 40)
    
    dpo = estimate_training_cost(
        args.model_size,
        args.preferences,
        epochs=1,
        provider=provider,
        training_type="dpo"
    )
    print(f"  Preference pairs: {args.preferences:,}")
    print(f"  Epochs: 1")
    print(f"  Estimated time: {dpo['hours']:.1f} hours ({dpo['hours']/24:.1f} days)")
    print(f"  Cost: ${dpo['cost']:,.2f}")
    
    print()
    
    # Totals
    print("=" * 60)
    print("💰 TOTAL ESTIMATED COSTS")
    print("=" * 60)
    
    api_cost = api_costs["claude-3-sonnet"]
    total = api_cost + sft["cost"] + dpo["cost"]
    total_time = sft["hours"] + dpo["hours"]
    
    print(f"  Data generation:  ${api_cost:>10,.2f}")
    print(f"  SFT training:     ${sft['cost']:>10,.2f}")
    print(f"  DPO training:     ${dpo['cost']:>10,.2f}")
    print(f"  {'─' * 28}")
    print(f"  TOTAL:            ${total:>10,.2f}")
    print()
    print(f"  Total compute time: {total_time:.1f} hours ({total_time/24:.1f} days)")
    
    print()
    print("=" * 60)
    print("📋 COMPARISON BY PROVIDER")
    print("=" * 60)
    
    for name, prov in sorted(PROVIDERS.items(), key=lambda x: x[1].hourly_rate):
        sft_cost = estimate_training_cost(args.model_size, total_sft_examples, 3, prov, "sft")
        dpo_cost = estimate_training_cost(args.model_size, args.preferences, 1, prov, "dpo")
        total_prov = api_cost + sft_cost["cost"] + dpo_cost["cost"]
        print(f"  {prov.name:25} ${total_prov:>10,.2f} (${prov.hourly_rate}/GPU-hr)")
    
    print()
    print("Note: These are rough estimates. Actual costs depend on:")
    print("  - Implementation efficiency")
    print("  - Sequence lengths")
    print("  - Provider availability")
    print("  - Spot instance interruptions")


if __name__ == "__main__":
    main()
