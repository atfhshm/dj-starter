from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import is_valid_path

__all__ = [
    "URL404Middleware",
]

ERROR_CODE_URL_NOT_FOUND = "URL_NOT_FOUND"
ERROR_CODE_URL_TRAILING_SLASH_MISSING = "URL_TRAILING_SLASH_MISSING"


class URL404Middleware:
    """
    Middleware to handle URL not found errors.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if response.status_code != 404:
            return response

        path = request.path_info
        urlconf = getattr(request, "urlconf", settings.ROOT_URLCONF)

        if is_valid_path(path, urlconf):
            return response

        elif is_valid_path(f"{path}/", urlconf) and not path.endswith("/"):
            return JsonResponse(
                {
                    "error": ERROR_CODE_URL_TRAILING_SLASH_MISSING,
                    "detail": (
                        "A valid URL must end with a trailing slash. "
                        f"Please redirect requests to {path}/"
                    ),
                },
                status=404,
            )

        return JsonResponse(
            {
                "error": ERROR_CODE_URL_NOT_FOUND,
                "detail": f"The requested URL {path} was not found on the server.",
            },
            status=404,
        )
