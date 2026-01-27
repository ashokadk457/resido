import os
from celery import Celery
from celery.signals import setup_logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "resido.settings")

## Get the base REDIS URL, default to redis' default
BASE_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

app = Celery("resido")

app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.broker_url = BASE_REDIS_URL

# Disable eager mode to allow proper async task execution
# This prevents race conditions in tenant launch
app.conf.task_always_eager = False
app.conf.task_eager_propagates = False


@setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig  # noqa
    from django.conf import settings  # noqa

    dictConfig(settings.LOGGING)


@app.on_after_finalize.connect
def import_custom_task_modules(sender, **kwargs):
    from payments.tasks import recon  # noqa
    from payments.tasks import bill_pp  # noqa
    from payments.managers.bill.processor import refund  # noqa


app.conf.beat_schedule = {
    "add-every-30-seconds": {
        "task": "notifications.tasks.send_notification",
        "schedule": 30.0,
    },
}
