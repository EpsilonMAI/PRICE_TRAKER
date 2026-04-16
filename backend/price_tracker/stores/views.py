import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from items.models import Products
from stores.models import Stores
from tracking.models import PriceHistory, TrackingItems


logger = logging.getLogger(__name__)


class WBParserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        query = request.data.get("query")
        if not query:
            return Response({"error": "Query parameter is required"}, status=400)

        from .wb_parser import fetch_best_wb_offer

        best_offer = fetch_best_wb_offer(query)

        if not best_offer:
            return Response({"error": "No original offers found on Wildberries for this query"}, status=404)

        user = request.user

        store, _ = Stores.objects.get_or_create(
            name="Wildberries",
            defaults={"base_url": "https://www.wildberries.ru"},
        )

        product, _ = Products.objects.get_or_create(
            name=best_offer["name"],
            defaults={"brand": best_offer["brand"]},
        )

        track_item, created = TrackingItems.objects.get_or_create(
            user=user,
            product=product,
            store=store,
            defaults={
                "source_url": best_offer["url"],
                "custom_name": f"WB: {query}",
            },
        )

        if created:
            PriceHistory.objects.create(
                tracking_item=track_item,
                price=best_offer["price"],
                old_price=best_offer["old_price"],
                in_stock=True,
            )
            logger.info(
                "Added new TrackingItem(%s) with PriceHistory for user %s",
                track_item.id,
                user.username,
            )
        else:
            logger.info(
                "TrackingItem(%s) already exists for user %s",
                track_item.id,
                user.username,
            )

        return Response(
            {
                "message": "Offer found and added to tracking.",
                "offer": best_offer,
                "tracking_item_id": track_item.id,
                "is_new": created,
            }
        )
