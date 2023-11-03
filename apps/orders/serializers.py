from django.db.models import Sum, F, DecimalField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.orders.models import Order, Cart, CartItem


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'user',
            'cart',
            'status',
            'total'
        ]

    def validate(self, attrs):
        if attrs['address'].user != self.context['request'].user:
            raise serializers.ValidationError({'address': 'This is another user\'s address'})
        return attrs


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'status'
        ]


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = '__all__'

        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'user',
            'is_archived',
        ]


class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()

    class Meta:
        model = CartItem
        fields = [
            'id',
            'created_at',
            'updated_at',
            'product',
            'product_id',
            'price',
            'discount',
            'count'

        ]

        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'price',
            'discount',
            'product'
        ]

        extra_kwargs = {
            'product_id': {'write_only': True, 'required': True}
        }

        depth = 1

    def validate(self, attrs):
        count = attrs.get('count')
        if count is None or count < 1:
            raise ValidationError({'count': 'Count can\'t be less than 1'})
        return attrs


class CartDetailsSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'id',
            'created_at',
            'updated_at',
            'is_archived',
            'items',
            'total',
        ]

    def get_total(self, obj):
        total = obj.items.aggregate(
            total=Sum(F('product__price') * ((100 - F('product__discount')) / 100.0) * F('count'),
                      output_field=DecimalField())).get('total')
        return total
