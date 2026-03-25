"""Сигналы для автоматического управления профилями пользователей."""
from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import UserProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender: type, instance: User, created: bool, **kwargs: Any) -> None:
    """Автоматически создать профиль при регистрации нового пользователя.
    
    Args:
        sender: Класс модели, отправивший сигнал
        instance: Экземпляр созданного/измененного пользователя
        created: True если пользователь только что создан
        **kwargs: Дополнительные аргументы сигнала
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender: type, instance: User, **kwargs: Any) -> None:
    """Сохранить профиль пользователя при сохранении User.
    
    Args:
        sender: Класс модели, отправивший сигнал
        instance: Экземпляр пользователя
        **kwargs: Дополнительные аргументы сигнала
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
