import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import MagicMock, patch

from jobs.models import Job, JobPriority, JobStatus, JobType, InvalidStateTransitionError, OutboxMessage, OutboxStatus
from workers.tasks import execute_job_task, sweep_stalled_jobs, process_outbox_messages

User = get_user_model()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(email="reliability_test@example.com", password="Password123!")


@pytest.mark.django_db
class TestDeliveryAndStateReliability:
    def test_strict_fsm_state_transitions(self, test_user):
        """Verify illegal state transitions raise InvalidStateTransitionError."""
        job = Job.objects.create(
            user=test_user,
            job_type=JobType.PROCESS_DATA,
            status=JobStatus.QUEUED,
        )

        # Illegal transition: QUEUED directly to COMPLETED (must go via PROCESSING)
        with pytest.raises(InvalidStateTransitionError):
            job.transition_to(JobStatus.COMPLETED)

        # Legal transition: QUEUED -> PROCESSING
        job.transition_to(JobStatus.PROCESSING)
        assert job.status == JobStatus.PROCESSING

        # Legal transition: PROCESSING -> COMPLETED
        job.transition_to(JobStatus.COMPLETED)
        assert job.status == JobStatus.COMPLETED
        assert job.is_terminal is True

        # Illegal transition from terminal state COMPLETED -> PROCESSING
        with pytest.raises(InvalidStateTransitionError):
            job.transition_to(JobStatus.PROCESSING)

    def test_cancellation_race_condition_aborts_in_flight_completion(self, test_user):
        """
        If a job is marked CANCELLED while a worker is running,
        the worker's completion step must detect the cancellation and discard results.
        """
        job = Job.objects.create(
            user=test_user,
            job_type=JobType.PROCESS_DATA,
            payload={"items": ["x", "y"]},
            status=JobStatus.CANCELLED,  # Cancelled before or during execution
        )

        result = execute_job_task(str(job.id), attempt_number=1)
        assert result["status"] == "skipped" or result["status"] == "aborted"

        job.refresh_from_db()
        assert job.status == JobStatus.CANCELLED

    def test_stalled_job_sweeper_recovers_abandoned_jobs(self, test_user):
        """Verify the reaper sweeps and re-queues jobs stuck in PROCESSING."""
        past_time = timezone.now() - timezone.timedelta(minutes=45)

        stalled_job = Job.objects.create(
            user=test_user,
            job_type=JobType.GENERATE_REPORT,
            payload={"customer_id": 10},
            status=JobStatus.PROCESSING,
            max_retries=3,
            current_retry_count=0,
        )
        # Manually backdate updated_at to simulate worker timeout
        Job.objects.filter(id=stalled_job.id).update(updated_at=past_time)

        with patch("workers.tasks.execute_job_task.apply_async") as mock_apply:
            sweep_result = sweep_stalled_jobs(stalled_threshold_minutes=30)
            assert sweep_result["recovered_count"] == 1
            mock_apply.assert_called_once()

        stalled_job.refresh_from_db()
        assert stalled_job.status == JobStatus.RETRYING
        assert stalled_job.current_retry_count == 1
        assert "sweeper" in stalled_job.error_message.lower()

    def test_transactional_outbox_forwarder(self, test_user):
        """Verify outbox messages are published and marked PUBLISHED."""
        job = Job.objects.create(
            user=test_user,
            job_type=JobType.SEND_EMAIL,
            status=JobStatus.QUEUED,
        )
        outbox = OutboxMessage.objects.create(
            job=job,
            queue_name="high_priority",
            payload={"recipient": "boss@example.com"},
            status=OutboxStatus.PENDING,
        )

        with patch("workers.tasks.execute_job_task.apply_async") as mock_apply:
            result = process_outbox_messages(batch_size=10)
            assert result["published_count"] == 1
            mock_apply.assert_called_once()

        outbox.refresh_from_db()
        assert outbox.status == OutboxStatus.PUBLISHED
        assert outbox.published_at is not None
