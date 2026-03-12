"""
Unit tests for the fact extractor module.

Tests the parsing and storage format functions without network calls.
"""

import sys
import os
import pytest

# Add project paths
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "layers", "pragmatics")
)

from services.fact_extractor import (
    _parse_llm_response,
    _empty_result,
    facts_to_storage_format,
)


class TestParseResponse:
    """Tests for _parse_llm_response JSON parsing."""

    def test_basic_facts_array(self):
        """Parse a simple facts array."""
        response = '{"facts": [{"type": "firstName", "value": "Ian", "reason": "User introduced themselves"}]}'
        result = _parse_llm_response(response)

        assert len(result["facts"]) == 1
        assert result["facts"][0]["type"] == "firstName"
        assert result["facts"][0]["value"] == "Ian"
        assert result["facts"][0]["reason"] == "User introduced themselves"

    def test_multiple_facts(self):
        """Parse multiple facts."""
        response = """{"facts": [
            {"type": "firstName", "value": "Ian", "reason": "Name"},
            {"type": "spouse", "value": "Sarah", "reason": "Wife"},
            {"type": "city", "value": "Austin", "reason": "Location"}
        ]}"""
        result = _parse_llm_response(response)

        assert len(result["facts"]) == 3
        types = [f["type"] for f in result["facts"]]
        assert "firstName" in types
        assert "spouse" in types
        assert "city" in types

    def test_empty_facts_array(self):
        """Empty facts array returns empty result."""
        response = '{"facts": []}'
        result = _parse_llm_response(response)

        assert result["facts"] == []

    def test_markdown_code_block_json(self):
        """Extract JSON from markdown code block."""
        response = """```json
{"facts": [{"type": "firstName", "value": "Ian", "reason": "Name"}]}
```"""
        result = _parse_llm_response(response)

        assert len(result["facts"]) == 1
        assert result["facts"][0]["value"] == "Ian"

    def test_markdown_code_block_no_lang(self):
        """Extract JSON from markdown code block without language tag."""
        response = """```
{"facts": [{"type": "city", "value": "Austin", "reason": "Location"}]}
```"""
        result = _parse_llm_response(response)

        assert len(result["facts"]) == 1
        assert result["facts"][0]["value"] == "Austin"

    def test_json_with_surrounding_text(self):
        """Extract JSON when surrounded by explanatory text."""
        response = """Here is the extracted data:
{"facts": [{"type": "occupation", "value": "engineer", "reason": "Job"}]}
I hope this helps!"""
        result = _parse_llm_response(response)

        assert len(result["facts"]) == 1
        assert result["facts"][0]["type"] == "occupation"

    def test_rejects_placeholder_type(self):
        """Placeholder types like 'type' or 'string' are filtered."""
        response = (
            '{"facts": [{"type": "type", "value": "Ian", "reason": "Placeholder"}]}'
        )
        result = _parse_llm_response(response)

        assert result["facts"] == []

    def test_rejects_placeholder_value(self):
        """Placeholder values like 'value' or 'string' are filtered."""
        response = '{"facts": [{"type": "firstName", "value": "string", "reason": "Placeholder"}]}'
        result = _parse_llm_response(response)

        assert result["facts"] == []

    def test_rejects_null_value(self):
        """Null string values are filtered."""
        response = (
            '{"facts": [{"type": "firstName", "value": "null", "reason": "Bad"}]}'
        )
        result = _parse_llm_response(response)

        assert result["facts"] == []

    def test_rejects_empty_type(self):
        """Empty type is filtered."""
        response = '{"facts": [{"type": "", "value": "Ian", "reason": "Bad"}]}'
        result = _parse_llm_response(response)

        assert result["facts"] == []

    def test_rejects_empty_value(self):
        """Empty value is filtered."""
        response = '{"facts": [{"type": "firstName", "value": "", "reason": "Bad"}]}'
        result = _parse_llm_response(response)

        assert result["facts"] == []

    def test_missing_reason_is_empty_string(self):
        """Missing reason becomes empty string."""
        response = '{"facts": [{"type": "firstName", "value": "Ian"}]}'
        result = _parse_llm_response(response)

        assert len(result["facts"]) == 1
        assert result["facts"][0]["reason"] == ""

    def test_invalid_json_returns_empty(self):
        """Invalid JSON returns empty result."""
        response = "This is not JSON at all"
        result = _parse_llm_response(response)

        assert result == {"facts": []}

    def test_facts_not_list_returns_empty(self):
        """If facts is not a list, return empty."""
        response = '{"facts": "not a list"}'
        result = _parse_llm_response(response)

        assert result == {"facts": []}

    def test_fact_not_dict_is_skipped(self):
        """Non-dict items in facts array are skipped."""
        response = '{"facts": ["string item", {"type": "firstName", "value": "Ian", "reason": "Name"}]}'
        result = _parse_llm_response(response)

        assert len(result["facts"]) == 1
        assert result["facts"][0]["value"] == "Ian"

    def test_whitespace_trimmed(self):
        """Whitespace is trimmed from type, value, reason."""
        response = '{"facts": [{"type": "  firstName  ", "value": "  Ian  ", "reason": "  Name  "}]}'
        result = _parse_llm_response(response)

        assert result["facts"][0]["type"] == "firstName"
        assert result["facts"][0]["value"] == "Ian"
        assert result["facts"][0]["reason"] == "Name"


class TestEmptyResult:
    """Tests for _empty_result."""

    def test_returns_empty_facts_list(self):
        """Empty result has empty facts list."""
        result = _empty_result()
        assert result == {"facts": []}


class TestFactsToStorageFormat:
    """Tests for facts_to_storage_format conversion."""

    def test_basic_conversion(self):
        """Basic conversion strips reason field."""
        facts = {
            "facts": [
                {"type": "firstName", "value": "Ian", "reason": "Name"},
                {"type": "spouse", "value": "Sarah", "reason": "Wife"},
            ]
        }
        result = facts_to_storage_format(facts)

        assert len(result) == 2
        assert result[0] == {"type": "firstName", "value": "Ian"}
        assert result[1] == {"type": "spouse", "value": "Sarah"}

    def test_empty_facts(self):
        """Empty facts returns empty list."""
        result = facts_to_storage_format({"facts": []})
        assert result == []

    def test_missing_facts_key(self):
        """Missing facts key returns empty list."""
        result = facts_to_storage_format({})
        assert result == []

    def test_filters_empty_type(self):
        """Facts with empty type are filtered."""
        facts = {
            "facts": [
                {"type": "", "value": "Ian", "reason": "Bad"},
                {"type": "firstName", "value": "Ian", "reason": "Good"},
            ]
        }
        result = facts_to_storage_format(facts)

        assert len(result) == 1
        assert result[0]["type"] == "firstName"

    def test_filters_empty_value(self):
        """Facts with empty value are filtered."""
        facts = {
            "facts": [
                {"type": "firstName", "value": "", "reason": "Bad"},
                {"type": "lastName", "value": "Westerfield", "reason": "Good"},
            ]
        }
        result = facts_to_storage_format(facts)

        assert len(result) == 1
        assert result[0]["type"] == "lastName"

    def test_whitespace_only_filtered(self):
        """Whitespace-only type/value are filtered."""
        facts = {
            "facts": [
                {"type": "  ", "value": "Ian", "reason": "Bad"},
                {"type": "firstName", "value": "   ", "reason": "Bad"},
            ]
        }
        result = facts_to_storage_format(facts)

        assert result == []

    def test_preserves_semantic_types(self):
        """Various semantic types are preserved as-is."""
        facts = {
            "facts": [
                {"type": "prefersDarkMode", "value": "true", "reason": "UI pref"},
                {
                    "type": "terminology",
                    "value": "agents = FunnelCloud Agents",
                    "reason": "Definition",
                },
                {"type": "pet", "value": "Max (dog)", "reason": "Pet name"},
            ]
        }
        result = facts_to_storage_format(facts)

        assert len(result) == 3
        types = [r["type"] for r in result]
        assert "prefersDarkMode" in types
        assert "terminology" in types
        assert "pet" in types
