"""Сериализаторы для регистрации и профиля пользователя."""
from typing import Dict, Any, Optional

from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile, CustomRules


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
    notify_price_drop = serializers.SerializerMethodField()
    notify_back_in_stock = serializers.SerializerMethodField()
    notify_weekly_summary = serializers.SerializerMethodField()
    tracking_count = serializers.SerializerMethodField()
    active_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'date_joined', 
                  'avatar', 'phone', 'created_at',
                  'notify_price_drop', 'notify_back_in_stock', 'notify_weekly_summary',
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
        if hasattr(obj, 'profile'):
            return obj.profile.created_at
        return None

    def _get_rules(self, obj: User):
        """Получить или создать CustomRules для профиля пользователя."""
        if not hasattr(obj, 'profile'):
            return None
        rules = obj.profile.custom_rules
        if rules is None:
            rules = CustomRules.objects.create()
            obj.profile.custom_rules = rules
            obj.profile.save(update_fields=["custom_rules"])
        return rules

    def get_notify_price_drop(self, obj: User) -> bool:
        rules = self._get_rules(obj)
        return rules.notify_price_drop if rules else True

    def get_notify_back_in_stock(self, obj: User) -> bool:
        rules = self._get_rules(obj)
        return rules.notify_back_in_stock if rules else True

    def get_notify_weekly_summary(self, obj: User) -> bool:
        rules = self._get_rules(obj)
        return rules.notify_weekly_summary if rules else False

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


class NotificationSettingsSerializer(serializers.Serializer):
    """Сериализатор для обновления настроек уведомлений."""

    notify_price_drop = serializers.BooleanField()
    notify_back_in_stock = serializers.BooleanField()
    notify_weekly_summary = serializers.BooleanField()
