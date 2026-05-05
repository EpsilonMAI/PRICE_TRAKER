from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient


class SendTestNotificationApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="mail-user",
            email="mail-user@example.com",
            password="password123",
        )
        self.client.force_authenticate(user=self.user)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend")
    def test_test_notification_rejects_non_delivery_backend(self) -> None:
        response = self.client.post("/api/profile/notifications/test/")

        self.assertEqual(response.status_code, 503)
        self.assertIn("Email backend", response.data["detail"])

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
        DEFAULT_FROM_EMAIL="sender@example.com",
    )
    def test_test_notification_returns_smtp_diagnostics_on_success(self) -> None:
        with patch("django.core.mail.send_mail", return_value=1) as send_mail_mock:
            response = self.client.post("/api/profile/notifications/test/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email_backend"], "django.core.mail.backends.smtp.EmailBackend")
        self.assertEqual(response.data["from_email"], "sender@example.com")
        self.assertEqual(send_mail_mock.call_args.kwargs["recipient_list"], ["mail-user@example.com"])

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend")
    def test_test_notification_rejects_zero_sent_count(self) -> None:
        with patch("django.core.mail.send_mail", return_value=0):
            response = self.client.post("/api/profile/notifications/test/")

        self.assertEqual(response.status_code, 502)
