import os
from common.utils.enum import EnumWithValueConverter


class LeaseAction(EnumWithValueConverter):
    APPLICATION_PENDING = "application_pending"
    APPLICATION_FILLED = "application_filled"
    APPLICATION_NOT_FILLED = "application_not_filled"
    BACKGROUN_CHECK_STARTED = "background_check_started"
    BACKGROUN_CHECK_FAILED = "background_check_failed"
    BACKGROUN_CHECK_COMPLETED = "background_check_completed"
    APPLICATION_APPROVED = "application_approved"
    LEASE_SENT = "lease_sent"
    LEASE_SIGNED = "lease_signed"


class LeaseTerm(EnumWithValueConverter):
    FIXED_TERM = "fixed_term"
    MONTH_TO_MONTH = "month_to_month"


class LeaseStatus(EnumWithValueConverter):
    PENDING = "pending"
    DRAFT = "draft"
    ACTIVE = "active"
    TERMINATED = "terminated"
    EVICTION = "eviction"
    PENDING_RENEWAL = "pending_renewal"
    EXPIRED = "expired"


class LeaseApplicationStatus(EnumWithValueConverter):
    SENT = "sent"
    RECEIVED = "received"
    APPROVED = "approved"
    REJECTED = "rejected"


class LandlordType(EnumWithValueConverter):
    INDIVIDUAL = "individual"
    COMPANY = "company"


class SmokingStatus(EnumWithValueConverter):
    YES = "yes"
    NO = "no"
    OUTSIDE_ONLY = "outside_only"


class ParkingType(EnumWithValueConverter):
    TWO_WHEELER = "Two Wheeler"
    FOUR_WHEELER = "Four Wheeler"


class ExtraParkingType(EnumWithValueConverter):
    ELECTRIC_VEHICLE = "Electric Vehicle"
    BICYCLE = "Bicycle"
    VISITOR = "Visitor"
    RESERVED = "Reserved"
    DISABLED = "Disabled"


class OneTimeFeeType(EnumWithValueConverter):
    FLAT = "flat"
    PERCENT_RENT = "percent_rent"
    PERCENT_UNPAID = "percent_unpaid"


class FeeAppliedOn(EnumWithValueConverter):
    ONE_DAY_AFTER = 1
    TWO_DAYS_AFTER = 2
    THREE_DAYS_AFTER = 3


class LateFeeLimit(EnumWithValueConverter):
    NO_LIMIT = "no_limit"
    DAY_LIMIT = "day_limit"
    FLAT_LIMIT = "flat_limit"
    RENT_LIMIT = "rent_limit"


class LeaseUtilityServiceResponsible(EnumWithValueConverter):
    TENANT = "tenant"
    LANDLORD = "landlord"
    NA = "na"


class ESAType(EnumWithValueConverter):
    SERVICE_ANIMAL = "service_animal"
    ESA = "esa"
    BOTH = "both"


LEASE_STATUS_LEVEL = {
    LeaseStatus.DRAFT.value: 1,
    LeaseStatus.PENDING.value: 2,
    LeaseStatus.ACTIVE.value: 3,
    LeaseStatus.TERMINATED.value: 3,
    LeaseStatus.EVICTION.value: 3,
    LeaseStatus.PENDING_RENEWAL.value: 3,
    LeaseStatus.EXPIRED.value: 3,
}

LEASE_APPLICATION_STATUS_LEVEL = {
    LeaseApplicationStatus.SENT.value: 1,
    LeaseApplicationStatus.RECEIVED.value: 2,
    LeaseApplicationStatus.APPROVED.value: 3,
    LeaseApplicationStatus.REJECTED.value: 3,
}

LEASE_APPLICATION_FORM_LINK_EXPIRY = int(
    os.getenv("LEASE_APPLICATION_FORM_LINK_EXPIRY", "10000")
)
LEASE_APPLICATION_FORM_URL = "https://{domain}/#/rental-request-verification-view?request_id={request_id}&token={token}"
LEASE_APPLICATION_EMAIL_SUBJECT = "Please fill the Rental Request Form"
LEASE_APPLICATION_EMAIL_BODY = "Hi {first_name},\n\n You have been requested to fill the rental request form. Please click on the below link to fill.\n\n{url}"


class MoveRequestType(EnumWithValueConverter):
    MOVE_IN = "move_in"
    MOVE_OUT = "move_out"


class MoveRequestStatus(EnumWithValueConverter):
    PENDING = "pending"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MoveInspectionStatus(EnumWithValueConverter):
    SCHEDULED = "scheduled"
    NOT_SCHEDULED = "not_scheduled"
    PASSED = "passed"
    FAILED = "failed"


class MoveRequestDepositStatus(EnumWithValueConverter):
    PENDING = "pending"
    PAID = "paid"


class LeaseEndActionChoice(EnumWithValueConverter):
    RENEW_MONTHLY = "Renew_monthly"
    TERMINATE = "Terminate"
