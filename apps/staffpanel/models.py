# apps/staffpanel/models.py
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, IsActiveModel


class StaffMember(TimeStampedModel, IsActiveModel):
    class GenderChoices(models.TextChoices):
        FEMALE = "female", _("Female")
        MALE = "male", _("Male")
        OTHER = "other", _("Other")

    first_name = models.CharField(
        max_length=100,
        verbose_name=_("First name"),
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name=_("Last name"),
    )
    role_title = models.CharField(
        max_length=150,
        verbose_name=_("Role title"),
        help_text=_("Examples: Hair stylist, Nail artist"),
    )
    bio = models.TextField(
        blank=True,
        verbose_name=_("Bio"),
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Phone number"),
    )
    email = models.EmailField(
        blank=True,
        verbose_name=_("Email"),
    )
    avatar = models.ImageField(
        upload_to="staff/avatars/",
        blank=True,
        null=True,
        verbose_name=_("Avatar"),
    )
    gender = models.CharField(
        max_length=10,
        choices=GenderChoices.choices,
        blank=True,
        verbose_name=_("Gender"),
    )
    experience_years = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(80)],
        verbose_name=_("Experience years"),
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Sort order"),
    )

    services = models.ManyToManyField(
        "services.Service",
        blank=True,
        related_name="staff_members",
        verbose_name=_("Services"),
    )

    class Meta:
        verbose_name = _("Staff member")
        verbose_name_plural = _("Staff members")
        ordering = ("sort_order", "first_name", "last_name")

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()


class StaffSchedule(TimeStampedModel):
    class WeekDayChoices(models.IntegerChoices):
        SATURDAY = 0, _("Saturday")
        SUNDAY = 1, _("Sunday")
        MONDAY = 2, _("Monday")
        TUESDAY = 3, _("Tuesday")
        WEDNESDAY = 4, _("Wednesday")
        THURSDAY = 5, _("Thursday")
        FRIDAY = 6, _("Friday")

    staff = models.ForeignKey(
        StaffMember,
        on_delete=models.CASCADE,
        related_name="schedules",
        verbose_name=_("Staff"),
    )
    week_day = models.PositiveSmallIntegerField(
        choices=WeekDayChoices.choices,
        verbose_name=_("Week day"),
    )
    start_time = models.TimeField(
        verbose_name=_("Start time"),
    )
    end_time = models.TimeField(
        verbose_name=_("End time"),
    )
    is_off = models.BooleanField(
        default=False,
        verbose_name=_("Is off"),
    )

    class Meta:
        verbose_name = _("Staff schedule")
        verbose_name_plural = _("Staff schedules")
        ordering = ("staff", "week_day", "start_time")
        unique_together = ("staff", "week_day", "start_time", "end_time")

    def __str__(self):
        return f"{self.staff} - {self.week_day}"
