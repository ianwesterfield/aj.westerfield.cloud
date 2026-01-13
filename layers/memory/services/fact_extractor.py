"""
Fact Extractor

Extracts structured facts from conversational text via pragmatics service.
Uses LLM-based extraction for terminology, preferences, and relationships.
Uses spaCy NER for named entities (names, orgs, dates, etc.).

NO REGEX - all extraction delegated to pragmatics service.
"""

import os
import logging
from typing import List, Dict

import requests

logger = logging.getLogger("memory.fact_extractor")

# Pragmatics service URL
PRAGMATICS_API_URL = os.getenv("PRAGMATICS_API_URL", "http://pragmatics_api:8001")


def extract_facts(text: str) -> List[Dict[str, str]]:
    """
    Extract structured facts from text via pragmatics service.
    
    Combines:
    1. LLM-based extraction (terminology, preferences, relationships)
    2. spaCy NER (names, orgs, dates, emails, locations)
    
    Returns list of {type, value} dicts for storage.
    Falls back gracefully if services are unavailable.
    """
    if not text or len(text.strip()) < 3:
        return []
    
    facts = []
    
    # 1. LLM-based fact extraction (terminology, preferences, relationships)
    llm_facts = _extract_facts_llm(text)
    facts.extend(llm_facts)
    
    # 2. spaCy NER extraction (names, orgs, dates, etc.)
    ner_facts = _extract_facts_ner(text)
    facts.extend(ner_facts)
    
    return facts


def _extract_facts_llm(text: str) -> List[Dict[str, str]]:
    """
    Call pragmatics LLM endpoint for semantic fact extraction.
    
    Extracts:
    - Terminology definitions ("agents" = FunnelCloud Agents)
    - Preferred names
    - Preferences
    - Relationships
    """
    try:
        resp = requests.post(
            f"{PRAGMATICS_API_URL}/api/pragmatics/extract-facts-storage",
            json={"text": text},
            timeout=30,  # LLM can take a moment
        )
        
        if resp.status_code == 200:
            result = resp.json()
            facts = result.get("facts", [])
            if facts:
                logger.debug(f"LLM extracted {len(facts)} facts")
            return facts
        else:
            logger.warning(f"Fact extraction returned {resp.status_code}")
            return []
            
    except requests.Timeout:
        logger.warning("Fact extraction timeout")
        return []
    except requests.ConnectionError:
        logger.warning("Pragmatics service unavailable for fact extraction")
        return []
    except Exception as e:
        logger.error(f"Fact extraction failed: {e}")
        return []


def _extract_facts_ner(text: str) -> List[Dict[str, str]]:
    """
    Call pragmatics NER endpoint for named entity extraction.
    
    Extracts:
    - Person names
    - Organizations
    - Dates
    - Emails
    - Locations
    """
    try:
        resp = requests.post(
            f"{PRAGMATICS_API_URL}/api/pragmatics/entities",
            json={"text": text},
            timeout=10,
        )
        
        if resp.status_code == 200:
            entities = resp.json()
            facts = []
            
            for name in entities.get("names", []):
                facts.append({"type": "person_name", "value": name})
            
            for org in entities.get("organizations", []):
                facts.append({"type": "organization", "value": org})
            
            for email in entities.get("emails", []):
                facts.append({"type": "email", "value": email})
            
            for date in entities.get("dates", []):
                facts.append({"type": "date", "value": date})
            
            for loc in entities.get("locations", []):
                facts.append({"type": "location", "value": loc})
            
            if facts:
                logger.debug(f"NER extracted {len(facts)} entities")
            return facts
        else:
            logger.warning(f"NER service returned {resp.status_code}")
            return []
            
    except requests.Timeout:
        logger.warning("NER service timeout")
        return []
    except requests.ConnectionError:
        logger.warning("NER service unavailable")
        return []
    except Exception as e:
        logger.error(f"NER extraction failed: {e}")
        return []


def extract_facts_from_document(text: str) -> List[Dict[str, str]]:
    """
    Extract facts from longer documents.
    
    Same as extract_facts but for documents - could add 
    document-specific handling in the future.
    """
    return extract_facts(text)


def format_facts_for_storage(facts: List[Dict[str, str]]) -> str:
    """
    Format facts as readable string for storage.
    
    Output: "type: value" on separate lines.
    """
    if not facts:
        return ""
    
    lines = []
    for f in facts:
        lines.append(f"{f['type']}: {f['value']}")
    
    return "\n".join(lines)


def facts_to_embedding_text(facts: List[Dict[str, str]], original_text: str = "") -> str:
    """
    Build text optimized for embedding search.
    
    Combines fact types and values in a searchable format.
    """
    if not facts:
        return ""
    
    parts = []
    for f in facts:
        # Make type readable
        readable_type = f['type'].replace('_', ' ')
        parts.append(f"{readable_type}: {f['value']}")
    
    return " | ".join(parts)
