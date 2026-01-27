import django_filters

from meetings.models import MeetingMessage, Meeting


class MeetingMessageFilter(django_filters.FilterSet):
    session = django_filters.CharFilter(field_name="session__id")
    meeting = django_filters.CharFilter(field_name="session__meeting__id")

    class Meta:
        model = MeetingMessage
        fields = ["session", "session__meeting__id"]


class MeetingFilter(django_filters.FilterSet):
    staff = django_filters.CharFilter(
        field_name="meetingparticipant__staff__id", lookup_expr="icontains"
    )
    patient = django_filters.CharFilter(
        field_name="meetingparticipant__patient__id", lookup_expr="icontains"
    )
    participation_type = django_filters.CharFilter(field_name="participation_type")
    engagement_type = django_filters.CharFilter(field_name="engagement_type")
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    active = django_filters.BooleanFilter(field_name="active")

    class Meta:
        model = Meeting
        fields = [
            "meetingparticipant__staff__id",
            "meetingparticipant__patient__id",
            "participation_type",
            "engagement_type",
            "title",
            "active",
        ]
