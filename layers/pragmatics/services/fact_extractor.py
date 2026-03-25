"""
Memory Summarizer

Summarizes what's worth remembering from conversational text using Ollama LLM.
Instead of extracting structured key:value facts, this creates a concise summary
of personal information, preferences, and context worth preserving.

This is a middle ground between:
  - Full prompt saving (too much noise)
  - Structured fact extraction (too brittle, loses context)
"""

import os
import logging
from typing import List, Dict, Any, Optional

import httpx

logger = logging.getLogger("pragmatics.memory_summarizer")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
# Uses the main model - no separate fact extraction model needed

SUMMARIZE_PROMPT = """Summarize what's worth REMEMBERING about this user from their message.

Focus ONLY on:
- Personal identity (name, location, job)
- Relationships (spouse, family, pets)
- Preferences and opinions ("I prefer...", "I like...", "I hate...")
- Custom terminology ("when I say X, I mean Y")
- Important context for future conversations

DO NOT summarize:
- General questions (e.g., "What is the capital of France?")
- Casual mentions without preference signals
- Technical requests without personal info

If nothing is worth remembering, respond with exactly: NOTHING_TO_REMEMBER

Keep the summary concise - 1-3 sentences max.

Message: {text}

Summary:"""


async def summarize_for_memory(
    text: str, model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Summarize what's worth remembering from text using LLM.

    Returns dict with:
      - summary: string summary of what to remember (or None if nothing worth saving)
      - facts: list with one {type: "memory", value: summary} for storage compatibility

    Uses the main Ollama model for better context understanding.
    """
    if not text or len(text.strip()) < 10:
        return _empty_result()

    # Use provided model or default to r1-distill-aj (main model)
    ollama_model = model or "r1-distill-aj:32b-8k"

    prompt = SUMMARIZE_PROMPT.format(text=text)

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Some creativity for natural summaries
                        "num_predict": 150,  # Short summaries only
                    },
                },
            )

            if response.status_code != 200:
                logger.warning(f"Ollama returned {response.status_code}")
                return _empty_result()

            result = response.json()
            summary = result.get("response", "").strip()

            # Check if LLM said nothing worth remembering
            if not summary or "NOTHING_TO_REMEMBER" in summary.upper():
                logger.debug(f"LLM found nothing to remember: {text[:50]}...")
                return _empty_result()

            # Clean up the summary
            summary = _clean_summary(summary)

            if not summary:
                return _empty_result()

            logger.info(f"Memory summary: {summary[:100]}...")

            # Return in format compatible with existing storage
            return {"summary": summary, "facts": [{"type": "memory", "value": summary}]}

    except httpx.TimeoutException:
        logger.warning("Ollama timeout during summarization")
        return _empty_result()
    except httpx.ConnectError:
        logger.warning(f"Cannot connect to Ollama at {OLLAMA_HOST}:{OLLAMA_PORT}")
        return _empty_result()
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        return _empty_result()


def _clean_summary(summary: str) -> str:
    """Clean up LLM summary output."""
    # Remove any markdown formatting
    summary = summary.strip()

    # Remove leading "Summary:" if present
    if summary.lower().startswith("summary:"):
        summary = summary[8:].strip()

    # Remove quotes if wrapped
    if summary.startswith('"') and summary.endswith('"'):
        summary = summary[1:-1].strip()

    # Reject if too short or generic
    if len(summary) < 10:
        return ""

    # Reject if it's just a restatement of the prompt
    generic_phrases = [
        "nothing to remember",
        "no personal information",
        "general question",
        "no preferences",
    ]
    if any(phrase in summary.lower() for phrase in generic_phrases):
        return ""

    return summary


def _empty_result() -> Dict[str, Any]:
    """Return empty result."""
    return {"summary": None, "facts": []}


# Compatibility aliases for existing code
async def extract_facts_llm(text: str, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract facts from text - now uses summarization.

    This is a compatibility wrapper - new code should use summarize_for_memory().
    """
    return await summarize_for_memory(text, model)


def facts_to_storage_format(result: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Convert summarization result to storage format.

    Returns list of {type, value} dicts for Qdrant storage.
    """
    return result.get("facts", [])
