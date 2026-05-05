"""Административная панель для управления профилями пользователей."""
from django.contrib import admin

from .models import UserProfile, CustomRules


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Административная панель для профилей пользователей."""
    list_display = ('user', 'phone', 'created_at')
    search_fields = ('user__username', 'phone')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)


@admin.register(CustomRules)
class CustomRulesAdmin(admin.ModelAdmin):
    """Административная панель для настроек уведомлений."""
    list_display = ('notify_price_drop', 'notify_back_in_stock', 'notify_weekly_summary')
    list_filter = ('notify_price_drop', 'notify_back_in_stock', 'notify_weekly_summary')
