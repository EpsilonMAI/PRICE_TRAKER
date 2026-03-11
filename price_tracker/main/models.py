from django.db import models
from django.contrib.auth.models import User



class Items(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=256, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    seller = models.CharField(max_length=256)
    reviews = models.URLField(max_length=512, blank=True, null=True)

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Items'
        ordering = ['-id']

    def __str__(self):
        return f"{self.item_name} - {self.price}"

class PriceHistory(models.Model):
    item = models.ForeignKey(Items, on_delete=models.CASCADE, related_name='price_history')
    price_ozon = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_ym = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_wb = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tm = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Price History'
        verbose_name_plural = 'Price Histories'
        ordering = ['-tm']

    def __str__(self):
        return f"{self.item.item_name} - {self.tm.strftime('%Y-%m-%d %H:%M')}"

