from datetime import datetime
from dateutil import rrule
from django.db import transaction
from django.utils import timezone

from bookings.models import AmenityBooking, RecurrenceException
from bookings.constants import RecurringFrequency
from common.utils.logging import logger


class RecurringBookingManager:
    # Map RecurringFrequency to rrule frequency
    FREQUENCY_MAP = {
        RecurringFrequency.WEEKLY.value: rrule.WEEKLY,
        RecurringFrequency.BIWEEKLY.value: rrule.WEEKLY,
        RecurringFrequency.MONTHLY.value: rrule.MONTHLY,
        RecurringFrequency.CUSTOM.value: rrule.DAILY,
    }

    # Map day names to rrule weekday constants
    DAY_MAP = {
        "monday": rrule.MO,
        "tuesday": rrule.TU,
        "wednesday": rrule.WE,
        "thursday": rrule.TH,
        "friday": rrule.FR,
        "saturday": rrule.SA,
        "sunday": rrule.SU,
    }

    def __init__(self, parent_booking):
        """
        Initialize the recurring booking manager.

        Args:
            parent_booking: Parent AmenityBooking instance with recurrence settings
        """
        self.parent_booking = parent_booking
        self.amenity = parent_booking.amenity
        self.tenant = parent_booking.tenant

    def _build_rrule(self):
        """
        Build rrule object from parent booking recurrence settings.

        Returns:
            dateutil.rrule.rrule object
        """
        freq = self.FREQUENCY_MAP.get(self.parent_booking.repeat_frequency, rrule.DAILY)

        # Base parameters
        kwargs = {
            "freq": freq,
            "interval": self.parent_booking.repeat_interval or 1,
            "dtstart": datetime.combine(
                self.parent_booking.booking_date, self.parent_booking.start_time
            ),
        }

        # Add end date
        if self.parent_booking.recurrence_end_type == "on_date":
            kwargs["until"] = datetime.combine(
                self.parent_booking.recurrence_end_date, self.parent_booking.start_time
            )
        elif self.parent_booking.recurrence_end_type == "after_occurrences":
            kwargs["count"] = self.parent_booking.recurrence_occurrences

        # Add weekly days if specified
        if (
            self.parent_booking.repeat_frequency == RecurringFrequency.WEEKLY.value
            and self.parent_booking.repeat_on_days_of_week
        ):
            byweekday = [
                self.DAY_MAP[day.lower()]
                for day in self.parent_booking.repeat_on_days_of_week
                if day.lower() in self.DAY_MAP
            ]
            if byweekday:
                kwargs["byweekday"] = byweekday

        # Handle biweekly as weekly with interval=2
        if self.parent_booking.repeat_frequency == RecurringFrequency.BIWEEKLY.value:
            kwargs["interval"] = 2
            if self.parent_booking.repeat_on_days_of_week:
                byweekday = [
                    self.DAY_MAP[day.lower()]
                    for day in self.parent_booking.repeat_on_days_of_week
                    if day.lower() in self.DAY_MAP
                ]
                if byweekday:
                    kwargs["byweekday"] = byweekday

        # Add monthly day if specified
        if (
            self.parent_booking.repeat_frequency == RecurringFrequency.MONTHLY.value
            and self.parent_booking.repeat_on_day_of_month
        ):
            kwargs["bymonthday"] = self.parent_booking.repeat_on_day_of_month

        return rrule.rrule(**kwargs)

    @transaction.atomic
    def generate_instances(self):
        """
        Generate all recurring booking instances based on parent booking settings.

        Returns:
            Dictionary with:
                - 'created': List of created AmenityBooking instances
                - 'skipped': List of skipped dates due to exceptions
                - 'errors': List of error messages
                - 'count': Total instances created
        """
        result = {
            "created": [],
            "skipped": [],
            "errors": [],
            "count": 0,
        }

        try:
            # Build rrule from parent booking
            recurrence_rule = self._build_rrule()

            # Get all exception dates for this parent booking
            exceptions = self.parent_booking.recurrence_exceptions.all()
            exception_map = {exc.occurrence_date: exc for exc in exceptions}

            # Generate instances
            sequence = 1
            for occurrence_dt in recurrence_rule:
                occurrence_date = occurrence_dt.date()

                # Check if this occurrence has an exception
                if occurrence_date in exception_map:
                    exception = exception_map[occurrence_date]

                    if exception.exception_type == "skip":
                        result["skipped"].append(occurrence_date)
                        continue
                    elif exception.exception_type == "cancel":
                        result["skipped"].append(occurrence_date)
                        continue

                try:
                    # Apply exception modifications if any
                    booking_date = occurrence_date
                    start_time = self.parent_booking.start_time
                    end_time = self.parent_booking.end_time
                    selected_slot_ids = self.parent_booking.selected_slot_ids or []

                    if occurrence_date in exception_map:
                        exception = exception_map[occurrence_date]
                        if exception.exception_type == "modify":
                            if exception.new_booking_date:
                                booking_date = exception.new_booking_date
                            if exception.new_start_time:
                                start_time = exception.new_start_time
                            if exception.new_end_time:
                                end_time = exception.new_end_time

                    # Create booking instance
                    instance = AmenityBooking.objects.create(
                        amenity=self.amenity,
                        tenant=self.tenant,
                        booking_date=booking_date,
                        start_time=start_time,
                        end_time=end_time,
                        status=self.parent_booking.status,
                        is_recurring=False,  # Instance is not recurring
                        parent_booking=self.parent_booking,
                        occurrence_date=occurrence_date,
                        recurrence_sequence=sequence,
                        selected_slot_ids=selected_slot_ids,
                        booking_notes=self.parent_booking.booking_notes,
                    )

                    result["created"].append(instance)
                    result["count"] += 1
                    sequence += 1

                except Exception as e:
                    error_msg = (
                        f"Error creating instance for {occurrence_date}: {str(e)}"
                    )
                    result["errors"].append(error_msg)
                    logger.error(error_msg)

        except Exception as e:
            error_msg = f"Error generating recurring instances: {str(e)}"
            result["errors"].append(error_msg)
            logger.error(error_msg)

        logger.info(
            f"Recurring booking generation for {self.parent_booking.display_id}: "
            f"Created {result['count']}, "
            f"Skipped {len(result['skipped'])}, "
            f"Errors {len(result['errors'])}"
        )

        return result

    @transaction.atomic
    def update_instances(self, **kwargs):
        """
        Update all recurring instances with new values.

        Args:
            **kwargs: Fields to update (e.g., status='confirmed')

        Returns:
            Number of instances updated
        """
        updated_count = self.parent_booking.recurring_instances.update(**kwargs)
        logger.info(
            f"Updated {updated_count} instances for parent booking "
            f"{self.parent_booking.display_id}"
        )
        return updated_count

    def get_instances_for_date_range(self, from_date, to_date):
        """
        Get all instances for a date range.

        Args:
            from_date: Start date
            to_date: End date

        Returns:
            QuerySet of AmenityBooking instances
        """
        return self.parent_booking.recurring_instances.filter(
            booking_date__gte=from_date,
            booking_date__lte=to_date,
        ).order_by("booking_date")

    def cancel_all_future_instances(self, from_date, reason=None):
        """
        Cancel all future instances from a given date.

        Args:
            from_date: Start canceling from this date
            reason: Cancellation reason

        Returns:
            Number of instances cancelled
        """
        from bookings.constants import BookingStatus

        instances_to_cancel = self.parent_booking.recurring_instances.filter(
            booking_date__gte=from_date,
        )

        updated_count = instances_to_cancel.update(
            status=BookingStatus.CANCELLED.value,
            cancellation_reason=reason,
            cancelled_on=timezone.now(),
        )

        logger.info(
            f"Cancelled {updated_count} future instances for parent booking "
            f"{self.parent_booking.display_id} from {from_date}"
        )
        return updated_count

    def create_exception(self, occurrence_date, exception_type, **kwargs):
        """
        Create an exception for a specific occurrence.

        Args:
            occurrence_date: Date of the occurrence
            exception_type: 'skip', 'modify', or 'cancel'
            **kwargs: Additional fields (new_start_time, new_end_time, new_booking_date, reason, modified_by)

        Returns:
            Created RecurrenceException instance
        """
        exception = RecurrenceException.objects.create(
            parent_booking=self.parent_booking,
            occurrence_date=occurrence_date,
            exception_type=exception_type,
            **kwargs,
        )

        logger.info(
            f"Created {exception_type} exception for {self.parent_booking.display_id} "
            f"on {occurrence_date}"
        )
        return exception

    def delete_all_instances(self):
        """
        Delete all recurring instances for this parent booking.

        Returns:
            Tuple of (deleted_count, deletion_details)
        """
        deletion_result = self.parent_booking.recurring_instances.delete()
        logger.info(
            f"Deleted {deletion_result[0]} instances for parent booking "
            f"{self.parent_booking.display_id}"
        )
        return deletion_result
