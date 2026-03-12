"""
LLM-based Fact Extractor

Extracts structured facts from conversational text using Ollama LLM.
No regex - pure LLM-based semantic extraction.

Flexible schema: the LLM decides WHAT to extract and HOW to categorize it.
Each fact has:
  - type: semantic category (e.g., "firstName", "spouse", "preference", "terminology")
  - value: the actual fact content
  - reason: why this is worth saving (for debugging/transparency)
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional

import httpx

logger = logging.getLogger("pragmatics.fact_extractor")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "ollama")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "11434")
OLLAMA_MODEL = os.getenv("FACT_EXTRACTION_MODEL", "qwen2.5:1.5b")

EXTRACTION_PROMPT = """You are a fact extractor. Identify PERSONAL PREFERENCES and IDENTITY FACTS worth remembering from this message.

For each fact, provide:
- "type": A semantic category name (camelCase). Choose the MOST SPECIFIC type that describes this fact.
  Examples: firstName, lastName, spouse, child, boss, favoriteColor, prefersDarkMode, terminology, hometown, occupation, birthday
- "value": The actual fact content
- "reason": Brief explanation of why this is worth saving

CRITICAL GUIDELINES:
- ONLY extract facts that indicate PREFERENCES, IDENTITY, or RELATIONSHIPS
- DO NOT extract casual mentions or references (e.g., "I was watching X" is NOT a favorite show)
- DO NOT extract topics from QUESTIONS (e.g., "How many episodes in Big Bang Theory?" reveals nothing about the user)
- Look for signal words: "favorite", "love", "prefer", "hate", "always", "my", "I am", "I work as"
- Use specific types: "spouse" not "relationship", "favoriteColor" not "preference"
- For terminology definitions ("when I say X, I mean Y"), use type "terminology" with value "X = Y"
- If nothing indicates a preference or identity fact, return empty array

OUTPUT FORMAT (JSON array):
{{"facts": [
  {{"type": "firstName", "value": "Ian", "reason": "User introduced their first name"}},
  {{"type": "spouse", "value": "Sarah", "reason": "User mentioned wife's name"}}
]}}

EXAMPLES:

Input: "My name is Ian, I prefer dark mode. When I say agents I mean FunnelCloud Agents."
Output: {{"facts": [
  {{"type": "firstName", "value": "Ian", "reason": "User introduced themselves"}},
  {{"type": "prefersDarkMode", "value": "true", "reason": "Stated UI preference"}},
  {{"type": "terminology", "value": "agents = FunnelCloud Agents", "reason": "Explicit definition"}}
]}}

Input: "My wife Sarah and I live in Austin with our dog Max"
Output: {{"facts": [
  {{"type": "spouse", "value": "Sarah", "reason": "Named their wife"}},
  {{"type": "city", "value": "Austin", "reason": "Where they live"}},
  {{"type": "pet", "value": "Max (dog)", "reason": "Named their pet"}}
]}}

Input: "I was watching Big Bang Theory last night"
Output: {{"facts": []}}

Input: "How many episodes are in each season of Big Bang Theory?"
Output: {{"facts": []}}

Input: "What is the capital of France?"
Output: {{"facts": []}}

Input: "Can you help me write a Python script?"
Output: {{"facts": []}}

Input: "Big Bang Theory is my favorite show!"
Output: {{"facts": [
  {{"type": "favoriteShow", "value": "Big Bang Theory", "reason": "Explicitly stated as favorite"}}
]}}

Input: "How are you today?"
Output: {{"facts": []}}

Input: "I work as a software engineer at Google"
Output: {{"facts": [
  {{"type": "occupation", "value": "software engineer", "reason": "Stated their job"}},
  {{"type": "employer", "value": "Google", "reason": "Where they work"}}
]}}

Message: {text}

JSON:"""


# Valid fact types - whitelist of acceptable semantic categories
VALID_FACT_TYPES = {
    # Identity
    "firstname",
    "lastname",
    "fullname",
    "name",
    "nickname",
    "preferredname",
    "birthday",
    "birthdate",
    "age",
    # Location
    "city",
    "hometown",
    "location",
    "country",
    "state",
    "address",
    # Work
    "occupation",
    "job",
    "employer",
    "company",
    "workplace",
    "role",
    "title",
    # Relationships
    "spouse",
    "wife",
    "husband",
    "partner",
    "child",
    "parent",
    "sibling",
    "friend",
    "pet",
    "dog",
    "cat",
    # Preferences
    "favoritecolor",
    "favoriteshow",
    "favoritebook",
    "favoritemovie",
    "favoritemusic",
    "favoritefood",
    "favoritegenre",
    "favoriteartist",
    "prefersdarkmode",
    "preferslightmode",
    "preference",
    # Terminology
    "terminology",
    "alias",
    "definition",
    # Other personal
    "hobby",
    "interest",
    "skill",
    "language",
    "education",
    "school",
}

# Invalid value patterns - things that shouldn't be saved as facts
GREETING_WORDS = {"hola", "hello", "hi", "hey", "howdy", "greetings", "yo", "sup"}
RESPONSE_PREFIXES = {"yes", "no", "maybe", "sure", "ok", "okay", "yeah", "nah", "nope"}


def _is_invalid_fact(fact_type: str, fact_value: str) -> bool:
    """
    Check if a fact should be rejected.

    Returns True if the fact is invalid and should NOT be saved.
    """
    type_lower = fact_type.lower().replace("_", "").replace("-", "")
    value_lower = fact_value.lower().strip()

    # Reject if type is not in whitelist
    if type_lower not in VALID_FACT_TYPES:
        logger.debug(f"Reject: type '{fact_type}' not in whitelist")
        return True

    # Reject if value is just a number (e.g., "season: 1")
    if value_lower.isdigit() or value_lower.replace(".", "").isdigit():
        logger.debug(f"Reject: value is just a number '{fact_value}'")
        return True

    # Reject if value is a greeting word (e.g., "firstName: Hola!")
    value_word = value_lower.rstrip("!?.").strip()
    if value_word in GREETING_WORDS:
        logger.debug(f"Reject: value is a greeting '{fact_value}'")
        return True

    # Reject if value starts with a response prefix (e.g., "collaboration: Yes, they...")
    first_word = value_lower.split(",")[0].split()[0] if value_lower.split() else ""
    if first_word in RESPONSE_PREFIXES:
        logger.debug(f"Reject: value starts with response prefix '{fact_value}'")
        return True

    # Reject if value is too long (likely an answer, not a fact)
    if len(fact_value) > 100:
        logger.debug(f"Reject: value too long ({len(fact_value)} chars)")
        return True

    # Reject if value contains multiple sentences (likely an explanation)
    if fact_value.count(". ") >= 2:
        logger.debug(f"Reject: value contains multiple sentences")
        return True

    return False


async def extract_facts_llm(text: str) -> Dict[str, Any]:
    """
    Extract structured facts from text using LLM.

    Returns dict with:
      - facts: list of {type, value, reason} dicts

    The LLM decides what facts are worth saving and how to categorize them.
    """
    if not text or len(text.strip()) < 5:
        return _empty_result()

    prompt = EXTRACTION_PROMPT.format(text=text)

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,  # Deterministic for structured output
                        "num_predict": 200,  # Compact JSON, don't need much
                    },
                },
            )

            if response.status_code != 200:
                logger.warning(f"Ollama returned {response.status_code}")
                return _empty_result()

            result = response.json()
            llm_response = result.get("response", "")

            # Parse JSON from response
            return _parse_llm_response(llm_response)

    except httpx.TimeoutException:
        logger.warning("Ollama timeout during fact extraction")
        return _empty_result()
    except httpx.ConnectError:
        logger.warning(f"Cannot connect to Ollama at {OLLAMA_HOST}:{OLLAMA_PORT}")
        return _empty_result()
    except Exception as e:
        logger.error(f"Fact extraction failed: {e}")
        return _empty_result()


def _parse_llm_response(response: str) -> Dict[str, Any]:
    """Parse LLM JSON response with flexible fact array."""
    response = response.strip()

    # Extract JSON from markdown code blocks if present
    if "```json" in response:
        start = response.find("```json") + 7
        end = response.find("```", start)
        if end > start:
            response = response[start:end].strip()
    elif "```" in response:
        start = response.find("```") + 3
        end = response.find("```", start)
        if end > start:
            response = response[start:end].strip()

    # Find JSON object boundaries
    if "{" in response:
        start = response.find("{")
        end = response.rfind("}") + 1
        if end > start:
            response = response[start:end]

    try:
        data = json.loads(response)
        facts_raw = data.get("facts", [])

        if not isinstance(facts_raw, list):
            return _empty_result()

        # Minimal guard: reject obviously placeholder/template values
        # that the model may echo from the prompt schema
        placeholder_values = {"string", "value", "type", "null", "none", ""}

        facts = []
        for fact in facts_raw:
            if not isinstance(fact, dict):
                continue

            fact_type = str(fact.get("type", "")).strip()
            fact_value = str(fact.get("value", "")).strip()
            fact_reason = str(fact.get("reason", "")).strip()

            # Skip if type or value is empty or a placeholder
            if not fact_type or not fact_value:
                continue
            if (
                fact_type.lower() in placeholder_values
                or fact_value.lower() in placeholder_values
            ):
                logger.debug(f"Rejected placeholder fact: {fact_type}={fact_value}")
                continue

            # POST-PROCESSING VALIDATION: Reject obviously bad facts
            # The small model doesn't follow instructions well, so we filter here
            if _is_invalid_fact(fact_type, fact_value):
                logger.debug(f"Rejected invalid fact: {fact_type}={fact_value}")
                continue

            facts.append(
                {
                    "type": fact_type,
                    "value": fact_value,
                    "reason": fact_reason,
                }
            )

        return {"facts": facts}

    except json.JSONDecodeError as e:
        logger.debug(f"Failed to parse LLM response as JSON: {e}")
        logger.debug(f"Response was: {response[:200]}")
        return _empty_result()


def _empty_result() -> Dict[str, Any]:
    """Return empty extraction result."""
    return {"facts": []}


def facts_to_storage_format(facts: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Convert LLM-extracted facts to storage format.

    Returns list of {type, value} dicts for Qdrant storage.
    The LLM already provides semantic types - we just strip the reason field.
    """
    result = []

    for fact in facts.get("facts", []):
        fact_type = fact.get("type", "").strip()
        fact_value = fact.get("value", "").strip()

        if fact_type and fact_value:
            result.append({"type": fact_type, "value": fact_value})

    return result
