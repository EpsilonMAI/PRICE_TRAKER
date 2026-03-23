from django.db import models


class Stores(models.Model):
    """Магазины для отслеживания цен"""
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

    def __str__(self):
        return self.name

