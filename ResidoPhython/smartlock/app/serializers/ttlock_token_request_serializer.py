from rest_framework import serializers

class TTLockTokenRequestSerializer(serializers.Serializer):
    clientId = serializers.CharField(max_length=128)
    clientSecret = serializers.CharField(max_length=128)
    username = serializers.CharField(max_length=64)
    password = serializers.CharField(max_length=128)
