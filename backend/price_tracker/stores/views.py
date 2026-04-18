"""Views для парсинга товаров с маркетплейсов."""
import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from items.models import Categories
from items.models import Products
from stores.models import Stores
from tracking.models import PriceHistory, TrackingItems


logger = logging.getLogger(__name__)


def _resolve_category(category_name: str | None):
    normalized = (category_name or "").strip()
    if not normalized:
        return None
    category, _ = Categories.objects.get_or_create(name=normalized)
    return category


class WBParserByURLView(APIView):
    """Добавить товар в отслеживание по прямой ссылке на WB.

    Использует официальное API WB — быстро, без браузера (~1 сек).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Получить данные товара по URL и добавить в отслеживание.

        Body: { "url": "https://www.wildberries.ru/catalog/12345678/detail.aspx" }
        """
        url = request.data.get("url", "").strip()
        if not url:
            return Response({"error": "Укажите ссылку на товар"}, status=400)

        if "wildberries.ru" not in url:
            return Response({"error": "Поддерживаются только ссылки с wildberries.ru"}, status=400)

        from .wb_parser import fetch_wb_product_by_url

        product_data = fetch_wb_product_by_url(url)

        if not product_data:
            return Response({"error": "Не удалось получить данные о товаре. Проверьте ссылку."}, status=404)

        user = request.user

        store, _ = Stores.objects.get_or_create(
            name="Wildberries",
            defaults={"base_url": "https://www.wildberries.ru"},
        )

        product, _ = Products.objects.get_or_create(
            name=product_data["name"],
            defaults={
                "brand": product_data.get("brand", ""),
                "category": _resolve_category(product_data.get("category_name")),
            },
        )

        updated_fields = []
        if product_data.get("brand") and product.brand != product_data["brand"]:
            product.brand = product_data["brand"]
            updated_fields.append("brand")
        parsed_category = _resolve_category(product_data.get("category_name"))
        if parsed_category and product.category_id != parsed_category.id:
            product.category = parsed_category
            updated_fields.append("category")
        if updated_fields:
            product.save(update_fields=updated_fields)

        track_item, created = TrackingItems.objects.get_or_create(
            user=user,
            product=product,
            store=store,
            defaults={
                "source_url": url,
                "custom_name": "",
            },
        )

        PriceHistory.objects.create(
            tracking_item=track_item,
            price=product_data["price"],
            old_price=product_data.get("old_price"),
            in_stock=product_data.get("in_stock", True),
            raw_payload=product_data,
        )

        logger.info(
            "%s TrackingItem(%s) с ценой %s для пользователя %s",
            "Создан" if created else "Обновлена цена для",
            track_item.id,
            product_data["price"],
            user.username,
        )

        return Response({
            "message": "Товар добавлен в отслеживание." if created else "Цена обновлена.",
            "offer": product_data,
            "tracking_item_id": track_item.id,
            "is_new": created,
        })


class WBParserView(APIView):
    """Найти лучшее предложение на WB по поисковому запросу (через браузер)."""
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
            defaults={
                "brand": best_offer.get("brand", ""),
                "category": _resolve_category(best_offer.get("category_name")),
            },
        )

        updated_fields = []
        if best_offer.get("brand") and product.brand != best_offer["brand"]:
            product.brand = best_offer["brand"]
            updated_fields.append("brand")
        parsed_category = _resolve_category(best_offer.get("category_name"))
        if parsed_category and product.category_id != parsed_category.id:
            product.category = parsed_category
            updated_fields.append("category")
        if updated_fields:
            product.save(update_fields=updated_fields)

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
                raw_payload=best_offer,
            )

        return Response({
            "message": "Offer found and added to tracking.",
            "offer": best_offer,
            "tracking_item_id": track_item.id,
            "is_new": created,
        })
