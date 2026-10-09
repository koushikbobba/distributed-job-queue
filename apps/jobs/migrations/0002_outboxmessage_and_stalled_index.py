import uuid
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="OutboxMessage",
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
                ("queue_name", models.CharField(default="default_priority", max_length=64)),
                ("payload", models.JSONField(default=dict)),
                (
                    "status",
                    models.CharField(
                        choices=[("PENDING", "Pending"), ("PUBLISHED", "Published"), ("FAILED", "Failed")],
                        db_index=True,
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("retry_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True, null=True)),
                (
                    "job",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="outbox_messages",
                        to="jobs.job",
                    ),
                ),
            ],
            options={
                "verbose_name": "outbox message",
                "verbose_name_plural": "outbox messages",
                "db_table": "outbox_messages",
                "ordering": ["created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="job",
            index=models.Index(fields=["status", "started_at"], name="idx_jobs_status_started"),
        ),
        migrations.AddIndex(
            model_name="outboxmessage",
            index=models.Index(fields=["status", "created_at"], name="idx_outbox_status_created"),
        ),
    ]
