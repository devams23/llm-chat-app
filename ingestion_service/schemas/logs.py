from typing import Any, Dict, List, Optional

from pydantic import BaseModel


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
