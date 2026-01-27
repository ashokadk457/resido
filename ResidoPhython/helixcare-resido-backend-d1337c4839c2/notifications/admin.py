from django.contrib import admin

from notifications.models import (
    NotificationQueue,
    NotificationSetting,
    NotificationTypePriority,
    NotificationDL,
    NotificationUserDL,
    NotificationMessage,
    NotificationTemplate,
)

# Register your models here.

# admin.site.register(NotificationQueue)
# admin.site.register(NotificationSetting)
admin.site.register(NotificationTypePriority)
admin.site.register(NotificationDL)
admin.site.register(NotificationUserDL)
admin.site.register(NotificationMessage)
admin.site.register(NotificationTemplate)


@admin.register(NotificationQueue)
class NotificationQueueAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "receiving_address",
        "payload",
        "user",
        "provider",
        "sent_date",
        "received_date",
        "status",
        "error_code",
        "created_on",
        "updated_on",
    )
    list_filter = ("status", "priority")
    search_fields = ("id", "receiving_address")
    ordering = ("-created_on",)


@admin.register(NotificationSetting)
class NotificationSettingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "notification_type",
        "frequency",
        "language",
        "event_type",
        "when",
        "send_time",
        "message",
        "created_on",
        "updated_on",
    )
    list_filter = ("notification_type", "when", "language", "event_type")
    search_fields = ("id", "notification_type")
    ordering = ("-created_on",)
