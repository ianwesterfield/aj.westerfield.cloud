"""
Summarizer

Generates summaries of stored memories using Ollama/Qwen.
This replaces the previous DistilBART implementation for consolidated
model architecture.

Env vars:
  - OLLAMA_HOST (default: http://ollama:11434)
  - OLLAMA_MODEL (default: qwen2.5:14b)
"""

import os
import re
from typing import Optional
import httpx

# Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")

# Reusable HTTP client
_client = None


def _get_client() -> httpx.Client:
    """Get or create HTTP client for Ollama API."""
    global _client
    if _client is None:
        _client = httpx.Client(timeout=60.0)  # Longer timeout for generation
    return _client


def summarize(text: str, max_words: int = 60) -> str:
    """
    Summarize text using Ollama/Qwen.
    
    Falls back to heuristic (first sentences) if Ollama is unavailable.
    
    Args:
        text: Text to summarize
        max_words: Target maximum words in summary
        
    Returns:
        Summarized text
    """
    print(f"[summarizer] summarize() called, text length={len(text or '')}, max_words={max_words}")
    text = (text or "").strip()
    if not text:
        print("[summarizer] Empty text, returning empty string")
        return ""

    # Try Ollama/Qwen summarization
    try:
        print("[summarizer] Using Ollama/Qwen for summarization")
        client = _get_client()
        
        prompt = f"""Summarize the following text in {max_words} words or less. 
Focus on key personal facts, dates, names, and preferences. Be concise.

Text:
{text}

Summary:"""
        
        response = client.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": max_words * 2,  # Rough token estimate
                }
            }
        )
        response.raise_for_status()
        
        data = response.json()
        summary = data.get("response", "").strip()
        
        if summary:
            print(f"[summarizer] Ollama returned summary: {summary[:80]}..." if len(summary) > 80 else f"[summarizer] Ollama returned summary: {summary}")
            return summary
            
    except Exception as e:
        print(f"[summarizer] Ollama summarization failed: {e}")

    # Fallback: take first sentences and trim to max_words
    print("[summarizer] Using heuristic fallback")
    sentences = re.split(r"(?<=[.!?])\s+", text)
    summary = " ".join(sentences[:2])
    words = summary.split()
    if len(words) > max_words:
        summary = " ".join(words[:max_words]) + "…"
    print(f"[summarizer] Heuristic summary: {summary[:80]}..." if len(summary) > 80 else f"[summarizer] Heuristic summary: {summary}")
    return summary