import inspect
import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar, Token
from typing import cast

from django.http import HttpRequest, HttpResponse


class TracedHttpRequest(HttpRequest):
    request_id: str
    correlation_id: str


__all__ = [
    "TraceMiddleware",
    "get_correlation_id",
    "get_request_id",
]
# Header names
REQUEST_ID_HEADER = "X-Request-ID"
CORRELATION_ID_HEADER = "X-Correlation-ID"

# Per-request state. ContextVars are isolated per thread (WSGI) and per task (ASGI)
_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_request_id() -> str | None:
    """Return the current request's id, or ``None`` outside a request."""
    return _request_id.get()


def get_correlation_id() -> str | None:
    """Return the current correlation id, or ``None`` outside a request."""
    return _correlation_id.get()


class TraceMiddleware:
    """Attach a request id and a correlation id to every request.

    Works under both WSGI (sync) and ASGI (async) with no third-party
    dependency. For each request the ids are:

    * stored on the request (``request.request_id`` / ``request.correlation_id``),
    * echoed back on the response headers.

    Both ids are always generated on the server. Inbound ``X-Request-ID`` /
    ``X-Correlation-ID`` headers are ignored, so a client can never set or
    influence the trace ids.
    """

    sync_capable = True
    async_capable = True

    def __init__(
        self,
        get_response: Callable[[HttpRequest], HttpResponse | Awaitable[HttpResponse]],
    ) -> None:
        self.get_response = get_response
        self.is_async = inspect.iscoroutinefunction(get_response)
        if self.is_async:
            inspect.markcoroutinefunction(self)

    def __call__(self, request: HttpRequest) -> HttpResponse | Awaitable[HttpResponse]:
        if self.is_async:
            return self.__acall__(request)
        tokens = self.activate(request)
        try:
            get_response = cast(Callable[[HttpRequest], HttpResponse], self.get_response)
            response = get_response(request)
            self.inject_headers(response)
            return response
        finally:
            self.reset(tokens)

    async def __acall__(self, request: HttpRequest) -> HttpResponse:
        tokens = self.activate(request)
        try:
            get_response = cast(
                Callable[[HttpRequest], Awaitable[HttpResponse]],
                self.get_response,
            )
            response = await get_response(request)
            self.inject_headers(response)
            return response
        finally:
            self.reset(tokens)

    @staticmethod
    def activate(request: HttpRequest) -> tuple[Token, Token]:
        request_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())
        traced_request = cast(TracedHttpRequest, request)
        traced_request.request_id = request_id
        traced_request.correlation_id = correlation_id
        return _request_id.set(request_id), _correlation_id.set(correlation_id)

    @staticmethod
    def inject_headers(response: HttpResponse) -> None:
        request_id = _request_id.get()
        correlation_id = _correlation_id.get()
        if request_id is not None:
            response[REQUEST_ID_HEADER] = request_id
        if correlation_id is not None:
            response[CORRELATION_ID_HEADER] = correlation_id

    @staticmethod
    def reset(tokens: tuple[Token, Token]) -> None:
        # Reset so a reused WSGI thread never leaks ids into the next request.
        request_token, correlation_token = tokens
        _request_id.reset(request_token)
        _correlation_id.reset(correlation_token)
