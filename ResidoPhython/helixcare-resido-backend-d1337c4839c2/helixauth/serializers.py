from django.contrib.auth.models import update_last_login
from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenRefreshSerializer,
    TokenObtainPairSerializer,
)
from helixauth.utils import generate_pdf_from_html
from io import BytesIO
from assets.models import Asset
from assets.serializers import AssetSerializer
from common.errors import ERROR_DETAILS
from common.utils.general import replace_address_attrs
from common.utils.access_devices import update_device_access
from common.validators import (
    validate_phone_number,
    validate_country_code,
    normalize_empty_to_none,
    validate_not_whitespace,
    check_unique_field,
)
from notifications.apiviews import sendEmail
from helixauth.utils import random_password
from helixauth.managers.admin import AdminManager
from helixauth.managers.user.generic import HelixUserManager
from helixauth.models import (
    SecurityQuestion,
    HelixUser,
    Module,
    ModuleComposition,
    ModulePermission,
    SubModulePermission,
    EntityAttributePermission,
    EntityAttributeComposition,
    Entity,
    UserRole,
    RegisteredDevice,
    AccessLog,
    UserGroup,
    SubModuleComposition,
    Policy,
    PolicyVersion,
    UserPolicyAcceptance,
)
from helixauth.constants import AuthenticateType
from lookup.fields import BaseSerializer
from residents.models import Resident
from staff.models import HelixStaff
from common.serializers import StandardModelSerializer
from lookup.fields import LookupSerializerField
from helixauth.managers.access_log import AccessLogManager
from common.utils.logging import logger


class StrictCharField(serializers.CharField):
    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("invalid", value=data)
        return super().to_internal_value(data)


class StrictTextField(serializers.CharField):
    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("invalid", value=data)
        return super().to_internal_value(data)


class AuthenticateSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    type = serializers.ChoiceField(choices=AuthenticateType.choices())
    mobile = serializers.CharField(source="phone", max_length=15, required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(required=False)
    otp = serializers.CharField(max_length=6, required=False)
    refresh = serializers.CharField(required=False)
    question_id = serializers.UUIDField(required=False)
    answer = serializers.CharField(required=False)
    device_detail = serializers.JSONField(required=False, default=None)
    location_detail = serializers.JSONField(required=False, default={})

    from helixauth.managers.user.generic import HelixUserManager

    def validate_for_login_with_otp(self, attrs):
        if "mobile" not in attrs.keys() and "email" not in attrs.keys():
            raise serializers.ValidationError(
                detail=ERROR_DETAILS["req_param_missing"], code="req_param_missing"
            )
        manager = HelixUserManager()
        return manager.send_otp_to_user(
            attrs.get("email", None), attrs.get("mobile", None)
        )

    @staticmethod
    def validate_for_login_with_password(attrs):
        if ("email" not in attrs.keys() or "password" not in attrs.keys()) or (
            attrs["email"] is None or attrs["password"] is None
        ):
            raise serializers.ValidationError(
                detail=ERROR_DETAILS["req_param_missing"], code="req_param_missing"
            )

    @staticmethod
    def login_with_password(attrs):
        user_manager = HelixUserManager(
            username=attrs.get("username").lower() if attrs.get("username") else None,
            email=attrs.get("email").lower() if attrs.get("email") else None,
            password=attrs.get("password"),
        )
        return user_manager.validate_and_login_with_email(
            device_detail=attrs.get("device_detail"),
            location_detail=attrs.get("location_detail", {}),
        )

    @staticmethod
    def validate_for_otp(attrs):
        if ("mobile" not in attrs.keys() and "email" not in attrs.keys()) or attrs[
            "otp"
        ] is None:
            raise serializers.ValidationError(
                detail=ERROR_DETAILS["req_param_missing"], code="req_param_missing"
            )

    @staticmethod
    def login_with_otp(attrs):
        username = attrs.get("email") if attrs.get("email") else attrs.get("mobile")
        user_manager = HelixUserManager(
            username=username,
            email=attrs.get("email").lower(),
        )
        return user_manager.validate_otp_and_login(
            mobile=attrs.get("mobile", None),
            email=attrs.get("email", None),
            otp=attrs["otp"],
            device_detail=attrs.get("device_detail", None),
            location_detail=attrs.get("location_detail", {}),
        )

    def validate_for_refresh_token(self, attrs):
        if "refresh" not in attrs.keys():
            raise serializers.ValidationError(
                detail=ERROR_DETAILS["req_param_missing"], code="req_param_missing"
            )
        data = {
            "refresh": attrs["refresh"],
            "location_detail": attrs.get("location_detail", {}),
        }
        parent_serializer = CustomTokenRefreshSerializer(
            data=data, context=self.context
        )
        parent_serializer.is_valid(raise_exception=True)
        return parent_serializer.validated_data

    @staticmethod
    def validate_for_security_question(attrs):
        if (
            ("mobile" not in attrs.keys() and "email" not in attrs.keys())
            or "question_id" not in attrs.keys()
            or "answer" not in attrs.keys()
        ):
            raise serializers.ValidationError(
                detail=ERROR_DETAILS["req_param_missing"], code="req_param_missing"
            )

    @staticmethod
    def login_with_security_question(attrs):
        username = (
            attrs.get("email").lower() if attrs.get("email") else attrs.get("mobile")
        )
        user_manager = HelixUserManager(
            username=username,
            email=attrs.get("email").lower(),
        )

        return user_manager.validate_security_answer_and_login(
            attrs["question_id"],
            attrs["answer"],
            attrs["mobile"] if "mobile" in attrs else None,
            attrs["email"].lower() if "email" in attrs else None,
            attrs.get("device_detail", None),
            attrs.get("location_detail", {}),
        )

    @staticmethod
    def validate_for_activate_and_authenticate(attrs):
        if not attrs.get("email"):
            raise serializers.ValidationError(
                code="email_missing",
                detail=ERROR_DETAILS["email_missing"],
            )
        if not attrs.get("otp"):
            raise serializers.ValidationError(
                code="otp_missing",
                detail=ERROR_DETAILS["otp_missing"],
            )
        provider = AdminManager().validate_otp_and_activate_user(
            attrs.get("email").lower(), attrs.get("otp"), attrs
        )
        if not provider:
            raise serializers.ValidationError(
                code="invalid_otp",
                detail=ERROR_DETAILS["invalid_otp"],
            )
        username = (
            attrs.get("email").lower() if attrs.get("email") else attrs.get("mobile")
        )
        user_manager = HelixUserManager(
            username=username, email=attrs.get("email").lower()
        )
        token = user_manager.get_token_for_user_v2(
            associated_account=provider, associated_account_class_name="HelixStaff"
        )
        update_device_access(
            provider.user,
            token["refresh"],
            attrs.get("device_detail", None),
            attrs.get("location_detail", {}),
        )
        update_last_login(None, provider.user)
        from staff.serializers import TenantAdminSerializer

        return {
            "provider": TenantAdminSerializer(provider).data,
            "token": token,
        }

    def validate(self, attrs):
        # TODO this is anti pattern. the validate method is doing too many actions.
        # TODO it is validating as well as performing login. Violating Single Responsibility Principle
        # TODO need to refactor
        auth_type = attrs["type"]
        if auth_type == AuthenticateType.login_with_otp.value:
            return self.validate_for_login_with_otp(attrs)
        if auth_type == AuthenticateType.login_with_password.value:
            self.validate_for_login_with_password(attrs=attrs)
            return self.login_with_password(attrs=attrs)
        if auth_type == AuthenticateType.validate_otp.value:
            self.validate_for_otp(attrs=attrs)
            return self.login_with_otp(attrs=attrs)
        if auth_type == AuthenticateType.refresh_token.value:
            return self.validate_for_refresh_token(attrs)
        if auth_type == AuthenticateType.validate_security_question.value:
            self.validate_for_security_question(attrs)
            return self.login_with_security_question(attrs=attrs)
        if auth_type == AuthenticateType.activate_and_authenticate.value:
            return self.validate_for_activate_and_authenticate(attrs)


class UserSerializer(BaseSerializer):
    class Meta:
        model = HelixUser
        fields = ("username", "email")


class SecurityQuestionSerializer(BaseSerializer):
    class Meta:
        model = SecurityQuestion
        fields = ("name", "active")


class UserSerializerCreate(BaseSerializer):
    class Meta:
        model = HelixUser
        fields = ("username", "email", "password")


class HelixTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super(HelixTokenObtainPairSerializer, self).validate(attrs)
        match = None
        try:
            match = HelixStaff.objects.get(user=self.user)
        except HelixStaff.DoesNotExist:
            pass
        if match is None:
            try:
                match = Resident.objects.get(user=self.user)
            except Resident.DoesNotExist:
                pass
        if match is not None:
            data.update({"id": match.id})
            data.update({"user_id": match.user.id})
            data.update({"type": match.__class__.__name__})

        return data


class HelixUserWorkAddressSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = super(HelixUserWorkAddressSerializer, self).to_representation(instance)
        return replace_address_attrs(data, "second_", "work_")

    def to_internal_value(self, data):
        data = replace_address_attrs(data, "work_", "second_")
        return super(HelixUserWorkAddressSerializer, self).to_internal_value(data)


class HelixUserSerializer(
    BaseSerializer, HelixUserWorkAddressSerializer, StandardModelSerializer
):
    profile_img_details = AssetSerializer(read_only=True, source="profile_img")
    password = serializers.CharField(write_only=True, required=False)
    age = serializers.IntegerField(read_only=True, required=False)
    email = serializers.EmailField(
        max_length=255,
        required=True,
        allow_blank=False,
    )
    first_name = serializers.CharField(
        max_length=100,
        required=True,
        allow_blank=False,
    )
    last_name = serializers.CharField(
        max_length=100,
        required=True,
        allow_blank=False,
    )
    phone = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[validate_phone_number],
    )
    work_phone = serializers.CharField(
        max_length=25,
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[validate_phone_number],
    )
    home_phone = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[validate_phone_number],
    )
    fax = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[validate_phone_number],
    )
    country_code = serializers.CharField(
        max_length=10,
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[validate_country_code],
    )
    work_country_code = serializers.CharField(
        max_length=5,
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[validate_country_code],
    )
    home_country_code = serializers.CharField(
        max_length=5,
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[validate_country_code],
    )
    fax_country_code = serializers.CharField(
        max_length=5,
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[validate_country_code],
    )

    class Meta:
        model = HelixUser
        exclude = [
            "is_superuser",
            "version",
            "groups",
            "user_permissions",
        ]
        read_only_fields = [
            "last_login",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # During updates, remove unique validators from email and phone fields
        # to allow updating with the same values (since DRF's default unique
        # validators don't exclude the current instance during partial updates)
        if self.instance is not None:
            for field_name in ["email", "phone"]:
                if field_name in self.fields:
                    field = self.fields[field_name]
                    # Remove unique validators (they check if value exists without excluding current instance)
                    field.validators = [
                        v
                        for v in field.validators
                        if not (
                            hasattr(v, "__class__")
                            and v.__class__.__name__
                            in ["UniqueValidator", "UniqueTogetherValidator"]
                        )
                    ]

    def validate_phone(self, value):
        """
        Validate that the phone number is unique.
        During updates, allow the same phone if it belongs to the current user.
        Convert empty strings to None to avoid unique constraint issues.
        """
        value = normalize_empty_to_none(value)
        if value:
            check_unique_field(HelixUser, "phone", value, self.instance)
        return value

    def validate_work_phone(self, value):
        """Convert empty strings to None for work_phone field."""
        return normalize_empty_to_none(value)

    def validate_home_phone(self, value):
        """Convert empty strings to None for home_phone field."""
        return normalize_empty_to_none(value)

    def validate_fax(self, value):
        """Convert empty strings to None for fax field."""
        return normalize_empty_to_none(value)

    def validate_country_code(self, value):
        """Convert empty strings to None for country_code field."""
        return normalize_empty_to_none(value)

    def validate_work_country_code(self, value):
        """Convert empty strings to None for work_country_code field."""
        return normalize_empty_to_none(value)

    def validate_home_country_code(self, value):
        """Convert empty strings to None for home_country_code field."""
        return normalize_empty_to_none(value)

    def validate_fax_country_code(self, value):
        """Convert empty strings to None for fax_country_code field."""
        return normalize_empty_to_none(value)

    def validate_email(self, value):
        """
        Validate that the email is unique and not just whitespace.
        During updates, allow the same email if it belongs to the current user.
        """
        value = validate_not_whitespace(value, "email")
        value = value.lower()  # Normalize email to lowercase
        check_unique_field(
            HelixUser, "email", value, self.instance, case_insensitive=True
        )
        return value

    def validate_first_name(self, value):
        """Validate that first_name is not just whitespace."""
        return validate_not_whitespace(value, "first_name")

    def validate_last_name(self, value):
        """Validate that last_name is not just whitespace."""
        return validate_not_whitespace(value, "last_name")

    def create(self, validated_data):
        # password_created = False
        password = validated_data.pop("password", None)
        if not validated_data.get("username"):
            validated_data["username"] = validated_data.get("email")
        if not password:
            password = random_password()
            # password_created = True
        user = HelixUser.objects.create_user(password=password, **validated_data)
        # if password_created:
        #     self._send_email_for_temporary_password(user=user, password=password)
        return user

    def _send_email_for_temporary_password(self, user, password):
        if not self.context.get("request"):
            return
        request = self.context.get("request")
        sendEmail(
            subject=f"{request.tenant.name} Email Verification",
            message=f"Hi {user.first_name} {user.last_name}\n\nYour account has been created"
            f" in {request.tenant.name}. Please use the following credentials to login. \n\n"
            f"Email: {user.email}\n"
            f"Password: {password}\n",
            emails=[user.email],
            sender_id=None,
            rec_id=str(user.id),
        )


class HelixPartialUserSerializer(BaseSerializer, HelixUserWorkAddressSerializer):
    # Custom field to delay queryset evaluation - avoids AppRegistryNotReady error
    class LazyAssetField(serializers.PrimaryKeyRelatedField):
        def get_queryset(self):
            from assets.models import Asset

            return Asset.objects.all()

    profile_img_id = LazyAssetField(
        source="profile_img",
        write_only=True,
        required=False,
    )
    profile_img = AssetSerializer(read_only=True)

    class Meta:
        model = HelixUser
        fields = [
            "id",
            "is_active",
            "salutation",
            "first_name",
            "middle_name",
            "last_name",
            "gender",
            # "sexual_orientation",
            "languages_known",
            "profile_img",
            "profile_img_id",
            "status",
        ]


class HelixUserUpdateSerializer(BaseSerializer, HelixUserWorkAddressSerializer):
    profile_img_details = AssetSerializer(read_only=True)
    salutation = LookupSerializerField(lookup_name="PREFIX", required=True)
    gender = LookupSerializerField(lookup_name="GENDER_TYPE", required=True)
    date_of_birth = serializers.DateField(required=True)

    class Meta:
        model = HelixUser
        exclude = [
            "is_superuser",
            "staff",
            "version",
            "last_login",
            "email",
            "password",
        ]
        read_only_fields = exclude


class ModuleSerializer(BaseSerializer):
    class Meta:
        model = Module
        exclude = [
            "version",
        ]


class ModuleCompositionSerializer(BaseSerializer):
    entity_id = serializers.UUIDField(source="entity_obj_id", read_only=True)

    class Meta:
        model = ModuleComposition
        exclude = [
            "entity_obj",
            "version",
        ]


class EntitySerializer(BaseSerializer):
    class Meta:
        model = Entity
        exclude = [
            "app_name",
            "version",
        ]

    def to_representation(self, instance):
        role = self.context.get("role")
        data = super().to_representation(instance)
        data["attr_permissions"] = []
        attrs = instance.attributes.all()
        if role:
            for attr in attrs:
                for perm in attr.permissions.filter(role=role):
                    data["attr_permissions"].append(
                        EntityAttributePermissionSerializer(perm).data
                    )
        return data

    def update(self, instance, validated_data):
        attr_perms = self.initial_data.get("attr_permissions", [])
        role = self.context.get("role")
        if attr_perms and role:
            all_attr_ids = [s["id"] for s in attr_perms]
            attr_objs = EntityAttributePermission.objects.filter(
                id__in=all_attr_ids, role=role
            )
            attr_map = {str(o.id): o for o in attr_objs}
            for perm in attr_perms:
                if attr_map.get(str(perm["id"])):
                    permission = EntityAttributePermissionSerializer(
                        instance=attr_map.get(str(perm["id"])),
                        data=perm,
                        partial=True,
                    )
                    permission.is_valid(raise_exception=True)
                    permission.save()
        return super().update(instance, validated_data)


class SubmodulePermissionSerializer(BaseSerializer):
    module = serializers.CharField(source="submodule.module", read_only=True)
    submodule = serializers.CharField(source="submodule.submodule", read_only=True)

    class Meta:
        model = SubModulePermission
        exclude = [
            "version",
        ]
        read_only_fields = (
            "module",
            "submodule",
            "role",
        )


class SubmodulePermissionReadOnlySerializer(BaseSerializer):
    submodule = serializers.CharField(source="submodule.submodule", read_only=True)

    class Meta:
        model = SubModulePermission
        exclude = [
            "version",
            "role",
        ]


class EntityAttributeSerializer(BaseSerializer):
    class Meta:
        model = EntityAttributeComposition
        exclude = [
            "version",
        ]


class EntityAttributePermissionSerializer(BaseSerializer):
    attribute = serializers.CharField(source="attribute.attribute", read_only=True)
    display_name = serializers.CharField(
        source="attribute.display_name", read_only=True
    )

    class Meta:
        model = EntityAttributePermission
        exclude = [
            "version",
        ]
        read_only_fields = (
            "attribute",
            "display_name",
            "entity",
            "role",
        )


class ModulePermissionDetailSerializer(BaseSerializer):
    module_name = serializers.CharField(source="module.name", read_only=True)
    role_name = serializers.CharField(source="role.role_name", read_only=True)
    entities = ModuleCompositionSerializer(
        source="module.composition", many=True, read_only=True
    )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["submodule_permissions"] = []
        submodules = instance.module.submodules.all()
        for submod in submodules:
            for perm in submod.permissions.filter(role=instance.role):
                data["submodule_permissions"].append(
                    SubmodulePermissionSerializer(perm).data
                )
        return data

    class Meta:
        model = ModulePermission
        exclude = [
            "version",
        ]
        read_only_fields = (
            "module",
            "role",
            "submodule_permissions",
        )

    def update(self, instance, validated_data):
        submod_perms = self.initial_data.get("submodule_permissions", [])
        if submod_perms:
            all_submod_ids = [s["id"] for s in submod_perms]
            submod_objs = SubModulePermission.objects.filter(id__in=all_submod_ids)
            submod_map = {str(o.id): o for o in submod_objs}
            for perm in submod_perms:
                if submod_map.get(str(perm["id"])):
                    permission = SubmodulePermissionSerializer(
                        instance=submod_map.get(str(perm["id"])),
                        data=perm,
                        partial=True,
                    )
                    permission.is_valid(raise_exception=True)
                    permission.save()
        return super().update(instance, validated_data)


class ModulePermissionSerializer(BaseSerializer):
    module_name = serializers.CharField(source="module.name", read_only=True)

    class Meta:
        model = ModulePermission
        exclude = [
            "version",
        ]
        read_only_fields = (
            "module",
            "role",
        )


class ModulePermissionReadOnlySerializer(BaseSerializer):
    module_name = serializers.CharField(source="module.name", read_only=True)

    class Meta:
        model = ModulePermission
        exclude = [
            "role",
            "version",
        ]


class UserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroup
        exclude = [
            "version",
        ]
        read_only_fields = [
            "updated_on",
            "created_on",
        ]


class UserRoleCreateSerializer(serializers.ModelSerializer):
    # Custom field to delay queryset evaluation - avoids AppRegistryNotReady error
    class LazyUserRoleField(serializers.PrimaryKeyRelatedField):
        def get_queryset(self):
            return UserRole.objects.all()

    group = UserGroupSerializer(read_only=True)
    group_id = serializers.UUIDField(write_only=True, required=True)
    copy_from = LazyUserRoleField(required=False)

    class Meta:
        model = UserRole
        fields = "__all__"
        read_only_fields = (
            "seeded",
            "group",
        )


class UserRoleReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = "__all__"


class UserGroupExtendedSerializer(serializers.ModelSerializer):
    roles = UserRoleReadSerializer(many=True, source="c_roles", read_only=True)

    class Meta:
        model = UserGroup
        fields = "__all__"


class UserRoleDetailSerializer(serializers.ModelSerializer):
    permissions = ModulePermissionSerializer(required=False, many=True)
    group = UserGroupSerializer(read_only=True)
    group_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = UserRole
        exclude = [
            "version",
        ]
        read_only_fields = (
            "seeded",
            "group",
        )

    @staticmethod
    def validate_group_id(data):
        try:
            UserGroup.objects.get(id=data, is_active=True)
            return data
        except Exception:
            raise serializers.ValidationError(
                detail=ERROR_DETAILS["invalid_id"].format(param="group"),
                code="invalid_id",
            )

    def update(self, instance, validated_data):
        if "is_role_active" in validated_data and not validated_data["is_role_active"]:
            if HelixStaff.objects.filter(
                user_roles=instance, user__is_active=True
            ).exists():
                raise serializers.ValidationError(
                    detail=ERROR_DETAILS["cannot_deactivate_role"],
                    code="cannot_deactivate_role",
                )

        validated_data.pop("permissions", {})
        # validated_data.pop("attr_permissions", {})
        permissions_data = self.initial_data.pop("permissions", {})
        if permissions_data:
            perm_ids = [s["id"] for s in permissions_data]
            objs = instance.permissions.filter(id__in=perm_ids)
            perm_objs = {str(obj.id): obj for obj in objs}
            for permission_data in permissions_data:
                if perm_objs.get(str(permission_data["id"])):
                    permission = ModulePermissionSerializer(
                        instance=perm_objs.get(str(permission_data["id"])),
                        data=permission_data,
                        partial=self.partial,
                    )
                    permission.is_valid(raise_exception=True)
                    permission.save()
        return super(UserRoleDetailSerializer, self).update(instance, validated_data)

        # attr_permissions_data = self.initial_data.pop("attr_permissions", {})
        # if attr_permissions_data:
        #     attr_ids = [s["id"] for s in attr_permissions_data]
        #     attr_objs = {
        #         str(obj.id): obj
        #         for obj in instance.attr_permissions.filter(id__in=attr_ids)
        #     }
        #     for attr_perm in attr_permissions_data:
        #         if attr_objs.get(str(attr_perm["id"])):
        #             permission = EntityAttributePermissionSerializer(
        #                 instance=attr_objs.get(str(attr_perm["id"])),
        #                 data=attr_perm,
        #                 partial=self.partial,
        #             )
        #             permission.is_valid(raise_exception=True)
        #             permission.save()


class RegisteredDeviceSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField()
    user = serializers.UUIDField()
    make = serializers.CharField()
    model = serializers.CharField()
    mac_address = serializers.CharField()
    os_detail = serializers.CharField()
    ip_address = serializers.ReadOnlyField(source="last_ip_address")
    location = serializers.ReadOnlyField(source="last_location")
    device_token = serializers.CharField(required=False)
    device_fingerprint = serializers.CharField(
        required=False
    )  # Unique device fingerprint

    class Meta:
        fields = (
            "id",
            "user",
            "make",
            "model",
            "mac_address",
            "os_detail",
            "ip_address",
            "location",
            "device_token",
            "device_fingerprint",
        )
        read_only_fields = ("id", "ip_address", "location")

    @staticmethod
    def update_device_token(instance, device_token):
        instance.device_token = device_token
        instance.save()
        return instance

    def create(self, validated_data):
        user = validated_data.pop("user")
        validated_data["user_id"] = user
        device_token = validated_data.pop("device_token", None)
        device_fingerprint = validated_data.get("device_fingerprint")
        instance, created = RegisteredDevice.objects.get_or_create(
            user__id=user,
            make=validated_data.get("make"),
            model=validated_data.get("model"),
            mac_address=validated_data.get("mac_address"),
            defaults=validated_data,
        )
        # Update device_fingerprint if provided and record already existed
        if not created and device_fingerprint:
            instance.device_fingerprint = device_fingerprint
            instance.save()
        if device_token:
            instance = self.update_device_token(
                instance=instance, device_token=device_token
            )
        return instance


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    location_detail = serializers.JSONField(required=False)

    def _update_access_log_with_token(self, attrs):
        access_manager = AccessLogManager()
        access_manager.update_access_log_with_token(
            attrs["refresh"],
            (
                self.context.get("request")._request.META
                if self.context.get("request", None)
                else {}
            ),
            attrs.get("location_detail", {}),
        )

    def validate(self, attrs):
        user_manager = HelixUserManager()
        fresh_tokens = user_manager.refresh(refresh_token=attrs["refresh"])
        self._update_access_log_with_token(attrs=attrs)
        return fresh_tokens


class AccessLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessLog
        fields = (
            "id",
            "user",
            "ip_address",
            "location",
            "login_status",
            "created_on",
            "updated_on",
        )


class HelixUserReceipientSerialiser(HelixPartialUserSerializer):
    provider_type = serializers.CharField(
        source="helixuser_staff.provider_type", max_length=15, required=False
    )
    user_role = serializers.SerializerMethodField()
    email_address = serializers.EmailField(source="email", required=False)

    class Meta:
        model = HelixUser
        fields = [
            "id",
            "is_active",
            "salutation",
            "first_name",
            "middle_name",
            "last_name",
            "gender",
            "sexual_orientation",
            "languages_known",
            "profile_img",
            "profile_img_id",
            "status",
            "provider_type",
            "user_role",
            "email_address",
        ]

    def get_user_role(self, obj):
        return obj.user_roles.all().first().id if obj.user_roles.all().first() else None


class CareCenterRoleSerializer(serializers.Serializer):
    code = serializers.CharField()
    display_name = serializers.CharField()


class SubModuleCompositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubModuleComposition
        fields = "__all__"


class PolicyVersionListSerializer(serializers.ModelSerializer):
    policy_version = serializers.IntegerField(source="version_number", read_only=True)
    created_at = serializers.DateTimeField(source="created_on", read_only=True)
    template_pdf_url = AssetSerializer(read_only=True, required=False, allow_null=True)

    class Meta:
        model = PolicyVersion
        fields = [
            "id",
            "policy_version",
            "template_pdf_url",
            "created_at",
        ]
        read_only_fields = ["id", "policy_version", "created_at", "template_pdf_url"]


class PolicyListSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(source="created_on", read_only=True)
    updated_at = serializers.DateTimeField(source="updated_on", read_only=True)
    versions = PolicyVersionListSerializer(read_only=True, many=True)

    class Meta:
        model = Policy
        fields = [
            "id",
            "name",
            "policy_type",
            "status",
            "description",
            "publishing_date",
            "versions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "versions", "created_at", "updated_at"]


class PolicyVersionSerializer(serializers.ModelSerializer):
    policy_version = serializers.IntegerField(source="version_number", read_only=True)
    created_at = serializers.DateTimeField(source="created_on", read_only=True)
    content = serializers.CharField(
        source="content_html", required=False, allow_blank=True
    )
    template_pdf_url = AssetSerializer(read_only=True, required=False, allow_null=True)

    class Meta:
        model = PolicyVersion
        fields = [
            "id",
            "policy",
            "policy_version",
            "content",
            "template_pdf_url",
            "created_at",
        ]
        read_only_fields = ["id", "policy_version", "created_at", "template_pdf_url"]


class PolicyVersionDetailSerializer(serializers.ModelSerializer):
    policy_version = serializers.IntegerField(source="version_number", read_only=True)
    created_at = serializers.DateTimeField(source="created_on", read_only=True)
    content = serializers.CharField(
        source="content_html", required=False, allow_blank=True
    )
    template_pdf_url = AssetSerializer(read_only=True, required=False, allow_null=True)

    class Meta:
        model = PolicyVersion
        fields = [
            "id",
            "policy_version",
            "content",
            "template_pdf_url",
            "created_at",
        ]
        read_only_fields = ["id", "policy_version", "created_at", "template_pdf_url"]


class PolicyDetailSerializer(BaseSerializer):
    name = StrictCharField(max_length=255)
    description = StrictTextField(required=False, allow_blank=True)
    content = StrictTextField(required=False, allow_blank=True, write_only=True)
    created_at = serializers.DateTimeField(source="created_on", read_only=True)
    updated_at = serializers.DateTimeField(source="updated_on", read_only=True)
    versions = PolicyVersionSerializer(many=True, read_only=True)
    current_version_html = serializers.SerializerMethodField(read_only=True)
    latest_version_number = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Policy
        fields = [
            "id",
            "name",
            "policy_type",
            "status",
            "description",
            "publishing_date",
            "current_version",
            "current_version_html",
            "latest_version_number",
            "versions",
            "created_at",
            "updated_at",
            "content",
        ]
        read_only_fields = ["id", "versions", "created_at", "updated_at"]

    def get_current_version_html(self, obj):
        if obj.current_version:
            return obj.current_version.content_html
        latest = obj.versions.all().order_by("-version_number").first()
        if latest:
            return latest.content_html
        return None

    def get_latest_version_number(self, obj):
        latest = obj.versions.all().order_by("-version_number").first()
        if latest:
            return latest.version_number
        return None

    def validate(self, attrs):
        validated = super().validate(attrs)
        # Check for duplicate name at validation time
        if self.instance is None:  # Only check for create operations
            name = validated.get("name")
            if name and Policy.objects.filter(name=name).exists():
                raise serializers.ValidationError(
                    {"name": "A policy with this name already exists."}
                )
        return validated

    def update(self, instance, validated_data):
        content_html = self.initial_data.get("content_html", None)
        instance = super().update(instance, validated_data)
        if content_html:
            self._create_version(instance=instance, content=content_html)
        return instance

    @staticmethod
    def _create_version(instance, content):
        latest_version = instance.versions.all().order_by("-version_number").first()
        next_version_number = (
            (latest_version.version_number + 1) if latest_version else 1
        )

        new_version = PolicyVersion.objects.create(
            policy=instance,
            version_number=next_version_number,
            content_html=content,
        )

        # Generate PDF if policy is ACTIVE
        if instance.status == "ACTIVE" and content:
            try:
                # Generate PDF from HTML content
                pdf_bytes = generate_pdf_from_html(content)

                if pdf_bytes:
                    # Create Asset record for the PDF
                    pdf_file = BytesIO(pdf_bytes)
                    pdf_filename = (
                        f"{instance.name.replace(' ', '_')}_v{next_version_number}.pdf"
                    )

                    asset = Asset.objects.create(
                        type="doc",
                        filename=pdf_filename,
                    )
                    asset.file.save(pdf_filename, pdf_file, save=True)

                    # Link the Asset to PolicyVersion
                    new_version.template_pdf_url = asset
                    new_version.save()
            except Exception as e:
                # Log the error but don't fail the policy creation
                logger.error(f"Error generating PDF for policy {instance.id}: {str(e)}")

        instance.current_version = new_version
        instance.save()

    def create(self, validated_data):
        # Extract content before passing to parent since it's write_only and not a model field
        content_html = validated_data.pop("content", None) or self.initial_data.get(
            "content_html"
        )
        instance = super().create(validated_data)
        if content_html:
            self._create_version(instance=instance, content=content_html)
        return instance


class UserPolicyAcceptanceSerializer(serializers.ModelSerializer):
    # Custom field to delay queryset evaluation - avoids AppRegistryNotReady error
    class LazyPolicyVersionField(serializers.PrimaryKeyRelatedField):
        def get_queryset(self):
            from helixauth.models import PolicyVersion

            return PolicyVersion.objects.all()

    policy_version_id = LazyPolicyVersionField(
        source="policy_version",
        write_only=True,
        required=True,
    )
    policy_version = PolicyVersionDetailSerializer(read_only=True)

    class Meta:
        model = UserPolicyAcceptance
        fields = "__all__"
