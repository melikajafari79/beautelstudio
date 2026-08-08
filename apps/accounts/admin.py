from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import OTPRequest, ReferralSource, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    گسترش UserAdmin پیش‌فرض جنگو برای نمایش/ویرایش فیلدهای اختصاصیِ این
    پروژه (شماره موبایل، تاریخ تولد، وضعیت تایید موبایل، شیوه‌ی آشنایی).
    """
    list_display = (
        "phone_number",
        "first_name",
        "last_name",
        "is_phone_verified",
        "is_active",
        "is_staff",
        "created_at",
    )
    list_filter = ("is_phone_verified", "is_active", "is_staff", "referral_source")
    search_fields = ("phone_number", "first_name", "last_name", "username", "email")
    ordering = ("-created_at",)

    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "اطلاعات اختصاصی سالن",
            {"fields": ("phone_number", "birth_date", "is_phone_verified", "referral_source")},
        ),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (
            "اطلاعات اختصاصی سالن",
            {"fields": ("phone_number", "birth_date", "referral_source")},
        ),
    )


@admin.register(ReferralSource)
class ReferralSourceAdmin(admin.ModelAdmin):
    list_display = ("title", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    search_fields = ("title",)


@admin.register(OTPRequest)
class OTPRequestAdmin(admin.ModelAdmin):
    """
    فقط برای مشاهده و عیب‌یابی (مثلاً وقتی کاربر می‌گوید کد را دریافت
    نکرده)؛ به همین دلیل امکان افزودن/ویرایش دستی از ادمین غیرفعال شده.
    """
    list_display = ("phone_number", "code", "status", "attempt_count", "created_at", "expires_at")
    list_filter = ("status",)
    search_fields = ("phone_number",)
    readonly_fields = [f.name for f in OTPRequest._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
