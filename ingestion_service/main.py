from contextlib import asynccontextmanager
from http.client import HTTPResponse

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

        """ TODO: here now instead of directly caling the supabase client, we have to first add it to a queue, (in-memory), like a buffere to store the logs, but the buffer will have a limit, and once the limit is reached, then we will call the supabase client to store the logs in bulk, this way we can reduce the number of calls to the supabase client, and also we can handle the case when the supabase client is down, we can store the logs in the buffer and then once the supabase client is up, we can store the logs in bulk.
        , we can also have a background task, which looks at the buffer and the logs inthe buffere exceed a certain threshold, or a certain time interval, then it will try to store the logs in the supabase client in bulk, this way we can ensure that the logs are stored in the supabase client even if the supabase client is down for some time. """
        

        """ # 6. Publish events (optional)
        for log in stored_logs:
            publish_event("inference.logged", log) """

        return HTTPResponse(status_code=200, content={"status": "success", "logs_ingested": len(logs_to_store)})
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

