from __future__ import annotations

import structlog
from django.dispatch import receiver
from django_structlog import signals

from core.middlewares.trace import get_correlation_id, get_request_id

__all__: list[str] = [
    "bind_trace_ids",
]


@receiver(signals.bind_extra_request_metadata)
def bind_trace_ids(request=None, logger=None, **kwargs) -> None:
    """
    Bind ``TraceMiddleware``'s request/correlation ids onto the log context.
    """
    bindings: dict[str, str] = {}
    request_id = get_request_id()
    if request_id:
        bindings["request_id"] = request_id
    correlation_id = get_correlation_id()
    if correlation_id:
        bindings["correlation_id"] = correlation_id
    if bindings:
        structlog.contextvars.bind_contextvars(**bindings)
