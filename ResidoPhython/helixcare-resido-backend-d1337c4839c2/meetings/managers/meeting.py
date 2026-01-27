from datetime import datetime

from livekit.api import AccessToken, VideoGrants
from nanoid import generate as generate_nanoid

from common.utils.dict_ import DictUtils
from common.utils.proto import ProtoUtils
from external.lk.configuration import LiveKitConfiguration
from external.lk.core import LiveKit
from helixauth.constants import NotificationChannel
from meetings.constants import (
    ROOM_NAME_SIZE,
    MeetingEvent,
    DEFAULT_MEETING_INVITE_NOTIFICATION_CHANNELS,
)
from meetings.managers.notifications.email import MeetingEmailNotificationDispatcher
from meetings.managers.participant import MeetingParticipantManager
from meetings.managers.session import MeetingSessionManager
from meetings.models import Meeting, MeetingSession
from scheduling.constants import EventTrigger


class MeetingManager:
    @classmethod
    def init(cls, meeting_id):
        meeting_obj = Meeting.objects.filter(id=meeting_id).first()
        if not meeting_obj:
            return None

        return cls(meeting_id=meeting_id, meeting_obj=meeting_obj)

    def __init__(self, meeting_id=None, meeting_obj=None):
        self.meeting_obj = meeting_obj
        self.meeting_id = meeting_id
        self.livekit_config = LiveKitConfiguration.init()
        self.live_kit = LiveKit.init(config=self.livekit_config)
        self.participant_manager = None
        self.session_manger = MeetingSessionManager(meeting_id=self.meeting_id)

    def setup_new_meeting(self, meeting_data):
        meeting_data["room_name"] = self._generate_room_name()
        self.meeting_obj = Meeting.objects.create(**meeting_data)
        self.meeting_id = str(self.meeting_obj.id)
        return self.meeting_obj

    def set_participants(self, participants_data):
        if not self.meeting_obj or not participants_data:
            return

        participant_manager = MeetingParticipantManager(meeting_obj=self.meeting_obj)
        return participant_manager.upsert_participants(
            participants_data=participants_data
        )

    def get_or_create_room_session(self, started_by, notify=True):
        if not self.meeting_obj:
            return

        last_session_id = self.meeting_obj.last_session
        last_session_active = self.meeting_obj.last_session_active

        existing = True
        if last_session_active and last_session_id:
            last_session = MeetingSession.objects.filter(id=last_session_id).first()
            self.session_manger.session_obj = last_session
        else:
            existing = False
            room = self.live_kit.create_room(room_name=self.meeting_obj.room_name)
            room_data = ProtoUtils.to_dict(proto_obj=room)
            session_data = self.prepare_room_data_for_session_data(room_data=room_data)
            _, self.meeting_obj = self.session_manger.create_new_session(
                session_data=session_data
            )

        if not existing and notify:
            participants = self.meeting_obj.meetingparticipant_set.all()
            self.notify_all_participants(
                participants=participants,
                meeting_event=MeetingEvent.ROOM_STARTED.value,
                inviter=started_by,
            )

        return self.session_manger.get_session_representation()

    def notify_all_participants(self, participants, meeting_event, inviter):
        for participant in participants:
            if participant.is_host:
                continue

            participant_manager = MeetingParticipantManager(
                meeting_obj=self.meeting_obj, participant_obj=participant
            )
            participant_manager.notify(inviter=inviter, meeting_event=meeting_event)

    def _generate_token(self, id_of_participant, meeting_participant_id):
        """

        @param id_of_participant: # The actual staff id or patient id
        @param meeting_participant_id: # The id of the participant for this particular meeting
        @return:
        """
        token_obj = (
            AccessToken(
                api_key=self.livekit_config.api_key,
                api_secret=self.livekit_config.api_secret,
            )
            .with_identity(id_of_participant)
            .with_name(meeting_participant_id)
            .with_grants(VideoGrants(room_join=True, room=self.meeting_obj.room_name))
        )
        return token_obj.to_jwt()

    def initialize_participant_manager(self, meeting_participant_id):
        participant_manager = MeetingParticipantManager.init(
            participant_id=meeting_participant_id, meeting_obj=self.meeting_obj
        )
        if not participant_manager.participant_obj:
            return None

        self.participant_manager = participant_manager
        return self.participant_manager

    def generate_token(self, meeting_participant_id):
        if not self.participant_manager:
            self.participant_manager = self.initialize_participant_manager(
                meeting_participant_id=meeting_participant_id
            )
            if not self.participant_manager:
                return None

        return self._generate_token(
            id_of_participant=self.participant_manager.participant_obj.id_of_participant,
            meeting_participant_id=meeting_participant_id,
        )

    @staticmethod
    def _generate_room_name():
        return generate_nanoid(size=ROOM_NAME_SIZE)

    def prepare_room_data_for_session_data(self, room_data):
        room_data = DictUtils.convert_camelcase_dict_to_snake_case_dict(data=room_data)

        room_data["meeting_id"] = self.meeting_id
        room_data["session_id"] = room_data.pop("sid", None)
        room_data.pop("version", None)
        room_data.pop("name", None)
        room_data["creation_time"] = datetime.fromtimestamp(
            int(room_data["creation_time"])
        )
        room_data["active"] = True

        return room_data

    def get_participants(self):
        all_participants_excluding_host = (
            self.meeting_obj.meetingparticipant_set.exclude(
                staff_id=str(self.meeting_obj.host.id)
            )
        )
        return all_participants_excluding_host

    def send_invites(self, notification_channels=None, participants=None, **kwargs):
        if notification_channels is None:
            notification_channels = DEFAULT_MEETING_INVITE_NOTIFICATION_CHANNELS

        kwargs = kwargs or {}
        kwargs["trigger"] = EventTrigger.INVITE.value
        kwargs["meeting_type"] = self.meeting_obj.meeting_type
        kwargs["host_name"] = self.meeting_obj.host_name
        kwargs["meeting_room"] = self.meeting_obj.room_name
        kwargs["meeting_link"] = self.meeting_obj.link
        if not kwargs.get("event"):
            event = self.meeting_obj.scheduled_event
            if event is not None:
                kwargs["event"] = event.schedule

        if participants is None:
            participants = self.get_participants()

        if NotificationChannel.EMAIL.value in notification_channels:
            self.send_email_invites(participants=participants, **kwargs)

    @classmethod
    def send_email_invites(cls, participants, **kwargs):
        for participant in participants:
            kwargs["name"] = participant.name
            kwargs["email"] = participant.email
            dispatcher = MeetingEmailNotificationDispatcher()
            dispatcher.send(**kwargs)
