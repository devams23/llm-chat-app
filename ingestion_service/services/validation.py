from datetime import datetime
from typing import List

from schemas.logs import IngestPayload, InferenceLogPayload


VALID_STATUSES = {"success", "error", "failed", "timeout"}


def validate_ingest_payload(payload: IngestPayload) -> None:
    if not payload.logs:
        raise ValueError("No logs provided")

    errors: List[str] = []
    for index, log in enumerate(payload.logs):
        errors.extend(validate_inference_log(log, index))

    if errors:
        raise ValueError("; ".join(errors))


def validate_inference_log(log: InferenceLogPayload, index: int) -> List[str]:
    errors: List[str] = []
    prefix = f"logs[{index}]"

    if log.latency_ms < 0:
        errors.append(f"{prefix}.latency_ms must be non-negative")
    if log.input_tokens < 0:
        errors.append(f"{prefix}.input_tokens must be non-negative")
    if log.output_tokens < 0:
        errors.append(f"{prefix}.output_tokens must be non-negative")
    if log.total_tokens < 0:
        errors.append(f"{prefix}.total_tokens must be non-negative")
    if log.total_tokens and log.total_tokens != log.input_tokens + log.output_tokens:
        errors.append(f"{prefix}.total_tokens must equal input_tokens + output_tokens")
    if log.temperature < 0:
        errors.append(f"{prefix}.temperature must be non-negative")
    if log.max_tokens <= 0:
        errors.append(f"{prefix}.max_tokens must be positive")
    if log.status.lower() not in VALID_STATUSES:
        errors.append(f"{prefix}.status must be one of {sorted(VALID_STATUSES)}")

    try:
        datetime.fromisoformat(log.timestamp.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{prefix}.timestamp must be ISO-8601 compatible")

    return errors
