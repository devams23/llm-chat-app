from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException

from models import (
    InferenceLogModel,
    IngestPayload,
    LogStore,
    close_db,
    create_log_store,
    init_db,
)
from services.extraction import extract_metadata
from services.pii_redaction import redact_pii
from services.validation import validate_ingest_payload


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    try:
        yield
    finally:
        close_db()


app = FastAPI(title="Inference Logging Ingestion Service", lifespan=lifespan)


def get_log_store() -> LogStore:
    return create_log_store()


@app.post("/api/ingest/logs")
async def ingest_logs(payload: IngestPayload, log_store: LogStore = Depends(get_log_store)):
    """
    Receives inference logs from SDK.
    Validates, processes, and stores.
    """

    try:
        validate_ingest_payload(payload)

        # Process each log
        logs_to_store = []
        for log_data in payload.logs:
            # 1. Parse and validate
            log_dict = log_data.model_dump()  # Convert Pydantic model to dict for processing

            # 2. Extract metadata
            extracted_metadata = extract_metadata(log_dict)

            # 3. Redact PII (if enabled)
            redacted_log = redact_pii(log_dict)

            # 4. Prepare database record
            logs_to_store.append(
                {
                    **redacted_log,
                    "extracted_metadata": extracted_metadata,
                }
            )

        # 5. Batch insert
        stored_logs = log_store.save_logs(logs_to_store)

        # 6. Publish events (optional)
        for log in stored_logs:
            publish_event("inference.logged", log)

        return {
            "status": "success",
            "logs_ingested": len(stored_logs)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        rollback = getattr(log_store, "rollback", None)
        if rollback:
            rollback()
        raise HTTPException(status_code=500, detail=str(e))


def publish_event(event_name: str, log: InferenceLogModel) -> None:
    """Placeholder hook for event bus integration."""
    return None

