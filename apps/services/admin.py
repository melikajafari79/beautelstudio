from django.contrib import admin
from .models import Category, Service

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'duration', 'base_price', 'is_parallel', 'is_active')
    list_filter = ('category', 'is_active', 'is_parallel')
    search_fields = ('name', 'description')
    ordering = ('category', 'name')