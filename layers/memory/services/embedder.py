"""
Embedding Service

Generates semantic embeddings using Ollama's nomic-embed-text model.
This replaces the previous SentenceTransformers implementation for
consolidated model architecture.

The embeddings are normalized (L2), so COSINE ≈ DOT product.

Key functions:
    embed(text) - embed a single string
    embed_messages(messages) - embed a full conversation with role prefixes

Environment:
    OLLAMA_HOST - Ollama server URL (default: http://ollama:11434)
    EMBEDDING_MODEL - Model name (default: nomic-embed-text)
"""

import os
import httpx
from typing import List, Any

# Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

# Reusable HTTP client
_client = None


def _get_client() -> httpx.Client:
    """Get or create HTTP client for Ollama API."""
    global _client
    if _client is None:
        _client = httpx.Client(timeout=30.0)
    return _client


def _embed_via_ollama(text: str) -> List[float]:
    """
    Call Ollama embedding API.
    
    Args:
        text: Text to embed
        
    Returns:
        List of floats (embedding vector)
    """
    client = _get_client()
    
    response = client.post(
        f"{OLLAMA_HOST}/api/embeddings",
        json={
            "model": EMBEDDING_MODEL,
            "prompt": text,
        }
    )
    response.raise_for_status()
    
    data = response.json()
    return data.get("embedding", [])


def _extract_text_from_content(content: List[dict] | str) -> str:
    """
    Extract text from message content. Handles both plain strings
    and multi-modal arrays (text + images). Images become "[image]".
    """
    if isinstance(content, str):
        return content
    
    text_parts = []
    
    if isinstance(content, list):
        
        for item in content:
            
            if isinstance(item, dict):
    
                if item.get("type") == "text" and "text" in item:
                    text_parts.append(item["text"])
                elif item.get("type") == "image_url":
                    # For images, add a placeholder
                    text_parts.append("[image]")
    
    return " ".join(text_parts)

def embed_messages(messages: List[dict]) -> List[float]:
    """
    Turn a full conversation into a single embedding vector.
    
    Joins all messages with their roles as prefixes (like "[user] ..."),
    then embeds. Handles both dicts and Pydantic models.
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys
        
    Returns:
        List of floats (embedding vector, typically 768-dim for nomic-embed-text)
    """
    text_parts = []
    
    for msg in messages:
        if hasattr(msg, 'model_dump'):
            msg = msg.model_dump()
        
        if isinstance(msg, dict):
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role:
                text_parts.append(f"[{role}]")
            
            extracted = _extract_text_from_content(content)
            if extracted:
                text_parts.append(extracted)
    
    combined_text = " ".join(text_parts)
    
    if not combined_text.strip():
        combined_text = "[empty conversation]"
    
    return _embed_via_ollama(combined_text)


def embed(text: str) -> List[float]:
    """
    Embed a single string.
    
    Low-level version—use embed_messages() for conversations.
    
    Args:
        text: Text to embed
        
    Returns:
        List of floats (embedding vector)
    """
    return _embed_via_ollama(text)