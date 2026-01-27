from rest_framework import serializers

from meetings.models import MeetingSession
from meetings.serializers.meeting import MeetingSerializer


class MeetingSessionSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(
        source="meeting.room_name", read_only=True, required=False
    )
    meeting = MeetingSerializer(read_only=True, required=False)
    duration_in_seconds = serializers.SerializerMethodField()
    meeting_id = serializers.CharField(write_only=True)

    class Meta:
        model = MeetingSession
        fields = "__all__"

    @staticmethod
    def get_duration_in_seconds(obj):
        return obj.duration_in_seconds
