import phonenumbers
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import UserManager
from django.db import models
from rest_framework.exceptions import ValidationError

from apps.common.models import BaseModel
# Create your models here.


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

    first_name = models.CharField(max_length=120, blank=False)
    last_name = models.CharField(max_length=120, blank=False)
    profile_pic = models.ImageField(null=True, blank=True, upload_to="user/profile_pic")
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

    def get_user_cart(self, create_if_none=False):
        if cart := self.carts.filter(is_archived=False).first():
            return cart

        if create_if_none:
            cart = self.carts.create(is_archived=False)
        else:
            raise ValidationError({'cart': 'Current user has no cart.'})

        return cart


class UserVerification(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification')
    code = models.CharField(max_length=16, null=False, blank=False)
    expires_at = models.DateTimeField()
    is_completed = models.BooleanField(default=False)
    is_registration = models.BooleanField(default=False)

    class Meta:

        ordering = ['-id']


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
