"""
OpenAPI Configuration for the project.
"""

__all__ = [
    "OPENAPI_SETTINGS",
]

OPENAPI_SETTINGS = {
    "TITLE": "Django Starter API Server",
    "DESCRIPTION": "Django Starter API Server schema and documentation.",
    "VERSION": "0.1.0",
    "CONTACT": {
        "name": "Atef hesham",
        "url": "https://atfhshm.com",
        "email": "atefheshamattia@gmail.com",
    },
    "SERVERS": [
        {"url": "http://localhost:8000", "description": "Local"},
        {"url": "https://your-domain.com", "description": "Production"},
    ],
    "SERVE_INCLUDE_SCHEMA": True,
    "COMPONENT_SPLIT_REQUEST": True,
    "POSTPROCESSING_HOOKS": [],
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    "SERVE_PERMISSIONS": [
        "rest_framework.permissions.IsAdminUser",
    ],
    "SERVE_AUTHENTICATION": [
        "rest_framework.authentication.SessionAuthentication",
    ],
}
