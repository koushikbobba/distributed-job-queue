import logging
import random
import socket
import time
import traceback
from typing import Optional
from celery import shared_task
from django.db import transaction
from django.utils import timezone

from jobs.models import Job, JobExecution, JobPriority, JobResult, JobStatus
from monitoring.metrics import (
    ACTIVE_JOBS_GAUGE,
    JOB_EXECUTION_SECONDS,
    JOB_RETRIES_TOTAL,
    JOBS_TOTAL,
    JOB_QUEUE_LATENCY_SECONDS,
)
from .locking import RedisDistributedLock, DistributedLockException
from .registry import JobRegistry

logger = logging.getLogger(__name__)


def calculate_backoff_with_jitter(retry_count: int, base_delay: float = 2.0, max_delay: float = 300.0) -> float:
    """Calculates exponential backoff with full jitter to avoid the thundering herd problem."""
    exponential_delay = min(max_delay, base_delay * (2 ** retry_count))
    jitter = random.uniform(0, exponential_delay)
    return round(jitter, 2)


@shared_task(
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
    max_retries=None,
)
def execute_job_task(self, job_id: str, attempt_number: int = 1) -> dict:
    """
    Main Celery worker entrypoint for processing an asynchronous job.
    Enforces distributed locking, idempotency checks, FSM state transitions,
    OCC optimistic concurrency, and exponential backoff retry semantics.
    """
    worker_node_id = f"worker-{socket.gethostname()}-{self.request.id[:8] if self.request.id else 'local'}"
    start_time = time.monotonic()
    job_type_label = "unknown"

    logger.info(f"[Worker] Received job {job_id} (Attempt #{attempt_number}) on {worker_node_id}")

    # 1. Fetch Job from PostgreSQL
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        logger.error(f"[Worker] Job {job_id} does not exist in PostgreSQL. Dropping task.")
        return {"status": "dropped", "reason": "job_not_found"}

    job_type_label = job.job_type

    # 2. Check if Job was already cancelled before execution began
    if job.status == JobStatus.CANCELLED:
        logger.info(f"[Worker] Job {job_id} was CANCELLED before processing started. Skipping.")
        return {"status": "skipped", "reason": "job_cancelled"}

    if job.status == JobStatus.COMPLETED:
        logger.warning(f"[Worker] Job {job_id} is already COMPLETED. Skipping duplicate execution.")
        return {"status": "skipped", "reason": "already_completed"}

    # Record Queue Latency Metric (Time spent waiting in queue)
    if job.created_at:
        queue_latency = (timezone.now() - job.created_at).total_seconds()
        JOB_QUEUE_LATENCY_SECONDS.labels(job_type=job_type_label).observe(max(0.0, queue_latency))

    # 3. Acquire Distributed Lock (prevents concurrent duplicate execution across workers)
    try:
        lock = RedisDistributedLock(key=f"job:{job_id}", ttl_seconds=120)
        if not lock.acquire(blocking=False):
            logger.warning(f"[Worker] Job {job_id} is currently locked by another worker. Skipping concurrent execution.")
            return {"status": "locked", "reason": "concurrent_lock_active"}
    except DistributedLockException as exc:
        logger.error(f"[Worker] Lock error for Job {job_id}: {exc}")
        return {"status": "lock_failed", "reason": str(exc)}

    ACTIVE_JOBS_GAUGE.labels(job_type=job_type_label).inc()
    execution_record: Optional[JobExecution] = None

    try:
        # 4. Atomic Transition to PROCESSING with Optimistic Lock & FSM check
        with transaction.atomic():
            # Lock row for update to prevent concurrent cancel race
            job = Job.objects.select_for_update().get(id=job_id)
            if job.status == JobStatus.CANCELLED:
                logger.info(f"[Worker] Job {job_id} was CANCELLED right before processing.")
                return {"status": "skipped", "reason": "cancelled"}

            job.transition_to(
                JobStatus.PROCESSING,
                save=True,
                worker_id=worker_node_id,
                started_at=job.started_at or timezone.now(),
            )

            # Create Execution Audit Record
            execution_record = JobExecution.objects.create(
                job=job,
                worker_id=worker_node_id,
                attempt_number=attempt_number,
                status=JobStatus.PROCESSING,
                started_at=timezone.now(),
            )

        # 5. Execute Business Logic via Pluggable Handler
        handler = JobRegistry.get_handler(job.job_type)
        result_data = handler.execute(job=job, payload=job.payload)

        # 6. Success Handling & State Transition to COMPLETED with Race Guard
        duration = round(time.monotonic() - start_time, 3)
        with transaction.atomic():
            job = Job.objects.select_for_update().get(id=job_id)
            if job.status == JobStatus.CANCELLED:
                logger.warning(f"[Worker] Job {job_id} was cancelled during execution. Discarding output.")
                if execution_record:
                    execution_record.status = JobStatus.CANCELLED
                    execution_record.duration_seconds = duration
                    execution_record.finished_at = timezone.now()
                    execution_record.save(update_fields=["status", "duration_seconds", "finished_at"])
                return {"status": "aborted", "reason": "cancelled_mid_execution"}

            job.transition_to(
                JobStatus.COMPLETED,
                save=True,
                completed_at=timezone.now(),
                execution_duration=duration,
                error_message=None,
            )

            JobResult.objects.update_or_create(
                job=job,
                defaults={"result_data": result_data, "created_at": timezone.now()},
            )

            if execution_record:
                execution_record.status = JobStatus.COMPLETED
                execution_record.duration_seconds = duration
                execution_record.finished_at = timezone.now()
                execution_record.save(update_fields=["status", "duration_seconds", "finished_at"])

        # Record Telemetry
        JOBS_TOTAL.labels(job_type=job.job_type, status="COMPLETED", priority=job.priority).inc()
        JOB_EXECUTION_SECONDS.labels(job_type=job.job_type).observe(duration)
        logger.info(f"[Worker] Job {job_id} COMPLETED successfully in {duration}s")
        return {"status": "completed", "result": result_data}

    except Exception as exc:
        duration = round(time.monotonic() - start_time, 3)
        error_msg = str(exc)
        tb_str = traceback.format_exc()
        logger.error(f"[Worker] Job {job_id} failed on attempt #{attempt_number}: {error_msg}\n{tb_str}")

        # 7. Retry or Permanent Failure Logic with FSM transition
        with transaction.atomic():
            job = Job.objects.select_for_update().get(id=job_id)
            if job.status == JobStatus.CANCELLED:
                logger.info(f"[Worker] Failed Job {job_id} was already marked CANCELLED.")
                return {"status": "aborted", "reason": "cancelled"}

            job.current_retry_count += 1
            job.error_message = f"{error_msg}\n{tb_str[:500]}"
            job.execution_duration = duration

            if execution_record:
                execution_record.status = JobStatus.FAILED
                execution_record.error_traceback = tb_str
                execution_record.duration_seconds = duration
                execution_record.finished_at = timezone.now()
                execution_record.save(update_fields=["status", "error_traceback", "duration_seconds", "finished_at"])

            if job.current_retry_count <= job.max_retries:
                # Schedule Exponential Backoff Retry
                job.transition_to(
                    JobStatus.RETRYING,
                    save=True,
                    current_retry_count=job.current_retry_count,
                    error_message=job.error_message,
                    execution_duration=job.execution_duration,
                )

                countdown = calculate_backoff_with_jitter(job.current_retry_count)
                JOB_RETRIES_TOTAL.labels(job_type=job.job_type).inc()
                JOBS_TOTAL.labels(job_type=job.job_type, status="RETRYING", priority=job.priority).inc()

                logger.info(f"[Worker] Retrying Job {job_id} in {countdown}s (Attempt {job.current_retry_count}/{job.max_retries})")
                
                queue_name = f"{job.priority}_priority" if job.priority in ["high", "low"] else "default_priority"
                
                execute_job_task.apply_async(
                    args=[str(job.id), attempt_number + 1],
                    countdown=countdown,
                    queue=queue_name,
                )
                return {"status": "retrying", "attempt": attempt_number, "countdown": countdown}
            else:
                # Max Retries Exhausted -> Permanent FAILED state
                job.transition_to(
                    JobStatus.FAILED,
                    save=True,
                    failed_at=timezone.now(),
                    current_retry_count=job.current_retry_count,
                    error_message=job.error_message,
                    execution_duration=job.execution_duration,
                )

                JOBS_TOTAL.labels(job_type=job.job_type, status="FAILED", priority=job.priority).inc()
                logger.error(f"[Worker] Job {job_id} permanently FAILED after {job.current_retry_count} retries.")
                return {"status": "failed", "error": error_msg}

    finally:
        ACTIVE_JOBS_GAUGE.labels(job_type=job_type_label).dec()
        lock.release()


@shared_task
def sweep_stalled_jobs(stalled_threshold_minutes: int = 30) -> dict:
    """
    Reaper / Stalled Job Recovery sweeper task:
    Identifies jobs stuck in PROCESSING where the worker died or lost lock,
    recovering them back to RETRYING or FAILED state.
    """
    cutoff = timezone.now() - timezone.timedelta(minutes=stalled_threshold_minutes)
    stalled_jobs = Job.objects.filter(
        status=JobStatus.PROCESSING,
        updated_at__lt=cutoff,
    )

    recovered = 0
    for job in stalled_jobs:
        logger.warning(f"[Sweeper] Recovering stalled job {job.id} (last updated: {job.updated_at})")
        with transaction.atomic():
            if job.current_retry_count < job.max_retries:
                job.current_retry_count += 1
                job.status = JobStatus.RETRYING
                job.error_message = "Recovered by background sweeper: worker timed out or crashed."
                job.save(update_fields=["status", "current_retry_count", "error_message", "updated_at"])
                
                queue_name = f"{job.priority}_priority" if job.priority in ["high", "low"] else "default_priority"
                execute_job_task.apply_async(args=[str(job.id)], queue=queue_name)
            else:
                job.status = JobStatus.FAILED
                job.failed_at = timezone.now()
                job.error_message = "Failed: Worker crashed and max retries exhausted."
                job.save(update_fields=["status", "failed_at", "error_message", "updated_at"])
            recovered += 1

    return {"recovered_count": recovered}


@shared_task
def process_outbox_messages(batch_size: int = 100) -> dict:
    """
    Transactional Outbox forwarder:
    Guarantees that pending outbox messages are published to Redis.
    """
    from jobs.models import OutboxMessage, OutboxStatus

    pending_messages = OutboxMessage.objects.filter(status=OutboxStatus.PENDING).select_related("job")[:batch_size]
    published_count = 0

    for msg in pending_messages:
        try:
            execute_job_task.apply_async(
                args=[str(msg.job_id)],
                queue=msg.queue_name,
            )
            msg.status = OutboxStatus.PUBLISHED
            msg.published_at = timezone.now()
            msg.save(update_fields=["status", "published_at"])
            published_count += 1
        except Exception as exc:
            msg.retry_count += 1
            msg.error_message = str(exc)
            if msg.retry_count > 5:
                msg.status = OutboxStatus.FAILED
            msg.save(update_fields=["retry_count", "error_message", "status"])

    return {"published_count": published_count}
