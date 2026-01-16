from celery import Celery
from fuse.config import settings

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_log_format="%(message)s",
    worker_task_log_format="%(message)s",
    worker_log_color=True,
    task_routes={
        "fuse.workflows.engine.execute_workflow": "trigger_queue",
        "fuse.workflows.engine.run_node": "default",
        "fuse.workflows.engine.check_scheduled_workflows": "default",
    },
    beat_schedule={
        "check-scheduled-workflows-every-10s": {
            "task": "fuse.workflows.engine.check_scheduled_workflows",
            "schedule": 10.0,
        },
    },
)

# Import tasks to ensure they are registered
import fuse.workflows.engine
import fuse.workflows.engine.periodic_scheduler

# Beautiful Logging for Celery
from celery.signals import after_setup_logger, after_setup_task_logger
from fuse.logger import setup_celery_logger

@after_setup_logger.connect
@after_setup_task_logger.connect
def on_setup_logger(logger, loglevel, **kwargs):
    setup_celery_logger(logger=logger, loglevel=loglevel, **kwargs)

