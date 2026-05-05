from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from items.models import Categories, Products
from stores.models import Stores
from users.models import CustomRules

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

    def test_successful_check_uses_saved_wb_url_when_available(self) -> None:
        tracking_item = TrackingItems.objects.create(
            user=self.user,
            product=self.product,
            store=self.wb_store,
            source_url="https://www.wildberries.ru/catalog/555/detail.aspx",
            is_active=True,
        )

        offer = {
            "id": "555",
            "name": "iPhone 16",
            "brand": "Apple",
            "price": 64990,
            "old_price": 69990,
            "url": "https://www.wildberries.ru/catalog/555/detail.aspx",
            "in_stock": True,
        }

        with patch("tracking.services._fetch_wildberries_offer_by_url", return_value=offer) as parser_mock, \
             patch("tracking.services._fetch_wildberries_offer") as search_mock:
            call_command("update_price_history")

        tracking_item.refresh_from_db()

        parser_mock.assert_called_once_with("https://www.wildberries.ru/catalog/555/detail.aspx")
        search_mock.assert_not_called()
        self.assertEqual(tracking_item.last_status, "success")
        self.assertEqual(tracking_item.price_history.count(), 1)

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

    def test_price_drop_notification_uses_previous_history_point(self) -> None:
        self.user.email = "tester@example.com"
        self.user.save(update_fields=["email"])
        tracking_item = TrackingItems.objects.create(
            user=self.user,
            product=self.product,
            store=self.wb_store,
            source_url="https://www.wildberries.ru/catalog/555/detail.aspx",
            is_active=True,
        )
        PriceHistory.objects.create(
            tracking_item=tracking_item,
            price="70000.00",
            old_price="75000.00",
            currency="RUB",
            in_stock=True,
        )

        offer = {
            "id": "555",
            "name": "iPhone 16",
            "brand": "Apple",
            "price": 65000,
            "old_price": 70000,
            "url": "https://www.wildberries.ru/catalog/555/detail.aspx",
            "in_stock": True,
        }

        with patch("tracking.services._fetch_wildberries_offer_by_url", return_value=offer), \
             patch("tracking.notifications.send_mail") as send_mail_mock:
            call_command("update_price_history")

        send_mail_mock.assert_called_once()
        self.assertIn("Цена снизилась", send_mail_mock.call_args.kwargs["subject"])
        self.assertEqual(send_mail_mock.call_args.kwargs["recipient_list"], ["tester@example.com"])

    def test_price_drop_notification_creates_default_rules_when_missing(self) -> None:
        self.user.email = "tester@example.com"
        self.user.save(update_fields=["email"])
        self.user.profile.custom_rules = None
        self.user.profile.save(update_fields=["custom_rules"])
        tracking_item = TrackingItems.objects.create(
            user=self.user,
            product=self.product,
            store=self.wb_store,
            source_url="https://www.wildberries.ru/catalog/555/detail.aspx",
            is_active=True,
        )
        PriceHistory.objects.create(
            tracking_item=tracking_item,
            price="70000.00",
            in_stock=True,
        )

        offer = {
            "id": "555",
            "name": "iPhone 16",
            "brand": "Apple",
            "price": 65000,
            "old_price": 70000,
            "url": "https://www.wildberries.ru/catalog/555/detail.aspx",
        }

        with patch("tracking.services._fetch_wildberries_offer_by_url", return_value=offer), \
             patch("tracking.notifications.send_mail") as send_mail_mock:
            call_command("update_price_history")

        self.user.profile.refresh_from_db()

        send_mail_mock.assert_called_once()
        self.assertIsInstance(self.user.profile.custom_rules, CustomRules)


class TrackingItemsListApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="list-user",
            password="password123",
        )
        self.other_user = User.objects.create_user(
            username="list-user-2",
            password="password123",
        )
        self.category = Categories.objects.create(name="Электроника")
        self.wb_store = Stores.objects.create(
            name="Wildberries",
            base_url="https://www.wildberries.ru",
        )
        self.ozon_store = Stores.objects.create(
            name="Ozon",
            base_url="https://www.ozon.ru",
        )
        self.client.force_authenticate(user=self.user)

        self.phone = self._create_tracking_item(
            name="iPhone 16",
            store=self.wb_store,
            price="95000.00",
            collected_at=timezone.now() - timezone.timedelta(hours=1),
            is_active=True,
            custom_name="Основной телефон",
        )
        self.laptop = self._create_tracking_item(
            name="MacBook Air",
            store=self.ozon_store,
            price="120000.00",
            collected_at=timezone.now() - timezone.timedelta(days=2),
            is_active=False,
            custom_name="Рабочий ноутбук",
        )
        self.headphones = self._create_tracking_item(
            name="AirPods Pro",
            store=self.wb_store,
            price="22000.00",
            collected_at=timezone.now() - timezone.timedelta(days=1),
            is_active=True,
        )

        other_product = Products.objects.create(
            name="Чужой товар",
            category=self.category,
        )
        other_item = TrackingItems.objects.create(
            user=self.other_user,
            product=other_product,
            store=self.wb_store,
        )
        PriceHistory.objects.create(tracking_item=other_item, price="1.00")

    def _create_tracking_item(
        self,
        *,
        name: str,
        store: Stores,
        price: str,
        collected_at,
        is_active: bool,
        custom_name: str = "",
    ) -> TrackingItems:
        product = Products.objects.create(
            name=name,
            category=self.category,
        )
        tracking_item = TrackingItems.objects.create(
            user=self.user,
            product=product,
            store=store,
            is_active=is_active,
            custom_name=custom_name,
        )
        history = PriceHistory.objects.create(
            tracking_item=tracking_item,
            price=price,
        )
        PriceHistory.objects.filter(pk=history.pk).update(collected_at=collected_at)
        return tracking_item

    def _response_ids(self, response) -> list[int]:
        return [item["id"] for item in response.data]

    def test_list_filters_by_store_and_active_status(self) -> None:
        response = self.client.get(
            "/api/detailedprod/",
            {"store": "Wildberries", "is_active": "true"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(self._response_ids(response)),
            {self.phone.id, self.headphones.id},
        )

    def test_list_searches_product_and_custom_name(self) -> None:
        product_response = self.client.get("/api/detailedprod/", {"search": "iphone"})
        custom_name_response = self.client.get("/api/detailedprod/", {"search": "рабочий"})

        self.assertEqual(product_response.status_code, 200)
        self.assertEqual(self._response_ids(product_response), [self.phone.id])
        self.assertEqual(custom_name_response.status_code, 200)
        self.assertEqual(self._response_ids(custom_name_response), [self.laptop.id])

    def test_list_sorts_by_latest_price_update_and_current_price(self) -> None:
        updated_response = self.client.get(
            "/api/detailedprod/",
            {"ordering": "-price_updated_at"},
        )
        price_response = self.client.get(
            "/api/detailedprod/",
            {"ordering": "current_price"},
        )

        self.assertEqual(updated_response.status_code, 200)
        self.assertEqual(
            self._response_ids(updated_response),
            [self.phone.id, self.headphones.id, self.laptop.id],
        )
        self.assertEqual(price_response.status_code, 200)
        self.assertEqual(
            self._response_ids(price_response),
            [self.headphones.id, self.phone.id, self.laptop.id],
        )

    def test_list_rejects_invalid_query_params(self) -> None:
        active_response = self.client.get("/api/detailedprod/", {"is_active": "maybe"})
        ordering_response = self.client.get("/api/detailedprod/", {"ordering": "name"})

        self.assertEqual(active_response.status_code, 400)
        self.assertEqual(ordering_response.status_code, 400)


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
            raw_payload={
                "brand": "Apple",
                "category_name": "Ультрабуки",
                "wallet_price": 95990,
            },
        )

    def test_history_endpoint_returns_summary_and_points(self) -> None:
        response = self.client.get(f"/api/tracking/{self.tracking_item.id}/history/?period=30")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["product_name"], "MacBook Air")
        self.assertEqual(response.data["store_name"], "Wildberries")
        self.assertEqual(str(response.data["current_price"]), "97990.00")
        self.assertEqual(str(response.data["min_price"]), "97990.00")
        self.assertEqual(str(response.data["max_price"]), "99990.00")
        self.assertEqual(len(response.data["history_points"]), 2)

    def test_history_endpoint_supports_one_day_period(self) -> None:
        response = self.client.get(f"/api/tracking/{self.tracking_item.id}/history/?period=1")

        self.assertEqual(response.status_code, 200)

    def test_history_endpoint_is_available_only_for_owner(self) -> None:
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(f"/api/tracking/{self.tracking_item.id}/history/")

        self.assertEqual(response.status_code, 404)

    def test_tracking_item_detail_endpoint_returns_card_data(self) -> None:
        response = self.client.get(f"/api/tracking/{self.tracking_item.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["product_name"], "MacBook Air")
        self.assertEqual(response.data["store_name"], "Wildberries")
        self.assertEqual(str(response.data["current_price"]), "97990.00")
        self.assertEqual(str(response.data["all_time_min_price"]), "97990.00")
        self.assertEqual(str(response.data["all_time_max_price"]), "99990.00")
        self.assertEqual(response.data["category_name"], "Ультрабуки")
        self.assertEqual(str(response.data["wb_wallet_price"]), "95990")
        self.assertEqual(response.data["history_count"], 2)
        self.assertTrue(response.data["latest_in_stock"])

    def test_tracking_item_detail_endpoint_is_available_only_for_owner(self) -> None:
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(f"/api/tracking/{self.tracking_item.id}/")

        self.assertEqual(response.status_code, 404)

    def test_tracking_item_delete_endpoint_removes_owned_item_and_history(self) -> None:
        response = self.client.delete(f"/api/tracking/{self.tracking_item.id}/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(TrackingItems.objects.filter(id=self.tracking_item.id).exists())
        self.assertEqual(PriceHistory.objects.filter(tracking_item_id=self.tracking_item.id).count(), 0)

    def test_tracking_item_delete_endpoint_is_available_only_for_owner(self) -> None:
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(f"/api/tracking/{self.tracking_item.id}/")

        self.assertEqual(response.status_code, 404)
        self.assertTrue(TrackingItems.objects.filter(id=self.tracking_item.id).exists())
        self.assertEqual(PriceHistory.objects.filter(tracking_item_id=self.tracking_item.id).count(), 2)

    def test_tracking_item_delete_endpoint_requires_authentication(self) -> None:
        self.client.force_authenticate(user=None)
        response = self.client.delete(f"/api/tracking/{self.tracking_item.id}/")

        self.assertEqual(response.status_code, 401)
        self.assertTrue(TrackingItems.objects.filter(id=self.tracking_item.id).exists())
        self.assertEqual(PriceHistory.objects.filter(tracking_item_id=self.tracking_item.id).count(), 2)

    def test_manual_refresh_endpoint_updates_item_and_returns_serialized_item(self) -> None:
        offer = {
            "name": "MacBook Air",
            "brand": "Apple",
            "price": 95990,
            "old_price": 97990,
            "url": "https://www.wildberries.ru/catalog/987/detail.aspx",
        }

        with patch("tracking.services._fetch_wildberries_offer", return_value=offer):
            response = self.client.post(f"/api/tracking/{self.tracking_item.id}/refresh/")

        self.tracking_item.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(str(response.data["item"]["current_price"]), "95990.00")
        self.assertEqual(response.data["item"]["source_url"], offer["url"])
        self.assertEqual(self.tracking_item.price_history.count(), 3)

    def test_manual_refresh_endpoint_returns_400_for_parser_failure(self) -> None:
        with patch(
            "tracking.services._fetch_wildberries_offer",
            side_effect=RuntimeError("wildberries is unavailable"),
        ):
            response = self.client.post(f"/api/tracking/{self.tracking_item.id}/refresh/")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["status"], "parser_error")
