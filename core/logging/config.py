from __future__ import annotations

import logging.config
from typing import Any

import structlog

SERVICE_NAME = "dj-starter"

__all__ = [
    "SERVICE_NAME",
    "build_logging_config",
    "configure_structlog",
    "get_logger",
    "setup_celery_logging",
]

PRE_CHAIN_PROCESSORS: list[Any] = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.processors.UnicodeDecoder(),
]


def _add_service_name(
    logger: Any,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    event_dict.setdefault("service", SERVICE_NAME)
    return event_dict


def shared_processors() -> list[Any]:
    return [
        *PRE_CHAIN_PROCESSORS[:1],
        structlog.stdlib.filter_by_level,
        *PRE_CHAIN_PROCESSORS[1:],
        _add_service_name,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]


def configure_structlog() -> None:
    structlog.configure(
        processors=shared_processors(),
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger bound to the stdlib logging tree."""
    return structlog.get_logger(name)


def _processor_formatter(processor: Any) -> dict[str, Any]:
    return {
        "()": structlog.stdlib.ProcessorFormatter,
        "processor": processor,
        "foreign_pre_chain": [*PRE_CHAIN_PROCESSORS, _add_service_name],
        "keep_exc_info": True,
    }


def build_logging_config(
    *,
    debug: bool = False,
    log_level: str = "INFO",
) -> dict[str, Any]:
    console_formatter = "plain_console" if debug else "json_formatter"

    formatters: dict[str, Any] = {
        "json_formatter": _processor_formatter(
            structlog.processors.JSONRenderer(sort_keys=True),
        ),
        "plain_console": _processor_formatter(
            structlog.dev.ConsoleRenderer(colors=True),
        ),
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[{server_time}] {message}",
            "style": "{",
        },
    }

    handlers: dict[str, Any] = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": console_formatter,
        },
    }

    if debug:
        handlers["django.server"] = {
            "class": "logging.StreamHandler",
            "formatter": "django.server",
        }
        django_server_handlers = ["django.server"]
    else:
        django_server_handlers = ["console"]

    app_loggers: dict[str, Any] = {
        "django_structlog": {
            "handlers": ["console"],
            "level": log_level,
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.server": {
            "handlers": django_server_handlers,
            "level": log_level,
            "propagate": False,
        },
        "celery": {
            "handlers": ["console"],
            "level": log_level,
            "propagate": False,
        },
        "celery.task": {
            "handlers": ["console"],
            "level": log_level,
            "propagate": False,
        },
        "celery.worker": {
            "handlers": ["console"],
            "level": log_level,
            "propagate": False,
        },
        "celery.app.trace": {
            "handlers": ["console"],
            "level": log_level,
            "propagate": False,
        },
    }

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": handlers,
        "root": {
            "handlers": ["console"],
            "level": log_level,
        },
        "loggers": app_loggers,
    }


def setup_celery_logging(**kwargs: Any) -> None:
    from django.conf import settings

    logging.config.dictConfig(settings.LOGGING)
    configure_structlog()
