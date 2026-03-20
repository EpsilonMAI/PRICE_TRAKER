from rest_framework import serializers
from .models import Products, Categories


class ProductsSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Products
        fields = ("id", "name", "description", "category", "category_name", "brand", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at", "category_name")

