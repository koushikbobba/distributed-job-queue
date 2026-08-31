from django.contrib import admin
from .models import IdempotencyKey, Job, JobExecution, JobResult


class JobExecutionInline(admin.TabularInline):
    model = JobExecution
    extra = 0
    readonly_fields = (
        "worker_id",
        "attempt_number",
        "status",
        "error_traceback",
        "duration_seconds",
        "started_at",
        "finished_at",
    )
    can_delete = False


class JobResultInline(admin.StackedInline):
    model = JobResult
    extra = 0
    readonly_fields = ("result_data", "created_at")
    can_delete = False


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "job_type",
        "status",
        "priority",
        "current_retry_count",
        "created_at",
        "completed_at",
    )
    list_filter = ("status", "priority", "job_type", "created_at")
    search_fields = ("id", "user__email", "job_type", "worker_id")
    readonly_fields = (
        "id",
        "created_at",
        "started_at",
        "completed_at",
        "failed_at",
        "updated_at",
        "execution_duration",
    )
    inlines = [JobResultInline, JobExecutionInline]


@admin.register(JobExecution)
class JobExecutionAdmin(admin.ModelAdmin):
    list_display = ("id", "job", "attempt_number", "worker_id", "status", "duration_seconds", "started_at")
    list_filter = ("status", "started_at")
    search_fields = ("job__id", "worker_id")


@admin.register(JobResult)
class JobResultAdmin(admin.ModelAdmin):
    list_display = ("id", "job", "created_at")
    search_fields = ("job__id",)


@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):
    list_display = ("idempotency_key", "user", "job", "response_status_code", "created_at", "expires_at")
    search_fields = ("idempotency_key", "user__email", "job__id")
    list_filter = ("response_status_code", "created_at")
