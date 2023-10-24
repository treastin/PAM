from django.contrib.auth.base_user import AbstractBaseUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, IntegrityError
from django.db.models import Sum, F
from django.db.models.signals import pre_save
from django.dispatch import receiver
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
            item, was_created = self.items.get_or_create(product_id=item_id)
        except IntegrityError:
            raise ValidationError({'product': 'Invalid product'})

        if count < 1:
            raise ValidationError({'count': 'Item count can\'t be less than 1'})

        item.count = count
        item.price = item.product.price
        item.discount = item.product.discount

        item.save()
        return item

    def remove_item(self, item_id):
        self.items.filter(product_id=item_id).delete()


class CartItem(BaseModel):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='carts')
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    price = models.DecimalField(max_digits=9, decimal_places=2, null=True)
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
    total = models.DecimalField(max_digits=9, decimal_places=2, null=True)
    address = models.ForeignKey(UserAddress, null=True, on_delete=models.SET_NULL, related_name='orders')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ['-id']

    def create_order(self, user):
        user_cart = self.cart.objects.filter(user=user, is_archived=False).first()

        if not user_cart:
            raise ValidationError({'cart': 'The cart is empty'})

        if not user_cart.items.count():
            raise ValidationError({'cart': 'The cart is empty'})

        total = user_cart.items.aggregate(
            total=Sum(F('price') * ((100 - F('discount')) / 100) * F('count'))).get('total')

        order = self.objects.create(user=user, cart=user_cart, total=total)
        user_cart.is_archived = True
        user_cart.save()

        return order


@receiver(pre_save, sender=Order)
def create_order(sender, instance, *args, **kwargs):
    user_cart = instance.user.get_user_cart()

    if not user_cart:
        raise ValidationError({'cart': 'The cart is empty'})

    if not user_cart.items.count():
        raise ValidationError({'cart': 'The cart is empty'})

    total = user_cart.items.aggregate(
        total=Sum(F('price') * ((100 - F('discount')) / 100) * F('count'))).get('total')

    instance.cart = user_cart
    instance.total = total

    user_cart.is_archived = True
    user_cart.save()
