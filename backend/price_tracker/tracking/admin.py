"""Административная панель для управления отслеживанием товаров."""
from django.contrib import admin

from .models import PriceHistory, TrackingItems


@admin.register(TrackingItems)
class TrackingItemsAdmin(admin.ModelAdmin):
    """Административная панель для отслеживаемых товаров."""
    list_display = ('user', 'product', 'store', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'store')
    search_fields = ('user__username', 'product__name', 'custom_name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    """Административная панель для истории цен."""
    list_display = ('tracking_item', 'price', 'old_price', 'in_stock', 'collected_at')
    list_filter = ('in_stock', 'collected_at')
    search_fields = ('tracking_item__product__name',)
    readonly_fields = ('collected_at',)
    date_hierarchy = 'collected_at'
