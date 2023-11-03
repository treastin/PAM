from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.orders.models import Order
from apps.products.models import Products
from apps.users.models import User


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

        item = self.user.get_user_cart().add_item(self.product1, 2)

        data = {
            'product': self.product1.id,
            'count': 10
        }

        response = self.client.post(reverse('cart-item-update'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEquals(item.count, response.data['count'])

    def test_user_remove_item_from_cart(self):
        self.client.force_authenticate(self.user)

        self.user.get_user_cart().add_item(self.product1, 2)

        data = {
            'product': self.product1.id
        }

        response = self.client.post(reverse('cart-item-remove'), data)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_get_items(self):
        self.client.force_authenticate(self.user)

        user_cart = self.user.get_user_cart()
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

        data = {
            'product': self.product1.id
        }
        response = self.client.post(reverse('cart-item-remove'), data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

