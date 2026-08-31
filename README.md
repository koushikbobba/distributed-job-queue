# Distributed Job Queue & Task Processing System

A production-grade, fault-tolerant asynchronous task execution engine and distributed job queue built with **Python, Django REST Framework, Celery, Redis, and PostgreSQL**. 

Features multi-priority scheduling, distributed locking, atomic state transitions, at-least-once delivery guarantees, idempotency deduplication, exponential backoff retries with jitter, Prometheus telemetry, Grafana dashboards, and Docker orchestration.

---

## 📐 Architecture Overview

```mermaid
flowchart TD
    Client(["HTTP Client / Webhook"])
    
    subgraph APILayer ["Django API Layer (Horizontally Scalable)"]
        API["Django REST Framework"]
        Auth["JWT Authenticator & Token Blacklist"]
        Throttle["Redis Rate Limiter (100 req/min, 10 jobs/min)"]
        Idem["Idempotency Guard (SHA-256 + Unique DB Constraint)"]
    end

    subgraph StateAndCoordination ["State & Coordination Layer"]
        PG[("PostgreSQL\n- Jobs (State Machine & JSONB Payloads)\n- JobExecutions (Audit History)\n- JobResults (Outputs)\n- IdempotencyKeys")]
        RedisCoord[("Redis 7.0\n- Priority Message Queues\n- Distributed Locks (SETNX + Lua)\n- Rate Limit Buckets")]
    end

    subgraph CeleryPool ["Celery Distributed Worker Pool"]
        WorkerHigh["High-Priority Worker Node(s)"]
        WorkerDefault["Default / Low-Priority Worker Node(s)"]
    end

    subgraph Observability ["Observability & Telemetry"]
        Prom["Prometheus Engine"]
        Grafana["Grafana Visual Dashboard"]
    end

    Client -->|1. POST /api/jobs/ (with Idempotency-Key)| API
    API --> Auth
    Auth --> Throttle
    Throttle --> Idem
    Idem -->|2. ACID Insert Job (State: QUEUED)| PG
    API -->|3. Publish Job ID to Redis Queue (on_commit)| RedisCoord
    API -->|4. HTTP 202 Accepted| Client

    RedisCoord -->|5. BRPOP Tasks in Priority Order| WorkerHigh
    RedisCoord -->|5. BRPOP Tasks| WorkerDefault

    WorkerHigh -->|6. Atomic Acquire Lock (SETNX)| RedisCoord
    WorkerHigh -->|7. Transition State to PROCESSING| PG
    WorkerHigh -->|8. Execute Pluggable Task Handler| WorkerHigh
    WorkerHigh -->|9. Update State to COMPLETED / RETRYING / FAILED| PG
    WorkerHigh -->|10. Safe Release Lock (Lua Script)| RedisCoord

    API -.->|Expose /metrics| Prom
    Prom --> Grafana
```

---

## 🛠️ Technology Stack

- **Backend Framework:** Python 3.11, Django 4.2+, Django REST Framework (DRF)
- **Database:** PostgreSQL 15 (JSONB payloads, composite indexing, foreign key constraints)
- **Task Queue & Coordination:** Celery 5.3+, Redis 7.0 (Message broker, distributed locks, rate limiting)
- **Authentication & Security:** JWT (JSON Web Tokens) with cryptographic rotation and database blacklisting
- **Observability:** Prometheus, `django-prometheus`, Grafana, structured JSON logging
- **Infrastructure:** Docker, Docker Compose, AWS ECS Fargate, AWS RDS PostgreSQL, AWS ElastiCache
- **Testing & Quality:** Pytest, `pytest-django`, Locust (Load testing)
- **API Documentation:** OpenAPI 3.0 / Swagger UI via `drf-spectacular`

---

## 🚀 Key Distributed Systems Features

### 1. Atomic Job State Machine
Jobs transition through a strictly enforced finite state machine:
`QUEUED` ➔ `PROCESSING` ➔ `COMPLETED` | `RETRYING` ➔ `FAILED` | `CANCELLED`

### 2. At-Least-Once Delivery & Worker Crash Recovery
Configured with `task_acks_late = True` and `task_reject_on_worker_lost = True`. If a worker process is terminated by the OS (OOM / power loss), unacknowledged messages are automatically returned to the Redis queue and re-delivered to another active worker.

### 3. Distributed Locking with TTL & Lua Verification
Prevents duplicate concurrent execution of identical jobs across worker instances:
- **Acquisition:** Redis `SET lock:job:<id> <token> NX PX 120000`
- **Safe Release:** Atomic Lua script verifying token ownership before deleting the key to prevent releasing expired locks acquired by other workers.

### 4. Idempotency Key Deduplication (SHA-256 Hashing)
Clients can supply an `Idempotency-Key: <uuid>` header. The system hashes the request endpoint and payload with SHA-256 and enforces uniqueness at the PostgreSQL database level. Duplicate submissions return the cached HTTP response instantly (`X-Cache-Lookup: HIT-Idempotency`) without spawning redundant jobs.

### 5. Multi-Priority Queues
Three distinct priority bands: `high_priority`, `default_priority`, `low_priority`. Workers perform priority blocking pops (`BRPOP`) draining high-priority tasks before lower bands.

### 6. Exponential Backoff with Jitter
Failed jobs retry with randomized exponential backoff ($2^{\text{retry\_count}} \times \text{base\_delay} + \text{jitter}$) to eliminate thundering herd storms on downstream services.

---

## 📦 Quick Start (Local Setup via Docker)

### 1. Clone & Configure Environment
```bash
git clone https://github.com/your-username/distributed-job-queue.git
cd distributed-job-queue
cp .env.example .env
```

### 2. Build & Launch Containers
```bash
docker compose up --build -d
```

### 3. Verify Running Services
```bash
docker compose ps
```

| Service | Port | Description |
| :--- | :--- | :--- |
| **API Server** | `http://localhost:8000` | Django REST Framework API |
| **Swagger UI** | `http://localhost:8000/api/docs/` | Interactive OpenAPI 3 Documentation |
| **Prometheus** | `http://localhost:9090` | Time-series metrics engine |
| **Grafana** | `http://localhost:3000` | Real-time monitoring dashboard (`admin` / `admin`) |
| **PostgreSQL** | `localhost:5432` | Relational Database |
| **Redis** | `localhost:6379` | Cache, Lock engine & Message Broker |

---

## 📡 API Usage & Example Requests

### 1. User Registration & Login
```bash
# Register User
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "engineer@example.com",
    "password": "ProductionPassword123!",
    "password_confirm": "ProductionPassword123!"
  }'

# Login to get JWT Bearer Token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "engineer@example.com",
    "password": "ProductionPassword123!"
  }'
```

### 2. Submit a Background Job (with Idempotency Key)
```bash
curl -X POST http://localhost:8000/api/jobs/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: txn-7c9b-4401" \
  -d '{
    "job_type": "generate_report",
    "priority": "high",
    "payload": {
      "customer_id": 108,
      "report_type": "monthly"
    },
    "max_retries": 3
  }'
```
**Response (202 Accepted):**
```json
{
  "id": "7b8e722a-cf39-4458-967c-d652ce649987",
  "job_type": "generate_report",
  "priority": "high",
  "payload": { "customer_id": 108, "report_type": "monthly" },
  "max_retries": 3,
  "status": "QUEUED",
  "created_at": "2026-08-31T12:00:00Z"
}
```

### 3. Check Job Status & Execution History
```bash
curl -X GET http://localhost:8000/api/jobs/7b8e722a-cf39-4458-967c-d652ce649987/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```
**Response (200 OK):**
```json
{
  "id": "7b8e722a-cf39-4458-967c-d652ce649987",
  "job_type": "generate_report",
  "status": "COMPLETED",
  "priority": "high",
  "current_retry_count": 0,
  "worker_id": "worker-prod-node-01-a7b4",
  "execution_duration": 1.02,
  "created_at": "2026-08-31T12:00:00Z",
  "started_at": "2026-08-31T12:00:01Z",
  "completed_at": "2026-08-31T12:00:02Z",
  "result": {
    "report_url": "https://s3.amazonaws.com/reports/108_monthly.pdf",
    "customer_id": 108,
    "records_analyzed": 1420
  },
  "executions": [
    {
      "attempt_number": 1,
      "worker_id": "worker-prod-node-01-a7b4",
      "status": "COMPLETED",
      "duration_seconds": 1.02,
      "started_at": "2026-08-31T12:00:01Z",
      "finished_at": "2026-08-31T12:00:02Z"
    }
  ]
}
```

---

## 🧪 Automated Testing

Execute the comprehensive test suite:
```bash
# Run all unit and integration tests
pytest

# Run tests with test coverage reporting
pytest --cov=apps --cov-report=term-missing
```

### Load Testing with Locust
```bash
locust -f tests/load_testing/locustfile.py --host=http://localhost:8000
```
Open `http://localhost:8089` to configure user concurrency and measure request throughput and latency percentiles.

---

## 💡 Engineering Challenges & Solutions

### 1. The Post-Commit Message Dispatch Race Condition
- **Problem:** If a Celery task is dispatched (`task.delay(job_id)`) *inside* an open Django database transaction, a fast worker can pop the task from Redis and query PostgreSQL before the web server's transaction has committed, resulting in an immediate `Job.DoesNotExist` crash.
- **Solution:** Utilized Django's `transaction.on_commit(lambda: task.apply_async(...))` callback hook. The message is published to the Redis broker **only after** PostgreSQL has successfully committed the row to disk.

### 2. Preventing Concurrent Duplicate Execution with Distributed Locks
- **Problem:** Under network partitions or Celery retry redeliveries, two worker threads can simultaneously pick up the same job ID and execute side-effect-heavy tasks (e.g. charging a credit card twice).
- **Solution:** Implemented a Redis-based distributed lock using atomic `SET key token NX PX <ttl_ms>`. A Lua script validates token ownership upon release, preventing a slow worker from deleting a lock that had already expired and been acquired by another worker.

### 3. Idempotency Key Deduplication & Payload Tampering
- **Problem:** If a client retries a failed HTTP request or a rogue client attempts to replay an old idempotency key with a modified payload, standard key-value deduplication fails to detect tampering.
- **Solution:** We compute a deterministic SHA-256 hash of `(user_id, request_path, request_body)` and store it alongside a PostgreSQL unique constraint on `(user_id, idempotency_key)`. If the key is reused with a modified payload, the API rejects the request with `HTTP 422 Unprocessable Entity`.

### 4. Heterogeneous Workloads & Worker Starvation
- **Problem:** By default, Celery prefetches multiple tasks per worker (`worker_prefetch_multiplier = 4`). If one worker reserves a batch containing several 30-second heavy jobs, subsequent 100ms fast jobs in the same batch get blocked while other worker processes sit idle.
- **Solution:** Enforced `worker_prefetch_multiplier = 1` and `task_acks_late = True`. Workers fetch exactly one task at a time, ensuring fair, responsive distribution across heterogeneous workloads.

### 5. At-Least-Once Delivery Worker Crash Recovery
- **Problem:** Default task queues acknowledge messages immediately upon receiving them (`acks_late=False`). If a worker container experiences an unexpected SIGKILL or OOM event mid-execution, the task is lost forever with no record.
- **Solution:** Enabled `task_acks_late = True` and `task_reject_on_worker_lost = True` combined with an immutable `JobExecution` attempt audit log table. If a worker dies, Redis requeues the task for another worker, and the audit trail preserves the failure history.
