
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Protocol

from pydantic import BaseModel

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

try:
    from supabase import Client, create_client
except ModuleNotFoundError:
    Client = None
    create_client = None


if load_dotenv:
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_TABLE = os.environ.get("SUPABASE_TABLE", "inference_logs")
supabase_client: Optional[Client] = None


class InferenceLogPayload(BaseModel):
    log_id: str
    conversation_id: str
    session_id: str
    timestamp: str
    latency_ms: float
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    request_preview: str
    response_preview: str
    status: str
    error_message: Optional[str] = None
    temperature: float
    max_tokens: int
    user_id: Optional[str] = None
    custom_metadata: Optional[Dict[str, Any]] = None

class IngestPayload(BaseModel):
    logs: List[InferenceLogPayload]


class InferenceLogModel:
    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


class LogStore(Protocol):
    def save_logs(self, logs: Iterable[Dict[str, Any]]) -> List[InferenceLogModel]:
        ...


class SupabaseLogStore:
    def __init__(self, client: Client, table_name: str) -> None:
        self.client = client
        self.table_name = table_name

    def save_logs(self, logs: Iterable[Dict[str, Any]]) -> List[InferenceLogModel]:
        records = [normalize_log_record(log) for log in logs]
        if not records:
            return []

        response = self.client.table(self.table_name).insert(records).execute()
        inserted_records = response.data or records
        return [InferenceLogModel(**record) for record in inserted_records]

    def rollback(self) -> None:
        return None


class FallbackLogStore:
    def __init__(self) -> None:
        self.items: List[InferenceLogModel] = []

    def save_logs(self, logs: Iterable[Dict[str, Any]]) -> List[InferenceLogModel]:
        stored_logs = [InferenceLogModel(**normalize_log_record(log)) for log in logs]
        self.items.extend(stored_logs)
        return stored_logs

    def rollback(self) -> None:
        return None


def create_supabase_client() -> Optional[Client]:
    """Change this function if you move away from Supabase later."""
    if not SUPABASE_URL and not SUPABASE_KEY:
        return None

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Both SUPABASE_URL and SUPABASE_KEY must be set")

    if not create_client:
        raise RuntimeError("Install the supabase package to use Supabase storage")

    return create_client(SUPABASE_URL, SUPABASE_KEY)


def create_log_store() -> LogStore:
    """Swap this factory when replacing Supabase with another backend."""
    if supabase_client:
        return SupabaseLogStore(supabase_client, SUPABASE_TABLE)
    return FallbackLogStore()


def normalize_log_record(log: Dict[str, Any]) -> Dict[str, Any]:
    record = log.copy()
    timestamp = record.get("timestamp")

    if hasattr(timestamp, "isoformat"):
        record["timestamp"] = timestamp.isoformat()

    return record


def init_db() -> None:
    global supabase_client
    supabase_client = create_supabase_client()


def close_db() -> None:
    global supabase_client
    supabase_client = None
