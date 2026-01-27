import datetime
import uuid

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
)
from django.contrib.postgres.fields.array import ArrayField
from django.db import models, connection

from audit.models import GenericModel
from common.models import Address, SecondAddress, HealthCareCustomer
from assets.models import Asset
from common.constants import OTPChannels, LOCKOUT_LIMIT
from common.utils.fields import SafeCharField
from helixauth.constants import AccessLevel, AddressTypes, SystemPlatform
from helixauth.managers.user.object import HelixUserObjectManager
from helixauth.managers.object.user_role import UserRoleObjectManager
from lookup.fields import LookupField

optional = {"null": True, "blank": True}


class HealthCareCustomerAsset(GenericModel):
    customer = models.OneToOneField(
        HealthCareCustomer, related_name="asset", on_delete=models.DO_NOTHING
    )
    logo = models.ForeignKey(
        Asset, on_delete=models.DO_NOTHING, related_name="tenant_logo", **optional
    )
    favicon = models.ForeignKey(
        Asset, on_delete=models.DO_NOTHING, related_name="tenant_favicon", **optional
    )


class UserGroup(GenericModel):
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)


class UserRole(GenericModel):
    role_name = models.CharField(max_length=60, unique=True)
    description = models.CharField(max_length=255)
    is_role_active = models.BooleanField(default=True)
    seeded = models.BooleanField(default=False)
    group = models.ForeignKey(
        UserGroup, on_delete=models.RESTRICT, related_name="roles", **optional
    )

    objects = UserRoleObjectManager()

    def __str__(self):
        return self.role_name

    def save(self, *args, **kwargs):
        create = False
        if self._state.adding:
            create = True
        reference_role = kwargs.pop("reference_role", None)
        role = super(UserRole, self).save(*args, **kwargs)
        if not create or self.seeded:
            return role
        if not reference_role:
            self.seed_default_permissions_to_role()
        else:
            self.copy_permissions_from_reference_role(reference_role=reference_role)
        return role

    def copy_permissions_from_reference_role(self, reference_role):
        if not isinstance(reference_role, UserRole):
            reference_role = UserRole.objects.get(id=reference_role)
        mod_list = []
        for perm in ModulePermission.objects.filter(role=reference_role):
            perm.id = None
            perm.role = self
            mod_list.append(perm)
        ModulePermission.objects.bulk_create(mod_list)
        sub_list = []
        for perm in SubModulePermission.objects.filter(role=reference_role):
            perm.id = None
            perm.role = self
            sub_list.append(perm)
        SubModulePermission.objects.bulk_create(sub_list)
        attr_list = []
        for perm in EntityAttributePermission.objects.filter(role=reference_role):
            perm.id = None
            perm.role = self
            attr_list.append(perm)
        EntityAttributePermission.objects.bulk_create(attr_list)

    def seed_default_permissions_to_role(self):
        mod_list = []
        for module in Module.objects.all():
            mod_list.append(
                ModulePermission(
                    role=self,
                    module=module,
                    can_create=False,
                    can_view=True,
                    can_update=False,
                    can_delete=False,
                    is_active=True,
                )
            )
        ModulePermission.objects.bulk_create(mod_list)
        sub_list = []
        for sub in SubModuleComposition.objects.all():
            sub_list.append(
                SubModulePermission(
                    role=self,
                    submodule=sub,
                    can_create=False,
                    can_view=True,
                    can_update=False,
                    can_delete=False,
                    is_active=True,
                )
            )
        SubModulePermission.objects.bulk_create(sub_list)
        attr_list = []
        for attr in EntityAttributeComposition.objects.all():
            attr_list.append(
                EntityAttributePermission(role=self, attribute=attr, has_perm=True)
            )
        EntityAttributePermission.objects.bulk_create(attr_list)


class HelixUser(
    AbstractBaseUser, PermissionsMixin, GenericModel, Address, SecondAddress
):
    # ACCESS_LEVEL = (
    #     ("admin", "Admin"),
    #     ("customer", "Customer"),
    #     ("health_center", "HealthCenter"),
    #     ("location", "Location"),
    # )
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
    )
    username = models.CharField(max_length=150, unique=True, **optional)
    is_active = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    access_level = models.CharField(
        max_length=15, choices=AccessLevel.choices(), default=AccessLevel.Location.value
    )
    salutation = LookupField(max_length=50, lookup_name="PREFIX", **optional)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, **optional)
    last_name = models.CharField(max_length=100)
    suffix = models.CharField(max_length=100, **optional)
    gender = LookupField(lookup_name="GENDER_TYPE", max_length=20, **optional)
    date_of_birth = models.DateField(**optional)
    country_code = models.CharField(max_length=10, default="+1", **optional)
    phone = models.CharField(max_length=20, unique=True, **optional)
    home_country_code = models.CharField(max_length=5, default="+1", **optional)
    home_phone = models.CharField(max_length=20, **optional)
    fax_country_code = models.CharField(max_length=5, default="+1", **optional)
    fax = models.CharField(max_length=20, **optional)
    previous_name = models.CharField(max_length=100, **optional)
    preferred_name = models.CharField(max_length=100, **optional)
    short_name = models.CharField(max_length=100, **optional)
    alias = models.CharField(max_length=50, **optional)
    ssn = models.CharField(max_length=50, **optional)
    national_id = models.CharField(max_length=50, **optional)
    national_id_identifier = models.CharField(max_length=50, **optional)
    profile_img = models.OneToOneField(Asset, on_delete=models.DO_NOTHING, **optional)
    mfa_enabled = models.BooleanField(default=False)
    work_country_code = models.CharField(max_length=5, default="+1", **optional)
    work_phone = models.CharField(max_length=25, **optional)
    default_address = models.CharField(
        max_length=250, choices=AddressTypes.choices(), **optional
    )
    status = LookupField(
        max_length=50,
        default="PENDING",
        lookup_name="USER_ACTIVATION_STATUS",
        **optional,
    )
    other_emails = ArrayField(models.EmailField(**optional), default=list, **optional)
    locked = models.BooleanField(default=False)
    failed_attempt_count = models.IntegerField(default=0)
    locked_at = models.DateTimeField(**optional)
    auth_user_id = SafeCharField(max_length=50, unique=True, **optional, db_index=True)
    languages_known = ArrayField(
        LookupField(max_length=50, lookup_name="LANGUAGE"), default=list, **optional
    )

    # class Meta:
    #     abstract = True

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = HelixUserObjectManager()

    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)

    def save(self, *args, **kwargs):
        if self._state.adding and not self.username:
            self.username = self.email if self.email else self.phone
            self.username = self.username if self.username else str(uuid.uuid4())
        return super(HelixUser, self).save(*args, **kwargs)

    @property
    def name(self):
        return self.__str__()

    @property
    def is_user_superuser(self):
        return self.is_superuser

    @property
    def is_resident_user(self):
        return not self.is_staff

    @property
    def age(self):
        today = datetime.date.today()
        if self.date_of_birth:
            return (
                today.year
                - self.date_of_birth.year
                - (
                    (today.month, today.day)
                    < (self.date_of_birth.month, self.date_of_birth.day)
                )
            )
        return None


class VerificationCode(GenericModel):
    USER_TYPE_CHOICE = (
        (1, "Practice User"),
        (2, "Patient"),
        (3, "PatientCreate"),
        (4, "PatientResetPassword"),
        (5, "GuestPatientLogin"),
    )
    user_id = models.CharField(null=True, max_length=255)
    user_type = models.IntegerField(choices=USER_TYPE_CHOICE, default=1)
    channel = models.CharField(max_length=50, choices=OTPChannels.choices(), **optional)
    code = models.CharField(max_length=10)

    class Meta:
        unique_together = ("user_id", "user_type", "channel")


class SecurityQuestion(GenericModel):
    name = models.CharField(max_length=1000)
    active = models.BooleanField(default=True)


class UserSecurityQuestion(GenericModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(SecurityQuestion, on_delete=models.CASCADE)
    response = models.CharField(max_length=1000)


class Module(GenericModel):
    product = models.CharField(max_length=45)
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=45)
    description = models.CharField(max_length=200)
    is_active = models.BooleanField()

    def __str__(self) -> str:
        return self.name


class Entity(GenericModel):
    MODEL_ALL_DATA_CACHE_KEY = "PERM_ENTITY"

    entity = models.CharField(max_length=100)
    app_name = models.CharField(max_length=100)

    class Meta:
        unique_together = (("app_name", "entity"),)


class EntityAttributeComposition(GenericModel):
    MODEL_ALL_DATA_CACHE_KEY = "PERM_ENTITY_ATTR_COMP"

    entity = models.ForeignKey(
        Entity, on_delete=models.CASCADE, related_name="attributes"
    )
    attribute = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        unique_together = (("attribute", "entity"),)


class ModuleComposition(GenericModel):
    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="composition"
    )
    entity = models.CharField(max_length=100)
    entity_obj = models.ForeignKey(Entity, on_delete=models.CASCADE, **optional)

    class Meta:
        unique_together = (("module", "entity"),)


class SubModuleComposition(GenericModel):
    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="submodules"
    )
    submodule = models.CharField(max_length=100)
    code = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = (("module", "submodule"),)

    def __str__(self):
        return self.submodule


class EntityAttributePermission(GenericModel):
    attribute = models.ForeignKey(
        EntityAttributeComposition, on_delete=models.CASCADE, related_name="permissions"
    )
    role = models.ForeignKey(
        UserRole, on_delete=models.CASCADE, related_name="attr_permissions"
    )
    has_perm = models.BooleanField()

    class Meta:
        unique_together = (("attribute", "role"),)


class ModulePermission(GenericModel):
    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="permissions"
    )
    role = models.ForeignKey(
        UserRole, on_delete=models.CASCADE, related_name="permissions"
    )
    can_create = models.BooleanField()
    can_view = models.BooleanField()
    can_update = models.BooleanField()
    can_delete = models.BooleanField()
    is_active = models.BooleanField()

    class Meta:
        unique_together = (("module", "role"),)


class SubModulePermission(GenericModel):
    submodule = models.ForeignKey(
        SubModuleComposition, on_delete=models.CASCADE, related_name="permissions"
    )
    role = models.ForeignKey(
        UserRole, related_name="submodule_permissions", on_delete=models.CASCADE
    )
    is_active = models.BooleanField(default=True)
    can_create = models.BooleanField()
    can_view = models.BooleanField()
    can_update = models.BooleanField()
    can_delete = models.BooleanField()

    class Meta:
        unique_together = (("submodule", "role"),)


class RegisteredDevice(GenericModel):
    user = models.ForeignKey(HelixUser, on_delete=models.CASCADE)
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
            ("user", "device_fingerprint"),  # Primary constraint using fingerprint
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


class AccessLog(GenericModel):
    ACCESS_STATUS_CHOICES = (
        ("success", "Successful Sign-In"),
        ("failure", "Unsuccessful Sign-In"),
    )
    user = models.ForeignKey(HelixUser, on_delete=models.CASCADE)
    device = models.ForeignKey(RegisteredDevice, on_delete=models.CASCADE)
    refresh_jti = models.CharField(max_length=255, **optional)
    refresh_exp = models.DateTimeField(**optional)
    refresh_token = models.TextField(**optional)
    ip_address = models.CharField(max_length=255)
    location = models.JSONField()
    login_status = models.CharField(
        max_length=20, choices=ACCESS_STATUS_CHOICES, default="success"
    )

    def save(self, *args, **kwargs):
        log = super(AccessLog, self).save(*args, **kwargs)
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


class Policy(GenericModel):
    name = models.CharField(max_length=255, unique=True)
    policy_type = LookupField(
        lookup_name="POLICY_TYPE", max_length=100, default="RENT_PAYMENT"
    )
    status = LookupField(lookup_name="POLICY_STATUS", max_length=100, default="DRAFT")
    description = models.TextField(**optional)
    publishing_date = models.DateTimeField(**optional)
    current_version = models.ForeignKey(
        "PolicyVersion",
        on_delete=models.SET_NULL,
        related_name="current_in_policy",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_on"]
        indexes = [
            models.Index(fields=["status", "-created_on"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.status})"


class PolicyVersion(GenericModel):
    policy = models.ForeignKey(
        Policy, on_delete=models.CASCADE, related_name="versions"
    )
    version_number = models.IntegerField(default=1)
    content_html = models.TextField(**optional)
    template_pdf_url = models.ForeignKey(
        Asset,
        on_delete=models.DO_NOTHING,
        related_name="policy_version_pdfs",
        **optional,
    )

    class Meta:
        unique_together = (("policy", "version_number"),)
        ordering = ["-version_number"]

    def __str__(self):
        return f"{self.policy.name} v{self.version_number}"


class UserPolicyAcceptance(GenericModel):
    user = models.ForeignKey(
        HelixUser, on_delete=models.DO_NOTHING, related_name="acceptance"
    )
    policy_version = models.ForeignKey(
        PolicyVersion, on_delete=models.DO_NOTHING, related_name="acceptance"
    )

    class Meta:
        path_to_resident_id = "user__resident__id"
        unique_together = (
            (
                "user",
                "policy_version",
            ),
        )
