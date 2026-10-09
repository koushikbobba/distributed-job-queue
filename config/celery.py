import os
from celery import Celery
from kombu import Exchange, Queue

# Set default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("job_processor")

# Read config from Django settings, using CELERY_ namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Configure Exchanges & Priority Queues including Dead-Letter Queue (DLQ)
default_exchange = Exchange("default", type="direct")
dlq_exchange = Exchange("dead_letter", type="direct")

app.conf.task_queues = (
    Queue("high_priority", default_exchange, routing_key="high_priority"),
    Queue("default_priority", default_exchange, routing_key="default_priority"),
    Queue("low_priority", default_exchange, routing_key="low_priority"),
    Queue("dead_letter", dlq_exchange, routing_key="dead_letter"),
)

app.conf.task_default_queue = "default_priority"
app.conf.task_default_exchange = "default"
app.conf.task_default_routing_key = "default_priority"

# At-Least-Once Delivery & Worker Reliability Settings
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True
app.conf.worker_prefetch_multiplier = 1  # Fair task distribution for heterogeneous workloads

# Periodic Schedule: Stalled Job Sweeper & Transactional Outbox Forwarder
app.conf.beat_schedule = {
    "sweep-stalled-jobs-every-5-minutes": {
        "task": "workers.tasks.sweep_stalled_jobs",
        "schedule": 300.0,
        "args": (30,),
    },
    "forward-outbox-messages-every-minute": {
        "task": "workers.tasks.process_outbox_messages",
        "schedule": 60.0,
        "args": (100,),
    },
}

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
