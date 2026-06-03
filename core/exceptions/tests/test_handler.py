from unittest.mock import patch

from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.test import SimpleTestCase, override_settings
from rest_framework import exceptions
from rest_framework.settings import api_settings

from core.exceptions.const import (
    FORBIDDEN_ERROR_CODE,
    INTERNAL_ERROR_CODE,
    NOT_FOUND_ERROR_CODE,
    UNAUTHORIZED_ERROR_CODE,
    VALIDATION_ERROR_CODE,
)
from core.exceptions.exceptions import AppError, ConflictError, NotFoundError
from core.exceptions.handler import app_error_handler, extract_detail, resolve_error_code


class ExtractDetailTests(SimpleTestCase):
    def test_returns_string_unchanged(self):
        self.assertEqual(extract_detail("Something went wrong."), "Something went wrong.")

    def test_unwraps_single_non_field_error_to_string(self):
        detail = {api_settings.NON_FIELD_ERRORS_KEY: ["Only one error."]}
        self.assertEqual(extract_detail(detail), "Only one error.")

    def test_unwraps_multiple_non_field_errors_to_list(self):
        detail = {api_settings.NON_FIELD_ERRORS_KEY: ["First error.", "Second error."]}
        self.assertEqual(extract_detail(detail), ["First error.", "Second error."])

    def test_unwraps_single_item_list_to_string(self):
        self.assertEqual(extract_detail(["Single error."]), "Single error.")

    def test_keeps_multi_item_list(self):
        detail = ["First error.", "Second error."]
        self.assertEqual(extract_detail(detail), detail)

    def test_keeps_field_errors_dict(self):
        detail = {"email": ["Enter a valid email address."]}
        self.assertEqual(extract_detail(detail), detail)


class ResolveErrorCodeTests(SimpleTestCase):
    def test_maps_not_authenticated_to_unauthorized(self):
        self.assertEqual(
            resolve_error_code(exceptions.NotAuthenticated()),
            UNAUTHORIZED_ERROR_CODE,
        )

    def test_maps_permission_denied_to_forbidden(self):
        self.assertEqual(
            resolve_error_code(exceptions.PermissionDenied()),
            FORBIDDEN_ERROR_CODE,
        )

    def test_maps_not_found(self):
        self.assertEqual(
            resolve_error_code(exceptions.NotFound()),
            NOT_FOUND_ERROR_CODE,
        )

    def test_uppercases_unknown_codes(self):
        self.assertEqual(resolve_error_code(exceptions.Throttled()), "THROTTLED")


class AppErrorHandlerTests(SimpleTestCase):
    context = {"request": None, "view": None}

    def call_handler(self, exc):
        response = app_error_handler(exc, self.context)
        assert response is not None
        return response.data, response.status_code

    def test_handles_validation_error(self):
        data, status_code = self.call_handler(
            exceptions.ValidationError({"email": ["Enter a valid email address."]})
        )
        self.assertEqual(status_code, 400)
        self.assertEqual(data["error_code"], VALIDATION_ERROR_CODE)
        self.assertEqual(data["detail"], {"email": ["Enter a valid email address."]})

    def test_handles_django_validation_error(self):
        data, status_code = self.call_handler(DjangoValidationError({"name": ["Required."]}))
        self.assertEqual(status_code, 400)
        self.assertEqual(data["error_code"], VALIDATION_ERROR_CODE)
        self.assertEqual(data["detail"], {"name": ["Required."]})

    def test_handles_http404(self):
        data, status_code = self.call_handler(Http404())
        self.assertEqual(status_code, 404)
        self.assertEqual(data["error_code"], NOT_FOUND_ERROR_CODE)

    def test_handles_permission_denied(self):
        data, status_code = self.call_handler(PermissionDenied())
        self.assertEqual(status_code, 403)
        self.assertEqual(data["error_code"], FORBIDDEN_ERROR_CODE)

    def test_handles_not_authenticated(self):
        data, status_code = self.call_handler(exceptions.NotAuthenticated())
        self.assertEqual(status_code, 401)
        self.assertEqual(data["error_code"], UNAUTHORIZED_ERROR_CODE)

    def test_handles_app_error(self):
        data, status_code = self.call_handler(
            AppError(detail="Custom failure.", error_code="CUSTOM_ERROR", status_code=418)
        )
        self.assertEqual(status_code, 418)
        self.assertEqual(data["error_code"], "CUSTOM_ERROR")
        self.assertEqual(data["detail"], "Custom failure.")

    def test_handles_app_error_subclass(self):
        data, status_code = self.call_handler(NotFoundError(detail="User not found."))
        self.assertEqual(status_code, 404)
        self.assertEqual(data["error_code"], NOT_FOUND_ERROR_CODE)
        self.assertEqual(data["detail"], "User not found.")

    def test_handles_app_error_subclass_default_message(self):
        data, status_code = self.call_handler(ConflictError())
        self.assertEqual(status_code, 409)
        self.assertEqual(data["error_code"], "CONFLICT")
        self.assertEqual(data["detail"], "Conflict.")

    @override_settings(DEBUG=False)
    @patch("core.exceptions.handler.logger")
    def test_handles_unexpected_exception_without_debug_detail(self, mock_logger):
        data, status_code = self.call_handler(ValueError("secret internals"))
        self.assertEqual(status_code, 500)
        self.assertEqual(data["error_code"], INTERNAL_ERROR_CODE)
        self.assertEqual(data["detail"], "An unexpected error occurred.")
        mock_logger.exception.assert_called_once()

    @override_settings(DEBUG=True)
    @patch("core.exceptions.handler.logger")
    def test_handles_unexpected_exception_with_debug_detail(self, mock_logger):
        data, status_code = self.call_handler(ValueError("secret internals"))
        self.assertEqual(status_code, 500)
        self.assertEqual(data["error_code"], INTERNAL_ERROR_CODE)
        self.assertEqual(data["detail"], "secret internals")
        mock_logger.exception.assert_called_once()
