from rest_framework import serializers


class TTLockPayloadSerializer(serializers.Serializer):
    client_id = serializers.CharField()
    client_secret = serializers.CharField()
    username = serializers.CharField()
    password = serializers.CharField()
    grant_type = serializers.CharField(default="password")
    dialCode = serializers.CharField(required=False,
        allow_blank=True,
        default=None)
