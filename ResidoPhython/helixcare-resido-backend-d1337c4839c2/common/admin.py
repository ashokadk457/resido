from django.contrib import admin
from django_tenants.admin import TenantAdminMixin

from common.models import HealthCareCustomer, Domain, HealthCareCustomerConfig
from common.utils.admin import PULSEBaseAdmin


class DomainInline(admin.TabularInline):
    model = Domain
    max_num = 1
    fields = ("domain",)


@admin.register(HealthCareCustomer)
class HealthCareCustomerAdmin(TenantAdminMixin, PULSEBaseAdmin):
    list_display = (
        "id",
        "name",
        "domain",
        "schema_name",
        "realm",
        "client_id",
        "client_secret",
        "client_uuid",
        "created_on_ist",
        "updated_on_ist",
    )
    fields = [
        "name",
        "schema_name",
        "app_conf_type",
        "allow_ext_providers",
        "url",
        "max_security_question",
        "code",
        "website",
        "address",
        "address_1",
        "city",
        "state",
        "zipcode",
        "contact_prefix",
        "contact_first_name",
        "contact_last_name",
        "contact_suffix",
        "work_phone",
        "phone",
        "fax",
        "email",
        "preferred_communication_mode",
        "status",
        "max_age_of_minor",
        "s2s_public_key",
        "realm",
        "client_id",
        "client_secret",
        "client_uuid",
        "realm_admin",
        "realm_password",
    ]
    inlines = (DomainInline,)


@admin.register(HealthCareCustomerConfig)
class HealthCareCustomerConfigAdmin(PULSEBaseAdmin):
    list_display = (
        "id",
        "customer",
        "is_payment_processing_enabled",
        "is_maintenance_module_enabled",
        "is_booking_module_enabled",
        "is_analytics_enabled",
        "resident_portal_enabled",
        "created_on_ist",
        "updated_on_ist",
    )
    list_filter = (
        "is_payment_processing_enabled",
        "is_maintenance_module_enabled",
        "is_booking_module_enabled",
        "is_analytics_enabled",
        "resident_portal_enabled",
    )
    search_fields = ("customer__name", "customer__schema_name")
    readonly_fields = ("created_on_ist", "updated_on_ist")
    fieldsets = (
        (
            "Tenant Information",
            {"fields": ("customer",)},
        ),
        (
            "Module Features",
            {
                "fields": (
                    "is_payment_processing_enabled",
                    "is_maintenance_module_enabled",
                    "is_booking_module_enabled",
                    "is_analytics_enabled",
                    "is_digital_forms_enabled",
                )
            },
        ),
        (
            "Payment Configuration",
            {
                "fields": (
                    "payment_grace_period_days",
                    "late_fee_enabled",
                    "auto_payment_reminder_days",
                )
            },
        ),
        (
            "Maintenance Settings",
            {
                "fields": (
                    "maintenance_auto_assignment_enabled",
                    "maintenance_sla_hours",
                )
            },
        ),
        (
            "Resident Portal",
            {
                "fields": (
                    "resident_portal_enabled",
                    "self_service_enabled",
                )
            },
        ),
        (
            "Additional Settings",
            {"fields": ("notification_preferences",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_on_ist", "updated_on_ist")},
        ),
    )
