from unittest import mock

from django.test import TestCase
from django.urls import reverse
from drf_util.utils import gt
from rest_framework import status
from rest_framework.test import APIClient

from apps.orders.models import Order, Invoice
from apps.products.models import Products
from apps.users.models import User, UserAddress


# Create your test here.


class TestCart(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create(email='user@example.com', phone='+23560391790', is_active=True)
        self.other_user = User.objects.create(email='other_user@example.com', phone='+23560391791', is_active=True)

        self.product1 = Products.objects.create(name='test', price=99.99, discount=0)
        self.product2 = Products.objects.create(name='test2', price=11.11, discount=0)

    def test_user_add_item_to_cart(self):
        self.client.force_authenticate(self.user)
        data = {
            'product': self.product1.id,
            'count': 2
        }

        response = self.client.post(reverse('cart-item-update'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_update_item_count(self):
        self.client.force_authenticate(self.user)

        item = self.user.get_user_cart(create_if_none=True).add_item(self.product1, 2)

        data = {
            'product': self.product1.id,
            'count': 10
        }

        response = self.client.post(reverse('cart-item-update'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEquals(item.count, response.data['count'])

    def test_user_remove_item_from_cart(self):
        self.client.force_authenticate(self.user)

        self.user.get_user_cart(create_if_none=True).add_item(self.product1, 2)

        data = {
            'product': self.product1.id
        }

        response = self.client.post(reverse('cart-item-remove'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_get_items(self):
        self.client.force_authenticate(self.user)

        user_cart = self.user.get_user_cart(create_if_none=True)
        user_cart.add_item(self.product1, 2)
        user_cart.add_item(self.product2, 1)

        response = self.client.get(reverse('cart-detail', kwargs={'pk': user_cart.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['items']), 2)

    def test_user_add_item_invalid_count_negative(self):
        self.client.force_authenticate(self.user)
        data = {
            'product': self.product1.id,
            'count': -2
        }

        response = self.client.post(reverse('cart-item-update'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_add_invalid_item(self):
        self.client.force_authenticate(self.user)
        data = {
            'product': 999999,
            'count': 1
        }

        response = self.client.post(reverse('cart-item-update'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_delete_invalid_item(self):
        self.client.force_authenticate(self.user)
        self.user.get_user_cart(create_if_none=True)
        data = {
            'product': self.product1.id
        }
        response = self.client.post(reverse('cart-item-remove'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_delete_item_from_invalid_cart(self):
        self.client.force_authenticate(self.user)
        data = {
            'product': self.product1.id
        }
        response = self.client.post(reverse('cart-item-remove'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_clear_cart(self):
        self.client.force_authenticate(self.user)

        user_cart = self.user.get_user_cart(create_if_none=True)
        user_cart.add_item(self.product1, 2)
        user_cart.add_item(self.product2, 1)

        response = self.client.post(reverse('cart-clear'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestOrders(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create(email='user@example.com', phone='+23560391790', is_active=True)
        self.user_address = UserAddress.objects.create(user=self.user)
        self.other_user = User.objects.create(email='other_user@example.com', phone='+23560391791', is_active=True)
        self.admin_user = User.objects.create(
            email='admin@example.com', phone='+23561391790', is_active=True, role='admin')

        self.product1 = Products.objects.create(name='test', price=99.99, discount=0)
        self.product2 = Products.objects.create(name='test2', price=11.11, discount=0)

    def test_user_get_order(self):
        self.client.force_authenticate(self.user)

        cart = self.user.get_user_cart(create_if_none=True)
        cart.add_item(self.product1, 2)
        cart.add_item(self.product2, 1)
        current_order = Order.objects.create(user=self.user, cart=cart, address=self.user_address)

        response = self.client.get(reverse('order-detail', kwargs={'pk': current_order.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_get_foreign_order(self):
        self.client.force_authenticate(self.other_user)

        cart = self.user.get_user_cart(create_if_none=True)
        cart.add_item(self.product1, 2)
        cart.add_item(self.product2, 1)
        current_order = Order.objects.create(user=self.user, cart=cart, address=self.user_address)

        response = self.client.get(reverse('order-detail', kwargs={'pk': current_order.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_list_order(self):
        self.client.force_authenticate(self.user)

        cart = self.user.get_user_cart(create_if_none=True)
        cart.add_item(self.product1, 2)
        cart.add_item(self.product2, 1)
        Order.objects.create(user=self.user, cart=cart, address=self.user_address)

        response = self.client.get(reverse('order-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_create_order(self):
        self.client.force_authenticate(self.user)

        cart = self.user.get_user_cart(create_if_none=True)
        cart.add_item(self.product1, 2)
        cart.add_item(self.product2, 1)
        data = {
            'address': self.user_address.id
        }

        response = self.client.post(reverse('cart-checkout'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_create_order_empty_cart_negative(self):
        self.client.force_authenticate(self.user)

        cart = self.user.get_user_cart(create_if_none=True)
        data = {
            'address': self.user_address.id
        }

        response = self.client.post(reverse('cart-checkout'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_create_order_foreign_address(self):
        self.client.force_authenticate(self.other_user)

        cart = self.user.get_user_cart(create_if_none=True)
        cart.add_item(self.product1, 2)
        cart.add_item(self.product2, 1)
        data = {
            'address': self.user_address.id
        }

        response = self.client.post(reverse('cart-checkout'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_cancel_order(self):
        self.client.force_authenticate(self.user)

        cart = self.user.get_user_cart(create_if_none=True)
        cart.add_item(self.product1, 2)
        cart.add_item(self.product2, 1)
        current_order = Order.objects.create(cart=cart, user=self.user, address=self.user_address)

        response = self.client.post(reverse('order-cancel', kwargs={'pk': current_order.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_cancel_foreign_order(self):
        self.client.force_authenticate(self.other_user)

        cart = self.user.get_user_cart(create_if_none=True)
        cart.add_item(self.product1, 2)
        cart.add_item(self.product2, 1)
        current_order = Order.objects.create(cart=cart, user=self.user, address=self.user_address)

        response = self.client.post(reverse('order-cancel', kwargs={'pk': current_order.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_cancel_order(self):
        self.client.force_authenticate(self.admin_user)

        cart = self.user.get_user_cart(create_if_none=True)
        cart.add_item(self.product1, 2)
        cart.add_item(self.product2, 1)
        current_order = Order.objects.create(cart=cart, user=self.user, address=self.user_address)

        response = self.client.post(reverse('order-cancel', kwargs={'pk': current_order.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_update_order(self):
        self.client.force_authenticate(self.admin_user)

        cart = self.user.get_user_cart(create_if_none=True)
        cart.add_item(self.product1, 2)
        cart.add_item(self.product2, 1)
        current_order = Order.objects.create(cart=cart, user=self.user, address=self.user_address)

        data = {
            'status': Order.Status.COMPLETED
        }
        response = self.client.patch(reverse('order-update-status', kwargs={'pk': current_order.id}), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        current_order.refresh_from_db()
        self.assertEqual(current_order.status, Order.Status.COMPLETED)

    @mock.patch('apps.common.views.get_event_from_request')
    def test_order_update_on_payment(self, mock_get_event_from_request):
        # Create user using endpoint
        self.client.force_authenticate(self.user)

        cart = self.user.get_user_cart(create_if_none=True)
        cart.add_item(self.product1, 2)
        cart.add_item(self.product2, 1)
        data = {
            'address': self.user_address.id
        }

        response = self.client.post(reverse('cart-checkout'), data)

        invoice = Invoice.objects.first()
        self.assertEqual(invoice.status, Invoice.Status.REQUIRES_PAYMENT)

        mock_event = {
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'metadata': {
                        'order_id': gt(response.data, 'order.id'),
                        'user_id': self.user.id
                    }
                }
            }
        }
        mock_get_event_from_request.return_value = mock_event

        self.client.post(reverse('webhooks-stripe'))

        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.Status.SUCCEEDED)

    @mock.patch('apps.common.views.get_event_from_request')
    def test_order_update_on_payment_canceled(self, mock_get_event_from_request):
        self.client.force_authenticate(self.user)

        cart = self.user.get_user_cart(create_if_none=True)
        cart.add_item(self.product1, 2)
        cart.add_item(self.product2, 1)
        data = {
            'address': self.user_address.id
        }

        response = self.client.post(reverse('cart-checkout'), data)

        invoice = Invoice.objects.first()
        self.assertEqual(invoice.status, Invoice.Status.REQUIRES_PAYMENT)

        mock_event = {
            'type': 'payment_intent.canceled',
            'data': {
                'object': {
                    'metadata': {
                        'order_id': gt(response.data, 'order.id'),
                        'user_id': self.user.id
                    }
                }
            }
        }
        mock_get_event_from_request.return_value = mock_event

        self.client.post(reverse('webhooks-stripe'))

        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.Status.CANCELED)
