"""Сериализаторы для регистрации и профиля пользователя."""
from typing import Dict, Any, Optional

from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации новых пользователей.
    
    Attributes:
        password: Пароль пользователя (только для записи)
    """
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data: Dict[str, Any]) -> User:
        """Создание нового пользователя с хешированием пароля.
        
        Args:
            validated_data: Валидированные данные пользователя
            
        Returns:
            User: Созданный пользователь
        """
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email"),
            password=validated_data["password"],
        )
        return user
    

class ProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения профиля пользователя.
    
    Объединяет данные из модели User и связанного UserProfile.
    
    Attributes:
        avatar: URL аватара пользователя
        phone: Номер телефона
        created_at: Дата создания профиля
        custom_rules: Пользовательские правила отслеживания
        tracking_count: Общее количество отслеживаемых товаров
        active_count: Количество активно отслеживаемых товаров
    """
    avatar = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    custom_rules = serializers.SerializerMethodField()
    tracking_count = serializers.SerializerMethodField()
    active_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'date_joined', 
                  'avatar', 'phone', 'created_at', 'custom_rules', 
                  'tracking_count', 'active_count')

    def get_avatar(self, obj: User) -> Optional[str]:
        """Получить URL аватара пользователя.
        
        Args:
            obj: Экземпляр пользователя
            
        Returns:
            Optional[str]: URL аватара или None
        """
        if hasattr(obj, 'profile') and obj.profile.avatar:
            return obj.profile.avatar.url
        return None
    
    def get_phone(self, obj: User) -> Optional[str]:
        """Получить номер телефона пользователя.
        
        Args:
            obj: Экземпляр пользователя
            
        Returns:
            Optional[str]: Номер телефона или None
        """
        if hasattr(obj, 'profile'):
            return obj.profile.phone
        return None
    
    def get_created_at(self, obj: User) -> Optional[str]:
        """Получить дату создания профиля.
        
        Args:
            obj: Экземпляр пользователя
            
        Returns:
            Optional[str]: Дата создания профиля или None
        """
        if hasattr(obj, 'profile'):
            return obj.profile.created_at
        return None
    
    def get_custom_rules(self, obj: User) -> Optional[str]:
        """Получить пользовательские правила отслеживания.
        
        Args:
            obj: Экземпляр пользователя
            
        Returns:
            Optional[str]: Текст правил или None
        """
        if hasattr(obj, 'profile') and obj.profile.custom_rules:
            return obj.profile.custom_rules.custom_rule
        return None
    
    def get_tracking_count(self, obj: User) -> int:
        """Получить общее количество отслеживаемых товаров.
        
        Args:
            obj: Экземпляр пользователя
            
        Returns:
            int: Количество отслеживаемых товаров
        """
        return obj.tracking_items.count()
    
    def get_active_count(self, obj: User) -> int:
        """Получить количество активных отслеживаемых товаров.
        
        Args:
            obj: Экземпляр пользователя
            
        Returns:
            int: Количество активных товаров
        """
        return obj.tracking_items.filter(is_active=True).count()
        