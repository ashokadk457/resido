from rest_framework import serializers


class LoginResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    accessToken = serializers.CharField(required=False, allow_null=True)
    refreshToken = serializers.CharField(required=False, allow_null=True)
    uid = serializers.IntegerField(required=False, allow_null=True)
    expiresIn = serializers.IntegerField(required=False, allow_null=True)
    scope = serializers.CharField(required=False, allow_null=True)

