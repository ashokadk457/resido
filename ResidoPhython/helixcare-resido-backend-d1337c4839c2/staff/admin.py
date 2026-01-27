from django.contrib import admin

from common.utils.admin import PULSEBaseAdmin
from staff.models import HelixStaff, NPIOverrides


# Register your models here.
@admin.register(HelixStaff)
class HelixStaffAdmin(PULSEBaseAdmin):
    list_display = (
        "id",
        "display_id",
        "user",
        "created_on_ist",
        "updated_on_ist",
        # "visit_type_configs",
    )
    ordering = ["-created_on"]
    list_per_page = 25
    search_fields = (
        "id",
        "display_id",
        "user__first_name",
        "user__last_name",
        "user__email",
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            # All model fields as read_only
            return self.readonly_fields + tuple(
                [item.name for item in obj._meta.fields]
            )
        return self.readonly_fields

    # def visit_type_configs(self, obj):
    #     _obj_id, link_text = (
    #         str(obj.id),
    #         "View Visit Type Configurations",
    #     )
    #     if not _obj_id:
    #         return _obj_id

    #     return self._get_admin_changelist_link(
    #         app="scheduling",
    #         model="staffvisittype",
    #         obj_id=_obj_id,
    #         link_text=link_text,
    #     )


admin.site.register(NPIOverrides)
