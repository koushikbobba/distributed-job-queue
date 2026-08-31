import uuid
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Job",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "job_type",
                    models.CharField(
                        choices=[
                            ("send_email", "Send Email"),
                            ("generate_report", "Generate Report"),
                            ("process_data", "Process Data"),
                            ("simulate_long_task", "Simulate Long Task"),
                        ],
                        help_text="Identifier for the task handler",
                        max_length=64,
                    ),
                ),
                (
                    "payload",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="JSON payload containing parameters for task execution",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("QUEUED", "Queued"),
                            ("PROCESSING", "Processing"),
                            ("COMPLETED", "Completed"),
                            ("FAILED", "Failed"),
                            ("RETRYING", "Retrying"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        db_index=True,
                        default="QUEUED",
                        max_length=20,
                    ),
                ),
                (
                    "priority",
                    models.CharField(
                        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")],
                        db_index=True,
                        default="medium",
                        max_length=10,
                    ),
                ),
                (
                    "max_retries",
                    models.PositiveIntegerField(
                        default=3,
                        help_text="Maximum allowed automatic retry attempts upon failure",
                    ),
                ),
                (
                    "current_retry_count",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Number of retries executed so far",
                    ),
                ),
                (
                    "worker_id",
                    models.CharField(
                        blank=True,
                        help_text="Identity of the worker node processing this job",
                        max_length=255,
                        null=True,
                    ),
                ),
                (
                    "error_message",
                    models.TextField(
                        blank=True,
                        help_text="Last recorded error message or exception description",
                        null=True,
                    ),
                ),
                (
                    "execution_duration",
                    models.FloatField(
                        blank=True,
                        help_text="Total execution duration in seconds",
                        null=True,
                    ),
                ),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("failed_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="jobs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "job",
                "verbose_name_plural": "jobs",
                "db_table": "jobs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="JobResult",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "result_data",
                    models.JSONField(
                        default=dict,
                        help_text="Structured output returned by the task handler",
                    ),
                ),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "job",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="result",
                        to="jobs.job",
                    ),
                ),
            ],
            options={
                "verbose_name": "job result",
                "verbose_name_plural": "job results",
                "db_table": "job_results",
            },
        ),
        migrations.CreateModel(
            name="JobExecution",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("worker_id", models.CharField(max_length=255)),
                ("attempt_number", models.PositiveIntegerField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("QUEUED", "Queued"),
                            ("PROCESSING", "Processing"),
                            ("COMPLETED", "Completed"),
                            ("FAILED", "Failed"),
                            ("RETRYING", "Retrying"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        max_length=20,
                    ),
                ),
                ("error_traceback", models.TextField(blank=True, null=True)),
                ("duration_seconds", models.FloatField(blank=True, null=True)),
                ("started_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                (
                    "job",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="executions",
                        to="jobs.job",
                    ),
                ),
            ],
            options={
                "verbose_name": "job execution",
                "verbose_name_plural": "job executions",
                "db_table": "job_executions",
                "ordering": ["attempt_number"],
            },
        ),
        migrations.CreateModel(
            name="IdempotencyKey",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "idempotency_key",
                    models.CharField(
                        help_text="Client-provided unique transaction token",
                        max_length=255,
                    ),
                ),
                (
                    "request_hash",
                    models.CharField(
                        help_text="SHA-256 hash of the request path and payload to detect tampering",
                        max_length=64,
                    ),
                ),
                (
                    "response_payload",
                    models.JSONField(
                        blank=True,
                        help_text="Cached response payload to replay on duplicate requests",
                        null=True,
                    ),
                ),
                ("response_status_code", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("expires_at", models.DateTimeField(db_index=True)),
                (
                    "job",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="idempotency_records",
                        to="jobs.job",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="idempotency_keys",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "idempotency key",
                "verbose_name_plural": "idempotency keys",
                "db_table": "idempotency_keys",
            },
        ),
        migrations.AddIndex(
            model_name="job",
            index=models.Index(
                fields=["user", "status", "-created_at"],
                name="idx_jobs_user_status_created",
            ),
        ),
        migrations.AddIndex(
            model_name="job",
            index=models.Index(
                fields=["status", "priority"],
                name="idx_jobs_status_priority",
            ),
        ),
        migrations.AddIndex(
            model_name="job",
            index=models.Index(
                fields=["job_type", "status"],
                name="idx_jobs_type_status",
            ),
        ),
        migrations.AddIndex(
            model_name="jobexecution",
            index=models.Index(
                fields=["job", "attempt_number"],
                name="idx_exec_job_attempt",
            ),
        ),
        migrations.AddIndex(
            model_name="idempotencykey",
            index=models.Index(fields=["expires_at"], name="idx_idemp_expires_at"),
        ),
        migrations.AddConstraint(
            model_name="idempotencykey",
            constraint=models.UniqueConstraint(
                fields=["user", "idempotency_key"],
                name="unique_user_idempotency_key",
            ),
        ),
    ]
