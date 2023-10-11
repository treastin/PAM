from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.users.models import User


# Create your models here.


class BaseModelMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ProductCategory(BaseModelMixin):
    name = models.CharField(max_length=255)
    img = models.ImageField()
    subcategory_of = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)


class Products(BaseModelMixin):
    deleted_at = models.DateTimeField(null=True, default=None)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(ProductCategory, null=True, on_delete=models.SET_NULL)
    details = models.TextField(null=True, default=None)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    discount = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(99)])
    specs = models.CharField(max_length=255)


class ProductReview(BaseModelMixin):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField(null=True, default=None)


class ProductAttachments(BaseModelMixin):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='attachments')
    attachment = models.FileField()
