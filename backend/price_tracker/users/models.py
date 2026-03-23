from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings


class CustomRules(models.Model):
    """Правила для пользователя"""
    custom_rule = models.CharField(max_length=255)
    
    class Meta:
        verbose_name_plural = "Custom Rules"
    
    def __str__(self):
        return self.custom_rule


class UserProfile(models.Model):
    """Расширение модели User через OneToOne"""
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
    
    def __str__(self):
        return f"Профиль {self.user.username}"

