from rest_framework import mixins
from rest_framework.parsers import MultiPartParser
from rest_framework.serializers import Serializer
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from django.shortcuts import get_object_or_404

from apps.users.models import User, UserVerification, UserAddress
from apps.users.serializers import UserSerializer, UserVerificationSerializer, UserCodeSendSerializer, \
    UserLoginResetSerializer, UserProfileSerializer, UserPasswordUpdateSerializer, UserAddressSerializer

from apps.common.permisions import IsAdminOrItself

# Create your views here.


class UserSignupViewSet(GenericViewSet):
    """
    Used for creating and verifying new accounts.
    """
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = (AllowAny,)

    @action(detail=False, methods=['POST'])
    def new(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        existing_user_same_cred = self.queryset.filter(
            email=serializer.initial_data['email'], phone=serializer.initial_data['phone'], is_active=False).first()
        if existing_user_same_cred:
            existing_user_same_cred.set_password(serializer.initial_data['password'])
            data = self.get_serializer(existing_user_same_cred).data
            return Response(data)

        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        raw_password = validated_data.pop('password')

        user, created = User.objects.get_or_create(**validated_data)

        user.set_password(raw_password)
        user.save()

        data = self.get_serializer(user).data
        return Response(data)

    @action(detail=True, methods=['POST'], url_path='verification-create', serializer_class=Serializer)
    def generate_registration_code(self, request, pk, *args, **kwargs):
        user = get_object_or_404(User, id=pk, is_active=False)
        user.generate_code(is_registration=True)
        return Response()

    @action(detail=False, methods=['POST'], serializer_class=UserVerificationSerializer)
    def verification(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        user = get_object_or_404(User, id=validated_data['user'].id, is_active=False)

        verification_passed = user.verify_code(validated_data['code'])

        if verification_passed:
            user.is_active = True
            user.save()
            user_data = UserSerializer(user).data
            return Response(user_data)
        else:
            raise ValidationError({'code': 'Verification code is not valid.'})


class UserLoginViewSet(GenericViewSet):
    """
    Used for authentication and managing existing accounts.
    """
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = (AllowAny,)

    @action(detail=False, methods=['POST'], serializer_class=UserCodeSendSerializer)
    def send_reset_code(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        data = serializer.initial_data

        user = get_object_or_404(User, email=data['email'], is_active=True)

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
    parser_classes = (MultiPartParser,)

    @action(detail=False, methods=['GET'])
    def current(self, request, *args, **kwargs):
        return Response(UserSerializer(self.request.user).data)

    @action(detail=False, methods=['PATCH'], url_path='partial_update')
    def partial(self, request, *args, **kwargs):
        user = self.request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @action(detail=False, methods=['POST'], serializer_class=UserPasswordUpdateSerializer)
    def update_password(self, request, *args, **kwargs):
        user = self.request.user

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
    permission_classes = (IsAuthenticated, IsAdminOrItself,)

    def get_queryset(self):
        if hasattr(self, 'swagger_fake_view'):
            return self.queryset.none()

        if self.action in ['list']:
            return self.queryset.filter(user=self.request.user)
        return self.queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
