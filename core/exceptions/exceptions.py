from django.utils.translation import gettext_noop as _

from core.exceptions.const import (
    BAD_REQUEST_ERROR_CODE,
    CONFLICT_ERROR_CODE,
    FORBIDDEN_ERROR_CODE,
    INTERNAL_ERROR_CODE,
    NOT_FOUND_ERROR_CODE,
    UNAUTHORIZED_ERROR_CODE,
)

__all__ = [
    "AppError",
    "BadRequestError",
    "ConflictError",
    "ForbiddenError",
    "NotFoundError",
    "UnauthorizedError",
]

ErrorDetailType = str | list[str] | dict[str, list[str]]
ErrorDetail = dict[str, ErrorDetailType]


class AppError(Exception):
    """
    Base class for all application errors.
    """

    status_code: int = 500
    error_code: str = INTERNAL_ERROR_CODE
    default_message: str = _("An unexpected error occurred.")

    def __init__(
        self,
        detail: str | ErrorDetail | None = None,
        *,
        error_code: str | None = None,
        status_code: int | None = None,
    ):
        self.detail: str | ErrorDetail = detail if detail is not None else self.default_message
        if error_code is not None:
            self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.detail if isinstance(self.detail, str) else str(self.detail))


class BadRequestError(AppError):
    status_code = 400
    error_code = BAD_REQUEST_ERROR_CODE
    default_message = _("Invalid request.")


class UnauthorizedError(AppError):
    status_code = 401
    error_code = UNAUTHORIZED_ERROR_CODE
    default_message = _("Authentication credentials were not provided.")


class ForbiddenError(AppError):
    status_code = 403
    error_code = FORBIDDEN_ERROR_CODE
    default_message = _("You do not have permission to perform this action.")


class NotFoundError(AppError):
    status_code = 404
    error_code = NOT_FOUND_ERROR_CODE
    default_message = _("Not found.")


class ConflictError(AppError):
    status_code = 409
    error_code = CONFLICT_ERROR_CODE
    default_message = _("Conflict.")
