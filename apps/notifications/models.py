# apps/notifications/models.py
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Notification(TimeStampedModel):
    class NotificationType(models.TextChoices):
        SMS = "sms", _("SMS")
        SYSTEM = "system", _("System")
        EMAIL = "email", _("Email")

    class StatusChoices(models.TextChoices):
        PENDING = "pending", _("Pending")
        SENT = "sent", _("Sent")
        FAILED = "failed", _("Failed")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("User"),
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        verbose_name=_("Notification type"),
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Title"),
    )
    message = models.TextField(
        verbose_name=_("Message"),
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        verbose_name=_("Status"),
    )
    sent_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Sent at"),
    )
    error_message = models.TextField(
        blank=True,
        verbose_name=_("Error message"),
    )

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user} - {self.notification_type}"
