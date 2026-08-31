import pytest
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model

from jobs.models import Job, JobExecution, JobPriority, JobResult, JobStatus, JobType
from workers.locking import RedisDistributedLock
from workers.tasks import execute_job_task

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="worker_test@example.com", password="Password123!")


@pytest.mark.django_db
class TestWorkerExecution:
    @patch.object(RedisDistributedLock, "acquire", return_value=True)
    @patch.object(RedisDistributedLock, "release", return_value=True)
    def test_task_execution_success(self, mock_release, mock_acquire, user):
        job = Job.objects.create(
            user=user,
            job_type=JobType.PROCESS_DATA,
            payload={"items": ["alpha", "beta", "gamma"]},
            status=JobStatus.QUEUED,
        )

        result = execute_job_task(str(job.id), attempt_number=1)
        assert result["status"] == "completed"

        job.refresh_from_db()
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.execution_duration is not None
        assert job.result is not None
        assert job.result.result_data["input_count"] == 3

        # Check execution audit history
        assert job.executions.count() == 1
        execution = job.executions.first()
        assert execution.status == JobStatus.COMPLETED
        assert execution.attempt_number == 1

    @patch.object(RedisDistributedLock, "acquire", return_value=True)
    @patch.object(RedisDistributedLock, "release", return_value=True)
    @patch("workers.tasks.execute_job_task.apply_async")
    def test_task_execution_retry_on_failure(self, mock_apply_async, mock_release, mock_acquire, user):
        job = Job.objects.create(
            user=user,
            job_type=JobType.SIMULATE_LONG_TASK,
            payload={"duration": 0.01, "simulate_failure": True, "failure_reason": "Database connection timed out"},
            status=JobStatus.QUEUED,
            max_retries=2,
            current_retry_count=0,
        )

        result = execute_job_task(str(job.id), attempt_number=1)
        assert result["status"] == "retrying"

        job.refresh_from_db()
        assert job.status == JobStatus.RETRYING
        assert job.current_retry_count == 1
        assert "Database connection timed out" in job.error_message

        # Assert task was scheduled for retry with exponential countdown
        mock_apply_async.assert_called_once()

    @patch.object(RedisDistributedLock, "acquire", return_value=True)
    @patch.object(RedisDistributedLock, "release", return_value=True)
    def test_task_execution_exhausted_retries_fails_permanently(self, mock_release, mock_acquire, user):
        job = Job.objects.create(
            user=user,
            job_type=JobType.SIMULATE_LONG_TASK,
            payload={"duration": 0.01, "simulate_failure": True},
            status=JobStatus.RETRYING,
            max_retries=2,
            current_retry_count=2,  # Already reached max retries
        )

        result = execute_job_task(str(job.id), attempt_number=3)
        assert result["status"] == "failed"

        job.refresh_from_db()
        assert job.status == JobStatus.FAILED
        assert job.failed_at is not None
        assert job.current_retry_count == 3
