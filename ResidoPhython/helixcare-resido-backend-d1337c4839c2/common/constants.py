import os
import pytz
from dateutil import rrule
from faker import Faker

from enums.framework.enum import StandardEnum
from enums.framework.item import StandardEnumItem

from common.utils.enum import EnumWithValueConverter

YES = "Y"
NO = "N"
ACTION_CHOICES = ((YES, "Yes"), (NO, "No"))

LOCKOUT_LIMIT = 5
LOCKOUT_RELEASE_IN_MINS = 24 * 60  # One day

HB_LOGGER = "hb_logger"
CUSTOM_READABLE_TIMESTAMP = "%d %b %Y %H:%M:%S.%f %Z"
IST_TIMEZONE = pytz.timezone("Asia/Kolkata")
UTC_TIMEZONE = pytz.timezone("UTC")
DEFAULT_VERSIONS_DATA = {
    "version": None,
    "release": None,
    "built_on": None,
    "deployed_on": None,
    "uptime": None,
    "commit": None,
}
EXTERNAL_API_TIMEOUT = int(os.getenv("EXTERNAL_API_TIMEOUT", "30"))
OTP_EXPIRY_IN_SECONDS = int(
    os.getenv("OTP_EXPIRY_IN_SECONDS", "300")
)  # Default expiry 75 seconds


class DayOfWeek(EnumWithValueConverter):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"


class EventRepeatFrequency(EnumWithValueConverter):
    day = "day"
    week = "week"
    month = "month"
    year = "year"


class EventType(EnumWithValueConverter):
    available = "available"
    unavailable = "unavailable"


class ScheduleCategory(EnumWithValueConverter):
    shift = "shift"
    working_hours = "working_hours"
    holidays = "holidays"
    walkin = "walkin"


class ScheduleType(EnumWithValueConverter):
    weekly = "weekly"
    monthly = "monthly"


class CategoryForVisitType(EnumWithValueConverter):
    new_patient = "new_patient"
    returning_patient = "returning_patient"


DAILY = "DAILY"
WEEKLY = "WEEKLY"
MONTHLY = "MONTHLY"
YEARLY = "YEARLY"

REPEAT_FREQUENCY_MAP = {
    EventRepeatFrequency.day.value: rrule.DAILY,
    EventRepeatFrequency.week.value: rrule.WEEKLY,
    EventRepeatFrequency.month.value: rrule.MONTHLY,
    EventRepeatFrequency.year.value: rrule.YEARLY,
}

DAY_OF_WEEK_MAP = {
    DayOfWeek.monday.value: rrule.MO,
    DayOfWeek.tuesday.value: rrule.TU,
    DayOfWeek.wednesday.value: rrule.WE,
    DayOfWeek.thursday.value: rrule.TH,
    DayOfWeek.friday.value: rrule.FR,
    DayOfWeek.saturday.value: rrule.SA,
    DayOfWeek.sunday.value: rrule.SU,
}

DAY_OF_WEEK_MAP_REVERSE = {
    0: DayOfWeek.monday.value,
    1: DayOfWeek.tuesday.value,
    2: DayOfWeek.wednesday.value,
    3: DayOfWeek.thursday.value,
    4: DayOfWeek.friday.value,
    5: DayOfWeek.saturday.value,
    6: DayOfWeek.sunday.value,
}


ALLOWED_PREFERRED_TIMES = [
    "starts_in_early_morning",
    "starts_in_morning",
    "starts_in_afternoon",
    "starts_in_evening",
]

GUEST_PATIENT_TOKEN_EXPIRY = int(os.getenv("GUEST_PATIENT_TOKEN_EXPIRY", "600"))
RESET_PASSWORD_TOKEN_EXPIRY = int(os.getenv("RESET_PASSWORD_TOKEN_EXPIRY", "600"))
CUSTOMER_ONBOARDING_TOKEN_EXPIRY = int(
    os.getenv("CUSTOMER_ONBOARDING_TOKEN_EXPIRY", "600")
)

TEST_ENVIRONMENT = "TEST"
LOCAL_ENVIRONMENT = "LOCAL"
PRODUCTION_ENVIRONMENT = "PROD"

STATUS_CATEGORY_TO_VISIT_STATUS_MAP = {
    "scheduled": [
        "PENDING",
        "BOOKED",
        "PRECHECK",
        "ARRIVED",
        "CHECK_IN",
        "CHECK_IN_ARR",
        "CHECK_IN_NOTIFY",
        "RESCHEDULED",
    ],
    "completed": ["COMPLETE", "CHECK_OUT", "DISCHARGE"],
    "cancelled": ["CANCELLED"],
    "no_show": ["NO_SHOW"],
}


class CreatePatientContexts(EnumWithValueConverter):
    create_account = "create_account"
    book_appointment = "book_appointment"


ALLOWED_METHODS_TO_PATIENT = {
    "get": False,
    "post": False,
    "put": False,
    "patch": False,
    "delete": False,
}


INFANT = "INF"
CHILD = "CHILD"
TEEN = "TEEN"
PEDIA_AGES = {INFANT, CHILD, TEEN}

URGENT_CARE = "Urgent Care"
PRIMARY_CARE = "Primary Care"


class OTPChannels(EnumWithValueConverter):
    EMAIL = "EMAIL"
    SMS = "SMS"


# change this to toggle the RLA check on server start
RLA_CHECK_ENFORCED = False

# name the models for which RLA check should not be checked on server start
RLA_WHITELISTED_MODELS = []

CCDA_CERTIFICATION_COL_HELP_TEXT = "Field added for CCDA Certification"

fake = Faker()
RANDOMISED_TENANT_DATA = {
    "schema_name": None,
    "name": None,
    "app_conf_type": fake.random_element(elements=[1, 2]),
    "allow_ext_providers": fake.boolean(),
    "url": None,
    "max_security_question": fake.random_int(min=1, max=20),
    "code": fake.random_int(min=1000, max=9999),
    "website": fake.url() if fake.boolean(chance_of_getting_true=50) else None,
    "address": fake.address(),
    "address_1": fake.secondary_address(),
    "city": fake.city(),
    "state": fake.state(),
    "zipcode": fake.zipcode(),
    "contact_prefix": fake.prefix(),
    "contact_first_name": fake.first_name(),
    "contact_middle_name": fake.random_element(elements=["", fake.first_name()[0]]),
    "contact_last_name": fake.last_name(),
    "contact_suffix": fake.suffix(),
    "work_phone": fake.phone_number(),
    "phone": fake.phone_number(),
    "fax": fake.phone_number(),
    "email": fake.email(),
    "preferred_communication_mode": fake.random_element(
        elements=["EM", "WP", "CP", "FAX", "ML", "ALL"]
    ),
    "country": "US",
    "status": fake.random_element(elements=["YES", "NO"]),
}

TRUE_QUERY_PARAMS = ["True", "TRUE", "true"]
FALSE_QUERY_PARAMS = ["False", "FALSE", "false"]

FEATURE_SWITCHES_FILE_PATH = "./data/features/switches.csv"
PERIODIC_TASKS_JSON_FILE_PATH = "./data/periodic_tasks/tasks_data.json"


class StandardTimeZone(StandardEnum):
    UTC = StandardEnumItem(
        code="UTC",
        visible_name="UTC",
        extra_data={
            "country_codes": [],
            "utc_offset": {"sdt": "+00:00", "dst": "+00:00"},
            "abbreviation": {"sdt": "GMT", "dst": None},
        },
    )
    IST = StandardEnumItem(
        code="Asia/Kolkata",
        visible_name="IST",
        extra_data={
            "country_codes": ["IND"],
            "utc_offset": {"sdt": "+05:30", "dst": "+05:30"},
            "abbreviation": {"sdt": "IST", "dst": None},
        },
    )


class DurationUnit(EnumWithValueConverter):
    SECONDS = "SECONDS"
    MINUTES = "MINUTES"
    HOURS = "HOURS"
    DAYS = "DAYS"


class ProductPlanCode(EnumWithValueConverter):
    """
    Standard plan codes for RESIDO subscriptions
    """

    STARTER = "STARTER"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"
    CUSTOM = "CUSTOM"


class ProviderLoginMethods(StandardEnum):
    PASSWORD = StandardEnumItem(code="password", visible_name="Password")
    OTP = StandardEnumItem(code="otp", visible_name="OTP")
    BOTH = StandardEnumItem(code="both", visible_name="Both")


class MfaMethod(StandardEnum):
    EMAIL = "EMAIL"
    PHONE = "PHONE"


GENIUS_DOMAIN = os.getenv("GENIUS_DOMAIN", "https://genius-dev.helixbeat.com")
LIVEKIT_WEBSOCKET_URL = os.getenv(
    "LIVEKIT_WEBSOCKET_URL", "wss://falcon-nwojd9zo.livekit.cloud"
)
