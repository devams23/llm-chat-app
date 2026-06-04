# app/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON, Boolean, Index
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True)
    title = Column(String, default="New Conversation")
    
    # Multi-provider settings
    preferred_provider = Column(String, default="anthropic")
    preferred_model = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    
    role = Column(String)  # "user" or "assistant"
    content = Column(Text)
    
    # Track which provider/model generated this
    provider = Column(String)  # "anthropic", "openai", etc.
    model = Column(String)
    
    # Cost tracking
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    cost = Column(Float, default=0.0)  # in USD
    
    created_at = Column(DateTime, default=datetime.utcnow)

class ProviderConfig(Base):
    __tablename__ = "provider_configs"
    
    id = Column(Integer, primary_key=True)
    provider_name = Column(String, unique=True)  # "anthropic", "openai", etc.
    api_key = Column(String)  # Store securely with encryption
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class InferenceLog(Base):
    """Store all inference logs"""
    __tablename__ = "inference_logs"
    
    # Primary
    id = Column(Integer, primary_key=True)
    log_id = Column(String, unique=True, index=True)
    
    # Identifiers
    conversation_id = Column(String, index=True)
    session_id = Column(String, index=True)
    user_id = Column(String, nullable=True, index=True)
    
    # Timing
    timestamp = Column(DateTime, index=True)
    latency_ms = Column(Float)
    
    # Model Info
    model = Column(String, index=True)
    provider = Column(String, index=True)
    
    # Tokens
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    total_tokens = Column(Integer)
    
    # Request/Response
    request_preview = Column(Text)
    response_preview = Column(Text)
    
    # Status
    status = Column(String, index=True)  # success, error, rate_limit
    error_message = Column(Text, nullable=True)
    
    # Config
    temperature = Column(Float)
    max_tokens = Column(Integer)
    
    # Metadata
    extracted_metadata = Column(JSON)  # cost, latency_bucket, etc.
    custom_metadata = Column(JSON, nullable=True)
    
    # Indices for queries
    __table_args__ = (
        Index('idx_conversation_timestamp', 'conversation_id', 'timestamp'),
        Index('idx_provider_model_timestamp', 'provider', 'model', 'timestamp'),
        Index('idx_status_timestamp', 'status', 'timestamp'),
    )

class ErrorLog(Base):
    """Store error details for analysis"""
    __tablename__ = "error_logs"
    
    id = Column(Integer, primary_key=True)
    log_id = Column(String, ForeignKey('inference_logs.log_id'))
    
    error_type = Column(String, index=True)
    error_message = Column(Text)
    stack_trace = Column(Text, nullable=True)
    
    timestamp = Column(DateTime, index=True)
    provider = Column(String, index=True)
    model = Column(String, index=True)