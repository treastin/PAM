import datetime

import phonenumbers
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import UserManager
from django.db import models
from django.utils import timezone

# For verification code generation
from string import ascii_letters, digits
from random import choices

from rest_framework.exceptions import ValidationError


# Create your models here.


class BaseModelMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


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


class User(BaseModelMixin, AbstractBaseUser):

    class Role(models.IntegerChoices):
        ADMIN = (0, 'Administrator')
        COURIER = (1, 'Courier')
        USER = (2, 'User')

    stripe_id = models.CharField(max_length=24, blank=True)
    name = models.CharField(max_length=120,blank=False)
    surname = models.CharField(max_length=120, blank=False)
    profile_pic = models.ImageField(null=True, blank=True, upload_to="profile_pic/")
    phone = models.CharField(max_length=20, blank=False, unique=True, validators=[phone_is_valid])
    email = models.EmailField(unique=True)
    birthdate = models.DateField(null=True, default=None)
    role = models.PositiveSmallIntegerField(choices=Role.choices, default=Role.USER)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"

    objects = UserManager()

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def generate_code(self, is_registration=True):  # TODO Send this to email
        verification_code, code_created = UserVerification.objects.get_or_create(
            user=self,
            is_registration=is_registration
        )
        if not code_created:
            verification_code.code = generate_code()
            verification_code.expires_at = datetime.datetime.now() + datetime.timedelta(minutes=5)
            verification_code.save()

        # TODO if is_registration send different messages

    def verify_code(self, verification_code) -> bool:
        verification_match = UserVerification.objects.filter(
            user=self,
            code=verification_code,
            expires_at__gte=datetime.datetime.now(),
            is_completed=False
        ).exists()

        return verification_match


class UserVerification(BaseModelMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification')
    code = models.CharField(max_length=16, default=generate_code())
    expires_at = models.DateTimeField(default=datetime.datetime.now() + datetime.timedelta(minutes=5))
    is_completed = models.BooleanField(default=False)
    is_registration = models.BooleanField(default=False)


class UserAddress(BaseModelMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='address')
    country = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    block = models.CharField(max_length=10)
    zipcode = models.CharField(max_length=16)


