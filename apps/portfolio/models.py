# apps/portfolio/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, IsActiveModel, SEOMixin


class PortfolioCategory(TimeStampedModel, IsActiveModel, SEOMixin):
    title = models.CharField(
        max_length=150,
        unique=True,
        verbose_name=_("Title"),
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Sort order"),
    )

    class Meta:
        verbose_name = _("Portfolio category")
        verbose_name_plural = _("Portfolio categories")
        ordering = ("sort_order", "title")

    def __str__(self):
        return self.title


class Portfolio(TimeStampedModel, IsActiveModel, SEOMixin):
    category = models.ForeignKey(
        PortfolioCategory,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="portfolios",
        verbose_name=_("Category"),
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_("Title"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
    )
    image = models.ImageField(
        upload_to="portfolio/",
        verbose_name=_("Image"),
    )
    related_service = models.ForeignKey(
        "services.Service",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="portfolios",
        verbose_name=_("Related service"),
    )
    related_staff = models.ForeignKey(
        "staffpanel.StaffMember",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="portfolios",
        verbose_name=_("Related staff"),
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_("Is featured"),
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Sort order"),
    )

    class Meta:
        verbose_name = _("Portfolio")
        verbose_name_plural = _("Portfolios")
        ordering = ("sort_order", "-created_at")

    def __str__(self):
        return self.title
