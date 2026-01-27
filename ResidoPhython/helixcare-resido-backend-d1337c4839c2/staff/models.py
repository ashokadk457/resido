import re
import random
from django.contrib.postgres.fields import ArrayField
from django.db import models

from audit.models import GenericModel
from common.errors import ERROR_DETAILS
from common.utils.general import get_org_prefix
from common.utils.logging import logger
from helixauth.models import HelixUser, UserRole
from locations.models import Location, Property, Customer, Building, Floor, Unit
from lookup.fields import LookupField
from staff.managers.staffvisittypeduration import VisitTypeDurationManager

# Create your models here.
optional = {"null": True, "blank": True}


class StaffGroup(GenericModel):
    name = models.CharField(max_length=155, unique=True)
    active = models.BooleanField(default=True)


class HelixStaff(GenericModel):
    user = models.OneToOneField(
        HelixUser, on_delete=models.CASCADE, related_name="helixuser_staff"
    )
    groups = models.ManyToManyField(StaffGroup, related_name="staff", **optional)
    user_roles = models.ManyToManyField(UserRole, **optional)
    employee_id = models.CharField(
        max_length=100,
        unique=True,
        error_messages={"unique": ERROR_DETAILS["employee_id_exists"]},
        **optional,
    )
    properties = models.ManyToManyField(Property, related_name="properties", **optional)
    locations = models.ManyToManyField(
        Location, related_name="staff_locations", **optional
    )
    customers = models.ManyToManyField(
        Customer, related_name="staff_customers", **optional
    )
    buildings = models.ManyToManyField(
        Building, related_name="staff_buildings", **optional
    )
    floors = models.ManyToManyField(Floor, related_name="staff_floors", **optional)
    units = models.ManyToManyField(Unit, related_name="staff_units", **optional)
    display_id = models.CharField(**optional, max_length=100)
    communication_mode = ArrayField(
        LookupField(max_length=200, lookup_name="COMMUNICATION_MODE"),
        default=[],
        **optional,
    )

    class Meta:
        path_to_location = "locations"

    @property
    def email(self):
        return self.user.email

    @property
    def phone_number(self):
        return self.user.phone

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

    def __str__(self):
        return "%s %s" % (self.user.first_name, self.user.last_name)

    @property
    def speciality_codes(self):
        return list(self.specialities.all().values_list("code", flat=True))

    def clean(self):
        super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        name = get_org_prefix().upper()
        name += "PRO"
        if self._state.adding:
            last_id = HelixStaff.objects.all().aggregate(
                largest=models.Max("display_id")
            )["largest"]
            if last_id is not None:
                reg = re.compile(r"[a-zA-Z]+(?P<last_id>[0-9]+)$")
                obj = reg.search(last_id)
                self.display_id = str(name) + str(
                    int(obj.group(1)) + 1
                    if obj.group(1)
                    else random.randint(11111, 99999)
                )
            else:
                self.display_id = name + "10000001"
        super(HelixStaff, self).save(*args, **kwargs)

    @property
    def starts_in_early_morning(self):
        try:
            return (
                self.staffworkinghour_set.all()
                .first()
                .staffworkinghourdetail_set.filter(
                    start_time__gte="00:00:00", start_time__lt="10:00:00"
                )
                .exists()
            )
        except Exception as e:
            logger.info(f"Exception occurred while checking start time: {str(e)}")
            return False

    @property
    def starts_in_morning(self):
        try:
            return (
                self.staffworkinghour_set.all()
                .first()
                .staffworkinghourdetail_set.filter(
                    start_time__gte="10:00:00", start_time__lt="12:00:00"
                )
                .exists()
            )
        except Exception as e:
            logger.info(f"Exception occurred while checking start time: {str(e)}")
            return False

    @property
    def starts_in_afternoon(self):
        try:
            return (
                self.staffworkinghour_set.all()
                .first()
                .staffworkinghourdetail_set.filter(
                    start_time__gte="12:00:00", start_time__lt="17:00:00"
                )
                .exists()
            )
        except Exception as e:
            logger.info(f"Exception occurred while checking start time: {str(e)}")
            return False

    @property
    def starts_in_evening(self):
        try:
            return (
                self.staffworkinghour_set.all()
                .first()
                .staffworkinghourdetail_set.filter(
                    start_time__gte="17:00:00", start_time__lt="23:59:00"
                )
                .exists()
            )
        except Exception as e:
            logger.info(f"Exception occurred while checking start time: {str(e)}")
            return False


class VisitTypeDuration(GenericModel):
    # TODO MUST REMOVE THIS - DEPRECATED
    provider = models.ForeignKey(
        HelixStaff, **optional, related_name="visit", on_delete=models.SET_NULL
    )
    visit_type = LookupField(max_length=100, lookup_name="VISIT_TYPE", default="NP_PHY")
    duration = models.IntegerField(default=30)

    objects = VisitTypeDurationManager()


class NPIOverrides(GenericModel):
    npi = models.CharField(max_length=100)
    npi_data = models.JSONField(**optional)
