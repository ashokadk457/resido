from datetime import timedelta, datetime


from common.constants import UTC_TIMEZONE, DAY_OF_WEEK_MAP_REVERSE
from common.managers.model.base import BaseModelManager
from common.utils.datetime import DateTimeUtils
from common.utils.logging import logger
from scheduling.dto.slot import SlotDTO
from scheduling.managers.event import EventManager
from scheduling.managers.schedule.location import LocationScheduleManager
from scheduling.managers.schedule.staff import StaffScheduleManager
from scheduling.managers.vt_config import VisitTypeConfigManager
from scheduling.models import Slot


class SlotsManager(BaseModelManager):
    model = Slot

    def __init__(
        self,
        staff_id,
        visit_type,
        from_date,
        to_date,
        practice_location_id=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.staff_id = staff_id
        self.staff_ids = kwargs.get("staff_ids")  # Bulk Approach
        self.visit_type = visit_type
        self.from_date_str = from_date
        self.to_date_str = to_date
        # self.from_date_obj = datetime.strptime(from_date, "%Y-%m-%d").date()
        # self.to_date_obj = datetime.strptime(to_date, "%Y-%m-%d").date()
        self.from_date_obj = DateTimeUtils.custom_date_parser(from_date)
        self.to_date_obj = DateTimeUtils.custom_date_parser(to_date)
        self.get_all_vt_configs = kwargs.get("get_all_vt_configs", False)
        self.practice_location_id = practice_location_id
        self.practice_location_ids = kwargs.get("practice_location_ids")

        # Related objects
        self.schedule_manager = StaffScheduleManager(
            staff_id=staff_id,
            staff_ids=self.staff_ids,
            from_date=from_date,
            to_date=to_date,
            from_date_obj=self.from_date_obj,
            to_date_obj=self.to_date_obj,
            practice_location_id=self.practice_location_id,
            practice_location_ids=self.practice_location_ids,
        )
        self.unavailable_schedule_manager = StaffScheduleManager(
            staff_id=staff_id,
            staff_ids=self.staff_ids,
            from_date=from_date,
            to_date=to_date,
            from_date_obj=self.from_date_obj,
            to_date_obj=self.to_date_obj,
            practice_location_id=self.practice_location_id,
            practice_location_ids=self.practice_location_ids,
        )
        self.vt_config_manager = VisitTypeConfigManager(
            staff_id=staff_id,
            staff_ids=self.staff_ids,
            visit_type=visit_type,
            get_all_vt_configs=self.get_all_vt_configs,
        )

        # Computation values
        self.slot_map = self.get_base_slots()
        self.str_dates_list = list(map(str, self.slot_map.keys()))
        self.schedule = None
        self.unavailable_schedule = None
        self.slot_bookings_map = {}

        # Computation values for Bulk Mode (Multi Staff)
        self.multi_staff_slot_map = self.get_multi_staff_base_slot_map()
        self.multi_staff_schedule = None
        self.multi_staff_unavailable_schedule = None
        self.multi_staff_slot_bookings_map = {}
        self.multi_staff_location_schedule_managers_map = {}

    def get_base_slots(self):
        base_slots, current_date = {}, self.from_date_obj
        while current_date <= self.to_date_obj:
            base_slots[current_date.isoformat()] = []
            current_date += timedelta(days=1)
        return base_slots

    def get_multi_staff_base_slot_map(self):
        if not self.staff_ids:
            return {}
        multi_staff_slot_map = {}
        for staff_id in self.staff_ids:
            staff_slots_map = self.get_base_slots()
            multi_staff_slot_map[staff_id] = {
                "slot_map": staff_slots_map,
                "error": None,
            }
        return multi_staff_slot_map

    def generate_slot_candidates(self, staff_id, current_date_str, blocks):
        all_slot_candidate_dtos = []
        for block in blocks:
            # block_start_time_obj = datetime.strptime(
            #     f"{current_date_str} {block['start_time']}", "%Y-%m-%d %H:%M:%S"
            # )
            # block_end_time_obj = datetime.strptime(
            #     f"{current_date_str} {block['end_time']}", "%Y-%m-%d %H:%M:%S"
            # )
            block_start_time_obj = DateTimeUtils.custom_datetime_parser(
                f"{current_date_str} {block['start_time']}"
            )
            block_end_time_obj = DateTimeUtils.custom_datetime_parser(
                f"{current_date_str} {block['end_time']}"
            )

            if not self.get_all_vt_configs:
                _duration = self.vt_config_manager.get_staff_vt_config_duration(
                    staff_id=staff_id
                )
                slot_candidate_dtos = DateTimeUtils.generate_slots(
                    event_block=block,
                    block_start_time=block_start_time_obj,
                    block_end_time=block_end_time_obj,
                    slot_duration=_duration,
                    visit_type=self.vt_config_manager.visit_type,
                    visit_type_duration=_duration,
                )
                if slot_candidate_dtos:
                    all_slot_candidate_dtos += slot_candidate_dtos
            else:
                staff_all_vt_configs = self.vt_config_manager.get_staff_all_vt_configs(
                    staff_id=staff_id
                )
                for vt_config in staff_all_vt_configs:
                    slot_candidate_dtos = None
                    if vt_config.visit_type in block["visit_types"]:
                        slot_candidate_dtos = DateTimeUtils.generate_slots(
                            event_block=block,
                            block_start_time=block_start_time_obj,
                            block_end_time=block_end_time_obj,
                            slot_duration=vt_config.duration,
                            visit_type=vt_config.visit_type,
                            visit_type_duration=vt_config.duration,
                        )
                    if slot_candidate_dtos:
                        all_slot_candidate_dtos += slot_candidate_dtos

        return all_slot_candidate_dtos

    @classmethod
    def _get_booked_slots(cls, event_ids, slot_dates):
        return (
            Slot.objects.filter(
                slot_start_ts__date__in=slot_dates, event_id__in=event_ids
            )
            .select_related("event")
            .select_related("event__staff")
        )

    @classmethod
    def get_booked_slots_map(cls, event_ids, slot_dates):
        booked_slots_list = list(
            cls._get_booked_slots(event_ids=event_ids, slot_dates=slot_dates)
        )
        slot_bookings_map = {}
        for booking in booked_slots_list:
            booking_date = booking.slot_start_ts.date().isoformat()
            slot_bookings_map[booking_date] = slot_bookings_map.get(
                booking_date, []
            ) + [booking]
        return slot_bookings_map

    @classmethod
    def get_multi_staff_booked_slots_map(cls, event_ids, slot_dates):
        all_booked_slots_list = list(
            cls._get_booked_slots(event_ids=event_ids, slot_dates=slot_dates)
        )

        multi_staff_booked_slots_map = {}

        for booking in all_booked_slots_list:
            staff_id = str(booking.event.staff_id)
            slot_bookings_map = multi_staff_booked_slots_map.get(staff_id, {})
            booking_date = booking.slot_start_ts.date().isoformat()
            slot_bookings_map[booking_date] = slot_bookings_map.get(
                booking_date, []
            ) + [booking]
            multi_staff_booked_slots_map[staff_id] = slot_bookings_map

        return multi_staff_booked_slots_map

    @classmethod
    def _get_event_ids_and_location_ids(cls, schedule_dict):
        slot_dates = list(schedule_dict.keys())
        event_ids, location_ids = set(), set()
        for current_date_str in slot_dates:
            available_blocks = schedule_dict[current_date_str]
            for block in available_blocks:
                event_ids.add(block["id"])
                location_ids.add(block["practice_location_id"])

        return list(event_ids), list(location_ids)

    def get_multi_staff_event_ids_and_location_ids(self, multi_staff_schedule):
        event_ids, location_ids = set(), set()
        for staff_id, schedule_error_report_dict in multi_staff_schedule.items():
            schedule_dict = schedule_error_report_dict.get("schedule", {})
            staff_event_ids, staff_location_ids = self._get_event_ids_and_location_ids(
                schedule_dict=schedule_dict
            )
            event_ids.update(staff_event_ids)
            location_ids.update(staff_location_ids)

        return list(event_ids), list(location_ids)

    def _generate_final_slots_map(
        self,
        staff_id,
        schedule_dict,
        unavailable_schedule_dict,
        slot_bookings_map,
        multi_location_schedule_manager,
    ):
        slot_map = {}
        for current_date_str in schedule_dict:
            # Generate slot for each date by filtering out the candidate slots
            available_blocks = schedule_dict[current_date_str]

            slot_candidate_dtos = self.generate_slot_candidates(
                staff_id=staff_id,
                current_date_str=current_date_str,
                blocks=available_blocks,
            )

            final_available_slot_dicts = self.get_filtered_slots(
                staff_id=staff_id,
                current_date_str=current_date_str,
                slot_candidates=slot_candidate_dtos,
                slot_bookings_map=slot_bookings_map,
                unavailable_schedule=unavailable_schedule_dict,
                multi_location_schedule_manager=multi_location_schedule_manager,
            )
            slot_map[current_date_str] = final_available_slot_dicts

        return slot_map, None

    def get_slots(self):
        if not self.vt_config_manager.vt_config and not self.get_all_vt_configs:
            return self.slot_map, "visit_type_not_configured"

        # Generate Schedule
        self.schedule = self.schedule_manager.build_schedule(
            event_type="available", visit_type=self.visit_type
        )
        self.unavailable_schedule = self.unavailable_schedule_manager.build_schedule(
            event_type="unavailable"
        )

        # Find event_ids and location_ids to prefetch booked slots
        # and location schedule managers - Both for ultimately filtering out
        # dates and slots
        event_ids, location_ids = self._get_event_ids_and_location_ids(
            schedule_dict=self.schedule
        )
        self.slot_bookings_map = self.get_booked_slots_map(
            slot_dates=list(self.schedule.keys()), event_ids=event_ids
        )
        multi_location_schedules_manager = LocationScheduleManager(
            practice_location_id=None, practice_location_ids=location_ids
        )

        staff_id = self.staff_id
        self.slot_map, error = self._generate_final_slots_map(
            staff_id=staff_id,
            schedule_dict=self.schedule,
            unavailable_schedule_dict=self.unavailable_schedule,
            slot_bookings_map=self.slot_bookings_map,
            multi_location_schedule_manager=multi_location_schedules_manager,
        )

        return self.slot_map, error

    def _generate_multi_staff_slots_map(
        self,
        multi_staff_schedule_dict,
        multi_staff_unavailable_schedule_dict,
        multi_staff_slot_bookings_map,
        multi_location_schedule_manager,
    ):
        multi_staff_slot_map = {}
        for staff_id, schedule_error_report_dict in multi_staff_schedule_dict.items():
            staff_schedule_dict = schedule_error_report_dict.get("schedule", {})
            staff_unavailable_schedule_dict = multi_staff_unavailable_schedule_dict.get(
                staff_id, {}
            ).get("schedule", {})
            staff_slot_bookings_map = multi_staff_slot_bookings_map.get("staff_id", {})
            staff_slot_map, error = self._generate_final_slots_map(
                schedule_dict=staff_schedule_dict,
                unavailable_schedule_dict=staff_unavailable_schedule_dict,
                slot_bookings_map=staff_slot_bookings_map,
                multi_location_schedule_manager=multi_location_schedule_manager,
                staff_id=staff_id,
            )
            multi_staff_slot_map[staff_id] = {
                "slot_map": staff_slot_map,
                "error": error,
            }

        return multi_staff_slot_map

    def get_multi_staff_slots(self):
        if not self.staff_ids:
            return self.multi_staff_slot_map

        self.multi_staff_schedule = self.schedule_manager.build_multi_staff_schedules(
            event_type="available", visit_type=self.visit_type
        )
        self.multi_staff_unavailable_schedule = (
            self.unavailable_schedule_manager.build_multi_staff_schedules(
                event_type="unavailable"
            )
        )
        (
            multi_staff_event_ids,
            multi_staff_location_ids,
        ) = self.get_multi_staff_event_ids_and_location_ids(
            multi_staff_schedule=self.multi_staff_schedule
        )
        self.multi_staff_slot_bookings_map = self.get_multi_staff_booked_slots_map(
            event_ids=multi_staff_event_ids, slot_dates=self.str_dates_list
        )
        multi_location_schedules_manager = LocationScheduleManager(
            practice_location_id=None, practice_location_ids=multi_staff_location_ids
        )

        self.multi_staff_slot_map = self._generate_multi_staff_slots_map(
            multi_staff_schedule_dict=self.multi_staff_schedule,
            multi_staff_unavailable_schedule_dict=self.multi_staff_unavailable_schedule,
            multi_staff_slot_bookings_map=self.multi_staff_slot_bookings_map,
            multi_location_schedule_manager=multi_location_schedules_manager,
        )

        return self.multi_staff_slot_map

    @staticmethod
    def get_min_count(arr):
        min_val = min(val for val in arr if val) if arr else 0
        max_val = max(arr) if arr else 0

        if min_val == max_val:
            return f"{min_val}"

        return f"{min_val}+"

    def _get_min_slot_counts_map(self, slot_map):
        final_slot_counts_map = {}
        for curr_date, all_slots in slot_map.items():
            vt_counts_map = {}
            for slot in all_slots:
                visit_type = slot.get("visit_type")
                vt_counts_map[visit_type] = vt_counts_map.get(visit_type, 0) + 1

            final_slot_counts_map[curr_date] = self.get_min_count(
                arr=vt_counts_map.values()
            )

        return final_slot_counts_map, ""

    def get_min_slot_counts_map(self):
        self.slot_map, error_code = self.get_slots()
        if error_code:
            return self.slot_map, error_code

        return self._get_min_slot_counts_map(slot_map=self.slot_map)

    def get_multi_staff_min_slot_counts_map(self):
        self.multi_staff_slot_map = self.get_multi_staff_slots()

        multi_staff_min_slot_counts_map = {}
        for staff_id, slot_map_with_error_report in self.multi_staff_slot_map.items():
            slot_map, error = slot_map_with_error_report.get(
                "slot_map", {}
            ), slot_map_with_error_report.get("error")
            if error:
                multi_staff_min_slot_counts_map[staff_id] = {}
                logger.info(
                    f"Error occurred while getting slots for staff {staff_id}: {error}"
                )
                continue

            min_slot_counts_map = self._get_min_slot_counts_map(slot_map=slot_map)
            multi_staff_min_slot_counts_map[staff_id] = min_slot_counts_map

        return multi_staff_min_slot_counts_map

    def check_slot_overlapping_and_overbooking(self, staff_id, slot, bookings):
        overlapping, exact_overlapping, overlapping_booking = False, False, None
        slot_id = slot.id
        for booking in bookings:
            slot_candidate_start_ts = slot.slot_start_time.astimezone(tz=UTC_TIMEZONE)
            slot_candidate_end_ts = slot.slot_end_time.astimezone(tz=UTC_TIMEZONE)
            if not (
                slot_candidate_start_ts >= booking.slot_end_ts
                or slot_candidate_end_ts <= booking.slot_start_ts
            ):
                overlapping = True
                overlapping_booking = booking
                if (
                    slot_candidate_start_ts == booking.slot_start_ts
                    and slot_candidate_end_ts == booking.slot_end_ts
                ):
                    # set slot id for the client to refer back to this slot
                    slot_id = booking.id
                    exact_overlapping = True
                break

        if (not overlapping) or (
            exact_overlapping
            and self.is_overbooking_allowed(
                staff_id=staff_id, booked_slot=overlapping_booking
            )
        ):
            return True, slot_id
        return False, slot_id

    @staticmethod
    def get_all_locations_from_slot_candidates(slot_candidates: list[SlotDTO]):
        return [slot.practice_location_id for slot in slot_candidates]

    @staticmethod
    def get_location_schedule_managers_map(all_location_ids):
        location_schedule_manager_map = {}
        for location_id in all_location_ids:
            if location_id not in location_schedule_manager_map:
                location_schedule_manager_map[location_id] = LocationScheduleManager(
                    practice_location_id=location_id
                )

        return location_schedule_manager_map

    @staticmethod
    def check_slot_falling_in_location_walkin(
        slot: SlotDTO, multi_location_schedule_manager: LocationScheduleManager
    ) -> bool:
        if not multi_location_schedule_manager:
            return True

        practice_location_id = str(slot.practice_location_id)
        walkin_schedule = multi_location_schedule_manager.walkin_schedules_maps.get(
            practice_location_id, {}
        )
        slot_start_time_dow = DAY_OF_WEEK_MAP_REVERSE.get(
            slot.slot_start_time.weekday()
        )
        if walkin_schedule.get(slot_start_time_dow) is None:
            return True

        walkin_schedule_on_weekday = walkin_schedule.get(slot_start_time_dow)
        combined_walkin_start_time = datetime.combine(
            slot.slot_start_time.date(), walkin_schedule_on_weekday["start_time"]
        )
        combined_walkin_end_time = datetime.combine(
            slot.slot_end_time.date(), walkin_schedule_on_weekday["end_time"]
        )

        return (
            slot.slot_end_time <= combined_walkin_start_time
            or slot.slot_start_time >= combined_walkin_end_time
        )

    @staticmethod
    def check_slot_falling_on_a_holiday(
        slot: SlotDTO, multi_location_schedule_manager: LocationScheduleManager
    ) -> bool:
        if not multi_location_schedule_manager:
            return True

        practice_location_id = str(slot.practice_location_id)
        holiday_schedule = multi_location_schedule_manager.holiday_schedules_maps.get(
            practice_location_id, []
        )
        if not holiday_schedule:
            return True

        slot_date = slot.slot_start_time.date()
        slot_month, slot_day_of_month = slot_date.month, slot_date.day

        for holiday in holiday_schedule:
            if (
                holiday["month"] == slot_month
                and holiday["day_of_month"] == slot_day_of_month
            ):
                return False

        return True

    @classmethod
    def check_slot_falling_in_an_unavailable_event(
        cls, slot: SlotDTO, current_date_str: str, unavailable_schedule
    ) -> bool:
        if not unavailable_schedule:
            return True

        unavailable_events_for_date = unavailable_schedule.get(current_date_str, [])
        for unavailable_event in unavailable_events_for_date:
            # date_obj = datetime.strptime(
            #     unavailable_event.get("start_date"), "%Y-%m-%d"
            # ).date()
            date_obj = DateTimeUtils.custom_date_parser(
                unavailable_event.get("start_date")
            )
            combined_event_start_time = datetime.combine(
                date_obj,
                DateTimeUtils.custom_time_parser(unavailable_event.get("start_time")),
                # datetime.strptime(
                #     unavailable_event.get("start_time"), "%H:%M:%S"
                # ).time(),
            )
            combined_event_end_time = datetime.combine(
                date_obj,
                DateTimeUtils.custom_time_parser(unavailable_event.get("end_time")),
                # datetime.strptime(unavailable_event.get("end_time"), "%H:%M:%S").time(),
            )

            if not (
                slot.slot_start_time >= combined_event_end_time
                or slot.slot_end_time <= combined_event_start_time
            ):
                return False

        return True

    def get_filtered_slots(
        self,
        staff_id,
        current_date_str,
        slot_candidates,
        slot_bookings_map,
        unavailable_schedule,
        multi_location_schedule_manager,
    ):
        filtered_slot_dicts = []

        bookings = slot_bookings_map.get(current_date_str, [])
        for slot in slot_candidates:
            (
                overlap_and_overbooking_check,
                slot_id,
            ) = self.check_slot_overlapping_and_overbooking(
                staff_id=staff_id, slot=slot, bookings=bookings
            )
            if not overlap_and_overbooking_check:
                continue

            slot.id = slot_id  # Set slot id (helps in booking the slot)

            unavailable_check = self.check_slot_falling_in_an_unavailable_event(
                slot=slot,
                current_date_str=current_date_str,
                unavailable_schedule=unavailable_schedule,
            )
            if not unavailable_check:
                continue

            walkin_check = self.check_slot_falling_in_location_walkin(
                slot=slot,
                multi_location_schedule_manager=multi_location_schedule_manager,
            )
            if not walkin_check:
                continue

            holiday_check = self.check_slot_falling_on_a_holiday(
                slot=slot,
                multi_location_schedule_manager=multi_location_schedule_manager,
            )
            if not holiday_check:
                continue

            filtered_slot_dicts.append(slot.data())

        return filtered_slot_dicts

    def is_overbooking_allowed(self, staff_id, booked_slot):
        if (
            booked_slot.visit_type != self.visit_type
            and booked_slot.total_bookings == 0
        ):
            return True

        staff_vt_config = self.vt_config_manager.get_staff_vt_config(staff_id=staff_id)
        if booked_slot.visit_type != self.visit_type or not staff_vt_config:
            return False

        return booked_slot.total_bookings < staff_vt_config.max_bookings

    @classmethod
    def increment_slot_bookings(cls, slot_obj, visit_type=None):
        if not slot_obj:
            return

        if slot_obj.total_bookings == 0:
            slot_obj.visit_type = visit_type
        slot_obj.total_bookings += 1
        slot_obj.save()
        return slot_obj

    @classmethod
    def decrement_slot_bookings(cls, slot_obj):
        if not slot_obj:
            return

        if slot_obj.total_bookings > 0:
            new_bookings = slot_obj.total_bookings - 1
            slot_obj.total_bookings = new_bookings
            if new_bookings == 0:
                # detach the visit type if total bookings are getting reduced to 0
                slot_obj.visit_type = None
            slot_obj.save()
        return slot_obj

    @classmethod
    def check_if_booking_allowed_in_slot(cls, slot_obj, incoming_visit_type):
        vt_config_manager = VisitTypeConfigManager(
            staff_id=str(slot_obj.event.staff_id), visit_type=slot_obj.visit_type
        )
        if not vt_config_manager.vt_config:
            return False

        if slot_obj.total_bookings == 0:
            # If no bookings currently made, new bookings are allowed.
            # no need to check for visit type mismatch as visit type
            # would be null anyway
            return True

        # Incase total bookings are not 0, check against max bookings and visit type
        return (
            1 + slot_obj.total_bookings <= vt_config_manager.vt_config.max_bookings
        ) and (slot_obj.visit_type == incoming_visit_type)

    @classmethod
    def _create_slot(cls, slot_data):
        try:
            slot_obj = cls.model.objects.create(**slot_data)
        except Exception as e:
            logger.info(f"Exception occurred while creating a slot: {str(e)}")
            return None, "error_occurred_while_creating_slot"

        return slot_obj, None

    @classmethod
    def validate_event_and_visit_type(cls, event_id, visit_type):
        if not event_id and not visit_type:
            return False, None, "event_id_and_visit_type_missing"

        event = EventManager.filter_by_event_id_and_visit_type(
            event_id=event_id, visit_type=visit_type
        )
        if not event:
            return False, None, "invalid_event_id_or_visit_type"

        return True, event, None

    @classmethod
    def get_or_create_slot_for_booking(cls, slot_data):
        slot_obj, error_code = None, "error_occurred_while_creating_slot"

        valid_event, event_obj, error_code = cls.validate_event_and_visit_type(
            event_id=slot_data.get("event_id"), visit_type=slot_data.get("visit_type")
        )
        if not valid_event:
            return slot_obj, error_code

        if not slot_data.get("id"):
            slot_data.pop("id", None)
            slot_obj, error_code = cls._create_slot(slot_data)
        else:
            # try to get a slot
            slot_obj = cls.model.objects.filter(id=slot_data.get("id")).first()
            if not slot_obj:
                return slot_obj, "invalid_slot_id"

            booking_allowed = cls.check_if_booking_allowed_in_slot(
                slot_obj=slot_obj, incoming_visit_type=slot_data.get("visit_type")
            )
            error_code = "slot_already_booked" if not booking_allowed else ""
        return slot_obj, error_code
