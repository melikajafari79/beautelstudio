# apps/services/models.py
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, IsActiveModel, SEOMixin


class ServiceCategory(TimeStampedModel, IsActiveModel, SEOMixin):
    title = models.CharField(
        max_length=150,
        unique=True,
        verbose_name=_("Title"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
    )
    image = models.ImageField(
        upload_to="services/categories/",
        blank=True,
        null=True,
        verbose_name=_("Image"),
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Sort order"),
    )

    class Meta:
        verbose_name = _("Service category")
        verbose_name_plural = _("Service categories")
        ordering = ("sort_order", "title")

    def __str__(self):
        return self.title


class Service(TimeStampedModel, IsActiveModel, SEOMixin):
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.PROTECT,
        related_name="services",
        verbose_name=_("Category"),
    )
    title = models.CharField(
        max_length=200,
        unique=True,
        verbose_name=_("Title"),
    )
    short_description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Short description"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
    )
    duration_minutes = models.PositiveIntegerField(
        validators=[MinValueValidator(5)],
        verbose_name=_("Duration (minutes)"),
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Price"),
        help_text=_("Price in Toman."),
    )
    discount_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        verbose_name=_("Discount price"),
    )
    image = models.ImageField(
        upload_to="services/",
        blank=True,
        null=True,
        verbose_name=_("Image"),
    )
    requires_consultation = models.BooleanField(
        default=False,
        verbose_name=_("Requires consultation"),
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Sort order"),
    )

    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")
        ordering = ("sort_order", "title")
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return self.title

    @property
    def final_price(self):
        if self.discount_price is not None and self.discount_price >= 0:
            return self.discount_price
        return self.price
