"""Модели для отслеживания товаров и истории изменения цен."""
from typing import Optional
from decimal import Decimal

from django.db import models
from django.conf import settings
from items.models import Products
from stores.models import Stores


class TrackingItems(models.Model):
    """Товары, добавленные пользователем в список отслеживания.
    
    Attributes:
        user: Пользователь, отслеживающий товар
        product: Отслеживаемый товар
        store: Магазин, в котором отслеживается товар
        source_url: Ссылка на страницу товара
        custom_name: Пользовательское название товара
        is_active: Активно ли отслеживание (True = парсится, False = на паузе)
        last_checked_at: Время последней проверки цены
        last_success_at: Время последнего успешного получения цены
        last_status: Статус последней проверки
        created_at: Дата добавления в отслеживание
        updated_at: Дата последнего обновления
    """
    
    # === СВЯЗИ ===
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  
        on_delete=models.CASCADE,  
        related_name='tracking_items'
    )
    
    product = models.ForeignKey(
        Products,
        on_delete=models.CASCADE,
        related_name='tracked_by'
    )
    
    store = models.ForeignKey(
        Stores,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tracking_items'
    )
    
    source_url = models.TextField(null=True, blank=True)
    custom_name = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(max_length=30, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tracking Item"
        verbose_name_plural = "Tracking Items"
        ordering = ['-created_at']

    def __str__(self) -> str:
        """Строковое представление отслеживаемого товара.
        
        Returns:
            str: Пользователь и товар
        """
        return f"{self.user.username} отслеживает {self.product.name}"


class PriceHistory(models.Model):
    """История изменения цен товара.
    
    Каждая запись — снимок цены в конкретный момент времени.
    
    Attributes:
        tracking_item: Связь с отслеживаемым товаром
        price: Текущая цена товара
        old_price: Зачеркнутая (старая) цена
        currency: Валюта цены
        in_stock: Наличие товара в магазине
        collected_at: Время сбора данных о цене
        raw_payload: Дополнительные данные в JSON формате
    """
    
    # === СВЯЗЬ ===
    tracking_item = models.ForeignKey(
        TrackingItems,
        on_delete=models.CASCADE,
        related_name='price_history'
    )

    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    old_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  
    currency = models.CharField(max_length=3, null=True, blank=True, default='RUB')
    in_stock = models.BooleanField(default=True)
    collected_at = models.DateTimeField(auto_now_add=True)
    raw_payload = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Price History"
        verbose_name_plural = "Price Histories"
        ordering = ['-collected_at']

    def __str__(self) -> str:
        """Строковое представление записи истории.
        
        Returns:
            str: Товар, цена и дата
        """
        return f"{self.tracking_item.product.name}: {self.price} на {self.collected_at}"
