"""Consolidated serializers for smartlock.app

Moved up from the `app/serializers/` package into a module at
`app/serializers.py` so `import app.serializers` resolves to this
single module implementation.
"""

from rest_framework import serializers
from .models import Key

class BaseSerializer(serializers.Serializer):
    """
    Base serializer that other serializers can inherit from.
    Provides common functionality and configuration.
    """
    pass


class LoginRequestSerializer(BaseSerializer):
    dialCode = serializers.CharField(required=False, allow_blank=True, default=None)
    contactOrEmail = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class LoginResponseSerializer(BaseSerializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    accessToken = serializers.CharField(required=False, allow_null=True)
    refreshToken = serializers.CharField(required=False, allow_null=True)
    uid = serializers.IntegerField(required=False, allow_null=True)
    expiresIn = serializers.IntegerField(required=False, allow_null=True)
    scope = serializers.CharField(required=False, allow_null=True)


class TTLockPayloadSerializer(BaseSerializer):
    client_id = serializers.CharField()
    client_secret = serializers.CharField()
    username = serializers.CharField()
    password = serializers.CharField()
    grant_type = serializers.CharField(default="password")
    dialCode = serializers.CharField(required=False, allow_blank=True, default=None)


__all__ = [
    "LoginRequestSerializer",
    "LoginResponseSerializer",
    "TTLockPayloadSerializer",
]
