# AI Inference Observability Platform

> Production-inspired observability platform for AI applications that captures, processes, stores, and analyzes LLM inference telemetry in near real-time.

---

## Problem Statement

Modern AI applications generate thousands of inference events every day.

For every LLM call, engineering teams need answers to questions such as:

- Which model is causing latency spikes?
- Which customers consume the most tokens?
- Which prompts frequently fail?
- What is the error rate per provider?
- How much does each conversation cost?
- Which model should we route traffic to?

Most teams start with application logs scattered across services.

As usage grows, these logs become difficult to:

- Search
- Correlate
- Analyze
- Aggregate
- Scale

This project solves that problem by introducing a dedicated AI observability pipeline.

---

# Industry Inspiration

This architecture is inspired by systems built by:

- LangSmith
- Helicone
- Arize Phoenix
- Datadog
- OpenTelemetry
- OpenSearch Observability

Modern observability systems separate:

1. Data Producers
2. Ingestion Layer
3. Processing Layer
4. Storage Layer
5. Analytics Layer

This allows ingestion and storage systems to scale independently. :contentReference[oaicite:0]{index=0}

---

# Goals

### Functional Goals

- Multi-turn AI chatbot
- Inference metadata tracking
- Conversation tracking
- Centralized logging
- Real-time ingestion
- Historical analytics

### Non-Functional Goals

- Low request latency
- High write throughput
- Scalability
- Reliability
- Extensibility
- Fault tolerance

---

# System Architecture

```text
┌─────────────────────┐
│     React UI        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Chat API Service  │
│      FastAPI        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Logging SDK Wrapper │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Ingestion Service   │
│      FastAPI        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  In-Memory Buffer   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Batch Worker      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│     PostgreSQL      │
└─────────────────────┘
```

---

# Why This Architecture?

A naive implementation would write every log directly to the database.

```text
LLM Request
      ↓
Insert Log
      ↓
Commit
```

Problems:

- High database overhead
- Increased request latency
- Poor throughput
- Connection exhaustion under load

Instead, this system decouples ingestion from storage.

```text
Receive Log
      ↓
Buffer
      ↓
Batch Insert
```

This dramatically reduces:

- Database transactions
- Network overhead
- Disk flushes

while improving throughput.

Batching is a common optimization strategy in observability pipelines and telemetry systems. :contentReference[oaicite:1]{index=1}

---

# Core Components

## 1. Chat Service

Responsible for:

- Managing conversations
- Maintaining context
- Calling LLM providers
- Returning responses to users

The Chat Service never directly interacts with the database for observability data.

---

## 2. Logging SDK

A lightweight wrapper around LLM providers.

Responsibilities:

- Measure latency
- Track token usage
- Capture errors
- Capture metadata
- Generate traceable event payloads

Example:

```python
response = sdk.chat_completion(...)
```

Captured Metadata:

```json
{
  "provider": "openai",
  "model": "gpt-4.1",
  "latency_ms": 842,
  "prompt_tokens": 412,
  "completion_tokens": 201,
  "status": "success"
}
```

---

## 3. Ingestion Service

Central entry point for all telemetry.

Responsibilities:

- Validate payloads
- Parse metadata
- Enrich events
- Queue logs for processing

The ingestion service acts as the boundary between producers and storage.

---

## 4. In-Memory Buffer

Stores incoming logs temporarily before persistence.

Purpose:

- Absorb traffic bursts
- Reduce database load
- Improve write throughput

Logs are accumulated until:

```text
Batch Size Reached

OR

Flush Interval Reached
```

Example:

```python
MAX_BATCH_SIZE = 100
FLUSH_INTERVAL = 1 second
```

This mirrors batching strategies commonly used in telemetry pipelines. :contentReference[oaicite:2]{index=2}

---

## 5. Batch Worker

Background process responsible for:

- Reading buffered events
- Bulk inserting records
- Retrying failed writes

Pseudo Flow:

```text
Collect Logs
      ↓
Build Batch
      ↓
Bulk Insert
      ↓
Commit
```

---

## Database Design

### conversations

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id TEXT,
    created_at TIMESTAMP
);
```

---

### messages

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID,
    role TEXT,
    content TEXT,
    created_at TIMESTAMP
);
```

---

### inference_logs

```sql
CREATE TABLE inference_logs (
    id UUID PRIMARY KEY,

    conversation_id UUID,

    provider TEXT,
    model TEXT,

    latency_ms INTEGER,

    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,

    status TEXT,

    error_message TEXT,

    request_preview TEXT,
    response_preview TEXT,

    created_at TIMESTAMP
);
```

---

# Logging Strategy

Every LLM call generates a telemetry event.

Captured fields include:

| Category | Examples |
|-----------|-----------|
| Metadata | Provider, Model |
| Performance | Latency |
| Usage | Tokens |
| Reliability | Success, Failure |
| Context | Session ID |
| Cost | Token Consumption |

This enables:

- Cost monitoring
- Latency analysis
- Error analysis
- Usage analytics

---

# Scaling Considerations

## Current Implementation

Current architecture prioritizes simplicity.

```text
SDK
 ↓
HTTP
 ↓
Ingestion Service
 ↓
Buffer
 ↓
Batch Worker
 ↓
Postgres
```

Advantages:

- Simple deployment
- Easy debugging
- Minimal infrastructure
- Low operational overhead

Suitable for:

- Startups
- Internal tooling
- MVPs
- Assignments

---

# Future Architecture

As traffic increases:

```text
SDK
 ↓
Kafka
 ↓
Consumer Group
 ↓
ClickHouse
```

---

## Why Kafka?

Kafka does not make databases faster.

Kafka provides:

- Durability
- Backpressure handling
- Replayability
- Independent scaling

Benefits:

```text
Producer Scale ≠ Consumer Scale
```

If database writes slow down:

```text
Kafka stores backlog
Consumers catch up later
```

---

## Why ClickHouse?

At scale, observability workloads become:

```text
Write Heavy
Read Heavy
Analytics Heavy
```

Traditional PostgreSQL eventually becomes expensive.

ClickHouse is optimized for:

- High ingestion throughput
- Time-series queries
- Log analytics
- Aggregations

Large observability platforms commonly use columnar analytics stores for these workloads. :contentReference[oaicite:3]{index=3}

---

# Failure Handling

## Current Assumptions

### Ingestion Service Crash

Risk:

```text
Buffered logs may be lost.
```

Tradeoff accepted for MVP simplicity.

---

### Database Failure

Batch worker:

- Retries writes
- Applies exponential backoff
- Preserves batch until successful

---

### Provider Failure

Captured as:

```json
{
  "status": "failed",
  "error": "rate_limit_exceeded"
}
```

This ensures observability for failed requests.

---

# Future Reliability Improvements

## Kafka

Provides:

- Durable storage
- Event replay
- Consumer recovery

---

## Dead Letter Queue

For permanently failed events.

```text
Failed Event
      ↓
DLQ
      ↓
Manual Investigation
```

---

## Redis Streams

Alternative lightweight message broker.

Useful when:

- Kafka is operationally expensive
- Traffic is moderate

---

# Security Considerations

## PII Redaction

Future enhancement:

Before persistence:

```text
User Prompt
      ↓
PII Detection
      ↓
Redaction
      ↓
Storage
```

Examples:

```text
john@gmail.com
```

becomes

```text
[REDACTED_EMAIL]
```

---

## Data Retention

Future implementation:

```text
Hot Storage
  30 Days

Cold Storage
  S3/Object Storage
```

Reduces storage cost.

---

# Monitoring Metrics

The platform tracks:

### Throughput

```text
logs/sec
```

### Latency

```text
p50
p95
p99
```

### Reliability

```text
success rate
error rate
```

### Usage

```text
tokens consumed
requests per model
```

### Cost

```text
estimated spend per provider
```

---

# Tradeoffs Made

| Decision | Benefit | Tradeoff |
|-----------|----------|----------|
| In-Memory Buffer | Simple | Potential data loss |
| PostgreSQL | Easy setup | Limited analytical scale |
| HTTP Ingestion | Simple integration | No durability |
| Single Worker | Simplicity | Limited throughput |
| No Kafka | Lower complexity | No replayability |

---

# What I Would Build Next

Priority 1:

- Kafka
- Consumer Groups
- DLQ

Priority 2:

- ClickHouse
- Dashboards
- Cost Analytics

Priority 3:

- OpenTelemetry Integration
- Distributed Tracing
- Multi-Provider Routing

Priority 4:

- Kubernetes Deployment
- Horizontal Autoscaling
- Multi-Tenant Support

---

# Running Locally

```bash
docker-compose up --build
```

Services:

```text
Frontend      : localhost:3000
Chat API      : localhost:8000
Ingestion API : localhost:8001
Postgres      : localhost:5432
```

---

# Key Engineering Learnings

This project demonstrates:

- Event-driven thinking
- Observability design
- High-throughput ingestion
- Batching strategies
- Reliability tradeoffs
- Database scaling
- Future Kafka migration path
- AI infrastructure engineering

Rather than building another chatbot, this project focuses on the operational challenges of running AI systems in production.