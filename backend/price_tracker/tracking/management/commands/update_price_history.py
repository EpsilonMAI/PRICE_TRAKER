"""Management command for refreshing tracked item prices."""
from collections import Counter

from django.core.management.base import BaseCommand

from tracking.models import TrackingItems
from tracking.services import refresh_tracking_item_price


class Command(BaseCommand):
    help = "Refresh prices for active tracking items and append PriceHistory records."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--tracking-item-id",
            action="append",
            dest="tracking_item_ids",
            type=int,
            help="Refresh only the selected tracking item id. May be repeated.",
        )

    def handle(self, *args, **options) -> None:
        tracking_item_ids = options.get("tracking_item_ids") or []

        queryset = TrackingItems.objects.filter(is_active=True).select_related(
            "product",
            "store",
            "user",
        )

        if tracking_item_ids:
            queryset = queryset.filter(id__in=tracking_item_ids)

        total = queryset.count()
        counters = Counter()

        self.stdout.write(f"Checking {total} active tracking items...")

        for tracking_item in queryset.iterator():
            result = refresh_tracking_item_price(tracking_item)
            counters[result.status] += 1

        summary = ", ".join(
            f"{status}={count}"
            for status, count in sorted(counters.items())
        ) or "no items"
        self.stdout.write(self.style.SUCCESS(f"Done: {summary}"))
