"""
Manager for AmenitySlot bulk generation.
Generates slots for a date range with specified time intervals.
Respects blackout periods to mark unavailable slots.
"""

from datetime import datetime, timedelta
from django.db import transaction

from bookings.models import AmenitySlot, AmenityBlackoutPeriod
from common.utils.logging import logger


class AmenitySlotManager:
    """
    Manager for generating amenity slots in bulk based on date range and time intervals.

    Usage:
        manager = AmenitySlotManager(
            amenity=amenity_obj,
            from_date="2024-11-01",
            to_date="2024-11-30",
            operating_start_time="09:00:00",
            operating_end_time="17:00:00",
            interval_minutes=60,  # 1-hour slots
            max_concurrent_bookings=1
        )
        slots = manager.generate_slots()
    """

    def __init__(
        self,
        amenity,
        from_date,
        to_date,
        operating_start_time,
        operating_end_time,
        interval_minutes=60,
        max_concurrent_bookings=1,
    ):
        """
        Initialize the slot manager.

        Args:
            amenity: Amenity instance
            from_date: Start date (string "YYYY-MM-DD" or date object)
            to_date: End date (string "YYYY-MM-DD" or date object)
            operating_start_time: Daily operating start time (string "HH:MM:SS")
            operating_end_time: Daily operating end time (string "HH:MM:SS")
            interval_minutes: Slot duration in minutes (default: 60)
            max_concurrent_bookings: Max bookings per slot (default: 1)
        """
        self.amenity = amenity
        self.interval_minutes = interval_minutes
        self.max_concurrent_bookings = max_concurrent_bookings

        # Parse dates
        self.from_date = self._parse_date(from_date)
        self.to_date = self._parse_date(to_date)

        # Parse times (provided by admin)
        self.start_time = self._parse_time(operating_start_time)
        self.end_time = self._parse_time(operating_end_time)

        # Cache for blackout periods
        self.blackout_periods = self._load_blackout_periods()

    @staticmethod
    def _parse_date(date_input):
        """Convert date string or object to date object."""
        if isinstance(date_input, str):
            return datetime.strptime(date_input, "%Y-%m-%d").date()
        return date_input

    @staticmethod
    def _parse_time(time_input):
        """Convert time string or object to time object."""
        if isinstance(time_input, str):
            return datetime.strptime(time_input, "%H:%M:%S").time()
        return time_input

    def _load_blackout_periods(self):
        """Load all active blackout periods for the amenity."""
        return list(
            AmenityBlackoutPeriod.objects.filter(
                amenity=self.amenity,
                active=True,
                start_date__lte=self.to_date,
                end_date__gte=self.from_date,
            )
        )

    def _is_in_blackout_period(self, slot_date, slot_start_time, slot_end_time):
        """
        Check if a slot falls within any blackout period.

        Args:
            slot_date: Date of the slot
            slot_start_time: Start time of the slot
            slot_end_time: End time of the slot

        Returns:
            Boolean indicating if slot is blocked
        """
        for blackout in self.blackout_periods:
            # Check date range
            if not (blackout.start_date <= slot_date <= blackout.end_date):
                continue

            # Full day blackout (no time specified)
            if not blackout.start_time or not blackout.end_time:
                return True

            # Time-specific blackout
            if (
                blackout.start_time <= slot_start_time
                and slot_end_time <= blackout.end_time
            ):
                return True

            # Partial overlap
            if (blackout.start_time < slot_end_time) and (
                slot_start_time < blackout.end_time
            ):
                return True

        return False

    def _generate_slot_times_for_day(self, slot_date):
        """
        Generate all slot start/end times for a given day based on interval.

        Args:
            slot_date: Date object

        Returns:
            List of (start_time, end_time) tuples
        """
        slots = []
        current = datetime.combine(slot_date, self.start_time)
        end_of_day = datetime.combine(slot_date, self.end_time)

        while current < end_of_day:
            slot_start = current.time()
            slot_end = (current + timedelta(minutes=self.interval_minutes)).time()

            # Don't create slot if it extends beyond operating hours
            if (current + timedelta(minutes=self.interval_minutes)) <= end_of_day:
                slots.append((slot_start, slot_end))

            current += timedelta(minutes=self.interval_minutes)

        return slots

    @transaction.atomic
    def generate_slots(self, delete_existing=False):
        """
        Generate all slots for the date range with specified intervals.
        Respects blackout periods - slots within blackout are marked unavailable.

        Args:
            delete_existing: If True, delete existing slots for this date range first

        Returns:
            Dictionary with:
                - 'created': List of created AmenitySlot instances
                - 'updated': List of existing slots marked unavailable due to blackout
                - 'errors': List of error messages
        """
        result = {
            "created": [],
            "updated": [],
            "errors": [],
        }

        # Delete existing slots if requested
        if delete_existing:
            deleted_count, _ = AmenitySlot.objects.filter(
                amenity=self.amenity,
                slot_date__gte=self.from_date,
                slot_date__lte=self.to_date,
            ).delete()
            logger.info(
                f"Deleted {deleted_count} existing slots for {self.amenity.name} "
                f"({self.from_date} to {self.to_date})"
            )

        current_date = self.from_date
        while current_date <= self.to_date:
            try:
                slot_times = self._generate_slot_times_for_day(current_date)

                for slot_start_time, slot_end_time in slot_times:
                    try:
                        # Check if slot is in blackout period
                        is_blocked = self._is_in_blackout_period(
                            current_date, slot_start_time, slot_end_time
                        )

                        # Create or get slot
                        slot, created = AmenitySlot.objects.get_or_create(
                            amenity=self.amenity,
                            slot_date=current_date,
                            slot_start_time=slot_start_time,
                            defaults={
                                "slot_end_time": slot_end_time,
                                "slot_duration_minutes": self.interval_minutes,
                                "is_available": not is_blocked,
                                "max_concurrent_bookings": self.max_concurrent_bookings,
                                "active": True,
                            },
                        )

                        if created:
                            result["created"].append(slot)
                        elif is_blocked and slot.is_available:
                            # Mark as unavailable due to blackout
                            slot.is_available = False
                            slot.save()
                            result["updated"].append(slot)

                    except Exception as e:
                        error_msg = (
                            f"Error creating slot for {current_date} "
                            f"{slot_start_time}-{slot_end_time}: {str(e)}"
                        )
                        result["errors"].append(error_msg)
                        logger.error(error_msg)

            except Exception as e:
                error_msg = f"Error processing date {current_date}: {str(e)}"
                result["errors"].append(error_msg)
                logger.error(error_msg)

            current_date += timedelta(days=1)

        logger.info(
            f"Slot generation for {self.amenity.name}: "
            f"Created {len(result['created'])}, "
            f"Updated {len(result['updated'])}, "
            f"Errors {len(result['errors'])}"
        )

        return result

    def get_available_slots(self, slot_date=None, filters=None):
        """
        Get available slots for a specific date or date range.

        Args:
            slot_date: Specific date (optional)
            filters: Additional filter criteria (dict)

        Returns:
            QuerySet of available AmenitySlot instances
        """
        query = AmenitySlot.objects.filter(
            amenity=self.amenity,
            is_available=True,
            active=True,
        )

        if slot_date:
            query = query.filter(slot_date=slot_date)
        else:
            query = query.filter(
                slot_date__gte=self.from_date,
                slot_date__lte=self.to_date,
            )

        if filters:
            # Filter by start time
            if "start_time" in filters:
                query = query.filter(slot_start_time__gte=filters["start_time"])
            # Filter by end time
            if "end_time" in filters:
                query = query.filter(slot_end_time__lte=filters["end_time"])
            # Filter by not fully booked
            if filters.get("exclude_fully_booked", False):
                query = query.exclude(total_bookings__gte=self.max_concurrent_bookings)

        return query.order_by("slot_date", "slot_start_time")

    def check_slot_overlapping(
        self, booking_start_time, booking_end_time, booking_date
    ):
        """
        Check if a booking overlaps with existing bookings in a slot.

        Args:
            booking_start_time: Start time of booking
            booking_end_time: End time of booking
            booking_date: Date of booking

        Returns:
            List of overlapping AmenitySlot instances
        """
        overlapping_slots = AmenitySlot.objects.filter(
            amenity=self.amenity,
            slot_date=booking_date,
            slot_start_time__lt=booking_end_time,
            slot_end_time__gt=booking_start_time,
        )
        return list(overlapping_slots)

    def increment_slot_booking(self, slot, decrement=False):
        """
        Increment or decrement booking count for a slot.
        Updates is_available flag based on capacity.

        Args:
            slot: AmenitySlot instance
            decrement: If True, decrement instead of increment
        """
        if decrement:
            slot.total_bookings = max(0, slot.total_bookings - 1)
        else:
            slot.total_bookings += 1

        # Update availability based on max_concurrent_bookings
        slot.is_available = slot.total_bookings < slot.max_concurrent_bookings
        slot.save()

        return slot

    @staticmethod
    def update_slot_availability(slot):
        """
        Update slot availability based on current booking count.

        Args:
            slot: AmenitySlot instance

        Returns:
            Updated AmenitySlot instance
        """
        slot.is_available = slot.total_bookings < slot.max_concurrent_bookings
        slot.save()
        return slot
