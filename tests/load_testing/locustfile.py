import random
import uuid
from locust import HttpUser, between, task


class JobQueueLoadTester(HttpUser):
    """
    Simulates realistic client traffic submitting background jobs,
    checking status, querying filtered lists, and testing idempotency under heavy load.
    """

    wait_time = between(0.1, 0.5)

    def on_start(self):
        """Register and login a dedicated user per simulated client."""
        self.user_email = f"loadtest_{uuid.uuid4().hex[:8]}@example.com"
        self.password = "BenchmarkPassword123!"

        # Register
        self.client.post(
            "/api/auth/register/",
            json={
                "email": self.user_email,
                "password": self.password,
                "password_confirm": self.password,
            },
        )

        # Login
        login_resp = self.client.post(
            "/api/auth/login/",
            json={"email": self.user_email, "password": self.password},
        )
        if login_resp.status_code == 200:
            self.access_token = login_resp.json()["access"]
            self.headers = {"Authorization": f"Bearer {self.access_token}"}
        else:
            self.headers = {}

        self.created_job_ids = []

    @task(5)
    def submit_job(self):
        """Submit high/medium/low priority jobs with idempotency keys."""
        job_types = ["send_email", "generate_report", "process_data", "simulate_long_task"]
        priorities = ["high", "medium", "low"]

        selected_type = random.choice(job_types)
        selected_priority = random.choice(priorities)

        payload = {}
        if selected_type == "send_email":
            payload = {"recipient": f"client_{random.randint(1, 1000)}@test.com", "subject": "Invoice"}
        elif selected_type == "generate_report":
            payload = {"customer_id": random.randint(1, 500), "report_type": "monthly"}
        elif selected_type == "process_data":
            payload = {"items": [random.randint(1, 100) for _ in range(10)]}
        elif selected_type == "simulate_long_task":
            payload = {"duration": 0.5, "simulate_failure": random.random() < 0.1}

        idempotency_key = f"load-{uuid.uuid4().hex}"
        request_headers = {**self.headers, "Idempotency-Key": idempotency_key}

        with self.client.post(
            "/api/jobs/",
            json={
                "job_type": selected_type,
                "priority": selected_priority,
                "payload": payload,
                "max_retries": 3,
            },
            headers=request_headers,
            catch_response=True,
        ) as resp:
            if resp.status_code == 202:
                job_id = resp.json().get("id")
                if job_id:
                    self.created_job_ids.append(job_id)
                resp.success()
            elif resp.status_code == 429:
                resp.success()  # Rate limit working as designed

    @task(3)
    def check_job_status(self):
        """Poll the status of an existing job."""
        if not self.created_job_ids:
            return

        job_id = random.choice(self.created_job_ids)
        self.client.get(f"/api/jobs/{job_id}/", headers=self.headers)

    @task(2)
    def list_and_filter_jobs(self):
        """Query user's job listing with status and priority filters."""
        status_filter = random.choice(["QUEUED", "PROCESSING", "COMPLETED", "FAILED"])
        self.client.get(f"/api/jobs/?status={status_filter}", headers=self.headers)

    @task(1)
    def test_idempotency_cache_hit(self):
        """Re-send the exact same request with the same Idempotency-Key to test cache deduplication."""
        idempotency_key = f"fixed-key-{uuid.uuid4().hex[:6]}"
        headers = {**self.headers, "Idempotency-Key": idempotency_key}
        payload = {"job_type": "send_email", "payload": {"recipient": "boss@test.com"}}

        # Initial submit
        self.client.post("/api/jobs/", json=payload, headers=headers)
        # Duplicate submit -> Must hit idempotency cache
        self.client.post("/api/jobs/", json=payload, headers=headers)
