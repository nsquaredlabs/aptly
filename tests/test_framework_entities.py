"""
Tests for framework-specific entity selection.
"""

import pytest
from src.compliance.framework_entities import (
    get_entities_for_frameworks,
    BASELINE_ENTITIES,
    HIPAA_ADDITIONAL_ENTITIES,
    FINTECH_ADDITIONAL_ENTITIES,
    GDPR_ADDITIONAL_ENTITIES,
    SOC2_ADDITIONAL_ENTITIES,
)


def test_get_entities_for_frameworks_none():
    """When frameworks is None, should return baseline entities."""
    entities = get_entities_for_frameworks(None)

    assert len(entities) == len(BASELINE_ENTITIES)
    assert set(entities) == set(BASELINE_ENTITIES)
    assert entities == sorted(BASELINE_ENTITIES)  # Should be sorted


def test_get_entities_for_frameworks_empty_list():
    """When frameworks is empty list, should return baseline entities."""
    entities = get_entities_for_frameworks([])

    assert len(entities) == len(BASELINE_ENTITIES)
    assert set(entities) == set(BASELINE_ENTITIES)


def test_get_entities_for_frameworks_hipaa():
    """HIPAA framework should include baseline + HIPAA-specific entities."""
    entities = get_entities_for_frameworks(["HIPAA"])

    expected = set(BASELINE_ENTITIES + HIPAA_ADDITIONAL_ENTITIES)
    assert set(entities) == expected
    assert entities == sorted(list(expected))  # Should be sorted

    # Verify HIPAA-specific entities are included
    assert "MEDICAL_RECORD_NUMBER" in entities
    assert "HEALTH_PLAN_NUMBER" in entities
    assert "DEVICE_SERIAL_NUMBER" in entities
    assert "UK_NHS" in entities
    assert "US_DRIVER_LICENSE" in entities

    # Verify baseline entities are still included
    assert "PERSON" in entities
    assert "EMAIL_ADDRESS" in entities


def test_get_entities_for_frameworks_fintech():
    """FinTech framework should include baseline + FinTech-specific entities."""
    entities = get_entities_for_frameworks(["FinTech"])

    expected = set(BASELINE_ENTITIES + FINTECH_ADDITIONAL_ENTITIES)
    assert set(entities) == expected

    # Verify FinTech-specific entities are included
    assert "CVV" in entities
    assert "ROUTING_NUMBER" in entities
    assert "ACCOUNT_NUMBER" in entities
    assert "US_BANK_NUMBER" in entities
    assert "CRYPTO" in entities
    assert "US_ITIN" in entities

    # Verify baseline entities are still included
    assert "CREDIT_CARD" in entities


def test_get_entities_for_frameworks_gdpr():
    """GDPR framework should include baseline + GDPR-specific entities."""
    entities = get_entities_for_frameworks(["GDPR"])

    expected = set(BASELINE_ENTITIES + GDPR_ADDITIONAL_ENTITIES)
    assert set(entities) == expected

    # Verify GDPR-specific entities are included
    assert "EU_NATIONAL_ID" in entities
    assert "EU_VAT_NUMBER" in entities
    assert "EU_PASSPORT" in entities


def test_get_entities_for_frameworks_soc2():
    """SOC2 framework should include baseline + SOC2-specific entities."""
    entities = get_entities_for_frameworks(["SOC2"])

    expected = set(BASELINE_ENTITIES + SOC2_ADDITIONAL_ENTITIES)
    assert set(entities) == expected

    # Verify SOC2-specific entities are included
    assert "API_KEY" in entities
    assert "AWS_KEY" in entities
    assert "GCP_KEY" in entities
    assert "GITHUB_TOKEN" in entities
    assert "JWT_TOKEN" in entities
    assert "PRIVATE_KEY" in entities


def test_get_entities_for_frameworks_multiple():
    """Multiple frameworks should return union of all entities."""
    entities = get_entities_for_frameworks(["HIPAA", "GDPR"])

    expected = set(
        BASELINE_ENTITIES + HIPAA_ADDITIONAL_ENTITIES + GDPR_ADDITIONAL_ENTITIES
    )
    assert set(entities) == expected

    # Verify entities from both frameworks are included
    assert "MEDICAL_RECORD_NUMBER" in entities  # HIPAA
    assert "EU_VAT_NUMBER" in entities  # GDPR
    assert "PERSON" in entities  # Baseline


def test_get_entities_for_frameworks_all_frameworks():
    """All frameworks together should return union of all entities."""
    entities = get_entities_for_frameworks(["HIPAA", "FinTech", "GDPR", "SOC2"])

    expected = set(
        BASELINE_ENTITIES
        + HIPAA_ADDITIONAL_ENTITIES
        + FINTECH_ADDITIONAL_ENTITIES
        + GDPR_ADDITIONAL_ENTITIES
        + SOC2_ADDITIONAL_ENTITIES
    )
    assert set(entities) == expected

    # Should have significantly more entities than baseline
    assert len(entities) > len(BASELINE_ENTITIES)


def test_get_entities_for_frameworks_case_insensitive():
    """Framework names should be case-insensitive."""
    entities_lower = get_entities_for_frameworks(["hipaa"])
    entities_upper = get_entities_for_frameworks(["HIPAA"])
    entities_mixed = get_entities_for_frameworks(["HiPaA"])

    assert set(entities_lower) == set(entities_upper)
    assert set(entities_upper) == set(entities_mixed)
    assert "MEDICAL_RECORD_NUMBER" in entities_lower


def test_get_entities_for_frameworks_aliases():
    """Framework aliases should work (e.g., PCI-DSS for FinTech)."""
    entities_fintech = get_entities_for_frameworks(["FinTech"])
    entities_pci = get_entities_for_frameworks(["PCI-DSS"])
    entities_pci_short = get_entities_for_frameworks(["PCI"])

    assert set(entities_fintech) == set(entities_pci)
    assert set(entities_fintech) == set(entities_pci_short)


def test_get_entities_for_frameworks_unknown_framework():
    """Unknown framework should not crash and should include known frameworks."""
    # Unknown framework should not crash
    entities = get_entities_for_frameworks(["ISO27001", "HIPAA"])

    # Should still include HIPAA entities (ignores unknown framework)
    expected = set(BASELINE_ENTITIES + HIPAA_ADDITIONAL_ENTITIES)
    assert set(entities) == expected

    # Test with only unknown framework - should return baseline
    entities_unknown_only = get_entities_for_frameworks(["UnknownFramework"])
    assert set(entities_unknown_only) == set(BASELINE_ENTITIES)


def test_get_entities_for_frameworks_deduplication():
    """Duplicate frameworks should not result in duplicate entities."""
    entities = get_entities_for_frameworks(["HIPAA", "HIPAA", "hipaa"])

    expected = set(BASELINE_ENTITIES + HIPAA_ADDITIONAL_ENTITIES)
    assert set(entities) == expected

    # Verify no duplicates in the list
    assert len(entities) == len(set(entities))


def test_get_entities_for_frameworks_baseline_always_included():
    """Baseline entities should always be included regardless of framework."""
    for framework in ["HIPAA", "FinTech", "GDPR", "SOC2"]:
        entities = get_entities_for_frameworks([framework])

        # All baseline entities should be present
        for baseline_entity in BASELINE_ENTITIES:
            assert baseline_entity in entities, f"{baseline_entity} missing for {framework}"
