from common.utils.enum import EnumWithValueConverter

early_morning_start_times_1st_half = ["06:00:00", "06:30:00", "07:00:00"]
early_morning_end_time_1st_half = ["10:30:00", "11:00:00"]

early_morning_break_start_time = ["11:00", "11:30:00"]
early_morning_break_end_time = ["12:00:00", "12:30:00"]

early_morning_start_times_2nd_half = ["12:30:00", "13:00:00"]
early_morning_end_time_2nd_half = ["13:30:00", "14:00:00"]

morning_start_times_1st_half = ["11:00:00", "11:30:00", "12:00:00"]
morning_end_time_1st_half = ["14:30:00", "15:00:00", "15:30:00"]

morning_break_start_time = ["15:30:00"]
morning_break_end_time = ["16:00:00"]

morning_start_times_2nd_half = ["16:00:00", "16:30:00"]
morning_end_time_2nd_half = ["18:30:00", "19:00:00"]

afternoon_start_times_1st_half = ["13:00:00", "13:30:00", "14:00:00"]
afternoon_end_time_1st_half = ["15:30:00", "16:00:00"]

afternoon_break_start_time = ["16:00:00", "16:30:00"]
afternoon_break_end_time = ["17:30:00", "18:00:00"]

afternoon_start_times_2nd_half = ["18:30:00", "19:00:00"]
afternoon_end_time_2nd_half = ["20:30:00", "21:00:00"]

evening_start_times_1st_half = ["17:00:00", "17:30:00", "18:00:00"]
evening_end_time_1st_half = ["19:30:00", "20:00:00"]

evening_break_start_time = ["20:00:00", "20:30:00"]
evening_break_end_time = ["21:00:00", "21:30:00"]

evening_start_times_2nd_half = ["21:30:00", "22:00:00"]
evening_end_time_2nd_half = ["23:00:00", "23:30:00"]

# right
early_morning_details = [
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "monday",
        "start_time": "06:00:00",
        "end_time": "14:00:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "tuesday",
        "start_time": "06:00:00",
        "end_time": "14:00:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "wednesday",
        "start_time": "06:00:00",
        "end_time": "14:00:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "thursday",
        "start_time": "06:00:00",
        "end_time": "14:00:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "friday",
        "start_time": "06:00:00",
        "end_time": "14:00:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "saturday",
        "start_time": "06:00:00",
        "end_time": "14:00:00",
        "active": True,
    },
]

# right
morning_details = [
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "monday",
        "start_time": "11:00:00",
        "end_time": "19:00:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "tuesday",
        "start_time": "11:00:00",
        "end_time": "19:00:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "wednesday",
        "start_time": "11:00:00",
        "end_time": "19:00:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "thursday",
        "start_time": "11:00:00",
        "end_time": "19:00:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "friday",
        "start_time": "11:00:00",
        "end_time": "19:00:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "saturday",
        "start_time": "11:00:00",
        "end_time": "19:00:00",
        "active": True,
    },
]

# right
afternoon_details = [
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "monday",
        "start_time": "14:00:00",
        "end_time": "22:00:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "tuesday",
        "start_time": "13:00:00",
        "end_time": "21:00:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "wednesday",
        "start_time": "13:00:00",
        "end_time": "21:00:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "thursday",
        "start_time": "13:00:00",
        "end_time": "21:00:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "friday",
        "start_time": "13:00:00",
        "end_time": "21:00:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "saturday",
        "start_time": "13:00:00",
        "end_time": "21:00:00",
        "active": True,
    },
]

# right
evening_details = [
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "monday",
        "start_time": "17:00:00",
        "end_time": "23:30:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "tuesday",
        "start_time": "17:00:00",
        "end_time": "23:30:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "wednesday",
        "start_time": "17:00:00",
        "end_time": "23:30:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "thursday",
        "start_time": "17:00:00",
        "end_time": "23:30:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "friday",
        "start_time": "17:00:00",
        "end_time": "23:30:00",
        "active": True,
    },
    {
        "schedule_template": None,
        "month": None,
        "day_of_month": None,
        "day_of_week": "saturday",
        "start_time": "17:00:00",
        "end_time": "23:30:00",
        "active": True,
    },
]

# right
time_details = [
    early_morning_details,
    morning_details,
    afternoon_details,
    evening_details,
]

weekdays = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


class EventCategory(EnumWithValueConverter):
    APPOINTMENT_BLOCK = "APPOINTMENT_BLOCK"
    INTERNAL_MEETING = "INTERNAL_EVENT"
    EXTERNAL_MEETING = "EXTERNAL_EVENT"


class EventTrigger(EnumWithValueConverter):
    INVITE = "INVITE"
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"


class VisitTypeAssignmentRequestMethod(EnumWithValueConverter):
    COPY_FROM_SOURCE_TEMPLATE = "COPY_FROM_SOURCE_TEMPLATE"
    COPY_FROM_SOURCE_STAFF = "COPY_FROM_SOURCE_STAFF"
    COPY_FROM_SOURCE_COMPOSITION = "COPY_FROM_SOURCE_COMPOSITION"


class VisitTypeAssignmentRequestStatus(EnumWithValueConverter):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    FAILED = "FAILED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    COMPLETED = "COMPLETED"


FROM_SOURCE_TEMPLATE = VisitTypeAssignmentRequestMethod.COPY_FROM_SOURCE_TEMPLATE.value
FROM_SOURCE_STAFF = VisitTypeAssignmentRequestMethod.COPY_FROM_SOURCE_STAFF.value
FROM_SOURCE_COMPOSITION = (
    VisitTypeAssignmentRequestMethod.COPY_FROM_SOURCE_COMPOSITION.value
)

ASSIGNMENT_REQUEST_METHODS = [
    FROM_SOURCE_TEMPLATE,
    FROM_SOURCE_STAFF,
    FROM_SOURCE_COMPOSITION,
]
