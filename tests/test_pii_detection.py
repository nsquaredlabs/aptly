"""Tests for PII detection and redaction."""

import pytest
from unittest.mock import MagicMock, patch


class MockRecognizerResult:
    """Mock Presidio recognizer result."""

    def __init__(self, entity_type: str, start: int, end: int, score: float = 0.9):
        self.entity_type = entity_type
        self.start = start
        self.end = end
        self.score = score


@pytest.fixture
def mock_analyzer():
    """Create a mock Presidio analyzer."""
    with patch("src.compliance.pii_redactor.AnalyzerEngine") as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield instance


def test_pii_redactor_mask_mode(mock_analyzer):
    """Test mask redaction mode: 'John Smith' → 'PERSON_A'."""
    # Set up mock to detect a person name
    mock_analyzer.analyze.return_value = [
        MockRecognizerResult("PERSON", start=8, end=18, score=0.95)
    ]

    from src.compliance.pii_redactor import PIIRedactor

    redactor = PIIRedactor(mode="mask")
    result = redactor.redact("Patient John Smith has diabetes.")

    assert result.pii_detected is True
    assert "PERSON_A" in result.redacted_text
    assert "John Smith" not in result.redacted_text
    assert len(result.detections) == 1
    assert result.detections[0].type == "PERSON"
    assert result.detections[0].replacement == "PERSON_A"


def test_pii_redactor_hash_mode(mock_analyzer):
    """Test hash redaction mode: 'John Smith' → 'HASH_a3f2c1b9'."""
    mock_analyzer.analyze.return_value = [
        MockRecognizerResult("PERSON", start=0, end=10, score=0.95)
    ]

    from src.compliance.pii_redactor import PIIRedactor

    redactor = PIIRedactor(mode="hash")
    result = redactor.redact("John Smith went to the store.")

    assert result.pii_detected is True
    assert result.redacted_text.startswith("HASH_")
    assert "John Smith" not in result.redacted_text
    assert result.detections[0].replacement.startswith("HASH_")


def test_pii_redactor_remove_mode(mock_analyzer):
    """Test remove redaction mode: 'John Smith' → '[REDACTED]'."""
    mock_analyzer.analyze.return_value = [
        MockRecognizerResult("PERSON", start=0, end=10, score=0.95)
    ]

    from src.compliance.pii_redactor import PIIRedactor

    redactor = PIIRedactor(mode="remove")
    result = redactor.redact("John Smith went to the store.")

    assert result.pii_detected is True
    assert "[REDACTED]" in result.redacted_text
    assert "John Smith" not in result.redacted_text


def test_pii_redactor_no_pii(mock_analyzer):
    """Test when no PII is detected."""
    mock_analyzer.analyze.return_value = []

    from src.compliance.pii_redactor import PIIRedactor

    redactor = PIIRedactor(mode="mask")
    result = redactor.redact("The weather is nice today.")

    assert result.pii_detected is False
    assert result.redacted_text == "The weather is nice today."
    assert len(result.detections) == 0


def test_pii_redactor_multiple_entities(mock_analyzer):
    """Test detection of multiple PII entities."""
    mock_analyzer.analyze.return_value = [
        MockRecognizerResult("PERSON", start=0, end=10, score=0.95),
        MockRecognizerResult("EMAIL_ADDRESS", start=24, end=44, score=0.99),
    ]

    from src.compliance.pii_redactor import PIIRedactor

    redactor = PIIRedactor(mode="mask")
    result = redactor.redact("John Smith's email is john.smith@email.com today.")

    assert result.pii_detected is True
    assert len(result.detections) == 2
    assert "PERSON_A" in result.redacted_text
    assert "EMAIL_ADDRESS_A" in result.redacted_text


def test_pii_redactor_same_type_multiple_times(mock_analyzer):
    """Test multiple entities of same type get sequential labels."""
    mock_analyzer.analyze.return_value = [
        MockRecognizerResult("PERSON", start=0, end=10, score=0.95),
        MockRecognizerResult("PERSON", start=15, end=25, score=0.90),
    ]

    from src.compliance.pii_redactor import PIIRedactor

    redactor = PIIRedactor(mode="mask")
    result = redactor.redact("John Smith and Jane Smith went out.")

    assert "PERSON_A" in result.redacted_text
    assert "PERSON_B" in result.redacted_text


def test_pii_redactor_empty_text(mock_analyzer):
    """Test handling of empty text."""
    from src.compliance.pii_redactor import PIIRedactor

    redactor = PIIRedactor(mode="mask")
    result = redactor.redact("")

    assert result.pii_detected is False
    assert result.redacted_text == ""
    assert len(result.detections) == 0


def test_pii_redactor_whitespace_only(mock_analyzer):
    """Test handling of whitespace-only text."""
    from src.compliance.pii_redactor import PIIRedactor

    redactor = PIIRedactor(mode="mask")
    result = redactor.redact("   ")

    assert result.pii_detected is False


def test_redact_messages_single_message(mock_analyzer):
    """Test redacting a single message."""
    mock_analyzer.analyze.return_value = [
        MockRecognizerResult("PERSON", start=8, end=18, score=0.95)
    ]

    from src.compliance.pii_redactor import PIIRedactor

    redactor = PIIRedactor(mode="mask")
    messages = [{"role": "user", "content": "Patient John Smith has diabetes."}]

    redacted, detections = redactor.redact_messages(messages)

    assert len(redacted) == 1
    assert "PERSON_A" in redacted[0]["content"]
    assert len(detections) == 1


def test_redact_messages_multiple_messages(mock_analyzer):
    """Test redacting multiple messages."""
    # First call returns person, second returns email
    mock_analyzer.analyze.side_effect = [
        [MockRecognizerResult("PERSON", start=0, end=10, score=0.95)],
        [MockRecognizerResult("EMAIL_ADDRESS", start=11, end=31, score=0.99)],
    ]

    from src.compliance.pii_redactor import PIIRedactor

    redactor = PIIRedactor(mode="mask")
    messages = [
        {"role": "user", "content": "John Smith is a patient."},
        {"role": "assistant", "content": "Contact at john.smith@email.com please."},
    ]

    redacted, detections = redactor.redact_messages(messages)

    assert len(redacted) == 2
    assert len(detections) == 2


def test_redact_messages_preserves_role(mock_analyzer):
    """Test that message role is preserved after redaction."""
    mock_analyzer.analyze.return_value = []

    from src.compliance.pii_redactor import PIIRedactor

    redactor = PIIRedactor(mode="mask")
    messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]

    redacted, _ = redactor.redact_messages(messages)

    assert redacted[0]["role"] == "system"
    assert redacted[1]["role"] == "user"
    assert redacted[2]["role"] == "assistant"


def test_pii_detection_confidence(mock_analyzer):
    """Test that confidence scores are preserved."""
    mock_analyzer.analyze.return_value = [
        MockRecognizerResult("PERSON", start=0, end=10, score=0.85)
    ]

    from src.compliance.pii_redactor import PIIRedactor

    redactor = PIIRedactor(mode="mask")
    result = redactor.redact("John Smith")

    assert result.detections[0].confidence == 0.85


def test_supported_entity_types():
    """Verify all expected entity types are supported."""
    from src.compliance.pii_redactor import SUPPORTED_ENTITIES

    expected_types = [
        "PERSON",
        "EMAIL_ADDRESS",
        "PHONE_NUMBER",
        "US_SSN",
        "CREDIT_CARD",
        "LOCATION",
    ]

    for entity_type in expected_types:
        assert entity_type in SUPPORTED_ENTITIES


def test_unredact_mask_mode(mock_analyzer):
    """Unredact restores original PII values in mask mode."""
    mock_analyzer.analyze.return_value = [
        MockRecognizerResult("PERSON", start=8, end=18, score=0.95)
    ]

    from src.compliance.pii_redactor import PIIRedactor

    redactor = PIIRedactor(mode="mask")
    result = redactor.redact("Patient John Smith has diabetes.")

    assert "PERSON_A" in result.redacted_text
    assert "John Smith" not in result.redacted_text

    restored = redactor.unredact(result.redacted_text, result.detections)
    assert restored == "Patient John Smith has diabetes."


def test_unredact_hash_mode(mock_analyzer):
    """Unredact restores original PII values in hash mode."""
    mock_analyzer.analyze.return_value = [
        MockRecognizerResult("PERSON", start=0, end=10, score=0.95)
    ]

    from src.compliance.pii_redactor import PIIRedactor

    redactor = PIIRedactor(mode="hash")
    result = redactor.redact("John Smith went to the store.")

    assert "John Smith" not in result.redacted_text
    assert result.redacted_text.startswith("HASH_")

    restored = redactor.unredact(result.redacted_text, result.detections)
    assert restored == "John Smith went to the store."


def test_unredact_remove_mode_noop(mock_analyzer):
    """Unredact in remove mode returns text unchanged (cannot reverse [REDACTED])."""
    mock_analyzer.analyze.return_value = [
        MockRecognizerResult("PERSON", start=0, end=10, score=0.95)
    ]

    from src.compliance.pii_redactor import PIIRedactor

    redactor = PIIRedactor(mode="remove")
    result = redactor.redact("John Smith went to the store.")

    assert "[REDACTED]" in result.redacted_text

    restored = redactor.unredact(result.redacted_text, result.detections)
    assert restored == result.redacted_text
    assert "[REDACTED]" in restored


def test_unredact_no_placeholders(mock_analyzer):
    """Unredact returns text unchanged when there are no placeholders."""
    mock_analyzer.analyze.return_value = [
        MockRecognizerResult("PERSON", start=0, end=10, score=0.95)
    ]

    from src.compliance.pii_redactor import PIIRedactor

    redactor = PIIRedactor(mode="mask")
    result = redactor.redact("John Smith went to the store.")

    # Apply unredact to text that has no placeholders
    clean_text = "The weather is nice today."
    restored = redactor.unredact(clean_text, result.detections)
    assert restored == "The weather is nice today."
