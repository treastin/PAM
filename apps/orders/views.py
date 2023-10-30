from drf_util.utils import gt
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import GenericViewSet, mixins
from rest_framework import status

from apps.common.permisions import IsAdmin
from apps.orders.models import Order, Cart
from apps.orders.serializers import OrderSerializer, CartSerializer, CartItemSerializer, CartDetailsSerializer, \
    OrderStatusSerializer
from apps.users.models import User


class OrderViewSet(GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filterset_fields = ('user',)

    def get_queryset(self):
        qs = self.queryset

        if hasattr(self, 'swagger_fake_view'):
            qs = self.queryset.none()

        if gt(self.request.user, 'role') == User.Role.USER:
            qs = self.queryset.filter(user=self.request.user)

        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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

        instance = Order.objects.filter(id=pk).update(validated_data.pop(status))
        return Response(self.get_serializer(instance).data)


class CartViewSet(GenericViewSet, mixins.RetrieveModelMixin):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

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

        order = cart.create_order(user=self.request.user, address=validated_data['address'])

        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=False, methods=['POST'], url_path='item-update', serializer_class=CartItemSerializer)
    def item_update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        user_cart = self.request.user.get_user_cart()
        item = user_cart.add_item(validated_data['product_id'], count=validated_data.get('count'))
        return Response(self.get_serializer(item).data)

    @action(detail=False, methods=['POST'], url_path='item-remove', serializer_class=CartItemSerializer)
    def item_remove(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        user_cart = self.request.user.get_user_cart()
        user_cart.remove_item(validated_data['product_id'])
        return Response(status=status.HTTP_204_NO_CONTENT)
