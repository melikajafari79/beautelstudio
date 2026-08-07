from django.contrib import admin
from .models import Category, Service

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'is_active', 'created_at')
    search_fields = ('name',)
    list_filter = ('is_active',)
    readonly_fields = ()

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category', 'base_price', 'discount_price',
        'duration', 'is_active', 'requires_staff_confirmation', 'requires_deposit',
    )
    list_filter = ('category', 'is_active', 'is_parallel', 'requires_staff_confirmation', 'requires_deposit')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    autocomplete_fields = ('category',)
    ordering = ('category', 'name')