from meetings.constants import MeetingEvent
from meetings.managers.session import MeetingSessionManager


class MeetingEventProcessor:
    def __init__(
        self,
        meeting_id=None,
        session_id=None,
        room_name=None,
        event=None,
    ):
        self.meeting_id = meeting_id
        self.session_id = session_id
        self.room_name = room_name
        self.event = event

    def process(self):
        if self.event is None:
            return None

        if self.event == MeetingEvent.ROOM_FINISHED.value:
            return self._process_room_finished()

    def _process_room_finished(self):
        session_manager = MeetingSessionManager.init(
            meeting_id=self.meeting_id, session_id=self.session_id
        )
        if not session_manager:
            return False

        session_manager.close_session()
        return True
