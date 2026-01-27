from datetime import datetime
from django.db import IntegrityError
from rest_framework import serializers
from common.models import PetSpecies, PetBreed
from common.serializers import BaseSerializer, PetSpeciesSerializer, PetBreedSerializer
from common.validators import AgeValidationMixin
from lease.utils.corenter import create_corenter_accounts

from lease.models import (
    Application,
    Lease,
    LeaseOtherOccupants,
    LeaseLateFees,
    LeaseAdditionalSigners,
    LeasePetsAllowed,
    LeaseUtilityServices,
    LeaseKeys,
    LeasePromotionalDiscount,
    LeaseOneTimeFees,
    MoveRequest,
    MoveInspectionLog,
    ApplicationOtherOccupants,
    ApplicationPetsAllowed,
    ApplicationUtilityServices,
    ApplicationAdditionalLeaseHolders,
)
from lease.constants import MoveInspectionStatus
from assets.models import Asset
from assets.serializers import AssetSerializer
from locations.models import Unit, Location
from locations.serializers import UnitDetailSerializer
from lease.constants import LeaseApplicationStatus
from lease.managers.application import ApplicationManager
from common.errors import ERROR_DETAILS
from helixauth.models import PolicyVersion
from helixauth.serializers import PolicyVersionDetailSerializer
from residents.serializers import (
    ResidentSerializer,
    ResidentDocumentSerializer,
    EmergencyContactSerializer,
    ResidentAddressSerializer,
    ResidentFinancialGurantorsSerializer,
)
from residents.models import (
    Resident,
    ResidentDocument,
    EmergencyContact,
    ResidentAddress,
    ResidentFinancialGurantors,
)
from residents.managers.patient import ResidentManager
from helixauth.serializers import HelixUserSerializer
from helixauth.models import HelixUser
from residents.constants import ResidentProfileType
from hb_core.utils.logging import logger


class ApplicationSerializerForStaff(BaseSerializer):
    # Existing resident_id field - now optional (used when resident already exists)
    resident_id = serializers.PrimaryKeyRelatedField(
        queryset=Resident.objects.all(),
        write_only=True,
        source="resident",
        required=False,
        allow_null=True,
    )
    unit_id = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.all(), write_only=True, source="unit", required=True
    )

    # New renter details fields - used when creating application for new renter
    first_name = serializers.CharField(
        max_length=100, write_only=True, required=False, allow_blank=False
    )
    last_name = serializers.CharField(
        max_length=100, write_only=True, required=False, allow_blank=False
    )
    email = serializers.EmailField(
        max_length=255, write_only=True, required=False, allow_blank=False
    )
    phone = serializers.CharField(
        max_length=20,
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    country_code = serializers.CharField(
        max_length=10,
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    resident = ResidentSerializer(read_only=True)
    unit = UnitDetailSerializer(read_only=True)
    additional_occupants = serializers.SerializerMethodField()
    pet_details = serializers.SerializerMethodField()
    esa_type = serializers.SerializerMethodField()
    esa_perform = serializers.SerializerMethodField()
    esa_attachments = serializers.SerializerMethodField()
    application_additional_holders = serializers.SerializerMethodField()

    def _get_leases(self, obj):
        """
        Helper method to retrieve all leases related to this application.
        Avoids querying multiple times.
        """
        return obj.lease.all()

    def get_additional_occupants(self, obj):
        """
        Returns serialized data of all additional occupants across all leases.
        """
        leases = self._get_leases(obj)
        occupants_qs = LeaseOtherOccupants.objects.filter(lease__in=leases)
        return LeaseOtherOccupantsSerializer(occupants_qs, many=True).data

    def get_pet_details(self, obj):
        """
        Returns serialized data of all pets allowed across all leases.
        """
        leases = self._get_leases(obj)
        pets_qs = LeasePetsAllowed.objects.filter(lease__in=leases)
        return LeasePetsAllowedSerializer(pets_qs, many=True).data

    def get_esa_type(self, obj):
        """
        Returns ESA type from the first lease that has it.
        """
        leases = self._get_leases(obj)
        for lease in leases:
            if lease.esa_type:
                return lease.esa_type
        return None

    def get_esa_perform(self, obj):
        """
        Returns ESA perform description from the first lease that has it.
        """
        leases = self._get_leases(obj)
        for lease in leases:
            if lease.esa_perform:
                return lease.esa_perform
        return None

    def get_esa_attachments(self, obj):
        """
        Returns serialized data of all ESA attachments across all leases.
        """
        leases = self._get_leases(obj)
        attachments_qs = Asset.objects.filter(lease_esa_attachment__in=leases)
        return AssetSerializer(attachments_qs, many=True).data

    def get_application_additional_holders(self, obj):
        """
        Returns serialized data of all additional lease holders for this application.
        """
        holders = obj.application_additional_holders.all()
        return [{"id": str(h.id), "name": h.name, "email": h.email} for h in holders]

    def _create_corenter_accounts(self, additional_holders):
        """
        Create Resident accounts for co-renters/additional lease holders
        and send password setup emails to them.
        """
        create_corenter_accounts(additional_holders, context=self.context)

    def update(self, instance, validated_data):
        """
        Update application and handle additional lease holders.
        """
        # Handle application_additional_holders from initial_data (since it's a SerializerMethodField)
        additional_holders_data = self.initial_data.get(
            "application_additional_holders", []
        )

        # Update the application instance
        instance = super().update(instance, validated_data)

        # Process additional lease holders
        if additional_holders_data:
            logger.info(
                f"Processing {len(additional_holders_data)} additional holders for application {instance.id}"
            )
            holder_objs = []
            for holder_data in additional_holders_data:
                obj, _ = ApplicationAdditionalLeaseHolders.objects.update_or_create(
                    application=instance,
                    email=holder_data.get("email"),
                    defaults=holder_data,
                )
                holder_objs.append(obj)
            instance.application_additional_holders.set(holder_objs)

            # Create co-renter accounts and send password setup emails
            self._create_corenter_accounts(holder_objs)

        return instance

    def _create_new_resident(
        self, first_name, last_name, email, phone=None, country_code=None
    ):
        """
        Creates a new HelixUser and Resident for the new renter.
        Returns the created Resident instance.
        """
        # Check if user with this email already exists
        existing_user = HelixUser.objects.filter(email__iexact=email).first()
        if existing_user:
            # Check if resident exists for this user
            existing_resident = Resident.objects.filter(user=existing_user).first()
            if existing_resident:
                return existing_resident, False  # Return existing resident, not new
            raise serializers.ValidationError(
                code="email_exists",
                detail=ERROR_DETAILS.get(
                    "email_exists", "A user with this email already exists."
                ),
            )

        # Create HelixUser
        user_data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "country_code": country_code,
        }
        user_serializer = HelixUserSerializer(data=user_data, context=self.context)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        # Create Resident
        resident = Resident.objects.create(
            user=user,
            profile_type=ResidentProfileType.TENANT.value,
            resident_id=ResidentManager.generate_resident_id(first_name, last_name),
        )

        # Send password setup email
        ResidentManager.send_email(resident)

        return resident, True  # Return new resident, is_new=True

    def create(self, validated_data):
        # Extract new renter details if provided
        first_name = validated_data.pop("first_name", None)
        last_name = validated_data.pop("last_name", None)
        email = validated_data.pop("email", None)
        phone = validated_data.pop("phone", None)
        country_code = validated_data.pop("country_code", None)

        is_new_renter = False

        # If new renter details provided, create resident first
        if first_name and last_name and email:
            resident, is_new_renter = self._create_new_resident(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                country_code=country_code,
            )
            validated_data["resident"] = resident

        validated_data["sent_date"] = datetime.now().date()

        # If new renter, set pending_activation_email flag
        # Application email will be sent after password setup
        if is_new_renter:
            validated_data["pending_activation_email"] = True

        try:
            obj = super().create(validated_data)
        except IntegrityError as e:
            error_message = str(e)
            if (
                "lease_application_display_id_key" in error_message
                or "unique_application_per_resident_unit" in error_message
            ):
                raise serializers.ValidationError(
                    code="duplicate_application",
                    detail=ERROR_DETAILS["duplicate_application"],
                )
            raise

        # Only send application email immediately if existing renter (already active)
        if not is_new_renter:
            mngr = ApplicationManager(instance=obj)
            mngr.send_email()

        return obj

    def validate(self, attrs):
        if not self.instance:
            resident = attrs.get("resident")
            unit = attrs.get("unit")

            # Check if either resident_id OR new renter details are provided
            first_name = attrs.get("first_name")
            last_name = attrs.get("last_name")
            email = attrs.get("email")

            has_new_renter_details = first_name and last_name and email

            if not resident and not has_new_renter_details:
                raise serializers.ValidationError(
                    code="missing_required_param",
                    detail="Either 'resident_id' or new renter details (first_name, last_name, email) must be provided.",
                )

            # Check for duplicate application only if resident is provided
            if resident and unit:
                existing = Application.objects.filter(
                    resident=resident, unit=unit
                ).exists()
                if existing:
                    raise serializers.ValidationError(
                        code="duplicate_application",
                        detail=ERROR_DETAILS["duplicate_application"],
                    )

        status = attrs.get("status")
        if status:
            if status == LeaseApplicationStatus.APPROVED.value:
                if not self.instance or (
                    self.instance and not self.instance.approved_date
                ):
                    attrs["approved_date"] = datetime.now().date()
            if status == LeaseApplicationStatus.REJECTED.value:
                if not attrs.get("reject_reason"):
                    raise serializers.ValidationError(
                        code="missing_required_param",
                        detail=ERROR_DETAILS["missing_required_param"].format(
                            param="reject_reason"
                        ),
                    )
                if not self.instance or (
                    self.instance and not self.instance.reject_date
                ):
                    attrs["reject_date"] = datetime.now().date()
        return super().validate(attrs)

    class Meta:
        model = Application
        fields = "__all__"


class ApplicationSerializerForResident(BaseSerializer):
    resident = ResidentSerializer(read_only=True)
    unit = UnitDetailSerializer(read_only=True)
    esa_attachments = serializers.SerializerMethodField()

    def get_esa_attachments(self, obj):
        leases = obj.lease.all()
        attachments_qs = Asset.objects.filter(lease_esa_attachment__in=leases)
        return AssetSerializer(attachments_qs, many=True).data

    class Meta:
        model = Application
        fields = "__all__"

    def update(self, instance, validated_data):
        # Call the parent update to set status and received_date
        instance = super().update(instance, validated_data)

        # If status is set to received, create co-renter accounts and send password setup emails
        if instance.status == LeaseApplicationStatus.RECEIVED.value:
            additional_holders = instance.application_additional_holders.all()
            logger.info(
                f"Application {instance.id} status set to RECEIVED. Checking for {additional_holders.count()} additional holders"
            )
            if additional_holders.exists():
                logger.info(
                    f"Found {additional_holders.count()} additional holders for application {instance.id}"
                )
                # Create co-renter accounts and send emails using shared utility
                create_corenter_accounts(additional_holders, context=self.context)
            else:
                logger.info(
                    f"No additional holders found for application {instance.id}"
                )

        return instance

    def validate(self, attrs):
        status = attrs.pop("status", None)
        if attrs:
            raise serializers.ValidationError(
                code="invalid_input",
                detail=ERROR_DETAILS["invalid_input"],
            )
        if not status:
            raise serializers.ValidationError(
                code="missing_required_param",
                detail=ERROR_DETAILS["missing_required_param"].format(param="status"),
            )
        if status != LeaseApplicationStatus.RECEIVED.value:
            raise serializers.ValidationError(
                code="invalid_value",
                detail=ERROR_DETAILS["invalid_value"].format(attr="status"),
            )
        return {"status": status, "received_date": datetime.now().date()}


class LeaseLateFeesSerializer(BaseSerializer):
    lease_id = serializers.PrimaryKeyRelatedField(
        queryset=Lease.objects.all(),
        write_only=False,
        source="lease",
        required=True,
    )

    class Meta:
        model = LeaseLateFees
        fields = "__all__"
        extra_kwargs = {"lease": {"required": False}}


class LeaseOtherOccupantsSerializer(AgeValidationMixin, BaseSerializer):
    lease_id = serializers.PrimaryKeyRelatedField(
        queryset=Lease.objects.all(),
        write_only=False,
        source="lease",
        required=True,
    )

    class Meta:
        model = LeaseOtherOccupants
        fields = "__all__"
        extra_kwargs = {"lease": {"required": False}}


class LeaseAdditionalSignersSerializer(BaseSerializer):
    lease_id = serializers.PrimaryKeyRelatedField(
        queryset=Lease.objects.all(),
        write_only=False,
        source="lease",
        required=True,
    )

    class Meta:
        model = LeaseAdditionalSigners
        fields = "__all__"
        extra_kwargs = {"lease": {"required": False}}


class LeasePetsAllowedSerializer(AgeValidationMixin, BaseSerializer):
    lease_id = serializers.PrimaryKeyRelatedField(
        queryset=Lease.objects.all(),
        write_only=False,
        source="lease",
        required=True,
    )
    type_of_pet = PetSpeciesSerializer(read_only=True)
    type_of_pet_id = serializers.PrimaryKeyRelatedField(
        queryset=PetSpecies.objects.all(),
        write_only=True,
        source="type_of_pet",
        required=False,
        allow_null=True,
    )
    breed = PetBreedSerializer(read_only=True)
    breed_id = serializers.PrimaryKeyRelatedField(
        queryset=PetBreed.objects.all(),
        write_only=True,
        source="breed",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = LeasePetsAllowed
        fields = "__all__"
        extra_kwargs = {"lease": {"required": False}}


class LeaseUtilityServicesSerializer(BaseSerializer):
    lease_id = serializers.PrimaryKeyRelatedField(
        queryset=Lease.objects.all(),
        write_only=False,
        source="lease",
        required=True,
    )

    class Meta:
        model = LeaseUtilityServices
        fields = "__all__"
        extra_kwargs = {"lease": {"required": False}}


class LeaseOneTimeFeesSerializer(BaseSerializer):
    lease_id = serializers.PrimaryKeyRelatedField(
        queryset=Lease.objects.all(),
        write_only=False,
        source="lease",
        required=True,
    )

    class Meta:
        model = LeaseOneTimeFees
        fields = "__all__"
        extra_kwargs = {"lease": {"required": False}}


class LeaseSerialiserForStaff(BaseSerializer):
    resident_id = serializers.PrimaryKeyRelatedField(
        queryset=Resident.objects.all(),
        write_only=True,
        source="resident",
        required=True,
    )
    unit_id = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.all(),
        write_only=True,
        source="unit",
        required=False,
    )
    application_id = serializers.PrimaryKeyRelatedField(
        queryset=Application.objects.filter(
            status=LeaseApplicationStatus.APPROVED.value
        ),
        write_only=False,
        source="application",
        required=True,
    )
    other_resident_ids = serializers.PrimaryKeyRelatedField(
        queryset=Resident.objects.all(),
        write_only=True,
        source="other_residents",
        required=False,
        many=True,
    )
    attachment_ids = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(),
        write_only=True,
        source="attachments",
        required=False,
        many=True,
    )
    esa_attachment_ids = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(),
        write_only=True,
        source="esa_attachments",
        required=False,
        many=True,
    )
    parking_policy_id = serializers.PrimaryKeyRelatedField(
        queryset=PolicyVersion.objects.filter(policy__status="ACTIVE"),
        write_only=False,
        source="parking_policy",
        required=False,
    )
    early_termination_policy_id = serializers.PrimaryKeyRelatedField(
        queryset=PolicyVersion.objects.filter(policy__status="ACTIVE"),
        write_only=False,
        source="early_termination_policy",
        required=False,
    )
    additional_terms_policy_id = serializers.PrimaryKeyRelatedField(
        queryset=PolicyVersion.objects.filter(policy__status="ACTIVE"),
        write_only=False,
        source="additional_terms_policy",
        required=False,
    )
    resident = ResidentSerializer(read_only=True)
    unit = UnitDetailSerializer(read_only=True)
    parking_policy = PolicyVersionDetailSerializer(read_only=True)
    early_termination_policy = PolicyVersionDetailSerializer(read_only=True)
    additional_terms_policy = PolicyVersionDetailSerializer(read_only=True)
    attachments = AssetSerializer(read_only=True, many=True)
    esa_attachments = AssetSerializer(read_only=True, many=True)
    late_fees = LeaseLateFeesSerializer(read_only=True, many=True)
    other_occupants = LeaseOtherOccupantsSerializer(read_only=True, many=True)
    additional_signers = LeaseAdditionalSignersSerializer(read_only=True, many=True)
    pets_allowed = LeasePetsAllowedSerializer(read_only=True, many=True)
    utility_services = LeaseUtilityServicesSerializer(read_only=True, many=True)
    one_time_fees = LeaseOneTimeFeesSerializer(read_only=True, many=True)
    pdf_asset = AssetSerializer(read_only=True)
    lease_term = serializers.CharField(required=True)
    rent_amount = serializers.FloatField(required=True)
    due_date = serializers.DateField(required=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)

    def validate(self, attrs):
        if attrs.get("application") and not attrs.get("unit"):
            attrs["unit"] = attrs.get("application").unit
        if not self.instance:
            if (
                attrs.get("application")
                and attrs.get("unit")
                and attrs.get("application").unit != attrs.get("unit")
            ):
                raise serializers.ValidationError(
                    code="invalid_id",
                    detail=ERROR_DETAILS["invalid_id"].format(param="unit"),
                )
        else:
            if attrs.get("application") or attrs.get("unit"):
                raise serializers.ValidationError(
                    code="cannot_update_data",
                    detail=ERROR_DETAILS["cannot_update_data"].format(
                        field="application or unit"
                    ),
                )

        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")
        lease_term = attrs.get("lease_term")
        rent_amount = attrs.get("rent_amount")
        due_date = attrs.get("due_date")

        if not start_date or not end_date:
            raise serializers.ValidationError(
                code="required_start_end_date",
                detail=ERROR_DETAILS["required_start_end_date"],
            )

        if start_date >= end_date:
            raise serializers.ValidationError(
                code="invalid_start_end_date",
                detail=ERROR_DETAILS["invalid_start_end_date"],
            )

        if rent_amount is not None and rent_amount <= 0:
            raise serializers.ValidationError(
                code="positive_rent_amount",
                detail=ERROR_DETAILS["positive_rent_amount"],
            )

        if due_date and due_date < start_date:
            raise serializers.ValidationError(
                code="invalid_due_date",
                detail=ERROR_DETAILS["invalid_due_date"],
            )
        valid_terms = ["fixed_term", "month_to_month"]

        if lease_term not in valid_terms:
            raise serializers.ValidationError(
                code="invalid_lease_term",
                detail=ERROR_DETAILS["invalid_lease_term"],
            )
        if lease_term == "fixed_term" and not end_date:
            raise serializers.ValidationError(
                code="end_date_required_for_fixed_term",
                detail=ERROR_DETAILS["end_date_required_for_fixed_term"],
            )
        return super().validate(attrs)

    def upsert_m2m_relations(self):
        relations = {
            "late_fees": LeaseLateFeesSerializer,
            "other_occupants": LeaseOtherOccupantsSerializer,
            "additional_signers": LeaseAdditionalSignersSerializer,
            "pets_allowed": LeasePetsAllowedSerializer,
            "utility_services": LeaseUtilityServicesSerializer,
            "one_time_fees": LeaseOneTimeFeesSerializer,
        }
        for item, srz_class in relations.items():
            data = self.initial_data.get(item, None)
            if data is None:
                continue
            saved_ids = []
            model = srz_class.Meta.model
            for obj in data:
                id = obj.get("id")
                obj["lease_id"] = self.instance.id
                if id:
                    instance = model.objects.get(id=id)
                    srz_obj = srz_class(instance=instance, data=obj)
                    srz_obj.is_valid(raise_exception=True)
                    srz_obj.save()
                else:
                    srz_obj = srz_class(data=obj)
                    srz_obj.is_valid(raise_exception=True)
                    srz_obj.save()
                saved_ids.append(srz_obj.instance.id)
            other_related_objs = model.objects.filter(
                lease_id=self.instance.id
            ).exclude(id__in=saved_ids)
            other_related_objs.delete()

    def create(self, validated_data):
        resp = super().create(validated_data)
        self.instance = resp
        self.upsert_m2m_relations()
        return resp

    def update(self, instance, validated_data):
        resp = super().update(instance, validated_data)
        self.instance = resp
        self.upsert_m2m_relations()
        return resp

    class Meta:
        model = Lease
        fields = "__all__"


class LeaseSerializerForResident(BaseSerializer):
    resident = ResidentSerializer(read_only=True)
    unit = UnitDetailSerializer(read_only=True)
    parking_policy = PolicyVersionDetailSerializer(read_only=True)
    early_termination_policy = PolicyVersionDetailSerializer(read_only=True)
    additional_terms_policy = PolicyVersionDetailSerializer(read_only=True)
    attachments = AssetSerializer(read_only=True, many=True)
    attachments_id = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False,
        help_text="Attach one or more files (PDF, JPG, PNG)",
    )
    co_renter_status = serializers.BooleanField(write_only=True, required=False)
    co_renters = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )
    pdf_asset = AssetSerializer(read_only=True)

    class Meta:
        model = Lease
        fields = "__all__"

    def update(self, instance, validated_data):
        uploaded_files = validated_data.pop("attachments_id", [])
        co_renter_status = validated_data.pop("co_renter_status", None)
        co_renters_id = validated_data.pop("co_renters", [])

        instance = super().update(instance, validated_data)
        if isinstance(co_renter_status, str):
            co_renter_status = co_renter_status.lower() == "true"
        if uploaded_files:
            for file_obj in uploaded_files:
                asset = Asset.objects.create(
                    type="doc",
                    file=file_obj,
                    filename=file_obj.name,
                )
                instance.attachments.add(asset)

        if co_renter_status is True and co_renters_id:
            co_renters = LeaseOtherOccupants.objects.filter(id__in=co_renters_id)
            instance.other_occupants.add(*co_renters)
        elif co_renter_status is False and co_renters_id:
            LeaseOtherOccupants.objects.filter(
                id__in=co_renters_id, lease=instance
            ).delete()
        instance.save()
        return instance


class LeasePromotionalDiscountSerializer(BaseSerializer):
    lease_id = serializers.PrimaryKeyRelatedField(
        queryset=Lease.objects.all(),
        write_only=False,
        source="lease",
        required=True,
    )

    class Meta:
        model = LeasePromotionalDiscount
        fields = "__all__"
        extra_kwargs = {"lease": {"required": False}}


class LeaseKeysSerializer(BaseSerializer):
    lease_id = serializers.PrimaryKeyRelatedField(
        queryset=Lease.objects.all(),
        write_only=False,
        source="lease",
        required=True,
    )

    class Meta:
        model = LeaseKeys
        fields = "__all__"
        extra_kwargs = {"lease": {"required": False}}


class MoveRequestSerializer(BaseSerializer):
    unit_id = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.all(), write_only=True, source="unit", required=True
    )
    unit = UnitDetailSerializer(read_only=True)
    resident = ResidentSerializer(read_only=True)
    resident_id = serializers.PrimaryKeyRelatedField(
        queryset=Resident.objects.all(),
        write_only=True,
        source="resident",
        required=True,
    )
    image_ids = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(),
        write_only=True,
        source="images",
        required=False,
        many=True,
    )
    images = AssetSerializer(many=True, read_only=True)
    inspection_status = serializers.SerializerMethodField()

    class Meta:
        model = MoveRequest
        fields = "__all__"

    def get_inspection_status(self, obj):
        return list(obj.move_requests.values_list("result", flat=True))

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)

        passed_log_exists = instance.moveinspectionlog_set.filter(
            result=MoveInspectionStatus.PASSED.value
        ).exists()
        if passed_log_exists and "status" in validated_data:
            instance.status = validated_data["status"]
            instance.save(update_fields=["status"])

        return instance


class MoveRequestPostSerializer(BaseSerializer):
    class Meta:
        model = MoveRequest
        fields = "__all__"


class MoveRequestInspectionLogSerializer(BaseSerializer):
    move_request_id = serializers.PrimaryKeyRelatedField(
        queryset=MoveRequest.objects.all(),
        write_only=True,
        source="move_request",
        required=True,
    )
    move_request = MoveRequestPostSerializer(read_only=True)

    class Meta:
        model = MoveInspectionLog
        fields = "__all__"


class ApplicationOtherOccupantsSerializer(AgeValidationMixin, BaseSerializer):
    application_id = serializers.PrimaryKeyRelatedField(
        queryset=Application.objects.all(),
        write_only=False,
        source="application",
        required=True,
    )

    class Meta:
        model = ApplicationOtherOccupants
        fields = "__all__"
        extra_kwargs = {
            "application": {"read_only": True},
        }


class ApplicationPetsAllowedSerializer(AgeValidationMixin, BaseSerializer):
    application_id = serializers.PrimaryKeyRelatedField(
        queryset=Application.objects.all(),
        write_only=False,
        source="application",
        required=True,
    )
    type_of_pet = PetSpeciesSerializer(read_only=True)
    type_of_pet_id = serializers.PrimaryKeyRelatedField(
        queryset=PetSpecies.objects.all(),
        write_only=True,
        source="type_of_pet",
        required=False,
        allow_null=True,
    )
    breed = PetBreedSerializer(read_only=True)
    breed_id = serializers.PrimaryKeyRelatedField(
        queryset=PetBreed.objects.all(),
        write_only=True,
        source="breed",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ApplicationPetsAllowed
        fields = "__all__"
        extra_kwargs = {
            "application": {"read_only": True},
        }


class ApplicationUtilityServicesSerializer(BaseSerializer):
    application_id = serializers.PrimaryKeyRelatedField(
        queryset=Application.objects.all(),
        write_only=False,
        source="application",
        required=True,
    )
    attachment_ids = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(),
        write_only=True,
        source="attachments",
        required=False,
        many=True,
    )

    class Meta:
        model = ApplicationUtilityServices
        fields = "__all__"
        extra_kwargs = {
            "application": {"read_only": True},
        }


class ApplicationAdditionalLeaseHoldersSerializer(BaseSerializer):
    application_id = serializers.PrimaryKeyRelatedField(
        queryset=Application.objects.all(),
        write_only=False,
        source="application",
        required=True,
    )

    class Meta:
        model = ApplicationAdditionalLeaseHolders
        fields = "__all__"
        extra_kwargs = {
            "application": {"read_only": True},
        }


class ApplicationVIewSerializer(BaseSerializer):
    resident = ResidentSerializer(required=False)

    # Read-only fields fetched from resident
    documents = serializers.SerializerMethodField()
    emergency_contacts = serializers.SerializerMethodField()
    financial_guarantors = serializers.SerializerMethodField()
    addresses = serializers.SerializerMethodField()

    application_other_occupants = ApplicationOtherOccupantsSerializer(
        required=False, many=True, allow_null=True
    )
    application_pets_allowed = ApplicationPetsAllowedSerializer(
        required=False, many=True, allow_null=True
    )
    application_utility_services = ApplicationUtilityServicesSerializer(
        required=False, many=True, allow_null=True
    )
    application_additional_holders = ApplicationAdditionalLeaseHoldersSerializer(
        required=False, many=True, allow_null=True
    )
    esa_attachments = serializers.SerializerMethodField()

    def get_documents(self, obj):
        """Return documents for the resident associated with this application."""
        if obj.resident:
            documents = ResidentDocument.objects.filter(resident=obj.resident)
            return ResidentDocumentSerializer(documents, many=True).data
        return []

    def get_emergency_contacts(self, obj):
        """Return emergency contacts for the resident associated with this application."""
        if obj.resident:
            contacts = EmergencyContact.objects.filter(resident=obj.resident)
            return EmergencyContactSerializer(contacts, many=True).data
        return []

    def get_financial_guarantors(self, obj):
        """Return financial guarantors for the resident associated with this application."""
        if obj.resident:
            guarantors = ResidentFinancialGurantors.objects.filter(
                resident=obj.resident
            )
            return ResidentFinancialGurantorsSerializer(guarantors, many=True).data
        return []

    def get_addresses(self, obj):
        """Return addresses for the resident associated with this application."""
        if obj.resident:
            addresses = ResidentAddress.objects.filter(resident=obj.resident)
            return ResidentAddressSerializer(addresses, many=True).data
        return []

    def get_esa_attachments(self, obj):
        leases = obj.lease.all()
        attachments_qs = Asset.objects.filter(lease_esa_attachment__in=leases)
        return AssetSerializer(attachments_qs, many=True).data

    class Meta:
        model = Application
        fields = "__all__"

    def _create_corenter_accounts(self, additional_holders):
        """
        Create Resident accounts for co-renters/additional lease holders
        and send password setup emails to them.
        """
        create_corenter_accounts(additional_holders, context=self.context)

    def _update_emergency_contacts(self, resident, emergency_contacts_data):
        """
        Update emergency contacts for the resident.
        Creates new contacts or updates existing ones, and removes contacts not in the list.
        """
        if not emergency_contacts_data:
            return

        populated_ids = []
        for contact_data in emergency_contacts_data:
            contact_id = contact_data.pop("id", None)
            contact_data.pop("created_by", None)
            contact_data.pop("updated_by", None)
            contact_data["resident"] = resident

            if contact_id and EmergencyContact.objects.filter(id=contact_id).exists():
                EmergencyContact.objects.filter(id=contact_id).update(**contact_data)
                populated_ids.append(str(contact_id))
            else:
                # Use serializer to create new contact
                contact_data["resident"] = resident.id
                contact_serializer = EmergencyContactSerializer(data=contact_data)
                contact_serializer.is_valid(raise_exception=True)
                new_contact = contact_serializer.save()
                populated_ids.append(str(new_contact.id))

        # Remove contacts not in the list
        for contact in resident.emergencycontact_set.all():
            if str(contact.id) not in populated_ids:
                contact.delete()

    def _update_financial_guarantors(self, resident, financial_guarantors_data):
        """
        Update financial guarantors for the resident.
        Creates new guarantors or updates existing ones, and removes guarantors not in the list.
        """
        if not financial_guarantors_data:
            return

        populated_ids = []
        for guarantor_data in financial_guarantors_data:
            guarantor_id = guarantor_data.pop("id", None)
            guarantor_data.pop("created_by", None)
            guarantor_data.pop("updated_by", None)
            guarantor_data["resident"] = resident

            if (
                guarantor_id
                and ResidentFinancialGurantors.objects.filter(id=guarantor_id).exists()
            ):
                ResidentFinancialGurantors.objects.filter(id=guarantor_id).update(
                    **guarantor_data
                )
                populated_ids.append(str(guarantor_id))
            else:
                # Use serializer to create new guarantor
                guarantor_data["resident"] = resident.id
                guarantor_serializer = ResidentFinancialGurantorsSerializer(
                    data=guarantor_data
                )
                guarantor_serializer.is_valid(raise_exception=True)
                new_guarantor = guarantor_serializer.save()
                populated_ids.append(str(new_guarantor.id))

        # Remove guarantors not in the list
        for guarantor in resident.residentfinancialgurantors_set.all():
            if str(guarantor.id) not in populated_ids:
                guarantor.delete()

    def update(self, instance, validated_data):
        resident_data = validated_data.pop("resident", None)
        other_occupants_data = validated_data.pop("application_other_occupants", [])
        pets_allowed_data = validated_data.pop("application_pets_allowed", [])
        utility_services_data = validated_data.pop("application_utility_services", [])
        additional_holders_data = validated_data.pop(
            "application_additional_holders", []
        )
        # Extract top-level emergency_contacts and financial_guarantors from initial_data
        # (since they are SerializerMethodField, they won't be in validated_data)
        emergency_contacts_data = self.initial_data.get("emergency_contacts", [])
        financial_guarantors_data = self.initial_data.get("financial_guarantors", [])
        documents_data = self.initial_data.get("documents", [])
        addresses_data = self.initial_data.get("addresses", [])

        if resident_data:
            user_data = resident_data.pop("user", None)
            # Also check for nested data (backward compatibility)
            nested_documents = resident_data.pop("residentdocument_set", [])
            nested_emergency_contacts = resident_data.pop("emergencycontact_set", [])
            nested_addresses = resident_data.pop("residentaddress_set", [])
            nested_financial_guarantors = resident_data.pop(
                "residentfinancialgurantors_set", []
            )

            resident_serializer = ResidentSerializer(
                instance=instance.resident,
                data=resident_data,
                partial=True,
            )
            resident_serializer.is_valid(raise_exception=True)
            resident = resident_serializer.save()

            if user_data:
                user = resident.user
                for field, value in user_data.items():
                    setattr(user, field, value)
                user.save(update_fields=user_data.keys())

            # Merge nested data with top-level data (top-level takes precedence)
            if not documents_data and nested_documents:
                documents_data = nested_documents
            if not addresses_data and nested_addresses:
                addresses_data = nested_addresses
            if not emergency_contacts_data and nested_emergency_contacts:
                emergency_contacts_data = nested_emergency_contacts
            if not financial_guarantors_data and nested_financial_guarantors:
                financial_guarantors_data = nested_financial_guarantors
        else:
            resident = instance.resident

        for doc in documents_data:
            ResidentDocument.objects.update_or_create(resident=resident, **doc)

        # Handle emergency contacts
        self._update_emergency_contacts(resident, emergency_contacts_data)

        # Handle financial guarantors
        self._update_financial_guarantors(resident, financial_guarantors_data)

        for addr in addresses_data:
            ResidentAddress.objects.update_or_create(resident=resident, **addr)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        occ_objs = []
        for occ in other_occupants_data:
            obj, _ = ApplicationOtherOccupants.objects.update_or_create(
                application=instance, name=occ.get("name"), defaults=occ
            )
            occ_objs.append(obj)
        instance.application_other_occupants.set(occ_objs)

        pet_objs = []
        for pet in pets_allowed_data:
            obj, _ = ApplicationPetsAllowed.objects.update_or_create(
                application=instance, age=pet.get("age"), defaults=pet
            )
            pet_objs.append(obj)
        instance.application_pets_allowed.set(pet_objs)

        svc_objs = []
        for svc in utility_services_data:
            attachments = svc.pop("attachments", [])
            util_obj, _ = ApplicationUtilityServices.objects.update_or_create(
                application=instance, service=svc.get("service"), defaults=svc
            )
            if attachments:
                util_obj.attachments.set(attachments)

            svc_objs.append(util_obj)
        instance.application_utility_services.set(svc_objs)
        holder_objs = []
        for holder in additional_holders_data:
            obj, _ = ApplicationAdditionalLeaseHolders.objects.update_or_create(
                application=instance, email=holder.get("email"), defaults=holder
            )
            holder_objs.append(obj)
        instance.application_additional_holders.set(holder_objs)

        # Create accounts for co-renters/additional lease holders and send password setup emails
        if holder_objs:
            self._create_corenter_accounts(holder_objs)

        return instance


class PropertyManagerSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    contact_number = serializers.CharField(source="work_phone", read_only=True)
    email = serializers.CharField(source="contact_email", read_only=True)

    class Meta:
        model = Location
        fields = ["name", "contact_number", "email"]

    def get_name(self, obj):
        if obj.contact_first_name and obj.contact_last_name:
            return f"{obj.contact_first_name} {obj.contact_last_name}"
        elif obj.contact_first_name:
            return obj.contact_first_name
        return "Not Available"


class LandlordDetailsSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="landlord_full_name", read_only=True)
    contact_number = serializers.CharField(source="landlord_phone", read_only=True)
    email = serializers.EmailField(source="landlord_email", read_only=True)

    class Meta:
        model = Lease
        fields = ["name", "contact_number", "email"]


class CoRenterSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)

    class Meta:
        model = Resident
        fields = ["id", "name", "email", "phone"]

    def get_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"


class LeaseDocumentSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="filename", read_only=True)
    signed_date = serializers.DateTimeField(source="created_on", read_only=True)
    document_url = serializers.CharField(source="file", read_only=True)
    document_type = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = ["id", "name", "signed_date", "document_url", "document_type"]

    def get_document_type(self, obj):
        if "lease" in obj.filename.lower():
            return "Signed Lease"
        elif "moi" in obj.filename.lower() or "pt" in obj.filename.lower():
            return "MOI for PT"
        elif "2026" in obj.filename.lower():
            return "MOI for 2026"
        return "Other Document"


class PropertyDetailSerializer(serializers.ModelSerializer):
    property_type = serializers.CharField(
        source="unit.floor.building.location.property.name", read_only=True
    )
    location = serializers.SerializerMethodField()
    property_owner = serializers.SerializerMethodField()
    floor = serializers.CharField(source="unit.floor.floor_number", read_only=True)
    unit = serializers.CharField(source="unit.unit_number", read_only=True)
    annual_rent_rental = serializers.DecimalField(
        source="rent_amount", max_digits=10, decimal_places=2, read_only=True
    )
    security_deposit = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    square_feet = serializers.CharField(source="unit.square_feet", read_only=True)
    bedrooms = serializers.IntegerField(source="unit.bedrooms", read_only=True)
    status = serializers.CharField(read_only=True)
    floor_plan = serializers.CharField(source="unit.floor_plan", read_only=True)

    landlord_details = LandlordDetailsSerializer(source="*", read_only=True)

    property_manager = serializers.SerializerMethodField()

    co_renters = CoRenterSerializer(source="other_residents", many=True, read_only=True)

    lease_documents = serializers.SerializerMethodField()

    lease_start_date = serializers.DateField(source="start_date", read_only=True)
    lease_end_date = serializers.DateField(source="end_date", read_only=True)
    lease_term = serializers.CharField(read_only=True)
    due_date = serializers.DateField(read_only=True)

    building_name = serializers.CharField(
        source="unit.floor.building.name", read_only=True
    )
    building_address = serializers.CharField(
        source="unit.floor.building.location.address", read_only=True
    )
    city = serializers.CharField(
        source="unit.floor.building.location.city", read_only=True
    )
    state = serializers.CharField(
        source="unit.floor.building.location.state", read_only=True
    )
    zipcode = serializers.CharField(
        source="unit.floor.building.location.zipcode", read_only=True
    )

    class Meta:
        model = Lease
        fields = [
            "id",
            # Property Details
            "property_type",
            "location",
            "property_owner",
            "floor",
            "unit",
            "annual_rent_rental",
            "security_deposit",
            "square_feet",
            "bedrooms",
            "status",
            "floor_plan",
            # Landlord Details
            "landlord_details",
            # Property Manager
            "property_manager",
            # Co-Renters
            "co_renters",
            # Lease Documents
            "lease_documents",
            # Additional Information
            "lease_start_date",
            "lease_end_date",
            "lease_term",
            "due_date",
            "building_name",
            "building_address",
            "city",
            "state",
            "zipcode",
        ]

    def _format_unit_location(self, unit):
        if not unit:
            return None
        display_id = (
            unit.display_id
            or f"{unit.floor.building.name}-{unit.floor.floor_number}-{unit.unit_number}"
        )
        address = unit.floor.building.location.address
        return f"{display_id}, {address}"

    def get_location(self, obj):
        return self._format_unit_location(obj.unit)

    def _format_resident_name(self, resident):
        if not resident or not resident.user:
            return None
        return f"{resident.user.first_name} {resident.user.last_name}"

    def get_property_owner(self, obj):
        return self._format_resident_name(obj.resident)

    def _get_property_manager_data(self, location):
        if not location:
            return self._default_manager_data()
        serializer = PropertyManagerSerializer(location)
        return serializer.data

    def _default_manager_data(self):
        return {"name": "Not Available", "contact_number": None, "email": None}

    def get_property_manager(self, obj):
        location = obj.unit.floor.building.location
        return self._get_property_manager_data(location)

    def _format_document(self, doc_id, name, created_on, file_url, doc_type):
        signed_date = created_on.strftime("%m/%d/%Y - %I:%M%p") if created_on else None
        file_url = file_url if file_url else None
        return {
            "id": str(doc_id),
            "name": name,
            "signed_date": signed_date,
            "document_url": file_url,
            "document_type": doc_type,
        }

    def _add_lease_attachments(self, obj, documents):
        if obj.attachments.exists():
            for attachment in obj.attachments.all():
                doc = self._format_document(
                    doc_id=attachment.id,
                    name=f"Lease - {attachment.filename}",
                    created_on=attachment.created_on,
                    file_url=attachment.file.url if attachment.file else None,
                    doc_type="SignedLease",
                )
                documents.append(doc)

    def _add_esa_attachments(self, obj, documents):
        if obj.esa_attachments.exists():
            for esa_doc in obj.esa_attachments.all():
                doc = self._format_document(
                    doc_id=esa_doc.id,
                    name=f"ESA - {esa_doc.filename}",
                    created_on=esa_doc.created_on,
                    file_url=esa_doc.file.url if esa_doc.file else None,
                    doc_type="ESA Document",
                )
                documents.append(doc)

    def _add_parking_policy(self, obj, documents):
        if obj.parking_policy:
            doc = {
                "id": str(obj.parking_policy.id),
                "name": f"Parking Policy - {obj.parking_policy.version}",
                "signed_date": None,
                "document_url": None,
                "document_type": "Policy",
            }
            documents.append(doc)

    def _add_early_termination_policy(self, obj, documents):
        if obj.early_termination_policy:
            doc = {
                "id": str(obj.early_termination_policy.id),
                "name": f"Early Termination Policy - {obj.early_termination_policy.version}",
                "signed_date": None,
                "document_url": None,
                "document_type": "Policy",
            }
            documents.append(doc)

    def _add_additional_terms_policy(self, obj, documents):
        if obj.additional_terms_policy:
            doc = {
                "id": str(obj.additional_terms_policy.id),
                "name": f"Additional Terms - {obj.additional_terms_policy.version}",
                "signed_date": None,
                "document_url": None,
                "document_type": "Policy",
            }
            documents.append(doc)

    def get_lease_documents(self, obj):
        documents = []
        self._add_lease_attachments(obj, documents)
        self._add_esa_attachments(obj, documents)
        self._add_parking_policy(obj, documents)
        self._add_early_termination_policy(obj, documents)
        self._add_additional_terms_policy(obj, documents)
        return documents


class RenterRentedPropertiesSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(
        source="unit.floor.building.location.property.name", read_only=True
    )
    location_name = serializers.CharField(
        source="unit.floor.building.location.name", read_only=True
    )
    location_address = serializers.CharField(
        source="unit.floor.building.location.address", read_only=True
    )
    building_name = serializers.CharField(
        source="unit.floor.building.name", read_only=True
    )
    floor_number = serializers.CharField(
        source="unit.floor.floor_number", read_only=True
    )
    unit_number = serializers.CharField(source="unit.unit_number", read_only=True)
    unit_type = serializers.CharField(source="unit.unit_type", read_only=True)
    lease_start_date = serializers.DateField(source="start_date", read_only=True)
    lease_end_date = serializers.DateField(source="end_date", read_only=True)

    class Meta:
        model = Lease
        fields = [
            "id",
            "property_name",
            "location_name",
            "location_address",
            "building_name",
            "floor_number",
            "unit_number",
            "unit_type",
            "lease_start_date",
            "lease_end_date",
            "status",
            "rent_amount",
        ]


class PropertyMinimalSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    display_id = serializers.CharField()
    name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    address = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    zipcode = serializers.CharField()
    country = serializers.CharField()


class LocationMinimalSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    display_id = serializers.CharField()
    name = serializers.CharField()
    address = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    zipcode = serializers.CharField()
    country = serializers.CharField()
    property = PropertyMinimalSerializer()


class BuildingMinimalSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    display_id = serializers.CharField()
    name = serializers.CharField()
    year_built = serializers.DateField()


class FloorMinimalSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    display_id = serializers.CharField()
    floor_number = serializers.CharField()
    description = serializers.CharField()
    building = BuildingMinimalSerializer()


class UnitMinimalSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    display_id = serializers.CharField()
    unit_number = serializers.CharField()
    unit_type = serializers.CharField()
    status = serializers.CharField()
    floor_plan = serializers.CharField()
    unfurnished_price = serializers.SerializerMethodField()
    furnished_price = serializers.SerializerMethodField()
    floor = FloorMinimalSerializer()

    def get_unfurnished_price(self, obj):
        if obj.unfurnished_price:
            return float(obj.unfurnished_price.amount)
        return 0.0

    def get_furnished_price(self, obj):
        if obj.furnished_price:
            return float(obj.furnished_price.amount)
        return 0.0


class ResidentMinimalSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    display_id = serializers.CharField(source="resident_id")
    resident_id = serializers.CharField()
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.EmailField(source="user.email")
    phone = serializers.CharField(source="user.phone")
    age = serializers.IntegerField(source="user.age", read_only=True)
    profile_type = serializers.CharField()
    profile = serializers.SerializerMethodField()

    def get_profile(self, obj):
        if obj.user and obj.user.profile_img:
            return {
                "id": str(obj.user.profile_img.id),
                "file": obj.user.profile_img.file.url
                if obj.user.profile_img.file
                else None,
            }
        return None


class ApplicationMinimalSerializer(BaseSerializer):
    resident = ResidentMinimalSerializer(read_only=True)
    unit = UnitMinimalSerializer(read_only=True)
    location = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            "id",
            "display_id",
            "created_on",
            "updated_on",
            "sent_date",
            "received_date",
            "approved_date",
            "status",
            "resident",
            "unit",
            "location",
        ]

    def get_location(self, obj):
        if obj.unit and obj.unit.floor and obj.unit.floor.building:
            location = obj.unit.floor.building.location
            return LocationMinimalSerializer(location).data
        return None


class MoveRequestMinimalSerializer(BaseSerializer):
    """
    Minimal move request serializer for fast response times.
    Returns only essential fields with minimal nested objects.
    """

    resident = ResidentMinimalSerializer(read_only=True)
    unit = UnitMinimalSerializer(read_only=True)
    location = serializers.SerializerMethodField()

    class Meta:
        model = MoveRequest
        fields = [
            "id",
            "display_id",
            "created_on",
            "updated_on",
            "move_type",
            "move_date",
            "status",
            "deposit_status",
            "inspection_datetime",
            "resident",
            "unit",
            "location",
        ]

    def get_location(self, obj):
        if obj.unit and obj.unit.floor and obj.unit.floor.building:
            location = obj.unit.floor.building.location
            return LocationMinimalSerializer(location).data
        return None


class LeaseSerializerV2(BaseSerializer):
    """
    Complete read-only serializer for lease data with minimal nested objects.
    Used for /api/v1/lease-minimal endpoint for fast response times.
    Returns all lease fields but uses minimal serializers for related objects.
    """

    resident = ResidentMinimalSerializer(read_only=True)
    unit = UnitMinimalSerializer(read_only=True)
    location = serializers.SerializerMethodField()
    pdf_asset = AssetSerializer(read_only=True)

    class Meta:
        model = Lease
        fields = "__all__"

    def get_location(self, obj):
        """Return minimal location information for quick response"""
        if obj.unit and obj.unit.floor and obj.unit.floor.building:
            location = obj.unit.floor.building.location
            return LocationMinimalSerializer(location).data
        return None
