#!/usr/bin/env python3
"""
Upload training data to HuggingFace Hub for fast download on cloud instances.
"""
import os
import sys
from pathlib import Path
from huggingface_hub import HfApi, login

# Config
REPO_ID = "ajwesterfield/granite-training-data"  # Change to your HF username
DATA_FILE = Path(__file__).parent / "data" / "all_training_data_merged.jsonl"

def main():
    print("=" * 60)
    print("Upload Training Data to HuggingFace Hub")
    print("=" * 60)
    
    if not DATA_FILE.exists():
        print(f"ERROR: Data file not found: {DATA_FILE}")
        sys.exit(1)
    
    file_size_gb = DATA_FILE.stat().st_size / 1e9
    print(f"File: {DATA_FILE.name}")
    print(f"Size: {file_size_gb:.2f} GB")
    print(f"Repo: {REPO_ID}")
    
    # Login to HuggingFace
    print("\nLogging in to HuggingFace...")
    print("(If not logged in, run: huggingface-cli login)")
    
    api = HfApi()
    
    # Create repo if it doesn't exist
    print(f"\nCreating/checking repo: {REPO_ID}")
    try:
        api.create_repo(
            repo_id=REPO_ID,
            repo_type="dataset",
            private=True,  # Keep it private!
            exist_ok=True
        )
    except Exception as e:
        print(f"Note: {e}")
    
    # Upload the file
    print(f"\nUploading {DATA_FILE.name}...")
    print("This may take a while for large files...")
    
    api.upload_file(
        path_or_fileobj=str(DATA_FILE),
        path_in_repo="all_training_data_merged.jsonl",
        repo_id=REPO_ID,
        repo_type="dataset",
    )
    
    print("\n" + "=" * 60)
    print("✓ Upload complete!")
    print("=" * 60)
    print(f"\nDataset URL: https://huggingface.co/datasets/{REPO_ID}")
    print("\nTo download on vast.ai:")
    print(f"  huggingface-cli download {REPO_ID} --repo-type dataset --local-dir /workspace/training/data")


if __name__ == "__main__":
    main()
