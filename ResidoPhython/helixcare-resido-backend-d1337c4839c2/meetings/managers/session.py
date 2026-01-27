from meetings.models import MeetingSession
from meetings.serializers.session import MeetingSessionSerializer


class MeetingSessionManager:
    @classmethod
    def init(cls, meeting_id=None, session_id=None, session_obj=None):
        if session_id is not None and session_obj is None:
            session_obj = MeetingSession.objects.filter(session_id=session_id).first()

        if not session_obj:
            return None

        if not meeting_id:
            meeting_id = str(session_obj.meeting.id)

        return cls(
            meeting_id=meeting_id, session_id=session_id, session_obj=session_obj
        )

    def __init__(self, meeting_id, session_id=None, session_obj=None):
        self.meeting_id = meeting_id
        self.session_id = session_id
        self.session_obj = session_obj

    def create_new_session(self, session_data):
        if not session_data:
            return

        session_serializer = MeetingSessionSerializer(data=session_data)
        session_serializer.is_valid(raise_exception=True)
        self.session_obj = session_serializer.save()
        self.session_id = str(self.session_obj.id)

        meeting_obj = self.update_last_session_info(active=True)

        return self.session_obj, meeting_obj

    def update_last_session_info(self, active):
        meeting_obj = self.session_obj.meeting
        meeting_obj.last_session = str(self.session_obj.id)
        meeting_obj.last_session_active = active
        meeting_obj.save()
        return meeting_obj

    def get_session_representation(self):
        if not self.session_obj:
            return None

        return MeetingSessionSerializer(instance=self.session_obj).data

    def close_session(self):
        if not self.session_obj:
            return

        self.session_obj = self.session_obj.close()
        self.update_last_session_info(active=False)
        return self.session_obj
