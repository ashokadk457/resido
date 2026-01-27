from django.contrib import admin
from .models import (
    Resident,
    EmergencyContact,
)


@admin.register(Resident)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_on",
        "updated_on",
    )
    search_fields = (
        "id",
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__phone_number",
        "user__date_of_birth",
    )


admin.site.register(EmergencyContact)
