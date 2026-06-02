
import os
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Protocol

from pydantic import BaseModel

try:
    from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text, create_engine
    from sqlalchemy.orm import declarative_base, sessionmaker
except ModuleNotFoundError:
    Column = DateTime = Float = Integer = JSON = String = Text = create_engine = None
    declarative_base = sessionmaker = None


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ingestion_logs.db")

if create_engine and sessionmaker and declarative_base:
    Base = declarative_base()
else:
    class _FallbackBase:
        pass

    Base = _FallbackBase


engine = None
SessionLocal = None


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


if Column:

    class InferenceLogModel(Base):
        __tablename__ = "inference_logs"

        id = Column(Integer, primary_key=True, index=True)
        log_id = Column(String(255), unique=True, nullable=False, index=True)
        conversation_id = Column(String(255), nullable=False, index=True)
        session_id = Column(String(255), nullable=False, index=True)
        timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
        latency_ms = Column(Float, nullable=False)
        model = Column(String(255), nullable=False)
        provider = Column(String(255), nullable=False)
        input_tokens = Column(Integer, nullable=False)
        output_tokens = Column(Integer, nullable=False)
        total_tokens = Column(Integer, nullable=False)
        request_preview = Column(Text, nullable=False)
        response_preview = Column(Text, nullable=False)
        status = Column(String(64), nullable=False, index=True)
        error_message = Column(Text, nullable=True)
        temperature = Column(Float, nullable=False)
        max_tokens = Column(Integer, nullable=False)
        user_id = Column(String(255), nullable=True, index=True)
        custom_metadata = Column(JSON, nullable=True)
        extracted_metadata = Column(JSON, nullable=False, default=dict)
else:

    class InferenceLogModel:
        def __init__(self, **kwargs: Any) -> None:
            for key, value in kwargs.items():
                setattr(self, key, value)


class FallbackSession:
    def __init__(self) -> None:
        self.items: List[InferenceLogModel] = []

    def add(self, item: InferenceLogModel) -> None:
        self.items.append(item)

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def close(self) -> None:
        return None


class LogStore(Protocol):
    def save_logs(self, logs: Iterable[Dict[str, Any]]) -> List[InferenceLogModel]:
        ...


class SqlAlchemyLogStore:
    def __init__(self, db: Any) -> None:
        self.db = db

    def save_logs(self, logs: Iterable[Dict[str, Any]]) -> List[InferenceLogModel]:
        stored_logs = [InferenceLogModel(**normalize_log_record(log)) for log in logs]
        for db_log in stored_logs:
            self.db.add(db_log)

        self.db.commit()
        return stored_logs

    def rollback(self) -> None:
        self.db.rollback()


class FallbackLogStore(SqlAlchemyLogStore):
    pass


def create_engine_for_url(database_url: str):
    """Change this function when moving to a different SQL database connection."""
    if not create_engine:
        return None

    return create_engine(
        database_url,
        connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
    )


def create_log_store(db: Any) -> LogStore:
    """Swap this factory when replacing SQLAlchemy/Supabase with another backend."""
    if SessionLocal:
        return SqlAlchemyLogStore(db)
    return FallbackLogStore(db)


def normalize_log_record(log: Dict[str, Any]) -> Dict[str, Any]:
    record = log.copy()
    timestamp = record.get("timestamp")

    if isinstance(timestamp, str):
        record["timestamp"] = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    return record


def init_db() -> None:
    global SessionLocal, engine

    if not engine:
        engine = create_engine_for_url(DATABASE_URL)
        if engine and sessionmaker:
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    if engine:
        Base.metadata.create_all(bind=engine)


def close_db() -> None:
    global SessionLocal, engine

    if engine:
        engine.dispose()

    engine = None
    SessionLocal = None


def get_db():
    db = SessionLocal() if SessionLocal else FallbackSession()
    try:
        yield db
    finally:
        db.close()
