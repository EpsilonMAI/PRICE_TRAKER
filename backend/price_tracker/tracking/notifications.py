"""Email-уведомления пользователей об изменении цен.

Все функции молча подавляют ошибки отправки, чтобы не прерывать основной
процесс обновления истории цен.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from django.core.mail import send_mail
from django.conf import settings

if TYPE_CHECKING:
    from .models import TrackingItems

logger = logging.getLogger(__name__)


def _get_user_rules(tracking_item: TrackingItems):
    """Вернуть CustomRules пользователя или None."""
    try:
        return tracking_item.user.profile.custom_rules
    except Exception:
        return None


def _user_email(tracking_item: TrackingItems) -> str | None:
    """Вернуть email пользователя, если он задан."""
    email = tracking_item.user.email
    return email if email else None


def _product_label(tracking_item: TrackingItems) -> str:
    """Понятное название товара (custom_name или product.name)."""
    return (tracking_item.custom_name or tracking_item.product.name).strip()


# ---------------------------------------------------------------------------
# Публичные функции
# ---------------------------------------------------------------------------

def notify_price_drop(
    tracking_item: TrackingItems,
    old_price: Decimal | None,
    new_price: Decimal,
) -> None:
    """Отправить письмо при снижении цены.

    Args:
        tracking_item: Отслеживаемый товар.
        old_price: Предыдущая цена (None — если нет истории).
        new_price: Новая (сниженная) цена.
    """
    rules = _get_user_rules(tracking_item)
    if not rules or not rules.notify_price_drop:
        return

    email = _user_email(tracking_item)
    if not email:
        logger.debug(
            "Пропуск уведомления о снижении цены: у пользователя %s нет email",
            tracking_item.user.username,
        )
        return

    name = _product_label(tracking_item)
    url = tracking_item.source_url or ""
    savings = ""
    if old_price:
        diff = old_price - new_price
        pct = round(diff / old_price * 100)
        savings = f" (−{diff:.0f} ₽, −{pct}%)"

    subject = f"🎉 Цена снизилась: {name}"
    body = (
        f"Привет, {tracking_item.user.username}!\n\n"
        f'Цена на товар «{name}» снизилась{savings}:\n'
        f"  Было: {old_price:.0f} ₽\n"
        f"  Стало: {new_price:.0f} ₽\n\n"
        f"Ссылка на товар: {url}\n\n"
        "— PriceTracker"
    )

    _send(email, subject, body)


def notify_back_in_stock(tracking_item: TrackingItems) -> None:
    """Отправить письмо когда товар снова появился в наличии.

    Args:
        tracking_item: Отслеживаемый товар.
    """
    rules = _get_user_rules(tracking_item)
    if not rules or not rules.notify_back_in_stock:
        return

    email = _user_email(tracking_item)
    if not email:
        return

    name = _product_label(tracking_item)
    url = tracking_item.source_url or ""

    subject = f"✅ Товар снова в наличии: {name}"
    body = (
        f"Привет, {tracking_item.user.username}!\n\n"
        f'Товар «{name}» снова появился в наличии.\n\n'
        f"Ссылка: {url}\n\n"
        "— PriceTracker"
    )

    _send(email, subject, body)


def send_weekly_digest() -> None:
    """Отправить еженедельную сводку всем подписанным пользователям.

    Перебирает всех пользователей с notify_weekly_summary=True,
    собирает актуальные цены из последней записи PriceHistory
    и отправляет сводное письмо.
    """
    from users.models import UserProfile
    from .models import TrackingItems, PriceHistory

    profiles = UserProfile.objects.filter(
        custom_rules__notify_weekly_summary=True,
    ).select_related("user", "custom_rules")

    for profile in profiles:
        user = profile.user
        email = user.email
        if not email:
            continue

        items = TrackingItems.objects.filter(
            user=user, is_active=True
        ).select_related("product")

        if not items.exists():
            continue

        lines = []
        for item in items:
            latest: PriceHistory | None = (
                item.price_history.order_by("-collected_at").first()
            )
            name = _product_label(item)
            if latest:
                lines.append(f"  • {name}: {latest.price:.0f} ₽")
            else:
                lines.append(f"  • {name}: нет данных")

        subject = "📊 Еженедельная сводка PriceTracker"
        body = (
            f"Привет, {user.username}!\n\n"
            "Актуальные цены на ваши отслеживаемые товары:\n\n"
            + "\n".join(lines)
            + "\n\n— PriceTracker"
        )

        _send(email, subject, body)


def _send(to: str, subject: str, body: str) -> None:
    """Обёртка над send_mail с перехватом ошибок."""
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to],
            fail_silently=False,
        )
        logger.info("Письмо отправлено: %s → %s", subject, to)
    except Exception as exc:
        logger.error("Ошибка отправки письма на %s: %s", to, exc)
