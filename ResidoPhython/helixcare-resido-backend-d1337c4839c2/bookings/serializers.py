from rest_framework import serializers
from common.serializers import BaseSerializer
from .models import (
    AmenitySlot,
    AmenityBlackoutPeriod,
    AmenityBooking,
    RecurrenceException,
)
from locations.models import Amenity
from residents.models import Resident


class AmenitySlotSerializer(BaseSerializer):
    amenity = serializers.UUIDField(
        write_only=True
    )  # Accept amenity UUID in POST/PATCH
    amenity_name = serializers.CharField(source="amenity.name", read_only=True)
    is_fully_booked = serializers.BooleanField(read_only=True)

    class Meta:
        model = AmenitySlot
        fields = [
            "id",
            "display_id",
            "amenity",
            "amenity_id",
            "amenity_name",
            "slot_date",
            "slot_start_time",
            "slot_end_time",
            "slot_duration_minutes",
            "is_available",
            "total_bookings",
            "max_concurrent_bookings",
            "is_fully_booked",
            "active",
            "created_on",
            "updated_on",
        ]
        read_only_fields = [
            "amenity_id",
            "display_id",
            "total_bookings",
            "is_fully_booked",
            "created_on",
            "updated_on",
        ]

    def create(self, validated_data):
        from locations.models import Amenity

        amenity_uuid = validated_data.pop("amenity")
        try:
            validated_data["amenity"] = Amenity.objects.get(id=amenity_uuid)
        except Amenity.DoesNotExist:
            raise serializers.ValidationError({"amenity": "Amenity not found"})
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "amenity" in validated_data:
            amenity_uuid = validated_data.pop("amenity")
            try:
                validated_data["amenity"] = Amenity.objects.get(id=amenity_uuid)
            except Amenity.DoesNotExist:
                raise serializers.ValidationError({"amenity": "Amenity not found"})
        return super().update(instance, validated_data)


class BlackoutPeriodSerializer(BaseSerializer):
    amenity = serializers.UUIDField(
        write_only=True
    )  # Accept amenity UUID in POST/PATCH
    amenity_name = serializers.CharField(source="amenity.name", read_only=True)
    created_by_name = serializers.CharField(
        source="created_by.user.get_full_name", read_only=True, allow_null=True
    )

    class Meta:
        model = AmenityBlackoutPeriod
        fields = [
            "id",
            "display_id",
            "amenity",
            "amenity_id",
            "amenity_name",
            "start_date",
            "end_date",
            "start_time",
            "end_time",
            "reason",
            "created_by_id",
            "created_by_name",
            "active",
            "created_on",
            "updated_on",
        ]
        read_only_fields = ["amenity_id", "display_id", "created_on", "updated_on"]

    def create(self, validated_data):
        from locations.models import Amenity

        amenity_uuid = validated_data.pop("amenity")
        try:
            validated_data["amenity"] = Amenity.objects.get(id=amenity_uuid)
        except Amenity.DoesNotExist:
            raise serializers.ValidationError({"amenity": "Amenity not found"})
        return super().create(validated_data)

    def update(self, instance, validated_data):
        from locations.models import Amenity

        if "amenity" in validated_data:
            amenity_uuid = validated_data.pop("amenity")
            try:
                validated_data["amenity"] = Amenity.objects.get(id=amenity_uuid)
            except Amenity.DoesNotExist:
                raise serializers.ValidationError({"amenity": "Amenity not found"})
        return super().update(instance, validated_data)


class RecurrenceExceptionSerializer(BaseSerializer):
    class Meta:
        model = RecurrenceException
        fields = [
            "id",
            "parent_booking_id",
            "occurrence_date",
            "exception_type",
            "new_start_time",
            "new_end_time",
            "new_booking_date",
            "reason",
            "created_on",
            "updated_on",
        ]
        read_only_fields = ["id", "created_on", "updated_on"]


class BookingSerializerForStaff(BaseSerializer):
    amenity = serializers.UUIDField(
        write_only=True
    )  # Accept amenity UUID in POST/PATCH
    tenant = serializers.UUIDField(write_only=True)  # Accept tenant UUID in POST/PATCH
    tenant_name = serializers.CharField(
        source="tenant.user.get_full_name", read_only=True
    )
    tenant_email = serializers.CharField(source="tenant.user.email", read_only=True)
    amenity_name = serializers.CharField(source="amenity.name", read_only=True)
    recurrence_exceptions = RecurrenceExceptionSerializer(many=True, read_only=True)
    instances_count = serializers.SerializerMethodField()

    class Meta:
        model = AmenityBooking
        fields = [
            "id",
            "display_id",
            "amenity",
            "amenity_id",
            "amenity_name",
            "tenant",
            "tenant_id",
            "tenant_name",
            "tenant_email",
            "booking_date",
            "start_time",
            "end_time",
            "status",
            "booking_notes",
            "selected_slot_ids",
            "rejection_reason",
            "rejection_remarks",
            "cancellation_reason",
            "requested_on",
            "confirmed_on",
            "rejected_on",
            "cancelled_on",
            "notification_sent",
            # Recurring fields
            "is_recurring",
            "parent_booking_id",
            "repeat_frequency",
            "repeat_interval",
            "repeat_on_days_of_week",
            "repeat_on_day_of_month",
            "recurrence_end_type",
            "recurrence_end_date",
            "recurrence_occurrences",
            "occurrence_date",
            "recurrence_sequence",
            "recurrence_exceptions",
            "instances_count",
            "created_on",
            "updated_on",
        ]
        read_only_fields = [
            "amenity_id",
            "tenant_id",
            "display_id",
            "requested_on",
            "confirmed_on",
            "rejected_on",
            "cancelled_on",
            "occurrence_date",
            "recurrence_sequence",
            "instances_count",
            "created_on",
            "updated_on",
            "status",  # Status should be set by model's default (PENDING)
        ]

    def get_instances_count(self, obj):
        """Count total recurring instances"""
        if obj.is_recurring and not obj.parent_booking:
            return obj.recurring_instances.count()
        return 0

    def create(self, validated_data):
        """Convert amenity and tenant UUIDs to instances"""
        from locations.models import Amenity
        from residents.models import Resident

        amenity_uuid = validated_data.pop("amenity")
        tenant_uuid = validated_data.pop("tenant")

        try:
            validated_data["amenity"] = Amenity.objects.get(id=amenity_uuid)
        except Amenity.DoesNotExist:
            raise serializers.ValidationError({"amenity": "Amenity not found"})

        try:
            validated_data["tenant"] = Resident.objects.get(id=tenant_uuid)
        except Resident.DoesNotExist:
            raise serializers.ValidationError({"tenant": "Tenant not found"})

        return super().create(validated_data)

    def update(self, instance, validated_data):
        from locations.models import Amenity
        from residents.models import Resident

        if "amenity" in validated_data:
            amenity_uuid = validated_data.pop("amenity")
            try:
                validated_data["amenity"] = Amenity.objects.get(id=amenity_uuid)
            except Amenity.DoesNotExist:
                raise serializers.ValidationError({"amenity": "Amenity not found"})

        if "tenant" in validated_data:
            tenant_uuid = validated_data.pop("tenant")
            try:
                validated_data["tenant"] = Resident.objects.get(id=tenant_uuid)
            except Resident.DoesNotExist:
                raise serializers.ValidationError({"tenant": "Tenant not found"})

        return super().update(instance, validated_data)


class BookingSerializerForTenant(BaseSerializer):
    amenity = serializers.UUIDField(write_only=True)
    tenant = serializers.UUIDField(write_only=True)
    amenity_name = serializers.CharField(source="amenity.name", read_only=True)
    amenity_capacity = serializers.IntegerField(
        source="amenity.capacity", read_only=True
    )
    instances_count = serializers.SerializerMethodField()

    class Meta:
        model = AmenityBooking
        fields = [
            "id",
            "display_id",
            "amenity",
            "amenity_id",
            "amenity_name",
            "amenity_capacity",
            "tenant",
            "tenant_id",
            "booking_date",
            "start_time",
            "end_time",
            "status",
            "booking_notes",
            "selected_slot_ids",
            "rejection_reason",
            "rejection_remarks",
            "requested_on",
            "confirmed_on",
            "rejected_on",
            # Recurring info (simplified)
            "is_recurring",
            "repeat_frequency",
            "instances_count",
            "created_on",
        ]
        read_only_fields = [
            "amenity_id",
            "tenant_id",
            "status",
            "confirmed_on",
            "rejected_on",
            "rejection_reason",
            "rejection_remarks",
            "created_on",
            "instances_count",
        ]

    def get_instances_count(self, obj):
        if obj.is_recurring and not obj.parent_booking:
            return obj.recurring_instances.count()
        return 0

    def create(self, validated_data):
        from locations.models import Amenity
        from residents.models import Resident

        amenity_uuid = validated_data.pop("amenity")
        tenant_uuid = validated_data.pop("tenant")

        try:
            validated_data["amenity"] = Amenity.objects.get(id=amenity_uuid)
        except Amenity.DoesNotExist:
            raise serializers.ValidationError({"amenity": "Amenity not found"})

        try:
            validated_data["tenant"] = Resident.objects.get(id=tenant_uuid)
        except Resident.DoesNotExist:
            raise serializers.ValidationError({"tenant": "Tenant not found"})

        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "amenity" in validated_data:
            amenity_uuid = validated_data.pop("amenity")
            try:
                validated_data["amenity"] = Amenity.objects.get(id=amenity_uuid)
            except Amenity.DoesNotExist:
                raise serializers.ValidationError({"amenity": "Amenity not found"})

        if "tenant" in validated_data:
            tenant_uuid = validated_data.pop("tenant")
            try:
                validated_data["tenant"] = Resident.objects.get(id=tenant_uuid)
            except Resident.DoesNotExist:
                raise serializers.ValidationError({"tenant": "Tenant not found"})

        return super().update(instance, validated_data)


class BulkAmenitySlotCreationSerializer(serializers.Serializer):
    amenity_id = serializers.UUIDField(help_text="UUID of the amenity")
    from_date = serializers.DateField(
        help_text="Slot generation start date (YYYY-MM-DD)"
    )
    to_date = serializers.DateField(help_text="Slot generation end date (YYYY-MM-DD)")
    operating_start_time = serializers.TimeField(
        help_text="Daily operating start time (HH:MM:SS)"
    )
    operating_end_time = serializers.TimeField(
        help_text="Daily operating end time (HH:MM:SS)"
    )
    interval_minutes = serializers.IntegerField(
        default=60,
        min_value=15,
        max_value=480,
        help_text="Slot duration in minutes (15-480)",
    )
    max_concurrent_bookings = serializers.IntegerField(
        default=1, min_value=1, help_text="Max concurrent bookings per slot"
    )
    delete_existing = serializers.BooleanField(
        default=False,
        help_text="If True, delete existing slots for this date range first",
    )

    def validate(self, data):
        if data["from_date"] > data["to_date"]:
            raise serializers.ValidationError(
                "from_date must be before or equal to to_date"
            )

        if data["operating_start_time"] >= data["operating_end_time"]:
            raise serializers.ValidationError(
                "operating_start_time must be before operating_end_time"
            )

        return data


class BulkSlotCreationResultSerializer(serializers.Serializer):
    created_count = serializers.IntegerField(help_text="Number of slots created")
    updated_count = serializers.IntegerField(
        help_text="Number of slots updated due to blackout"
    )
    error_count = serializers.IntegerField(help_text="Number of errors encountered")
    errors = serializers.ListField(
        child=serializers.CharField(), help_text="List of error messages"
    )
    summary = serializers.CharField(help_text="Summary message")


class AvailableSlotSerializer(serializers.Serializer):
    date = serializers.DateField()
    slots = AmenitySlotSerializer(many=True, read_only=True)
    is_available_all_day = serializers.BooleanField()
    blackout_reason = serializers.CharField(allow_null=True)


class AmenitiesAndReservationsSummarySerializer(serializers.Serializer):
    amenities_count = serializers.IntegerField(help_text="Total number of amenities")
    bookings_count = serializers.IntegerField(help_text="Total number of bookings")
    blackout_periods_count = serializers.IntegerField(
        help_text="Total number of blackout periods"
    )
