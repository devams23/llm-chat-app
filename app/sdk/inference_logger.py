import inspect
import json
import time
import uuid
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
import httpx
import asyncio
from functools import wraps

@dataclass
class InferenceLog:
    """Complete inference metadata"""
    # Identifiers
    log_id: str
    conversation_id: str
    session_id: str
    
    # Timing
    timestamp: str
    latency_ms: float
    
    # Model Info
    model: str
    provider: str
    
    # Tokens
    input_tokens: int
    output_tokens: int
    total_tokens: int
    
    # Request/Response
    request_preview: str  # First 500 chars of input
    response_preview: str  # First 500 chars of output
    
    # Status
    status: str  # "success", "error", "rate_limit", etc.
    error_message: Optional[str] = None
    
    # Metadata
    temperature: float = 0.7
    max_tokens: int = 1000
    user_id: Optional[str] = None
    custom_metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)

class InferenceLogger:
    """
    Lightweight logger for LLM inferences.
    Sends logs to ingestion endpoint.
    """
    
    def __init__(
        self,
        ingestion_url: str,
        batch_size: int = 10,
        flush_interval_seconds: int = 5
    ):
        self.ingestion_url = ingestion_url
        self.batch_size = batch_size
        self.flush_interval_seconds = flush_interval_seconds
        self.buffer: list[InferenceLog] = []
        self.lock = asyncio.Lock()
        self._flush_task = None
    
    async def log(self, inference: InferenceLog) -> None:
        """Add log to buffer and flush if needed"""
        async with self.lock:
            self.buffer.append(inference)
            
            if len(self.buffer) >= self.batch_size:
                await self._flush()
    
    async def _flush(self) -> None:
        """Send buffered logs to ingestion service"""
        if not self.buffer:
            return
        
        logs_to_send = self.buffer.copy()
        self.buffer.clear()
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.ingestion_url}/api/ingest/logs",
                    json={"logs": [log.to_dict() for log in logs_to_send]},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    print(f"Logging error: {response.status_code}")
                    # Re-add to buffer on failure
                    self.buffer.extend(logs_to_send)
        
        except Exception as e:
            print(f"Failed to send logs: {e}")
            # Implement retry logic or queue to disk
            self.buffer.extend(logs_to_send)
    
    async def flush_all(self) -> None:
        """Force flush all buffered logs"""
        while self.buffer:
            await self._flush()
            await asyncio.sleep(0.1)

class LoggingDecorator:
    """Decorator to automatically log LLM calls"""
    
    def __init__(self, logger: InferenceLogger, provider: str, model: str):
        self.logger = logger
        self.provider = provider
        self.model = model
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            log_id = str(uuid.uuid4())
            start_time = time.time()
            
            # Extract context
            conversation_id = kwargs.get("conversation_id", "unknown")
            session_id = kwargs.get("session_id", str(uuid.uuid4()))
            user_id = kwargs.get("user_id")
            
            # Get input preview
            messages = kwargs.get("messages", args[0] if args else [])
            request_preview = json.dumps(messages)[:500]
            
            error_message = None
            response_preview = ""
            status = "success"
            input_tokens = 0
            output_tokens = 0
            
            try:
                # Call the wrapped function
                result = await func(*args, **kwargs)
                
                # Extract tokens if available
                if isinstance(result, dict):
                    input_tokens = result.get("input_tokens", 0)
                    output_tokens = result.get("output_tokens", 0)
                    response_preview = str(result.get("content", ""))[:500]
                else:
                    response_preview = str(result)[:500]
            
            except Exception as e:
                status = "error"
                error_message = str(e)
                raise
            
            finally:
                # Log the inference
                latency_ms = (time.time() - start_time) * 1000
                
                log = InferenceLog(
                    log_id=log_id,
                    conversation_id=conversation_id,
                    session_id=session_id,
                    timestamp=datetime.utcnow().isoformat(),
                    latency_ms=latency_ms,
                    model=self.model,
                    provider=self.provider,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens,
                    request_preview=request_preview,
                    response_preview=response_preview,
                    status=status,
                    error_message=error_message,
                    user_id=user_id,
                    custom_metadata=kwargs.get("metadata")
                )
                
                await self.logger.log(log)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # For sync functions
            log_id = str(uuid.uuid4())
            start_time = time.time()
            
            conversation_id = kwargs.get("conversation_id", "unknown")
            session_id = kwargs.get("session_id", str(uuid.uuid4()))
            user_id = kwargs.get("user_id")
            
            messages = kwargs.get("messages", args[0] if args else [])
            request_preview = json.dumps(messages)[:500]
            
            error_message = None
            response_preview = ""
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                response_preview = str(result)[:500]
                return result
            
            except Exception as e:
                status = "error"
                error_message = str(e)
                raise
            
            finally:
                latency_ms = (time.time() - start_time) * 1000
                
                log = InferenceLog(
                    log_id=log_id,
                    conversation_id=conversation_id,
                    session_id=session_id,
                    timestamp=datetime.utcnow().isoformat(),
                    latency_ms=latency_ms,
                    model=self.model,
                    provider=self.provider,
                    request_preview=request_preview,
                    response_preview=response_preview,
                    status=status,
                    error_message=error_message,
                    user_id=user_id
                )
                
                # Use asyncio to send logs
                asyncio.create_task(self.logger.log(log))
        
        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper