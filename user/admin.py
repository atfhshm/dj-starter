from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from user.models import User

__all__ = [
    "UserAdminConfig",
]


@admin.register(User)
class UserAdminConfig(UserAdmin):
    list_display = (
        "id",
        "name",
        "email",
        "email_verified",
        "phone_number",
        "phone_number_verified",
        "is_active",
        "is_staff",
        "is_superuser",
        "is_banned",
        "last_login_method",
        "last_login",
        "last_login_ip",
        "last_logout",
        "last_logout_ip",
        "updated_at",
        "date_joined",
    )
    readonly_fields = [
        "date_joined",
        "updated_at",
        "last_login",
    ]

    fieldsets = (
        (
            "basic info",
            {
                "fields": (
                    "name",
                    "email",
                    "email_verified",
                    "phone_number",
                    "phone_number_verified",
                    "avatar",
                    "timezone",
                    "locale",
                    "country",
                    "is_banned",
                    "banned_reason",
                    "banned_at",
                    "banned_until",
                    "password",
                )
            },
        ),
        (
            "groups and permissions",
            {
                "fields": (
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "user status",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                )
            },
        ),
        (
            "important dates",
            {
                "fields": (
                    "date_joined",
                    "updated_at",
                    "last_login",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "name",
                    "email",
                    "phone_number",
                    "password1",
                    "password2",
                    "avatar",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )

    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("email", "phone_number")
    filter_horizontal = []
    ordering = ("-id", "email")
