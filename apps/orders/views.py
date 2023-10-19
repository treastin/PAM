from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import GenericViewSet, mixins
from rest_framework import status

from apps.common.permisions import IsAdmin
from apps.orders.models import Order, Cart, CartItem
from apps.orders.serializers import OrderSerializer, CartSerializer, CartItemSerializer, CartDetailsSerializer
from apps.users.models import User
from apps.products.models import Products


class OrderViewSet(GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if hasattr(self, 'swagger_fake_view'):
            return self.queryset.none()

        if self.request.user.Role == 'admin':
            return self.queryset

        if self.request.user.Role == 'user':
            return self.queryset.filter(user=self.request.user)

        return self.queryset

    def perform_create(self, serializer):
        user_cart = Cart.objects.filter(user=self.request.user, is_archived=False).first()
        if user_cart:
            if not user_cart.items.count():
                raise ValidationError({'cart': 'The cart is empty'})

            serializer.save(user=self.request.user, cart=user_cart)
            user_cart.is_archived = True
            user_cart.save()
        else:
            raise ValidationError({'cart': 'The cart is empty'})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.status = Order.Status.CANCELED
        instance.save()
        return Response(status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['PATCH'], url_path='update-status',
            serializer_class=Serializer, permission_classes=(IsAuthenticated, IsAdmin))
    def update_status(self, request, pk, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        instance = Order.objects.filter(id=pk).update(validated_data.pop(status))
        return Response(self.get_serializer(instance).data)


class CartViewSet(GenericViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=['GET'], serializer_class=CartDetailsSerializer)
    def items(self, request, *args, **kwargs):
        instance = self.queryset.filter(
            user=self.request.user, is_archived=False).prefetch_related('items').first()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'], url_path='item-update', serializer_class=CartItemSerializer)
    def item_update(self, request, pk, *args, **kwargs):
        instance = self.request.user.get_user_cart()
        item = instance.add_item(pk, count=request.data['count'])
        return Response(CartItemSerializer(item).data)

    @action(detail=True, methods=['DELETE'], url_path='item-remove')
    def delete_item(self, request, pk, *args, **kwargs):
        instance = self.request.user.get_user_cart()
        instance.rm_item(pk)
        return Response()
