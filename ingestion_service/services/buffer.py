import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable

from db.log_store import LogStore


@dataclass
class BufferedLog:
    record: Dict[str, Any]
    retry_count: int = 0


class LogBuffer:
    def __init__(self) -> None:
        self.queue: asyncio.Queue[BufferedLog] = asyncio.Queue()
        self._worker_task: asyncio.Task[None] | None = None
        self._stop_event: asyncio.Event | None = None
        self._log_store: LogStore | None = None
        self._active_batch: list[BufferedLog] = []

    async def enqueue_many(self, logs: Iterable[Dict[str, Any]]) -> int:
        count = 0
        for log in logs:
            await self.queue.put(BufferedLog(record=log))
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

        self._log_store = log_store
        self._stop_event = asyncio.Event()
        self._worker_task = asyncio.create_task(
            
            self._run_worker(log_store, max_batch_size, flush_interval_seconds)
        )

    async def stop_worker(self) -> None:
        if not self._worker_task or not self._stop_event:
            return

        self._stop_event.set()
        await self._worker_task

        if self._log_store:
            await self.flush_remaining(self._log_store)

        self._worker_task = None
        self._stop_event = None
        self._log_store = None

    async def _run_worker(
        self,
        log_store: LogStore,
        max_batch_size: int,
        flush_interval_seconds: float,
    ) -> None:
        while self._stop_event and not self._stop_event.is_set():
            should_flush = False
            try:
                log = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=flush_interval_seconds,
                )
                self._active_batch.append(log)
                should_flush = len(self._active_batch) >= max_batch_size
            except asyncio.TimeoutError:
                should_flush = bool(self._active_batch)

            if should_flush:
                batch = self._active_batch
                self._active_batch = []
                await self._flush_batch(log_store, batch, requeue_failed=True)

    async def flush_remaining(self, log_store: LogStore) -> None:
        remaining = self._active_batch
        self._active_batch = []

        while not self.queue.empty():
            remaining.append(self.queue.get_nowait())

        await self._flush_batch(log_store, remaining, requeue_failed=False)

    async def _flush_batch(
        self,
        log_store: LogStore,
        batch: list[BufferedLog],
        requeue_failed: bool,
    ) -> None:
        if not batch:
            return

        try:
            await asyncio.to_thread(log_store.save_logs, [item.record for item in batch])
        except Exception:
            logging.exception("Failed to flush inference log batch")
            if requeue_failed:
                for item in batch:
                    if item.retry_count < 1:
                        item.retry_count += 1
                        await self.queue.put(item)


log_buffer = LogBuffer()
