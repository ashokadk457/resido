from uuid import UUID

from rest_framework import serializers

from meetings.models import MeetingParticipant


class MeetingParticipantSerializer(serializers.ModelSerializer):
    staff_first_name = serializers.CharField(
        source="staff.user.first_name", read_only=True, required=False
    )
    staff_last_name = serializers.CharField(
        source="staff.user.last_name", read_only=True, required=False
    )
    staff_role = serializers.CharField(
        source="staff.role.role_name", read_only=True, required=False
    )
    staff_gender = serializers.CharField(
        source="staff.user.gender", read_only=True, required=False
    )
    staff_provider_type = serializers.CharField(
        source="staff.provider_type", read_only=True, required=False
    )
    staff_age = serializers.CharField(
        source="staff.age", read_only=True, required=False
    )
    patient_first_name = serializers.CharField(
        source="patient.first_name", read_only=True, required=False
    )
    patient_last_name = serializers.CharField(
        source="patient.last_name", read_only=True, required=False
    )
    patient_gender = serializers.CharField(
        source="patient.gender", read_only=True, required=False
    )
    patient_age = serializers.CharField(
        source="patient.age", read_only=True, required=False
    )

    class Meta:
        model = MeetingParticipant
        fields = "__all__"

    def to_representation(self, instance):
        representation = super(MeetingParticipantSerializer, self).to_representation(
            instance
        )
        if not self.context.get("prefixed"):
            return representation

        return {
            f"participant_{key}": str(val) if isinstance(val, UUID) else val
            for key, val in representation.items()
        }
