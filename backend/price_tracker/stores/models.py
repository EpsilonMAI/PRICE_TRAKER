"""Модели для управления интернет-магазинами."""
from typing import Optional
from decimal import Decimal

from django.db import models


class Stores(models.Model):
    """Модель интернет-магазинов для парсинга цен.
    
    Attributes:
        name: Название магазина
        base_url: Базовый URL сайта магазина
        logo: Логотип магазина
        rating: Рейтинг магазина (от 0.0 до 5.0)
        is_active: Активен ли магазин для отслеживания
        parser_enabled: Включен ли парсер для этого магазина
        created_at: Дата добавления магазина
        updated_at: Дата последнего обновления
    """
    name = models.CharField(max_length=150, unique=True)
    base_url = models.URLField(max_length=500)
    logo = models.ImageField(upload_to='stores/logos/', blank=True, null=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    parser_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Store"
        verbose_name_plural = "Stores"
        ordering = ['name']

    def __str__(self) -> str:
        """Строковое представление магазина.
        
        Returns:
            str: Название магазина
        """
        return self.name

