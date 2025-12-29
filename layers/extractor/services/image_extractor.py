"""
Image Vision Model Service

Generates detailed text descriptions of images using Ollama's multimodal models.
This consolidates vision capability through the same Ollama instance used for LLM.

Supports:
  - llava: LLaVA vision-language model via Ollama
  - llava:34b: Larger LLaVA variant

Environment:
  - OLLAMA_HOST: Ollama server URL (default: http://ollama:11434)
  - IMAGE_MODEL: Ollama vision model (default: llava)
"""

import base64
import io
import os
from typing import Optional

import httpx
from PIL import Image


# ============================================================================
# Configuration
# ============================================================================

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "llava")

# Reusable HTTP client
_client = None


def _get_client() -> httpx.Client:
    """Get or create HTTP client for Ollama API."""
    global _client
    if _client is None:
        _client = httpx.Client(timeout=120.0)  # Longer timeout for vision
    return _client


# ============================================================================
# Public API
# ============================================================================

async def extract_from_image(image_data: bytes, prompt: Optional[str] = None) -> str:
    """
    Generate text description of an image using Ollama's multimodal API.
    
    Args:
        image_data: Raw image bytes (PNG, JPEG, etc.)
        prompt: Optional guided prompt for description
    
    Returns:
        Text description of the image content
    """
    # Convert image to base64
    image = Image.open(io.BytesIO(image_data)).convert("RGB")
    
    # Save to buffer as PNG for consistent format
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    # Build prompt
    user_prompt = (
        prompt
        if prompt
        else (
            "Describe this image in detail. Include all visible objects, "
            "people, text, colors, and any notable features."
        )
    )
    
    # Call Ollama multimodal API
    client = _get_client()
    
    try:
        response = client.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": IMAGE_MODEL,
                "prompt": user_prompt,
                "images": [image_base64],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 512,
                }
            }
        )
        response.raise_for_status()
        
        data = response.json()
        result = data.get("response", "").strip()
        
        return result if result else "[No description generated]"
        
    except Exception as e:
        print(f"[extractor] Image extraction failed: {e}")
        return f"[Image extraction error: {e}]"


def load_model_at_startup() -> None:
    """
    Preload vision model by making a warmup request.
    
    This ensures the model is loaded in Ollama before the first real request.
    """
    print(f"[extractor] Warming up vision model: {IMAGE_MODEL}")
    
    try:
        # Create a tiny test image (1x1 white pixel)
        img = Image.new("RGB", (1, 1), color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        
        client = _get_client()
        response = client.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": IMAGE_MODEL,
                "prompt": "test",
                "images": [base64.b64encode(buffer.getvalue()).decode("utf-8")],
                "stream": False,
                "options": {"num_predict": 1}
            }
        )
        
        if response.status_code == 200:
            print(f"[extractor] ✓ Vision model {IMAGE_MODEL} ready")
        else:
            print(f"[extractor] Warning: Vision model warmup returned {response.status_code}")
            
    except Exception as e:
        print(f"[extractor] Vision model warmup failed (will load on first request): {e}")
