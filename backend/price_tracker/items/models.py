"""Модели для управления категориями и товарами."""
from typing import List, Optional

from django.db import models


class Categories(models.Model):
    """Иерархическая структура категорий товаров.
    
    Поддерживает вложенные категории через self-референс.
    
    Attributes:
        name: Название категории
        parent: Родительская категория (для создания иерархии)
    """
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self) -> str:
        """Строковое представление категории.
        
        Returns:
            str: Название категории
        """
        return self.name

    def get_ancestors(self) -> List['Categories']:
        """Получить все родительские категории в иерархии.
        
        Возвращает список от самой верхней категории к текущей.
        Пример: [Электроника, Планшеты] для категории iPad.
        
        Returns:
            List[Categories]: Список родительских категорий
        """
        ancestors: List['Categories'] = []
        category: Optional['Categories'] = self.parent
        while category:
            ancestors.insert(0, category)
            category = category.parent
        return ancestors

    def get_descendants(self) -> List['Categories']:
        """Получить все дочерние категории рекурсивно.
        
        Returns:
            List[Categories]: Список всех подкатегорий
        """
        descendants: List['Categories'] = []
        for child in self.subcategories.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants


class Products(models.Model):
    """Модель товаров для отслеживания цен.
    
    Attributes:
        name: Название товара
        description: Описание товара
        category: Категория товара
        brand: Бренд производителя
        created_at: Дата добавления товара в систему
        updated_at: Дата последнего обновления
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Categories,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    brand = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['name']

    def __str__(self) -> str:
        """Строковое представление товара.
        
        Returns:
            str: Название товара
        """
        return self.name

