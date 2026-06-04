from typing import Any, Dict, Iterable, List, Protocol

from db.supabase_client import get_supabase_client, get_supabase_table


class LogStore(Protocol):
    def save_logs(self, logs: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        ...


class SupabaseLogStore:
    def __init__(self, client: Any, table_name: str) -> None:
        self.client = client
        self.table_name = table_name

    def save_logs(self, logs: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        records = [normalize_log_record(log) for log in logs]
        if not records:
            return []

        response = self.client.table(self.table_name).insert(records).execute()
        return response.data or records

    def rollback(self) -> None:
        return None


class FallbackLogStore:
    def __init__(self) -> None:
        self.items: List[Dict[str, Any]] = []

    def save_logs(self, logs: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        stored_logs = [normalize_log_record(log) for log in logs]
        self.items.extend(stored_logs)
        return stored_logs

    def rollback(self) -> None:
        return None


def create_log_store() -> LogStore:
    """Swap this factory when replacing Supabase with another backend."""
    supabase_client = get_supabase_client()
    if supabase_client:
        return SupabaseLogStore(supabase_client, get_supabase_table())
    return FallbackLogStore()


def normalize_log_record(log: Dict[str, Any]) -> Dict[str, Any]:
    record = log.copy()
    timestamp = record.get("timestamp")

    if hasattr(timestamp, "isoformat"):
        record["timestamp"] = timestamp.isoformat()

    return record
