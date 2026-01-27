from django.contrib import admin
from .models import (
    AmenitySlot,
    AmenityBlackoutPeriod,
    AmenityBooking,
    RecurrenceException,
)


@admin.register(AmenitySlot)
class AmenitySlotAdmin(admin.ModelAdmin):
    list_display = [
        "display_id",
        "amenity",
        "slot_date",
        "slot_start_time",
        "slot_end_time",
        "is_available",
        "total_bookings",
    ]
    list_filter = ["amenity", "slot_date", "is_available", "active"]
    search_fields = ["amenity__name", "display_id"]
    readonly_fields = [
        "display_id",
        "created_on",
        "updated_on",
        "created_by",
        "updated_by",
    ]
    fieldsets = (
        ("Identification", {"fields": ("display_id", "amenity")}),
        (
            "Timing",
            {
                "fields": (
                    "slot_date",
                    "slot_start_time",
                    "slot_end_time",
                    "slot_duration_minutes",
                )
            },
        ),
        (
            "Booking Info",
            {"fields": ("is_available", "total_bookings", "max_concurrent_bookings")},
        ),
        ("Status", {"fields": ("active",)}),
        (
            "Audit",
            {
                "fields": ("created_on", "updated_on", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )
    date_hierarchy = "slot_date"


@admin.register(AmenityBlackoutPeriod)
class AmenityBlackoutPeriodAdmin(admin.ModelAdmin):
    list_display = [
        "display_id",
        "amenity",
        "start_date",
        "end_date",
        "start_time",
        "end_time",
        "reason",
        "active",
    ]
    list_filter = ["amenity", "start_date", "active", "created_by"]
    search_fields = ["amenity__name", "reason", "display_id"]
    readonly_fields = [
        "display_id",
        "created_on",
        "updated_on",
        "created_by",
        "updated_by",
    ]
    fieldsets = (
        ("Identification", {"fields": ("display_id", "amenity")}),
        ("Date Range", {"fields": ("start_date", "end_date")}),
        (
            "Time Range (Optional)",
            {"fields": ("start_time", "end_time"), "classes": ("collapse",)},
        ),
        ("Details", {"fields": ("reason", "created_by")}),
        ("Status", {"fields": ("active",)}),
        (
            "Audit",
            {
                "fields": ("created_on", "updated_on", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )
    date_hierarchy = "start_date"


@admin.register(AmenityBooking)
class AmenityBookingAdmin(admin.ModelAdmin):
    list_display = [
        "display_id",
        "amenity",
        "tenant",
        "booking_date",
        "start_time",
        "end_time",
        "status",
        "is_recurring",
    ]
    list_filter = ["status", "booking_date", "amenity", "is_recurring", "created_by"]
    search_fields = [
        "tenant__user__first_name",
        "tenant__user__last_name",
        "amenity__name",
        "display_id",
    ]
    readonly_fields = [
        "display_id",
        "requested_on",
        "confirmed_on",
        "rejected_on",
        "cancelled_on",
        "created_on",
        "updated_on",
    ]
    fieldsets = (
        ("Identification", {"fields": ("display_id", "amenity", "tenant")}),
        (
            "Booking Details",
            {"fields": ("booking_date", "start_time", "end_time", "booking_notes")},
        ),
        (
            "Status",
            {
                "fields": (
                    "status",
                    "rejection_reason",
                    "rejection_remarks",
                    "cancellation_reason",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "requested_on",
                    "confirmed_on",
                    "rejected_on",
                    "cancelled_on",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Recurring (if applicable)",
            {
                "fields": (
                    "is_recurring",
                    "parent_booking",
                    "repeat_frequency",
                    "repeat_interval",
                    "repeat_on_days_of_week",
                    "repeat_on_day_of_month",
                    "recurrence_end_type",
                    "recurrence_end_date",
                    "recurrence_occurrences",
                    "occurrence_date",
                    "recurrence_sequence",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Other", {"fields": ("notification_sent", "created_by")}),
        (
            "Audit",
            {
                "fields": ("created_on", "updated_on", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )
    date_hierarchy = "booking_date"


@admin.register(RecurrenceException)
class RecurrenceExceptionAdmin(admin.ModelAdmin):
    list_display = ["parent_booking", "occurrence_date", "exception_type", "reason"]
    list_filter = ["exception_type", "occurrence_date", "modified_by"]
    search_fields = ["parent_booking__display_id", "reason"]
    readonly_fields = ["created_on", "updated_on"]
    fieldsets = (
        ("Recurring Booking", {"fields": ("parent_booking", "occurrence_date")}),
        ("Exception Details", {"fields": ("exception_type", "reason", "modified_by")}),
        (
            "Modifications (if applicable)",
            {
                "fields": ("new_start_time", "new_end_time", "new_booking_date"),
                "classes": ("collapse",),
            },
        ),
        ("Audit", {"fields": ("created_on", "updated_on"), "classes": ("collapse",)}),
    )
