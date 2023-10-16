from rest_framework import mixins
from rest_framework.serializers import Serializer
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from django.shortcuts import get_object_or_404

from apps.users.models import User, UserVerification, UserAddress
from apps.users.serializers import UserSerializer, UserVerificationSerializer, UserCodeSendSerializer, \
    UserLoginResetSerializer, UserProfileSerializer, UserPasswordUpdateSerializer, UserAddressSerializer


# Create your views here.
class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == User.Role.ADMIN


class IsAdminOrItself(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (request.user.role == User.Role.ADMIN) | (obj.user == request.user)


class UserSignupViewSet(GenericViewSet, mixins.RetrieveModelMixin):
    """
    Used for creating and verifying new accounts.
    """
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = (AllowAny,)

    @action(detail=False, methods=['POST'])
    def new(self, request, *args, **kwargs):  # TODO Change name
        serializer = self.get_serializer(data=request.data)  # TODO get user if not verified
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        raw_password = validated_data.pop('password')

        user, created = User.objects.get_or_create(**validated_data)

        user.set_password(raw_password)
        user.save()

        data = self.get_serializer(user).data
        return Response(data)

    @action(detail=True, methods=['POST'], url_path='verification/create', serializer_class=Serializer)
    def generate_registration_code(self, request, pk, *args, **kwargs):
        user = get_object_or_404(User, id=pk, is_verified=False)
        user.generate_code(is_registration=True)
        return Response()

    @action(detail=False, methods=['POST'], serializer_class=UserVerificationSerializer)
    def verification(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        user = get_object_or_404(User, id=validated_data['user'].id, is_verified=False)

        verification_passed = user.verify_code(validated_data['code'])

        if verification_passed:
            user.is_verified = True
            user.save()
            user_data = UserSerializer(user).data
            return Response(user_data)
        else:
            raise ValidationError({'code': 'Verification code is not valid.'})


class UserLoginViewSet(GenericViewSet, mixins.RetrieveModelMixin):
    """
    Used for authentication and managing existing accounts.
    """
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = (AllowAny,)

    @action(detail=False, methods=['POST'], serializer_class=UserCodeSendSerializer)
    def send_code(self, request, *args, **kwargs):  # TODO better name.
        serializer = self.get_serializer(data=request.data)
        data = serializer.initial_data

        user = get_object_or_404(User, email=data['email'], is_verified=True)

        user.generate_code(is_registration=False)

        return Response()

    @action(detail=False, methods=['POST'], serializer_class=UserLoginResetSerializer)
    def reset(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.data

        verification_code = get_object_or_404(
            UserVerification, code=validated_data['code'], is_completed=False, is_registration=False)

        user = get_object_or_404(User, id=verification_code.user_id)

        user.set_password(validated_data['password'])
        verification_code.is_completed = True

        verification_code.save()
        user.save()

        return Response(UserSerializer(user).data)


class UserProfileViewSet(GenericViewSet, mixins.RetrieveModelMixin):
    """
    Used for authentication and managing existing accounts.
    """
    serializer_class = UserProfileSerializer
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=['GET'])
    def current(self, request, *args, **kwargs):
        return Response(UserSerializer(self.request.user).data)

    @action(detail=False, methods=['PATCH'])
    def partial(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
        # TODO Make so user can't edit other's users profile but an admin can.

    @action(detail=False, methods=['POST'], serializer_class=UserPasswordUpdateSerializer)
    def update_password(self, request, *args, **kwargs):
        user = self.request.user

        if user.check_password(request.data.get('old_password')):
            user.set_password(request.data.get('new_password'))
        else:
            raise ValidationError({'old_password': 'incorrect password'})  # TODO Change text

        return Response(UserSerializer(user).data)


class UserAddressViewSet(
    GenericViewSet,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin
):
    """
    Used for managing user addresses.
    """
    serializer_class = UserAddressSerializer
    queryset = UserAddress.objects.all()
    permission_classes = (IsAuthenticated, IsAdminOrItself,)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action in ['list']:
            return self.queryset.filter(user=self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
