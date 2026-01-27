from rest_framework import serializers

from assets.models import Asset


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ("id", "type", "file", "filename", "created_on")
        read_only_fields = ("id", "created_on")
