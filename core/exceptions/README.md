# Exceptions

All API errors are returned in a consistent envelope by `app_error_handler` (configured in `REST_FRAMEWORK["EXCEPTION_HANDLER"]`).

## Response shape

Every handled error returns:

```json
{
  "error_code": "MACHINE_READABLE_CODE",
  "detail": "Human-readable message or structured errors"
}
```

`detail` can be:

- a **string** — single message
- a **string array** — multiple non-field messages
- an **object** — field-level validation errors

Field-level validation errors follow this shape:

```
{
  [field: string]:
    ├── string
    ├── string[]
    └── { [nestedField: string]: string[] }
}
```

Example:

```json
{
  "error_code": "VALIDATION_ERROR",
  "detail": {
    "email": "Enter a valid email address.",
    "password": ["This password is too short.", "This password is too common."],
    "address": {
      "city": ["This field is required."],
      "zip_code": ["Enter a valid zip code."]
    }
  }
}
```

## Built-in exceptions

Import from `core.exceptions`:


| Class               | Status | `error_code`     |
| ------------------- | ------ | ---------------- |
| `BadRequestError`   | 400    | `BAD_REQUEST`    |
| `UnauthorizedError` | 401    | `UNAUTHORIZED`   |
| `ForbiddenError`    | 403    | `FORBIDDEN`      |
| `NotFoundError`     | 404    | `NOT_FOUND`      |
| `ConflictError`     | 409    | `CONFLICT`       |
| `AppError`          | 500    | `INTERNAL_ERROR` |


### Raising in a view or service

```python
from core.exceptions import NotFoundError

def get_user(user_id: int):
    user = User.objects.filter(pk=user_id).first()
    if user is None:
        raise NotFoundError(detail="User not found.")
    return user
```

Use the default message:

```python
raise NotFoundError()
```

Override at raise time:

```python
raise AppError(
    detail="Payment provider is unavailable.",
    error_code="PAYMENT_UNAVAILABLE",
    status_code=503,
)
```

## Creating a custom exception

Follow three steps: define a code constant, create a subclass, raise it where needed.

### 1. Add an error code constant

In `core/exceptions/const.py`:

```python
USER_NOT_FOUND_CODE = "USER_NOT_FOUND"
```

Export it from `__all__` and `core/exceptions/__init__.py` when you want it available project-wide.

### 2. Create a subclass

In `core/exceptions/exceptions.py` (or in your app module if the error is domain-specific):

```python
from django.utils.translation import gettext_noop as _

from core.exceptions.const import USER_NOT_FOUND_CODE
from core.exceptions import NotFoundError


class UserNotFoundError(NotFoundError):
    error_code = USER_NOT_FOUND_CODE
    default_message = _("User not found.")
```

Subclass an existing HTTP-level base (`NotFoundError`, `BadRequestError`, etc.) so the correct status code is set automatically. Only use `AppError` directly when none of the built-in bases fit.

### 3. Raise it

```python
from core.exceptions.exceptions import UserNotFoundError

raise UserNotFoundError()
# or with a custom message:
raise UserNotFoundError(detail="User with id 42 was not found.")
```

Response:

```json
{
  "error_code": "USER_NOT_FOUND",
  "detail": "User not found."
}
```

## Field-level errors on custom exceptions

`AppError` accepts structured `detail` for domain validation outside DRF serializers:

```python
raise BadRequestError(
    detail={
        "email": ["This email is already registered."],
        "profile": {
            "bio": ["Bio must be 500 characters or fewer."],
        },
    }
)
```

## DRF and Django exceptions

You do not need custom exceptions for standard DRF/Django cases. The handler normalizes them automatically:


| Raised                                      | `error_code`       | Status |
| ------------------------------------------- | ------------------ | ------ |
| `serializer.is_valid(raise_exception=True)` | `VALIDATION_ERROR` | 400    |
| `raise Http404()`                           | `NOT_FOUND`        | 404    |
| `raise PermissionDenied()`                  | `FORBIDDEN`        | 403    |
| DRF `NotAuthenticated`                      | `UNAUTHORIZED`     | 401    |
| Unhandled exception                         | `INTERNAL_ERROR`   | 500    |


Unhandled exceptions are logged. In production, `detail` is a generic message. In `DEBUG=True`, the exception message is included.

## OpenAPI documentation

Document error responses with `get_error_schema` from `core.openapi.schema`:

```python
from drf_spectacular.utils import extend_schema

from core.exceptions import NOT_FOUND_ERROR_CODE, USER_NOT_FOUND_CODE
from core.openapi.schema import get_error_schema


@extend_schema(
    responses={
        404: get_error_schema(error_codes=[USER_NOT_FOUND_CODE]),
    },
)
def retrieve(self, request, pk):
    ...
```

Notes:

- Pass `[VALIDATION_ERROR_CODE]` for 400 responses — the validation field-error schema and example are applied automatically.
- For other errors, pass the exact `error_code` string(s) the handler returns so the OpenAPI enum matches the API.

## File layout

```
core/exceptions/
├── const.py        # Shared error code constants
├── exceptions.py   # AppError and HTTP-level base subclasses
├── handler.py      # app_error_handler and detail normalization
└── tests/          # Handler and extract_detail tests
```

## Guidelines

- Prefer **specific subclasses** over raising `AppError` with inline `error_code` / `status_code`.
- Keep error codes **SCREAMING_SNAKE_CASE** strings in `const.py`.
- Use `**gettext_noop as _`** for default messages so they can be translated.
- One error code per distinct client-facing failure; reuse codes across endpoints when the meaning is the same.
