from djmoney.models.fields import MoneyField
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils import timezone
from django.core.files.base import ContentFile
from assets.models import Asset
from audit.models import GenericModel
from helixauth.models import Policy
from lookup.fields import LookupField
from locations.constants import (
    UnitStatus,
    UnitType,
    SlotAvailabilityType,
    SlotType,
)
from lease.constants import SmokingStatus, ExtraParkingType, ESAType
from common.constants import ACTION_CHOICES, YES
from common.errors import ERROR_DETAILS
from common.models import Address, Contact, Phone, BillingAddress, PetSpecies, PetBreed
from common.utils.general import (
    get_title_string,
    validate_case_insensitive_unique,
    get_display_id,
)
from locations.managers.object.pl import PracticeLocationObjectManager
import logging

logger = logging.getLogger(__name__)


# Create your models here.
optional = {"null": True, "blank": True}


class Customer(GenericModel, Address, Contact, Phone):
    display_id = models.CharField(max_length=100, **optional)
    name = models.CharField(max_length=100, unique=True)
    short_name = models.CharField(max_length=100, **optional)
    max_security_question = models.IntegerField(default=10)
    email = models.EmailField(max_length=100)
    status = models.CharField(max_length=10, choices=ACTION_CHOICES, default=YES)
    is_active = models.BooleanField(default=True)
    customer_url = models.CharField(max_length=100, **optional)
    image = models.ForeignKey(Asset, on_delete=models.DO_NOTHING, **optional)
    logo = models.ForeignKey(
        Asset, on_delete=models.DO_NOTHING, related_name="customer_logo", **optional
    )
    favicon = models.ForeignKey(
        Asset, on_delete=models.DO_NOTHING, related_name="customer_favicon", **optional
    )
    brand_color = models.CharField(default="#3B1550", max_length=10)
    inactive_on = models.DateTimeField(**optional)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.display_id = get_display_id(self, "CUST")

        # Update inactive_on when is_active status changes
        if self.pk:
            try:
                previous = Customer.objects.get(pk=self.pk)
                # If is_active changed from True to False, set inactive_on
                if previous.is_active and not self.is_active:
                    self.inactive_on = timezone.now()
                # If is_active changed from False to True, clear inactive_on
                elif not previous.is_active and self.is_active:
                    self.inactive_on = None
            except Customer.DoesNotExist:
                pass

        super(Customer, self).save(*args, **kwargs)

    class Meta:
        path_to_location = "property__location"


class Property(GenericModel, Address, Contact, Phone, BillingAddress):
    name = models.CharField(
        max_length=100,
        unique=True,
        error_messages={
            "unique": ERROR_DETAILS["health_center_exists"],
        },
    )
    short_name = models.CharField(max_length=100, **optional)
    customer = models.ForeignKey(
        Customer, on_delete=models.DO_NOTHING, related_name="property"
    )
    email = models.EmailField(max_length=100, **optional)
    image = models.ForeignKey(Asset, on_delete=models.DO_NOTHING, **optional)
    url = models.URLField(max_length=100, **optional)
    display_id = models.CharField(max_length=100, **optional)
    brand_color = models.CharField(default="#3B1550", max_length=10, **optional)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "%s" % (self.name)

    @property
    def speciality_codes(self):
        return list(self.specialities.all().values_list("code", flat=True))

    def clean(self):
        super().clean()
        validate_case_insensitive_unique(self.name, Property, "name", self)

    def _send_creation_notification(self):
        """Send async email notification for property creation via NotificationQueue."""
        # Import here to avoid circular import
        from notifications.models import NotificationSetting, NotificationQueue
        from notifications.managers.notification import NotificationsManager
        from notifications.constants import TemplateCode

        if not self.contact_email:
            return

        try:
            notification_setting = NotificationSetting.objects.filter(
                notification_type="EMAIL"
            ).first()

            if not notification_setting:
                logger.warning(
                    f"No EMAIL NotificationSetting found. Cannot queue notification "
                    f"for property {self.id}"
                )
                return

            # Prepare template context
            template_context = {
                "property_name": self.name or "N/A",
                "display_id": self.display_id or "N/A",
                "customer_name": self.customer.name if self.customer else "N/A",
                "contact_first_name": self.contact_first_name or "",
                "contact_last_name": self.contact_last_name or "",
                "contact_email": self.contact_email or "",
                "contact_phone": self.phone or "",
                "created_by": (
                    f"{self.created_by.first_name} {self.created_by.last_name}"
                    if self.created_by
                    else "System"
                ),
                "created_on": (
                    self.created_on.strftime("%B %d, %Y at %I:%M %p")
                    if self.created_on
                    else "N/A"
                ),
            }

            # Load and render HTML template
            template_code = TemplateCode.EMAIL_PROPERTY_CREATED.value
            template_content = NotificationsManager._load_template(template_code)
            html_content = NotificationsManager._render_template(
                template_content, template_context
            )
            subject = NotificationsManager._get_subject_for_template(template_code)

            # Create notification queue entry - will be picked up by send_notification task
            NotificationQueue.objects.create(
                notification_setting=notification_setting,
                receiving_address=self.contact_email,
                payload={
                    "subject": subject,
                    "message": html_content,
                    "html_message": html_content,
                },
                status=3,  # Pending
                priority=2,  # Medium priority
            )

        except Exception as e:
            logger.error(
                f"Failed to queue property creation notification for property "
                f"{self.id}: {str(e)}"
            )

    def save(self, *args, **kwargs):
        is_new = self._state.adding  # Use Django's internal flag for UUID models
        self.clean()
        field_list = [
            "name",
            "first_name",
            "middle_name",
            "last_name",
            "billing_contact_first_name",
            "billing_contact_last_name",
        ]
        for field_name in field_list:
            field_value = getattr(self, field_name, None)
            if field_value is not None:
                title_field_value = get_title_string(field_value)
                setattr(self, field_name, title_field_value)

        self.display_id = get_display_id(self, "PROP")
        super(Property, self).save(*args, **kwargs)

        if is_new:
            self._send_creation_notification()

    class Meta:
        unique_together = ("name", "customer")
        path_to_resident_id = "location__building__floor__unit__lease__resident_id"


class Location(GenericModel, Address, Contact, Phone, BillingAddress):
    name = models.CharField(max_length=100, unique=True)
    short_name = models.CharField(max_length=100, **optional)
    url = models.URLField(**optional)
    email = models.EmailField(**optional)
    image = models.ForeignKey(Asset, on_delete=models.DO_NOTHING, **optional)
    payable_to = models.CharField(
        max_length=512, **optional
    )  # name will appear in bill
    latlng = gis_models.PointField(**optional)  # POINT(Longitude Latitudate)
    notes = models.TextField(**optional)
    property = models.ForeignKey(
        Property,
        related_name="location",
        on_delete=models.DO_NOTHING,
    )
    display_id = models.CharField(**optional, max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "%s" % (self.name)

    def _send_creation_notification(self):
        """Send async email notification for location creation via NotificationQueue."""
        # Import here to avoid circular import
        from notifications.models import NotificationSetting, NotificationQueue
        from notifications.managers.notification import NotificationsManager
        from notifications.constants import TemplateCode

        if not self.contact_email:
            return

        try:
            notification_setting = NotificationSetting.objects.filter(
                notification_type="EMAIL"
            ).first()

            if not notification_setting:
                logger.warning(
                    f"No EMAIL NotificationSetting found. Cannot queue notification "
                    f"for location {self.id}"
                )
                return

            # Prepare template context (use correct field names: address, address_1)
            template_context = {
                "location_name": self.name or "N/A",
                "display_id": self.display_id or "N/A",
                "property_name": self.property.name if self.property else "N/A",
                "contact_first_name": self.contact_first_name or "",
                "contact_last_name": self.contact_last_name or "",
                "contact_email": self.contact_email or "",
                "contact_phone": self.phone or "",
                "address_line1": self.address or "",
                "address_line2": self.address_1 or "",
                "city": self.city or "",
                "state": self.state or "",
                "zipcode": self.zipcode or "",
                "created_by": (
                    f"{self.created_by.first_name} {self.created_by.last_name}"
                    if self.created_by
                    else "System"
                ),
                "created_on": (
                    self.created_on.strftime("%B %d, %Y at %I:%M %p")
                    if self.created_on
                    else "N/A"
                ),
            }

            # Load and render HTML template
            template_code = TemplateCode.EMAIL_LOCATION_CREATED.value
            template_content = NotificationsManager._load_template(template_code)
            html_content = NotificationsManager._render_template(
                template_content, template_context
            )
            subject = NotificationsManager._get_subject_for_template(template_code)

            # Create notification queue entry - will be picked up by send_notification task
            NotificationQueue.objects.create(
                notification_setting=notification_setting,
                receiving_address=self.contact_email,
                payload={
                    "subject": subject,
                    "message": html_content,
                    "html_message": html_content,
                },
                status=3,  # Pending
                priority=2,  # Medium priority
            )

        except Exception as e:
            logger.error(
                f"Failed to queue location creation notification for location "
                f"{self.id}: {str(e)}"
            )

    def save(self, *args, **kwargs):
        is_new = self._state.adding  # Use Django's internal flag for UUID models
        field_list = [
            "name",
            "contact__first_name",
            "contact__middle_name",
            "contact__last_name",
            "billing_contact_first_name",
            "billing_contact_last_name",
        ]
        for field_name in field_list:
            field_value = getattr(self, field_name, None)
            if field_value is not None:
                title_field_value = get_title_string(field_value)
                setattr(self, field_name, title_field_value)

        self.display_id = get_display_id(self, "LOCA")
        super(Location, self).save(*args, **kwargs)

        if is_new:
            self._send_creation_notification()

    objects = PracticeLocationObjectManager()

    class Meta:
        unique_together = ("name", "property")
        path_to_location = "id"
        path_to_resident_id = "building__floor__unit__lease__resident_id"


class Building(GenericModel):
    display_id = models.CharField(max_length=100, **optional)
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="building"
    )
    name = models.CharField(max_length=255)
    total_floors = models.IntegerField()
    year_built = models.DateField(**optional)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = (("location", "name"),)
        path_to_location = "location"
        path_to_resident_id = "floor__unit__lease__resident_id"

    def save(self, *args, **kwargs):
        self.display_id = get_display_id(self, "BILD")
        return super().save(*args, **kwargs)


class Floor(GenericModel):
    display_id = models.CharField(max_length=100, **optional)
    building = models.ForeignKey(
        Building, on_delete=models.CASCADE, related_name="floor"
    )
    floor_number = models.CharField(max_length=255)
    description = models.TextField(**optional)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = (("building", "floor_number"),)
        path_to_location = "building__location"
        path_to_resident_id = "unit__lease__resident_id"

    def save(self, *args, **kwargs):
        self.display_id = get_display_id(self, "FLOR")
        return super().save(*args, **kwargs)


class Unit(GenericModel):
    display_id = models.CharField(max_length=100, **optional)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name="unit")
    unit_number = models.CharField(max_length=255)
    unit_type = models.CharField(max_length=50, choices=UnitType.choices())
    is_furnished = models.BooleanField(default=False)
    furnished_price = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    unfurnished_price = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    furnished_security_deposit = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    unfurnished_security_deposit = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    deposit_refundable = models.BooleanField(default=False)
    unit_capacity = models.IntegerField(**optional)
    max_unit_capacity = models.IntegerField(**optional)
    exceeding_occupancy_fee = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    hoa_fee = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    ownership = LookupField(max_length=50, lookup_name="OWNERSHIP", **optional)
    smoking_status = models.CharField(
        max_length=32, choices=SmokingStatus.choices(), **optional
    )
    extra_parking = models.BooleanField(default=False)
    allow_smoking = models.BooleanField(default=False)
    service_animal = models.CharField(
        max_length=32, choices=ESAType.choices(), **optional
    )
    parking_type = LookupField(max_length=32, lookup_name="PARKING_TYPE", **optional)
    extra_parking_type = models.CharField(
        max_length=32, choices=ExtraParkingType.choices(), **optional
    )
    max_extra_spaces_allowed = models.IntegerField(**optional)
    max_occupancy_limit = models.IntegerField(**optional)
    extra_parking_charges = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    parking_allowed_at_unit_level = models.BooleanField(default=False)
    parking_allowed_at_complex_level = models.BooleanField(default=False)
    parking_included_in_rent = models.BooleanField(default=False)
    additional_parking_cost = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    no_of_spaces_per_unit = models.IntegerField(**optional)
    guest_parking_available = models.BooleanField(default=False)
    accessible_parking_available = models.BooleanField(default=False)
    is_separate_parking_lease_required = models.BooleanField(default=False)
    parking_slots = models.ManyToManyField(
        "ParkingSlot", related_name="units", blank=True
    )
    parking_zone = models.ForeignKey(
        "ParkingZone",
        on_delete=models.SET_NULL,
        related_name="units_in_zone",
        **optional,
    )
    status = models.CharField(max_length=50, choices=UnitStatus.choices())
    unit_size = models.DecimalField(
        max_digits=14, decimal_places=2, **optional
    )  # units = sq ft
    floor_plan = LookupField(max_length=100, lookup_name="FLOOR_PLAN")
    is_pet_allowed = models.BooleanField(default=False)
    is_service_animal_allowed = models.BooleanField(default=False)
    pet_policies = models.ManyToManyField(
        Policy,
        related_name="units_with_pet_policies",
        blank=True,
    )
    pet_type = LookupField(max_length=50, lookup_name="PET_TYPE", **optional)

    pet_species = models.ForeignKey(
        PetSpecies, on_delete=models.SET_NULL, related_name="units", **optional
    )
    max_pets = models.IntegerField(**optional)
    lease_expiry_days = models.IntegerField(**optional)
    pet_max_weight = models.FloatField(**optional)
    pet_breed = models.ForeignKey(
        PetBreed, on_delete=models.SET_NULL, related_name="units", **optional
    )
    pet_agressive_breed_allowed = models.BooleanField(**optional)
    pet_fees_type = LookupField(max_length=100, lookup_name="PET_FEE_TYPE", **optional)
    pet_fees_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    pet_security_deposit_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    pet_security_deposit_refundable = models.BooleanField(default=False)
    admin_charges_applicable = models.BooleanField(default=False)
    violation_policies = models.ManyToManyField(
        Policy,
        related_name="units_with_violation_policies",
        blank=True,
    )
    images = models.ManyToManyField(Asset, **optional)
    is_active = models.BooleanField(default=True)
    pdf_asset = models.ForeignKey(
        Asset,
        on_delete=models.SET_NULL,
        related_name="unit_pdf",
        null=True,
        blank=True,
        help_text="Auto-generated unit PDF",
    )

    class Meta:
        unique_together = (("floor", "unit_number"),)
        path_to_location = "floor__building__location"
        path_to_resident_id = "lease__resident_id"

    def _generate_pdf(self):
        """Generate PDF for the unit"""
        try:
            # Generate the PDF
            from locations.services.pdf_generator import UnitPDFGenerator

            pdf_generator = UnitPDFGenerator(self)
            pdf_buffer = pdf_generator.generate()
            _pdf_size = len(pdf_buffer.getvalue())

            # Prepare filename
            unit_id = str(self.id)[:8]
            filename = f"unit_{unit_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"

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
                    type="doc", file=None, filename=filename
                )
                pdf_asset.file.save(filename, pdf_content, save=False)
                pdf_asset.save()
                self.pdf_asset = pdf_asset
                # Save the unit to persist the pdf_asset reference (using update to avoid recursion)
                Unit.objects.filter(pk=self.pk).update(pdf_asset=pdf_asset)
                action = "created"

            msg = f"Unit PDF {action} for unit {self.id}"
            logger.info(msg)

        except Exception as e:
            error_msg = f"Error generating PDF for unit {self.id}: {str(e)}"
            logger.error(error_msg, exc_info=True)

    def save(self, *args, **kwargs):
        self.display_id = get_display_id(self, "UNIT")
        super().save(*args, **kwargs)
        # Generate PDF after saving
        self._generate_pdf()


class UnitAdministrationCharge(GenericModel):
    unit = models.ForeignKey(
        Unit, on_delete=models.CASCADE, related_name="administration_charges"
    )
    charge_name = models.CharField(max_length=255)
    charge_amount = MoneyField(max_digits=14, decimal_places=2, default_currency="USD")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return f"{self.unit.unit_number} - {self.charge_name}: {self.charge_amount}"


class Amenity(GenericModel):
    display_id = models.CharField(max_length=100, **optional)
    building = models.ForeignKey(
        Building, on_delete=models.CASCADE, related_name="amenities"
    )
    name = models.CharField(max_length=255)
    capacity = models.IntegerField()
    images = models.ManyToManyField(Asset, **optional)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = (("building", "name"),)
        path_to_location = "building__location"

    def save(self, *args, **kwargs):
        self.display_id = get_display_id(self, "AMNT")
        return super().save(*args, **kwargs)


class ParkingLevel(GenericModel):
    building = models.ForeignKey(
        Building, on_delete=models.CASCADE, related_name="parking_levels"
    )
    level_name = models.CharField(max_length=100)
    level_type = LookupField(max_length=50, lookup_name="PARKING_LEVEL_TYPE")
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("building", "level_name")
        path_to_location = "building__location"

    def __str__(self):
        return f"{self.level_name} - {self.building.name}"

    @property
    def total_zones(self):
        return self.zones.count()


class ParkingZone(GenericModel):
    parking_level = models.ForeignKey(
        ParkingLevel, on_delete=models.CASCADE, related_name="zones"
    )
    name = models.CharField(max_length=100)
    zone_type = models.CharField(max_length=50, **optional)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("parking_level", "name")
        path_to_location = "parking_level__building__location"

    def __str__(self):
        return f"{self.name} - {self.parking_level.level_name}"

    @property
    def total_slots(self):
        return self.slots.count()


class ParkingSlot(GenericModel):
    zone = models.ForeignKey(
        ParkingZone, on_delete=models.CASCADE, related_name="slots"
    )
    slot_no = models.CharField(max_length=20)
    slot_type = models.CharField(max_length=50, choices=SlotType.choices())
    availability = models.CharField(
        max_length=50, choices=SlotAvailabilityType.choices()
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = (("zone", "slot_no"),)
        path_to_location = "zone__parking_level__building__location"

    def __str__(self):
        return f"{self.slot_no} ({self.zone.name})"
