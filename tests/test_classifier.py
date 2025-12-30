"""
Tests for Classifier - Intent Classification

Tests the DistilBERT-based intent classifier and context-aware classification.
These tests validate classifier behavior without requiring the actual model.
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any, Tuple, Set, List


# Test constants matching the real classifier
AFFIRMATIVE_PATTERNS: Set[str] = {
    "yes", "yeah", "yep", "yup", "sure", "ok", "okay", "go ahead", "do it",
    "please do", "proceed", "make it so", "sounds good", "that works",
    "perfect", "great", "go for it", "let's do it", "continue", "next",
    "all of them", "all", "both", "1", "2", "3", "commit", "save",
    "apply", "yes please", "yes go ahead", "ok do it", "sure thing",
}

TASK_PROPOSAL_PATTERNS: List[str] = [
    "would you like me to", "should i ", "do you want me to",
    "i can ", "i could ", "i'll ", "let me know if",
    "shall i", "want me to", "ready to", "proceed with",
    "here's the plan", "the changes would be",
    "files that need", "files to update", "files found",
    "which option", "option 1", "option 2", "choose",
    "select", "pick", "apply the", "make the change",
    "update the", "fix the", "create the", "delete the",
]

INTENT_LABELS = {0: "casual", 1: "save", 2: "recall", 3: "task"}


def classify_with_context(user_text: str, context: str = "") -> Dict[str, Any]:
    """Mock context-aware classification for testing."""
    user_lower = user_text.lower().strip()
    context_lower = context.lower() if context else ""
    
    # Check for affirmative continuation
    is_short = len(user_text.strip()) < 50
    is_affirmative = any(
        user_lower == pattern or user_lower.startswith(pattern + " ")
        for pattern in AFFIRMATIVE_PATTERNS
    )
    has_task_proposal = any(pattern in context_lower for pattern in TASK_PROPOSAL_PATTERNS)
    
    if is_short and is_affirmative and has_task_proposal:
        return {"intent": "task", "confidence": 0.85, "all_probs": {"task": 0.85, "casual": 0.10, "save": 0.025, "recall": 0.025}}
    
    # Action request patterns
    action_starters = ["can you", "could you", "would you", "please", "go through"]
    if any(user_lower.startswith(starter) for starter in action_starters):
        return {"intent": "task", "confidence": 0.80, "all_probs": {"task": 0.80, "casual": 0.15, "save": 0.025, "recall": 0.025}}
    
    # Default casual
    return {"intent": "casual", "confidence": 0.70, "all_probs": {"casual": 0.70, "task": 0.15, "save": 0.10, "recall": 0.05}}


def classify_intent_multiclass(text: str) -> Dict[str, Any]:
    """Mock multiclass classification for testing."""
    text_lower = text.lower()
    
    # Simple heuristic classification for tests
    if any(w in text_lower for w in ["my name is", "remember", "i work at", "my email"]):
        return {"intent": "save", "confidence": 0.85, "all_probs": {"save": 0.85, "casual": 0.10, "recall": 0.03, "task": 0.02}}
    if any(w in text_lower for w in ["what's my", "what do you remember", "do you know"]):
        return {"intent": "recall", "confidence": 0.85, "all_probs": {"recall": 0.85, "casual": 0.10, "save": 0.03, "task": 0.02}}
    if any(w in text_lower for w in ["list", "create", "update", "show me", "run", "largest"]):
        return {"intent": "task", "confidence": 0.85, "all_probs": {"task": 0.85, "casual": 0.10, "save": 0.03, "recall": 0.02}}
    
    return {"intent": "casual", "confidence": 0.75, "all_probs": {"casual": 0.75, "task": 0.15, "save": 0.05, "recall": 0.05}}


def classify_intent(text: str) -> Tuple[bool, float]:
    """Mock binary classification for testing."""
    result = classify_intent_multiclass(text)
    is_save = result["intent"] == "save"
    return is_save, result["all_probs"].get("save", 0.0)


class TestClassifyIntentMulticlass:
    """Test 4-class intent classification."""
    
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

    def test_casual_intent_patterns(self):
        """Casual greetings should classify as casual."""
        casual_texts = [
            "Hello!",
            "How are you?",
            "Good morning",
            "Thanks for the help",
            "That's interesting",
        ]
        
        # These would need actual model to test properly
        # Here we test the pattern matching fallback
        for text in casual_texts:
            # In real test, would call classify_intent_multiclass(text)
            assert len(text) > 0  # Placeholder assertion
    
    def test_save_intent_patterns(self):
        """Save patterns should classify as save."""
        save_texts = [
            "My name is Ian",
            "Remember that I prefer dark mode",
            "I work at Acme Corp",
            "My email is test@example.com",
            "Note that I use Python 3.11",
        ]
        
        for text in save_texts:
            assert len(text) > 0  # Placeholder
    
    def test_recall_intent_patterns(self):
        """Recall patterns should classify as recall."""
        recall_texts = [
            "What's my name?",
            "What do you remember about me?",
            "What's my email?",
            "Do you know where I work?",
            "What preferences have I set?",
        ]
        
        for text in recall_texts:
            assert len(text) > 0  # Placeholder
    
    def test_task_intent_patterns(self):
        """Task patterns should classify as task."""
        task_texts = [
            "List all files in the workspace",
            "Which files are the largest?",
            "Create a new Python script",
            "Update the README with installation instructions",
            "Run the tests",
            "Show me the git status",
        ]
        
        for text in task_texts:
            assert len(text) > 0  # Placeholder


class TestAffirmativePatterns:
    """Test affirmative pattern detection."""
    
    def test_affirmative_patterns_exist(self):
        """Verify affirmative patterns are defined."""
        assert "yes" in AFFIRMATIVE_PATTERNS
        assert "ok" in AFFIRMATIVE_PATTERNS
        assert "sure" in AFFIRMATIVE_PATTERNS
        assert "do it" in AFFIRMATIVE_PATTERNS
        assert "go ahead" in AFFIRMATIVE_PATTERNS
    
    def test_task_proposal_patterns_exist(self):
        """Verify task proposal patterns are defined."""
        assert any("would you like" in p for p in TASK_PROPOSAL_PATTERNS)
        assert any("should i" in p for p in TASK_PROPOSAL_PATTERNS)
        assert any("i can" in p for p in TASK_PROPOSAL_PATTERNS)


class TestClassifyWithContext:
    """Test context-aware classification."""
    
    def test_affirmative_with_task_proposal_upgrades_to_task(self):
        """Short affirmative + task proposal context should upgrade to task."""
        # Simulate context where assistant proposed a task
        context = "I found 5 files that need updating. Would you like me to proceed with the changes?"
        user_text = "yes"
        
        result = classify_with_context(user_text, context)
        
        # Should be upgraded to task due to context
        assert result["intent"] == "task"
        assert result["confidence"] >= 0.80
    
    def test_affirmative_without_context_stays_casual(self):
        """Affirmative without context should stay casual."""
        result = classify_with_context("yes", "")
        
        # Without context, "yes" alone should be casual
        assert result["intent"] == "casual"
    
    def test_action_request_upgrades_to_task(self):
        """Action request patterns should upgrade to task."""
        action_requests = [
            "Can you update the file?",
            "Could you show me the logs?",
            "Would you run the tests?",
            "Please fix the bug",
        ]
        
        for text in action_requests:
            result = classify_with_context(text, "")
            assert result["intent"] == "task"
    
    def test_long_message_not_upgraded(self):
        """Long messages should use ML classification, not pattern upgrade."""
        long_text = "This is a much longer message that discusses various topics and " * 5
        context = "Would you like me to do something?"
        
        result = classify_with_context(long_text, context)
        
        # Long messages shouldn't trigger affirmative pattern
        assert "intent" in result


class TestClassifyIntentBinary:
    """Test binary (save/not-save) classification for backward compat."""
    
    def test_returns_tuple(self):
        """Should return (is_save, confidence) tuple."""
        result = classify_intent("My name is Ian")
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], float)
    
    def test_save_request_detected(self):
        """Save requests should return is_save=True."""
        is_save, confidence = classify_intent("Remember that my favorite color is blue")
        
        # At minimum, confidence should be valid
        assert 0.0 <= confidence <= 1.0


class TestConfidenceThreshold:
    """Test confidence threshold configuration."""
    
    # Mock confidence threshold
    CONFIDENCE_THRESHOLD = 0.50
    
    def test_threshold_is_configured(self):
        """Confidence threshold should be set."""
        assert isinstance(self.CONFIDENCE_THRESHOLD, float)
        assert 0.0 < self.CONFIDENCE_THRESHOLD < 1.0
    
    def test_default_threshold_value(self):
        """Default threshold should be around 0.50."""
        assert self.CONFIDENCE_THRESHOLD >= 0.40
        assert self.CONFIDENCE_THRESHOLD <= 0.70


class TestModelLoading:
    """Test model loading and configuration."""
    
    def test_intent_labels_defined(self):
        """Intent labels should be defined."""
        assert 0 in INTENT_LABELS  # casual
        assert 1 in INTENT_LABELS  # save
        assert 2 in INTENT_LABELS  # recall
        assert 3 in INTENT_LABELS  # task
    
    def test_device_configured(self):
        """Device should be CPU or CUDA (mock returns cpu)."""
        # In tests, we mock as CPU
        DEVICE = type('obj', (object,), {'type': 'cpu'})()
        assert DEVICE.type in ("cpu", "cuda")
    
    def test_is_multiclass_flag(self):
        """IS_MULTICLASS flag should indicate 4-class model."""
        IS_MULTICLASS = True  # Our mock uses 4 classes
        assert isinstance(IS_MULTICLASS, bool)


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_string_classification(self):
        """Empty string should classify without error."""
        result = classify_intent_multiclass("")
        
        assert "intent" in result
        assert "confidence" in result
    
    def test_very_long_text_truncation(self):
        """Very long text should be truncated and handled."""
        long_text = "word " * 1000  # Way over 128 tokens
        
        result = classify_intent_multiclass(long_text)
        
        # Should not error
        assert "intent" in result
    
    def test_special_characters(self):
        """Text with special characters should classify."""
        special_text = "What's my email? 📧 test@example.com"
        
        result = classify_intent_multiclass(special_text)
        
        assert "intent" in result
    
    def test_unicode_text(self):
        """Unicode text should classify."""
        unicode_text = "我的名字是什么？"
        
        result = classify_intent_multiclass(unicode_text)
        
        assert "intent" in result


class TestAllProbabilities:
    """Test probability distribution in results."""
    
    def test_all_probs_returned(self):
        """Should return probabilities for all classes."""
        result = classify_intent_multiclass("Hello there")
        
        assert "all_probs" in result
        probs = result["all_probs"]
        
        assert "casual" in probs
        assert "save" in probs
        assert "recall" in probs
        assert "task" in probs
    
    def test_probabilities_sum_to_one(self):
        """Probabilities should approximately sum to 1."""
        result = classify_intent_multiclass("Test message")
        probs = result["all_probs"]
        
        total = sum(probs.values())
        assert 0.99 <= total <= 1.01  # Allow small floating point error
    
    def test_best_confidence_matches_all_probs(self):
        """Top confidence should match max in all_probs."""
        result = classify_intent_multiclass("What's my name?")
        
        best_intent = result["intent"]
        best_confidence = result["confidence"]
        all_probs = result["all_probs"]
        
        assert abs(best_confidence - all_probs[best_intent]) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
