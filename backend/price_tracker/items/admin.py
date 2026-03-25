"""Административная панель для управления товарами и категориями."""
from django.contrib import admin

from .models import Products, Categories


@admin.register(Categories)
class CategoriesAdmin(admin.ModelAdmin):
    """Административная панель для категорий товаров."""
    list_display = ('name', 'parent')
    search_fields = ('name',)
    list_filter = ('parent',)


@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    """Административная панель для товаров."""
    list_display = ('name', 'brand', 'category', 'created_at')
    search_fields = ('name', 'brand')
    list_filter = ('category', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
