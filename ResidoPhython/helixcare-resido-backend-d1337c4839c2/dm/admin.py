# Register your models here.
from django.contrib import admin

from common.utils.admin import PULSEBaseAdmin
from dm.models import DataMigrationExecution


# Register your models here.
@admin.register(DataMigrationExecution)
class DataMigrationExecutionAdmin(PULSEBaseAdmin):
    list_display = (
        "id",
        "task",
        "execution_version",
        "status",
        "created_on",
        "updated_on",
    )
    ordering = ["-created_on"]
    list_per_page = 25
    list_filter = ("status",)
    search_fields = ("id", "execution_version", "task")
