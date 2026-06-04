import asyncio
from typing import Any, Dict, Iterable


class LogBuffer:
    def __init__(self) -> None:
        self.queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

    async def enqueue_many(self, logs: Iterable[Dict[str, Any]]) -> int:
        count = 0
        for log in logs:
            await self.queue.put(log)
            count += 1
        return count

    def size(self) -> int:
        return self.queue.qsize()


log_buffer = LogBuffer()
