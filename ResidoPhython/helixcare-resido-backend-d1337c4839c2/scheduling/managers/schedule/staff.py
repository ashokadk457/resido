from datetime import timedelta, datetime

from django.db.models import Q

from common.utils.datetime import DateTimeUtils
from scheduling.managers.event import EventManager
from scheduling.models import EventInstanceUpdate


class StaffScheduleManager:
    def __init__(
        self,
        staff_id,
        from_date,
        to_date,
        practice_location_id=None,
        visit_type=None,
        **kwargs,
    ):
        self.staff_id = staff_id
        self.staff_ids = kwargs.get("staff_ids")
        self.from_date_str = from_date
        self.to_date_str = to_date
        self.from_date_obj = kwargs.get(
            "from_date_obj", datetime.strptime(from_date, "%Y-%m-%d").date()
        )
        self.to_date_obj = kwargs.get(
            "to_date_obj", datetime.strptime(to_date, "%Y-%m-%d").date()
        )
        self.practice_location_id = practice_location_id
        self.practice_location_ids = kwargs.get("practice_location_ids")
        self.visit_type = visit_type
        self.category = kwargs.get("category")

        # Computation values
        self.schedule = self.get_base_schedule()

        # Computation values for Bulk Mode (Multi Staff)
        self.multi_staff_schedule = self.get_multi_staff_base_schedule()

    def get_base_schedule(self):
        calendar, current_date = {}, self.from_date_obj
        while current_date <= self.to_date_obj:
            calendar[current_date.isoformat()] = []
            current_date += timedelta(days=1)
        return calendar

    def get_multi_staff_base_schedule(self):
        if not self.staff_ids:
            return {}

        multi_staff_calendar = {}
        for staff_id in self.staff_ids:
            staff_calendar = self.get_base_schedule()
            multi_staff_calendar[staff_id] = {"schedule": staff_calendar, "error": None}

        return multi_staff_calendar

    def _get_bulk_event_updates(self, all_event_ids):
        if not all_event_ids:
            return []

        all_event_updates = EventInstanceUpdate.objects.filter(
            (Q(event_id__in=all_event_ids))
            & (
                (Q(for_date__lte=self.from_date_obj) & Q(all_future=True))
                | (
                    Q(for_date__gte=self.from_date_obj)
                    & Q(for_date__lte=self.to_date_obj)
                    & (Q(all_future__isnull=True) | Q(all_future=False))
                )
            )
        )
        return list(all_event_updates)

    def build_events_updates_map(self, events_qs):
        all_event_ids = [str(event.id) for event in events_qs]
        all_event_updates = self._get_bulk_event_updates(all_event_ids=all_event_ids)

        event_updates_map = {}
        for update in all_event_updates:
            event_id = str(update.event_id)
            event_updates_map[event_id] = event_updates_map.get(event_id, []) + [update]

        return event_updates_map

    def _build_staff_schedule(
        self,
        relevant_events,
        all_event_updates_map,
        staff_id=None,
        staff_schedule_dict=None,
        sort=True,
    ):
        if staff_id is None:
            staff_id = self.staff_id
        if staff_schedule_dict is None:
            staff_schedule_dict = self.schedule

        for event in relevant_events:
            event_updates_list = all_event_updates_map.get(str(event.id), [])
            event_manager = EventManager(
                staff_id=staff_id,
                event_obj=event,
                from_date=self.from_date_obj,
                to_date=self.to_date_obj,
                generate_recurrence_list=True,
                generate_event_updates=True,
                event_updates_list=event_updates_list,
            )

            if event_manager.repeating:
                staff_schedule_dict = self.process_repeating_event(
                    event_manager=event_manager, staff_schedule_dict=staff_schedule_dict
                )
            else:
                staff_schedule_dict = self.process_non_repeating_event(
                    event_manager=event_manager, staff_schedule_dict=staff_schedule_dict
                )

        if sort:
            staff_schedule_dict = self.sort_schedule(
                staff_schedule_dict=staff_schedule_dict
            )

        return staff_schedule_dict

    def build_schedule(self, event_type=None, sort=True, visit_type=None):
        practice_location_ids = (
            [self.practice_location_id] if self.practice_location_id else None
        )
        relevant_events = EventManager.get_multi_staff_events_between_dates(
            staff_ids=[self.staff_id],
            from_date=self.from_date_obj,
            to_date=self.to_date_obj,
            event_type=event_type,
            practice_location_ids=practice_location_ids,
            visit_type=visit_type,
            category=self.category,
        )
        all_event_updates_map = self.build_events_updates_map(events_qs=relevant_events)
        self.schedule = self._build_staff_schedule(
            relevant_events=relevant_events,
            all_event_updates_map=all_event_updates_map,
            staff_id=self.staff_id,
            staff_schedule_dict=self.schedule,
            sort=sort,
        )
        return self.schedule

    @classmethod
    def _build_multi_staff_to_events_map(cls, events_qs):
        multi_staff_events_map = {}
        for event in events_qs:
            multi_staff_events_map[str(event.staff_id)] = multi_staff_events_map.get(
                str(event.staff_id), []
            ) + [event]

        return multi_staff_events_map

    def build_multi_staff_schedules(self, event_type=None, sort=True, visit_type=None):
        relevant_multi_staff_events = EventManager.get_multi_staff_events_between_dates(
            staff_ids=self.staff_ids,
            from_date=self.from_date_obj,
            to_date=self.to_date_obj,
            event_type=event_type,
            practice_location_ids=self.practice_location_ids,
            visit_type=visit_type,
        )
        all_event_updates_map = self.build_events_updates_map(
            events_qs=relevant_multi_staff_events
        )
        multi_staff_events_map = self._build_multi_staff_to_events_map(
            events_qs=relevant_multi_staff_events
        )
        for staff_id, relevant_events in multi_staff_events_map.items():
            staff_schedule_dict = self.multi_staff_schedule.get(staff_id, {}).get(
                "schedule", {}
            )
            staff_schedule_dict = self._build_staff_schedule(
                relevant_events=relevant_events,
                all_event_updates_map=all_event_updates_map,
                staff_id=staff_id,
                staff_schedule_dict=staff_schedule_dict,
                sort=sort,
            )
            self.multi_staff_schedule[staff_id] = {
                "schedule": staff_schedule_dict,
                "error": None,
            }

        return self.multi_staff_schedule

    @classmethod
    def process_non_repeating_event(
        cls, event_manager: EventManager, staff_schedule_dict
    ):
        event_manager.initial_event_data = event_manager.get_initial_event_data(
            largest_date_lte_from_date=None,
        )

        start_date_str = event_manager.initial_event_data["start_date"]
        staff_schedule_dict[start_date_str] = staff_schedule_dict.get(
            start_date_str, []
        ) + [event_manager.initial_event_data]

        return staff_schedule_dict

    def process_repeating_event(self, event_manager: EventManager, staff_schedule_dict):
        # 1. Have to find this event's timings on the "from_date"
        # In order to do that, we will consider all the event updates of this event
        # and find which largest update is closest to the "from_date"
        # Suppose "from_date" is 3rd March. Event was once updated on 15th Feb and next on 1st March,
        # We are looking to get 1st march (which is the largest date <= from_date)
        # This is because, the event timings on 3rd March could be same as event timings on 1st March.
        largest_date_lte_from_date = (
            DateTimeUtils.get_largest_date_less_than_or_equal_to(
                dates_map=event_manager.event_updates_map,
                from_date_obj=self.from_date_obj,
            )
        )

        # Get the initial event data as it would be on the start of the requested schedule.
        # That is, on `from_date`
        event_manager.initial_event_data = event_manager.get_initial_event_data(
            largest_date_lte_from_date=largest_date_lte_from_date,
        )

        # last_distinct_event_data represents a copy of the event data as it would be
        # on the start of the schedule day. That is on `from_date`
        reset_event_timings, last_distinct_event_data = (
            True,
            event_manager.initial_event_data.copy(),
        )

        # final_event_data is the varying final event data on each day of its occurrence.
        # This will be copied into the schedule map.
        final_event_data = last_distinct_event_data
        current_date = self.from_date_obj

        # Iterate over all dates starting from `from_date` all the way upto `to_date`.
        # And generate the event timings on each day this particular event occurs as per
        # it's recurrence rules and its updates.
        while current_date <= self.to_date_obj:
            # fall back to last_distinct_event_data if reset is required
            # Let's say last_distinct_event_data is x at the start of the schedule
            # let's say we found an update 2 days later (update applicable for a single day): event data is y
            # Then, on the 2nd day, event timings should be the updated one (that is y) and then from 3rd day
            # onwards, it should fall back to x (timings at the start of the schedule)
            final_event_data = (
                last_distinct_event_data if reset_event_timings else final_event_data
            )
            current_date_str = current_date.isoformat()
            current_date_time = datetime.combine(current_date, datetime.min.time())
            if current_date_time in event_manager.event_recurrence_list:
                last_distinct_event_data = final_event_data.copy()
                (
                    final_event_data,
                    reset_event_timings,
                ) = event_manager.get_updated_final_events_data(
                    final_event_data=final_event_data,
                    current_date_str=current_date_str,
                )

                if final_event_data["start_time"] and final_event_data["end_time"]:
                    # Append only if it is a valid event occurrence.
                    # That is, if it is not cancelled.
                    staff_schedule_dict[current_date_str] = staff_schedule_dict.get(
                        current_date_str, []
                    ) + [final_event_data.copy()]

            current_date += timedelta(days=1)

        return staff_schedule_dict

    @classmethod
    def sort_schedule(cls, staff_schedule_dict):
        for key, value in staff_schedule_dict.items():
            staff_schedule_dict[key] = sorted(
                value, key=lambda event: event["start_time"]
            )

        return staff_schedule_dict
