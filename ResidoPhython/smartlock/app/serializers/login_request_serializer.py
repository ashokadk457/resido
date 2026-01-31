from rest_framework import serializers


class LoginRequestSerializer(serializers.Serializer):
    dialCode = serializers.CharField(
        required=False,
        allow_blank=True,
        default=None
    )
    contactOrEmail = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
