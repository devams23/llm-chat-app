import re
from typing import Any, Dict


PII_PATTERNS = (
    (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "[REDACTED_EMAIL]",
    ),
    (
        re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
        "[REDACTED_PHONE]",
    ),
    (
        re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
        "[REDACTED_CC]",
    ),
)


def redact_pii(log: Dict[str, Any]) -> Dict[str, Any]:
    """Remove PII from logs"""
    log = log.copy()

    for field in ("request_preview", "response_preview"):
        value = log.get(field)
        if not isinstance(value, str):
            continue

        for pattern, replacement in PII_PATTERNS:
            value = pattern.sub(replacement, value)

        log[field] = value

    return log
