import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class JobStatus(models.TextChoices):
    QUEUED = "QUEUED", "Queued"
    PROCESSING = "PROCESSING", "Processing"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"
    RETRYING = "RETRYING", "Retrying"
    CANCELLED = "CANCELLED", "Cancelled"


class JobPriority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


class JobType(models.TextChoices):
    SEND_EMAIL = "send_email", "Send Email"
    GENERATE_REPORT = "generate_report", "Generate Report"
    PROCESS_DATA = "process_data", "Process Data"
    SIMULATE_LONG_TASK = "simulate_long_task", "Simulate Long Task"


class OutboxStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PUBLISHED = "PUBLISHED", "Published"
    FAILED = "FAILED", "Failed"


class InvalidStateTransitionError(ValidationError):
    """Raised when an illegal state machine transition is attempted."""
    pass


class Job(models.Model):
    """Primary Job entity representing a unit of asynchronous work."""

    # Explicit State Machine Transition Rules
    VALID_TRANSITIONS = {
        JobStatus.QUEUED: {JobStatus.PROCESSING, JobStatus.CANCELLED},
        JobStatus.PROCESSING: {JobStatus.COMPLETED, JobStatus.RETRYING, JobStatus.FAILED, JobStatus.CANCELLED},
        JobStatus.RETRYING: {JobStatus.PROCESSING, JobStatus.CANCELLED, JobStatus.FAILED},
        JobStatus.COMPLETED: set(),  # Terminal
        JobStatus.FAILED: set(),     # Terminal
        JobStatus.CANCELLED: set(),  # Terminal
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="jobs",
        db_index=True,
    )
    job_type = models.CharField(
        max_length=64,
        choices=JobType.choices,
        help_text="Identifier for the task handler",
    )
    payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON payload containing parameters for task execution",
    )
    status = models.CharField(
        max_length=20,
        choices=JobStatus.choices,
        default=JobStatus.QUEUED,
        db_index=True,
    )
    priority = models.CharField(
        max_length=10,
        choices=JobPriority.choices,
        default=JobPriority.MEDIUM,
        db_index=True,
    )
    max_retries = models.PositiveIntegerField(
        default=3,
        help_text="Maximum allowed automatic retry attempts upon failure",
    )
    current_retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of retries executed so far",
    )
    worker_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Identity of the worker node processing this job",
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Last recorded error message or exception description",
    )
    execution_duration = models.FloatField(
        null=True,
        blank=True,
        help_text="Total execution duration in seconds",
    )

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "jobs"
        verbose_name = "job"
        verbose_name_plural = "jobs"
        ordering = ["-created_at"]
        indexes = [
            # High-performance composite index for user job list + status filter
            models.Index(
                fields=["user", "status", "-created_at"],
                name="idx_jobs_user_status_created",
            ),
            # Index for monitoring / sweeper tasks scanning active jobs
            models.Index(
                fields=["status", "priority"],
                name="idx_jobs_status_priority",
            ),
            # Index for job type metrics & querying
            models.Index(
                fields=["job_type", "status"],
                name="idx_jobs_type_status",
            ),
            # Index for finding stalled jobs in PROCESSING
            models.Index(
                fields=["status", "started_at"],
                name="idx_jobs_status_started",
            ),
        ]

    def __str__(self) -> str:
        return f"Job {self.id} [{self.job_type} - {self.status}]"

    @property
    def is_terminal(self) -> bool:
        """Indicates if the job has reached a final immutable state."""
        return self.status in {
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        }

    def transition_to(self, new_status: str, save: bool = True, **fields) -> bool:
        """
        Safely transitions the job to a new state if permitted by the finite state machine.
        Raises InvalidStateTransitionError on illegal transitions.
        """
        if self.status == new_status:
            return True

        allowed_next = self.VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed_next:
            raise InvalidStateTransitionError(
                f"Illegal state transition from '{self.status}' to '{new_status}' for Job {self.id}."
            )

        self.status = new_status
        for key, val in fields.items():
            setattr(self, key, val)

        if save:
            update_fields = ["status", "updated_at"] + list(fields.keys())
            self.save(update_fields=update_fields)
        return True


class JobResult(models.Model):
    """Stores the execution output data of a completed job."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.OneToOneField(
        Job,
        on_delete=models.CASCADE,
        related_name="result",
    )
    result_data = models.JSONField(
        default=dict,
        help_text="Structured output returned by the task handler",
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "job_results"
        verbose_name = "job result"
        verbose_name_plural = "job results"

    def __str__(self) -> str:
        return f"Result for Job {self.job_id}"


class JobExecution(models.Model):
    """Immutable audit trail of individual worker execution attempts (including retries)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="executions",
        db_index=True,
    )
    worker_id = models.CharField(max_length=255)
    attempt_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=JobStatus.choices)
    error_traceback = models.TextField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)

    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "job_executions"
        verbose_name = "job execution"
        verbose_name_plural = "job executions"
        ordering = ["attempt_number"]
        indexes = [
            models.Index(
                fields=["job", "attempt_number"],
                name="idx_exec_job_attempt",
            ),
        ]

    def __str__(self) -> str:
        return f"Execution attempt #{self.attempt_number} for Job {self.job_id} [{self.status}]"


class IdempotencyKey(models.Model):
    """Tracks idempotency keys per user to guarantee deduplication and prevent race conditions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="idempotency_keys",
    )
    idempotency_key = models.CharField(
        max_length=255,
        help_text="Client-provided unique transaction token",
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="idempotency_records",
    )
    request_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 hash of the request path and payload to detect tampering",
    )
    response_payload = models.JSONField(
        null=True,
        blank=True,
        help_text="Cached response payload to replay on duplicate requests",
    )
    response_status_code = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = "idempotency_keys"
        verbose_name = "idempotency key"
        verbose_name_plural = "idempotency keys"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "idempotency_key"],
                name="unique_user_idempotency_key",
            )
        ]
        indexes = [
            models.Index(fields=["expires_at"], name="idx_idemp_expires_at"),
        ]

    def __str__(self) -> str:
        return f"IdempotencyKey {self.idempotency_key} for User {self.user_id}"

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at


class OutboxMessage(models.Model):
    """
    Transactional Outbox pattern implementation:
    Guarantees at-least-once message publishing to Redis/Celery without dual-write race conditions.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="outbox_messages",
    )
    queue_name = models.CharField(max_length=64, default="default_priority")
    payload = models.JSONField(default=dict)
    status = models.CharField(
        max_length=20,
        choices=OutboxStatus.choices,
        default=OutboxStatus.PENDING,
        db_index=True,
    )
    retry_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "outbox_messages"
        verbose_name = "outbox message"
        verbose_name_plural = "outbox messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"], name="idx_outbox_status_created"),
        ]

    def __str__(self) -> str:
        return f"OutboxMessage {self.id} for Job {self.job_id} [{self.status}]"
