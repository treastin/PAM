import datetime

import phonenumbers
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import UserManager
from django.core.mail import send_mail
from django.db import models

# For verification code generation
from string import ascii_letters, digits
from random import choices

from rest_framework.exceptions import ValidationError

from apps.common.models import BaseModel
# Create your models here.


def generate_code() -> str:
    """Generate a random """
    code_len = 16

    code = ''.join(
        choices(
            ascii_letters +
            digits,
            k=code_len
        )
    )
    return code


def phone_is_valid(value: str):
    try:
        phone_number_obj = phonenumbers.parse(value)
    except phonenumbers.phonenumberutil.NumberParseException:
        raise ValidationError('invalid phone number.')

    if not phonenumbers.is_valid_number(phone_number_obj):
        raise ValidationError('invalid phone number.')


class User(BaseModel, AbstractBaseUser):

    class Role(models.TextChoices):
        ADMIN = ('admin', 'Administrator')
        USER = ('user', 'User')

    stripe_id = models.CharField(max_length=24, blank=True)
    first_name = models.CharField(max_length=120, blank=False)
    last_name = models.CharField(max_length=120, blank=False)
    profile_pic = models.ImageField(null=True, blank=True, upload_to="profile_pic/")
    phone = models.CharField(max_length=20, blank=False, unique=True, validators=[phone_is_valid])
    email = models.EmailField(unique=True)
    birthdate = models.DateField(null=True, default=None)
    role = models.CharField(max_length=8, choices=Role.choices, default=Role.USER)
    is_active = models.BooleanField(default=False)

    USERNAME_FIELD = "email"

    objects = UserManager()

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

        ordering = ['-id']

    def generate_code(self, is_registration=True):
        try:
            verification_code = self.verification.get(user=self, is_registration=is_registration)

            verification_code.code = generate_code()
            verification_code.expires_at = datetime.datetime.now() + datetime.timedelta(minutes=5)
            verification_code.save()

        except self.verification.model.DoesNotExist:
            verification_code = self.verification.create(
                user=self,
                is_registration=is_registration,
                code=generate_code(),
                expires_at=datetime.datetime.now() + datetime.timedelta(minutes=5)
            )

        # TODO Make this async or parallel
        if is_registration:
            mail_subject = 'PAM - Verify your account '
            mail_message = f'Here is your verification code for registration : {verification_code.code}'
        else:
            mail_subject = 'PAM - Password reset. '
            mail_message = f'Here is your verification code for password reset : {verification_code.code}'

        send_mail(
            mail_subject,
            mail_message,
            from_email=None,
            recipient_list=[self.email],
            fail_silently=True
        )

    def get_user_cart(self):
        cart, _ = self.carts.get_or_create(user=self, is_archived=False)
        return cart


class UserVerification(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification')
    code = models.CharField(max_length=16, null=False, blank=False)
    expires_at = models.DateTimeField()
    is_completed = models.BooleanField(default=False)
    is_registration = models.BooleanField(default=False)

    class Meta:

        ordering = ['-id']

    def verify_user(self) -> User:
        """
        Verify the user using the code. Returns user.
        :return:
        """
        if self.expires_at < datetime.datetime.now():
            raise ValidationError({'code': 'Verification code is expired'})

        user = self.user
        user.is_active = True
        user.save()

        self.is_completed = True
        self.save()

        return user


class UserAddress(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='address')
    country = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    block = models.CharField(max_length=10)
    zipcode = models.CharField(max_length=16)

    class Meta:

        ordering = ['-id']
