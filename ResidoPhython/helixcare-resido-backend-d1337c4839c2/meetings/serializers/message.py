from rest_framework import serializers

from meetings.models import MeetingMessage
from meetings.serializers.participant import MeetingParticipantSerializer


class MeetingMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingMessage
        fields = "__all__"

    def to_representation(self, instance):
        representation = super(MeetingMessageSerializer, self).to_representation(
            instance=instance
        )
        sender_representation = MeetingParticipantSerializer(
            instance=instance.sender
        ).data
        representation["sender"] = sender_representation
        if instance.receiver:
            receiver_representation = MeetingParticipantSerializer(
                instance=instance.receiver
            ).data
            representation["receiver"] = receiver_representation

        return representation
