"""Модели для управления профилями пользователей и пользовательскими правилами."""
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings


class CustomRules(models.Model):
    """Настройки email-уведомлений пользователя.

    Attributes:
        notify_price_drop: Отправлять письмо при снижении цены
        notify_back_in_stock: Отправлять письмо при появлении товара в наличии
        notify_weekly_summary: Еженедельная сводка по всем отслеживаемым товарам
    """

    notify_price_drop = models.BooleanField(
        default=True,
        verbose_name="Уведомлять о снижении цены",
    )
    notify_back_in_stock = models.BooleanField(
        default=True,
        verbose_name="Уведомлять о появлении в наличии",
    )
    notify_weekly_summary = models.BooleanField(
        default=False,
        verbose_name="Еженедельная сводка",
    )

    class Meta:
        verbose_name = "Custom Rule"
        verbose_name_plural = "Custom Rules"

    def __str__(self) -> str:
        parts = []
        if self.notify_price_drop:
            parts.append("снижение цены")
        if self.notify_back_in_stock:
            parts.append("в наличии")
        if self.notify_weekly_summary:
            parts.append("сводка")
        return ", ".join(parts) if parts else "нет уведомлений"


class UserProfile(models.Model):
    """Расширенный профиль пользователя с дополнительной информацией.
    
    Связан с встроенной моделью User через OneToOne.
    
    Attributes:
        user: Связь с пользователем Django
        custom_rules: Пользовательские правила отслеживания
        phone: Номер телефона пользователя
        avatar: Аватар пользователя
        created_at: Дата создания профиля
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    custom_rules = models.ForeignKey(
        CustomRules,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    phone = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self) -> str:
        """Строковое представление профиля.
        
        Returns:
            str: Профиль с именем пользователя
        """
        return f"Профиль {self.user.username}"

