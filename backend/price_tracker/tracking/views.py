"""Views для управления отслеживанием товаров и их историей цен."""
from datetime import timedelta

from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import QuerySet
from django.utils import timezone

from .models import TrackingItems, PriceHistory
from .serializers import (
    TrackingItemSerializer, 
    PriceHistorySerializer, 
    AddItemToUserTrack, 
    UpdateTrackingItemSerializer,
    TrackingItemHistorySerializer,
)


class TrackingItemsAPIList(generics.ListAPIView):
    """API для получения списка отслеживаемых товаров текущего пользователя.
    
    Возвращает только товары, добавленные авторизованным пользователем.
    Использует prefetch для оптимизации запросов к БД.
    """
    serializer_class = TrackingItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self) -> QuerySet[TrackingItems]:
        """Получить отфильтрованный QuerySet для текущего пользователя.
        
        Returns:
            QuerySet[TrackingItems]: Товары текущего пользователя с предзагрузкой связей
        """
        return TrackingItems.objects.filter(
            user=self.request.user
        ).select_related(
            'user', 'product', 'store'
        ).prefetch_related('price_history')


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


class UpdateTrackingItemAPIView(generics.UpdateAPIView):
    """API для обновления параметров отслеживания товара.
    
    Позволяет изменять is_active (вкл/выкл отслеживание) и custom_name.
    Пользователь может обновлять только свои товары.
    """
    serializer_class = UpdateTrackingItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self) -> QuerySet[TrackingItems]:
        """Получить товары, доступные для редактирования текущему пользователю.
        
        Returns:
            QuerySet[TrackingItems]: Только товары текущего пользователя
        """
        return TrackingItems.objects.filter(user=self.request.user)


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
            "7": 7,
            "30": 30,
            "90": 90,
        }

        if period not in period_map:
            raise ValidationError({"period": "Допустимые значения: 7, 30, 90, all"})

        cutoff = timezone.now() - timedelta(days=period_map[period])
        return queryset.filter(collected_at__gte=cutoff)
