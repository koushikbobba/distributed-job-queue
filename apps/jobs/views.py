import logging
from config.celery import app as celery_app
from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from users.permissions import IsOwnerOrAdmin
from workers.tasks import execute_job_task
from .filters import JobFilter
from .idempotency import IdempotencyHandler
from .models import Job, JobPriority, JobStatus
from .serializers import (
    JobCancelResponseSerializer,
    JobCreateSerializer,
    JobDetailSerializer,
    JobListSerializer,
)
from .throttling import AuthenticatedUserRateThrottle, JobSubmissionRateThrottle

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="List User Jobs",
        description="Retrieve a paginated, filtered, and sorted list of background jobs owned by the authenticated user.",
    ),
    retrieve=extend_schema(
        summary="Get Job Details",
        description="Retrieve complete job state including retry history, execution logs, and output results.",
    ),
)
class JobViewSet(viewsets.ModelViewSet):
    """
    CRUD and Management ViewSet for asynchronous background jobs.
    Enforces multi-tenant ownership, idempotency checks, and rate limiting.
    """

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    filterset_class = JobFilter
    ordering_fields = ["created_at", "completed_at", "priority", "execution_duration"]
    ordering = ["-created_at"]

    def get_queryset(self):
        # Multi-tenant isolation: regular users only see their own jobs
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Job.objects.all().select_related("result").prefetch_related("executions")
        return (
            Job.objects.filter(user=self.request.user)
            .select_related("result")
            .prefetch_related("executions")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return JobCreateSerializer
        elif self.action == "list":
            return JobListSerializer
        return JobDetailSerializer

    def get_throttles(self):
        if self.action == "create":
            return [JobSubmissionRateThrottle()]
        return [AuthenticatedUserRateThrottle()]

    @extend_schema(
        summary="Submit a Background Job",
        description="Creates a new job, persists it to PostgreSQL, and queues it in Celery. Supports 'Idempotency-Key' header.",
        parameters=[
            OpenApiParameter(
                name="Idempotency-Key",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=False,
                description="Unique token to prevent duplicate job creation upon retries.",
            ),
        ],
        responses={
            202: JobCreateSerializer,
            409: OpenApiResponse(description="Concurrent request in progress with same Idempotency-Key"),
            422: OpenApiResponse(description="Idempotency-Key reused with modified payload"),
            429: OpenApiResponse(description="Rate limit exceeded"),
        },
    )
    def create(self, request: Request, *args, **kwargs) -> Response:
        """Processes job submission with atomic DB transactions and idempotency checks."""
        return IdempotencyHandler.process_idempotent_request(
            request=request,
            view_func=self._create_job_internal,
        )

    def _create_job_internal(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        priority = serializer.validated_data.get("priority", JobPriority.MEDIUM)
        queue_name = f"{priority}_priority" if priority in ["high", "low"] else "default_priority"

        # ACID Transaction: Persist to DB, then dispatch task ONLY after commit
        with transaction.atomic():
            job = serializer.save(
                user=request.user,
                status=JobStatus.QUEUED,
            )

            # Critical: Dispatch to Celery ONLY when DB transaction successfully commits
            transaction.on_commit(
                lambda: execute_job_task.apply_async(
                    args=[str(job.id)],
                    queue=queue_name,
                )
            )

        logger.info(f"[API] Created and queued Job {job.id} for user {request.user.id} on queue '{queue_name}'")

        response = Response(
            JobCreateSerializer(job).data,
            status=status.HTTP_202_ACCEPTED,
        )
        response.job_instance = job
        return response

    @extend_schema(
        summary="Cancel a Job",
        description="Requests cancellation of a queued or running job.",
        responses={
            200: JobCancelResponseSerializer,
            400: OpenApiResponse(description="Job cannot be cancelled (e.g. already COMPLETED or FAILED)"),
        },
    )
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request: Request, pk=None) -> Response:
        """
        Cancels a queued or processing job.
        
        Engineering explanation on running task cancellation:
        - If QUEUED: Task is immediately marked CANCELLED in DB and ignored by workers.
        - If PROCESSING: POSIX processes cannot be safely terminated mid-instruction without risk
          of resource leaks or half-committed DB state. We set status=CANCELLED in DB and issue
          Celery task revocation, which cooperative worker handlers inspect.
        """
        job = self.get_object()

        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            return Response(
                {
                    "error": f"Cannot cancel job {job.id} because it is already in terminal state '{job.status}'.",
                    "status": job.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        previous_status = job.status
        with transaction.atomic():
            job.status = JobStatus.CANCELLED
            job.save(update_fields=["status", "updated_at"])

        # Attempt Celery task revocation
        try:
            celery_app.control.revoke(str(job.id), terminate=False)
        except Exception as exc:
            logger.warning(f"Could not signal Celery revocation for job {job.id}: {exc}")

        return Response(
            {
                "job_id": str(job.id),
                "status": JobStatus.CANCELLED,
                "previous_status": previous_status,
                "message": "Job successfully cancelled.",
                "details": (
                    "If the job was QUEUED, it will not be executed. If it was already PROCESSING, "
                    "cooperative execution checks will halt further processing."
                ),
            },
            status=status.HTTP_200_OK,
        )
