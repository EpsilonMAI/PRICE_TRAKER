from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from items.models import Categories, Products
from stores.models import Stores

from .models import PriceHistory, TrackingItems


class UpdatePriceHistoryCommandTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="tester",
            password="password123",
        )
        self.category = Categories.objects.create(name="Смартфоны")
        self.product = Products.objects.create(
            name="iPhone 16",
            category=self.category,
            brand="Apple",
        )
        self.wb_store = Stores.objects.create(
            name="Wildberries",
            base_url="https://www.wildberries.ru",
        )

    def test_successful_check_creates_new_history_entry_each_time(self) -> None:
        tracking_item = TrackingItems.objects.create(
            user=self.user,
            product=self.product,
            store=self.wb_store,
            custom_name="WB: iphone 16",
            source_url="https://old.example/item",
            is_active=True,
        )
        PriceHistory.objects.create(
            tracking_item=tracking_item,
            price="65000.00",
            old_price="70000.00",
            currency="RUB",
            in_stock=True,
        )

        offer = {
            "name": "iPhone 16",
            "brand": "Apple",
            "price": 65000,
            "old_price": 70000,
            "url": "https://www.wildberries.ru/catalog/123/detail.aspx",
        }

        with patch("tracking.services._fetch_wildberries_offer", return_value=offer) as parser_mock:
            call_command("update_price_history")

        tracking_item.refresh_from_db()
        latest_history = tracking_item.price_history.first()

        self.assertEqual(parser_mock.call_args.args[0], "iphone 16")
        self.assertEqual(tracking_item.price_history.count(), 2)
        self.assertEqual(tracking_item.last_status, "success")
        self.assertIsNotNone(tracking_item.last_checked_at)
        self.assertIsNotNone(tracking_item.last_success_at)
        self.assertEqual(tracking_item.source_url, offer["url"])
        self.assertEqual(str(latest_history.price), "65000.00")
        self.assertEqual(str(latest_history.old_price), "70000.00")
        self.assertEqual(latest_history.raw_payload, offer)

    def test_unsupported_store_updates_status_without_history(self) -> None:
        ozon_store = Stores.objects.create(
            name="Ozon",
            base_url="https://www.ozon.ru",
        )
        tracking_item = TrackingItems.objects.create(
            user=self.user,
            product=self.product,
            store=ozon_store,
            is_active=True,
        )

        call_command("update_price_history")

        tracking_item.refresh_from_db()

        self.assertEqual(tracking_item.price_history.count(), 0)
        self.assertEqual(tracking_item.last_status, "unsupported_store")
        self.assertIsNotNone(tracking_item.last_checked_at)
        self.assertIsNone(tracking_item.last_success_at)

    def test_parser_error_marks_tracking_item_without_success_timestamp(self) -> None:
        tracking_item = TrackingItems.objects.create(
            user=self.user,
            product=self.product,
            store=self.wb_store,
            is_active=True,
        )

        with patch(
            "tracking.services._fetch_wildberries_offer",
            side_effect=RuntimeError("wildberries is unavailable"),
        ):
            call_command("update_price_history")

        tracking_item.refresh_from_db()

        self.assertEqual(tracking_item.price_history.count(), 0)
        self.assertEqual(tracking_item.last_status, "parser_error")
        self.assertIsNotNone(tracking_item.last_checked_at)
        self.assertIsNone(tracking_item.last_success_at)


class TrackingItemHistoryApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="history-user",
            password="password123",
        )
        self.other_user = User.objects.create_user(
            username="history-user-2",
            password="password123",
        )
        self.category = Categories.objects.create(name="Ноутбуки")
        self.product = Products.objects.create(
            name="MacBook Air",
            category=self.category,
            brand="Apple",
        )
        self.store = Stores.objects.create(
            name="Wildberries",
            base_url="https://www.wildberries.ru",
        )
        self.tracking_item = TrackingItems.objects.create(
            user=self.user,
            product=self.product,
            store=self.store,
            custom_name="WB: macbook air",
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)

        PriceHistory.objects.create(
            tracking_item=self.tracking_item,
            price="99990.00",
            old_price="109990.00",
        )
        PriceHistory.objects.create(
            tracking_item=self.tracking_item,
            price="97990.00",
            old_price="99990.00",
        )

    def test_history_endpoint_returns_summary_and_points(self) -> None:
        response = self.client.get(f"/api/tracking/{self.tracking_item.id}/history/?period=30")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["product_name"], "MacBook Air")
        self.assertEqual(response.data["store_name"], "Wildberries")
        self.assertEqual(response.data["current_price"], "97990.00")
        self.assertEqual(response.data["min_price"], "97990.00")
        self.assertEqual(response.data["max_price"], "99990.00")
        self.assertEqual(len(response.data["history_points"]), 2)

    def test_history_endpoint_is_available_only_for_owner(self) -> None:
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(f"/api/tracking/{self.tracking_item.id}/history/")

        self.assertEqual(response.status_code, 404)
