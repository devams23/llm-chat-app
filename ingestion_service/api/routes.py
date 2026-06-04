from fastapi import APIRouter, HTTPException

from schemas.logs import IngestPayload
from services.buffer import log_buffer
from services.ingestion import prepare_logs_for_ingestion


router = APIRouter()


@router.post("/api/ingest/logs")
async def ingest_logs(payload: IngestPayload):
    """
    Receives inference logs from SDK.
    Validates, processes, and stores.
    """

    try:
        logs_to_store = prepare_logs_for_ingestion(payload)
        logs_received = await log_buffer.enqueue_many(logs_to_store)

        return {
            "status": "accepted",
            "logs_received": logs_received,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
