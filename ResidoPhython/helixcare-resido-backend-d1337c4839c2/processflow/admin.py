from django.contrib import admin

from common.utils.admin import PULSEBaseAdmin
from processflow.models import Process


@admin.register(Process)
class ProcessAdmin(PULSEBaseAdmin):
    readonly_fields = (
        "created_by",
        "updated_by",
        "deleted_by",
        "periodic_task",
        "request_id",
        "task_id",
        "object_id",
        "object_name",
        "process_type",
        "trigger_type",
        "created_on",
        "updated_on",
        "report",
        "error_code",
        "error_body",
    )
    list_display = (
        "id",
        "periodic_task_name",
        "trigger_type",
        "request_id",
        "task_id",
        "object_id",
        "object_name",
        "process_type",
        "status",
        "active",
        "created_on_ist",
        "updated_on_ist",
    )
    ordering = ["-created_on"]
    list_per_page = 25
    search_fields = ("id", "request_id", "task_id", "object_id", "object_name")
    list_filter = (
        "status",
        "active",
        "process_type",
        "trigger_type",
    )

    @staticmethod
    def periodic_task_name(obj):
        if obj.periodic_task is None:
            return

        return obj.periodic_task.name
