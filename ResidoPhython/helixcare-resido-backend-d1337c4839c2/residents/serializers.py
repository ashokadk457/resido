from datetime import datetime

from rest_framework import serializers
from assets.serializers import AssetSerializer
from assets.models import Asset
from common.errors import ERROR_DETAILS
from common.mixins import HelixSerializerMixin
from common.utils.general import replace_address_attrs
from helixauth.serializers import HelixUserSerializer
from residents.models import (
    Resident,
    ResidentAccessLog,
    ResidentDocument,
    ResidentRegisteredDevice,
    EmergencyContact,
    ResidentAddress,
    ResidentCoOccupants,
    ResidentFinancialGurantors,
    ResidentEviction,
)
from residents.constants import (
    ResidentEvictionStatusType,
    ResidentEvictionDeliveryMethodType,
)
from lookup.fields import BaseSerializer
from external.kc.core import KeyCloak
from notifications.apiviews import sendEmail, sendSMS
from residents.managers.patient import ResidentManager


class HolderAddressSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = super(HolderAddressSerializer, self).to_representation(instance)
        return replace_address_attrs(data, "second_", "holder_")

    def to_internal_value(self, data):
        data = replace_address_attrs(data, "holder_", "second_")
        return super(HolderAddressSerializer, self).to_internal_value(data)


class SubscriberAddressSerializer(serializers.Serializer):
    def to_representation(self, instance):
        data = super(SubscriberAddressSerializer, self).to_representation(instance)
        return replace_address_attrs(data, "second_", "subscriber_")

    def to_internal_value(self, data):
        data = replace_address_attrs(data, "subscriber_", "second_")
        return super(SubscriberAddressSerializer, self).to_internal_value(data)


class EmergencyContactSerializer(BaseSerializer):
    class Meta:
        model = EmergencyContact
        fields = "__all__"


class ResidentDocumentSerializer(BaseSerializer):
    resident = serializers.PrimaryKeyRelatedField(
        queryset=Resident.objects.all(), write_only=True, required=False
    )
    resident_first_name = serializers.CharField(
        source="resident.user.first_name", read_only=True
    )
    resident_id = serializers.CharField(source="resident.id", read_only=True)
    resident_last_name = serializers.CharField(
        source="resident.user.last_name", read_only=True
    )
    front_image_details = AssetSerializer(
        read_only=True, required=False, source="front_image"
    )
    back_image_details = AssetSerializer(
        read_only=True, required=False, source="back_image"
    )
    size = serializers.SerializerMethodField()

    class Meta:
        model = ResidentDocument
        fields = "__all__"

    def get_size(self, obj):
        total_size = 0

        if obj.front_image and hasattr(obj.front_image, "file"):
            total_size += obj.front_image.file.size
        if obj.back_image and hasattr(obj.back_image, "file"):
            total_size += obj.back_image.file.size

        if total_size == 0:
            return None  # or "0 KB", or skip the field entirely

        size_in_kb = round(total_size / 1024, 2)
        return f"{size_in_kb} KB"


class ResidentAddressSerializer(BaseSerializer):
    class Meta:
        model = ResidentAddress
        fields = "__all__"
        extra_kwargs = {
            "resident": {"required": False},
            "address": {"required": True},
            "city": {"required": True},
            "state": {"required": True},
            "zipcode": {"required": True},
            "country": {"required": True},
        }


class ResidentCoOccupantsSerializer(BaseSerializer):
    class Meta:
        model = ResidentCoOccupants
        fields = "__all__"
        extra_kwargs = {
            "resident": {"required": False},
            "relationship": {"required": True},
        }


class PublicResidentSerializer(BaseSerializer, HolderAddressSerializer):
    class Meta:
        model = Resident
        fields = ("id", "user")


class ResidentFamilySerializer(BaseSerializer):
    relationship = serializers.SerializerMethodField()
    family_id = serializers.SerializerMethodField()
    address = serializers.CharField(source="user.resident.address", read_only=True)
    address_1 = serializers.CharField(source="user.resident.address_1", read_only=True)
    city = serializers.CharField(source="user.resident.city", read_only=True)
    state = serializers.CharField(source="user.resident.state", read_only=True)
    zipcode = serializers.CharField(source="user.resident.zipcode", read_only=True)
    country = serializers.CharField(source="user.resident.country", read_only=True)

    class Meta:
        model = Resident
        fields = "__all__"
        read_only_fields = (
            "id",
            "address",
            "address_1",
            "city",
            "state",
            "zipcode",
            "country",
        )

    def get_relationship(self, obj):
        return self.context.get("relationship", None)

    def get_family_id(self, obj):
        return self.context.get("family_id", None)


class ResidentFinancialGurantorsSerializer(BaseSerializer):
    class Meta:
        model = ResidentFinancialGurantors
        fields = "__all__"
        extra_kwargs = {
            "resident": {"required": True},
        }


class ResidentSerializer(HelixSerializerMixin, BaseSerializer, HolderAddressSerializer):
    user = serializers.JSONField(required=False)
    documents = ResidentDocumentSerializer(
        source="residentdocument_set", required=False, many=True, allow_null=True
    )
    emergency_contacts = EmergencyContactSerializer(
        source="emergencycontact_set", required=False, many=True, allow_null=True
    )
    addresses = ResidentAddressSerializer(
        source="residentaddress_set", required=False, many=True, allow_null=True
    )
    co_occupants = ResidentCoOccupantsSerializer(
        source="residentcooccupants_set", required=False, many=True, allow_null=True
    )
    financial_guarantors = ResidentFinancialGurantorsSerializer(
        source="residentfinancialgurantors_set",
        required=False,
        many=True,
        allow_null=True,
    )
    family = ResidentFamilySerializer(
        read_only=True, required=False, many=True, allow_null=True
    )
    profile_image_details = AssetSerializer(source="profile_image", read_only=True)

    class Meta:
        model = Resident
        fields = "__all__"
        read_only_fields = ("id",)
        extra_kwargs = {"profile_type": {"required": True}, "user": {"required": False}}

    def to_representation(self, instance):
        resp = super().to_representation(instance)
        resp["user"] = HelixUserSerializer(instance.user).data
        return resp

    def validate_primary(self, object, instance, type):
        if (
            object.filter(resident=instance, active=True).count() > 0
            and object.filter(resident=instance, is_primary=True, active=True).count()
            != 1
        ):
            raise serializers.ValidationError(
                code="primary_count",
                detail=ERROR_DETAILS["primary_count"].format(type=type),
            )

    def update_emergency_contacts(self, instance, emergency_contacts):
        populated_emails = []
        for contact in emergency_contacts:
            contact.pop("id", None)
            contact.pop("created_by", None)
            contact.pop("updated_by", None)
            emergency, _ = EmergencyContact.objects.update_or_create(
                resident=instance, email=contact.get("email"), defaults=contact
            )
            populated_emails.append(contact.get("email"))
        # Whatever was not included in the contacts list should be marked inactive
        # Don't delete
        for contact in instance.emergencycontact_set.all():
            if contact.email not in populated_emails:
                contact.active = False
                contact.save()
        self.validate_primary(
            EmergencyContact.objects.all(), instance, "Emergency Contact"
        )

    def update_documents(self, instance, documents):
        populated_ids = []
        for identity in documents:
            ID = identity.pop("id", None)
            identity.pop("front_image_details", None)
            identity.pop("back_image_details", None)
            if ID and ResidentDocument.objects.filter(id=ID).first():
                ResidentDocument.objects.filter(id=ID).update(**identity)
                populated_ids.append(ID)
            else:
                identity["resident"] = instance.id
                identity_obj = ResidentDocumentSerializer(data=identity)
                identity_obj.is_valid(raise_exception=True)
                new_identity = identity_obj.save()
                populated_ids.append(str(new_identity.id))
        for identity in instance.residentdocument_set.all():
            if str(identity.id) not in populated_ids:
                identity.active = False
                identity.save()
        self.validate_primary(
            ResidentDocument.objects.all(), instance, "Resident Document"
        )

    def update_addresses(self, instance, addresses):
        populated_ids = []
        for address_data in addresses:
            address_id = address_data.pop("id", None)
            address_data.pop("created_by", None)
            address_data.pop("updated_by", None)
            address_data["resident"] = instance.id
            if address_id and ResidentAddress.objects.filter(id=address_id).first():
                ResidentAddress.objects.filter(id=address_id).update(**address_data)
                populated_ids.append(str(address_id))
            else:
                address_obj = ResidentAddressSerializer(data=address_data)
                address_obj.is_valid(raise_exception=True)
                new_address = address_obj.save()
                populated_ids.append(str(new_address.id))
        # Mark addresses not in the list as inactive (soft delete)
        for address in instance.residentaddress_set.all():
            if str(address.id) not in populated_ids:
                address.delete()

    def update_co_occupants(self, instance, co_occupants):
        populated_ids = []
        for occupant_data in co_occupants:
            occupant_id = occupant_data.pop("id", None)
            occupant_data.pop("created_by", None)
            occupant_data.pop("updated_by", None)
            occupant_data["resident"] = instance.id
            if (
                occupant_id
                and ResidentCoOccupants.objects.filter(id=occupant_id).first()
            ):
                ResidentCoOccupants.objects.filter(id=occupant_id).update(
                    **occupant_data
                )
                populated_ids.append(str(occupant_id))
            else:
                occupant_obj = ResidentCoOccupantsSerializer(data=occupant_data)
                occupant_obj.is_valid(raise_exception=True)
                new_occupant = occupant_obj.save()
                populated_ids.append(str(new_occupant.id))
        # Remove occupants not in the list
        for occupant in instance.residentcooccupants_set.all():
            if str(occupant.id) not in populated_ids:
                occupant.delete()

    def update_financial_guarantors(self, instance, guarantors):
        populated_ids = []
        for guarantor_data in guarantors:
            guarantor_id = guarantor_data.pop("id", None)
            guarantor_data.pop("created_by", None)
            guarantor_data.pop("updated_by", None)
            guarantor_data["resident"] = instance.id
            if (
                guarantor_id
                and ResidentFinancialGurantors.objects.filter(id=guarantor_id).first()
            ):
                ResidentFinancialGurantors.objects.filter(id=guarantor_id).update(
                    **guarantor_data
                )
                populated_ids.append(str(guarantor_id))
            else:
                guarantor_obj = ResidentFinancialGurantorsSerializer(
                    data=guarantor_data
                )
                guarantor_obj.is_valid(raise_exception=True)
                new_guarantor = guarantor_obj.save()
                populated_ids.append(str(new_guarantor.id))
        # Remove guarantors not in the list
        for guarantor in instance.residentfinancialgurantors_set.all():
            if str(guarantor.id) not in populated_ids:
                guarantor.delete()

    def create(self, validated_data):
        user_obj = None
        is_user_created = False
        try:
            emergency = []
            documents = []
            addresses = []
            co_occupants = []
            financial_guarantors = []

            user_data = validated_data.pop("user", None)
            if not user_data:
                raise serializers.ValidationError(
                    code="missing_required_param",
                    detail=ERROR_DETAILS["missing_required_param"].format(param="user"),
                )
            user_srz = HelixUserSerializer(data=user_data, context=self.context)
            user_srz.is_valid(raise_exception=True)
            user = user_srz.save()
            user_obj = user
            is_user_created = True

            # Extract nested objects
            if "emergencycontact_set" in validated_data:
                emergency = validated_data.pop("emergencycontact_set")
            if "residentdocument_set" in validated_data:
                documents = self.initial_data.get("documents", [])
                validated_data.pop("residentdocument_set")
            if "residentaddress_set" in validated_data:
                addresses = self.initial_data.get("addresses", [])
                validated_data.pop("residentaddress_set")
            if "residentcooccupants_set" in validated_data:
                co_occupants = self.initial_data.get("co_occupants", [])
                validated_data.pop("residentcooccupants_set")
            if "residentfinancialgurantors_set" in validated_data:
                financial_guarantors = self.initial_data.get("financial_guarantors", [])
                validated_data.pop("residentfinancialgurantors_set")

            # Create resident
            patient = Resident.objects.create(user=user, **validated_data)

            # Update nested objects
            if emergency:
                self.update_emergency_contacts(patient, emergency)
            if documents:
                self.update_documents(patient, documents)
            if addresses:
                self.update_addresses(patient, addresses)
            if co_occupants:
                self.update_co_occupants(patient, co_occupants)
            if financial_guarantors:
                self.update_financial_guarantors(patient, financial_guarantors)

            ResidentManager.send_email(patient)
            return patient
        except Exception as e:
            # rollback creation on keycloak
            if is_user_created and user_obj and user_obj.auth_user_id:
                kc = KeyCloak.init()
                kc.delete_user(user_obj.auth_user_id)
            raise e

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", None)
        if user_data:
            user_srz = HelixUserSerializer(
                instance=instance.user, data=user_data, context=self.context
            )
            user_srz.is_valid(raise_exception=True)
            user_srz.save()
        data = self.initial_data

        # Handle emergency contacts
        if "emergency_contacts" in data:
            emergency = data.get("emergency_contacts", [])
            self.update_emergency_contacts(instance, emergency)
            validated_data.pop("emergencycontact_set", None)

        # Handle documents
        if "documents" in data:
            documents = data.get("documents", [])
            self.update_documents(instance, documents)
            validated_data.pop("residentdocument_set", None)

        # Handle addresses
        if "addresses" in data:
            addresses = data.get("addresses", [])
            self.update_addresses(instance, addresses)
            validated_data.pop("residentaddress_set", None)

        # Handle co-occupants
        if "co_occupants" in data:
            co_occupants = data.get("co_occupants", [])
            self.update_co_occupants(instance, co_occupants)
            validated_data.pop("residentcooccupants_set", None)

        # Handle financial guarantors
        if "financial_guarantors" in data:
            financial_guarantors = data.get("financial_guarantors", [])
            self.update_financial_guarantors(instance, financial_guarantors)
            validated_data.pop("residentfinancialgurantors_set", None)

        return super().update(instance, validated_data)


class PatientRegisteredDeviceSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField()
    user = serializers.UUIDField()
    make = serializers.CharField()
    model = serializers.CharField()
    mac_address = serializers.CharField()
    os_detail = serializers.CharField()
    ip_address = serializers.ReadOnlyField(source="last_ip_address")
    location = serializers.ReadOnlyField(source="last_location")
    device_token = serializers.CharField(required=False)
    device_fingerprint = serializers.CharField(required=False)

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
        instance, created = ResidentRegisteredDevice.objects.get_or_create(
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


class PatientAccessLogSerializer(BaseSerializer):
    class Meta:
        model = ResidentAccessLog
        fields = ("id", "user", "ip_address", "location", "created_on", "updated_on")


class ResidentAddressSerializer(BaseSerializer):
    class Meta:
        model = ResidentAddress
        fields = "__all__"
        extra_kwargs = {
            "resident": {"required": True},
            "address": {"required": True},
            "city": {"required": True},
            "state": {"required": True},
            "zipcode": {"required": True},
            "country": {"required": True},
        }


class ResidentCoOccupantsSerializer(BaseSerializer):
    class Meta:
        model = ResidentCoOccupants
        fields = "__all__"
        extra_kwargs = {
            "resident": {"required": True},
            "relationship": {"required": True},
        }


class ResidentEvictionSerializer(BaseSerializer):
    resident_first_name = serializers.CharField(
        source="resident.user.first_name", read_only=True
    )
    resident_id = serializers.CharField(source="resident.id", read_only=True)
    resident_last_name = serializers.CharField(
        source="resident.user.last_name", read_only=True
    )
    resident_email = serializers.CharField(source="resident.user.email", read_only=True)
    attachment_id = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(),
        write_only=True,
        source="attachment",
        required=False,
        many=True,
    )
    attachment = AssetSerializer(many=True, read_only=True)

    class Meta:
        model = ResidentEviction
        fields = "__all__"
        extra_kwargs = {
            "resident": {"required": True},
            "select_reason": {"required": True},
            "notice_date": {"required": True},
            "vacate_by_date": {"required": True},
        }

    def validate(self, attrs):
        # Validation for "OTHER" reason
        if attrs.get("select_reason") == "OTHER" and not attrs.get("custom_reason"):
            raise serializers.ValidationError(
                {"custom_reason": "Custom reason is required when 'Other' is selected."}
            )

        # Validation for REJECTED status
        status = attrs.get("status")
        if status == ResidentEvictionStatusType.REJECTED.value:
            if not attrs.get("reject_reason"):
                raise serializers.ValidationError(
                    {
                        "reject_reason": ERROR_DETAILS["missing_required_param"].format(
                            param="reject_reason"
                        )
                    }
                )
            if not self.instance or (self.instance and not self.instance.reject_date):
                attrs["reject_date"] = datetime.now().date()

        return super().validate(attrs)

    def send_rent_notice_email(self, resident, eviction_instance):
        subject = "Eviction Notice"
        message = (
            f"Dear {resident.user.first_name}, your eviction notice has been sent."
        )
        recipient = resident.user.email
        if recipient:
            sendEmail(
                subject=subject,
                message=message,
                emails=[recipient],
                sender_id=None,
                rec_id=str(resident.user.id),
            )

    def send_rent_notice_sms(self, resident, eviction_instance):
        phone_number = getattr(resident.user, "phone_number", None)
        message = "Your eviction notice has been sent."
        if phone_number:
            sendSMS(
                to=phone_number,
                message=message,
                sender_id=None,
                rec_id=str(resident.user.id),
            )

    def create(self, validated_data):
        attachments = validated_data.pop("attachment", [])
        instance = super().create(validated_data)
        if attachments:
            instance.attachment.set(attachments)
        return instance

    def update(self, instance, validated_data):
        attachments = validated_data.pop("attachment", None)
        status = validated_data.get("status")
        instance = super().update(instance, validated_data)
        if attachments is not None:
            instance.attachment.set(attachments)
        if status == ResidentEvictionStatusType.SENT.value:
            resident = instance.resident
            communication_modes = (
                getattr(resident, "rent_notices_communication", []) or []
            )
            if not communication_modes:
                raise serializers.ValidationError(
                    {"communication_modes": "Communication modes are not defined"}
                )
            if (
                ResidentEvictionDeliveryMethodType.EMAIL_NOTIFICATION.value
                in communication_modes
            ):
                self.send_rent_notice_email(resident, instance)

            if ResidentEvictionDeliveryMethodType.SMS.value in communication_modes:
                self.send_rent_notice_sms(resident, instance)

        return instance


class RenterProfileSerializer(BaseSerializer):
    user = serializers.SerializerMethodField()
    emergency_contacts = EmergencyContactSerializer(
        source="emergencycontact_set", many=True, read_only=True
    )
    identity_documents = ResidentDocumentSerializer(
        source="residentdocument_set", many=True, read_only=True
    )
    addresses = ResidentAddressSerializer(
        source="residentaddress_set", many=True, read_only=True
    )
    co_occupants = ResidentCoOccupantsSerializer(
        source="residentcooccupants_set", many=True, read_only=True
    )
    financial_guarantors = ResidentFinancialGurantorsSerializer(
        source="residentfinancialgurantors_set", many=True, read_only=True
    )
    profile_image_details = AssetSerializer(source="profile_image", read_only=True)

    class Meta:
        model = Resident
        fields = [
            "id",
            "resident_id",
            "user",
            "profile_type",
            "ssn",
            "profile_image_details",
            "emergency_contacts",
            "identity_documents",
            "addresses",
            "co_occupants",
            "financial_guarantors",
            "communication_mode",
            "emergency_alerts_communication",
            "maintenance_communication",
            "rent_notices_communication",
            "last_login",
            "created_on",
            "updated_on",
        ]
        read_only_fields = ("id", "resident_id")

    def get_user(self, obj):
        from helixauth.serializers import HelixUserSerializer

        return HelixUserSerializer(obj.user).data
