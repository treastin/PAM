from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import UserManager
from django.db import models
from django.utils import timezone


# Create your models here.

class BaseModelMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(BaseModelMixin, AbstractBaseUser):

    class Role(models.IntegerChoices):
        ADMIN = (0, 'Administrator')
        COURIER = (1, 'Courier')
        USER = (2, 'User')

    stripe_id = models.CharField(max_length=24, blank=True)
    name = models.CharField(max_length=120,blank=False)
    surname = models.CharField(max_length=120, blank=False)
    profile_pic = models.ImageField(null=True, blank=True, upload_to="profile_pic/")
    phone = models.CharField(max_length=20, blank=False)
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


class UserVerification(BaseModelMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification')
    code = models.CharField(max_length=16)
    expires_at = models.DateTimeField()
    is_completed = models.BooleanField(default=False)
    is_registration = models.BooleanField()


class UserAddress(BaseModelMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='address')
    country = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    block = models.CharField(max_length=10)
    zipcode = models.CharField(max_length=16)
