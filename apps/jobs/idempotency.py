import hashlib
import json
from datetime import timedelta
from typing import Any, Callable, Dict, Optional, Tuple
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from monitoring.metrics import IDEMPOTENCY_HITS_TOTAL
from .models import IdempotencyKey


def compute_request_hash(user_id: str, path: str, data: Any) -> str:
    """Computes a deterministic SHA-256 hash of the request path, user, and payload."""
    serialized_payload = json.dumps(data, sort_keys=True) if data else ""
    raw_signature = f"{user_id}:{path}:{serialized_payload}"
    return hashlib.sha256(raw_signature.encode("utf-8")).hexdigest()


class IdempotencyHandler:
    """
    Guarantees that repeated requests with the same Idempotency-Key return the identical
    cached response without re-executing job creation or dispatching duplicate tasks.
    """

    DEFAULT_TTL_HOURS = 24

    @classmethod
    def process_idempotent_request(
        cls,
        request: Request,
        view_func: Callable[[Request], Response],
    ) -> Response:
        idempotency_key_str = request.headers.get("Idempotency-Key")

        # If no key is provided, bypass idempotency and process normally
        if not idempotency_key_str:
            return view_func(request)

        user = request.user
        request_hash = compute_request_hash(str(user.id), request.path, request.data)

        # 1. Check for existing idempotency key in DB
        existing_key = IdempotencyKey.objects.filter(
            user=user,
            idempotency_key=idempotency_key_str,
        ).first()

        if existing_key:
            # Check for payload tampering
            if existing_key.request_hash != request_hash:
                return Response(
                    {
                        "error": "Idempotency key reused with a different request payload or endpoint.",
                        "code": "idempotency_payload_mismatch",
                    },
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            # If response is already recorded, return the cached response
            if existing_key.response_payload is not None:
                IDEMPOTENCY_HITS_TOTAL.inc()
                response = Response(
                    existing_key.response_payload,
                    status=existing_key.response_status_code or status.HTTP_200_OK,
                )
                response["X-Cache-Lookup"] = "HIT-Idempotency"
                return response

            # If the record exists but has no response payload yet, a concurrent request is in flight
            return Response(
                {
                    "error": "A request with this Idempotency-Key is currently in flight. Please retry shortly.",
                    "code": "concurrent_request_in_progress",
                },
                status=status.HTTP_409_CONFLICT,
            )

        # 2. Reserve the key record atomically before executing the view
        expires_at = timezone.now() + timedelta(hours=cls.DEFAULT_TTL_HOURS)
        try:
            with transaction.atomic():
                idempotency_record = IdempotencyKey.objects.create(
                    user=user,
                    idempotency_key=idempotency_key_str,
                    request_hash=request_hash,
                    expires_at=expires_at,
                )
        except IntegrityError:
            # Concurrent race condition caught by DB unique constraint
            return Response(
                {
                    "error": "Concurrent request detected with identical Idempotency-Key.",
                    "code": "concurrent_request_conflict",
                },
                status=status.HTTP_409_CONFLICT,
            )

        # 3. Execute the actual view function
        response = view_func(request)

        # 4. Save response payload back to idempotency record for future replays
        if response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED]:
            idempotency_record.response_payload = response.data
            idempotency_record.response_status_code = response.status_code
            if hasattr(response, "job_instance"):
                idempotency_record.job = response.job_instance
            idempotency_record.save(update_fields=["response_payload", "response_status_code", "job"])

        response["X-Cache-Lookup"] = "MISS-Idempotency-Saved"
        return response
