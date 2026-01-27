from django.db.models import Q
from dateutil import rrule

from common.constants import REPEAT_FREQUENCY_MAP, DAY_OF_WEEK_MAP
from common.managers.model.base import BaseModelManager
from meetings.managers.meeting import MeetingManager
from scheduling.managers.title_availability import TitleAvailabilityManager
from scheduling.models import StaffEvent
from scheduling.serializers import EventInstanceSerializer


class EventManager(BaseModelManager):
    model = StaffEvent

    def __init__(
        self,
        staff_id=None,
        event_obj=None,
        from_date=None,
        to_date=None,
        generate_recurrence_list=False,
        generate_event_updates=False,
        event_updates_list=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.staff_id = staff_id
        self.event_obj = event_obj
        self.from_date = from_date
        self.to_date = to_date
        self.repeating = self.event_obj.repeating
        self.original_event_data = self.get_original_event_data()
        self.initial_event_data = None
        self.event_recurrence_list = (
            None if not generate_recurrence_list else self.get_event_recurrence_list()
        )
        self.generate_event_updates = generate_event_updates
        self.event_updates_list = event_updates_list
        self.event_updates_map = (
            None if not generate_event_updates else self.get_applicable_event_updates()
        )

    def get_event_recurrence_list(self):
        if not self.event_obj.repeating:
            return []

        dtstart = self.event_obj.start_date
        until = self.to_date
        if self.event_obj.end_date and self.event_obj.end_date < until:
            until = self.event_obj.end_date
        kwargs = {
            "freq": REPEAT_FREQUENCY_MAP.get(self.event_obj.repeat_frequency),
            "wkst": rrule.MO,
            "dtstart": dtstart,
            "interval": self.event_obj.repeat_interval,
            "until": until,
        }
        # TODO add support for Monthly and Yearly freq
        if kwargs["freq"] == rrule.WEEKLY:
            kwargs["byweekday"] = [
                DAY_OF_WEEK_MAP.get(dow)
                for dow in self.event_obj.repeat_on_days_of_week
            ]

        self.event_recurrence_list = rrule.rrule(**kwargs)
        return self.event_recurrence_list

    def get_applicable_event_updates(self):
        if self.event_updates_list is None:
            self.event_updates_list = self.event_obj.eventinstanceupdate_set.filter(
                (Q(for_date__lte=self.to_date) & Q(all_future=True))
                | (
                    Q(for_date__gte=self.from_date)
                    & Q(for_date__lte=self.to_date)
                    & (Q(all_future__isnull=True) | Q(all_future=False))
                )
            )

        self.event_updates_map = {
            update.for_date.isoformat(): update for update in self.event_updates_list
        }
        return self.event_updates_map

    def get_original_event_data(self):
        serializer = EventInstanceSerializer(self.event_obj)
        return serializer.data

    def get_initial_event_data(self, largest_date_lte_from_date):
        if self.repeating:
            return self._get_initial_event_data_for_repeating_event(
                largest_date_lte_from_date=largest_date_lte_from_date
            )

        return self._get_initial_event_data_for_non_repeating_event()

    def _get_initial_event_data_for_repeating_event(self, largest_date_lte_from_date):
        if largest_date_lte_from_date is None or (
            largest_date_lte_from_date
            and not self.event_updates_map[largest_date_lte_from_date].all_future
        ):
            # This will occur when the event has never been updated before the `from_date`
            # OR, event was updated at least once before the `from_date` but it was not
            # for updated all future.
            # In such a case, the event occurrence on `from_date` will assume its original
            # timings.
            initial_event_data = self.original_event_data.copy()
            initial_event_data["event_update_id"] = None
            initial_event_data["event_update_for_date"] = None
            return initial_event_data

        event_update_largest_date = self.event_updates_map[largest_date_lte_from_date]
        initial_event_data = self.original_event_data.copy()
        initial_event_data["start_time"] = (
            event_update_largest_date.new_start_time.isoformat()
            if event_update_largest_date.new_start_time
            else None
        )
        initial_event_data["end_time"] = (
            event_update_largest_date.new_end_time.isoformat()
            if event_update_largest_date.new_end_time
            else None
        )
        initial_event_data["event_update_id"] = event_update_largest_date.id
        initial_event_data["event_update_for_date"] = (
            event_update_largest_date.for_date.isoformat()
            if event_update_largest_date.for_date
            else None
        )

        return initial_event_data

    def _get_initial_event_data_for_non_repeating_event(self):
        initial_event_data = self.original_event_data.copy()
        initial_event_data["event_update_id"] = None
        initial_event_data["event_update_for_date"] = None

        start_date = initial_event_data["start_date"]
        event_update = self.event_updates_map.get(start_date)
        if event_update:
            initial_event_data["start_time"] = (
                event_update.new_start_time.isoformat()
                if event_update.new_start_time
                else None
            )
            initial_event_data["end_time"] = (
                event_update.new_end_time.isoformat()
                if event_update.new_end_time
                else None
            )
            initial_event_data["event_update_id"] = event_update.id
            initial_event_data["event_update_for_date"] = event_update.for_date

        return initial_event_data

    def get_updated_final_events_data(self, final_event_data, current_date_str):
        event_update_for_curr_date = self.event_updates_map.get(current_date_str)
        if not event_update_for_curr_date:
            # Nothing changes and reset to the last_distinct ones in the next iteration
            return final_event_data, True

        new_start_time, new_end_time = (
            event_update_for_curr_date.new_start_time,
            event_update_for_curr_date.new_end_time,
        )

        final_event_data["start_time"] = (
            new_start_time.isoformat() if new_start_time else None
        )
        final_event_data["end_time"] = (
            new_end_time.isoformat() if new_end_time else None
        )
        final_event_data["event_update_id"] = event_update_for_curr_date.id
        final_event_data[
            "event_update_for_date"
        ] = event_update_for_curr_date.for_date.isoformat()

        # final event for this current date did change, fall back to last_distinct_timings if not all future
        return final_event_data, not event_update_for_curr_date.all_future

    def invite_all(self, notification_channels=None):
        meeting_manager = MeetingManager(
            meeting_id=str(self.event_obj.meeting_id),
            meeting_obj=self.event_obj.meeting,
        )
        kwargs = {"event": self.event_obj.schedule}
        meeting_manager.send_invites(
            notification_channels=notification_channels, **kwargs
        )

    @classmethod
    def _get_base_events_qs(cls, staff_ids, from_date, to_date):
        return (
            cls.model.objects.filter(
                (
                    Q(staff_id__in=staff_ids)
                    | Q(meeting__meetingparticipant__staff_id__in=staff_ids)
                )
                & Q(start_date__lte=to_date)
                & (Q(end_date__isnull=True) | Q(end_date__gte=from_date))
            )
            .exclude(Q(start_date__lt=from_date) & ~Q(repeating=True))
            .select_related("practice_location")
            .select_related("staff")
            .select_related("meeting")
            .prefetch_related("meeting__meetingparticipant_set")
        )

    @classmethod
    def _get_filtered_events_qs(
        cls,
        events_qs,
        event_type,
        practice_location_ids=None,
        visit_type=None,
        category=None,
    ):
        if event_type:
            events_qs = cls.filter_events_qs_by_event_type(
                events_qs=events_qs, event_type=event_type
            )

        if practice_location_ids:
            events_qs = events_qs.filter(practice_location_id__in=practice_location_ids)

        if visit_type:
            events_qs = events_qs.filter(visit_types__contains=[visit_type])

        if category:
            events_qs = events_qs.filter(category=category)

        return list(events_qs.distinct())

    @classmethod
    def get_multi_staff_events_between_dates(
        cls,
        staff_ids,
        from_date,
        to_date,
        event_type,
        practice_location_ids=None,
        visit_type=None,
        category=None,
    ):
        events_qs = cls._get_base_events_qs(
            staff_ids=staff_ids, from_date=from_date, to_date=to_date
        )
        return cls._get_filtered_events_qs(
            events_qs=events_qs,
            event_type=event_type,
            practice_location_ids=practice_location_ids,
            visit_type=visit_type,
            category=category,
        )

    @classmethod
    def filter_events_qs_by_event_type(cls, events_qs, event_type):
        event_title_availability = (
            TitleAvailabilityManager.filter_by_available_for_appointment(
                available_for_appointment=event_type == "available"
            )
        )
        titles = [ea["event_title"] for ea in event_title_availability]

        return events_qs.filter(title__in=titles)

    @classmethod
    def filter_by_event_id_and_visit_type(cls, event_id, visit_type):
        # TODO Test this
        return cls.model.objects.filter(
            id=event_id,
            visit_types__contains=[visit_type],
            title="AVAILABLE",
            active=True,
        ).first()
