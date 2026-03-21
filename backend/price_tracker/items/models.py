from django.db import models


class Categories(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_ancestors(self):
        """Получить всех родителей (Электроника <- Планшеты <- iPad)"""
        ancestors = []
        category = self.parent
        while category:
            ancestors.insert(0, category)
            category = category.parent
        return ancestors

    def get_descendants(self):
        """Получить всех потомков"""
        descendants = []
        for child in self.subcategories.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants


class Products(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Categories,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    brand = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Products"

    def __str__(self):
        return self.name

