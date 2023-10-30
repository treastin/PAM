from django.contrib.auth.base_user import AbstractBaseUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Sum, F, Subquery, OuterRef, DecimalField
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.generics import get_object_or_404

from apps.products.models import Products
from apps.users.models import User, UserAddress
from apps.common.models import BaseModel

# Create your models here.


class Cart(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['-id']

    def add_item(self, item_id, count):
        product = get_object_or_404(Products, id=item_id)

        try:
            item = self.items.get(product=product)
            if not item.count == count:
                item.count = count
                item.save()

        except self.items.model.DoesNotExist:
            item = self.items.create(product=product, count=count)

        return item

    def remove_item(self, item_id):
        deleted, _ = self.items.filter(product_id=item_id).delete()

        if not deleted:
            raise NotFound()

    def create_order(self, user, address):

        if not self.items.count():
            raise ValidationError({'cart': 'The cart is empty'})

        price_subquery = Subquery(Products.objects.filter(id=OuterRef('product__id')).values('price')[:1])
        discount_subquery = Subquery(Products.objects.filter(id=OuterRef('product__id')).values('discount')[:1])

        CartItem.objects.filter(cart=self).update(price=price_subquery, discount=discount_subquery)

        total = self.items.aggregate(
            total=Sum(F('price') * ((100 - F('discount')) / 100.0) * F('count'),
                      output_field=DecimalField())).get('total')

        order = Order.objects.create(user=user, address=address, cart=self, total=total)
        self.is_archived = True
        self.save()

        # Todo Create payment intent stripe

        return order


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
        CONFIRMED = ('confirmed', 'Confirmed')
        COMPLETED = ('completed', 'Completed')
        CANCELED = ('canceled', 'Canceled')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='order')
    total = models.DecimalField(max_digits=9, decimal_places=2, null=True)
    address = models.ForeignKey(UserAddress, null=True, on_delete=models.SET_NULL, related_name='orders')
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ['-id']
