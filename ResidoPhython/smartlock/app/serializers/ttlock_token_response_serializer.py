from rest_framework import serializers

class TTLockTokenResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField(max_length=256, required=False)
    refresh_token = serializers.CharField(max_length=256, required=False)
    uid = serializers.CharField(max_length=64, required=False)
    expires_in = serializers.IntegerField(required=False)
    error = serializers.CharField(max_length=256, required=False)
    status_code = serializers.IntegerField(required=False)
