from typing import Any, Dict, List

from schemas.logs import IngestPayload
from services.extraction import extract_metadata
from services.pii_redaction import redact_pii
from services.validation import validate_ingest_payload


def prepare_logs_for_ingestion(payload: IngestPayload) -> List[Dict[str, Any]]:
    validate_ingest_payload(payload)

    logs_to_store: List[Dict[str, Any]] = []
    for log_data in payload.logs:
        log_dict = (
            log_data.model_dump()
            if hasattr(log_data, "model_dump")
            else log_data.dict()
        )
        extracted_metadata = extract_metadata(log_dict)
        redacted_log = redact_pii(log_dict)
        logs_to_store.append(
            {
                **redacted_log,
                "extracted_metadata": extracted_metadata,
            }
        )

    return logs_to_store
