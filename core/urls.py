"""
URL configuration for the project.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.authtoken import views

from core.root_view import RootView

urlpatterns = [
    path("", RootView.as_view(), name="root"),
    path("admin/", admin.site.urls),
    path("api-token-auth/", views.obtain_auth_token),
]


if settings.ENABLE_OPENAPI:
    urlpatterns += [
        path(
            "api/schema/",
            SpectacularAPIView.as_view(),
            name="schema",
        ),
        path(
            "api/swagger/",
            SpectacularSwaggerView.as_view(
                url_name="schema",
            ),
            name="swagger",
        ),
        path(
            "api/redoc/",
            SpectacularRedocView.as_view(
                url_name="schema",
            ),
            name="redoc",
        ),
    ]

if settings.SILK_ENABLED:
    urlpatterns += [
        path(
            "silk/",
            include(
                "silk.urls",
                namespace="silk",
            ),
        ),
    ]
