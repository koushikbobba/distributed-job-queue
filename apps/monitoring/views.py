import logging
import django_redis
from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from jobs.models import Job, JobStatus

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Production health check endpoint verifying database connectivity,
    Redis availability, and reporting active queue metrics.
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="System Health & Status Check",
        description="Verifies PostgreSQL, Redis, and overall cluster health.",
    )
    def get(self, request: Request) -> Response:
        health_status = {
            "status": "healthy",
            "database": "unreachable",
            "redis": "unreachable",
            "metrics": {},
        }
        status_code = status.HTTP_200_OK

        # 1. Check PostgreSQL
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
            health_status["database"] = "healthy"
        except Exception as exc:
            health_status["database"] = f"unhealthy: {exc}"
            health_status["status"] = "degraded"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        # 2. Check Redis
        try:
            redis_client = django_redis.get_redis_connection("default")
            redis_client.ping()
            health_status["redis"] = "healthy"
        except Exception as exc:
            health_status["redis"] = f"unhealthy: {exc}"
            health_status["status"] = "degraded"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        # 3. Aggregate Queue Metrics
        try:
            queued_count = Job.objects.filter(status=JobStatus.QUEUED).count()
            processing_count = Job.objects.filter(status=JobStatus.PROCESSING).count()
            failed_count = Job.objects.filter(status=JobStatus.FAILED).count()
            completed_count = Job.objects.filter(status=JobStatus.COMPLETED).count()

            health_status["metrics"] = {
                "queued_jobs": queued_count,
                "processing_jobs": processing_count,
                "failed_jobs": failed_count,
                "completed_jobs": completed_count,
            }
        except Exception:
            pass

        return Response(health_status, status=status_code)
