"""Views для управления отслеживанием товаров и их историей цен."""
from typing import Any

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from django.db.models import QuerySet

from .models import TrackingItems, PriceHistory
from .serializers import (
    TrackingItemSerializer, 
    PriceHistorySerializer, 
    AddItemToUserTrack, 
    UpdateTrackingItemSerializer
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
