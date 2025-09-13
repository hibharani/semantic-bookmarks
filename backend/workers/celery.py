from celery import Celery
from config import settings

# Create Celery instance
celery_app = Celery(
    "semantic_bookmarks",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["workers.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)