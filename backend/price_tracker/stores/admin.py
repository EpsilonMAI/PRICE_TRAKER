"""Административная панель для управления магазинами."""
from django.contrib import admin

from .models import Stores


@admin.register(Stores)
class StoresAdmin(admin.ModelAdmin):
    """Административная панель для интернет-магазинов."""
    list_display = ('name', 'rating', 'is_active', 'parser_enabled', 'created_at')
    list_filter = ('is_active', 'parser_enabled', 'created_at')
    search_fields = ('name', 'base_url')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_active', 'parser_enabled')
    date_hierarchy = 'created_at'
