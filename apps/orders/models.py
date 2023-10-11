from django.contrib.auth.base_user import AbstractBaseUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from apps.products.models import Products
from apps.users.models import User, UserAddress


# Create your models here.

class BaseModelMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Cart(BaseModelMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')
    is_archived = models.BooleanField(default=False)


class CartItem(BaseModelMixin):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='carts')
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    price = models.DecimalField(max_digits=6, decimal_places=2)
    discount = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(99)])
    count = models.PositiveSmallIntegerField()


class Order(BaseModelMixin):

    class Status(models.IntegerChoices):
        PENDING = (1, 'Pending')
        SHIPPED = (2, 'Shipped')
        COMPLETED = (3, 'Completed')
        CANCELED = (4, 'Canceled')
        REFUNDED = (5, 'Refunded')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='order')
    address = models.ForeignKey(UserAddress,null=True, on_delete=models.SET_NULL, related_name='orders')
    status = models.SmallIntegerField(choices=Status.choices, default=Status.PENDING)

