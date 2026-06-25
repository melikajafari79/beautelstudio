# apps/cms/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, IsActiveModel, SEOMixin


class Page(TimeStampedModel, IsActiveModel, SEOMixin):
    title = models.CharField(
        max_length=200,
        verbose_name=_("Title"),
    )
    content = models.TextField(
        verbose_name=_("Content"),
    )
    meta_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Meta title"),
    )
    meta_description = models.CharField(
        max_length=320,
        blank=True,
        verbose_name=_("Meta description"),
    )

    class Meta:
        verbose_name = _("Page")
        verbose_name_plural = _("Pages")

    def __str__(self):
        return self.title


class FAQ(TimeStampedModel, IsActiveModel):
    question = models.CharField(
        max_length=255,
        verbose_name=_("Question"),
    )
    answer = models.TextField(
        verbose_name=_("Answer"),
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Sort order"),
    )

    class Meta:
        verbose_name = _("FAQ")
        verbose_name_plural = _("FAQs")
        ordering = ("sort_order", "id")

    def __str__(self):
        return self.question
