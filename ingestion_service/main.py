from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import router
from core.config import settings
from db.log_store import create_log_store
from db.supabase_client import close_db, init_db
from services.buffer import log_buffer


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await log_buffer.start_worker(
        create_log_store(),
        settings.max_batch_size,
        settings.flush_interval_seconds,
    )
    try:
        yield
    finally:
        await log_buffer.stop_worker()
        close_db()


app = FastAPI(title="Inference Logging Ingestion Service", lifespan=lifespan)
app.include_router(router)
