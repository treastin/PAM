import datetime

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.users.models import User
from apps.common.models import BaseModel

# Create your models here.


class ProductCategory(BaseModel):
    name = models.CharField(max_length=255)
    img = models.ImageField(null=True)
    child_of = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)

    class Meta:

        ordering = ['-id']


class Products(BaseModel):
    deleted_at = models.DateTimeField(null=True, default=None)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(ProductCategory, null=True, on_delete=models.SET_NULL)
    details = models.TextField(null=True, default=None)
    price = models.DecimalField(max_digits=9, decimal_places=2)
    discount = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(99)])
    specs = models.CharField(max_length=255, null=True)

    class Meta:

        ordering = ['-id']

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = datetime.datetime.now()
        self.save()


class ProductReview(BaseModel):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField(null=True, default=None)

    class Meta:
        ordering = ['-id']


class ProductAttachments(BaseModel):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='attachments')
    attachment = models.ImageField(upload_to='product/attachments')

    class Meta:
        ordering = ['-id']
