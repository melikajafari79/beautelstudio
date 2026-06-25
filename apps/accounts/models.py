# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, IsActiveModel


phone_validator = RegexValidator(
    regex=r"^09\d{9}$",
    message=_("Phone number must be in the format 09xxxxxxxxx."),
)

class User(AbstractUser, TimeStampedModel):
    email = models.EmailField(blank=True, null=True, unique=True, verbose_name=_("Email"))
    phone_number = models.CharField(max_length=11, unique=True, validators=[phone_validator], verbose_name=_("Phone number"))
    birth_date = models.DateField(blank=True, null=True, verbose_name=_("Birth date"))
    is_phone_verified = models.BooleanField(default=False, verbose_name=_("Is phone verified"))
    referral_source = models.ForeignKey(
        "accounts.ReferralSource",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="users",
        verbose_name=_("Referral source"),
    )

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ("-created_at",)

    def __str__(self):
        return self.username or self.phone_number


class ReferralSource(IsActiveModel, TimeStampedModel):
    title = models.CharField(
        max_length=150,
        unique=True,
        verbose_name=_("Title"),
        help_text=_("Examples: Instagram, Google, Friend introduction"),
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Sort order"),
    )

    class Meta:
        verbose_name = _("Referral source")
        verbose_name_plural = _("Referral sources")
        ordering = ("sort_order", "title")

    def __str__(self):
        return self.title


class OTPRequest(TimeStampedModel):
    class OTPStatus(models.TextChoices):
        PENDING = "pending", _("Pending")
        VERIFIED = "verified", _("Verified")
        EXPIRED = "expired", _("Expired")
        FAILED = "failed", _("Failed")

    phone_number = models.CharField(
        max_length=11,
        validators=[phone_validator],
        db_index=True,
        verbose_name=_("Phone number"),
    )
    code = models.CharField(
        max_length=6,
        verbose_name=_("Code"),
    )
    status = models.CharField(
        max_length=20,
        choices=OTPStatus.choices,
        default=OTPStatus.PENDING,
        verbose_name=_("Status"),
    )
    expires_at = models.DateTimeField(
        verbose_name=_("Expires at"),
    )
    verified_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Verified at"),
    )
    attempt_count = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_("Attempt count"),
    )
    max_attempts = models.PositiveSmallIntegerField(
        default=5,
        verbose_name=_("Max attempts"),
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=_("IP address"),
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=_("User agent"),
    )

    class Meta:
        verbose_name = _("OTP request")
        verbose_name_plural = _("OTP requests")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["phone_number", "status"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.phone_number} - {self.code}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def can_verify(self):
        return (
            self.status == self.OTPStatus.PENDING
            and not self.is_expired
            and self.attempt_count < self.max_attempts
        )
