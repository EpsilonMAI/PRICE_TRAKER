"""Сериализаторы для отслеживания товаров и истории цен."""
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

from rest_framework import serializers
from django.db import transaction

from .models import TrackingItems, PriceHistory
from stores.models import Stores
from items.models import Products


class TrackingItemSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения отслеживаемых товаров.
    
    Включает дополнительные поля с информацией о пользователе, товаре, 
    магазине и последней цене из истории.
    
    Attributes:
        user_name: Имя пользователя, отслеживающего товар
        product_name: Название товара
        store_name: Название магазина
        current_price: Последняя зафиксированная цена
        last_old_price: Зачеркнутая (старая) цена
        price_updated_at: Дата последнего обновления цены
    """
    user_name = serializers.CharField(source='user.username', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    
    current_price = serializers.SerializerMethodField()
    last_old_price = serializers.SerializerMethodField()
    price_updated_at = serializers.SerializerMethodField()
    sparkline_points = serializers.SerializerMethodField()

    class Meta:
        model = TrackingItems
        fields = (
            "id", "user", "user_name", "product", "product_name", 
            "store", "store_name", "source_url", "custom_name", 
            "is_active", "last_checked_at", "last_success_at", 
            "last_status", "created_at", "updated_at",
            "current_price", "last_old_price", "price_updated_at",
            "sparkline_points",
        )
        read_only_fields = ("id", "last_checked_at", "last_status", "created_at", "updated_at")
    
    def get_current_price(self, obj: TrackingItems) -> Optional[Decimal]:
        """Получить последнюю актуальную цену товара.
        
        Args:
            obj: Экземпляр отслеживаемого товара
            
        Returns:
            Optional[Decimal]: Последняя цена или None
        """
        latest = obj.price_history.first()  # ordering = ['-collected_at'] в модели
        return latest.price if latest else None
    
    def get_last_old_price(self, obj: TrackingItems) -> Optional[Decimal]:
        """Получить зачеркнутую (старую) цену товара.
        
        Args:
            obj: Экземпляр отслеживаемого товара
            
        Returns:
            Optional[Decimal]: Старая цена или None
        """
        latest = obj.price_history.first()
        return latest.old_price if latest else None
    
    def get_price_updated_at(self, obj: TrackingItems) -> Optional[datetime]:
        """Получить дату последнего обновления цены.
        
        Args:
            obj: Экземпляр отслеживаемого товара
            
        Returns:
            Optional[datetime]: Дата обновления или None
        """
        latest = obj.price_history.first()
        return latest.collected_at if latest else None

    def get_sparkline_points(self, obj: TrackingItems) -> list[Dict[str, Any]]:
        """Получить сокращенную историю цен для маленького графика в карточке."""
        history_points = [
            point for point in obj.price_history.all()
            if point.price is not None
        ][:12]
        history_points.reverse()
        return [
            {
                "price": point.price,
                "collected_at": point.collected_at.isoformat(),
            }
            for point in history_points
        ]


class TrackingItemDetailSerializer(serializers.ModelSerializer):
    """Расширенный сериализатор для детальной карточки одного товара."""

    product_name = serializers.CharField(source="product.name", read_only=True)
    product_description = serializers.CharField(source="product.description", read_only=True)
    product_brand = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    store_name = serializers.CharField(source="store.name", read_only=True)
    store_base_url = serializers.CharField(source="store.base_url", read_only=True)
    current_price = serializers.SerializerMethodField()
    last_old_price = serializers.SerializerMethodField()
    wb_wallet_price = serializers.SerializerMethodField()
    price_updated_at = serializers.SerializerMethodField()
    latest_in_stock = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    history_count = serializers.SerializerMethodField()
    all_time_min_price = serializers.SerializerMethodField()
    all_time_max_price = serializers.SerializerMethodField()

    class Meta:
        model = TrackingItems
        fields = (
            "id",
            "product",
            "product_name",
            "product_description",
            "product_brand",
            "category_name",
            "store",
            "store_name",
            "store_base_url",
            "source_url",
            "custom_name",
            "is_active",
            "last_checked_at",
            "last_success_at",
            "last_status",
            "created_at",
            "updated_at",
            "current_price",
            "last_old_price",
            "wb_wallet_price",
            "price_updated_at",
            "latest_in_stock",
            "currency",
            "history_count",
            "all_time_min_price",
            "all_time_max_price",
        )

    def _get_latest_history(self, obj: TrackingItems) -> Optional[PriceHistory]:
        return obj.price_history.first()

    def _get_latest_payload(self, obj: TrackingItems) -> Dict[str, Any]:
        latest = self._get_latest_history(obj)
        return latest.raw_payload or {} if latest else {}

    def _get_prices(self, obj: TrackingItems) -> list[Decimal]:
        return [point.price for point in obj.price_history.all() if point.price is not None]

    def get_product_brand(self, obj: TrackingItems) -> str:
        payload = self._get_latest_payload(obj)
        return payload.get("brand") or obj.product.brand or ""

    def get_category_name(self, obj: TrackingItems) -> str:
        payload = self._get_latest_payload(obj)
        return (
            payload.get("category_name")
            or payload.get("subject_name")
            or getattr(obj.product.category, "name", "")
            or ""
        )

    def get_current_price(self, obj: TrackingItems) -> Optional[Decimal]:
        latest = self._get_latest_history(obj)
        return latest.price if latest else None

    def get_last_old_price(self, obj: TrackingItems) -> Optional[Decimal]:
        latest = self._get_latest_history(obj)
        return latest.old_price if latest else None

    def get_wb_wallet_price(self, obj: TrackingItems) -> Optional[Decimal]:
        payload = self._get_latest_payload(obj)
        wallet_price = payload.get("wallet_price")
        if wallet_price in (None, ""):
            return None
        return wallet_price

    def get_price_updated_at(self, obj: TrackingItems) -> Optional[datetime]:
        latest = self._get_latest_history(obj)
        return latest.collected_at if latest else None

    def get_latest_in_stock(self, obj: TrackingItems) -> bool:
        latest = self._get_latest_history(obj)
        return latest.in_stock if latest else False

    def get_currency(self, obj: TrackingItems) -> str:
        latest = self._get_latest_history(obj)
        return latest.currency if latest and latest.currency else "RUB"

    def get_history_count(self, obj: TrackingItems) -> int:
        return len([point for point in obj.price_history.all() if point.price is not None])

    def get_all_time_min_price(self, obj: TrackingItems) -> Optional[Decimal]:
        prices = self._get_prices(obj)
        return min(prices) if prices else None

    def get_all_time_max_price(self, obj: TrackingItems) -> Optional[Decimal]:
        prices = self._get_prices(obj)
        return max(prices) if prices else None


class PriceHistorySerializer(serializers.ModelSerializer):
    """Сериализатор для истории изменения цен.
    
    Attributes:
        product_name: Название товара
    """
    product_name = serializers.CharField(source='tracking_item.product.name', read_only=True)
    
    class Meta:
        model = PriceHistory
        fields = (
            "id", "tracking_item", "product_name", "price", 
            "old_price", "currency", "in_stock", "collected_at"
        )
        read_only_fields = ("id", "collected_at")


class TrackingItemHistorySerializer(serializers.ModelSerializer):
    """Сериализатор детальной истории цены для одного отслеживаемого товара."""

    product_name = serializers.CharField(source='product.name', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    current_price = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    max_price = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    price_updated_at = serializers.SerializerMethodField()
    history_points = serializers.SerializerMethodField()

    class Meta:
        model = TrackingItems
        fields = (
            "id",
            "product_name",
            "store_name",
            "custom_name",
            "source_url",
            "current_price",
            "min_price",
            "max_price",
            "currency",
            "price_updated_at",
            "history_points",
        )

    def _get_history_points(self) -> list[PriceHistory]:
        return self.context.get("history_points", [])

    def get_current_price(self, obj: TrackingItems) -> Optional[Decimal]:
        history_points = self._get_history_points()
        return history_points[-1].price if history_points else None

    def get_min_price(self, obj: TrackingItems) -> Optional[Decimal]:
        prices = [point.price for point in self._get_history_points() if point.price is not None]
        return min(prices) if prices else None

    def get_max_price(self, obj: TrackingItems) -> Optional[Decimal]:
        prices = [point.price for point in self._get_history_points() if point.price is not None]
        return max(prices) if prices else None

    def get_currency(self, obj: TrackingItems) -> str:
        history_points = self._get_history_points()
        latest = history_points[-1] if history_points else None
        return latest.currency if latest and latest.currency else "RUB"

    def get_history_points(self, obj: TrackingItems) -> list[Dict[str, Any]]:
        return [
            {
                "price": point.price,
                "old_price": point.old_price,
                "currency": point.currency,
                "in_stock": point.in_stock,
                "collected_at": point.collected_at.isoformat(),
            }
            for point in self._get_history_points()
            if point.price is not None
        ]

    def get_price_updated_at(self, obj: TrackingItems) -> Optional[datetime]:
        history_points = self._get_history_points()
        latest = history_points[-1] if history_points else None
        return latest.collected_at if latest else None


class UpdateTrackingItemSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления параметров отслеживания.
    
    Позволяет пользователю изменять только is_active и custom_name.
    """
    class Meta:
        model = TrackingItems
        fields = ("is_active", "custom_name")


class AddItemToUserTrack(serializers.Serializer):
    """Сериализатор для добавления товара в отслеживание пользователя.
    
    Создает товар, магазин (если не существуют), трекинг и первую запись истории цен
    в одной атомарной транзакции.
    
    Attributes:
        productName: Название товара
        storeName: Название магазина
        price: Начальная цена товара
        customName: Пользовательское название (опционально)
    """
    productName = serializers.CharField()
    storeName = serializers.CharField()
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    customName = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация входных данных.
        
        Args:
            attrs: Словарь с данными для валидации
            
        Returns:
            Dict[str, Any]: Валидированные данные
            
        Raises:
            serializers.ValidationError: При некорректных данных
        """
        price = attrs.get('price')
        product_name = attrs.get('productName')
        store_name = attrs.get('storeName')

        if price and price < 0:
            raise serializers.ValidationError("Цена не может быть отрицательной")

        if not product_name:
            raise serializers.ValidationError("Название товара не может быть пустым")
        
        if len(store_name) > 255 or len(product_name) > 255:
            raise serializers.ValidationError("Название слишком длинное")

        return attrs
    
    @transaction.atomic
    def create(self, validated_data: Dict[str, Any]) -> TrackingItems:
        """Создание товара в отслеживании с атомарной транзакцией.
        
        Создает/получает товар и магазин, создает запись отслеживания
        и первую запись истории цен.
        
        Args:
            validated_data: Валидированные данные с полем user
            
        Returns:
            TrackingItems: Созданная запись отслеживания
        """
        product_name = validated_data['productName']
        store_name = validated_data['storeName']
        price = validated_data['price']
        custom_name = validated_data.get('customName', '')
        user = validated_data['user']

        # Создаем/получаем товар и магазин
        product, _ = Products.objects.get_or_create(name=product_name)
        store, _ = Stores.objects.get_or_create(
            name=store_name,
            defaults={'base_url': 'https://example.com'}
        )

        tracking_item = TrackingItems.objects.create(
            user=user,
            product=product,
            store=store,
            custom_name=custom_name,
            source_url='test'
        )

        # Создаем первую запись истории цен
        PriceHistory.objects.create(
            tracking_item=tracking_item,
            price=price,
            currency='RUB',
            in_stock=True
        )

        return tracking_item
    
    def to_representation(self, instance: TrackingItems) -> Dict[str, Any]:
        """Преобразование экземпляра в JSON-представление.
        
        Использует TrackingItemSerializer для формирования ответа.
        
        Args:
            instance: Экземпляр отслеживаемого товара
            
        Returns:
            Dict[str, Any]: Сериализованные данные
        """
        return TrackingItemSerializer(instance).data
