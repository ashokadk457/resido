import os

from common.utils.enum import EnumWithValueConverter
from helixauth.constants import NotificationChannel
from notifications.constants import TemplateCode


class MeetingType(EnumWithValueConverter):
    IMMEDIATE = "IMMEDIATE"
    ON_DEMAND = "ON_DEMAND"
    SCHEDULED = "SCHEDULED"


class NotificationType(EnumWithValueConverter):
    CALL = "CALL"
    SMS = "SMS"
    EMAIL = "EMAIL"
    MESSAGE = "MESSAGE"


class ParticipationType(EnumWithValueConverter):
    LIMITED = "LIMITED"
    OPEN = "OPEN"
    INVITE_ONLY = "INVITE_ONLY"


class MeetingEvent(EnumWithValueConverter):
    ROOM_FINISHED = "room_finished"
    ROOM_STARTED = "room_started"


class SessionListMode(EnumWithValueConverter):
    HISTORY = "HISTORY"
    LIST = "LIST"


class MeetingSessionType(EnumWithValueConverter):
    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"


class MessageLevel(EnumWithValueConverter):
    ROOT = "ROOT"
    DESCENDANT = "DESCENDANT"


class MessageType(EnumWithValueConverter):
    LEAF = "LEAF"
    NON_LEAF = "NON_LEAF"


class MeetingEngagementType(EnumWithValueConverter):
    ONE_ON_ONE = "ONE_ON_ONE"
    GROUP = "GROUP"


class OtherParticipantType(EnumWithValueConverter):
    STAFF = "STAFF"
    PATIENT = "PATIENT"
    STAFF_AND_PATIENTS = "STAFF_AND_PATIENTS"


MEETING_TYPE_TO_AUTO_NOTIFICATION_TYPE_MAP = {
    MeetingType.IMMEDIATE.value: NotificationType.CALL.value,
    MeetingType.ON_DEMAND.value: NotificationType.MESSAGE.value,
    MeetingType.SCHEDULED.value: NotificationType.MESSAGE.value,
}

TEMPLATE_CODE_MAP = {
    f"{MeetingEvent.ROOM_STARTED.value}_{NotificationType.CALL.value}": TemplateCode.INCOMING_CALL.value,
    f"{MeetingEvent.ROOM_STARTED.value}_{NotificationType.MESSAGE.value}": TemplateCode.MEETING_STARTED.value,
}

ROOM_NAME_SIZE = int(os.getenv("ROOM_NAME_SIZE", 8))

MEETING_LINK = (
    "{domain}/#/provider-telehealth?meeting_id={meeting_id}&room_name={room_name}"
)

FACEMEET_EMAIL_INVITE_TITLE = "Facemeet Invite for {title}"
SCHEDULED_FACEMEET_EMAIL_INVITE_BODY = """Hi {_name},\n\n
{host_name} has invited you to a scheduled FaceMeet. Your FaceMeet details are as follows:\n
FaceMeet: {title}
Date and Time: From {start_date} at {start_time} onwards till {end_time}
Meeting Room Name: {meeting_room}
Meeting Link: {meeting_link}
"""

QUICK_JOIN_FACEMEET_INVITE_TITLE = "QuickJoin FaceMeet Invite"
QUICK_JOIN_FACEMEET_INVITE_BODY = """Hi {_name},\n
{host_name} is inviting you to join the FaceMeet here -> {meeting_link}
"""

DEFAULT_MEETING_INVITE_NOTIFICATION_CHANNELS = [
    NotificationChannel.EMAIL.value,
    NotificationChannel.PUSH.value,
]
