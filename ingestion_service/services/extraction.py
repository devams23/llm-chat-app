from datetime import datetime
from typing import Any, Dict, Optional


def extract_metadata(log: Dict[str, Any]) -> Dict[str, Any]:
    """Extract useful metadata from logs"""
    latency_ms = float(log.get("latency_ms") or 0)
    output_tokens = int(log.get("output_tokens") or 0)
    throughput = output_tokens / (latency_ms / 1000) if latency_ms > 0 else 0

    return {
        "cost_usd": calculate_cost(
            log.get("provider", ""),
            log.get("model", ""),
            int(log.get("input_tokens") or 0),
            output_tokens,
        ),
        "latency_bucket": categorize_latency(latency_ms),
        "throughput": throughput,
        "error_type": categorize_error(log.get("error_message")),
        "date": parse_log_date(str(log.get("timestamp", ""))),
    }


def calculate_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost in USD"""
    costs = {
        "anthropic": {
            "claude-opus-4-6": {"input": 0.003, "output": 0.015},
            "claude-sonnet-4-6": {"input": 0.003, "output": 0.015},
        },
        "openai": {
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        }
    }
    
    pricing = costs.get(provider, {}).get(model, {"input": 0, "output": 0})
    return (input_tokens / 1000) * pricing["input"] + (output_tokens / 1000) * pricing["output"]


def categorize_latency(latency_ms: float) -> str:
    if latency_ms < 0:
        return "invalid"
    if latency_ms < 500:
        return "fast"
    if latency_ms < 2000:
        return "normal"
    if latency_ms < 10000:
        return "slow"
    return "very_slow"


def categorize_error(error_message: Optional[str]) -> Optional[str]:
    if not error_message:
        return None

    message = error_message.lower()
    if "timeout" in message or "timed out" in message:
        return "timeout"
    if "rate limit" in message or "429" in message:
        return "rate_limit"
    if "auth" in message or "api key" in message or "401" in message or "403" in message:
        return "auth"
    if "token" in message or "context" in message:
        return "token_limit"
    if "network" in message or "connection" in message:
        return "network"
    return "other"


def parse_log_date(timestamp: str) -> str:
    try:
        normalized = timestamp.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).date().isoformat()
    except ValueError:
        return datetime.utcnow().date().isoformat()
