from uuid import UUID

from rest_framework import serializers

from meetings.constants import MeetingEngagementType
from meetings.models import Meeting
from meetings.serializers.participant import MeetingParticipantSerializer


class MeetingSerializerTrimmed(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = [
            "id",
            "title",
            "host",
            "room_name",
            "last_session",
            "last_session_active",
            "meeting_type",
            "active",
        ]

    def to_representation(self, instance):
        representation = super(MeetingSerializerTrimmed, self).to_representation(
            instance
        )
        representation_mod = {
            f"meeting_{key}": str(val) if isinstance(val, UUID) else val
            for key, val in representation.items()
        }
        appointment = instance.appointment_set.first()
        if appointment:
            representation_mod["meeting_appointment_id"] = str(appointment.id)

        return representation_mod


class MeetingSerializer(serializers.ModelSerializer):
    participants = serializers.JSONField(required=False, write_only=True)
    link = serializers.SerializerMethodField(required=False, read_only=True)

    class Meta:
        model = Meeting
        fields = "__all__"

    @staticmethod
    def get_link(obj):
        return obj.link

    @staticmethod
    def derive_engagement_type_on_the_basis_of_participants_count(participant_count):
        if participant_count == 2:
            return MeetingEngagementType.ONE_ON_ONE.value

        if participant_count >= 3:
            return MeetingEngagementType.GROUP.value

    @staticmethod
    def derive_patient_presence_in_participants(participants):
        return bool(
            sum(
                1
                for participant in participants
                if participant.get("patient") is not None
            )
        )

    def create(self, validated_data):
        from meetings.managers.meeting import MeetingManager

        participants_data = validated_data.pop("participants", [])
        validated_data[
            "engagement_type"
        ] = self.derive_engagement_type_on_the_basis_of_participants_count(
            participant_count=len(participants_data)
        )
        validated_data[
            "patients_in_participation"
        ] = self.derive_patient_presence_in_participants(participants=participants_data)
        meeting_manager = MeetingManager()
        meeting_obj = meeting_manager.setup_new_meeting(meeting_data=validated_data)
        meeting_manager.set_participants(participants_data=participants_data)

        return meeting_obj

    def to_representation(self, instance):
        meeting_representation = super(MeetingSerializer, self).to_representation(
            instance
        )

        participants = instance.meetingparticipant_set.all()
        participant_serializer = MeetingParticipantSerializer(participants, many=True)
        participant_representation_dict = participant_serializer.data

        meeting_representation["participants"] = participant_representation_dict

        return meeting_representation
