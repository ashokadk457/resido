from common.utils.enum import EnumWithValueConverter


class BookingStatus(EnumWithValueConverter):
    PENDING = "pending"  # Tenant requested, awaiting admin approval
    CONFIRMED = "confirmed"  # Admin approved
    REJECTED = "rejected"  # Admin rejected
    CANCELLED = "cancelled"  # Booking cancelled


class SlotStatus(EnumWithValueConverter):
    AVAILABLE = "available"
    BOOKED = "booked"
    UNAVAILABLE = "unavailable"


class RecurringFrequency(EnumWithValueConverter):
    NOT_REQUIRED = "not_required"  # One-time booking
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"  # Custom recurrence pattern


class RecurrenceEndType(EnumWithValueConverter):
    NEVER = "never"
    AFTER_OCCURRENCES = "after_occurrences"
    ON_DATE = "on_date"


class DayOfWeek(EnumWithValueConverter):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


# Status level mapping (like LeaseStatus in lease/constants.py)
BOOKING_STATUS_LEVEL = {
    BookingStatus.PENDING.value: 1,
    BookingStatus.CONFIRMED.value: 2,
    BookingStatus.REJECTED.value: 3,
    BookingStatus.CANCELLED.value: 4,
}

# For use with python-dateutil rrule
# Biweekly = weekly with interval=2
REPEAT_FREQUENCY_MAP = {
    RecurringFrequency.NOT_REQUIRED.value: None,  # No recurrence
    RecurringFrequency.WEEKLY.value: "WEEKLY",
    RecurringFrequency.BIWEEKLY.value: "WEEKLY",  # Weekly with interval=2
    RecurringFrequency.MONTHLY.value: "MONTHLY",
    RecurringFrequency.CUSTOM.value: "CUSTOM",  # Custom pattern
}

DAY_OF_WEEK_MAP = {
    DayOfWeek.MONDAY.value: 0,
    DayOfWeek.TUESDAY.value: 1,
    DayOfWeek.WEDNESDAY.value: 2,
    DayOfWeek.THURSDAY.value: 3,
    DayOfWeek.FRIDAY.value: 4,
    DayOfWeek.SATURDAY.value: 5,
    DayOfWeek.SUNDAY.value: 6,
}

# Reverse mapping
DAY_OF_WEEK_REVERSE_MAP = {
    0: DayOfWeek.MONDAY.value,
    1: DayOfWeek.TUESDAY.value,
    2: DayOfWeek.WEDNESDAY.value,
    3: DayOfWeek.THURSDAY.value,
    4: DayOfWeek.FRIDAY.value,
    5: DayOfWeek.SATURDAY.value,
    6: DayOfWeek.SUNDAY.value,
}
