"""
Custom PII recognizers for framework-specific entity detection.

This module provides pattern-based recognizers for PII types not included
in Microsoft Presidio's default set, supporting HIPAA, FinTech, GDPR, and SOC2
compliance frameworks.
"""

from presidio_analyzer import PatternRecognizer, Pattern


def get_custom_recognizers() -> list[PatternRecognizer]:
    """
    Return list of custom PII recognizers for framework-specific entities.

    Returns:
        List of PatternRecognizer instances to be added to Presidio analyzer.
    """
    return [
        # ========== Baseline Overrides ==========
        # US SSN — Presidio's built-in UsSsnRecognizer has "very weak" patterns
        # that fail with en_core_web_sm. This custom recognizer detects reliably.
        PatternRecognizer(
            supported_entity="US_SSN",
            patterns=[
                Pattern(
                    name="ssn_dashed",
                    regex=r"\b(?!9\d{2}-[7-9]\d)\d{3}-\d{2}-\d{4}\b",
                    score=0.85,
                ),
                Pattern(
                    name="ssn_spaced",
                    regex=r"\b(?!9\d{2} [7-9]\d)\d{3} \d{2} \d{4}\b",
                    score=0.85,
                ),
                Pattern(
                    name="ssn_dotted",
                    regex=r"\b(?!9\d{2}\.[7-9]\d)\d{3}\.\d{2}\.\d{4}\b",
                    score=0.85,
                ),
            ],
            context=["social", "security", "ssn", "ssid", "tax"],
        ),
        # US Passport — built-in scores 0.05-0.1, effectively broken
        PatternRecognizer(
            supported_entity="US_PASSPORT",
            patterns=[
                Pattern(
                    name="passport_9digit",
                    regex=r"\b[0-9]{9}\b",
                    score=0.4,
                ),
                Pattern(
                    name="passport_next_gen",
                    regex=r"\b[A-Z][0-9]{8}\b",
                    score=0.5,
                ),
            ],
            context=["passport", "travel", "document", "state department"],
        ),
        # US Driver's License — built-in scores 0.01-0.3, effectively broken
        PatternRecognizer(
            supported_entity="US_DRIVER_LICENSE",
            patterns=[
                Pattern(
                    name="license_alpha_numeric",
                    regex=r"\b[A-Z][0-9]{7,12}\b",
                    score=0.4,
                ),
                Pattern(
                    name="license_numeric",
                    regex=r"\b[0-9]{7,13}\b",
                    score=0.3,
                ),
            ],
            context=["driver", "license", "licence", "dl", "driving", "dmv"],
        ),
        # US ITIN — built-in scores 0.05-0.3, effectively broken
        PatternRecognizer(
            supported_entity="US_ITIN",
            patterns=[
                Pattern(
                    name="itin_dashed",
                    regex=r"\b9\d{2}-[7-9]\d-\d{4}\b",
                    score=0.85,
                ),
                Pattern(
                    name="itin_spaced",
                    regex=r"\b9\d{2} [7-9]\d \d{4}\b",
                    score=0.85,
                ),
            ],
            context=["itin", "tax", "individual", "taxpayer"],
        ),
        # US Bank Account — built-in score 0.05, effectively broken
        PatternRecognizer(
            supported_entity="US_BANK_NUMBER",
            patterns=[
                Pattern(
                    name="bank_account",
                    regex=r"\b[0-9]{8,17}\b",
                    score=0.3,
                ),
            ],
            context=["bank", "account", "checking", "savings", "routing", "deposit"],
        ),
        # ========== HIPAA Recognizers ==========
        # Medical Record Number (MRN)
        PatternRecognizer(
            supported_entity="MEDICAL_RECORD_NUMBER",
            patterns=[
                Pattern(
                    name="mrn_pattern",
                    regex=r"\b(MRN|MR#|Medical\s+Record)[:\s#]*([A-Z0-9]{6,10})\b",
                    score=0.85,
                )
            ],
            context=["patient", "medical", "health", "record", "hospital"],
        ),
        # Health Plan Beneficiary Number
        PatternRecognizer(
            supported_entity="HEALTH_PLAN_NUMBER",
            patterns=[
                Pattern(
                    name="health_plan_pattern",
                    regex=r"\b(Plan\s+ID|Health\s+Plan|Member\s+ID|Beneficiary)[:\s#]*([A-Z0-9]{9,12})\b",
                    score=0.80,
                )
            ],
            context=["insurance", "plan", "health", "member", "beneficiary"],
        ),
        # Device Serial Number
        PatternRecognizer(
            supported_entity="DEVICE_SERIAL_NUMBER",
            patterns=[
                Pattern(
                    name="device_serial_pattern",
                    regex=r"\b(S/N|Serial|Device\s+ID)[:\s#]*([A-Z0-9]{8,20})\b",
                    score=0.75,
                )
            ],
            context=["device", "serial", "equipment", "medical", "implant"],
        ),
        # ========== FinTech Recognizers ==========
        # CVV / CVC Code
        PatternRecognizer(
            supported_entity="CVV",
            patterns=[
                Pattern(
                    name="cvv_pattern",
                    regex=r"\b(CVV|CVC|Security\s+Code)[:\s]*(\d{3,4})\b",
                    score=0.90,
                )
            ],
            context=["card", "credit", "debit", "payment", "cvv", "cvc"],
        ),
        # Routing Number (ABA routing number)
        PatternRecognizer(
            supported_entity="ROUTING_NUMBER",
            patterns=[
                Pattern(
                    name="routing_pattern",
                    regex=r"\b(Routing|ABA|RTN)[:\s#]*(\d{9})\b",
                    score=0.95,
                )
            ],
            context=["bank", "account", "transfer", "routing", "aba"],
        ),
        # Account Number (generic financial account)
        PatternRecognizer(
            supported_entity="ACCOUNT_NUMBER",
            patterns=[
                Pattern(
                    name="account_pattern",
                    regex=r"\b(Account|Acct|A/C)[:\s#]*(\d{8,17})\b",
                    score=0.80,
                )
            ],
            context=["bank", "account", "financial", "checking", "savings"],
        ),
        # ========== GDPR Recognizers ==========
        # EU VAT Number
        PatternRecognizer(
            supported_entity="EU_VAT_NUMBER",
            patterns=[
                Pattern(
                    name="eu_vat_pattern",
                    regex=r"\b(VAT|VAT\s+Number)[:\s#]*([A-Z]{2}\d{8,12})\b",
                    score=0.90,
                ),
                Pattern(
                    name="vat_standalone",
                    regex=r"\b([A-Z]{2}\d{8,12})\b",
                    score=0.70,  # Lower score without context
                ),
            ],
            context=["vat", "tax", "company", "business", "eu", "european"],
        ),
        # EU National ID (simplified pattern - actual implementation would need
        # country-specific patterns)
        PatternRecognizer(
            supported_entity="EU_NATIONAL_ID",
            patterns=[
                Pattern(
                    name="eu_id_pattern",
                    regex=r"\b(National\s+ID|ID\s+Number)[:\s#]*([A-Z0-9]{8,15})\b",
                    score=0.75,
                )
            ],
            context=["national", "id", "identity", "citizen", "passport"],
        ),
        # EU Passport (simplified pattern)
        PatternRecognizer(
            supported_entity="EU_PASSPORT",
            patterns=[
                Pattern(
                    name="eu_passport_pattern",
                    regex=r"\b(Passport|Passport\s+Number)[:\s#]*([A-Z0-9]{6,9})\b",
                    score=0.85,
                )
            ],
            context=["passport", "travel", "document", "identity"],
        ),
        # ========== SOC2 Recognizers ==========
        # API Keys (various formats)
        PatternRecognizer(
            supported_entity="API_KEY",
            patterns=[
                Pattern(
                    name="openai_key",
                    regex=r"\bsk-proj-[A-Za-z0-9_-]{48,}\b",
                    score=0.99,
                ),
                Pattern(
                    name="openai_legacy_key",
                    regex=r"\bsk-[A-Za-z0-9]{48,}\b",
                    score=0.99,
                ),
                Pattern(
                    name="google_api_key",
                    regex=r"\bAIza[A-Za-z0-9_-]{35,}\b",
                    score=0.99,
                ),
                Pattern(
                    name="generic_api_key",
                    regex=r"\b(api[_-]?key|apikey)[:\s=]+['\"]?([A-Za-z0-9_-]{32,})['\"]?\b",
                    score=0.85,
                ),
            ],
            context=["api", "key", "token", "secret", "credential"],
        ),
        # AWS Access Key
        PatternRecognizer(
            supported_entity="AWS_KEY",
            patterns=[
                Pattern(
                    name="aws_access_key",
                    regex=r"\bAKIA[A-Z0-9]{16}\b",
                    score=0.99,
                ),
                Pattern(
                    name="aws_secret_key",
                    regex=r"\b(aws[_-]?secret[_-]?access[_-]?key)[:\s=]+['\"]?([A-Za-z0-9/+=]{40})['\"]?\b",
                    score=0.95,
                ),
            ],
            context=["aws", "amazon", "access", "secret", "key"],
        ),
        # GCP Key (Google Cloud Platform)
        PatternRecognizer(
            supported_entity="GCP_KEY",
            patterns=[
                Pattern(
                    name="gcp_api_key",
                    regex=r"\bAIza[A-Za-z0-9_-]{35,}\b",
                    score=0.99,
                ),
                Pattern(
                    name="gcp_service_account",
                    regex=r'"type":\s*"service_account"',
                    score=0.90,
                ),
            ],
            context=["gcp", "google", "cloud", "service", "account"],
        ),
        # GitHub Token
        PatternRecognizer(
            supported_entity="GITHUB_TOKEN",
            patterns=[
                Pattern(
                    name="github_pat",
                    regex=r"\bghp_[A-Za-z0-9]{36,}\b",
                    score=0.99,
                ),
                Pattern(
                    name="github_oauth",
                    regex=r"\bgho_[A-Za-z0-9]{36,}\b",
                    score=0.99,
                ),
                Pattern(
                    name="github_app",
                    regex=r"\bghs_[A-Za-z0-9]{36,}\b",
                    score=0.99,
                ),
            ],
            context=["github", "token", "pat", "oauth"],
        ),
        # JWT Token
        PatternRecognizer(
            supported_entity="JWT_TOKEN",
            patterns=[
                Pattern(
                    name="jwt_pattern",
                    regex=r"\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b",
                    score=0.90,
                )
            ],
            context=["jwt", "token", "bearer", "authorization", "auth"],
        ),
        # Private Key (SSH, PGP, etc.)
        PatternRecognizer(
            supported_entity="PRIVATE_KEY",
            patterns=[
                Pattern(
                    name="rsa_private_key",
                    regex=r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
                    score=0.99,
                ),
                Pattern(
                    name="openssh_private_key",
                    regex=r"-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----",
                    score=0.99,
                ),
                Pattern(
                    name="pgp_private_key",
                    regex=r"-----BEGIN\s+PGP\s+PRIVATE\s+KEY\s+BLOCK-----",
                    score=0.99,
                ),
            ],
            context=["private", "key", "ssh", "rsa", "pgp", "certificate"],
        ),
    ]
