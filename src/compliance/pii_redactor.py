import hashlib
from dataclasses import dataclass
from typing import Literal

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# Supported PII entity types
SUPPORTED_ENTITIES = [
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

RedactionMode = Literal["mask", "hash", "remove"]


@dataclass
class PIIDetection:
    """A single detected PII entity."""

    type: str
    replacement: str
    confidence: float
    start: int
    end: int


@dataclass
class RedactionResult:
    """Result of PII redaction."""

    redacted_text: str
    detections: list[PIIDetection]
    pii_detected: bool


class PIIRedactor:
    """
    PII detection and redaction using Microsoft Presidio.

    Supports three redaction modes:
    - mask: "John Smith" → "PERSON_A"
    - hash: "John Smith" → "HASH_a3f2c1b9"
    - remove: "John Smith" → "[REDACTED]"
    """

    def __init__(self, mode: RedactionMode = "mask"):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.mode = mode

    def redact(self, text: str) -> RedactionResult:
        """
        Detect and redact PII from text.

        Args:
            text: The text to scan and redact

        Returns:
            RedactionResult with redacted text and detection details
        """
        if not text or not text.strip():
            return RedactionResult(
                redacted_text=text,
                detections=[],
                pii_detected=False,
            )

        # Detect PII entities
        results = self.analyzer.analyze(
            text=text,
            entities=SUPPORTED_ENTITIES,
            language="en",
        )

        if not results:
            return RedactionResult(
                redacted_text=text,
                detections=[],
                pii_detected=False,
            )

        # Track replacements for consistent labeling (PERSON_A, PERSON_B, etc.)
        entity_counts: dict[str, int] = {}
        detections: list[PIIDetection] = []

        # Sort by start position for consistent processing
        sorted_results = sorted(results, key=lambda x: x.start)

        for result in sorted_results:
            entity_type = result.entity_type
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            label = chr(ord("A") + entity_counts[entity_type] - 1)

            # Generate replacement based on mode
            original_value = text[result.start : result.end]

            if self.mode == "mask":
                replacement = f"{entity_type}_{label}"
            elif self.mode == "hash":
                hash_val = hashlib.sha256(original_value.encode()).hexdigest()[:8]
                replacement = f"HASH_{hash_val}"
            else:  # remove
                replacement = "[REDACTED]"

            detections.append(
                PIIDetection(
                    type=entity_type,
                    replacement=replacement,
                    confidence=result.score,
                    start=result.start,
                    end=result.end,
                )
            )

        # Apply redactions in reverse order to preserve positions
        redacted = text
        for detection in sorted(detections, key=lambda x: x.start, reverse=True):
            redacted = (
                redacted[: detection.start]
                + detection.replacement
                + redacted[detection.end :]
            )

        return RedactionResult(
            redacted_text=redacted,
            detections=detections,
            pii_detected=True,
        )

    def redact_messages(
        self, messages: list[dict]
    ) -> tuple[list[dict], list[PIIDetection]]:
        """
        Redact PII from a list of chat messages.

        Args:
            messages: List of message dicts with 'role' and 'content' keys

        Returns:
            (redacted_messages, all_detections)
        """
        redacted_messages = []
        all_detections: list[PIIDetection] = []

        for message in messages:
            content = message.get("content", "")

            if isinstance(content, str):
                result = self.redact(content)
                redacted_messages.append(
                    {**message, "content": result.redacted_text}
                )
                all_detections.extend(result.detections)
            else:
                # Handle multimodal content (list of content parts)
                redacted_content = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        result = self.redact(part.get("text", ""))
                        redacted_content.append(
                            {**part, "text": result.redacted_text}
                        )
                        all_detections.extend(result.detections)
                    else:
                        redacted_content.append(part)
                redacted_messages.append({**message, "content": redacted_content})

        return redacted_messages, all_detections


# Create a default instance for import convenience
_default_redactor: PIIRedactor | None = None


def get_redactor(mode: RedactionMode = "mask") -> PIIRedactor:
    """Get a PIIRedactor instance with the specified mode."""
    global _default_redactor
    if _default_redactor is None or _default_redactor.mode != mode:
        _default_redactor = PIIRedactor(mode=mode)
    return _default_redactor
