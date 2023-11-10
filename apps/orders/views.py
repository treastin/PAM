from drf_util.utils import gt
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import mixins, GenericViewSet
from rest_framework import status

from apps.common.permisions import IsAdmin, IsAdminOrOwner
from apps.orders.models import Order, Cart
from apps.orders.serializers import OrderSerializer, CartSerializer, CartItemDetailSerializer, CartDetailsSerializer, \
    OrderStatusSerializer, CartItemSerializer, OrderDetailSerializer
from apps.users.models import User
from drf_util.views import BaseViewSet


class OrderViewSet(BaseViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filterset_fields = ('user',)
    permission_classes_by_action = {
        "partial_update": (IsAuthenticated, IsAdmin,),
        "update": (IsAuthenticated, IsAdmin,),
        "default": (IsAuthenticated,)
    }

    def get_queryset(self):
        qs = self.queryset

        if hasattr(self, 'swagger_fake_view'):
            qs = self.queryset.none()

        if gt(self.request.user, 'role') == User.Role.USER:
            qs = self.queryset.filter(user=self.request.user)

        if self.action in ['detail']:
            qs = self.queryset.select_related('address', 'cart')

        return qs

    def get_serializer_class(self):
        serializer = self.serializer_class
        if self.action in ['retrieve']:
            serializer = OrderDetailSerializer

        if self.action in ['partial_update', 'update']:
            serializer = OrderStatusSerializer

        return serializer

    @action(detail=True, methods=['POST'], serializer_class=Serializer)
    def cancel(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.status = Order.Status.CANCELED
        instance.save()
        return Response(status.HTTP_200_OK)

    @action(detail=True, methods=['PATCH'], serializer_class=OrderStatusSerializer,
            permission_classes=(IsAuthenticated, IsAdmin))
    def update_status(self, request, pk, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        instance = Order.objects.filter(id=pk).update(**validated_data)
        return Response(self.get_serializer(instance).data)


class CartViewSet(GenericViewSet, mixins.RetrieveModelMixin):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = (IsAuthenticated, IsAdminOrOwner,)

    def get_serializer_class(self):

        if self.action in ['retrieve']:
            return CartDetailsSerializer

        return self.serializer_class

    @action(detail=False, methods=['POST'], serializer_class=OrderSerializer)
    def checkout(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        cart = request.user.get_user_cart()

        order, payment_intent = cart.create_order(user=self.request.user, address=validated_data['address'])

        response = {
            'order': self.get_serializer(order).data,
            'client_secret': payment_intent.client_secret
        }
        return Response(response)

    @action(detail=False, methods=['POST'], url_path='item-update', serializer_class=CartItemSerializer)
    def item_update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        user_cart = self.request.user.get_user_cart(create_if_none=True)
        item = user_cart.add_item(validated_data['product'], validated_data['count'])
        return Response(CartItemDetailSerializer(item).data)

    @action(detail=False, methods=['POST'], url_path='item-remove', serializer_class=CartItemSerializer)
    def item_remove(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        user_cart = self.request.user.get_user_cart()
        user_cart.items.filter(product=validated_data['product']).delete()

        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'], serializer_class=Serializer)
    def clear(self, request, *args, **kwargs):
        user_cart = self.request.user.get_user_cart()
        user_cart.items.all().delete()

        return Response(status=status.HTTP_200_OK)

