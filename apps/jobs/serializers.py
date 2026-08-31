from rest_framework import serializers

from workers.registry import JobRegistry
from .models import Job, JobExecution, JobPriority, JobResult, JobStatus, JobType


class JobResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobResult
        fields = ("id", "result_data", "created_at")


class JobExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobExecution
        fields = (
            "id",
            "attempt_number",
            "worker_id",
            "status",
            "error_traceback",
            "duration_seconds",
            "started_at",
            "finished_at",
        )


class JobCreateSerializer(serializers.ModelSerializer):
    job_type = serializers.ChoiceField(choices=JobType.choices)
    priority = serializers.ChoiceField(choices=JobPriority.choices, default=JobPriority.MEDIUM)
    payload = serializers.JSONField(required=False, default=dict)
    max_retries = serializers.IntegerField(min_value=0, max_value=10, default=3)

    class Meta:
        model = Job
        fields = ("id", "job_type", "payload", "priority", "max_retries", "status", "created_at")
        read_only_fields = ("id", "status", "created_at")

    def validate_job_type(self, value: str) -> str:
        supported_types = JobRegistry.get_supported_types()
        if value not in supported_types:
            raise serializers.ValidationError(
                f"Unsupported job_type '{value}'. Supported types: {supported_types}"
            )
        return value


class JobDetailSerializer(serializers.ModelSerializer):
    result = JobResultSerializer(read_only=True)
    executions = JobExecutionSerializer(many=True, read_only=True)

    class Meta:
        model = Job
        fields = (
            "id",
            "job_type",
            "status",
            "priority",
            "payload",
            "max_retries",
            "current_retry_count",
            "worker_id",
            "error_message",
            "execution_duration",
            "created_at",
            "started_at",
            "completed_at",
            "failed_at",
            "result",
            "executions",
        )


class JobListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = (
            "id",
            "job_type",
            "status",
            "priority",
            "current_retry_count",
            "worker_id",
            "execution_duration",
            "created_at",
            "completed_at",
        )


class JobCancelResponseSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    status = serializers.CharField()
    message = serializers.CharField()
    details = serializers.CharField()
