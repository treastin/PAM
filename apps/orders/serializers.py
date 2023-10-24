from django.db.models import Sum, F
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
    class Meta:
        model = CartItem
        fields = [
            'id',
            'created_at',
            'updated_at',
            'product',
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
        ]

        depth = 1


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
        return obj.items.aggregate(total=Sum(F('price') * ((100 - F('discount')) / 100) * F('count'))).get('total')
