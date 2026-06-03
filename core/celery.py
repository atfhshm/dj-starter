import os
from collections import defaultdict
from typing import Any, cast

from celery import Celery
from celery.signals import setup_logging
from django_structlog.celery.steps import DjangoStructLogInitStep

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

celery_app = Celery("celery_app")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()

# Bind task ids / parent task ids into the structlog context for worker logs.
cast(defaultdict[str, set[Any]], celery_app.steps)["worker"].add(DjangoStructLogInitStep)


@setup_logging.connect
def configure_celery_logging(**kwargs) -> None:
    # Stop Celery hijacking the root logger; apply the project's structlog setup.
    from core.logging import setup_celery_logging

    setup_celery_logging(**kwargs)
