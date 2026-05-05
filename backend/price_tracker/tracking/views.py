"""Views для управления отслеживанием товаров и их историей цен."""
from datetime import timedelta

from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import DateTimeField, DecimalField, F, OuterRef, Q, QuerySet, Subquery
from django.utils import timezone

from .models import TrackingItems, PriceHistory
from .serializers import (
    TrackingItemSerializer, 
    TrackingItemDetailSerializer,
    PriceHistorySerializer, 
    AddItemToUserTrack, 
    UpdateTrackingItemSerializer,
    TrackingItemHistorySerializer,
)
from .services import refresh_tracking_item_price


REFRESH_STATUS_MESSAGES = {
    "success": "Цена успешно обновлена",
    "store_missing": "Для товара не указан магазин",
    "store_inactive": "Магазин сейчас неактивен",
    "parser_disabled": "Парсер для этого магазина отключен",
    "unsupported_store": "Для этого магазина ручное обновление пока не поддерживается",
    "parser_error": "Не удалось получить цену из магазина",
    "not_found": "Товар не найден в магазине",
}


class TrackingItemsAPIList(generics.ListAPIView):
    """API для получения списка отслеживаемых товаров текущего пользователя.
    
    Возвращает только товары, добавленные авторизованным пользователем.
    Использует prefetch для оптимизации запросов к БД.
    """
    serializer_class = TrackingItemSerializer
    permission_classes = [IsAuthenticated]

    ACTIVE_PARAM_VALUES = {
        "true": True,
        "1": True,
        "yes": True,
        "active": True,
        "false": False,
        "0": False,
        "no": False,
        "paused": False,
        "inactive": False,
    }

    ORDERING_MAP = {
        "price_updated_at": F("price_updated_at_sort").asc(nulls_last=True),
        "-price_updated_at": F("price_updated_at_sort").desc(nulls_last=True),
        "current_price": F("current_price_sort").asc(nulls_last=True),
        "-current_price": F("current_price_sort").desc(nulls_last=True),
        "updated_at": F("updated_at").asc(nulls_last=True),
        "-updated_at": F("updated_at").desc(nulls_last=True),
        "created_at": F("created_at").asc(nulls_last=True),
        "-created_at": F("created_at").desc(nulls_last=True),
    }
    
    def get_queryset(self) -> QuerySet[TrackingItems]:
        """Получить отфильтрованный QuerySet для текущего пользователя.
        
        Returns:
            QuerySet[TrackingItems]: Товары текущего пользователя с предзагрузкой связей
        """
        latest_history = PriceHistory.objects.filter(
            tracking_item=OuterRef("pk"),
            price__isnull=False,
        ).order_by("-collected_at")

        queryset = TrackingItems.objects.filter(
            user=self.request.user
        ).annotate(
            current_price_sort=Subquery(
                latest_history.values("price")[:1],
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            price_updated_at_sort=Subquery(
                latest_history.values("collected_at")[:1],
                output_field=DateTimeField(),
            ),
        ).select_related(
            'user', 'product', 'store'
        ).prefetch_related('price_history')

        params = self.request.query_params
        store = params.get("store", "").strip()
        search = params.get("search", "").strip()
        active = params.get("is_active", "").strip().lower()
        ordering = params.get("ordering", "").strip()

        if store:
            queryset = queryset.filter(store__name__iexact=store)

        if search:
            queryset = queryset.filter(
                Q(product__name__icontains=search) |
                Q(custom_name__icontains=search)
            )

        if active:
            if active not in self.ACTIVE_PARAM_VALUES:
                raise ValidationError({
                    "is_active": "Допустимые значения: true, false, active, paused"
                })
            queryset = queryset.filter(is_active=self.ACTIVE_PARAM_VALUES[active])

        if ordering:
            if ordering not in self.ORDERING_MAP:
                raise ValidationError({
                    "ordering": (
                        "Допустимые значения: price_updated_at, -price_updated_at, "
                        "current_price, -current_price, updated_at, -updated_at, "
                        "created_at, -created_at"
                    )
                })
            queryset = queryset.order_by(self.ORDERING_MAP[ordering], "-created_at")

        return queryset


class UserTrackingItemsAPIList(generics.ListAPIView):
    """Альтернативный API для получения отслеживаемых товаров.
    
    Deprecated: Дублирует функционал TrackingItemsAPIList.
    """
    serializer_class = TrackingItemSerializer
    
    def get_queryset(self) -> QuerySet[TrackingItems]:
        """Получить товары текущего пользователя.
        
        Returns:
            QuerySet[TrackingItems]: Отслеживаемые товары
        """
        return TrackingItems.objects.filter(
            user=self.request.user
        ).select_related(
            'user', 'product', 'store'
        ).prefetch_related('price_history') 
    

class AddItemToTrackAPIView(generics.CreateAPIView):
    """API для добавления нового товара в отслеживание.
    
    Создает товар, магазин (при необходимости), запись отслеживания
    и первую точку в истории цен.
    """
    serializer_class = AddItemToUserTrack
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer: AddItemToUserTrack) -> None:
        """Сохранить новый товар с привязкой к текущему пользователю.
        
        Args:
            serializer: Валидированный сериализатор с данными
        """
        serializer.save(user=self.request.user)


class UpdateTrackingItemAPIView(generics.RetrieveUpdateDestroyAPIView):
    """API для обновления параметров отслеживания товара.
    
    Позволяет изменять is_active (вкл/выкл отслеживание) и custom_name.
    Пользователь может получать, обновлять и удалять только свои товары.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self) -> QuerySet[TrackingItems]:
        """Получить товары, доступные для редактирования текущему пользователю.
        
        Returns:
            QuerySet[TrackingItems]: Только товары текущего пользователя
        """
        return TrackingItems.objects.filter(user=self.request.user).select_related(
            "product",
            "product__category",
            "store",
        ).prefetch_related("price_history")

    def get_serializer_class(self):
        if self.request.method == "GET":
            return TrackingItemDetailSerializer
        return UpdateTrackingItemSerializer


class TrackingItemHistoryAPIView(generics.RetrieveAPIView):
    """API для получения подробной истории цен одного товара."""

    serializer_class = TrackingItemHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[TrackingItems]:
        return TrackingItems.objects.filter(user=self.request.user).select_related(
            "product",
            "store",
        )

    def get_serializer_context(self) -> dict:
        context = super().get_serializer_context()
        context["history_points"] = list(self._get_history_queryset())
        return context

    def _get_history_queryset(self) -> QuerySet[PriceHistory]:
        tracking_item = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        queryset = tracking_item.price_history.filter(price__isnull=False).order_by("collected_at")
        period = self.request.query_params.get("period", "30")

        if period == "all":
            return queryset

        period_map = {
            "1": 1,
            "7": 7,
            "30": 30,
            "90": 90,
        }

        if period not in period_map:
            raise ValidationError({"period": "Допустимые значения: 1, 7, 30, 90, all"})

        cutoff = timezone.now() - timedelta(days=period_map[period])
        return queryset.filter(collected_at__gte=cutoff)


class RefreshTrackingItemAPIView(generics.GenericAPIView):
    """API для ручного обновления цены одного товара."""

    serializer_class = TrackingItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[TrackingItems]:
        return TrackingItems.objects.filter(user=self.request.user).select_related(
            "user",
            "product",
            "store",
        ).prefetch_related("price_history")

    def post(self, request, *args, **kwargs):
        tracking_item = get_object_or_404(self.get_queryset(), pk=kwargs["pk"])
        result = refresh_tracking_item_price(tracking_item)
        tracking_item.refresh_from_db()

        response_payload = {
            "status": result.status,
            "history_created": result.history_created,
            "message": REFRESH_STATUS_MESSAGES.get(result.status, "Не удалось обновить цену"),
            "item": self.get_serializer(tracking_item).data,
        }

        if result.status != "success":
            return Response(response_payload, status=status.HTTP_400_BAD_REQUEST)

        return Response(response_payload, status=status.HTTP_200_OK)
