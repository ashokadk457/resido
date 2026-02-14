import os
import pytz
from uuid import uuid4
from Crypto.PublicKey import RSA

from django.db import models
from django.utils.deconstruct import deconstructible
from django_tenants.models import DomainMixin
from rest_framework.serializers import ValidationError

from audit.models import GenericModel
from common.constants import (
    ACTION_CHOICES,
    YES,
    LOCKOUT_LIMIT,
    LOCKOUT_RELEASE_IN_MINS,
)
from common.errors import ERROR_DETAILS
from common.managers.domain import DomainManager
from lookup.fields import LookupField
from hb_core.constants import UTC_TIMEZONE
from customer_backend.mixins.tenant import BaseTenantMixin

optional = {"null": True, "blank": True}


@deconstructible
class PathAndRename(object):
    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split(".")[-1]
        # get filename
        if instance.pk:
            filename = "{}.{}".format(instance.pk, ext)
        else:
            # set filename as random string
            filename = "{}.{}".format(uuid4().hex, ext)
        # return the whole path to the file
        return os.path.join(self.path, filename)


class GenericDisplayModel(GenericModel):
    display_id = models.CharField(max_length=512, unique=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        from common.utils.general import get_display_id

        self.display_id = get_display_id(self)
        return super(GenericDisplayModel, self).save(*args, **kwargs)


class Country(GenericModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=2, unique=True, **optional)
    is_active = models.BooleanField(default=False)
    MODEL_ALL_DATA_CACHE_KEY = "COUNTRY"

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class State(GenericModel):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name="states"
    )
    state_code = models.CharField(max_length=10, **optional)
    is_active = models.BooleanField(default=False)
    MODEL_ALL_DATA_CACHE_KEY = "STATE"

    class Meta:
        unique_together = (
            ("name", "country"),
            ("name", "state_code"),
            ("country", "state_code"),
        )

    def __str__(self):
        return f"{self.name}, {self.country.name}"


class PetSpecies(GenericModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    MODEL_ALL_DATA_CACHE_KEY = "PET_SPECIES"

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Pet Species"

    def __str__(self):
        return self.name


class PetBreed(GenericModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    species = models.ForeignKey(
        PetSpecies, on_delete=models.CASCADE, related_name="breeds"
    )
    is_active = models.BooleanField(default=True)
    MODEL_ALL_DATA_CACHE_KEY = "PET_BREED"

    class Meta:
        unique_together = (("name", "species"), ("code", "species"))
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.species.name})"


def validate_country_state(instance, country_field_name, state_field_name):
    country_obj = None
    country_val = getattr(instance, country_field_name)
    state_val = getattr(instance, state_field_name)
    if country_val:
        country_objs = Country.objects.filter_from_cache(code=country_val)
        if len(country_objs) == 0:
            raise ValidationError(
                detail=ERROR_DETAILS["invalid_value"].format(attr=country_field_name),
                code="invalid_value",
            )
        country_obj = country_objs[0]
    if state_val:
        if not country_obj:
            raise ValidationError(
                detail=ERROR_DETAILS["missing_required_param"].format(
                    param=country_field_name
                ),
                code="missing_required_param",
            )
        if not State.objects.filter_from_cache(
            state_code=state_val, country=country_obj.get("id")
        ):
            raise ValidationError(
                detail=ERROR_DETAILS["invalid_value"].format(attr="billing_state"),
                code="invalid_value",
            )


class Address(models.Model):
    address = models.CharField(max_length=512, **optional)
    address_1 = models.CharField(max_length=512, **optional)
    city = models.CharField(max_length=50, **optional)
    state = models.CharField(max_length=50, **optional)
    zipcode = models.CharField(max_length=10, **optional)
    country = LookupField(max_length=10, lookup_name="COUNTRY", **optional)

    class Meta:
        abstract = True

    def clean(self):
        validate_country_state(self, "country", "state")
        return super().clean()


class BillingAddress(models.Model):
    billing_contact_first_name = models.CharField(max_length=255, **optional)
    billing_contact_last_name = models.CharField(max_length=255, **optional)
    billing_address = models.CharField(max_length=512, **optional)
    billing_address_1 = models.CharField(max_length=512, **optional)
    billing_city = models.CharField(max_length=50, **optional)
    billing_state = models.CharField(max_length=50, **optional)
    billing_zipcode = models.CharField(max_length=10, **optional)
    billing_country = LookupField(max_length=10, lookup_name="COUNTRY", **optional)

    class Meta:
        abstract = True


class SecondAddress(models.Model):
    second_address = models.CharField(max_length=512, **optional)
    second_address_1 = models.CharField(max_length=512, **optional)
    second_city = models.CharField(max_length=50, **optional)
    second_state = models.CharField(max_length=50, **optional)
    second_zipcode = models.CharField(max_length=10, **optional)
    second_country = LookupField(max_length=10, lookup_name="COUNTRY", **optional)

    def clean(self):
        validate_country_state(self, "billing_country", "billing_state")
        return super().clean()

    class Meta:
        abstract = True


class Contact(models.Model):
    contact_prefix = LookupField(
        max_length=100, default="Mr", lookup_name="PREFIX", **optional
    )
    contact_first_name = models.CharField(max_length=100, **optional)
    contact_middle_name = models.CharField(max_length=100, **optional)
    contact_last_name = models.CharField(max_length=100, **optional)
    contact_email = models.EmailField(max_length=100, **optional)
    contact_suffix = LookupField(max_length=100, lookup_name="SUFFIX", **optional)

    class Meta:
        abstract = True


class Phone(models.Model):
    work_country_code = models.CharField(max_length=5, default="+1", **optional)
    work_phone = models.CharField(max_length=255, **optional)
    phone_country_code = models.CharField(max_length=5, default="+1", **optional)
    phone = models.CharField(max_length=255, **optional)
    home_phone_country_code = models.CharField(max_length=5, default="+1", **optional)
    home_phone = models.CharField(max_length=255, **optional)
    fax_country_code = models.CharField(max_length=5, default="+1", **optional)
    fax = models.CharField(max_length=255, **optional)

    class Meta:
        abstract = True


class PhoneEmail(Phone):
    email = models.EmailField(**optional)

    class Meta:
        abstract = True


class HealthCareCustomer(BaseTenantMixin, Contact):
    MODEL_ALL_DATA_CACHE_KEY = "TENANTS"

    CONF_CHOICE = ((1, "Auto"), (2, "Manual"))

    COMMU_CHOICE = (
        ("EM", "Email"),
        ("WP", "Work phone"),
        ("CP", "Cell phone"),
        ("FAX", "Fax"),
        ("ML", "Mail"),
        ("ALL", "All"),
    )

    name = models.CharField(max_length=100)
    brand_color = models.CharField(default="#3B1550", max_length=10)
    slogan = models.CharField(**optional)
    description = models.TextField(**optional)
    app_conf_type = models.IntegerField(choices=CONF_CHOICE, default=1)
    url = models.CharField(max_length=100)
    max_security_question = models.IntegerField(default=10)
    code = models.IntegerField(unique=True)
    website = models.URLField(null=True, blank=True)
    email = models.CharField(max_length=100, **optional)
    preferred_communication_mode = models.CharField(
        choices=COMMU_CHOICE, default="ÁLL", max_length=10
    )
    status = models.CharField(max_length=100, choices=ACTION_CHOICES, default=YES)
    s2s_private_key = models.TextField(null=True)
    s2s_public_key = models.TextField(null=True)
    max_age_of_minor = models.IntegerField(default=12)
    lockout_limit = models.IntegerField(default=LOCKOUT_LIMIT)
    lockout_release_duration = models.IntegerField(default=LOCKOUT_RELEASE_IN_MINS)
    realm = models.CharField(max_length=100, **optional)
    client_id = models.CharField(max_length=100, **optional)
    client_secret = models.CharField(max_length=100, **optional)
    client_uuid = models.CharField(max_length=100, **optional)
    realm_admin = models.CharField(max_length=100, **optional)
    realm_password = models.CharField(max_length=100, **optional)

    def __str__(self):
        return "{}: ({})".format(self.name, self.schema_name)

    auto_create_schema = True

    def get_timezone_obj(self):
        if self.timezone is None:
            return UTC_TIMEZONE

        return pytz.timezone(self.timezone)

    @property
    def is_anonymous(self):
        return False

    def get_username(self):
        return str(self.id)

    def save(self, **kwargs):
        if not self.code:
            max_code = HealthCareCustomer.objects.aggregate(
                max_code=models.Max("code")
            )["max_code"]
            self.code = (max_code or 1000) + 1

        if not self.s2s_private_key or not self.s2s_public_key:
            key = RSA.generate(2048)
            private_key = key.export_key()
            public_key = key.publickey().export_key()
            self.s2s_private_key = private_key.decode()
            self.s2s_public_key = public_key.decode()
        return super().save(**kwargs)

    @property
    def domain(self):
        return (
            self.domains.filter(is_primary=True).first().domain
            if self.domains.filter(is_primary=True).first()
            else None
        )

    # def get_effective_brand_color_for_helix_staff(self, helix_staff):
    #     if helix_staff.primary_location and helix_staff.primary_location.brand_color:
    #         return helix_staff.primary_location.brand_color

    #     if (
    #         helix_staff.primary_location
    #         and helix_staff.primary_location.health_center
    #         and helix_staff.primary_location.health_center.brand_color
    #     ):
    #         return helix_staff.primary_location.health_center.brand_color

    #     return self.brand_color

    # def get_effective_logo_for_helix_staff(self, helix_staff):
    #     if helix_staff.primary_location and helix_staff.primary_location.image:
    #         return helix_staff.primary_location.image

    #     if (
    #         helix_staff.primary_location
    #         and helix_staff.primary_location.health_center
    #         and helix_staff.primary_location.health_center.image
    #     ):
    #         return helix_staff.primary_location.health_center.image

    #     if hasattr(self, 'asset') and self.asset and self.asset.logo:
    #         return self.asset.logo

    #     return None


class Domain(DomainMixin):
    objects = DomainManager()


class HealthCareCustomerConfig(GenericModel):
    """
    Tenant configuration for property management platform

    This model stores tenant-specific configuration settings that are
    determined by their subscription plan and module composition.

    Fields are named to maintain compatibility with customer_backend package,
    but are used for property management features in RESIDO.
    """

    customer = models.OneToOneField(
        HealthCareCustomer, on_delete=models.CASCADE, related_name="config"
    )

    # Property management feature flags
    # These fields are set based on subscribed modules during tenant launch
    is_payment_processing_enabled = models.BooleanField(default=False)
    is_maintenance_module_enabled = models.BooleanField(default=False)
    is_booking_module_enabled = models.BooleanField(default=False)
    is_analytics_enabled = models.BooleanField(default=False)
    is_digital_forms_enabled = models.BooleanField(default=False)

    # Notification settings
    notification_preferences = models.JSONField(default=dict, **optional)

    # Billing and payment configuration
    payment_grace_period_days = models.IntegerField(default=5)
    late_fee_enabled = models.BooleanField(default=False)
    auto_payment_reminder_days = models.IntegerField(default=3)

    # Maintenance request settings
    maintenance_auto_assignment_enabled = models.BooleanField(default=False)
    maintenance_sla_hours = models.IntegerField(default=24)

    # Resident portal settings
    resident_portal_enabled = models.BooleanField(default=True)
    self_service_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"Config for {self.customer.name}"

    class Meta:
        verbose_name = "Tenant Configuration"
        verbose_name_plural = "Tenant Configurations"


# Subscription models moved to subscriptions app (SHARED_APP)
