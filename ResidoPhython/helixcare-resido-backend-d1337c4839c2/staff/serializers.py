from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from common.utils.general import is_resident_request
from assets.serializers import AssetSerializer
from common.errors import ERROR_DETAILS
from helixauth.models import HelixUser, UserRole
from helixauth.serializers import (
    HelixUserSerializer,
)
from helixauth.constants import AccessLevel
from locations.models import Location, Customer, Property, Building, Floor, Unit
from locations.serializers import (
    CustomLocationSerializer,
    CustomerSerializer,
    PropertySerializer,
    BuildingSerializer,
    FloorSerializer,
    UnitSerializer,
)
from lookup.fields import BaseSerializer
from staff.models import HelixStaff, StaffGroup
from .constants import HELIX_STAFF_FIELD_TO_ACCESS_LEVEL_MAP, StaffStatus


class StaffGroupSerializer(BaseSerializer):
    count = serializers.IntegerField(read_only=True)

    class Meta:
        model = StaffGroup
        fields = "__all__"


class StaffSerializer(BaseSerializer):
    user = HelixUserSerializer()
    customers = CustomerSerializer(read_only=True, many=True)
    customer_ids = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.for_current_user(),
        write_only=True,
        source="customers",
    )
    properties = PropertySerializer(read_only=True, many=True)
    property_ids = serializers.PrimaryKeyRelatedField(
        queryset=Property.objects.for_current_user(),
        write_only=True,
        source="properties",
    )
    locations = CustomLocationSerializer(read_only=True, many=True)
    location_ids = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.for_current_user(),
        write_only=True,
        source="locations",
    )
    buildings = BuildingSerializer(read_only=True, many=True)
    building_ids = serializers.PrimaryKeyRelatedField(
        queryset=Building.objects.for_current_user(),
        write_only=True,
        source="buildings",
    )
    floors = FloorSerializer(read_only=True, many=True)
    floor_ids = serializers.PrimaryKeyRelatedField(
        queryset=Floor.objects.for_current_user(), write_only=True, source="floors"
    )
    units = UnitSerializer(read_only=True, many=True)
    unit_ids = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.for_current_user(), write_only=True, source="units"
    )
    groups = StaffGroupSerializer(many=True, read_only=True)
    group_ids = serializers.PrimaryKeyRelatedField(
        queryset=StaffGroup.objects.all(), write_only=True, source="groups"
    )

    class Meta:
        model = HelixStaff
        fields = "__all__"
        read_only_fields = ("created_on", "id")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # When updating a staff member, ensure the nested user serializer
        # receives the related user instance for proper validation
        if self.instance is not None and not isinstance(self.instance, list):
            self.fields["user"].instance = self.instance.user

    def validate(self, attrs):
        user = attrs.get("user")
        # if user and user.access_level != AccessLevel.Admin.value:
        if user:
            access_level = user.get("access_level")
            if access_level and access_level != AccessLevel.Admin.value:
                model_field_name = HELIX_STAFF_FIELD_TO_ACCESS_LEVEL_MAP.get(
                    access_level
                )
                staff_instance = self.instance

                if not staff_instance:
                    model_field = attrs.get(model_field_name)
                else:
                    model_field = getattr(staff_instance, model_field_name, None)
                # model_field = getattr(self, model_field_name)
                if not model_field or model_field.all().count() == 0:
                    raise serializers.ValidationError(
                        code="access_level_fields_required",
                        detail=ERROR_DETAILS["access_level_fields_required"].format(
                            field=model_field_name, access_level=access_level
                        ),
                    )
        return super().validate(attrs)

    def set_appropriate_access(self, instance, data):
        for key, val in data.items():
            attr = getattr(instance, key)
            if val:
                attr.set(val)
            else:
                attr.clear()

    def get_access_data(self, validated_data):
        access_data = {
            "customers": validated_data.pop("customers", None),
            "properties": validated_data.pop("properties", None),
            "locations": validated_data.pop("locations", None),
            "buidlings": validated_data.pop("buidlings", None),
            "floors": validated_data.pop("floors", None),
            "units": validated_data.pop("units", None),
        }
        return access_data, all([True if x else False for x in access_data.values()])

    def create(self, validated_data):
        access_data, _ = self.get_access_data(validated_data=validated_data)
        instance = super().create(validated_data)
        self.set_appropriate_access(instance, access_data)
        return instance

    def update(self, instance, validated_data):
        # Email is immutable for staff - remove it from update payload if present
        user_data = validated_data.pop("user", {})
        if user_data:
            # Remove email from user_data to prevent updates (email is immutable)
            user_data.pop("email", None)
            user_instance = instance.user

            if "is_active" in user_data:
                if user_data["is_active"] is False:
                    # When user is disabled, set status to REJECTED
                    user_data["status"] = StaffStatus.REJECTED.value
                elif user_data["is_active"] is True:
                    # When user is enabled, set status to APPROVED
                    user_data["status"] = StaffStatus.APPROVED.value

            for attr, value in user_data.items():
                setattr(user_instance, attr, value)
            user_instance.save()
        groups = validated_data.pop("groups", [])
        if isinstance(groups, list):
            instance.groups.set(groups)
        user_roles = validated_data.pop("user_roles", [])
        if user_roles:
            instance.user_roles.set(user_roles)
        access_data, has_access_data = self.get_access_data(
            validated_data=validated_data
        )
        instance = super().update(instance, validated_data)
        if has_access_data:
            self.set_appropriate_access(instance, access_data)
        return instance


class StaffMinDetailSerializer(BaseSerializer):
    user = HelixUserSerializer(allow_null=True, required=False, read_only=True)
    email = serializers.CharField(source="user.email", required=False)
    salutation = serializers.CharField(source="user.salutation", required=False)
    first_name = serializers.CharField(source="user.first_name", required=False)
    middle_name = serializers.CharField(source="user.middle_name", required=False)
    last_name = serializers.CharField(source="user.last_name", required=False)
    gender = serializers.CharField(source="user.gender", required=False)
    work_country_code = serializers.CharField(
        source="user.country_code", required=False
    )
    work_phone = serializers.CharField(source="user.phone", required=False)
    profile_img_details = AssetSerializer(source="user.profile_img", read_only=True)

    class Meta:
        model = HelixStaff
        fields = (
            "id",
            "email",
            "user",
            "salutation",
            "name",
            "display_id",
            "employee_id",
            "first_name",
            "middle_name",
            "last_name",
            "gender",
            "work_country_code",
            "work_phone",
            "profile_img_details",
            "created_on",
        )
        read_only_fields = ("created_on",)


class StaffGroupDetailSerializer(BaseSerializer):
    staff = StaffMinDetailSerializer(many=True, read_only=True)
    staff_ids = serializers.ListField(child=serializers.UUIDField(), write_only=True)

    class Meta:
        model = StaffGroup
        fields = "__all__"

    def create(self, validated_data):
        staff_ids = validated_data.pop("staff_ids")
        objs = list(HelixStaff.objects.filter(id__in=staff_ids))
        instance = super().create(validated_data)
        instance.staff.set(objs)
        return instance

    def update(self, instance, validated_data):
        staff_ids = validated_data.pop("staff_ids", None)
        instance = super().update(instance, validated_data)
        if staff_ids:
            objs = list(HelixStaff.objects.filter(id__in=staff_ids))
            instance.staff.set(objs)
        return instance


class TenantAdminSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email")
    is_active = serializers.BooleanField(source="user.is_active", read_only=True)

    class Meta:
        model = HelixStaff
        fields = ["id", "email", "is_active"]


class SearchProviderSerializer(BaseSerializer):
    profile_img = AssetSerializer(read_only=True)
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    address = serializers.CharField(source="user.address")
    work_phone = serializers.CharField(source="user.work_phone")
    gender = serializers.CharField(source="user.gender", required=False)
    languages_known = serializers.ListField(source="user.languages_known")
    primary_location_name = serializers.CharField(
        source="primary_location.name", required=False
    )
    favorite = serializers.SerializerMethodField()

    class Meta:
        model = HelixStaff
        fields = (
            "id",
            "name",
            "display_id",
            "profile_img",
            "first_name",
            "last_name",
            "address",
            "work_phone",
            "gender",
            "languages_known",
            "qualification",
            "education",
            "hospital_affiliation",
            "memberships",
            "certifications",
            "awards",
            "practice_since",
            "rating",
            "ratings_count",
            "provider_initials",
            "accepts_new_patient",
            "provides_telehealth",
            "description",
            "specialities",
            "cost",
            "pcp",
            "primary_location",
            "primary_location_name",
            "created_on",
            "favorite",
        )
        read_only_fields = ("created_on",)

    def get_favorite(self, obj):
        favorite_data = {"is_favorite": None, "favorite_id": None}
        if self.context.get("request") and is_resident_request(
            self.context.get("request")
        ):
            patient = self.context.get(
                "request"
            ).patient  # This is set in KC Auth class
            favorite = obj.patientfavoriteitem_set.filter(patient=patient).first()
            if favorite:
                favorite_data["is_favorite"] = favorite.favorite
                favorite_data["favorite_id"] = favorite.id

        return favorite_data


class InviteStaffSerializer(serializers.ModelSerializer):
    user_role = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=UserRole.objects.filter(is_role_active=True),
        ),
        required=True,
        allow_empty=False,
        write_only=True,
        error_messages={
            "not_a_list": ERROR_DETAILS["user_role_required"],
            "empty": ERROR_DETAILS["user_role_required"],
            "required": ERROR_DETAILS["user_role_required"],
        },
    )
    user = HelixUserSerializer(required=True)

    class Meta:
        model = HelixStaff
        fields = "__all__"
        read_only_fields = ("created_on",)

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        user = HelixUser.objects.filter(
            email__iexact=user_data.get("email"),
        ).first()
        if user:
            if user.status == StaffStatus.APPROVED.value:
                raise ValidationError(
                    code="user_already_verified",
                    detail=ERROR_DETAILS["user_already_verified"],
                )
        else:
            user_data["is_staff"] = True
            # Use the nested serializer's create method directly with already-validated data
            user_serializer = self.fields["user"]
            user = user_serializer.create(user_data)
        user_roles = validated_data.pop("user_role")
        staff, _ = HelixStaff.objects.get_or_create(
            user=user, defaults={"user": user, **validated_data}
        )
        staff.user_roles.set(user_roles)
        return staff
