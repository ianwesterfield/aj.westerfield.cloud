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
OLLAMA_MODEL = os.getenv("FACT_EXTRACTION_MODEL", "llama3.1:8b")

EXTRACTION_PROMPT = """Extract any facts, definitions, or preferences from this user message.

Return a JSON object with these fields (empty arrays if none found):
- terminology: Array of {"alias": "X", "means": "Y"} for definitions like "when I say X I mean Y"
- preferred_name: The user's preferred name if mentioned (string or null)
- preferences: Array of strings for user preferences
- relationships: Array of {"relation": "wife/friend/etc", "name": "Name"} for mentioned people

User message: {text}

Respond with ONLY valid JSON, no explanation:"""


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
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temp for structured output
                        "num_predict": 500,
                    }
                }
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
        return {
            "terminology": _normalize_terminology(data.get("terminology", [])),
            "preferred_name": data.get("preferred_name"),
            "preferences": data.get("preferences", []) or [],
            "relationships": data.get("relationships", []) or [],
        }
    except json.JSONDecodeError as e:
        logger.debug(f"Failed to parse LLM response as JSON: {e}")
        logger.debug(f"Response was: {response[:200]}")
        return _empty_result()


def _normalize_terminology(terms: Any) -> List[Dict[str, str]]:
    """Normalize terminology list to consistent format."""
    if not isinstance(terms, list):
        return []
    
    result = []
    for term in terms:
        if isinstance(term, dict):
            alias = term.get("alias", "").strip()
            means = term.get("means", "").strip()
            if alias and means:
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
            result.append({
                "type": "terminology",
                "value": f"{alias} = {means}"
            })
    
    # Preferred name
    if facts.get("preferred_name"):
        result.append({
            "type": "preferred_name",
            "value": facts["preferred_name"]
        })
    
    # Preferences
    for pref in facts.get("preferences", []):
        if pref:
            result.append({
                "type": "preference",
                "value": pref
            })
    
    # Relationships
    for rel in facts.get("relationships", []):
        relation = rel.get("relation", "")
        name = rel.get("name", "")
        if relation and name:
            result.append({
                "type": "relationship",
                "value": f"{relation}: {name}"
            })
    
    return result
