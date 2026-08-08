"""
تصمیم طراحی: StaffService, StaffSchedule, StaffLeave, StaffTimeBlock
به‌صورت مستقل در منوی ادمین ثبت نشده‌اند — فقط inline داخل صفحه‌ی
ویرایش خودِ پرسنل. مدیر سالن همه‌چیز مربوط به یک پرسنل را در یک صفحه
می‌بیند و ویرایش می‌کند.
"""
from django.contrib import admin
import django_jalali.admin as jadmin  # جدید: فعال‌سازی ویجت تقویم شمسی در کل پنل ادمین این اپ

from .models import StaffLeave, StaffMember, StaffSchedule, StaffService, StaffTimeBlock


class StaffServiceInline(admin.TabularInline):
    model = StaffService
    extra = 1
    autocomplete_fields = ['service']


class StaffScheduleInline(admin.TabularInline):
    model = StaffSchedule
    extra = 1


class StaffLeaveInline(admin.TabularInline):
    model = StaffLeave
    extra = 0


class StaffTimeBlockInline(admin.TabularInline):
    model = StaffTimeBlock
    extra = 0


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'job_title', 'years_of_experience', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('full_name', 'job_title')
    inlines = [StaffServiceInline, StaffScheduleInline, StaffLeaveInline, StaffTimeBlockInline]

    # جدید: گروه‌بندی فرم — بخش «مجوزهای پنل پرسنل» از بقیه جدا شد تا
    # مدیر سالن دقیقاً بداند این چک‌باکس‌ها چه اختیاری به پرسنل می‌دهند.
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('user', 'full_name', 'slug', 'job_title', 'bio', 'photo', 'years_of_experience', 'is_active', 'order'),
        }),
        ('مجوزهای پنل پرسنل', {
            'fields': ('can_manage_own_appointments', 'can_toggle_own_availability', 'can_upload_portfolio'),
            'description': 'این مجوزها تعیین می‌کنند این پرسنل در پنل اختصاصی خودش چه کارهایی می‌تواند انجام دهد.',
        }),
    )
