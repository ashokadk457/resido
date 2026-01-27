import os

from rest_framework import serializers
from django.templatetags.static import static
from django.conf import settings

from .models import Lookup, CPTCategoryValue, CPTData, UIMetaData
from assets.models import Asset
from assets.serializers import AssetSerializer
from common.errors import ERROR_DETAILS
from customer_backend.managers.tenant import TenantManager


class LookupSerializer(serializers.ModelSerializer):
    image_id = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(), source="image", write_only=True, required=False
    )
    image = AssetSerializer(read_only=True)

    class Meta:
        model = Lookup
        fields = [
            "id",
            "name",
            "code",
            "value",
            "active",
            "display_name",
            "image",
            "image_id",
            "favorite",
        ]
        read_only_fields = ("id",)

    def validate(self, data):
        name = data["name"]
        if not Lookup.objects.filter(name=name).exists():
            raise serializers.ValidationError(
                detail=ERROR_DETAILS["invalid_name"], code="invalid_name"
            )
        if "display_name" not in data:
            data["display_name"] = data["value"]
        return data


class LookupUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lookup
        fields = [
            "id",
            "name",
            "code",
            "value",
            "active",
            "display_name",
            "image",
            "favorite",
        ]
        read_only_fields = ["id", "name", "code", "value"]


class CPTCategoryValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPTCategoryValue
        fields = ["cpt_cat_id", "description", "cpt_cat_type"]


class CPTDataSerializer(serializers.ModelSerializer):
    cpt_cat_val = CPTCategoryValueSerializer()

    class Meta:
        model = CPTData
        fields = [
            "id",
            "cpt_code",
            "description",
            "mod_indicator",
            "status",
            "cpt_cat_val",
        ]


class UIMetadataSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        if obj.name:
            tenant_domain = TenantManager().tenant_obj.domain
            safe_name = obj.name.replace(" ", "-")
            image_path = f"helixbeat/testimonials-media/{safe_name}.jpg"
            file_path = os.path.join(settings.STATIC_ROOT, image_path)
            if os.path.exists(file_path):
                return f"https://{tenant_domain}{static(image_path)}"

        return None

    class Meta:
        model = UIMetaData
        fields = "__all__"
