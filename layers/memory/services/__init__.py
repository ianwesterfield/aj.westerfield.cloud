"""
Memory Services Package

Core services for the memory API.

Modules:
    embedder: Text embedding using SentenceTransformers (768-dim vectors).
    qdrant_client: Singleton Qdrant client and collection management.
    fact_extractor: Utility functions for formatting pre-extracted facts.
    summarizer: Multi-backend text summarization.
"""