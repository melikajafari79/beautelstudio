# apps/booking/models.py
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from apps.services.models import Service
from apps.staffpanel.models import StaffMember


class Appointment(TimeStampedModel):
    class StatusChoices(models.TextChoices):
        PENDING = "pending", _("Pending")
        CONFIRMED = "confirmed", _("Confirmed")
        COMPLETED = "completed", _("Completed")
        CANCELED = "canceled", _("Canceled")
        NO_SHOW = "no_show", _("No show")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appointments",
        verbose_name=_("User"),
    )
    staff = models.ForeignKey(
        StaffMember,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="appointments",
        verbose_name=_("Staff"),
    )
    appointment_date = models.DateField(
        verbose_name=_("Appointment date"),
    )
    start_time = models.TimeField(
        verbose_name=_("Start time"),
    )
    end_time = models.TimeField(
        verbose_name=_("End time"),
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        verbose_name=_("Status"),
    )
    customer_note = models.TextField(
        blank=True,
        verbose_name=_("Customer note"),
    )
    admin_note = models.TextField(
        blank=True,
        verbose_name=_("Admin note"),
    )
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Total price"),
    )

    class Meta:
        verbose_name = _("Appointment")
        verbose_name_plural = _("Appointments")
        ordering = ("-appointment_date", "-start_time")
        indexes = [
            models.Index(fields=["appointment_date", "start_time"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.appointment_date} {self.start_time}"


class AppointmentItem(models.Model):
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Appointment"),
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="appointment_items",
        verbose_name=_("Service"),
    )
    title_snapshot = models.CharField(
        max_length=200,
        verbose_name=_("Title snapshot"),
    )
    duration_snapshot = models.PositiveIntegerField(
        verbose_name=_("Duration snapshot"),
    )
    price_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Price snapshot"),
    )

    class Meta:
        verbose_name = _("Appointment item")
        verbose_name_plural = _("Appointment items")

    def __str__(self):
        return self.title_snapshot
