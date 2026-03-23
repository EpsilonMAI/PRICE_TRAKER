from rest_framework import serializers
from .models import TrackingItems, PriceHistory


class TrackingItemSerializer(serializers.ModelSerializer):
    """Сериализатор для трэка товара"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    
    current_price = serializers.SerializerMethodField()
    last_old_price = serializers.SerializerMethodField()
    price_updated_at = serializers.SerializerMethodField()

    class Meta:
        model = TrackingItems
        fields = (
            "id", "user", "user_name", "product", "product_name", 
            "store", "store_name", "source_url", "custom_name", 
            "is_active", "last_checked_at", "last_success_at", 
            "last_status", "created_at", "updated_at",
            "current_price", "last_old_price", "price_updated_at"
        )
        read_only_fields = ("id", "last_checked_at", "last_status", "created_at", "updated_at")
    
    def get_current_price(self, obj):
        """Получить последнюю цену"""
        latest = obj.price_history.first()  # ordering = ['-collected_at'] в модели
        return latest.price if latest else None
    
    def get_last_old_price(self, obj):
        """Получить зачёркнутую цену"""
        latest = obj.price_history.first()
        return latest.old_price if latest else None
    
    def get_price_updated_at(self, obj):
        """Когда последний раз обновлялась цена"""
        latest = obj.price_history.first()
        return latest.collected_at if latest else None


class PriceHistorySerializer(serializers.ModelSerializer):
    """Сериализатор для истории цен"""
    product_name = serializers.CharField(source='tracking_item.product.name', read_only=True)
    
    class Meta:
        model = PriceHistory
        fields = (
            "id", "tracking_item", "product_name", "price", 
            "old_price", "currency", "in_stock", "collected_at"
        )
        read_only_fields = ("id", "collected_at")
