from common.utils.enum import EnumWithValueConverter
from helixauth.constants import AccessLevel

ACCESS_LEVEL_TO_PRIORITY = {
    "admin": 0,
    "customer": 1,
    "health_center": 2,
    "location": 3,
}


class StaffStatus(EnumWithValueConverter):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"


class CareCenterRoleType(EnumWithValueConverter):
    CEO = "CEO"
    CMO = "CMO"
    practice_administrator = "Practice Administrator"
    clinic_manager_medical_office_manager = "Clinic Manager / Medical Office Manager"
    credentialing_specialist = "Credentialing Specialist"
    IT_administrator = "IT Administrator"


HELIX_STAFF_FIELD_TO_ACCESS_LEVEL_MAP = {
    AccessLevel.Customer.value: "customers",
    AccessLevel.Property.value: "properties",
    AccessLevel.Location.value: "locations",
    AccessLevel.Building.value: "buildings",
    AccessLevel.Floor.value: "floors",
    AccessLevel.Unit.value: "units",
}
