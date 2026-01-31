from rest_framework import serializers
from app.models.key_model import Key

class KeySerializer(serializers.ModelSerializer):
    class Meta:
        model = Key
        fields = '__all__'