from rest_framework import serializers

from common.models import HealthCareCustomer, Country, State, PetSpecies, PetBreed
from lookup.fields import BaseSerializer
from assets.serializers import AssetSerializer


class TenantSerializer(BaseSerializer):
    logo_details = AssetSerializer(source="asset.logo", read_only=True)
    favicon_details = AssetSerializer(source="asset.favicon", read_only=True)

    class Meta:
        model = HealthCareCustomer
        fields = (
            "url",
            "name",
            "logo_details",
            "website",
            "country",
            "favicon_details",
            "brand_color",
            "slogan",
            "description",
            "login_method",
            "language",
        )


class HealthCareCustomerSerializer(BaseSerializer):
    logo_details = AssetSerializer(source="asset.logo", read_only=True)
    favicon_details = AssetSerializer(source="asset.favicon", read_only=True)
    logo = serializers.CharField(source="asset.logo", read_only=True)
    favicon = serializers.CharField(source="asset.favicon", read_only=True)
    url = serializers.CharField(required=False, allow_blank=True)
    code = serializers.IntegerField(required=False, allow_null=True)
    email = serializers.CharField(required=True, allow_blank=False)
    work_phone = serializers.CharField(required=True, allow_blank=False)
    address = serializers.CharField(required=True, allow_blank=False)
    city = serializers.CharField(required=True, allow_blank=False)
    state = serializers.CharField(required=True, allow_blank=False)
    country = serializers.CharField(required=True, allow_blank=False)
    zipcode = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = HealthCareCustomer
        exclude = ("s2s_private_key", "s2s_public_key", "schema_name")

    def update(self, instance, validated_data):
        logo = self.initial_data.get("logo")
        favicon = self.initial_data.get("favicon")
        if logo or favicon:
            asset = instance.asset
            asset.logo_id = logo
            asset.favicon_id = favicon
            asset.save()
        return super().update(instance, validated_data)


class BulkUpdateListSerializer(serializers.ListSerializer):
    def update(self, instance, validated_data):
        instance_hash = {index: i for index, i in enumerate(instance)}
        result = [
            self.child.update(instance_hash[index], attrs)
            for index, attrs in enumerate(validated_data)
        ]
        writable_fields = [
            x
            for x in self.child.Meta.fields
            if x not in self.child.Meta.read_only_fields
        ]

        try:
            self.child.Meta.model.objects.bulk_update(result, writable_fields)
        except serializers.IntegrityError as e:
            raise serializers.ValidationError(e)

        return result


class StandardModelSerializer(serializers.ModelSerializer):
    def get_field_names(self, declared_fields, info):
        expanded_fields = super(StandardModelSerializer, self).get_field_names(
            declared_fields, info
        )
        if getattr(self.Meta, "extra_fields", None):
            return expanded_fields + self.Meta.extra_fields
        return expanded_fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We can make fields required based on context
        required_fields = self.context.get("required_fields", [])
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name", "code", "is_active"]


class StateSerializer(serializers.ModelSerializer):
    country = CountrySerializer()

    class Meta:
        model = State
        fields = ["id", "name", "country", "state_code", "is_active"]


class PetSpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PetSpecies
        fields = ["id", "name", "code", "is_active"]


class PetBreedSerializer(serializers.ModelSerializer):
    species = PetSpeciesSerializer(read_only=True)
    species_id = serializers.PrimaryKeyRelatedField(
        queryset=PetSpecies.objects.all(), source="species", write_only=True
    )

    class Meta:
        model = PetBreed
        fields = ["id", "name", "code", "species", "species_id", "is_active"]
