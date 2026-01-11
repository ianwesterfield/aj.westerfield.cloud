#!/usr/bin/env python3
"""
Master Training Data Generator
Runs all domain-specific generators and creates combined dataset.
"""

import subprocess
import sys
import json
import random
from pathlib import Path
from datetime import datetime
from typing import List

SCRIPTS_DIR = Path(__file__).parent
DATA_DIR = SCRIPTS_DIR.parent / "data"

# All generator scripts in order
GENERATORS = [
    "generate_git_data.py",
    "generate_vscode_data.py",
    "generate_windows_data.py",
    "generate_linux_data.py",
    "generate_docker_data.py",
    "generate_python_data.py",
    "generate_typescript_data.py",
    "generate_database_data.py",
    "generate_multistep_workflows.py",
    "generate_aiml_data.py",
    "generate_cloud_data.py",
    "generate_security_data.py",
    "generate_api_data.py",
    "generate_dotnet_data.py",
    "generate_nodejs_data.py",
    "generate_angular_data.py",
    "generate_networking_data.py",
    "generate_storage_data.py",
    "generate_memory_data.py",
    "generate_scss_data.py",
    "generate_architecture_data.py",
    "generate_testing_data.py",
    "generate_devops_data.py",
    "generate_web_data.py",
    "generate_programming_data.py",
    "generate_ubiquiti_data.py",
    "generate_firewalla_data.py",  # Firewalla Gold Plus network security
    "generate_mesosync_data.py",  # Workspace-specific knowledge
    "generate_qdrant_data.py",  # Vector database knowledge
    "generate_network_integration_data.py",  # Firewalla + UniFi cross-domain
    "generate_guardrails_extended.py",  # Extended safety guardrails
    "generate_code_snippets.py",  # Code snippet examples (provide_code)
    "extract_training_data.py",
    # New behavioral pattern generators
    "generate_refactoring_data.py",  # Before/after refactoring patterns
    "generate_code_review_data.py",  # Constructive code review feedback
    "generate_multiturn_data.py",  # Multi-turn conversations with context
    "generate_complex_code_data.py",  # Full implementations (provide_code boost)
    "generate_project_planning_data.py",  # Project planning (multi_step_plan boost)
]

def run_generator(script_name: str) -> bool:
    """Run a single generator script."""
    script_path = SCRIPTS_DIR / script_name
    
    if not script_path.exists():
        print(f"  ⚠️  Script not found: {script_name}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=SCRIPTS_DIR
        )
        
        if result.returncode != 0:
            print(f"  ❌ Error in {script_name}:")
            print(result.stderr)
            return False
        
        # Extract example count from output
        for line in result.stdout.split('\n'):
            if 'examples to' in line:
                print(f"  ✓ {line.strip()}")
        
        return True
    except Exception as e:
        print(f"  ❌ Failed to run {script_name}: {e}")
        return False


def count_examples(jsonl_file: Path) -> int:
    """Count examples in a JSONL file."""
    if not jsonl_file.exists():
        return 0
    return sum(1 for _ in open(jsonl_file))


def merge_datasets(output_file: Path) -> int:
    """Merge all JSONL files into one, shuffled."""
    all_examples = []
    
    for jsonl_file in DATA_DIR.glob("*.jsonl"):
        if jsonl_file.name == output_file.name:
            continue
        
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    all_examples.append(json.loads(line))
    
    # Shuffle for better training distribution
    random.shuffle(all_examples)
    
    # Write combined file
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    return len(all_examples)


def generate_stats() -> dict:
    """Generate statistics for the dataset."""
    stats = {
        "total_examples": 0,
        "by_domain": {},
        "response_types": {
            "execute_command": 0,
            "provide_code": 0,
            "multi_step_plan": 0,
            "concepts": 0,
            "errors": 0
        }
    }
    
    for jsonl_file in DATA_DIR.glob("*.jsonl"):
        if jsonl_file.name.startswith("all_"):
            continue
        
        domain = jsonl_file.stem
        count = 0
        
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1
                    example = json.loads(line)
                    
                    # Categorize response type
                    response = example.get("response", "")
                    if isinstance(response, str):
                        if response.startswith('{'):
                            try:
                                resp_data = json.loads(response)
                                action = resp_data.get("action", "")
                                if action in stats["response_types"]:
                                    stats["response_types"][action] += 1
                                elif "error" in str(resp_data).lower() or "status" in resp_data:
                                    stats["response_types"]["errors"] += 1
                            except:
                                stats["response_types"]["concepts"] += 1
                        else:
                            stats["response_types"]["concepts"] += 1
        
        stats["by_domain"][domain] = count
        stats["total_examples"] += count
    
    return stats


def main():
    print("=" * 70)
    print("AJ Training Data Generator - Master Runner")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)
    
    # Run all generators
    print("\n📊 Running domain generators...\n")
    
    successful = 0
    failed = 0
    
    for script in GENERATORS:
        print(f"\n→ Running {script}...")
        if run_generator(script):
            successful += 1
        else:
            failed += 1
    
    print(f"\n\n{'='*70}")
    print(f"Generator Results: {successful} successful, {failed} failed")
    print("=" * 70)
    
    # Merge all datasets
    print("\n📦 Merging all datasets...")
    combined_file = DATA_DIR / "all_training_data.jsonl"
    total = merge_datasets(combined_file)
    print(f"   ✓ Created {combined_file.name} with {total:,} examples")
    
    # Generate and display statistics
    print("\n📈 Dataset Statistics:")
    print("-" * 50)
    
    stats = generate_stats()
    
    print(f"\nTotal Examples: {stats['total_examples']:,}")
    print("\nBy Domain:")
    for domain, count in sorted(stats['by_domain'].items()):
        pct = (count / stats['total_examples'] * 100) if stats['total_examples'] else 0
        bar = "█" * int(pct / 2)
        print(f"  {domain:<25} {count:>5} ({pct:5.1f}%) {bar}")
    
    print("\nResponse Types:")
    for resp_type, count in stats['response_types'].items():
        pct = (count / stats['total_examples'] * 100) if stats['total_examples'] else 0
        print(f"  {resp_type:<20} {count:>5} ({pct:5.1f}%)")
    
    # Save stats
    stats_file = DATA_DIR / "dataset_stats.json"
    with open(stats_file, "w") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            **stats
        }, f, indent=2)
    print(f"\n✓ Stats saved to {stats_file.name}")
    
    print("\n" + "=" * 70)
    print(f"🎉 Complete! Training data ready at: {DATA_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
