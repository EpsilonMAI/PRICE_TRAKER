from rest_framework import generics
from .models import TrackingItems, PriceHistory
from .serializers import TrackingItemSerializer, PriceHistorySerializer


class TrackingItemsAPIList(generics.ListAPIView):
    """Список всех отслеживаемых товаров"""
    queryset = TrackingItems.objects.all().select_related(
        'user', 'product', 'store'
    ).prefetch_related('price_history')
    serializer_class = TrackingItemSerializer


class UserTrackingItemsAPIList(generics.ListAPIView):
    """Список отслеживаемых товаров конкретного пользователя"""
    serializer_class = TrackingItemSerializer
    
    def get_queryset(self):
        return TrackingItems.objects.filter(
            user=self.request.user
        ).select_related(
            'user', 'product', 'store'
        ).prefetch_related('price_history') 


