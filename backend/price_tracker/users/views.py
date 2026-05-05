"""Views для регистрации пользователей и управления профилями."""
from typing import Any

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

from .models import CustomRules
from .serializers import RegisterSerializer, ProfileSerializer, NotificationSettingsSerializer


class UserRegistration(APIView):
    """API для регистрации новых пользователей.
    
    Создает пользователя и возвращает JWT токены для авторизации.
    """
    
    def post(self, request: Request) -> Response:
        """Зарегистрировать нового пользователя.
        
        Args:
            request: HTTP запрос с данными пользователя (username, email, password)
            
        Returns:
            Response: Данные пользователя и JWT токены или ошибки валидации
        """
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            refresh = RefreshToken.for_user(user)

            return Response({
                "user": {
                    "username": user.username,
                    "email": user.email
                },
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                }
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class GetProfile(generics.RetrieveAPIView):
    """API для получения профиля текущего пользователя.
    
    Возвращает расширенную информацию о пользователе, включая
    данные из связанного UserProfile и статистику отслеживания.
    """
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self) -> User:
        """Получить объект текущего пользователя."""
        return self.request.user


class UpdateNotificationSettings(APIView):
    """PATCH /api/profile/notifications/ — обновить настройки уведомлений."""

    permission_classes = [IsAuthenticated]

    def patch(self, request: Request) -> Response:
        serializer = NotificationSettingsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user = request.user

        # Получить или создать профиль и правила
        profile, _ = user.profile.__class__.objects.get_or_create(user=user)
        if profile.custom_rules is None:
            rules = CustomRules.objects.create(**data)
            profile.custom_rules = rules
            profile.save(update_fields=["custom_rules"])
        else:
            rules = profile.custom_rules
            for field, value in data.items():
                setattr(rules, field, value)
            rules.save()

        return Response({
            "notify_price_drop": rules.notify_price_drop,
            "notify_back_in_stock": rules.notify_back_in_stock,
            "notify_weekly_summary": rules.notify_weekly_summary,
        })


class SendTestNotificationView(APIView):
    """POST /api/profile/notifications/test/ — отправить тестовое письмо на email пользователя."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        user = request.user
        email = user.email
        if not email:
            return Response(
                {"detail": "У вашего аккаунта не указан email. Добавьте его в профиле."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.core.mail import send_mail
        from django.conf import settings as django_settings

        try:
            send_mail(
                subject="✅ Тестовое уведомление PriceTracker",
                message=(
                    f"Привет, {user.username}!\n\n"
                    "Это тестовое письмо от PriceTracker.\n"
                    "Если вы его получили — email-уведомления работают корректно.\n\n"
                    "— PriceTracker"
                ),
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as exc:
            return Response(
                {"detail": f"Ошибка отправки: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"detail": f"Письмо отправлено на {email}"})


class UpdateEmailView(APIView):
    """PATCH /api/profile/email/ — обновить email пользователя."""

    permission_classes = [IsAuthenticated]

    def patch(self, request: Request) -> Response:
        email = (request.data.get("email") or "").strip()
        if not email or "@" not in email:
            return Response(
                {"detail": "Укажите корректный email."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.email = email
        request.user.save(update_fields=["email"])
        return Response({"email": email})
