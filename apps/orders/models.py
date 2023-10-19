from django.contrib.auth.base_user import AbstractBaseUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, IntegrityError
from rest_framework import status
from rest_framework.exceptions import ValidationError

from apps.products.models import Products
from apps.users.models import User, UserAddress
from apps.common.models import BaseModel

# Create your models here.


class Cart(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['-id']

    def add_item(self, item_id, count=None):
        try:
            item, was_created = self.items.get_or_create(cart_id=self.id, product_id=item_id)
        except IntegrityError:
            raise ValidationError({'product': 'Invalid product'})

        if not was_created:
            item.count = count
        item.save()
        return item

    def rm_item(self, item_id):
        CartItem.objects.filter(cart_id=self.id, product_id=item_id).delete()


class CartItem(BaseModel):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='carts')
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    price = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    discount = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99)], null=True, default=0)
    count = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['-id']


class Order(BaseModel):
    class Status(models.TextChoices):
        PENDING = ('pending', 'Pending')
        COMPLETED = ('completed', 'Completed')
        CANCELED = ('canceled', 'Canceled')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='order')
    address = models.ForeignKey(UserAddress, null=True, on_delete=models.SET_NULL, related_name='orders')
    status = models.SmallIntegerField(choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ['-id']
