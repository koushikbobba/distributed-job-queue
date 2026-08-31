import abc
import logging
import time
from typing import Any, Dict, Type

from jobs.models import Job

logger = logging.getLogger(__name__)


class BaseJobHandler(abc.ABC):
    """Abstract base class for all asynchronous job processors."""

    job_type: str = ""

    @abc.abstractmethod
    def execute(self, job: Job, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the business logic for the task.
        Must return a JSON-serializable dictionary representing the output.
        Raise exceptions to trigger automatic retries.
        """
        pass


class SendEmailHandler(BaseJobHandler):
    job_type = "send_email"

    def execute(self, job: Job, payload: Dict[str, Any]) -> Dict[str, Any]:
        recipient = payload.get("recipient")
        subject = payload.get("subject", "No Subject")
        body = payload.get("body", "")

        if not recipient:
            raise ValueError("Missing 'recipient' field in payload.")

        # Simulate network latency / SMTP dispatch
        time.sleep(0.5)
        logger.info(f"[Worker] Sent email to '{recipient}' with subject '{subject}'")

        return {
            "status": "delivered",
            "recipient": recipient,
            "subject": subject,
            "bytes_sent": len(body),
        }


class GenerateReportHandler(BaseJobHandler):
    job_type = "generate_report"

    def execute(self, job: Job, payload: Dict[str, Any]) -> Dict[str, Any]:
        customer_id = payload.get("customer_id")
        report_type = payload.get("report_type", "monthly")

        if not customer_id:
            raise ValueError("Missing 'customer_id' in payload.")

        # Simulate intensive aggregation / data processing
        time.sleep(1.0)
        logger.info(f"[Worker] Generated report '{report_type}' for customer {customer_id}")

        return {
            "report_url": f"https://s3.amazonaws.com/reports/{customer_id}_{report_type}.pdf",
            "customer_id": customer_id,
            "report_type": report_type,
            "records_analyzed": 1420,
        }


class ProcessDataHandler(BaseJobHandler):
    job_type = "process_data"

    def execute(self, job: Job, payload: Dict[str, Any]) -> Dict[str, Any]:
        dataset = payload.get("items", [])
        if not dataset:
            raise ValueError("Empty or missing 'items' array in payload.")

        # Simulate transformation & batch processing
        transformed = [str(x).upper() if isinstance(x, str) else x * 2 for x in dataset]
        time.sleep(0.8)

        return {
            "input_count": len(dataset),
            "output_sample": transformed[:5],
            "checksum": sum(hash(str(x)) for x in transformed),
        }


class SimulateLongTaskHandler(BaseJobHandler):
    job_type = "simulate_long_task"

    def execute(self, job: Job, payload: Dict[str, Any]) -> Dict[str, Any]:
        duration_seconds = min(float(payload.get("duration", 2.0)), 30.0)
        should_fail = payload.get("simulate_failure", False)

        time.sleep(duration_seconds)

        if should_fail:
            error_reason = payload.get("failure_reason", "Simulated transient failure for testing retries.")
            raise RuntimeError(error_reason)

        return {
            "duration_slept": duration_seconds,
            "status": "completed_successfully",
        }


class JobRegistry:
    """Pluggable registry mapping job_type strings to concrete handler instances."""

    _handlers: Dict[str, BaseJobHandler] = {}

    @classmethod
    def register(cls, handler_cls: Type[BaseJobHandler]) -> None:
        handler_instance = handler_cls()
        cls._handlers[handler_instance.job_type] = handler_instance
        logger.debug(f"Registered job handler for '{handler_instance.job_type}'")

    @classmethod
    def get_handler(cls, job_type: str) -> BaseJobHandler:
        handler = cls._handlers.get(job_type)
        if not handler:
            raise ValueError(f"No job handler registered for job_type='{job_type}'")
        return handler

    @classmethod
    def get_supported_types(cls) -> list[str]:
        return list(cls._handlers.keys())


# Auto-register default handlers
JobRegistry.register(SendEmailHandler)
JobRegistry.register(GenerateReportHandler)
JobRegistry.register(ProcessDataHandler)
JobRegistry.register(SimulateLongTaskHandler)
