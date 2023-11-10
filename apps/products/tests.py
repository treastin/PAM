import os.path
import shutil

from django.core.files.uploadedfile import SimpleUploadedFile, File

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.products.models import Products, ProductAttachments, ProductReview, ProductCategory
from apps.users.models import User

from config.settings import MEDIA_FOR_TESTING_ROOT, MEDIA_ROOT

# Create your test here.
TEST_DIR = os.path.join(MEDIA_ROOT, 'testing')


class TestProduct(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create(
            email='user@example.com', phone='+23598438282', role=User.Role.USER, is_active=True)
        self.admin = User.objects.create(
            email='admin@example.com', phone='+23598438283', role=User.Role.ADMIN, is_active=True)

        self.product1 = Products.objects.create(name='test1', price=3, discount=0)
        self.product2 = Products.objects.create(name='test2', price=4, discount=0)

    def test_user_get(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse('product-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_get_bestsellers(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse('product-best-sellers'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_get_bestsellers_negative(self):
        """If there is no product to show"""
        self.client.force_authenticate(self.user)

        Products.objects.all().delete()

        response = self.client.get(reverse('product-best-sellers'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_post_negative(self):
        self.client.force_authenticate(self.user)

    def test_user_update_negative(self):
        self.client.force_authenticate(self.user)

        data = {
            'price': 0
        }
        response = self.client.patch(reverse('product-detail', kwargs={'pk': self.product1.id}), data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_delete_negative(self):
        self.client.force_authenticate(self.user)

        response = self.client.delete(reverse('product-detail', kwargs={'pk': self.product1.id}))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_post(self):
        self.client.force_authenticate(self.admin)

        data = {
            'name': 'test1',
            'price': 9,
            'discount': 12,
            'specs': 'Promo'
        }

        response = self.client.post(reverse('product-list'), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_post_invalid_discount(self):
        self.client.force_authenticate(self.admin)

        data = {
            'name': 'test1',
            'price': 9,
            'discount': -2
        }

        response = self.client.post(reverse('product-list'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {
            'name': 'test1',
            'price': 9,
            'discount': 200
        }

        response = self.client.post(reverse('product-list'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_delete(self):
        self.client.force_authenticate(self.admin)

        response = self.client.delete(reverse('product-detail', kwargs={'pk': self.product1.id}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_admin_update(self):
        self.client.force_authenticate(self.admin)

        data = {
            'discount': 20
        }
        response = self.client.patch(reverse('product-detail', kwargs={'pk': self.product1.id}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


@override_settings(MEDIA_ROOT=TEST_DIR)
class TestProductAttachments(TestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_DIR)

    def setUp(self) -> None:
        self.client = APIClient()

        self.user = User.objects.create(
            email='user@example.com', phone='+23598438282', role=User.Role.USER, is_active=True)
        self.admin = User.objects.create(
            email='admin@example.com', phone='+23598438283', role=User.Role.ADMIN, is_active=True)

        self.product1 = Products.objects.create(name='test1', price=3, discount=0)

        self.img_path = os.path.join(MEDIA_FOR_TESTING_ROOT, 'green_square.jpg')
        self.img = SimpleUploadedFile(
            name='test_image.jpg', content=open(self.img_path, 'rb').read(), content_type='image/jpeg')
        self.attachment = ProductAttachments.objects.create(product=self.product1, attachment=self.img)

    def test_user_get(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse('attachments-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_get_filtered_product(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse('attachments-list'), {'product': self.product1.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_user_post_negative(self):
        self.client.force_authenticate(self.user)

        data = {
            'product': 1,
            'attachment': self.img
        }

        response = self.client.post(reverse('attachments-list'), data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_update_negative(self):
        self.client.force_authenticate(self.user)

        img = SimpleUploadedFile(
            name='test_image.jpg', content=open(self.img_path, 'rb').read(), content_type='image/jpeg')
        data = {
            'product': 1,
            'attachment': img
        }

        response = self.client.patch(reverse('attachments-detail', kwargs={'pk': self.product1.id}), data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_delete(self):
        self.client.force_authenticate(self.user)

        response = self.client.delete(reverse('attachments-detail', kwargs={'pk': self.attachment.id}))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_post(self):
        self.client.force_authenticate(self.admin)

        img = SimpleUploadedFile(
            name='test_image.jpg', content=open(self.img_path, 'rb').read(), content_type='image/jpeg')

        data = {
            'product': self.product1.id,
            'attachment': img
        }

        response = self.client.post(reverse('attachments-list'), data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_update(self):
        self.client.force_authenticate(self.admin)

        attachment = self.product1.attachments.create(attachment=File('/media/test/green_square.jpg'))

        img = SimpleUploadedFile(
            name='test_image.jpg', content=open(self.img_path, 'rb').read(), content_type='image/jpeg')
        data = {
            'attachment': img
        }

        response = self.client.patch(reverse('attachments-detail', kwargs={'pk': attachment.id}), data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_delete(self):
        self.client.force_authenticate(self.admin)

        response = self.client.delete(reverse('attachments-detail', kwargs={'pk': self.attachment.id}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class TestProductCategory(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()

        self.user = User.objects.create(
            email='user@example.com', phone='+23598438282', role=User.Role.USER, is_active=True)
        self.admin = User.objects.create(
            email='admin@example.com', phone='+23598438283', role=User.Role.ADMIN, is_active=True)

        self.product1 = Products.objects.create(name='test1', price=3, discount=0)

        self.category = ProductCategory.objects.create(name='test')

    def test_user_get(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse('category-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_post_negative(self):
        self.client.force_authenticate(self.user)

        data = {
            'name': 1,
        }

        response = self.client.post(reverse('category-list'), data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_update_negative(self):
        self.client.force_authenticate(self.user)

        data = {
            'name': 1
        }

        response = self.client.patch(reverse('category-detail', kwargs={'pk': self.product1.id}), data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_delete(self):
        self.client.force_authenticate(self.user)

        response = self.client.delete(reverse('category-detail', kwargs={'pk': self.category.id}))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_post(self):
        self.client.force_authenticate(self.admin)

        data = {
            'name': 'test1'
        }

        response = self.client.post(reverse('category-list'), data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_update(self):
        self.client.force_authenticate(self.admin)

        data = {
            'name': 'test1'
        }

        response = self.client.patch(reverse('category-detail', kwargs={'pk': self.category.id}), data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_delete(self):
        self.client.force_authenticate(self.admin)

        response = self.client.delete(reverse('category-detail', kwargs={'pk': self.category.id}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class TestProductReview(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()

        self.user = User.objects.create(
            email='user@example.com', phone='+23598438282', role=User.Role.USER, is_active=True)
        self.user2 = User.objects.create(
            email='user2@example.com', phone='+23598338282', role=User.Role.USER, is_active=True)

        self.admin = User.objects.create(
            email='admin@example.com', phone='+23598438283', role=User.Role.ADMIN, is_active=True)

        self.product1 = Products.objects.create(name='test1', price=3, discount=0)

        self.review = ProductReview.objects.create(user=self.user, text='', rating=3, product=self.product1)

    def test_user_get(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(reverse('review-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_post(self):
        self.client.force_authenticate(self.user)

        data = {
            'product': self.product1.id,
            'text': 'text',
            'rating': 4
        }

        response = self.client.post(reverse('review-list'), data=data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_update(self):
        self.client.force_authenticate(self.user)

        data = {
            'product': self.product1.id,
            'text': 'text!',
            'rating': 2
        }

        response = self.client.patch(reverse('review-detail', kwargs={'pk': self.review.id}), data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_delete(self):
        self.client.force_authenticate(self.user)

        response = self.client.delete(reverse('review-detail', kwargs={'pk': self.review.id}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_update_foreign_review_negative(self):
        self.client.force_authenticate(self.user2)

        data = {
            'product': self.product1.id,
            'text': 'text!',
            'rating': 2
        }

        response = self.client.patch(reverse('review-detail', kwargs={'pk': self.review.id}), data=data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_delete_foreign_review_negative(self):
        self.client.force_authenticate(self.user2)

        response = self.client.delete(reverse('review-detail', kwargs={'pk': self.review.id}))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_update_foreign_review(self):
        self.client.force_authenticate(self.admin)

        data = {
            'product': self.product1.id,
            'text': '[REDACTED]',
            'rating': 2
        }

        response = self.client.patch(reverse('review-detail', kwargs={'pk': self.review.id}), data=data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_delete(self):
        self.client.force_authenticate(self.admin)

        response = self.client.delete(reverse('review-detail', kwargs={'pk': self.review.id}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)