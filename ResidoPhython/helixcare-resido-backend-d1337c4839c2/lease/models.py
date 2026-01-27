import logging
import traceback

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from django.utils import timezone
from rest_framework.serializers import ValidationError
from assets.models import Asset
from common.utils.general import get_display_id
from common.models import (
    GenericModel,
    optional,
    validate_country_state,
    PhoneEmail,
    PetSpecies,
    PetBreed,
)
from common.errors import ERROR_DETAILS
from lookup.fields import LookupField
from residents.models import Resident
from locations.models import Unit
from lease.constants import (
    ESAType,
    LeaseTerm,
    FeeAppliedOn,
    LeaseStatus,
    LandlordType,
    SmokingStatus,
    LateFeeLimit,
    LeaseApplicationStatus,
    LeaseUtilityServiceResponsible,
    LEASE_APPLICATION_STATUS_LEVEL,
    LEASE_STATUS_LEVEL,
    MoveRequestType,
    MoveRequestStatus,
    MoveInspectionStatus,
    MoveRequestDepositStatus,
    LeaseEndActionChoice,
)
from staff.models import HelixStaff
from helixauth.models import PolicyVersion
from analytics.managers.dashboard.lease import LeaseAnalyticsManager
from lease.services import LeasePDFGenerator

logger = logging.getLogger(__name__)


class Application(GenericModel):
    display_id = models.CharField(
        max_length=20, unique=True, editable=False, **optional
    )
    resident = models.ForeignKey(
        Resident, on_delete=models.DO_NOTHING, related_name="application"
    )
    unit = models.ForeignKey(
        Unit, on_delete=models.DO_NOTHING, related_name="application"
    )
    sent_date = models.DateField(auto_now_add=True)
    received_date = models.DateField(**optional)
    approved_date = models.DateField(**optional)
    reject_date = models.DateField(**optional)
    notes = models.TextField(**optional)
    status = models.CharField(
        choices=LeaseApplicationStatus.choices(),
        default=LeaseApplicationStatus.SENT.value,
        max_length=255,
    )
    reject_reason = LookupField(
        max_length=100, lookup_name="APPLICATION_REJECT_REASON", **optional
    )
    reject_notes = models.TextField(**optional)
    application_lease_term = models.CharField(
        max_length=100, choices=LeaseTerm.choices(), **optional
    )
    application_lease_start_date = models.DateField(**optional)
    application_lease_end_date = models.DateField(**optional)
    application_lease_end_action = models.CharField(
        max_length=20, choices=LeaseEndActionChoice.choices(), **optional
    )
    application_lease_expected_move_in_date = models.DateField(**optional)
    application_lease_expected_move_out_date = models.DateField(**optional)
    smoking_status = models.BooleanField(default=False)
    parking_inside_premises = models.BooleanField(default=False)
    parking_preferences_in_rented_unit = ArrayField(
        LookupField(max_length=10, lookup_name="PARKING_PREFERENCES_IN_RENTED_UNIT"),
        **optional,
    )
    additional_notes = models.TextField(**optional)
    # Flag to track if application email should be sent after renter password setup
    pending_activation_email = models.BooleanField(default=False)

    class Meta:
        path_to_location = "unit__floor__building__location"
        path_to_resident_id = "resident_id"

    def clean(self):
        if (
            self._old_status
            and self.status != self._old_status
            and LEASE_APPLICATION_STATUS_LEVEL.get(self._old_status)
            >= LEASE_APPLICATION_STATUS_LEVEL.get(self.status)
        ):
            raise ValidationError(
                code="invalid_input_value",
                detail=ERROR_DETAILS["invalid_input_value"].format(param="status"),
            )
        return super().clean()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_status = self.status

    def save(self, *args, **kwargs):
        self.display_id = get_display_id(self, "RR")
        return super().save(*args, **kwargs)


class Lease(GenericModel):
    resident = models.ForeignKey(
        Resident, on_delete=models.DO_NOTHING, related_name="leases"
    )
    unit = models.ForeignKey(
        Unit, on_delete=models.DO_NOTHING, related_name="lease", **optional
    )
    application = models.ForeignKey(
        Application, on_delete=models.DO_NOTHING, related_name="lease", **optional
    )
    title = models.CharField(max_length=255)
    status = models.CharField(
        max_length=200, choices=LeaseStatus.choices(), default=LeaseStatus.DRAFT.value
    )
    lease_term = models.CharField(
        max_length=100, choices=LeaseTerm.choices(), **optional
    )
    rent_amount = models.FloatField(**optional)
    due_date = models.DateField(**optional)
    late_fees_applicable = models.BooleanField(default=False)
    # late_fees as reverse linking
    prorated_rent_applicable = models.BooleanField(default=False)
    prorated_rent_amount = models.FloatField(default=0)
    security_amount = models.FloatField(default=0)
    security_refundable = models.BooleanField(default=False)
    pet_deposit_required = models.BooleanField(default=False)
    pet_deposit_amount = models.FloatField(default=0)
    pet_deposit_refundable = models.BooleanField(default=False)
    start_date = models.DateField(**optional)
    end_date = models.DateField(**optional)
    auto_renewal = models.BooleanField(default=False)
    one_time_fees_applicable = models.BooleanField(default=False)
    one_time_fees_name = models.CharField(max_length=255, **optional)
    one_time_fees_amount = models.FloatField(default=0)
    payments_accepted = ArrayField(
        LookupField(max_length=10, lookup_name="PAYMENT_MODES"), **optional
    )
    other_residents = models.ManyToManyField(Resident, related_name="lease", **optional)
    # other_occupants as reverse linking
    landlord_type = models.CharField(
        max_length=100, choices=LandlordType.choices(), **optional
    )
    landlord_first_name = models.CharField(max_length=255, **optional)
    landlord_middle_name = models.CharField(max_length=255, **optional)
    landlord_last_name = models.CharField(max_length=255, **optional)
    landlord_full_name = models.CharField(max_length=255, **optional)
    landlord_email = models.EmailField(**optional)
    landlord_phone = models.CharField(max_length=100, **optional)
    landlord_phone_country_code = models.CharField(
        max_length=5, default="+1", **optional
    )
    landlord_address = models.CharField(max_length=512, **optional)
    landlord_address_1 = models.CharField(max_length=512, **optional)
    landlord_city = models.CharField(max_length=50, **optional)
    landlord_state = models.CharField(max_length=50, **optional)
    landlord_zipcode = models.CharField(max_length=10, **optional)
    landlord_country = LookupField(max_length=10, lookup_name="COUNTRY", **optional)
    # additional_signers as reverse linking
    # pets_allowed as reverse linking
    smoking_status = models.CharField(
        max_length=100, choices=SmokingStatus.choices(), **optional
    )
    parking_available = ArrayField(
        LookupField(max_length=10, lookup_name="PARKING_TYPE"), **optional
    )
    include_parking_rules = models.BooleanField(default=False)
    parking_policy = models.ForeignKey(
        PolicyVersion,
        on_delete=models.DO_NOTHING,
        related_name="parking_policy",
        **optional,
    )
    parking_rules = models.TextField(**optional)
    # utilities_services as reverse linking
    # keys as reverse linking
    early_termination_allowed = models.BooleanField(default=False)
    early_termination_clause = models.TextField(**optional)
    early_termination_policy = models.ForeignKey(
        PolicyVersion,
        on_delete=models.DO_NOTHING,
        related_name="early_termination_policy",
        **optional,
    )
    additional_terms_allowed = models.BooleanField(default=False)
    additional_terms_clause = models.TextField(**optional)
    additional_terms_policy = models.ForeignKey(
        PolicyVersion,
        on_delete=models.DO_NOTHING,
        related_name="additional_terms_policy",
        **optional,
    )
    attachments = models.ManyToManyField(Asset, **optional)
    esa_type = models.CharField(choices=ESAType.choices(), max_length=255, **optional)
    esa_perform = models.TextField(**optional)
    esa_attachments = models.ManyToManyField(
        Asset, related_name="lease_esa_attachment", **optional
    )
    smoking_allowed = models.BooleanField(default=False)
    pet_type = LookupField(max_length=50, lookup_name="PET_TYPE", **optional)
    pdf_asset = models.ForeignKey(
        Asset,
        on_delete=models.SET_NULL,
        related_name="lease_pdf",
        null=True,
        blank=True,
        help_text="Auto-generated lease PDF",
    )

    analytics = LeaseAnalyticsManager()

    class Meta:
        path_to_location = "unit__floor__building__location"
        path_to_resident_id = "resident_id"

    def clean(self):
        if (
            self._old_status
            and self.status != self._old_status
            and LEASE_STATUS_LEVEL.get(self._old_status)
            >= LEASE_STATUS_LEVEL.get(self.status)
        ):
            raise ValidationError(
                code="invalid_input_value",
                detail=ERROR_DETAILS["invalid_input_value"].format(param="status"),
            )
        # TODO: add more validations
        validate_country_state(self, "landlord_country", "landlord_state")
        return super().clean()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_status = self.status

    def _generate_pdf(self):
        """Generate PDF for the lease"""
        try:
            # Don't generate PDF for draft leases
            if self.status == "draft":
                msg = f"Skipping PDF generation for draft lease {self.id}"
                logger.info(msg)
                return

            # Generate the PDF
            pdf_generator = LeasePDFGenerator(self)
            pdf_buffer = pdf_generator.generate()

            # Prepare filename
            lease_id = str(self.id)[:8]
            filename = (
                f"lease_{lease_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )

            # Save PDF buffer to BytesIO
            pdf_buffer.seek(0)
            pdf_content = ContentFile(pdf_buffer.getvalue())

            # Create or update Asset for the PDF
            if self.pdf_asset:
                # Delete old file
                if self.pdf_asset.file:
                    self.pdf_asset.file.delete(save=False)
                # Update existing asset
                self.pdf_asset.file.save(filename, pdf_content, save=False)
                self.pdf_asset.filename = filename
                self.pdf_asset.save()
                action = "regenerated"
            else:
                # Create new asset
                pdf_asset = Asset.objects.create(
                    type="pdf", file=None, filename=filename
                )
                pdf_asset.file.save(filename, pdf_content, save=False)
                pdf_asset.save()
                self.pdf_asset = pdf_asset

                Lease.objects.filter(pk=self.pk).update(pdf_asset=pdf_asset)
                action = "created"

            msg = f"Lease PDF {action} for lease {self.id}"
            logger.info(msg)

        except Exception as e:
            error_msg = f" Error generating PDF for lease {self.id}: {str(e)}"
            traceback.print_exc()
            logger.error(error_msg, exc_info=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.status != "draft":
            self._generate_pdf()

    def delete(self, *args, **kwargs):
        try:
            if self.pdf_asset:
                self.pdf_asset.delete()
                logger.info(f"Cleaned up PDF asset for deleted lease {self.id}")
        except Exception as e:
            logger.error(
                f"Error cleaning up PDF for lease {self.id}: {str(e)}", exc_info=True
            )

        super().delete(*args, **kwargs)


class LeaseOneTimeFees(GenericModel):
    lease = models.ForeignKey(
        Lease, related_name="one_time_fees", on_delete=models.CASCADE
    )
    name = LookupField(max_length=10, lookup_name="LEASE_ONE_TIME_FEES")
    amount = models.FloatField(validators=[MinValueValidator(0)])

    class Meta:
        path_to_location = "lease__unit__floor__building__location"
        path_to_resident_id = "lease__resident_id"


class LeasePromotionalDiscount(GenericModel):
    lease = models.ForeignKey(
        Lease, related_name="promotional_discount", on_delete=models.CASCADE
    )
    name = LookupField(max_length=10, lookup_name="LEASE_DISCOUNT")
    amount = models.FloatField(validators=[MinValueValidator(0)])

    class Meta:
        path_to_location = "lease__unit__floor__building__location"
        path_to_resident_id = "lease__resident_id"


class LeaseLateFees(GenericModel):
    lease = models.ForeignKey(Lease, related_name="late_fees", on_delete=models.CASCADE)
    daily_late_fee_applicable = models.BooleanField(default=False)
    daily_late_fee = models.FloatField(**optional)
    daily_late_fee_applied_on = models.IntegerField(
        choices=FeeAppliedOn.choices(), **optional
    )
    late_fee_limit = models.CharField(choices=LateFeeLimit.choices(), **optional)
    late_fee_limit_value = models.FloatField(**optional)

    class Meta:
        path_to_location = "lease__unit__floor__building__location"
        path_to_resident_id = "lease__resident_id"

    def clean(self):
        # TODO: Add validations
        return super().clean()


class LeaseOtherOccupants(GenericModel):
    lease = models.ForeignKey(
        Lease, related_name="other_occupants", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    relationship = LookupField(max_length=10, lookup_name="OCCUPANTS_RELATIONSHIP")
    age = models.IntegerField()

    class Meta:
        path_to_location = "lease__unit__floor__building__location"
        path_to_resident_id = "lease__resident_id"


class LeaseAdditionalSigners(GenericModel):
    lease = models.ForeignKey(
        Lease, related_name="additional_signers", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    email = models.EmailField()

    class Meta:
        path_to_location = "lease__unit__floor__building__location"
        path_to_resident_id = "lease__resident_id"


class LeasePetsAllowed(GenericModel):
    lease = models.ForeignKey(
        Lease, related_name="pets_allowed", on_delete=models.CASCADE
    )
    type_of_pet = models.ForeignKey(
        PetSpecies, on_delete=models.SET_NULL, related_name="lease_pets", **optional
    )
    breed = models.ForeignKey(
        PetBreed, on_delete=models.SET_NULL, related_name="lease_pets", **optional
    )
    age = models.IntegerField()
    monthly_fee = models.FloatField(**optional)

    class Meta:
        path_to_location = "lease__unit__floor__building__location"
        path_to_resident_id = "lease__resident_id"


class LeaseUtilityServices(GenericModel):
    lease = models.ForeignKey(
        Lease, related_name="utility_services", on_delete=models.CASCADE
    )
    service = LookupField(max_length=10, lookup_name="UTILITY_SERVICE")
    responsible = models.CharField(
        max_length=100, choices=LeaseUtilityServiceResponsible.choices()
    )

    class Meta:
        path_to_location = "lease__unit__floor__building__location"
        path_to_resident_id = "lease__resident_id"


class LeaseKeys(GenericModel):
    lease = models.ForeignKey(Lease, related_name="keys", on_delete=models.CASCADE)
    key_type = LookupField(max_length=10, lookup_name="KEY_TYPE")
    copies = models.IntegerField()

    class Meta:
        path_to_location = "lease__unit__floor__building__location"
        path_to_resident_id = "lease__resident_id"


class MoveRequest(GenericModel, PhoneEmail):
    display_id = models.CharField(
        max_length=20, unique=True, editable=False, **optional
    )
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    move_type = models.CharField(max_length=100, choices=MoveRequestType.choices())
    move_date = models.DateField()
    inspector = models.ForeignKey(HelixStaff, on_delete=models.CASCADE, **optional)
    inspection_datetime = models.DateTimeField(**optional)
    notes = models.TextField(**optional)
    status = models.CharField(
        max_length=100,
        choices=MoveRequestStatus.choices(),
        default=MoveRequestStatus.PENDING.value,
    )
    images = models.ManyToManyField(Asset, **optional)
    deposit_status = models.CharField(
        max_length=100,
        choices=MoveRequestDepositStatus.choices(),
        default=MoveRequestDepositStatus.PENDING.value,
    )

    def save(self, *args, **kwargs):
        self.display_id = get_display_id(self, "MR")
        return super().save(*args, **kwargs)

    class Meta:
        path_to_location = "unit__floor__building__location"
        path_to_resident_id = "resident_id"
        constraints = [
            models.UniqueConstraint(
                fields=["unit", "resident", "move_type"],
                name="unique_move_request_per_move_type",
            )
        ]


class MoveInspectionLog(GenericModel):
    move_request = models.ForeignKey(
        MoveRequest, on_delete=models.CASCADE, related_name="move_requests"
    )
    inspector = models.ForeignKey(HelixStaff, on_delete=models.CASCADE)
    notes = models.TextField(**optional)
    additional_notes = models.TextField(**optional)
    result = models.CharField(
        max_length=100,
        choices=MoveInspectionStatus.choices(),
        default=MoveInspectionStatus.NOT_SCHEDULED.value,
    )
    preferred_datetime = models.DateTimeField()
    notify_renter = models.BooleanField(default=True)

    class Meta:
        path_to_location = "move_request__unit__floor__building__location"
        path_to_resident_id = "move_request__resident_id"
        constraints = [
            models.UniqueConstraint(
                fields=["move_request", "preferred_datetime"],
                name="unique_move_inspection_per_datetime",
            )
        ]

    def __str__(self):
        return f"{self.move_request} - {self.result} ({self.preferred_datetime})"


class ApplicationOtherOccupants(GenericModel):
    application = models.ForeignKey(
        Application,
        related_name="application_other_occupants",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)
    relationship = LookupField(max_length=10, lookup_name="OCCUPANTS_RELATIONSHIP")
    age = models.IntegerField()

    class Meta:
        path_to_location = "application__unit__floor__building__location"
        path_to_resident_id = "application__resident_id"


class ApplicationPetsAllowed(GenericModel):
    application = models.ForeignKey(
        Application, related_name="application_pets_allowed", on_delete=models.CASCADE
    )
    type_of_pet = models.ForeignKey(
        PetSpecies,
        on_delete=models.SET_NULL,
        related_name="application_pets",
        **optional,
    )
    breed = models.ForeignKey(
        PetBreed, on_delete=models.SET_NULL, related_name="application_pets", **optional
    )
    age = models.IntegerField()
    monthly_fee = models.FloatField(**optional)

    class Meta:
        path_to_location = "application__unit__floor__building__location"
        path_to_resident_id = "application__resident_id"


class ApplicationUtilityServices(GenericModel):
    application = models.ForeignKey(
        Application,
        related_name="application_utility_services",
        on_delete=models.CASCADE,
    )
    service = LookupField(max_length=10, lookup_name="UTILITY_SERVICE")
    responsible = models.CharField(
        max_length=100, choices=LeaseUtilityServiceResponsible.choices()
    )
    task_perform = models.CharField(max_length=200, **optional)
    attachments = models.ManyToManyField(Asset, **optional)

    class Meta:
        path_to_location = "application__unit__floor__building__location"
        path_to_resident_id = "application__resident_id"


class ApplicationAdditionalLeaseHolders(GenericModel):
    application = models.ForeignKey(
        Application,
        related_name="application_additional_holders",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)
    email = models.EmailField()

    class Meta:
        path_to_location = "application__unit__floor__building__location"
        path_to_resident_id = "application__resident_id"
