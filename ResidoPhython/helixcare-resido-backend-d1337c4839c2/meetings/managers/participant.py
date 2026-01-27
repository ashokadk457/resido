from common.utils.logging import logger
from external.hus.core import HelixUtilityService
from helixauth.managers.registered_device import RegisteredDeviceManager
from meetings.constants import (
    MEETING_TYPE_TO_AUTO_NOTIFICATION_TYPE_MAP,
    MeetingEvent,
    TEMPLATE_CODE_MAP,
)
from meetings.serializers.meeting import MeetingSerializerTrimmed
from meetings.serializers.participant import MeetingParticipantSerializer
from notifications.managers.payload.push import PushNotificationPayloadBuilder
from residents.managers.registered_device import ResidentRegisteredDeviceManager


class MeetingParticipantManager:
    @classmethod
    def init(cls, participant_id=None, meeting_obj=None):
        from meetings.models import MeetingParticipant

        if not participant_id:
            return cls(meeting_obj=meeting_obj, participant_obj=None)

        meeting_participant = MeetingParticipant.objects.filter(
            id=participant_id
        ).first()
        if not meeting_participant:
            return cls(meeting_obj=meeting_obj, participant_obj=None)

        return cls(meeting_obj=meeting_obj, participant_obj=meeting_participant)

    def __init__(self, meeting_obj, participant_obj=None):
        self.meeting_obj = meeting_obj
        self.participant_obj = participant_obj

    def upsert_participants(self, participants_data):
        staff_ids, patient_ids = {}, {}
        for participant in participants_data:
            participant["meeting"] = str(self.meeting_obj.id)
            if participant["staff"]:
                staff_ids[participant["staff"]] = participant
            if participant["patient"]:
                patient_ids[participant["patient"]] = participant

        current_staff_participants = list(
            self.meeting_obj.meetingparticipant_set.filter(
                staff_id__isnull=False
            ).values_list("staff_id", flat=True)
        )
        current_staff_participants = set(str(_id) for _id in current_staff_participants)
        current_patient_participants = list(
            self.meeting_obj.meetingparticipant_set.filter(
                patient_id__isnull=False
            ).values_list("patient_id", flat=True)
        )
        current_patient_participants = set(
            str(_id) for _id in current_patient_participants
        )

        if not current_staff_participants and not current_patient_participants:
            participant_serializer = MeetingParticipantSerializer(
                data=participants_data, many=True
            )
            participant_serializer.is_valid(raise_exception=True)
            return participant_serializer.save()

        new_staff_participants = set(staff_ids.keys()) - current_staff_participants
        new_patient_participants = (
            set(patient_ids.keys()) - current_patient_participants
        )

        created_participants = []
        if new_staff_participants:
            participants_data = [staff_ids.get(staff_id) for staff_id in staff_ids]
            participant_serializer = MeetingParticipantSerializer(
                data=participants_data, many=True
            )
            participant_serializer.is_valid(raise_exception=True)
            created_participants += participant_serializer.save()

        if new_patient_participants:
            participants_data = [
                patient_ids.get(patient_id) for patient_id in patient_ids
            ]
            participant_serializer = MeetingParticipantSerializer(
                data=participants_data, many=True
            )
            participant_serializer.is_valid(raise_exception=True)
            created_participants += participant_serializer.save()

        return created_participants

    def notify(
        self,
        inviter,
        notification_type=None,
        meeting_event=MeetingEvent.ROOM_STARTED.value,
    ):
        if not self.meeting_obj or not self.participant_obj:
            logger.info(
                f"Cannot send {notification_type} notification as meeting or participant is None"
            )
            return "no_meeting_or_no_participant", None

        return self.send_push_notification_for_meeting(
            inviter=inviter,
            notification_type=notification_type,
            meeting_event=meeting_event,
        )

    @classmethod
    def get_active_device_token_and_platform(cls, staff, patient):
        device_manager, user = ResidentRegisteredDeviceManager(), patient
        if staff is not None:
            device_manager, user = RegisteredDeviceManager(), staff.user

        return device_manager.get_active_device_token_and_platform(user=user)

    @classmethod
    def get_final_notification_type(cls, meeting_type, notification_type=None):
        if notification_type:
            return notification_type

        return MEETING_TYPE_TO_AUTO_NOTIFICATION_TYPE_MAP.get(meeting_type)

    def get_push_notification_payload(
        self, inviter, notification_type=None, meeting_event=None
    ):
        """

        @param inviter:
        @param notification_type:
        @param meeting_event:
        @return: Tuple of size 3 to denote success, error_code, payload_dict
        """
        staff = self.participant_obj.staff
        patient = self.participant_obj.patient

        active_device_token, platform = self.get_active_device_token_and_platform(
            staff=staff, patient=patient
        )
        if not active_device_token or not platform:
            logger.info("No active device token or platform. Cannot send invite")
            return False, "no_active_device_token_or_platform", {}

        meeting_data = MeetingSerializerTrimmed(instance=self.meeting_obj).data
        meeting_participant_data = MeetingParticipantSerializer(
            instance=self.participant_obj, context={"prefixed": True}
        ).data
        notification_type = self.get_final_notification_type(
            meeting_type=meeting_data.get("meeting_meeting_type"),
            notification_type=notification_type,
        )
        template_code = TEMPLATE_CODE_MAP.get(f"{meeting_event}_{notification_type}")
        extra_data = {
            "notification_type": notification_type,
            **meeting_data,
            **meeting_participant_data,
        }

        _name = "AnonymousUser" if inviter is None else inviter.name
        notification_payload_builder = PushNotificationPayloadBuilder(
            notification_type=notification_type,
            platform=platform,
            device_token=active_device_token,
            template_code=template_code,
            extra_data=extra_data,
            template_body_params={"_name": _name},
        )
        notification_payload = notification_payload_builder.build()
        logger.info(f"Final push notification payload: {notification_payload}")

        return True, None, notification_payload

    def send_push_notification_for_meeting(
        self, inviter, notification_type=None, meeting_event=None
    ):
        _, err, notification_payload = self.get_push_notification_payload(
            inviter=inviter,
            notification_type=notification_type,
            meeting_event=meeting_event,
        )
        if err:
            return None, None

        hus = HelixUtilityService()
        response_data, status_code = hus.send_push_notification(
            push_notif_payload=[notification_payload]
        )

        if isinstance(response_data, dict) and "data" in response_data:
            response_data = response_data.get("data", {})

        return response_data, status_code
