import random
import datetime

from django.db import models, connection
from django.contrib.postgres.fields.array import ArrayField
from assets.models import Asset
from audit.models import GenericModel, optional
from common.models import Address
from common.constants import LOCKOUT_LIMIT
from helixauth.constants import SystemPlatform
from helixauth.models import HelixUser
from lookup.fields import LookupField
from residents.constants import (
    ResidentProfileType,
    ResidentEvictionDeliveryMethodType,
    ResidentEvictionStatusType,
)
from residents.managers.patientobject import ResidentObjectManager
from residents.managers.emergencycontact import EmergencyContactManager


class Resident(GenericModel):
    user = models.OneToOneField(
        HelixUser, on_delete=models.CASCADE, related_name="resident"
    )
    last_login = models.DateTimeField(**optional)
    ssn = models.CharField(max_length=50, **optional)
    resident_id = models.CharField(unique=True, **optional)
    profile_type = models.CharField(
        default=ResidentProfileType.TENANT.value,
        choices=ResidentProfileType.choices(),
        max_length=200,
    )
    sms_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    profile_image = models.ForeignKey(Asset, on_delete=models.DO_NOTHING, **optional)
    locked = models.BooleanField(default=False)
    failed_attempt_count = models.IntegerField(default=0)
    locked_at = models.DateTimeField(**optional)
    communication_mode = ArrayField(
        LookupField(max_length=200, lookup_name="COMMUNICATION_MODE"),
        default=[],
        **optional,
    )
    emergency_alerts_communication = ArrayField(
        LookupField(max_length=200, lookup_name="COMMUNICATION_MODE"),
        default=[],
        **optional,
    )
    maintenance_communication = ArrayField(
        LookupField(max_length=200, lookup_name="COMMUNICATION_MODE"),
        default=[],
        **optional,
    )
    rent_notices_communication = ArrayField(
        LookupField(max_length=200, lookup_name="COMMUNICATION_MODE"),
        default=[],
        **optional,
    )

    objects = ResidentObjectManager()

    class Meta:
        path_to_location = "leases__unit__floor__building__location"
        path_to_resident_id = "id"

    def __str__(self):
        return self.name

    @property
    def is_anonymous(self):
        return False

    def get_username(self):
        return str(self.id)

    @property
    def name(self):
        name = ""
        if self.user.first_name:
            name = "%s" % (self.user.first_name)
        if self.user.middle_name:
            name = "%s %s" % (name, self.user.middle_name)
        if self.user.last_name:
            name = "%s %s" % (name, self.user.last_name)
        return name

    @property
    def is_authenticated(self):
        return True

    @property
    def country_code(self):
        return self.user.country_code

    @property
    def phone(self):
        return self.user.phone

    def save(self, *args, **kwargs):
        if self._state.adding and not self.resident_id:
            from residents.managers.patient import ResidentManager

            self.resident_id = ResidentManager.generate_resident_id(
                first_name=self.user.first_name, last_name=self.user.last_name
            )
        super(Resident, self).save(*args, **kwargs)

    @property
    def age(self):
        today = datetime.date.today()
        if self.dob:
            return (
                today.year
                - self.dob.year
                - ((today.month, today.day) < (self.dob.month, self.dob.day))
            )
        return None


class ResidentAddress(GenericModel, Address):
    resident = models.ForeignKey(Resident, on_delete=models.SET_NULL, **optional)
    is_primary = models.BooleanField(default=False)

    class Meta:
        path_to_location = "resident__leases__unit__floor__building__location"
        path_to_resident_id = "resident__id"


class EmergencyContact(GenericModel, Address):
    resident = models.ForeignKey(Resident, on_delete=models.SET_NULL, **optional)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, **optional)
    last_name = models.CharField(max_length=100)
    home_country_code = models.CharField(max_length=5, default="+1", **optional)
    home_no = models.CharField(max_length=20, **optional)
    work_country_code = models.CharField(max_length=5, default="+1", **optional)
    work_no = models.CharField(max_length=20, **optional)
    cell_country_code = models.CharField(max_length=5, default="+1", **optional)
    cell_no = models.CharField(max_length=20, **optional)
    email = models.EmailField(**optional)
    is_primary = models.BooleanField(default=False)
    gender = LookupField(lookup_name="GENDER_TYPE", max_length=30)
    relationship = LookupField(
        max_length=200, lookup_name="RESIDENT_RELATIONSHIP", **optional
    )
    active = models.BooleanField(default=True)
    objects = EmergencyContactManager()

    class Meta:
        path_to_location = "resident__leases__unit__floor__building__location"
        path_to_resident_id = "resident__id"
        # unique_together = (("patient", "email"),)


class ResidentDocument(GenericModel):
    resident = models.ForeignKey(Resident, on_delete=models.DO_NOTHING)
    document_type = LookupField(max_length=40, lookup_name="IDENTITY_LIST")
    front_image = models.ForeignKey(
        Asset,
        on_delete=models.DO_NOTHING,
        related_name="resident_document_front_image",
        **optional,
    )
    back_image = models.ForeignKey(
        Asset,
        on_delete=models.DO_NOTHING,
        related_name="resident_document_back_image",
        **optional,
    )
    document_data = models.CharField(max_length=255, **optional)
    is_primary = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    class Meta:
        path_to_resident_id = "resident__id"
        path_to_location = "resident__leases__unit__floor__building__location"


class ResidentFamily(GenericModel):
    patient = models.ForeignKey(
        Resident, on_delete=models.CASCADE, related_name="related_resident"
    )
    member = models.ForeignKey(
        Resident, on_delete=models.CASCADE, related_name="patient_family"
    )
    relationship = LookupField(
        max_length=200, lookup_name="RESIDENT_RELATIONSHIP", **optional
    )
    # patient is "relationship" of family. Example: Patient P1 is "FATHER" of Family Patient p2

    class Meta:
        unique_together = (("patient", "member"),)


class ResidentRegisteredDevice(GenericModel):
    user = models.ForeignKey(Resident, on_delete=models.CASCADE)
    make = models.CharField(max_length=255)  # Windows
    model = models.CharField(max_length=255)  # Desktop-i3
    mac_address = models.CharField(max_length=255)  # Unique device id or browser id
    os_detail = models.CharField(max_length=255)  # Google Chrome
    last_ip_address = models.CharField(max_length=255)
    last_location = models.JSONField(**optional)
    device_token = models.CharField(max_length=1024, unique=True, **optional)
    device_fingerprint = models.CharField(
        max_length=255, **optional
    )  # Unique device fingerprint
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = [
            ("user", "make", "model", "mac_address"),  # Backward compatibility
            ("user", "device_fingerprint"),  # New approach using fingerprint
        ]

    @property
    def platform(self):
        _make = self.make.lower()
        _os_detail = self.os_detail.lower()

        _windows_lower = SystemPlatform.WINDOWS.value.lower()
        _android_lower = SystemPlatform.ANDROID.value.lower()
        _ios_lower = SystemPlatform.IOS.value.lower()
        _webapp_lower = SystemPlatform.WEBAPP.value.lower()

        if _windows_lower in _make or _windows_lower in _os_detail:
            return SystemPlatform.WINDOWS.value

        if _android_lower in _make or _android_lower in _os_detail:
            return SystemPlatform.ANDROID.value

        if _ios_lower in _make or _ios_lower in _os_detail:
            return SystemPlatform.IOS.value

        if _webapp_lower in _make or _webapp_lower in _os_detail:
            return SystemPlatform.WEBAPP.value


class ResidentAccessLog(GenericModel):
    ACCESS_STATUS_CHOICES = (
        ("success", "Successful Sign-In"),
        ("failure", "Unsuccessful Sign-In"),
    )
    user = models.ForeignKey(Resident, on_delete=models.CASCADE)
    device = models.ForeignKey(ResidentRegisteredDevice, on_delete=models.CASCADE)
    refresh_jti = models.CharField(max_length=255, **optional)
    refresh_exp = models.DateTimeField(**optional)
    refresh_token = models.TextField(**optional)
    ip_address = models.CharField(max_length=255)
    location = models.JSONField()
    login_status = models.CharField(
        max_length=20, choices=ACCESS_STATUS_CHOICES, default="success"
    )

    def save(self, *args, **kwargs):
        log = super(ResidentAccessLog, self).save(*args, **kwargs)
        user = self.user
        if self.login_status == "success":
            user.locked = False
            user.failed_attempt_count = 0
            user.save()
            return log
        tenant = connection.get_tenant()
        count = tenant.lockout_limit if tenant else LOCKOUT_LIMIT
        if user.failed_attempt_count + 1 >= count:
            user.locked = True
            user.locked_at = datetime.datetime.now()
        user.failed_attempt_count = user.failed_attempt_count + 1
        user.save()
        return log


class ResidentCoOccupants(GenericModel, Address):
    resident = models.ForeignKey(Resident, on_delete=models.SET_NULL, **optional)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, **optional)
    last_name = models.CharField(max_length=100)
    phone_country_code = models.CharField(max_length=5, default="+1", **optional)
    phone = models.CharField(max_length=20, **optional)
    include_in_notice = models.BooleanField(default=False, **optional)
    relationship = LookupField(max_length=10, lookup_name="OCCUPANTS_RELATIONSHIP")

    class Meta:
        path_to_resident_id = "resident__id"
        path_to_location = "resident__leases__unit__floor__building__location"


class ResidentFinancialGurantors(GenericModel, Address):
    resident = models.ForeignKey(Resident, on_delete=models.SET_NULL, **optional)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, **optional)
    last_name = models.CharField(max_length=100)
    phone_country_code = models.CharField(max_length=5, default="+1", **optional)
    phone = models.CharField(max_length=20, **optional)
    include_in_notice = models.BooleanField(default=False, **optional)
    is_primary = models.BooleanField(default=False, **optional)
    relationship = LookupField(max_length=10, lookup_name="OCCUPANTS_RELATIONSHIP")
    communication_mode = ArrayField(
        LookupField(max_length=200, lookup_name="COMMUNICATION_MODE"),
        default=[],
        **optional,
    )
    languages_known = ArrayField(
        LookupField(max_length=50, lookup_name="LANGUAGE"), default=list, **optional
    )

    class Meta:
        path_to_resident_id = "resident__id"
        path_to_location = "resident__leases__unit__floor__building__location"


class ResidentEviction(GenericModel):
    notice_id = models.CharField(max_length=10, unique=True, editable=False)
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    select_reason = ArrayField(
        LookupField(max_length=200, lookup_name="EVICTION_REASON"),
        default=[],
        **optional,
    )
    custom_reason = models.CharField(
        max_length=255,
        **optional,
        help_text="Specify reason if 'Other' is selected",
    )
    notice_title = models.CharField(max_length=255, **optional)
    description = models.TextField(**optional)
    notice_date = models.DateField()
    vacate_by_date = models.DateField()

    attachment = models.ManyToManyField(
        Asset, related_name="resident_eviction_document", **optional
    )
    is_resolved = models.BooleanField(default=False)
    resolved_on = models.DateField(**optional)
    delivery_method = ArrayField(
        models.CharField(
            default=ResidentEvictionDeliveryMethodType.EMAIL_NOTIFICATION.value,
            choices=ResidentEvictionDeliveryMethodType.choices(),
            max_length=30,
        )
    )
    status = models.CharField(
        default=ResidentEvictionStatusType.PENDING.value,
        choices=ResidentEvictionStatusType.choices(),
        max_length=20,
    )
    reject_reason = LookupField(
        max_length=100, lookup_name="MAINTENANCE_REJECT_REASON", **optional
    )
    reject_date = models.DateField(**optional)
    reject_notes = models.TextField(**optional)

    def clean(self):
        from django.core.exceptions import ValidationError

        if "OTHER" in (self.select_reason or []) and not self.custom_reason:
            raise ValidationError({"custom_reason": "Please specify a custom reason."})

    def __str__(self):
        return f"{self.notice_title} - {self.resident}"

    def save(self, *args, **kwargs):
        if not self.notice_id:
            self.notice_id = self.generate_notice_id()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_notice_id():
        """Generate a unique 5–6 digit eviction notice ID like EN12345"""
        while True:
            # 5–6 digit random number
            random_num = random.randint(10000, 999999)
            notice_id = f"EN-{random_num}"
            if not ResidentEviction.objects.filter(notice_id=notice_id).exists():
                return notice_id

    class Meta:
        path_to_resident_id = "resident__id"
        path_to_location = "resident__leases__unit__floor__building__location"
