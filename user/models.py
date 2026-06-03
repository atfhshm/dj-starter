from typing import Any, ClassVar, Self
from zoneinfo import ZoneInfo

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from timezone_field import TimeZoneField

__all__ = ["User"]


class UserManager(BaseUserManager):
    """
    Custom manager for the :class:`User` model.

    Overrides Django's default ``BaseUserManager`` to account for the fact
    that ``User`` uses ``email`` as its ``USERNAME_FIELD`` and additionally
    requires ``name`` and ``phone_number`` at creation time. Use
    :meth:`create_superuser` to create admin accounts from management
    commands (e.g. ``createsuperuser``).
    """

    def _create_user(self, name, phone_number, email, password, **extra_fields):
        """
        Create and persist a :class:`User` with the given credentials.

        Validates that the required identity fields (``name``, ``email``,
        ``phone_number``) are provided, normalises the email, hashes the
        password and saves the user. Intended as an internal helper for
        public creation methods such as :meth:`create_superuser`.
        """
        if not name:
            raise ValueError(_("The Name field must be set"))
        if not email:
            raise ValueError(_("The Email field must be set"))
        if not phone_number:
            raise ValueError(_("The Phone Number field must be set"))
        email = self.normalize_email(email)
        user: User = self.model(name=name, phone_number=phone_number, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        name: str,
        phone_number: str,
        email: str,
        password: str,
        **extra_fields: Any,
    ):
        """
        Create a superuser with full staff and admin privileges.

        Forces ``is_staff`` and ``is_superuser`` to ``True`` (raising
        ``ValueError`` if a caller tries to override them to ``False``)
        and delegates the actual creation to :meth:`_create_user`.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self._create_user(name, phone_number, email, password, **extra_fields)


class User(
    AbstractBaseUser,
    PermissionsMixin,
):
    """
    Represents a person's account on the platform.

    This is the project's custom auth user model (referenced by
    ``AUTH_USER_MODEL``). It extends Django's ``AbstractBaseUser`` and
    ``PermissionsMixin`` and uses ``email`` as the unique
    ``USERNAME_FIELD``; ``name`` and ``phone_number`` are also required
    on creation (see :class:`UserManager`).

    The model groups its fields into the following concerns:

    - **Identity & profile**: ``name``, ``email``, ``phone_number``,
      ``avatar``, ``timezone`` together with their verification flags
      (``email_verified``, ``phone_number_verified``).
    - **Account status**: ``is_active`` (soft-delete / disable flag) and
      ``is_staff`` (admin-site access).
    - **Moderation**: ``is_banned`` along with ``banned_reason``,
      ``banned_at`` and ``banned_until`` for temporary or permanent bans.
    - **Security**: ``two_factor_enabled`` and the (currently disabled)
      hooks for storing 2FA secrets and recovery codes.
    - **Audit trail**: ``last_login_at``/``last_login_ip``,
      ``last_logout_at``/``last_logout_ip`` and ``last_login_method``
      track how and when the user most recently authenticated.
    - **Timestamps**: ``date_joined`` and ``updated_at`` are managed
      automatically by Django.

    Active login sessions are stored separately on the related
    ``sessions`` reverse relation (see :class:`Session`).
    """

    class LoginMethod(models.TextChoices):
        """Enumerates the authentication methods supported at sign-in."""

        CREDENTIALS = "credentials", _("Credentials")
        MAGIC_LINK = "magic_link", _("Magic Link")
        GOOGLE = "google", _("Google")
        APPLE = "apple", _("Apple")

    class Locale(models.TextChoices):
        """Enumerates the locales supported by the platform."""

        EN = "en", _("English")
        AR = "ar", _("Arabic")

    # basic info
    name = models.CharField(
        verbose_name=_("name"),
        max_length=128,
        help_text=_("The full name of the user."),
    )
    email = models.EmailField(
        verbose_name=_("email"),
        unique=True,
        db_index=True,
        help_text=_("The email address of the user."),
        error_messages={
            "unique": _("A user with that email already exists."),
        },
    )
    email_verified = models.BooleanField(
        verbose_name=_("email verified"),
        default=False,
        help_text=_("Designates whether the user's email is verified."),
    )
    phone_number = PhoneNumberField(
        verbose_name=_("phone number"),
        db_index=True,
        unique=True,
        null=True,
        blank=True,
        help_text=_("The phone number of the user."),
        error_messages={
            "unique": _("A user with that phone number already exists."),
        },
    )
    phone_number_verified = models.BooleanField(
        verbose_name=_("phone number verified"),
        default=False,
        help_text=_("Designates whether the user's phone number is verified."),
    )
    avatar = models.ImageField(
        verbose_name=_("avatar"),
        help_text=_("The avatar of the user."),
        upload_to="avatars/",
        null=True,
        blank=True,
    )

    # locale & timezone
    country = CountryField(
        verbose_name=_("country"),
        help_text=_("The country of the user."),
        null=True,
        blank=True,
    )
    locale = models.CharField(
        verbose_name=_("locale"),
        max_length=128,
        help_text=_("The locale of the user."),
        choices=Locale.choices,
        default=Locale.EN,
    )
    timezone = TimeZoneField(
        verbose_name=_("timezone"),
        help_text=_("The timezone of the user."),
        default=ZoneInfo("UTC"),
        choices_display="WITH_GMT_OFFSET",
    )

    # status
    is_staff = models.BooleanField(
        verbose_name=_("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        verbose_name=_("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )

    # banning status
    is_banned = models.BooleanField(
        verbose_name=_("banned"),
        default=False,
        help_text=_("Designates whether the user is banned."),
    )
    banned_reason = models.TextField(
        verbose_name=_("banned reason"),
        help_text=_("The reason the user was banned."),
        default="",
        blank=True,
    )
    banned_at = models.DateTimeField(
        verbose_name=_("banned at"),
        help_text=_("The date and time the user was banned."),
        null=True,
        blank=True,
    )
    banned_until = models.DateTimeField(
        verbose_name=_("banned until"),
        help_text=_("The date and time the user will be unbanned."),
        null=True,
        blank=True,
    )

    two_factor_enabled = models.BooleanField(
        verbose_name=_("two factor enabled"),
        default=False,
        help_text=_("Designates whether the user has two factor authentication enabled."),
    )
    last_login_method = models.CharField(
        verbose_name=_("last login method"),
        max_length=128,
        choices=LoginMethod.choices,
        help_text=_("The method the user last logged in with."),
        default=LoginMethod.CREDENTIALS,
        editable=False,
    )
    last_login = models.DateTimeField(
        verbose_name=_("last login"),
        help_text=_("The date and time the user last logged in."),
        null=True,
        blank=True,
        editable=False,
    )
    last_login_ip = models.GenericIPAddressField(
        verbose_name=_("last login ip"),
        help_text=_("The IP address the user last logged in from."),
        null=True,
        blank=True,
        editable=False,
    )
    last_logout = models.DateTimeField(
        verbose_name=_("last logout at"),
        help_text=_("The date and time the user last logged out."),
        null=True,
        blank=True,
        editable=False,
    )
    last_logout_ip = models.GenericIPAddressField(
        verbose_name=_("last logout ip"),
        help_text=_("The IP address the user last logged out from."),
        null=True,
        blank=True,
        editable=False,
    )

    # Timestamp dates
    updated_at = models.DateTimeField(
        _("updated at"),
        auto_now=True,
        help_text=_("The date and time the user was last updated."),
    )
    date_joined = models.DateTimeField(
        _("date joined"),
        help_text=_("The date and time the user joined the platform."),
        auto_now_add=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "phone_number"]
    objects: ClassVar[UserManager[Self]] = UserManager()

    class Meta:
        db_table = "users"
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ("-date_joined", "-id")

    def __str__(self):
        return f"<User: {self.pk}>-{self.name}"
