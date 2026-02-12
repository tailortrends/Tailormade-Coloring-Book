import os
from celery import Celery
from app.config import get_settings

settings = get_settings()

if not settings.redis_url:
    # Fallback for dev if Redis isn't configured, though it should be for this to work
    broker_url = "redis://localhost:6379/0"
    result_backend = "redis://localhost:6379/0"
else:
    broker_url = settings.redis_url
    result_backend = settings.redis_url

celery_app = Celery(
    "tailormade_worker",
    broker=broker_url,
    backend=result_backend,
    include=["app.tasks"],  # We'll create this file next
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Worker resiliency
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
