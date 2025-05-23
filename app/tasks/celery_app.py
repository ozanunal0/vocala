"""Celery application configuration."""

from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "vocala",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.scheduled_tasks",
        "app.tasks.notification_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic task schedule
celery_app.conf.beat_schedule = {
    "send-daily-vocabulary": {
        "task": "app.tasks.scheduled_tasks.send_daily_vocabulary_to_all_users",
        "schedule": 60.0,  # Run every minute for testing; adjust as needed
    },
    "cleanup-old-data": {
        "task": "app.tasks.scheduled_tasks.cleanup_old_data",
        "schedule": 86400.0,  # Daily
    },
}

# Import tasks to register them
from app.tasks import scheduled_tasks, notification_tasks  # noqa: F401 