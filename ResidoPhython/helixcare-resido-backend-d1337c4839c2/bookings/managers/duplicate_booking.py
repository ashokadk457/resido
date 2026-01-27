from bookings.models import AmenityBooking, BookingStatus


class DuplicateBookingManager:
    def __init__(self, original_booking):
        if not isinstance(original_booking, AmenityBooking):
            raise ValueError("original_booking must be an AmenityBooking instance")

        self.original_booking = original_booking

    def _prepare_selected_slots(self):
        selected_slots = []

        if self.original_booking.selected_slot_ids:
            if isinstance(self.original_booking.selected_slot_ids, list):
                selected_slots = self.original_booking.selected_slot_ids
            elif isinstance(self.original_booking.selected_slot_ids, str):
                selected_slots = [self.original_booking.selected_slot_ids]
            else:
                selected_slots = (
                    list(self.original_booking.selected_slot_ids)
                    if self.original_booking.selected_slot_ids
                    else []
                )

        return selected_slots

    def _prepare_repeat_days(self):
        repeat_days = []

        if self.original_booking.repeat_on_days_of_week:
            if isinstance(self.original_booking.repeat_on_days_of_week, list):
                repeat_days = self.original_booking.repeat_on_days_of_week
            elif isinstance(self.original_booking.repeat_on_days_of_week, str):
                repeat_days = [self.original_booking.repeat_on_days_of_week]
            else:
                repeat_days = (
                    list(self.original_booking.repeat_on_days_of_week)
                    if self.original_booking.repeat_on_days_of_week
                    else []
                )

        return repeat_days

    def duplicate(self, new_booking_date=None, new_start_time=None, new_end_time=None):
        selected_slots = self._prepare_selected_slots()
        repeat_days = self._prepare_repeat_days()

        duplicate_booking = AmenityBooking.objects.create(
            amenity=self.original_booking.amenity,
            tenant=self.original_booking.tenant,
            slot=self.original_booking.slot,
            selected_slot_ids=selected_slots,
            booking_date=new_booking_date or self.original_booking.booking_date,
            start_time=new_start_time or self.original_booking.start_time,
            end_time=new_end_time or self.original_booking.end_time,
            booking_notes=self.original_booking.booking_notes,
            is_recurring=self.original_booking.is_recurring,
            repeat_frequency=self.original_booking.repeat_frequency,
            repeat_interval=self.original_booking.repeat_interval,
            repeat_on_days_of_week=repeat_days,
            repeat_on_day_of_month=self.original_booking.repeat_on_day_of_month,
            recurrence_end_type=self.original_booking.recurrence_end_type,
            recurrence_end_date=self.original_booking.recurrence_end_date,
            recurrence_occurrences=self.original_booking.recurrence_occurrences,
            status=BookingStatus.PENDING.value,
        )

        return duplicate_booking
