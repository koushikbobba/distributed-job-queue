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
from .models import Job, JobPriority, JobStatus, OutboxMessage, OutboxStatus
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
    Enforces multi-tenant ownership, idempotency checks, transactional outbox, and rate limiting.
    """

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    filterset_class = JobFilter
    ordering_fields = ["created_at", "completed_at", "priority", "execution_duration"]
    ordering = ["-created_at"]

    def get_queryset(self):
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
        description="Creates a new job, persists it to PostgreSQL, and queues it in Celery with Transactional Outbox guarantee.",
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
        return IdempotencyHandler.process_idempotent_request(
            request=request,
            view_func=self._create_job_internal,
        )

    def _create_job_internal(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        priority = serializer.validated_data.get("priority", JobPriority.MEDIUM)
        queue_name = f"{priority}_priority" if priority in ["high", "low"] else "default_priority"

        # ACID Transaction: Persist Job + Transactional Outbox row in single commit
        with transaction.atomic():
            job = serializer.save(
                user=request.user,
                status=JobStatus.QUEUED,
            )

            outbox_entry = OutboxMessage.objects.create(
                job=job,
                queue_name=queue_name,
                payload=job.payload,
                status=OutboxStatus.PENDING,
            )

            # Direct fast-path dispatch upon commit; outbox reaper handles worker death/network split
            transaction.on_commit(
                lambda: self._dispatch_and_mark_outbox(job.id, queue_name, outbox_entry.id)
            )

        logger.info(f"[API] Created and queued Job {job.id} for user {request.user.id} on queue '{queue_name}'")

        response = Response(
            JobCreateSerializer(job).data,
            status=status.HTTP_202_ACCEPTED,
        )
        response.job_instance = job
        return response

    @staticmethod
    def _dispatch_and_mark_outbox(job_id, queue_name, outbox_id):
        try:
            execute_job_task.apply_async(
                args=[str(job_id)],
                queue=queue_name,
            )
            OutboxMessage.objects.filter(id=outbox_id).update(
                status=OutboxStatus.PUBLISHED,
                published_at=timezone.now(),
            )
        except Exception as exc:
            logger.error(f"Failed direct dispatch for Outbox {outbox_id}: {exc}. Fallback sweeper will publish.")

    @extend_schema(
        summary="Cancel a Job",
        description="Requests cancellation of a queued or running job.",
        responses={
            200: JobCancelResponseSerializer,
            400: OpenApiResponse(description="Job cannot be cancelled (already terminal)"),
        },
    )
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request: Request, pk=None) -> Response:
        job = self.get_object()

        if job.is_terminal:
            return Response(
                {
                    "error": f"Cannot cancel job {job.id} because it is already in terminal state '{job.status}'.",
                    "status": job.status,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        previous_status = job.status
        with transaction.atomic():
            # Use select_for_update to guard race conditions with worker completing simultaneously
            locked_job = Job.objects.select_for_update().get(id=job.id)
            if locked_job.is_terminal:
                return Response(
                    {
                        "error": f"Cannot cancel job {job.id} because it just transitioned to terminal state '{locked_job.status}'.",
                        "status": locked_job.status,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            locked_job.transition_to(JobStatus.CANCELLED, save=True)

        # Signal Celery revocation
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
                "details": "Cancellation recorded. Any in-flight execution will discard results at the next boundary.",
            },
            status=status.HTTP_200_OK,
        )
