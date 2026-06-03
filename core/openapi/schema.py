from typing import Any

from drf_spectacular.plumbing import build_array_type, build_object_type

from core.exceptions.const import VALIDATION_ERROR_CODE

Schema = dict[str, Any]

__all__ = [
    "get_error_schema",
]


def string_schema(**kwargs: Any) -> Schema:
    return {"type": "string", **kwargs}


def nested_field_error_schema() -> Schema:
    """Schema for `{ [nestedField: string]: string[] }`."""
    return build_object_type(
        description="Nested field validation errors.",
        additionalProperties=build_array_type(string_schema()),
    )


def field_error_value_schema() -> Schema:
    """Schema for field values: `string | string[] | { [nestedField: string]: string[] }`."""
    return {
        "oneOf": [
            string_schema(description="Human-readable error message."),
            {
                **build_array_type(string_schema()),
                "description": "Multiple errors on a single field.",
            },
            nested_field_error_schema(),
        ]
    }


def validation_error_detail_schema() -> Schema:
    """Schema for `{ [field: string]: FieldErrorValue }` validation payloads."""
    return build_object_type(
        description="Field-level validation errors.",
        additionalProperties=field_error_value_schema(),
        example={
            "email": "Enter a valid email address.",
            "password": [
                "This password is too short.",
                "This password is too common.",
            ],
            "address": {
                "city": ["This field is required."],
                "zip_code": ["Enter a valid zip code."],
            },
        },
    )


def error_detail_schema() -> Schema:
    """Schema for the detail payload returned by app_error_handler."""
    return {
        "oneOf": [
            string_schema(description="Human-readable error message."),
            {
                **build_array_type(string_schema()),
                "description": "Multiple error messages.",
            },
            validation_error_detail_schema(),
        ]
    }


def get_error_schema(error_codes: list[str] | None = None) -> Schema:
    """OpenAPI schema for the standard error envelope returned by app_error_handler."""
    error_code_schema: Schema = {
        "type": "string",
        "description": "Machine-readable error code.",
    }
    if error_codes is not None:
        error_code_schema["enum"] = error_codes

    is_validation_error = error_codes == [VALIDATION_ERROR_CODE]
    detail_schema = (
        validation_error_detail_schema() if is_validation_error else error_detail_schema()
    )

    schema = build_object_type(
        properties={
            "error_code": error_code_schema,
            "detail": detail_schema,
        },
        required=["error_code", "detail"],
    )

    if is_validation_error:
        schema["example"] = {
            "error_code": VALIDATION_ERROR_CODE,
            "detail": validation_error_detail_schema()["example"],
        }

    return schema
