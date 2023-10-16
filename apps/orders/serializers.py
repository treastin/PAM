from rest_framework import serializers

from apps.orders.models import Order, Cart, CartItem


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

        read_only_fields = [
            'id',
            'created_at',
            'updated_at'
        ]


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = '__all__'

        read_only_fields = [
            'id',
            'created_at',
            'updated_at'
        ]


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = '__all__'

        read_only_fields = [
            'id',
            'created_at',
            'updated_at'
        ]