from datetime import datetime
from django.db import models

from audit.models import GenericModel
from common.constants import UTC_TIMEZONE
from common.models import optional
from meetings.constants import (
    MeetingType,
    ParticipationType,
    MessageLevel,
    MessageType,
    MeetingEngagementType,
    MEETING_LINK,
)
from residents.models import Resident
from staff.models import HelixStaff


class Meeting(GenericModel):
    title = models.CharField(max_length=512, **optional)
    host = models.ForeignKey(HelixStaff, on_delete=models.CASCADE)
    room_name = models.CharField(max_length=50, unique=True, **optional)
    meeting_type = models.CharField(
        choices=MeetingType.choices(),
        max_length=50,
        default=MeetingType.ON_DEMAND.value,
    )
    participation_type = models.CharField(
        choices=ParticipationType.choices(),
        max_length=50,
        default=ParticipationType.INVITE_ONLY.value,
    )
    engagement_type = models.CharField(
        choices=MeetingEngagementType.choices(), max_length=50, **optional
    )
    patients_in_participation = models.BooleanField(default=False)
    last_session = models.CharField(max_length=50, **optional)
    last_session_active = models.BooleanField(default=False)
    active = models.BooleanField(default=False)

    @property
    def link(self):
        # Lazy import to avoid circular dependency during Django startup
        from customer_backend.managers.tenant import TenantManager

        domain = TenantManager().tenant_obj.domain
        return MEETING_LINK.format(
            domain=domain, meeting_id=str(self.id), room_name=self.room_name
        )

    @property
    def host_name(self):
        return self.host.name


class MeetingParticipant(GenericModel):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    staff = models.ForeignKey(
        HelixStaff, on_delete=models.CASCADE, **optional, related_name="staff_meeting"
    )
    patient = models.ForeignKey(
        Resident, on_delete=models.CASCADE, **optional, related_name="patient_meeting"
    )
    is_host = models.BooleanField(default=False)
    invited = models.BooleanField(default=False)

    class Meta:
        unique_together = (("meeting", "patient"), ("meeting", "staff"))

    @property
    def is_staff(self):
        return self.staff is not None and self.patient is None

    @property
    def id_of_participant(self):
        if self.staff:
            return str(self.staff.id)
        return str(self.patient.id)

    @property
    def name(self):
        if self.staff:
            return str(self.staff.name)

        return str(self.patient.name)

    @property
    def email(self):
        if self.staff is not None:
            return self.staff.user.email

        return self.patient.user.email


class MeetingSession(GenericModel):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=50, unique=True)
    empty_timeout = models.IntegerField(**optional)
    max_participants = models.IntegerField(**optional)
    creation_time = models.DateTimeField(**optional)
    close_time = models.DateTimeField(**optional)
    enabled_codecs = models.JSONField(**optional)
    departure_timeout = models.IntegerField(**optional)
    active = models.BooleanField(default=False)

    def close(self):
        self.active = False
        self.close_time = datetime.now(tz=UTC_TIMEZONE)
        self.save()
        return self

    @property
    def duration_in_seconds(self):
        seconds = None
        if self.close_time and not self.active:
            seconds = self.close_time - self.created_on
        elif not self.close_time and self.active:
            seconds = datetime.now(tz=UTC_TIMEZONE) - self.created_on

        return seconds.total_seconds() if seconds else None


class MeetingMessage(GenericModel):
    session = models.ForeignKey(MeetingSession, on_delete=models.CASCADE)
    sender = models.ForeignKey(
        MeetingParticipant, on_delete=models.CASCADE, related_name="message_sender"
    )
    receiver = models.ForeignKey(
        MeetingParticipant,
        on_delete=models.CASCADE,
        related_name="message_receiver",
        **optional,
    )
    parent = models.ForeignKey(
        to="self", on_delete=models.CASCADE, db_index=True, **optional
    )
    message_level = models.CharField(
        choices=MessageLevel.choices(),
        max_length=20,
        db_index=True,
        default=MessageLevel.ROOT.value,
    )
    message_type = models.CharField(
        choices=MessageType.choices(), max_length=20, default=MessageType.NON_LEAF.value
    )
    content = models.TextField()
