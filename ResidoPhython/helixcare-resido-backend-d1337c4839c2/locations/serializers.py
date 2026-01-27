from decimal import Decimal

from django.contrib.gis.geos import GEOSGeometry
from django.db import connection
from django.db.models import Exists, OuterRef
from rest_framework import serializers

from assets.models import Asset
from assets.serializers import AssetSerializer
from common.models import PetSpecies, PetBreed
from common.serializers import PetSpeciesSerializer, PetBreedSerializer
from common.utils.general import get_location_latlng
from common.validators import validate_phone_number
from common.errors import ERROR_DETAILS
from locations.models import (
    Location,
    Property,
    Customer,
    Building,
    Floor,
    Unit,
    Amenity,
    ParkingLevel,
    ParkingZone,
    ParkingSlot,
    UnitAdministrationCharge,
)
from locations.constants import UnitStatus
from lease.models import Lease
from lease.constants import LeaseStatus
from lookup.fields import BaseSerializer
from residents.serializers import ResidentSerializer
from staff.models import HelixStaff
from helixauth.models import Policy


class LocationSerializer(BaseSerializer):
    image_id = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(), source="image", write_only=True, required=False
    )
    customer = serializers.CharField(
        source="property__customer", required=False, read_only=True
    )
    image = serializers.SerializerMethodField(read_only=True)
    total_units = serializers.SerializerMethodField()
    occupied_units = serializers.SerializerMethodField()
    total_buildings = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = "__all__"

    def get_total_units(self, obj):
        return Unit.objects.filter(floor__building__location=obj).count()

    def get_occupied_units(self, obj):
        return Unit.objects.filter(
            floor__building__location=obj, status=UnitStatus.OCCUPIED.value
        ).count()

    def get_total_buildings(self, obj):
        return Building.objects.filter(location=obj).count()

    def get_image(self, obj):
        if obj.image is not None:
            return AssetSerializer(obj.image).data
        try:
            if obj.property is not None and obj.property.image is not None:
                return AssetSerializer(obj.property.image).data
            if (
                connection.tenant.asset is not None
                and connection.tenant.asset.logo is not None
            ):
                return AssetSerializer(connection.tenant.asset.logo).data
        except Exception:
            pass
        return None


class LocationCreateUpdateSerializer(LocationSerializer):
    contact_first_name = serializers.CharField(required=True, allow_blank=False)
    contact_last_name = serializers.CharField(required=True, allow_blank=False)
    contact_email = serializers.CharField(required=True, allow_blank=False)
    phone = serializers.CharField(required=True, allow_blank=False)
    phone = serializers.CharField(required=True, allow_blank=False)
    address = serializers.CharField(required=True, allow_blank=False)
    city = serializers.CharField(required=True, allow_blank=False)
    state = serializers.CharField(required=True, allow_blank=False)
    country = serializers.CharField(required=True, allow_blank=False)
    zipcode = serializers.CharField(required=True, allow_blank=False)

    def create(self, validated_data):
        location_address = validated_data.get("address")
        if location_address:
            latlng = get_location_latlng(location_address)
            if latlng:
                latlng_p = GEOSGeometry(
                    "POINT(" + str(latlng[1]) + " " + str(latlng[0]) + ")", srid=4326
                )
                validated_data["latlng"] = latlng_p

        location = super(LocationCreateUpdateSerializer, self).create(validated_data)
        return location

    def update(self, instance, validated_data):
        location_address = validated_data.get("address")
        if location_address:
            latlng = get_location_latlng(location_address)
            if latlng:
                latlng_p = GEOSGeometry(
                    "POINT(" + str(latlng[1]) + " " + str(latlng[0]) + ")", srid=4326
                )
                validated_data["latlng"] = latlng_p
        return super().update(instance, validated_data)


class PropertySerializer(BaseSerializer):
    image_id = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(), source="image", write_only=True, required=False
    )
    image = AssetSerializer(read_only=True)
    locations_count = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = "__all__"

    def get_locations_count(self, obj):
        return Location.objects.filter(property=obj).count()


class PropertyTabStatusSerializer(serializers.Serializer):
    property_id = serializers.SerializerMethodField()
    property_name = serializers.SerializerMethodField()
    saved_location = serializers.SerializerMethodField()
    saved_building = serializers.SerializerMethodField()
    saved_floor = serializers.SerializerMethodField()
    saved_unit = serializers.SerializerMethodField()

    def get_property_id(self, obj):
        return str(obj.id)

    def get_property_name(self, obj):
        return obj.name

    def get_saved_location(self, obj):
        return Location.objects.filter(property=obj).exists()

    def get_saved_building(self, obj):
        return Building.objects.filter(location__property=obj).exists()

    def get_saved_floor(self, obj):
        return Floor.objects.filter(building__location__property=obj).exists()

    def get_saved_unit(self, obj):
        return Unit.objects.filter(floor__building__location__property=obj).exists()


class PropertyEntityCountSerializer(serializers.Serializer):
    property_id = serializers.SerializerMethodField()
    property_name = serializers.SerializerMethodField()
    locations_count = serializers.SerializerMethodField()
    buildings_count = serializers.SerializerMethodField()
    floors_count = serializers.SerializerMethodField()
    units_count = serializers.SerializerMethodField()

    def get_property_id(self, obj):
        return str(obj.id)

    def get_property_name(self, obj):
        return obj.name

    def get_locations_count(self, obj):
        return Location.objects.filter(property=obj).count()

    def get_buildings_count(self, obj):
        return Building.objects.filter(location__property=obj).count()

    def get_floors_count(self, obj):
        return Floor.objects.filter(building__location__property=obj).count()

    def get_units_count(self, obj):
        return Unit.objects.filter(floor__building__location__property=obj).count()


class LocationTrimmedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "name", "address"]


class PropertyCreateUpdateSerializer(PropertySerializer):
    contact_first_name = serializers.CharField(required=True, allow_blank=False)
    contact_last_name = serializers.CharField(required=True, allow_blank=False)
    email = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(
        required=True,
        allow_blank=False,
        validators=[validate_phone_number],
    )


class CustomLocationSerializer(BaseSerializer):
    property_id = serializers.CharField(source="property.id")
    property_name = serializers.CharField(source="property.name")

    class Meta:
        model = Location
        fields = (
            "id",
            "name",
            "short_name",
            "address",
            "address_1",
            "city",
            "state",
            "zipcode",
            "latlng",
            "property_id",
            "property_name",
        )


class CustomerSerializer(BaseSerializer):
    image_id = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(), source="image", write_only=True, required=False
    )
    staff_id = serializers.PrimaryKeyRelatedField(
        queryset=HelixStaff.objects.for_current_user(), write_only=True, required=False
    )
    image = AssetSerializer(read_only=True)
    logo_details = AssetSerializer(source="logo", read_only=True)
    favicon_details = AssetSerializer(source="favicon", read_only=True)
    total_properties = serializers.SerializerMethodField()
    occupied_properties = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        exclude = ("logo", "favicon")
        read_only_fields = ("id",)

    def get_total_properties(self, obj):
        return Property.objects.filter(customer=obj).count()

    def get_occupied_properties(self, obj):
        return (
            Property.objects.filter(customer=obj)
            .filter(
                Exists(
                    Unit.objects.filter(
                        floor__building__location__property=OuterRef("pk"),
                        status=UnitStatus.OCCUPIED.value,
                    )
                )
            )
            .count()
        )

    def create(self, validated_data):
        validated_data.pop("staff_id", None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("staff_id", None)
        # Handle logo_details and favicon_details from request
        logo_details = self.initial_data.get("logo_details")
        favicon_details = self.initial_data.get("favicon_details")

        # Extract UUID from logo_details (can be string or list)
        if logo_details:
            if isinstance(logo_details, list) and len(logo_details) > 0:
                validated_data["logo_id"] = logo_details[0]
            elif isinstance(logo_details, str):
                validated_data["logo_id"] = logo_details

        # Extract UUID from favicon_details (can be string or list)
        if favicon_details:
            if isinstance(favicon_details, list) and len(favicon_details) > 0:
                validated_data["favicon_id"] = favicon_details[0]
            elif isinstance(favicon_details, str):
                validated_data["favicon_id"] = favicon_details

        return super().update(instance, validated_data)


class FloorSerializer(BaseSerializer):
    class Meta:
        model = Floor
        fields = "__all__"


class FloorCreateUpdateSerializer(FloorSerializer):
    building = serializers.PrimaryKeyRelatedField(
        queryset=Building.objects.all(), required=True
    )

    class Meta:
        model = Floor
        fields = "__all__"

    def validate(self, attrs):
        """Validate that floor_number is unique within the building"""
        building = attrs.get("building")
        floor_number = attrs.get("floor_number")

        if building and floor_number:
            if self.instance:
                # For updates, exclude the current floor from the check
                existing_floor = (
                    Floor.objects.filter(building=building, floor_number=floor_number)
                    .exclude(id=self.instance.id)
                    .first()
                )
            else:
                # For creates, only check active floors (allow restoration of soft-deleted)
                existing_floor = Floor.objects.filter(
                    building=building,
                    floor_number=floor_number,
                    deleted_by__isnull=True,  # Ignore soft-deleted floors
                ).first()

            if existing_floor:
                raise serializers.ValidationError(
                    {"floor_number": [ERROR_DETAILS["duplicate_floor_number"]]}
                )

        return attrs

    def update(self, instance, validated_data):
        if instance.deleted_by is not None:
            instance.deleted_by = None

            if "floor_number" in validated_data:
                if str(validated_data["floor_number"]) == str(instance.floor_number):
                    del validated_data["floor_number"]
            if "building" in validated_data:
                if str(validated_data["building"].id) == str(instance.building_id):
                    del validated_data["building"]

        return super().update(instance, validated_data)


class BuildingSerializer(BaseSerializer):
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source="location",
        write_only=True,
        required=True,
    )
    location = serializers.SerializerMethodField(read_only=True)
    floor = FloorSerializer(many=True, read_only=True)
    total_units = serializers.SerializerMethodField()
    occupied_units = serializers.SerializerMethodField()
    vacant_units = serializers.SerializerMethodField()
    total_floors = serializers.SerializerMethodField()

    class Meta:
        model = Building
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize the UniqueTogetherValidator error message
        for validator in self.validators:
            if isinstance(validator, serializers.UniqueTogetherValidator):
                validator.message = (
                    "A building with this name already exists in this location."
                )

    def get_location(self, obj):
        if obj.location:
            return LocationTrimmedSerializer(obj.location).data
        return None

    def get_total_units(self, obj):
        return Unit.objects.filter(floor__building=obj).count()

    def get_occupied_units(self, obj):
        return Unit.objects.filter(
            floor__building=obj, status=UnitStatus.OCCUPIED.value
        ).count()

    def get_vacant_units(self, obj):
        return Unit.objects.filter(
            floor__building=obj, status=UnitStatus.VACANT.value
        ).count()

    def get_total_floors(self, obj):
        return Floor.objects.filter(building=obj).count()

    def create(self, validated_data):
        floors_data = self.initial_data.get("floor", [])
        building = super().create(validated_data)

        for floor_data in floors_data:
            if not floor_data.get("building"):
                floor_data["building"] = building.id
            serializer = FloorCreateUpdateSerializer(
                data=floor_data, context=self.context
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(building=building)

        return building

    def validate(self, attrs):
        """Override to allow soft-deleted building names to be reused"""
        location = attrs.get("location")
        name = attrs.get("name")

        if location and name:
            # Check if this is a new building or an update
            if self.instance:
                # For updates, exclude the current building from the check
                existing_building = (
                    Building.objects.filter(location=location, name=name)
                    .exclude(id=self.instance.id)
                    .first()
                )
            else:
                existing_building = Building.objects.filter(
                    location=location,
                    name=name,
                    deleted_by__isnull=True,  # Ignore soft-deleted buildings
                ).first()

            if existing_building:
                raise serializers.ValidationError(
                    {
                        "name": [
                            "A building with this name already exists in this location."
                        ]
                    }
                )

        return attrs

    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = request.user if request else None

        floors_data = self.initial_data.get("floor", None)
        instance = super().update(instance, validated_data)

        if floors_data is not None:
            # Validate no duplicate floor numbers in the request
            floor_numbers = [
                f.get("floor_number") for f in floors_data if f.get("floor_number")
            ]
            if len(floor_numbers) != len(set(floor_numbers)):
                duplicates = sorted(
                    set([num for num in floor_numbers if floor_numbers.count(num) > 1])
                )
                raise serializers.ValidationError(
                    {
                        "floor": [
                            f"Duplicate floor numbers found in request: {', '.join(map(str, duplicates))}. Each floor must have a unique number within a building."
                        ]
                    }
                )

            sent_ids = []

            for floor_data in floors_data:
                floor_id = floor_data.get("id")
                floor_number = floor_data.get("floor_number")

                # Validate building if provided
                if floor_data.get("building") and str(instance.id) != str(
                    floor_data.get("building")
                ):
                    raise serializers.ValidationError(
                        "Assigning floor to another building is not allowed"
                    )

                # Get or create floor (handles both active and soft-deleted)
                if floor_id:
                    # Update by ID
                    try:
                        floor_instance = Floor._base_manager.get(
                            id=floor_id, building=instance
                        )
                    except Floor.DoesNotExist:
                        raise serializers.ValidationError(
                            f"Floor with ID {floor_id} does not exist in this building"
                        )
                else:
                    # Get or create by floor_number (includes soft-deleted)
                    floor_instance, created = Floor._base_manager.get_or_create(
                        building=instance,
                        floor_number=floor_number,
                        defaults={
                            "description": floor_data.get("description"),
                            "is_active": floor_data.get("is_active", True),
                            "created_by": user,
                            "updated_by": user,
                        },
                    )

                # Update with new data
                serializer = FloorCreateUpdateSerializer(
                    floor_instance,
                    data=floor_data,
                    context=self.context,
                    partial=True,
                )
                serializer.is_valid(raise_exception=True)

                # Restore if soft-deleted, otherwise just save
                if floor_instance.deleted_by is not None:
                    serializer.save(deleted_by=None)
                else:
                    serializer.save()

                sent_ids.append(str(floor_instance.id))

            # Soft-delete floors not in the request
            instance.floor.exclude(id__in=sent_ids).update(deleted_by=user)

        return instance


class LocationDetailSerializer(LocationCreateUpdateSerializer):
    property_detail = PropertySerializer(read_only=True, source="property")
    building = BuildingSerializer(many=True, read_only=True)

    class Meta(LocationCreateUpdateSerializer.Meta):
        fields = "__all__"

    def create(self, validated_data):
        buildings_data = self.initial_data.get("building", [])
        location = super().create(validated_data)

        for building_data in buildings_data:
            serializer = BuildingSerializer(data=building_data, context=self.context)
            serializer.is_valid(raise_exception=True)
            serializer.save(location=location)

        return location

    def update(self, instance, validated_data):
        buildings_data = self.initial_data.get("building", None)
        request = self.context.get("request")
        user = request.user if request else None
        instance = super().update(instance, validated_data)

        if buildings_data is not None:
            # Validate no duplicate building names in the request
            building_names = [b.get("name") for b in buildings_data if b.get("name")]
            building_names_lower = [
                str(name).strip().lower() for name in building_names
            ]
            if len(building_names_lower) != len(set(building_names_lower)):
                duplicates = sorted(
                    set(
                        [
                            name
                            for name in building_names
                            if building_names_lower.count(str(name).strip().lower()) > 1
                        ]
                    )
                )
                raise serializers.ValidationError(
                    {
                        "building": [
                            f"Duplicate building names found in request: {', '.join(set(duplicates))}. Each building must have a unique name within a location."
                        ]
                    }
                )

            sent_ids = []

            for building_data in buildings_data:
                building_id = building_data.get("id")
                building_name = building_data.get("name")

                # Validate location_id if provided
                if building_data.get("location_id") and str(instance.id) != str(
                    building_data.get("location_id")
                ):
                    raise serializers.ValidationError(
                        "Assigning building to another location is not allowed"
                    )

                # Get or create building (handles both active and soft-deleted)
                if building_id:
                    # Update by ID
                    try:
                        building_instance = Building._base_manager.get(
                            id=building_id, location=instance
                        )
                    except Building.DoesNotExist:
                        raise serializers.ValidationError(
                            f"Building with ID {building_id} does not exist in this location"
                        )
                else:
                    # Get or create by name (includes soft-deleted)
                    building_instance, created = Building._base_manager.get_or_create(
                        location=instance,
                        name=building_name,
                        defaults={
                            "total_floors": building_data.get("total_floors", 0),
                            "year_built": building_data.get("year_built"),
                            "is_active": building_data.get("is_active", True),
                            "created_by": user,
                            "updated_by": user,
                        },
                    )

                # Update with new data
                serializer = BuildingSerializer(
                    building_instance,
                    data=building_data,
                    context=self.context,
                    partial=True,
                )
                serializer.is_valid(raise_exception=True)

                # Restore if soft-deleted, otherwise just save
                if building_instance.deleted_by is not None:
                    serializer.save(deleted_by=None)
                else:
                    serializer.save()

                sent_ids.append(str(building_instance.id))

            # Soft-delete buildings not in the request
            instance.building.exclude(id__in=sent_ids).update(deleted_by=user)

        return instance


class BuildingDetailSerializer(BuildingSerializer):
    location_detail = LocationDetailSerializer(read_only=True, source="location")


class FloorDetailSerializer(FloorSerializer):
    building_detail = BuildingDetailSerializer(read_only=True, source="building")


class UnitAdministrationChargeSerializer(BaseSerializer):
    class Meta:
        model = UnitAdministrationCharge
        fields = [
            "id",
            "charge_name",
            "charge_amount",
            "charge_amount_currency",
            "is_active",
        ]


class UnitAdministrationChargeWriteSerializer(BaseSerializer):
    class Meta:
        model = UnitAdministrationCharge
        fields = ["charge_name", "charge_amount", "charge_amount_currency", "is_active"]


class UnitSerializer(BaseSerializer):
    tenant = serializers.SerializerMethodField()
    property_manager = serializers.SerializerMethodField()
    image_ids = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(),
        write_only=True,
        source="images",
        required=False,
        many=True,
    )
    images = AssetSerializer(many=True, read_only=True)
    floor_detail = FloorDetailSerializer(read_only=True, source="floor")
    unit_number = serializers.CharField(required=True, allow_blank=False)
    unit_type = serializers.CharField(required=True, allow_blank=False)
    status = serializers.CharField(required=True, allow_blank=False)
    ownership = serializers.CharField(required=True, allow_blank=False)
    parking_slot_ids = serializers.PrimaryKeyRelatedField(
        queryset=ParkingSlot.objects.all(),
        write_only=True,
        source="parking_slots",
        required=False,
        many=True,
    )
    parking_zone_id = serializers.PrimaryKeyRelatedField(
        queryset=ParkingZone.objects.all(),
        write_only=True,
        source="parking_zone",
        required=False,
        allow_null=True,
    )
    parking_zone_detail = serializers.SerializerMethodField(read_only=True)
    violation_policy_ids = serializers.PrimaryKeyRelatedField(
        queryset=Policy.objects.all(),
        write_only=True,
        source="violation_policies",
        required=False,
        many=True,
    )
    violation_policies = serializers.SerializerMethodField(read_only=True)
    pet_policy_ids = serializers.PrimaryKeyRelatedField(
        queryset=Policy.objects.all(),
        write_only=True,
        source="pet_policies",
        required=False,
        many=True,
    )
    pet_policies = serializers.SerializerMethodField(read_only=True)
    administration_charges_write = UnitAdministrationChargeWriteSerializer(
        many=True,
        write_only=True,
        source="administration_charges",
        required=False,
    )
    administration_charges = UnitAdministrationChargeSerializer(
        many=True, read_only=True
    )
    pdf_asset = AssetSerializer(read_only=True)
    type_of_pet = PetSpeciesSerializer(source="pet_species", read_only=True)
    type_of_pet_id = serializers.PrimaryKeyRelatedField(
        queryset=PetSpecies.objects.all(),
        write_only=True,
        source="pet_species",
        required=False,
        allow_null=True,
    )
    breed = PetBreedSerializer(source="pet_breed", read_only=True)
    breed_id = serializers.PrimaryKeyRelatedField(
        queryset=PetBreed.objects.all(),
        write_only=True,
        source="pet_breed",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Unit
        fields = "__all__"

    def validate(self, attrs):
        if self.instance is None:
            if not attrs.get("floor_plan"):
                raise serializers.ValidationError(
                    {"floor_plan": ["This field is required."]}
                )
        elif "floor_plan" in attrs and not attrs.get("floor_plan"):
            raise serializers.ValidationError(
                {"floor_plan": ["This field is required."]}
            )

        # Only validate if pets are allowed
        if attrs.get("is_pet_allowed"):
            missing_fields = []
            # Accept either pet_type (lookup) or pet_species (FK)
            if not attrs.get("pet_type") and not attrs.get("pet_species"):
                missing_fields.append("type_of_pet_id")
            if not attrs.get("pet_fees_type"):
                missing_fields.append("pet_fees_type")

            if missing_fields:
                raise serializers.ValidationError(
                    {
                        field: ["This field is required when pets are allowed."]
                        for field in missing_fields
                    }
                )

        return attrs

    def create(self, validated_data):
        administration_charges_data = validated_data.pop("administration_charges", [])
        unit = super().create(validated_data)

        for charge_data in administration_charges_data:
            UnitAdministrationCharge.objects.create(unit=unit, **charge_data)

        return unit

    def update(self, instance, validated_data):
        administration_charges_data = validated_data.pop("administration_charges", None)
        unit = super().update(instance, validated_data)

        # Only update charges if provided
        if administration_charges_data is not None:
            # Delete existing charges and create new ones
            UnitAdministrationCharge.objects.filter(unit=unit).delete()
            for charge_data in administration_charges_data:
                UnitAdministrationCharge.objects.create(unit=unit, **charge_data)

        return unit

    def get_tenant(self, obj):
        active_lease = Lease.objects.filter(
            application__unit=obj, status=LeaseStatus.ACTIVE.value
        ).first()
        if not active_lease:
            return None
        tenant = active_lease.resident
        if not tenant:
            return None
        return ResidentSerializer(tenant).data

    def get_property_manager(self, obj):
        return None

    def get_parking_zone_detail(self, obj):
        if obj.parking_zone:
            return ParkingZoneSerializer(obj.parking_zone).data
        return None

    def get_violation_policies(self, obj):
        policies = obj.violation_policies.all()
        if policies:
            return [{"id": policy.id, "name": policy.name} for policy in policies]
        return []

    def get_pet_policies(self, obj):
        policies = obj.pet_policies.all()
        if policies:
            return [{"id": policy.id, "name": policy.name} for policy in policies]
        return []


class UnitDetailSerializer(UnitSerializer):
    floor_detail = FloorDetailSerializer(read_only=True, source="floor")


class AmenitySerializer(BaseSerializer):
    building_id = serializers.PrimaryKeyRelatedField(
        queryset=Building.objects.all(), write_only=True, source="building"
    )
    building = BuildingSerializer(read_only=True)
    image_ids = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(),
        write_only=True,
        source="images",
        required=False,
        many=True,
    )
    images = AssetSerializer(many=True, read_only=True)

    class Meta:
        model = Amenity
        fields = "__all__"


class AmenityDetailSerializer(AmenitySerializer):
    building = BuildingDetailSerializer(read_only=True)


class ParkingLevelSerializer(BaseSerializer):
    building_id = serializers.PrimaryKeyRelatedField(
        queryset=Building.objects.all(), write_only=True, source="building"
    )
    building = BuildingSerializer(read_only=True)
    property_name = serializers.CharField(
        source="building.location.property.name", read_only=True
    )
    location_name = serializers.CharField(
        source="building.location.name", read_only=True
    )
    total_zones = serializers.SerializerMethodField()
    level_type = serializers.CharField(
        required=True, allow_blank=False, allow_null=False
    )

    class Meta:
        model = ParkingLevel
        fields = "__all__"

    def validate_level_type(self, value):
        if not value:
            raise serializers.ValidationError("This field is required.")
        return value

    def get_total_zones(self, obj):
        return obj.total_zones


class ParkingZoneSerializer(BaseSerializer):
    parking_level_id = serializers.PrimaryKeyRelatedField(
        queryset=ParkingLevel.objects.all(), write_only=True, source="parking_level"
    )
    parking_level = ParkingLevelSerializer(read_only=True)
    total_slots = serializers.SerializerMethodField()

    class Meta:
        model = ParkingZone
        fields = "__all__"

    def get_total_slots(self, obj):
        return obj.total_slots


class ParkingSlotSerializer(serializers.ModelSerializer):
    zone_id = serializers.PrimaryKeyRelatedField(
        queryset=ParkingZone.objects.all(), write_only=True, source="zone"
    )
    zone = ParkingZoneSerializer(read_only=True)
    level_name = serializers.CharField(
        source="zone.parking_level.level_name", read_only=True
    )
    building_name = serializers.CharField(
        source="zone.parking_level.building.name", read_only=True
    )
    zone_name = serializers.CharField(source="zone.name", read_only=True)

    class Meta:
        model = ParkingSlot
        fields = "__all__"


class ParkingSlotBulkCreateSerializer(serializers.Serializer):
    zone_id = serializers.PrimaryKeyRelatedField(
        queryset=ParkingZone.objects.all(), write_only=True, source="zone"
    )
    slot_prefix = serializers.CharField()
    start_slot_no = serializers.IntegerField()
    end_slot_no = serializers.IntegerField()
    slot_type = serializers.CharField()
    availability = serializers.CharField()
    is_active = serializers.BooleanField(default=True)

    def validate(self, attrs):
        start = attrs["start_slot_no"]
        end = attrs["end_slot_no"]

        if start > end:
            raise serializers.ValidationError(
                code="slot_start_end_mismatch",
                detail=ERROR_DETAILS["slot_start_end_mismatch"].format(
                    param="start_slot_no"
                ),
            )

        return attrs

    def create(self, validated_data):
        zone = validated_data["zone"]
        prefix = validated_data["slot_prefix"]
        start = validated_data["start_slot_no"]
        end = validated_data["end_slot_no"]
        slot_type = validated_data["slot_type"]
        availability = validated_data["availability"]
        is_active = validated_data["is_active"]

        slots_to_create = []
        for num in range(start, end + 1):
            slot_no = f"{prefix}{num}"
            if ParkingSlot.objects.filter(zone=zone, slot_no=slot_no).exists():
                continue

            slots_to_create.append(
                ParkingSlot(
                    zone=zone,
                    slot_no=slot_no,
                    slot_type=slot_type,
                    availability=availability,
                    is_active=is_active,
                )
            )

        created_slots = ParkingSlot.objects.bulk_create(slots_to_create)
        return created_slots


class ParkingZoneBulkCreateSerializer(serializers.Serializer):
    parking_level_id = serializers.PrimaryKeyRelatedField(
        queryset=ParkingLevel.objects.all(), source="parking_level"
    )
    zones = serializers.ListField(
        child=serializers.CharField(max_length=100), allow_empty=False
    )

    def create(self, validated_data):
        level = validated_data["parking_level"]
        zone_names = validated_data["zones"]

        created_zones = []
        for name in zone_names:
            zone, created = ParkingZone.objects.get_or_create(
                parking_level=level, name=name
            )
            created_zones.append(zone)

        return created_zones


class PropertyTrimmedSerializer(BaseSerializer):
    class Meta:
        model = Property
        fields = ["id", "name", "address", "city", "state", "country", "zipcode"]


class LocationWithPropertySerializer(BaseSerializer):
    property = PropertyTrimmedSerializer(read_only=True)

    class Meta:
        model = Location
        fields = ["id", "name", "address", "city", "state", "country", "property"]


class BuildingTrimmedSerializer(BaseSerializer):
    location = LocationWithPropertySerializer(read_only=True)

    class Meta:
        model = Building
        fields = ["id", "name", "location"]


class FloorTrimmedSerializer(BaseSerializer):
    building = BuildingTrimmedSerializer(read_only=True)

    class Meta:
        model = Floor
        fields = ["id", "floor_number", "building"]


class MyUnitSerializer(BaseSerializer):
    floor = FloorTrimmedSerializer(read_only=True)
    lease_id = serializers.SerializerMethodField()
    lease_start_date = serializers.SerializerMethodField()
    lease_end_date = serializers.SerializerMethodField()
    lease_status = serializers.SerializerMethodField()

    class Meta:
        model = Unit
        fields = "__all__"

    def get_latest_lease(self, obj):
        """
        Return the most recent (latest) lease for this unit.
        """
        return obj.lease.order_by("-created_on").first()

    def get_lease_id(self, obj):
        lease = self.get_latest_lease(obj)
        return lease.id if lease else None

    def get_lease_start_date(self, obj):
        lease = self.get_latest_lease(obj)
        return lease.start_date if lease else None

    def get_lease_end_date(self, obj):
        lease = self.get_latest_lease(obj)
        return lease.end_date if lease else None

    def get_lease_status(self, obj):
        lease = self.get_latest_lease(obj)
        return lease.status if lease else None


class PolicySerializer(BaseSerializer):
    class Meta:
        model = Policy
        fields = "__all__"


class MyUnitDetailSerializer(BaseSerializer):
    from lease.serializers import (
        LeaseSerializerForResident,
        LeaseKeysSerializer,
        LeasePetsAllowedSerializer,
        LeaseOtherOccupantsSerializer,
        LeaseAdditionalSignersSerializer,
        LeaseUtilityServicesSerializer,
        PolicyVersionDetailSerializer,
    )

    pet_policy = PolicySerializer(read_only=True)
    violation_policy = PolicySerializer(read_only=True)
    floor = FloorDetailSerializer(read_only=True)
    landlord_details = CustomerSerializer(
        source="floor.building.location.property.customer", read_only=True
    )
    lease_details = LeaseSerializerForResident(source="latest_lease", read_only=True)
    pet_details = LeasePetsAllowedSerializer(
        source="latest_lease.pets_allowed", many=True, read_only=True
    )
    other_occupants = LeaseOtherOccupantsSerializer(
        source="latest_lease.other_occupants", many=True, read_only=True
    )
    additional_occupants = LeaseAdditionalSignersSerializer(
        source="latest_lease.additional_signers", many=True, read_only=True
    )
    utility_services = LeaseUtilityServicesSerializer(
        source="latest_lease.utility_services", many=True, read_only=True
    )
    lease_keys = LeaseKeysSerializer(
        source="latest_lease.keys", many=True, read_only=True
    )
    early_termination_policy = PolicyVersionDetailSerializer(
        source="latest_lease.early_termination_policy", read_only=True
    )
    additional_terms_policy = PolicyVersionDetailSerializer(
        source="latest_lease.additional_terms_policy", read_only=True
    )
    parking_policy = PolicyVersionDetailSerializer(
        source="latest_lease.parking_policy", read_only=True
    )

    total_monthly_rent = serializers.SerializerMethodField()
    total_deposit = serializers.SerializerMethodField()
    late_fee = serializers.SerializerMethodField()
    promotional_discount = serializers.SerializerMethodField()
    property_staff = serializers.SerializerMethodField()

    class Meta(MyUnitSerializer.Meta):
        model = Unit
        fields = "__all__"

    def get_latest_lease(self, obj):
        return obj.lease.order_by("-updated_on").first()

    def get_total_monthly_rent(self, obj):
        lease = self.get_latest_lease(obj)
        rent_amount = lease.rent_amount if lease and lease.rent_amount else 0
        pet_fees = obj.pet_fees_amount
        if hasattr(pet_fees, "amount"):
            pet_fees_value = pet_fees.amount or 0
        else:
            pet_fees_value = pet_fees or 0

        total = Decimal(rent_amount) + Decimal(pet_fees_value)
        return total

    def get_total_deposit(self, obj):
        lease = self.get_latest_lease(obj)
        security_amount = (
            lease.security_amount if lease and lease.security_amount else 0
        )
        pet_security_deposit_amount = obj.pet_security_deposit_amount
        if hasattr(pet_security_deposit_amount, "amount"):
            pet_security_deposit_amount = pet_security_deposit_amount.amount or 0
        else:
            pet_security_deposit_amount = pet_security_deposit_amount or 0
        total = Decimal(security_amount) + Decimal(pet_security_deposit_amount)
        return total

    def get_late_fee(self, obj):
        lease = self.get_latest_lease(obj)
        if not lease:
            return None
        latest_fee = lease.late_fees.order_by("-updated_on").first()
        return latest_fee.amount if latest_fee else None

    def get_promotional_discount(self, obj):
        lease = self.get_latest_lease(obj)
        if not lease:
            return None
        promotional_discount = lease.promotional_discount.order_by(
            "-updated_on"
        ).first()
        return promotional_discount.amount if promotional_discount else None

    def to_representation(self, instance):
        """Attach latest_lease dynamically before serialization"""
        instance.latest_lease = self.get_latest_lease(instance)
        return super().to_representation(instance)

    def get_property_staff(self, obj):
        from staff.serializers import StaffMinDetailSerializer

        property_obj = getattr(obj.floor.building.location, "property", None)
        if not property_obj:
            return None
        staff = (
            HelixStaff.objects.filter(properties=property_obj)
            .select_related("user")
            .prefetch_related("groups", "user_roles")
            .order_by("created_on")
            .first()
        )
        if not staff:
            return None

        return StaffMinDetailSerializer(staff).data
