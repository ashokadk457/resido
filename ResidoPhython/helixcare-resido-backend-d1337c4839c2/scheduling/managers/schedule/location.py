from common.constants import ScheduleCategory
from common.managers.model.base import BaseModelManager
from scheduling.models import LocationSchedule
from django.forms.models import model_to_dict


class LocationScheduleManager(BaseModelManager):
    model = LocationSchedule

    def __init__(self, practice_location_id, **kwargs):
        super().__init__(**kwargs)
        self.practice_location_id = practice_location_id
        self.practice_location_ids = kwargs.get("practice_location_ids")

        self.walkin_schedule, self.holiday_schedule = None, None
        self.walkin_schedules_maps, self.holiday_schedules_maps = {}, {}
        if self.practice_location_id:
            self.walkin_schedule = self.get_walkin_schedule()
            self.holiday_schedule = self.get_holiday_schedule()

        elif self.practice_location_ids:
            self.walkin_schedules_maps = self.build_walkin_schedules_maps()
            self.holiday_schedules_maps = self.build_holiday_schedules_maps()

    @classmethod
    def _get_schedule_details_map_for_a_location(cls, schedule_details):
        walkin_schedule_map = {}
        for schedule_detail in schedule_details:
            walkin_schedule_map[schedule_detail.day_of_week] = model_to_dict(
                schedule_detail
            )

        return walkin_schedule_map

    def build_walkin_schedules_maps(self):
        walkin_schedules_maps = {}
        walkin_schedules = self._get_location_schedule_by_category(
            practice_location_ids=self.practice_location_ids,
            schedule_category=ScheduleCategory.walkin.value,
            first=False,
        )

        if not walkin_schedules:
            return walkin_schedules_maps

        for walkin_schedule in walkin_schedules:
            practice_location_id = str(walkin_schedule.practice_location_id)
            schedule_details = walkin_schedule.locationscheduledetail_set.all()
            walkin_schedule_for_location_map = (
                self._get_schedule_details_map_for_a_location(
                    schedule_details=schedule_details
                )
            )
            walkin_schedules_maps[
                practice_location_id
            ] = walkin_schedule_for_location_map

        return walkin_schedules_maps

    def build_holiday_schedules_maps(self):
        holidays_schedules_maps = {}
        holidays_schedules = self._get_location_schedule_by_category(
            practice_location_ids=self.practice_location_ids,
            schedule_category=ScheduleCategory.holidays.value,
            first=False,
        )

        if not holidays_schedules:
            return holidays_schedules_maps

        for holiday_schedule in holidays_schedules:
            practice_location_id = holiday_schedule.practice_location_id
            schedule_details = holiday_schedule.locationscheduledetail_set.all.all()

            location_holiday_schedule_list = [
                model_to_dict(schedule_detail) for schedule_detail in schedule_details
            ]
            holidays_schedules[practice_location_id] = location_holiday_schedule_list

        return holidays_schedules

    def get_walkin_schedule(self):
        walkin_schedule_map = {}
        walkin_schedule = self._get_location_schedule_by_category(
            practice_location_ids=[self.practice_location_id],
            schedule_category=ScheduleCategory.walkin.value,
        )

        if not walkin_schedule:
            return walkin_schedule_map
        schedule_details = walkin_schedule.locationscheduledetail_set.all()
        walkin_schedule_map = self._get_schedule_details_map_for_a_location(
            schedule_details=schedule_details
        )

        return walkin_schedule_map

    def get_holiday_schedule(self):
        holiday_schedule_obj = self._get_location_schedule_by_category(
            practice_location_ids=[self.practice_location_id],
            schedule_category=ScheduleCategory.holidays.value,
        )

        holiday_schedule = []
        if not holiday_schedule_obj:
            return holiday_schedule

        schedule_details = holiday_schedule_obj.locationscheduledetail_set.all.all()
        for schedule_detail in schedule_details:
            holiday_schedule.append(model_to_dict(schedule_detail))

        return holiday_schedule

    @classmethod
    # @lru_cache(maxsize=512)
    def _get_location_schedule_by_category(
        cls, practice_location_ids, schedule_category, first=True
    ):
        qs = cls.filter_by(
            practice_location_id__in=practice_location_ids,
            schedule_category=schedule_category,
            active=True,
        ).prefetch_related("locationscheduledetail_set")

        if first:
            return qs.first()

        return qs
