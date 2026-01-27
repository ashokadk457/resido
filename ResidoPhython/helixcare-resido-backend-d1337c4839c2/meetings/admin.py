from django.contrib import admin

from meetings.models import Meeting, MeetingParticipant


# Register your models here.
@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "host",
        "room_name",
        "meeting_type",
        "participation_type",
        "active",
        "created_on",
        "updated_on",
    )


@admin.register(MeetingParticipant)
class MeetingParticipantAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "meeting",
        "staff",
        "patient",
        "is_host",
        "invited",
        "created_on",
        "updated_on",
    )
