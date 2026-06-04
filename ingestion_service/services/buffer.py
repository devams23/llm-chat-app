import asyncio
import logging
from typing import Any, Dict, Iterable

from db.log_store import LogStore


class LogBuffer:
    def __init__(self) -> None:
        self.queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self._worker_task: asyncio.Task[None] | None = None
        self._stop_event: asyncio.Event | None = None

    async def enqueue_many(self, logs: Iterable[Dict[str, Any]]) -> int:
        count = 0
        for log in logs:
            await self.queue.put(log)
            count += 1
        return count

    def size(self) -> int:
        return self.queue.qsize()

    async def start_worker(
        self,
        log_store: LogStore,
        max_batch_size: int,
        flush_interval_seconds: float,
    ) -> None:
        if self._worker_task and not self._worker_task.done():
            return

        self._stop_event = asyncio.Event()
        self._worker_task = asyncio.create_task(
            self._run_worker(log_store, max_batch_size, flush_interval_seconds)
        )

    async def stop_worker(self) -> None:
        if not self._worker_task or not self._stop_event:
            return

        self._stop_event.set()
        await self._worker_task
        self._worker_task = None
        self._stop_event = None

    async def _run_worker(
        self,
        log_store: LogStore,
        max_batch_size: int,
        flush_interval_seconds: float,
    ) -> None:
        batch: list[Dict[str, Any]] = []

        while self._stop_event and not self._stop_event.is_set():
            should_flush = False
            try:
                log = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=flush_interval_seconds,
                )
                batch.append(log)
                should_flush = len(batch) >= max_batch_size
            except asyncio.TimeoutError:
                should_flush = bool(batch)

            if should_flush:
                await self._flush_batch(log_store, batch)
                batch.clear()

    async def _flush_batch(self, log_store: LogStore, batch: list[Dict[str, Any]]) -> None:
        if not batch:
            return

        try:
            await asyncio.to_thread(log_store.save_logs, list(batch))
        except Exception:
            logging.exception("Failed to flush inference log batch")


log_buffer = LogBuffer()
