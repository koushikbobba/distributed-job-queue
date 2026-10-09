from prometheus_client import Counter, Gauge, Histogram

# Metric Definitions

JOBS_TOTAL = Counter(
    "job_queue_jobs_total",
    "Total count of jobs processed through the queue",
    ["job_type", "status", "priority"],
)

JOB_EXECUTION_SECONDS = Histogram(
    "job_queue_execution_duration_seconds",
    "Histogram of job execution duration in seconds",
    ["job_type"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0),
)

JOB_QUEUE_LATENCY_SECONDS = Histogram(
    "job_queue_latency_seconds",
    "Time spent by a job waiting in queue before worker pickup",
    ["job_type"],
    buckets=(0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

JOB_RETRIES_TOTAL = Counter(
    "job_queue_retries_total",
    "Total count of retry attempts triggered",
    ["job_type"],
)

ACTIVE_JOBS_GAUGE = Gauge(
    "job_queue_active_jobs",
    "Current number of jobs actively being executed across workers",
    ["job_type"],
)

IDEMPOTENCY_HITS_TOTAL = Counter(
    "job_queue_idempotency_cache_hits_total",
    "Total number of duplicate requests intercepted by idempotency guard",
)

RATE_LIMIT_EXCEEDED_TOTAL = Counter(
    "job_queue_rate_limit_exceeded_total",
    "Total number of requests rejected due to rate limits (HTTP 429)",
    ["endpoint"],
)
