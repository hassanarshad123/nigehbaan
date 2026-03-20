"""Celery application factory configured with Redis broker."""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "nigehbaan",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Karachi",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Explicitly include task modules for reliable discovery
celery_app.conf.include = [
    "app.tasks.scraping_tasks",
    "app.tasks.processing_tasks",
    "app.tasks.schedule",
]
