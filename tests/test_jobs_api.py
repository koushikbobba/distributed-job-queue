import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from jobs.models import Job, JobPriority, JobStatus, JobType

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_a(db):
    return User.objects.create_user(email="user_a@example.com", password="Password123!")


@pytest.fixture
def user_b(db):
    return User.objects.create_user(email="user_b@example.com", password="Password123!")


@pytest.fixture
def auth_client_a(api_client, user_a):
    login_url = reverse("users:login")
    resp = api_client.post(login_url, {"email": user_a.email, "password": "Password123!"})
    token = resp.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def auth_client_b(api_client, user_b):
    login_url = reverse("users:login")
    resp = api_client.post(login_url, {"email": user_b.email, "password": "Password123!"})
    token = resp.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.mark.django_db
class TestJobAPI:
    def test_create_job_success(self, auth_client_a, user_a):
        url = reverse("jobs:job-list")
        payload = {
            "job_type": JobType.GENERATE_REPORT,
            "priority": JobPriority.HIGH,
            "payload": {"customer_id": 42, "report_type": "quarterly"},
            "max_retries": 4,
        }
        response = auth_client_a.post(url, payload, format="json")

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert "id" in response.data
        assert response.data["job_type"] == JobType.GENERATE_REPORT
        assert response.data["priority"] == JobPriority.HIGH
        assert response.data["status"] == JobStatus.QUEUED

        job = Job.objects.get(id=response.data["id"])
        assert job.user == user_a
        assert job.payload["customer_id"] == 42

    def test_create_job_invalid_job_type(self, auth_client_a):
        url = reverse("jobs:job-list")
        payload = {
            "job_type": "invalid_unknown_type",
            "payload": {},
        }
        response = auth_client_a.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "job_type" in response.data

    def test_multi_tenant_isolation(self, auth_client_a, auth_client_b, user_a, user_b):
        # User A creates a job
        job_a = Job.objects.create(
            user=user_a,
            job_type=JobType.SEND_EMAIL,
            payload={"recipient": "test@example.com"},
            status=JobStatus.QUEUED,
        )

        # User B cannot view User A's job
        detail_url = reverse("jobs:job-detail", kwargs={"pk": job_a.id})
        response = auth_client_b.get(detail_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # User B cannot cancel User A's job
        cancel_url = reverse("jobs:job-cancel", kwargs={"pk": job_a.id})
        response = auth_client_b.post(cancel_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_job_cancellation_queued_state(self, auth_client_a, user_a):
        job = Job.objects.create(
            user=user_a,
            job_type=JobType.SIMULATE_LONG_TASK,
            payload={"duration": 10},
            status=JobStatus.QUEUED,
        )

        cancel_url = reverse("jobs:job-cancel", kwargs={"pk": job.id})
        response = auth_client_a.post(cancel_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == JobStatus.CANCELLED
        job.refresh_from_db()
        assert job.status == JobStatus.CANCELLED

    def test_job_cancellation_terminal_state_fails(self, auth_client_a, user_a):
        job = Job.objects.create(
            user=user_a,
            job_type=JobType.PROCESS_DATA,
            payload={"items": [1, 2, 3]},
            status=JobStatus.COMPLETED,
        )

        cancel_url = reverse("jobs:job-cancel", kwargs={"pk": job.id})
        response = auth_client_a.post(cancel_url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already in terminal state" in response.data["error"]

    def test_job_listing_and_filtering(self, auth_client_a, user_a):
        Job.objects.create(user=user_a, job_type=JobType.SEND_EMAIL, status=JobStatus.COMPLETED, priority=JobPriority.LOW)
        Job.objects.create(user=user_a, job_type=JobType.GENERATE_REPORT, status=JobStatus.FAILED, priority=JobPriority.HIGH)
        Job.objects.create(user=user_a, job_type=JobType.PROCESS_DATA, status=JobStatus.QUEUED, priority=JobPriority.HIGH)

        url = reverse("jobs:job-list")
        response = auth_client_a.get(f"{url}?status=failed&priority=high")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["status"] == JobStatus.FAILED
        assert response.data["results"][0]["priority"] == JobPriority.HIGH
