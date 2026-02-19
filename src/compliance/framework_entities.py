"""
Framework-specific PII entity mappings.

This module defines which PII entities to detect based on customer's
compliance frameworks (HIPAA, FinTech, GDPR, SOC2).
"""

import structlog

logger = structlog.get_logger()

# Baseline entities - detected for ALL customers
# This matches the current SUPPORTED_ENTITIES in pii_redactor.py
BASELINE_ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "US_SSN",
    "CREDIT_CARD",
    "IBAN_CODE",
    "MEDICAL_LICENSE",
    "US_PASSPORT",
    "LOCATION",
    "DATE_TIME",
    "IP_ADDRESS",
    "URL",
]

# HIPAA (Healthcare) - additional entities for healthcare compliance
HIPAA_ADDITIONAL_ENTITIES = [
    "UK_NHS",                    # UK National Health Service number
    "US_DRIVER_LICENSE",         # Driver's license (PHI under HIPAA)
    "MEDICAL_RECORD_NUMBER",     # Custom recognizer
    "HEALTH_PLAN_NUMBER",        # Custom recognizer
    "DEVICE_SERIAL_NUMBER",      # Custom recognizer
]

# FinTech / PCI-DSS - additional entities for financial services
FINTECH_ADDITIONAL_ENTITIES = [
    "US_BANK_NUMBER",            # Bank account numbers
    "CRYPTO",                    # Cryptocurrency wallet addresses
    "US_ITIN",                   # Individual Taxpayer Identification Number
    "CVV",                       # Custom recognizer
    "ROUTING_NUMBER",            # Custom recognizer
    "ACCOUNT_NUMBER",            # Custom recognizer
]

# GDPR (EU Compliance) - additional entities for EU data protection
GDPR_ADDITIONAL_ENTITIES = [
    "EU_NATIONAL_ID",            # Custom recognizer (or Presidio regional)
    "EU_VAT_NUMBER",             # Custom recognizer
    "EU_PASSPORT",               # Custom recognizer (or Presidio regional)
]

# SOC2 (Security) - additional entities for security compliance
SOC2_ADDITIONAL_ENTITIES = [
    "API_KEY",                   # Custom recognizer
    "AWS_KEY",                   # Custom recognizer
    "GCP_KEY",                   # Custom recognizer
    "GITHUB_TOKEN",              # Custom recognizer
    "JWT_TOKEN",                 # Custom recognizer
    "PRIVATE_KEY",               # Custom recognizer
]

# Framework name to additional entities mapping
FRAMEWORK_ADDITIONAL_ENTITIES = {
    "hipaa": HIPAA_ADDITIONAL_ENTITIES,
    "fintech": FINTECH_ADDITIONAL_ENTITIES,
    "pci-dss": FINTECH_ADDITIONAL_ENTITIES,  # Alias for FinTech
    "pci": FINTECH_ADDITIONAL_ENTITIES,      # Alias for FinTech
    "gdpr": GDPR_ADDITIONAL_ENTITIES,
    "soc2": SOC2_ADDITIONAL_ENTITIES,
    "soc-2": SOC2_ADDITIONAL_ENTITIES,       # Alias for SOC2
}


def get_entities_for_frameworks(frameworks: list[str] | None) -> list[str]:
    """
    Get union of entities for given compliance frameworks.

    Args:
        frameworks: List of framework names (case-insensitive).
                   Examples: ["HIPAA"], ["FinTech", "GDPR"], None

    Returns:
        List of entity type names to detect. Always includes baseline entities,
        plus additional entities for specified frameworks.

    Examples:
        >>> get_entities_for_frameworks(None)
        ['PERSON', 'EMAIL_ADDRESS', ...]  # 12 baseline entities

        >>> get_entities_for_frameworks(["HIPAA"])
        ['PERSON', ..., 'MEDICAL_RECORD_NUMBER', ...]  # baseline + HIPAA

        >>> get_entities_for_frameworks(["HIPAA", "GDPR"])
        ['PERSON', ..., 'MEDICAL_RECORD_NUMBER', ..., 'EU_VAT_NUMBER']
        # baseline + HIPAA + GDPR (union, deduplicated)
    """
    # Start with baseline entities (always included)
    entities = set(BASELINE_ENTITIES)

    # If no frameworks specified, return baseline only
    if not frameworks:
        return sorted(list(entities))

    # Add entities for each framework
    for framework in frameworks:
        framework_lower = framework.lower().strip()

        if framework_lower in FRAMEWORK_ADDITIONAL_ENTITIES:
            entities.update(FRAMEWORK_ADDITIONAL_ENTITIES[framework_lower])
            logger.debug(
                "framework_entities_added",
                framework=framework,
                additional_count=len(FRAMEWORK_ADDITIONAL_ENTITIES[framework_lower]),
            )
        else:
            # Log warning for unknown framework but continue
            logger.warning(
                "unknown_compliance_framework",
                framework=framework,
                known_frameworks=list(FRAMEWORK_ADDITIONAL_ENTITIES.keys()),
            )

    # Return sorted list for consistency
    return sorted(list(entities))
