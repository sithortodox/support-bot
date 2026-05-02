from celery import Celery
from core.config import REDIS_URL

celery_app = Celery(
    "support_bot",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task
def send_notification(user_id: int, message: str):
    pass

@celery_app.task
def cleanup_old_tickets():
    pass

@celery_app.task
def generate_daily_report():
    pass
