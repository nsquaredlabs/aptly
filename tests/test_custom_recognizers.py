"""
Tests for custom PII recognizers.

These tests verify that framework-specific custom recognizers correctly identify
sensitive information patterns for HIPAA, FinTech, GDPR, and SOC2 compliance.
"""

import pytest
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

from src.compliance.custom_recognizers import get_custom_recognizers


@pytest.fixture
def analyzer():
    """Create an analyzer with custom recognizers loaded."""
    nlp_config = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
    }
    nlp_engine = NlpEngineProvider(nlp_configuration=nlp_config).create_engine()
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine)

    # Add custom recognizers
    for recognizer in get_custom_recognizers():
        analyzer.registry.add_recognizer(recognizer)

    return analyzer


# ========== HIPAA Recognizers ==========


def test_medical_record_number_detection(analyzer):
    """MRN patterns should be detected."""
    test_cases = [
        "Patient MRN: A1234567 has diabetes",
        "Medical Record Number is MR#987654321",
        "MRN ABC12345 needs follow-up",
    ]

    for text in test_cases:
        results = analyzer.analyze(
            text=text, entities=["MEDICAL_RECORD_NUMBER"], language="en"
        )
        assert len(results) > 0, f"Failed to detect MRN in: {text}"
        assert results[0].entity_type == "MEDICAL_RECORD_NUMBER"


def test_medical_record_number_no_false_positives(analyzer):
    """MRN should not match random numbers."""
    test_cases = [
        "The number 123456 is not an MRN",
        "ABC without context should not match",
        "Random text without medical context",
    ]

    for text in test_cases:
        results = analyzer.analyze(
            text=text, entities=["MEDICAL_RECORD_NUMBER"], language="en"
        )
        assert len(results) == 0, f"False positive MRN in: {text}"


def test_health_plan_number_detection(analyzer):
    """Health plan numbers should be detected."""
    test_cases = [
        "Plan ID: 123456789 for patient",
        "Member ID 987654321 is active",
        "Plan ID ABC123456789 on file",
    ]

    for text in test_cases:
        results = analyzer.analyze(
            text=text, entities=["HEALTH_PLAN_NUMBER"], language="en"
        )
        assert len(results) > 0, f"Failed to detect health plan number in: {text}"
        assert results[0].entity_type == "HEALTH_PLAN_NUMBER"


def test_device_serial_number_detection(analyzer):
    """Device serial numbers should be detected."""
    test_cases = [
        "Device ID: ABC123DEF456 implanted",
        "S/N XYZ78901234 is the serial",
        "Serial: 1234567890AB for the device",
    ]

    for text in test_cases:
        results = analyzer.analyze(
            text=text, entities=["DEVICE_SERIAL_NUMBER"], language="en"
        )
        assert len(results) > 0, f"Failed to detect device serial in: {text}"
        assert results[0].entity_type == "DEVICE_SERIAL_NUMBER"


# ========== FinTech Recognizers ==========


def test_cvv_detection(analyzer):
    """CVV codes should be detected."""
    test_cases = [
        "My CVV: 123 for verification",
        "CVC 4567 on the card",
        "Security Code: 789 on back",
    ]

    for text in test_cases:
        results = analyzer.analyze(text=text, entities=["CVV"], language="en")
        assert len(results) > 0, f"Failed to detect CVV in: {text}"
        assert results[0].entity_type == "CVV"


def test_cvv_no_false_positives(analyzer):
    """CVV should not match random 3-4 digit numbers without context."""
    test_cases = [
        "The year 1234 was important",
        "There are 567 items",
        "Random number 890",
    ]

    for text in test_cases:
        results = analyzer.analyze(text=text, entities=["CVV"], language="en")
        # Should not detect CVV without card-related context
        assert len(results) == 0, f"False positive CVV in: {text}"


def test_routing_number_detection(analyzer):
    """Routing numbers should be detected."""
    test_cases = [
        "Routing: 021000021 for transfer",
        "ABA: 111000025 number",
        "RTN: 123456789 required",
    ]

    for text in test_cases:
        results = analyzer.analyze(
            text=text, entities=["ROUTING_NUMBER"], language="en"
        )
        assert len(results) > 0, f"Failed to detect routing number in: {text}"
        assert results[0].entity_type == "ROUTING_NUMBER"


def test_account_number_detection(analyzer):
    """Account numbers should be detected."""
    test_cases = [
        "Account: 12345678901 is active",
        "Acct# 9876543210 for deposit",
        "A/C: 11223344556677 on file",
    ]

    for text in test_cases:
        results = analyzer.analyze(
            text=text, entities=["ACCOUNT_NUMBER"], language="en"
        )
        assert len(results) > 0, f"Failed to detect account number in: {text}"
        assert results[0].entity_type == "ACCOUNT_NUMBER"


# ========== GDPR Recognizers ==========


def test_eu_vat_number_detection(analyzer):
    """EU VAT numbers should be detected."""
    test_cases = [
        "VAT: DE123456789 registered",
        "Company VAT Number FR12345678901",
        "GB123456789 is the VAT ID",
    ]

    for text in test_cases:
        results = analyzer.analyze(text=text, entities=["EU_VAT_NUMBER"], language="en")
        assert len(results) > 0, f"Failed to detect VAT number in: {text}"
        assert results[0].entity_type == "EU_VAT_NUMBER"


def test_eu_national_id_detection(analyzer):
    """EU national IDs should be detected."""
    test_cases = [
        "National ID: ABC12345678 verified",
        "ID Number XYZ987654321 on file",
    ]

    for text in test_cases:
        results = analyzer.analyze(text=text, entities=["EU_NATIONAL_ID"], language="en")
        assert len(results) > 0, f"Failed to detect EU national ID in: {text}"
        assert results[0].entity_type == "EU_NATIONAL_ID"


def test_eu_passport_detection(analyzer):
    """EU passport numbers should be detected."""
    test_cases = [
        "Passport: ABC123456 expires soon",
        "Passport Number XYZ789012 verified",
    ]

    for text in test_cases:
        results = analyzer.analyze(text=text, entities=["EU_PASSPORT"], language="en")
        assert len(results) > 0, f"Failed to detect passport in: {text}"
        assert results[0].entity_type == "EU_PASSPORT"


# ========== SOC2 Recognizers ==========


def test_api_key_openai_detection(analyzer):
    """OpenAI API keys should be detected."""
    test_cases = [
        "My key is sk-proj-" + "a" * 48,
        "Use sk-" + "b" * 48 + " for API",
    ]

    for text in test_cases:
        results = analyzer.analyze(text=text, entities=["API_KEY"], language="en")
        assert len(results) > 0, f"Failed to detect OpenAI key in: {text}"
        assert results[0].entity_type == "API_KEY"


def test_api_key_google_detection(analyzer):
    """Google API keys should be detected."""
    text = "Use AIza" + "a" * 35 + " for Google API"
    results = analyzer.analyze(text=text, entities=["API_KEY"], language="en")

    assert len(results) > 0
    assert results[0].entity_type == "API_KEY"


def test_aws_key_detection(analyzer):
    """AWS access keys should be detected."""
    test_cases = [
        "AWS key: AKIAIOSFODNN7EXAMPLE",
        "Access key AKIATESTTESTTEST1234 is active",
    ]

    for text in test_cases:
        results = analyzer.analyze(text=text, entities=["AWS_KEY"], language="en")
        assert len(results) > 0, f"Failed to detect AWS key in: {text}"
        assert results[0].entity_type == "AWS_KEY"


def test_github_token_detection(analyzer):
    """GitHub tokens should be detected."""
    test_cases = [
        "Token: ghp_" + "a" * 36,
        "OAuth token gho_" + "b" * 36,
        "App token ghs_" + "c" * 36,
    ]

    for text in test_cases:
        results = analyzer.analyze(text=text, entities=["GITHUB_TOKEN"], language="en")
        assert len(results) > 0, f"Failed to detect GitHub token in: {text}"
        assert results[0].entity_type == "GITHUB_TOKEN"


def test_jwt_token_detection(analyzer):
    """JWT tokens should be detected."""
    # Simplified JWT format
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    results = analyzer.analyze(text=f"Bearer {jwt}", entities=["JWT_TOKEN"], language="en")

    assert len(results) > 0
    assert results[0].entity_type == "JWT_TOKEN"


def test_private_key_detection(analyzer):
    """Private keys should be detected."""
    test_cases = [
        "-----BEGIN RSA PRIVATE KEY-----",
        "-----BEGIN PRIVATE KEY-----",
        "-----BEGIN OPENSSH PRIVATE KEY-----",
        "-----BEGIN PGP PRIVATE KEY BLOCK-----",
    ]

    for text in test_cases:
        results = analyzer.analyze(text=text, entities=["PRIVATE_KEY"], language="en")
        assert len(results) > 0, f"Failed to detect private key in: {text}"
        assert results[0].entity_type == "PRIVATE_KEY"


# ========== Confidence Scores ==========


def test_recognizer_confidence_scores(analyzer):
    """High-confidence patterns should have appropriate scores."""
    # AWS keys should have very high confidence (0.99)
    results = analyzer.analyze(
        text="AKIAIOSFODNN7EXAMPLE", entities=["AWS_KEY"], language="en"
    )
    assert len(results) > 0
    assert results[0].score >= 0.95

    # MRN with context should have good confidence
    results = analyzer.analyze(
        text="Patient MRN: A1234567", entities=["MEDICAL_RECORD_NUMBER"], language="en"
    )
    assert len(results) > 0
    assert results[0].score >= 0.80


# ========== Edge Cases ==========


def test_multiple_entities_in_text(analyzer):
    """Should detect multiple different entity types in same text."""
    text = """
    Patient MRN: A1234567 has Account: 12345678901.
    CVV: 123 for payment.
    API key: sk-proj-""" + "a" * 48

    results = analyzer.analyze(
        text=text,
        entities=["MEDICAL_RECORD_NUMBER", "ACCOUNT_NUMBER", "CVV", "API_KEY"],
        language="en",
    )

    # Should detect multiple entity types
    entity_types = {r.entity_type for r in results}
    assert "MEDICAL_RECORD_NUMBER" in entity_types
    assert "CVV" in entity_types
    assert "API_KEY" in entity_types


def test_custom_recognizers_loaded():
    """Verify all custom recognizers are returned."""
    recognizers = get_custom_recognizers()

    # Should return multiple recognizers (at least 10)
    assert len(recognizers) >= 10

    # Each should be a recognizer instance
    from presidio_analyzer import PatternRecognizer

    for rec in recognizers:
        assert isinstance(rec, PatternRecognizer)

    # Verify key entity types are present
    entity_types = {rec.supported_entities[0] for rec in recognizers}
    expected_types = {
        "MEDICAL_RECORD_NUMBER",
        "CVV",
        "ROUTING_NUMBER",
        "API_KEY",
        "AWS_KEY",
        "GITHUB_TOKEN",
        "JWT_TOKEN",
        "PRIVATE_KEY",
        "EU_VAT_NUMBER",
    }

    for expected in expected_types:
        assert expected in entity_types, f"{expected} recognizer not found"
