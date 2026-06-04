from http.client import HTTPResponse

from fastapi import APIRouter, HTTPException

from models import InferenceLogModel
from schemas.logs import IngestPayload
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

        """TODO:here now instead of directly caling the supabase client, we have to first add it to a queue, (in-memory), like a buffere to store the logs, but the buffer will have a limit, and once the limit is reached, then we will call the supabase client to store the logs in bulk, this way we can reduce the number of calls to the supabase client, and also we can handle the case when the supabase client is down, we can store the logs in the buffer and then once the supabase client is up, we can store the logs in bulk.
        , we can also have a background task, which looks at the buffer and the logs inthe buffere exceed a certain threshold, or a certain time interval, then it will try to store the logs in the supabase client in bulk, this way we can ensure that the logs are stored in the supabase client even if the supabase client is down for some time."""

        """ # 6. Publish events (optional)
        for log in stored_logs:
            publish_event("inference.logged", log) """

        return HTTPResponse(status_code=200, content={"status": "success", "logs_ingested": len(logs_to_store)})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def publish_event(event_name: str, log: InferenceLogModel) -> None:
    """Placeholder hook for event bus integration."""
    return None
