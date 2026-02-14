from django.urls import reverse
from django.utils.html import format_html

from django.contrib import admin
from common.constants import (
    IST_TIMEZONE,
    CUSTOM_READABLE_TIMESTAMP,
    UTC_TIMEZONE,
)


class PULSEBaseAdmin(admin.ModelAdmin):
    readonly_fields = ("created_by", "updated_by", "deleted_by")

    @classmethod
    def _get_readable_timestamp(cls, obj, timestamp_field, tz=IST_TIMEZONE):
        if not hasattr(obj, timestamp_field) or (
            hasattr(obj, timestamp_field) and not getattr(obj, timestamp_field)
        ):
            return
        timezoned_field = getattr(obj, timestamp_field).astimezone(tz=tz)
        return timezoned_field.strftime(CUSTOM_READABLE_TIMESTAMP)

    @classmethod
    def created_on_utc(cls, obj):
        return cls._get_readable_timestamp(obj, "created_on", tz=UTC_TIMEZONE)

    @classmethod
    def created_on_ist(cls, obj):
        return cls._get_readable_timestamp(obj, "created_on")

    @classmethod
    def updated_on_ist(cls, obj):
        return cls._get_readable_timestamp(obj, "updated_on")

    @classmethod
    def _get_admin_changelist_link(cls, app, model, obj_id, link_text=None):
        link = reverse(f"admin:{app}_{model}_changelist")
        full_url = f"{link}?q={obj_id}"
        link_text = link_text if link_text else obj_id
        return format_html('<a href="{}">{}</a>', full_url, link_text)
