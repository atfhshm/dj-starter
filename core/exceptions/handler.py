from typing import Any

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework.settings import api_settings
from rest_framework.views import exception_handler

from core.exceptions.const import DRF_ERROR_CODE_MAP, INTERNAL_ERROR_CODE, VALIDATION_ERROR_CODE
from core.exceptions.exceptions import AppError
from core.logging import get_logger

logger = get_logger(__name__)


def app_error_handler(exc, ctx):
    """
    {
        "error_code": "Error code",
        "detail": "Error detail",
    }
    or
    {
        "error_code": "Error code",
        "detail": ["Error detail 1", "Error detail 2"],
    }
    or
    {
        "error_code": "Error code",
        "detail": {
            "field_1": "Error detail 1",
            "field_2": "Error detail 2",
        },
    }
    """
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(as_serializer_error(exc))

    if isinstance(exc, Http404):
        exc = exceptions.NotFound()

    if isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    response = exception_handler(exc, ctx)

    if response is None:
        if isinstance(exc, AppError):
            return Response(
                {
                    "error_code": exc.error_code,
                    "detail": extract_detail(exc.detail),
                },
                status=exc.status_code,
            )

        logger.exception("Unhandled exception", exc_info=exc)
        return Response(
            {
                "error_code": INTERNAL_ERROR_CODE,
                "detail": internal_error_detail(exc),
            },
            status=500,
        )

    if isinstance(exc, exceptions.ValidationError):
        return Response(
            {
                "error_code": VALIDATION_ERROR_CODE,
                "detail": extract_detail(exc.detail),
            },
            status=response.status_code,
        )

    return Response(
        {
            "error_code": resolve_error_code(exc),
            "detail": extract_detail(exc.detail),
        },
        status=response.status_code,
    )


def resolve_error_code(exc: Exception) -> str:
    default_code = getattr(exc, "default_code", None)
    if default_code is None:
        return INTERNAL_ERROR_CODE

    normalized = DRF_ERROR_CODE_MAP.get(str(default_code))
    if normalized is not None:
        return normalized

    return str(default_code).upper()


def internal_error_detail(exc: Exception) -> str:
    if settings.DEBUG:
        return str(exc)
    return str(AppError.default_message)


def extract_detail(detail: Any) -> Any:
    non_field_key = api_settings.NON_FIELD_ERRORS_KEY
    if isinstance(detail, dict) and list(detail.keys()) == [non_field_key]:
        detail = detail[non_field_key]
    if isinstance(detail, list) and len(detail) == 1:
        return str(detail[0])

    return detail
