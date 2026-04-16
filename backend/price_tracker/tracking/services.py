"""Сервисные функции для обновления истории цен."""
from dataclasses import dataclass
import logging
from typing import Optional

from django.utils import timezone

from .models import PriceHistory, TrackingItems


WB_STORE_NAMES = {"wildberries"}
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RefreshTrackingItemResult:
    """Результат обновления одного отслеживаемого товара."""

    status: str
    history_created: bool = False


def _save_status(
    tracking_item: TrackingItems,
    *,
    checked_at,
    status: str,
    success_at=None,
    source_url: Optional[str] = None,
) -> RefreshTrackingItemResult:
    """Обновить служебные поля статуса у TrackingItems."""

    tracking_item.last_checked_at = checked_at
    tracking_item.last_status = status

    update_fields = ["last_checked_at", "last_status"]

    if success_at is not None:
        tracking_item.last_success_at = success_at
        update_fields.append("last_success_at")

    if source_url and source_url != tracking_item.source_url:
        tracking_item.source_url = source_url
        update_fields.append("source_url")

    tracking_item.save(update_fields=update_fields)
    return RefreshTrackingItemResult(
        status=status,
        history_created=status == "success",
    )


def _get_wildberries_query(tracking_item: TrackingItems) -> str:
    """Получить поисковый запрос для Wildberries."""

    custom_name = (tracking_item.custom_name or "").strip()

    if custom_name.lower().startswith("wb:"):
        query = custom_name.split(":", 1)[1].strip()
        if query:
            return query

    return tracking_item.product.name


def _fetch_wildberries_offer(query: str):
    """Лениво импортировать парсер Wildberries для runtime-вызовов."""

    from stores.wb_parser import fetch_best_wb_offer

    return fetch_best_wb_offer(query)


def refresh_tracking_item_price(tracking_item: TrackingItems) -> RefreshTrackingItemResult:
    """Проверить актуальную цену товара и добавить новую точку в историю."""

    checked_at = timezone.now()
    store = tracking_item.store

    if store is None:
        return _save_status(
            tracking_item,
            checked_at=checked_at,
            status="store_missing",
        )

    if not store.is_active:
        return _save_status(
            tracking_item,
            checked_at=checked_at,
            status="store_inactive",
        )

    if not store.parser_enabled:
        return _save_status(
            tracking_item,
            checked_at=checked_at,
            status="parser_disabled",
        )

    store_name = (store.name or "").strip().lower()
    if store_name not in WB_STORE_NAMES:
        return _save_status(
            tracking_item,
            checked_at=checked_at,
            status="unsupported_store",
        )

    query = _get_wildberries_query(tracking_item)

    try:
        offer = _fetch_wildberries_offer(query)
    except Exception:
        logger.exception(
            "Failed to update price history for TrackingItem(%s)",
            tracking_item.id,
        )
        return _save_status(
            tracking_item,
            checked_at=checked_at,
            status="parser_error",
        )

    if not offer:
        return _save_status(
            tracking_item,
            checked_at=checked_at,
            status="not_found",
        )

    PriceHistory.objects.create(
        tracking_item=tracking_item,
        price=offer.get("price"),
        old_price=offer.get("old_price", offer.get("price")),
        currency="RUB",
        in_stock=True,
        raw_payload=offer,
    )

    return _save_status(
        tracking_item,
        checked_at=checked_at,
        success_at=checked_at,
        status="success",
        source_url=offer.get("url"),
    )
