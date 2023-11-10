from drf_util.utils import gt

from apps.common.helpers import stripe, decimal_to_int_stripe
from django.contrib.auth.base_user import AbstractBaseUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Sum, F, Subquery, OuterRef, DecimalField
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

    def add_item(self, product, count):

        item = self.items.filter(product=product).first()
        if item and not gt(item, 'count') == count:
            item.count = count
            item.save()

        elif not item:
            item = self.items.create(product=product, count=count)

        return item

    def create_order(self, user, address):

        if not self.items.count():
            raise ValidationError({'cart': 'The cart is empty'})

        price_subquery = Subquery(Products.objects.filter(id=OuterRef('product__id')).values('price')[:1])
        discount_subquery = Subquery(Products.objects.filter(id=OuterRef('product__id')).values('discount')[:1])

        self.items.update(price=price_subquery, discount=discount_subquery)

        total = self.items.aggregate(
            total=Sum(F('price') * ((100 - F('discount')) / 100.0) * F('count'),
                      output_field=DecimalField())).get('total')

        order = Order.objects.create(user=user, address=address, cart=self, total=total)

        stripe_amount = decimal_to_int_stripe(order.total)

        payment_intent = stripe.PaymentIntent.create(
            amount=stripe_amount,
            currency="mdl",
            metadata={'order_id': order.id, 'user_id': user.id},
            automatic_payment_methods={'enabled': True, 'allow_redirects': 'never'}
        )

        Invoice.objects.create(order=order, stripe_id=payment_intent.id, user=user, amount=stripe_amount)

        return order, payment_intent


class CartItem(BaseModel):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='carts')
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    price = models.DecimalField(max_digits=9, decimal_places=2, null=True)
    discount = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99)], null=True, default=0)
    count = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(100)])

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


class Invoice(BaseModel):
    class Status(models.TextChoices):
        REQUIRES_PAYMENT = ('requires_payment', 'Requires payment')
        SUCCEEDED = ('completed', 'Completed')
        CANCELED = ('canceled', 'Canceled')

    status = models.CharField(max_length=32, choices=Status.choices, default=Status.REQUIRES_PAYMENT)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order')
    stripe_id = models.CharField(max_length=32)
    amount = models.DecimalField(max_digits=9, decimal_places=2)

