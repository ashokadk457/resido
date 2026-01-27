from django.db import models
from django.core.exceptions import ValidationError
from audit.models import GenericModel
from common.models import optional
from common.utils.general import get_display_id
from lookup.fields import LookupField
from locations.models import Amenity
from residents.models import Resident
from staff.models import HelixStaff
from .constants import BookingStatus, RecurringFrequency


class AmenitySlot(GenericModel):
    display_id = models.CharField(max_length=100, **optional)
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE, related_name="slots")
    slot_date = models.DateField(db_index=True)
    slot_start_time = models.TimeField()
    slot_end_time = models.TimeField()
    slot_duration_minutes = models.IntegerField(default=30)
    is_available = models.BooleanField(default=True, db_index=True)
    total_bookings = models.IntegerField(default=0)  # Current booking count
    max_concurrent_bookings = models.IntegerField(default=1)  # Max allowed
    active = models.BooleanField(default=True, db_index=True)

    class Meta:
        unique_together = [("amenity", "slot_date", "slot_start_time")]
        path_to_location = "amenity__building__location"
        indexes = [
            models.Index(fields=["amenity", "slot_date"]),
            models.Index(fields=["amenity", "slot_date", "is_available"]),
        ]
        verbose_name = "Amenity Slot"
        verbose_name_plural = "Amenity Slots"

    def __str__(self):
        return f"{self.amenity.name} - {self.slot_date} {self.slot_start_time}"

    def save(self, *args, **kwargs):
        if not self.display_id:
            self.display_id = get_display_id(self, "SLOT")
        return super().save(*args, **kwargs)

    def clean(self):
        if self.slot_start_time >= self.slot_end_time:
            raise ValidationError("Slot start time must be before end time")

    @property
    def is_fully_booked(self):
        return self.total_bookings >= self.max_concurrent_bookings


class AmenityBlackoutPeriod(GenericModel):
    display_id = models.CharField(max_length=100, **optional)
    amenity = models.ForeignKey(
        Amenity, on_delete=models.CASCADE, related_name="blackout_periods"
    )
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    start_time = models.TimeField(**optional)
    end_time = models.TimeField(**optional)
    reason = models.TextField()
    created_by = models.ForeignKey(
        HelixStaff,
        on_delete=models.SET_NULL,
        null=True,
        related_name="blackout_periods_created",
    )
    active = models.BooleanField(default=True, db_index=True)

    class Meta:
        path_to_location = "amenity__building__location"
        indexes = [
            models.Index(fields=["amenity", "start_date", "end_date"]),
            models.Index(fields=["amenity", "active", "start_date"]),
        ]
        verbose_name = "Amenity Blackout Period"
        verbose_name_plural = "Amenity Blackout Periods"

    def __str__(self):
        return f"{self.amenity.name} - Blackout {self.start_date} to {self.end_date}"

    def set_created_by_and_updated_by(self):
        from helixauth.models import HelixUser
        from common.thread_locals import get_current_user

        current_user = get_current_user()
        if not isinstance(current_user, HelixUser):
            return

        # Set created_by to HelixStaff if available (only on creation)
        if self._state.adding and hasattr(current_user, "helixstaff"):
            self.created_by = current_user.helixstaff

        self.updated_by = current_user

    def save(self, *args, **kwargs):
        if not self.display_id:
            self.display_id = get_display_id(self, "BLKOUT")
        return super().save(*args, **kwargs)

    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError("Start date must be before or equal to end date")

        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("Start time must be before end time")


class AmenityBooking(GenericModel):
    display_id = models.CharField(
        max_length=100, unique=True, editable=False, **optional
    )

    amenity = models.ForeignKey(
        Amenity, on_delete=models.CASCADE, related_name="bookings"
    )
    tenant = models.ForeignKey(
        Resident, on_delete=models.CASCADE, related_name="amenity_bookings"
    )
    slot = models.ForeignKey(
        AmenitySlot,
        on_delete=models.SET_NULL,
        null=True,
        related_name="bookings",
        help_text="Associated slot if created from slot",
    )
    selected_slot_ids = models.JSONField(
        default=list,
        blank=True,
        help_text="List of selected AmenitySlot UUIDs for extended bookings",
    )
    booking_date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    booking_notes = models.TextField(**optional)
    status = models.CharField(
        max_length=50,
        choices=BookingStatus.choices(),
        default=BookingStatus.PENDING.value,
        db_index=True,
    )
    rejection_reason = LookupField(
        max_length=100, lookup_name="BOOKING_REJECTION_REASON", **optional
    )
    rejection_remarks = models.TextField(**optional)
    cancellation_reason = models.TextField(**optional)
    requested_on = models.DateTimeField(auto_now_add=True)
    confirmed_on = models.DateTimeField(**optional)
    rejected_on = models.DateTimeField(**optional)
    cancelled_on = models.DateTimeField(**optional)
    created_by = models.ForeignKey(
        HelixStaff,
        on_delete=models.SET_NULL,
        null=True,
        related_name="bookings_confirmed",
    )
    notification_sent = models.BooleanField(default=False)
    is_recurring = models.BooleanField(default=False, db_index=True)
    parent_booking = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        related_name="recurring_instances",
        help_text="Parent booking if this is a recurring instance",
    )
    repeat_frequency = models.CharField(
        max_length=50,
        choices=RecurringFrequency.choices(),
        null=True,
        blank=True,
        help_text="DAILY, WEEKLY, MONTHLY, YEARLY",
    )
    repeat_interval = models.IntegerField(
        default=1, help_text="Every N days/weeks/months (e.g., 2 = every 2 weeks)"
    )
    repeat_on_days_of_week = models.JSONField(
        default=list, blank=True, help_text='["monday", "wednesday", "friday"]'
    )
    repeat_on_day_of_month = models.IntegerField(
        null=True, blank=True, help_text="1-31 or -1 for last day"
    )
    recurrence_end_type = models.CharField(
        max_length=50,
        choices=[
            ("never", "Never ends"),
            ("after_occurrences", "After N occurrences"),
            ("on_date", "On specific date"),
        ],
        default="never",
    )
    recurrence_end_date = models.DateField(
        null=True, blank=True, help_text="Last date to create recurring bookings"
    )
    recurrence_occurrences = models.IntegerField(
        null=True, blank=True, help_text="Total number of occurrences to generate"
    )
    occurrence_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text="For recurring instances, the date of this occurrence",
    )
    recurrence_sequence = models.IntegerField(
        null=True,
        blank=True,
        help_text="Occurrence number in the series (1st, 2nd, 3rd...)",
    )

    class Meta:
        path_to_location = "amenity__building__location"
        indexes = [
            models.Index(fields=["amenity", "booking_date"]),
            models.Index(fields=["amenity", "booking_date", "status"]),
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["status", "booking_date"]),
            models.Index(fields=["is_recurring", "parent_booking"]),
            models.Index(fields=["parent_booking", "occurrence_date"]),
        ]
        verbose_name = "Amenity Booking"
        verbose_name_plural = "Amenity Bookings"

    def __str__(self):
        return f"{self.display_id} - {self.amenity.name} ({self.status})"

    def set_created_by_and_updated_by(self):
        from helixauth.models import HelixUser
        from common.thread_locals import get_current_user

        current_user = get_current_user()
        if not isinstance(current_user, HelixUser):
            return
        self.updated_by = current_user

    def save(self, *args, **kwargs):
        if not self.display_id:
            self.display_id = get_display_id(self, "BKG")
        return super().save(*args, **kwargs)

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")

    def confirm_booking(self, confirmed_by=None):
        from django.utils import timezone

        if self.status != BookingStatus.PENDING.value:
            raise ValidationError(f"Cannot confirm {self.status} booking")

        self.status = BookingStatus.CONFIRMED.value
        self.confirmed_on = timezone.now()
        if confirmed_by:
            self.created_by = confirmed_by
        self.save()
        return self

    def reject_booking(self, reason, remarks, rejected_by=None):
        from django.utils import timezone

        if self.status != BookingStatus.PENDING.value:
            raise ValidationError(f"Cannot reject {self.status} booking")

        self.status = BookingStatus.REJECTED.value
        self.rejection_reason = reason
        self.rejection_remarks = remarks
        self.rejected_on = timezone.now()
        if rejected_by:
            self.created_by = rejected_by
        self.save()
        return self

    def cancel_booking(self, reason=None):
        from django.utils import timezone

        if self.status not in [
            BookingStatus.CONFIRMED.value,
            BookingStatus.PENDING.value,
        ]:
            raise ValidationError(f"Cannot cancel {self.status} booking")

        self.status = BookingStatus.CANCELLED.value
        self.cancellation_reason = reason
        self.cancelled_on = timezone.now()
        self.save()
        return self


class RecurrenceException(GenericModel):
    parent_booking = models.ForeignKey(
        AmenityBooking, on_delete=models.CASCADE, related_name="recurrence_exceptions"
    )
    occurrence_date = models.DateField(db_index=True)

    exception_type = models.CharField(
        max_length=50,
        choices=[
            ("skip", "Skip this occurrence"),
            ("modify", "Modify this occurrence"),
            ("cancel", "Cancel this occurrence"),
        ],
    )

    new_start_time = models.TimeField(null=True, blank=True)
    new_end_time = models.TimeField(null=True, blank=True)
    new_booking_date = models.DateField(null=True, blank=True)

    reason = models.TextField(blank=True)
    modified_by = models.ForeignKey(HelixStaff, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = [("parent_booking", "occurrence_date")]
        path_to_location = "parent_booking__amenity__building__location"

    def __str__(self):
        return f"{self.parent_booking.display_id} - {self.occurrence_date} ({self.exception_type})"
