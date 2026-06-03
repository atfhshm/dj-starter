from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils import translation
from django.utils.cache import patch_vary_headers
from django.utils.translation import trans_real

__all__ = [
    "LocaleMiddleware",
]


class LocaleMiddleware:
    """
    Activate the request language and advertise it on the response.

    This middleware fully owns i18n for the project (Django's built-in
    ``LocaleMiddleware`` is intentionally not used). The language is resolved
    in the following order:

    1. the authenticated user's ``locale``;
    2. the best supported variant from the ``Accept-Language`` header;
    3. ``settings.LANGUAGE_CODE`` as a final fallback.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        user = request.user
        if user.is_authenticated:
            language = getattr(user, "locale")
        else:
            language = self.language_from_accept_header(request) or self.default_language()

        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()

        try:
            response = self.get_response(request)
        finally:
            translation.deactivate()

        response.headers.setdefault("Content-Language", request.LANGUAGE_CODE)
        if not user.is_authenticated:
            patch_vary_headers(response, ("Accept-Language",))
        return response

    @staticmethod
    def default_language() -> str:
        """
        Return ``settings.LANGUAGE_CODE`` normalised to a supported variant.
        e.g. `en-us` becomes `en`, `ar-EG` becomes `ar`.
        """
        try:
            return trans_real.get_supported_language_variant(settings.LANGUAGE_CODE)
        except LookupError:
            return settings.LANGUAGE_CODE

    @staticmethod
    def language_from_accept_header(request: HttpRequest) -> str | None:
        """
        Return the best supported language from the ``Accept-Language`` header.
        e.g. `en-us, en;q=0.8, ar-EG;q=0.6` returns `en`.
        """
        accept = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
        for code, _priority in trans_real.parse_accept_lang_header(accept):
            if code == "*":
                break
            try:
                return trans_real.get_supported_language_variant(code)
            except LookupError:
                continue
        return None
