# apps/core/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated at"),
    )

    class Meta:
        abstract = True


class IsActiveModel(models.Model):
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is active"),
    )

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(
        default=False,
        verbose_name=_("Is deleted"),
    )
    deleted_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Deleted at"),
    )

    class Meta:
        abstract = True


class SEOMixin(models.Model):
    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name=_("Slug"),
    )

    class Meta:
        abstract = True
