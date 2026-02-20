"""
LLM-based Fact Extractor

Extracts structured facts from conversational text using Ollama LLM.
No regex - pure LLM-based semantic extraction.

Handles:
  - Terminology definitions ("agents" = FunnelCloud Agents)
  - Preferred names ("Call me Ian")
  - Preferences ("I prefer dark mode")
  - Relationships ("My wife's name is Sarah")
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

EXTRACTION_PROMPT = """Extract personal facts from this message as JSON. Only include facts that are EXPLICITLY stated.

RULES:
- terminology: ONLY for explicit definitions like "when I say X, I mean Y" or "X refers to Y". Do NOT infer terminology from names, greetings, or context.
- preferred_name: The person's name if they introduce themselves.
- preferences: Stated likes/dislikes ("I prefer...", "I like...").
- relationships: Stated relationships ("my wife is...", "my boss is...").
- If nothing matches, return the empty object.

Empty (greetings, casual chat, questions):
{{"terminology":[],"preferred_name":null,"preferences":[],"relationships":[]}}

Example 1 input: "My name is Ian, I prefer dark mode. When I say agents I mean FunnelCloud Agents."
Example 1 output: {{"terminology":[{{"alias":"agents","means":"FunnelCloud Agents"}}],"preferred_name":"Ian","preferences":["dark mode"],"relationships":[]}}

Example 2 input: "Hello AJ, my name is Ian Westerfield"
Example 2 output: {{"terminology":[],"preferred_name":"Ian Westerfield","preferences":[],"relationships":[]}}

Example 3 input: "How are you today?"
Example 3 output: {{"terminology":[],"preferred_name":null,"preferences":[],"relationships":[]}}

Message: {text}

JSON:"""


async def extract_facts_llm(text: str) -> Dict[str, Any]:
    """
    Extract structured facts from text using LLM.

    Returns dict with:
      - terminology: list of {alias, means} dicts
      - preferred_name: str or None
      - preferences: list of strings
      - relationships: list of {relation, name} dicts
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
    """Parse LLM JSON response, handling common issues."""
    response = response.strip()

    # Try to extract JSON from response
    # LLM might include markdown code blocks
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

        # Validate and normalize structure
        result = {
            "terminology": _normalize_terminology(data.get("terminology", [])),
            "preferred_name": data.get("preferred_name"),
            "preferences": data.get("preferences", []) or [],
            "relationships": data.get("relationships", []) or [],
        }

        # GUARD: Strip placeholder/template values the model may have copied
        # These are never real facts - the model sometimes echoes the prompt schema
        bogus = {"strings", "string", "type", "name", "x", "y", "null", "none", ""}
        result["preferences"] = [
            p
            for p in result["preferences"]
            if isinstance(p, str) and p.strip().lower() not in bogus
        ]
        result["relationships"] = [
            r
            for r in result["relationships"]
            if isinstance(r, dict)
            and r.get("name", "").strip().lower() not in bogus
            and r.get("relation", "").strip().lower() not in bogus
        ]
        if (
            result["preferred_name"]
            and result["preferred_name"].strip().lower() in bogus
        ):
            result["preferred_name"] = None

        return result
    except json.JSONDecodeError as e:
        logger.debug(f"Failed to parse LLM response as JSON: {e}")
        logger.debug(f"Response was: {response[:200]}")
        return _empty_result()


def _normalize_terminology(terms: Any) -> List[Dict[str, str]]:
    """Normalize terminology list to consistent format with semantic guards."""
    if not isinstance(terms, list):
        return []

    # Words/phrases that are never valid terminology aliases or definitions
    bogus_terms = {
        "hello",
        "hi",
        "hey",
        "greetings",
        "goodbye",
        "bye",
        "my name",
        "your name",
        "name",
        "me",
        "you",
        "i",
        "thanks",
        "thank you",
        "please",
        "yes",
        "no",
        "ok",
        "okay",
        "null",
        "none",
        "",
        "type",
        "string",
        "value",
    }

    result = []
    for term in terms:
        if isinstance(term, dict):
            alias = term.get("alias", "").strip()
            means = term.get("means", "").strip()
            if not alias or not means:
                continue
            # Reject if alias or means is a bogus/generic term
            if alias.lower() in bogus_terms or means.lower() in bogus_terms:
                logger.debug(f"Rejected bogus terminology: {alias} = {means}")
                continue
            # Reject very short aliases (single char) - not meaningful
            if len(alias) < 2:
                continue
            # Reject if alias looks like a person's name (capitalized, no spaces)
            # and means is a generic phrase - this catches "Ian Westerfield = my name"
            if means.lower().startswith(("my ", "his ", "her ", "a ", "the ")):
                logger.debug(f"Rejected name-as-terminology: {alias} = {means}")
                continue
            result.append({"alias": alias, "means": means})

    return result


def _empty_result() -> Dict[str, Any]:
    """Return empty extraction result."""
    return {
        "terminology": [],
        "preferred_name": None,
        "preferences": [],
        "relationships": [],
    }


def facts_to_storage_format(facts: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Convert LLM-extracted facts to storage format.

    Returns list of {type, value} dicts for Qdrant storage.
    """
    result = []

    # Terminology: "alias = means"
    for term in facts.get("terminology", []):
        alias = term.get("alias", "")
        means = term.get("means", "")
        if alias and means:
            result.append({"type": "terminology", "value": f"{alias} = {means}"})

    # Preferred name
    if facts.get("preferred_name"):
        result.append({"type": "preferred_name", "value": facts["preferred_name"]})

    # Preferences
    for pref in facts.get("preferences", []):
        if pref:
            result.append({"type": "preference", "value": pref})

    # Relationships
    for rel in facts.get("relationships", []):
        relation = rel.get("relation", "")
        name = rel.get("name", "")
        if relation and name:
            result.append({"type": "relationship", "value": f"{relation}: {name}"})

    return result
