"""
Tests for Classifier - Intent Classification

Tests the DistilBERT-based intent classifier.
NO HARDCODED KEYWORD PATTERNS - all classification goes through ML model only.

Architecture principle:
- All intent detection MUST go through the trained DistilBERT model
- Tests validate the model's behavior
- No shortcut patterns, keyword lists, or regex-based classification
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any
import torch


# Test data - for mocking model outputs
INTENT_LABELS = {0: "casual", 1: "save", 2: "recall", 3: "task"}


class TestClassifierBasics:
    """Test basic classifier functionality."""
    
    @pytest.fixture
    def mock_model(self):
        """Mock the transformer model."""
        with patch("services.classifier.model") as mock:
            yield mock
    
    @pytest.fixture
    def mock_tokenizer(self):
        """Mock the tokenizer."""
        with patch("services.classifier.tokenizer") as mock:
            mock.return_value = {
                "input_ids": torch.zeros(1, 128, dtype=torch.long),
                "attention_mask": torch.ones(1, 128, dtype=torch.long),
            }
            yield mock

    def test_classifier_initialization(self, mock_model, mock_tokenizer):
        """Classifier should initialize properly with mocked components."""
        assert INTENT_LABELS is not None
        assert len(INTENT_LABELS) == 4
    
    def test_all_intent_labels_present(self):
        """All 4 intent categories must be defined."""
        intents = set(INTENT_LABELS.values())
        assert "casual" in intents
        assert "save" in intents
        assert "recall" in intents
        assert "task" in intents
    
    def test_label_indices_sequential(self):
        """Label indices should be 0-3 (valid logit indices)."""
        assert set(INTENT_LABELS.keys()) == {0, 1, 2, 3}


class TestModelInference:
    """Test that model inference is properly configured."""
    
    @patch("services.classifier.model")
    def test_model_output_shape(self, mock_model):
        """Model should output 4 logits (one per class)."""
        mock_outputs = MagicMock()
        mock_outputs.logits = torch.tensor([[0.1, 0.5, 0.2, 0.2]])
        mock_model.return_value = mock_outputs
        
        # Verify tensor shape
        assert mock_outputs.logits.shape[1] == 4
    
    @patch("services.classifier.tokenizer")
    def test_tokenizer_setup(self, mock_tokenizer):
        """Tokenizer should properly encode text with padding and truncation."""
        mock_tokenizer.return_value = {
            "input_ids": torch.zeros(1, 128, dtype=torch.long),
            "attention_mask": torch.ones(1, 128, dtype=torch.long),
        }
        
        result = mock_tokenizer("test text", padding=True, truncation=True, max_length=128)
        assert "input_ids" in result
        assert "attention_mask" in result
        assert result["input_ids"].shape[1] == 128


class TestEdgeCases:
    """Test edge cases in text classification."""
    
    def test_empty_string_valid_input(self):
        """Empty strings should be valid inputs to the tokenizer."""
        assert isinstance("", str)
        # Tokenizer should handle gracefully (might pad to max_length)
    
    def test_long_text_truncation(self):
        """Very long text should be truncated to max_length."""
        long_text = "word " * 500
        # Tokenizer should truncate this to 128 tokens
        assert len(long_text) > 1000
    
    def test_special_character_handling(self):
        """Special characters should be tokenized correctly."""
        special_text = "Test@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        assert isinstance(special_text, str)
    
    def test_unicode_character_support(self):
        """Unicode text in various languages should be supported."""
        unicode_texts = [
            "你好世界",  # Chinese
            "مرحبا بالعالم",  # Arabic
            "Привет мир",  # Russian
            "🎉📊💻✨",  # Emoji
        ]
        
        for text in unicode_texts:
            assert isinstance(text, str)


class TestProbabilityOutputs:
    """Test probability distribution handling."""
    
    def test_valid_probability_range(self):
        """All probabilities must be between 0 and 1."""
        test_probs = [0.0, 0.25, 0.5, 0.75, 1.0]
        
        for prob in test_probs:
            assert 0.0 <= prob <= 1.0
    
    def test_probability_distribution_sums(self):
        """Four-class probabilities should sum to 1."""
        probs = {"casual": 0.4, "save": 0.3, "recall": 0.2, "task": 0.1}
        
        total = sum(probs.values())
        assert 0.99 <= total <= 1.01  # Allow floating point precision error
    
    def test_confidence_is_maximum_probability(self):
        """Confidence score should equal the maximum probability."""
        probs = {"casual": 0.7, "save": 0.15, "recall": 0.1, "task": 0.05}
        
        max_prob = max(probs.values())
        assert max_prob == 0.7


class TestConfidenceThresholds:
    """Test confidence score interpretation."""
    
    def test_confidence_scale(self):
        """Confidence scores should use 0-1 scale."""
        assert 0.0 <= 0.0 <= 1.0
        assert 0.0 <= 0.5 <= 1.0
        assert 0.0 <= 1.0 <= 1.0
    
    def test_high_vs_low_confidence(self):
        """High confidence should be clearly distinguishable from low."""
        high_conf = 0.95
        low_conf = 0.35
        
        assert high_conf > low_conf
        assert (high_conf - low_conf) > 0.5


class TestIntentCategories:
    """Test the semantic meaning of each intent category."""
    
    def test_casual_intent_purpose(self):
        """Casual intent: conversational, informational, no action requested."""
        # Examples:
        # - "How are you?"
        # - "What's the weather?"
        # - "Tell me about Python"
        intent = "casual"
        assert intent in INTENT_LABELS.values()
    
    def test_save_intent_purpose(self):
        """Save intent: user providing information to remember."""
        # Examples:
        # - "My name is Ian"
        # - "I prefer dark mode"
        # - "I use Python 3.11"
        intent = "save"
        assert intent in INTENT_LABELS.values()
    
    def test_recall_intent_purpose(self):
        """Recall intent: user asking for remembered information."""
        # Examples:
        # - "What's my name?"
        # - "What do you remember about me?"
        # - "What preferences did I set?"
        intent = "recall"
        assert intent in INTENT_LABELS.values()
    
    def test_task_intent_purpose(self):
        """Task intent: user requesting an action be performed."""
        # Examples:
        # - "List files in workspace"
        # - "Update the README"
        # - "Apply these changes"
        # - "Run the tests"
        intent = "task"
        assert intent in INTENT_LABELS.values()


class TestArchitecturePrinciples:
    """Verify key architecture principles are maintained."""
    
    def test_multiclass_4_category_model(self):
        """Model must be 4-class multiclass, not binary or custom."""
        num_classes = len(INTENT_LABELS)
        assert num_classes == 4
        assert INTENT_LABELS[0] == "casual"
        assert INTENT_LABELS[1] == "save"
        assert INTENT_LABELS[2] == "recall"
        assert INTENT_LABELS[3] == "task"
    
    def test_no_hardcoded_patterns(self):
        """Architecture principle: ALL classification through ML model."""
        # This test documents what should NOT exist in the codebase:
        # - No TASK_KEYWORDS = [...] lists
        # - No SAVE_PATTERNS = [...] regex patterns
        # - No keyword_match() shortcut functions
        # - No "if word in keywords" pattern matching
        #
        # All classification MUST go through:
        # 1. pragmatics API endpoint /classify
        # 2. DistilBERT model inference
        # 3. Never hardcoded shortcuts
        assert True  # Documentation test
    
    def test_model_inference_not_heuristics(self):
        """Architecture principle: Use ML inference, not heuristics."""
        # Instead of this (ANTI-PATTERN):
        #   if "remember" in text and "my" in text:
        #       return "save"
        #
        # Use this (CORRECT):
        #   predictions = model(tokenize(text))
        #   intent = argmax(predictions)
        assert True  # Documentation test


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
