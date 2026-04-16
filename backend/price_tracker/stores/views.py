from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .wb_parser import fetch_best_wb_offer
from items.models import Products
from tracking.models import TrackingItems, PriceHistory
from stores.models import Stores
from loguru import logger

class WBParserView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        query = request.data.get("query")
        if not query:
            return Response({"error": "Query parameter is required"}, status=400)
            
        best_offer = fetch_best_wb_offer(query)
        
        if not best_offer:
            return Response({"error": "No original offers found on Wildberries for this query"}, status=404)
            
        # Успешно нашли выгодый оригинальный товар, добавляем в трекинг
        user = request.user
        
        store, _ = Stores.objects.get_or_create(
            name="Wildberries",
            defaults={"base_url": "https://www.wildberries.ru"}
        )
        
        product, _ = Products.objects.get_or_create(
            name=best_offer["name"],
            defaults={"brand": best_offer["brand"]}
        )
        
        track_item, created = TrackingItems.objects.get_or_create(
            user=user,
            product=product,
            store=store,
            defaults={
                "source_url": best_offer["url"],
                "custom_name": f"WB: {query}"
            }
        )
        
        # Сохраняем первую цену в историю, если товар только что добавлен
        if created:
            PriceHistory.objects.create(
                tracking_item=track_item,
                price=best_offer["price"],
                old_price=best_offer["old_price"],
                in_stock=True
            )
            logger.info(f"Added new TrackingItem({track_item.id}) with PriceHistory for user {user.username}")
        else:
            logger.info(f"TrackingItem({track_item.id}) already exists for user {user.username}")
        
        return Response({
            "message": "Offer found and added to tracking.",
            "offer": best_offer,
            "tracking_item_id": track_item.id,
            "is_new": created
        })
