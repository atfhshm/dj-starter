from django.db import models
from django.utils.translation import gettext_lazy as _


class CreatedAtMixin:
    """
    A mixin that adds a created_at field to a model.
    """

    created_at = models.DateTimeField(
        verbose_name=_("created at"),
        help_text=_("The date and time the record was created."),
        db_index=True,
        auto_now_add=True,
        editable=False,
    )


class UpdatedAtMixin:
    """
    A mixin that adds a updated_at field to a model.
    """

    updated_at = models.DateTimeField(
        verbose_name=_("updated at"),
        help_text=_("The date and time the record was updated."),
        db_index=True,
        auto_now=True,
        editable=False,
    )


class TimestampMixin(
    CreatedAtMixin,
    UpdatedAtMixin,
):
    """
    A mixin that adds a created_at and updated_at fields to a model.
    """

    class Meta:
        abstract = True
