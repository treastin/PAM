from rest_framework import serializers


from apps.users.models import User, UserVerification, UserAddress


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'created_at',
            'updated_at',
            'first_name',
            'last_name',
            'profile_pic',
            'phone',
            'email',
            'password',
            'birthdate',
        ]

        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'created_at',
            'updated_at',
            'first_name',
            'last_name',
            'profile_pic',
            'phone',
            'email',
            'birthdate',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]


class UserPasswordUpdateSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=255, required=True)
    new_password = serializers.CharField(max_length=255, required=True)

    class Meta:
        fields = [
            'old_password',
            'new_password'
        ]


class UserCodeSendSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'email',
        ]


class UserLoginResetSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=255)

    class Meta:
        model = UserVerification
        fields = [
            'code',
            'password'
        ]


class UserVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserVerification
        fields = [
            'code',
            'user',
            'expires_at'
        ]

        read_only_fields = [
            'expires_at'
        ]

        extra_kwargs = {
            'code': {'write_only': True, 'required': False}
        }


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = '__all__'

        read_only_fields = [
            'created_at',
            'updated_at',
            'user'
        ]

