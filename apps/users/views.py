from rest_framework import mixins, status
from rest_framework.parsers import MultiPartParser
from rest_framework.serializers import Serializer
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from django.shortcuts import get_object_or_404

from apps.users.models import User, UserVerification, UserAddress
from apps.users.serializers import UserSerializer, UserVerificationSerializer, UserEmailSerializer, \
    UserLoginResetSerializer, UserProfileSerializer, UserPasswordUpdateSerializer, UserAddressSerializer

from apps.common.permisions import IsAdminOrOwner, IsAdminOrItself, ReadOnly


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

        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        raw_password = validated_data.pop('password')

        user, created = User.objects.get_or_create(**validated_data)

        user.set_password(raw_password)
        user.save()

        data = self.get_serializer(user).data
        return Response(data, status.HTTP_201_CREATED)

    @action(detail=False, methods=['POST'], url_path='send-verification', serializer_class=UserEmailSerializer)
    def send_verification(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        user = get_object_or_404(User, email=serializer.initial_data['email'])

        if user.is_active:
            return Response({'user': 'The user with this email is verified'}, status.HTTP_403_FORBIDDEN)

        user.generate_code(is_registration=True)
        return Response()

    @action(detail=False, methods=['POST'], serializer_class=UserVerificationSerializer)
    def confirm(self, request, *args, **kwargs):  # TODO Create stripe ID
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        verification_code = get_object_or_404(UserVerification, code=validated_data['code'], is_completed=False)
        user = verification_code.verify_user()

        return Response(UserSerializer(user).data)


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


class UserProfileViewSet(GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    """
    Used for authentication and managing existing accounts.
    """
    serializer_class = UserProfileSerializer
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated, IsAdminOrItself | ReadOnly,)
    parser_classes = (MultiPartParser, )

    @action(detail=False, methods=['GET'])
    def current(self, request, *args, **kwargs):
        return Response(UserSerializer(self.request.user).data)

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
    permission_classes = (IsAuthenticated, IsAdminOrOwner,)

    def get_queryset(self):
        if hasattr(self, 'swagger_fake_view'):
            return self.queryset.none()

        if self.action in ['list']:
            return self.queryset.filter(user=self.request.user)
        return self.queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
