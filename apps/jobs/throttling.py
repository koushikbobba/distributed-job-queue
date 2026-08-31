from rest_framework.throttling import UserRateThrottle
from monitoring.metrics import RATE_LIMIT_EXCEEDED_TOTAL


class AuthenticatedUserRateThrottle(UserRateThrottle):
    """General rate limiting for authenticated user API requests (100/min)."""

    scope = "user"

    def throttle_failure(self):
        RATE_LIMIT_EXCEEDED_TOTAL.labels(endpoint="general").inc()
        return super().throttle_failure()


class JobSubmissionRateThrottle(UserRateThrottle):
    """Strict rate limiting for job submission endpoint (10/min per user)."""

    scope = "job_submission"

    def throttle_failure(self):
        RATE_LIMIT_EXCEEDED_TOTAL.labels(endpoint="job_submission").inc()
        return super().throttle_failure()
