import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from jobs.models import IdempotencyKey, Job, JobType

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="idempotent_user@example.com", password="Password123!")


@pytest.fixture
def auth_client(api_client, user):
    login_url = reverse("users:login")
    resp = api_client.post(login_url, {"email": user.email, "password": "Password123!"})
    token = resp.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.mark.django_db
class TestIdempotency:
    def test_duplicate_submission_with_same_key_returns_cached_response(self, auth_client, user):
        url = reverse("jobs:job-list")
        payload = {
            "job_type": JobType.SEND_EMAIL,
            "payload": {"recipient": "boss@company.com", "subject": "Quarterly Numbers"},
        }
        headers = {"HTTP_IDEMPOTENCY_KEY": "txn-abc-12345"}

        # First request -> Creates job
        resp1 = auth_client.post(url, payload, format="json", **headers)
        assert resp1.status_code == status.HTTP_202_ACCEPTED
        job_id_1 = resp1.data["id"]

        # Second request with IDENTICAL key & payload -> Intercepted by Idempotency Guard
        resp2 = auth_client.post(url, payload, format="json", **headers)
        assert resp2.status_code == status.HTTP_202_ACCEPTED
        assert resp2["X-Cache-Lookup"] == "HIT-Idempotency"
        assert resp2.data["id"] == job_id_1

        # Assert only ONE database Job row was created
        assert Job.objects.filter(user=user).count() == 1
        assert IdempotencyKey.objects.filter(user=user, idempotency_key="txn-abc-12345").count() == 1

    def test_idempotency_key_payload_tampering_rejected(self, auth_client, user):
        url = reverse("jobs:job-list")
        payload_original = {
            "job_type": JobType.SEND_EMAIL,
            "payload": {"recipient": "original@example.com"},
        }
        headers = {"HTTP_IDEMPOTENCY_KEY": "unique-fixed-key-999"}

        # First request
        resp1 = auth_client.post(url, payload_original, format="json", **headers)
        assert resp1.status_code == status.HTTP_202_ACCEPTED

        # Tampered second request with same key but different payload
        payload_modified = {
            "job_type": JobType.SEND_EMAIL,
            "payload": {"recipient": "tampered@example.com"},
        }
        resp2 = auth_client.post(url, payload_modified, format="json", **headers)
        assert resp2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert resp2.data["code"] == "idempotency_payload_mismatch"
