"""Модели для управления профилями пользователей и пользовательскими правилами."""
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings


class CustomRules(models.Model):
    """Модель пользовательских правил отслеживания цен.
    
    Attributes:
        custom_rule: Текстовое описание правила отслеживания
    """
    custom_rule = models.CharField(max_length=255)
    
    class Meta:
        verbose_name = "Custom Rule"
        verbose_name_plural = "Custom Rules"
    
    def __str__(self) -> str:
        """Строковое представление правила.
        
        Returns:
            str: Текст правила
        """
        return self.custom_rule


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

