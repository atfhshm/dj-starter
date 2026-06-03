from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils import timezone

__all__ = [
    "TimezoneMiddleware",
]


class TimezoneMiddleware:
    """
    Middleware to set the timezone for the request.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        user = request.user
        current_tz = getattr(user, "timezone", settings.TIME_ZONE)
        timezone.activate(current_tz)
        return self.get_response(request)
