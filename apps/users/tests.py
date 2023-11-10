from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import User, UserVerification, UserAddress

from datetime import datetime


# Create your test here.


class TestUserSignUp(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.active_user = User.objects.create(email='active@example.com', phone='+23594313184', is_active=True)
        self.inactive_user = User.objects.create(email='inactive@example.com', phone='+23594613184', is_active=False)

    def test_user_signup(self):
        data = {
            'first_name': 'User',
            'last_name': 'For Testing',
            'email': 'string@mail.ogg',
            'phone': '+23594313183',
            'password': 'StrongPassword'
        }
        response = self.client.post(reverse('signup-register'), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_signup_taken_email(self):
        data = {
            'first_name': 'User',
            'last_name': 'For Testing',
            'email': self.active_user.email,
            'phone': '+23594313183',
            'password': 'StrongPassword'
        }
        response = self.client.post(reverse('signup-register'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_full_verification(self):
        """
        Generate verification code and verifies user using said code.
        :return:
        """
        inactive_user = self.inactive_user

        response = self.client.post(reverse('signup-send-verification', kwargs={'pk': self.inactive_user.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        code_obj = UserVerification.objects.get(user=inactive_user)

        data = {
            'code': code_obj.code
        }

        response = self.client.post(reverse('signup-confirm'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        inactive_user.refresh_from_db()
        self.assertEqual(inactive_user.is_active, True)

    def test_user_verification_code_resend_full_verification(self):
        """
        Generate verification code and verifies user using said code.
        :return:
        """
        # Creating initial code

        response = self.client.post(reverse('signup-send-verification', kwargs={'pk': self.inactive_user.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refresh code if code was lost.
        inactive_user = self.inactive_user

        response = self.client.post(reverse('signup-send-verification', kwargs={'pk': self.inactive_user.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        code_obj = UserVerification.objects.filter(user=inactive_user).last()

        data = {
            'code': code_obj.code
        }

        response = self.client.post(reverse('signup-confirm'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        inactive_user.refresh_from_db()
        self.assertEqual(inactive_user.is_active, True)

    def test_user_signup_negative(self):
        existing_user = User.objects.create(email='exist@example.com', phone='+23594323184', is_active=True)

        data = {
            'first_name': 'User',
            'last_name': 'For Testing',
            'email': existing_user.email,
            'phone': existing_user.phone,
            'password': 'StrongPassword'
        }
        response = self.client.post(reverse('signup-register'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_send_verification_negative(self):

        response = self.client.post(reverse('signup-send-verification', kwargs={'pk': self.active_user.id}))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_verification_expired(self):
        user = User.objects.create(email='test@example.com', is_active=False)

        verification = UserVerification.objects.create(user=user, code='test', expires_at=datetime(2023, 1, 1))

        data = {
            'code': verification.code
        }
        response = self.client.post(reverse('signup-confirm'), data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_invalid_number_negative(self):
        data = {
            'first_name': 'User',
            'last_name': 'For Testing',
            'email': 'string@mail.ogg',
            'phone': 'DefinitelyNotAPhone',
            'password': 'StrongPassword'
        }
        response = self.client.post(reverse('signup-register'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_nonexistent_number_negative(self):
        data = {
            'first_name': 'User',
            'last_name': 'For Testing',
            'email': 'string@mail.ogg',
            'phone': '+93594313183443',
            'password': 'StrongPassword'
        }
        response = self.client.post(reverse('signup-register'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestUserLogin(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.active_user = User.objects.create(email='active@example.com', phone='+23594313184', is_active=True)
        self.inactive_user = User.objects.create(email='inactive@example.com', phone='+23594613184', is_active=False)

    def test_user_login(self):
        temporary_password = 'StrongPass'
        self.active_user.set_password(temporary_password)
        self.active_user.save()

        data = {
            'email': self.active_user.email,
            'password': temporary_password
        }

        response = self.client.post(reverse('token_obtain_pair'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_token_refresh(self):
        temporary_password = 'StrongPass'
        self.active_user.set_password(temporary_password)
        self.active_user.save()

        data = {
            'email': self.active_user.email,
            'password': temporary_password
        }

        response = self.client.post(reverse('token_obtain_pair'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {
            'refresh': response.data['refresh']
        }

        response = self.client.post(reverse('token_refresh'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_reset_password(self):
        # Generating verification code
        data = {
            'email': self.active_user.email
        }

        response = self.client.post(reverse('login-send-reset-code'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Extracting verification code and changing password using obtained verification code
        user_verification_code = UserVerification.objects.get(user=self.active_user, is_registration=False)

        new_password = 'new_password'

        data = {
            'code': user_verification_code.code,
            'password': new_password
        }

        response = self.client.post(reverse('login-reset'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Testing login with new password
        data = {
            'email': self.active_user.email,
            'password': new_password
        }

        response = self.client.post(reverse('token_obtain_pair'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestUserProfile(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create(email='user1@example.com', phone='+23594315184', is_active=True)
        self.user2 = User.objects.create(email='user2@example.com', phone='+23594413184', is_active=True)

    def test_user_profile_update(self):
        self.client.force_authenticate(self.user1)

        new_name = 'Alesha'

        data = {
            'first_name': new_name,
        }

        response = self.client.patch(reverse('user-profile-detail', kwargs={'pk': self.user1.id}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_profile_details(self):
        self.client.force_authenticate(self.user1)

        response = self.client.get(reverse('user-profile-detail', kwargs={'pk': self.user2.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_profile_update_password(self):
        old_password = 'Lorem'
        new_password = 'Ipsum'
        self.user1.set_password(old_password)
        self.user1.save()

        self.client.force_authenticate(self.user1)

        data = {
            'old_password': old_password,
            'new_password': new_password
        }

        self.client.post(reverse('user-profile-update-password'), data)

        self.user1.refresh_from_db()
        password_match = self.user1.check_password(new_password)
        self.assertTrue(password_match)

    def test_user_profile_update_password_negative(self):
        old_password = 'Lorem'
        new_password = 'Ipsum'
        self.user1.set_password(old_password)
        self.user1.save()

        self.client.force_authenticate(self.user1)

        data = {
            'old_password': old_password + 'Wrong',
            'new_password': new_password
        }

        response = self.client.post(reverse('user-profile-update-password'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_profile_update_negative(self):
        self.client.force_authenticate(self.user1)

        new_name = 'Teodor'

        data = {
            'first_name': new_name,
        }

        response = self.client.patch(reverse('user-profile-detail', kwargs={'pk': self.user2.id}), data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_profile_update(self):
        user_admin = User.objects.create(
            email='admin@example.com', phone='+23592613184', is_active=True, role=User.Role.ADMIN)

        self.client.force_authenticate(user_admin)

        new_name = 'George'

        data = {
            'first_name': new_name,
        }

        response = self.client.patch(reverse('user-profile-detail', kwargs={'pk': self.user1.id}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestUserAddress(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create(email='user1@example.com', phone='+23594315184', is_active=True)
        self.user2 = User.objects.create(email='user2@example.com', phone='+23594413184', is_active=True)

    def test_user_address_list(self):
        self.client.force_authenticate(self.user1)

        UserAddress.objects.create(user=self.user1)

        response = self.client.get(reverse('user-address-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_user_address_create(self):
        self.client.force_authenticate(self.user1)
        data = {
            'country': 'country',
            'region': 'region',
            'city': 'city',
            'street': 'street',
            'block': 'block',
            'zipcode': 'zip'
        }
        response = self.client.post(reverse('user-address-list'), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_address_update(self):
        self.client.force_authenticate(self.user1)

        address = UserAddress.objects.create(user=self.user1)

        new_country = 'new_country'
        new_region = 'new_region'

        data = {
            'country': new_country,
            'region': new_region,
        }

        response = self.client.patch(reverse('user-address-detail', kwargs={'pk': address.id}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_address_delete(self):
        self.client.force_authenticate(self.user1)

        address = UserAddress.objects.create(user=self.user1)

        response = self.client.delete(reverse('user-address-detail', kwargs={'pk': address.id}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_admin_address_update(self):
        admin = User.objects.create(email='admin@example.com', role='admin')
        self.client.force_authenticate(admin)

        address = UserAddress.objects.create(user=self.user2)

        new_country = 'new_country'
        new_region = 'new_region'

        data = {
            'country': new_country,
            'region': new_region,
        }

        response = self.client.patch(reverse('user-address-detail', kwargs={'pk': address.id}), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_address_delete(self):
        admin = User.objects.create(email='admin@example.com', role='admin')
        self.client.force_authenticate(admin)

        address = UserAddress.objects.create(user=self.user2)

        response = self.client.delete(reverse('user-address-detail', kwargs={'pk': address.id}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
