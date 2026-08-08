"""
نسخه‌ی به‌روزشده: فیلدهای قیمت جدید اضافه شدند و فرم با fieldsets
گروه‌بندی شد — چون کاربر این پنل، مدیر سالن (غیرفنی) است، نه برنامه‌نویس؛
گروه‌بندی و توضیح روی هر بخش، از پرکردن اشتباه فرم جلوگیری می‌کند.
"""
from django.contrib import admin
import django_jalali.admin as jadmin  # جدید: فعال‌سازی ویجت تقویم شمسی

from .models import Category, Service


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')
    search_fields = ('name',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category', 'base_price', 'show_price',
        'price_display_mode', 'is_active', 'requires_deposit',
    )
    list_filter = (
        'category', 'is_active', 'is_parallel',
        'show_price', 'price_display_mode',
        'requires_staff_confirmation', 'requires_deposit',
    )
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    autocomplete_fields = ('category',)

    # جدید: گروه‌بندی فرم — به‌خصوص بخش «نمایش قیمت در سایت» با توضیح روشن
    # می‌کند که این تنظیمات فقط روی نمایش عمومی اثر دارد، نه روی قیمت واقعی.
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('category', 'name', 'slug', 'description', 'image', 'order', 'is_active'),
        }),
        ('مدت زمان و اجرا', {
            'fields': ('duration', 'is_parallel', 'requires_staff_confirmation'),
        }),
        ('قیمت داخلی (مبنای محاسبات واقعی)', {
            'fields': ('base_price', 'discount_price'),
            'description': 'این مقادیر مبنای محاسبات واقعی سیستم (رزرو/فاکتور) هستند.',
        }),
        ('نمایش قیمت در سایت', {
            'fields': ('show_price', 'price_display_mode', 'price_min', 'price_max'),
            'description': (
                'این بخش فقط روی نمایش عمومی در سایت اثر می‌گذارد. '
                'اگر «نمایش قیمت» خاموش باشد، بقیه‌ی این فیلدها نادیده گرفته می‌شوند. '
                'فیلدهای «حداقل/حداکثر قیمت» فقط وقتی «محدوده قیمت» انتخاب شده باشد پر شوند.'
            ),
        }),
        ('بیعانه', {
            'fields': ('requires_deposit', 'deposit_amount'),
        }),
    )
