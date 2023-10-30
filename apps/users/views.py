import datetime

from drf_util.decorators import serialize_decorator
from drf_util.utils import gt
from rest_framework import mixins, status
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from django.shortcuts import get_object_or_404

from apps.common.helpers import generate_code
from apps.users.models import User, UserVerification, UserAddress
from apps.users.serializers import UserSerializer, UserVerificationSerializer, UserEmailSerializer, \
    UserLoginResetSerializer, UserPasswordUpdateSerializer, UserAddressSerializer,\
    UserRegisterSerializer

from apps.common.permisions import IsAdminOrOwner, IsAdminOrItself, ReadOnly


# Create your views here.


class UserSignupViewSet(GenericViewSet):
    """
    Used for creating and verifying new accounts.
    """
    serializer_class = UserRegisterSerializer
    queryset = User.objects.all()
    permission_classes = (AllowAny,)

    @serialize_decorator(UserRegisterSerializer)
    @action(detail=False, methods=['POST'])
    def register(self, request, *args, **kwargs):
        raw_password = request.valid.pop('password')

        user, _ = User.objects.get_or_create(**request.valid)

        user.set_password(raw_password)
        user.save()

        data = self.get_serializer(user).data
        return Response(data, status.HTTP_201_CREATED)

    @action(detail=True, methods=['POST'], url_path='send-verification', serializer_class=Serializer)
    def send_verification(self, request, *args, **kwargs):
        user = self.get_object()

        if user.is_active:
            return Response({'user': 'The user with this email is verified'}, status.HTTP_403_FORBIDDEN)

        user.verification.create(
            user=user,
            is_registration=True,
            code=generate_code(),
            expires_at=datetime.datetime.now() + datetime.timedelta(minutes=5)
        )
        return Response()

    @action(detail=False, methods=['POST'], serializer_class=UserVerificationSerializer)
    def confirm(self, request, *args, **kwargs):  # TODO Create stripe ID
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        verification_code = get_object_or_404(
            UserVerification, code=validated_data['code'], is_completed=False, expires_at__gt=datetime.datetime.now())

        user = verification_code.user
        user.is_active = True
        user.save()

        verification_code.is_completed = True
        verification_code.save()

        return Response(self.get_serializer(user).data)


class UserLoginResetViewSet(GenericViewSet):
    """
    Used for authentication and managing existing accounts.
    """
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = (AllowAny,)

    @action(detail=False, methods=['POST'], serializer_class=UserEmailSerializer)
    def send_reset_code(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        user = get_object_or_404(User, email=validated_data['email'], is_active=True)

        user.verification.create(
            user=user,
            is_registration=False,
            code=generate_code(),
            expires_at=datetime.datetime.now() + datetime.timedelta(minutes=5)
        )
        return Response()

    @action(detail=False, methods=['POST'], serializer_class=UserLoginResetSerializer)
    def reset(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.data

        verification_code = get_object_or_404(
            UserVerification, code=validated_data['code'], is_completed=False, is_registration=False)

        user = verification_code.user

        user.set_password(validated_data['password'])
        verification_code.is_completed = True

        verification_code.save()
        user.save()

        return Response(UserSerializer(user).data)


class UserProfileViewSet(GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    """
    Used for authentication and managing existing accounts.
    """
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated, IsAdminOrItself | ReadOnly,)
    parser_classes = (MultiPartParser, )

    def get_queryset(self):
        qs = self.queryset

        if gt(self.request.user, 'role') == User.Role.USER:
            qs = self.queryset.filter(user=self.request.user)

        return qs

    @action(detail=False, methods=['POST'], serializer_class=UserPasswordUpdateSerializer)
    def update_password(self, request, *args, **kwargs):
        user = self.get_queryset().first()

        if user.check_password(request.data.get('old_password')):
            user.set_password(request.data.get('new_password'))
            user.save()
        else:
            raise ValidationError({'old_password': 'incorrect password'})

        return Response(UserSerializer(user).data)


class UserAddressViewSet(ModelViewSet):
    """
    Used for managing user addresses.
    """
    serializer_class = UserAddressSerializer
    queryset = UserAddress.objects.all()
    permission_classes = (IsAuthenticated, IsAdminOrOwner,)

    def get_queryset(self):
        qs = self.queryset

        if hasattr(self, 'swagger_fake_view'):
            qs = self.queryset.none()

        if self.action in ['list'] and gt(self.request.user,'role') == User.Role.USER:
            qs = self.queryset.filter(user=self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
