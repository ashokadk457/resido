# from functools import lru_cache

# from django.db import models
# from django.contrib.postgres.fields import ArrayField


# from common.constants import (
#     DayOfWeek,
#     EventRepeatFrequency,
#     ScheduleCategory,
#     ScheduleType,
#     CategoryForVisitType,
#     EventType,
# )
# from audit.models import GenericModel
# from common.models import optional
# from locations.models import PracticeLocation
# from lookup.fields import LookupField
# from meetings.models import Meeting
# from staff.models import HelixStaff
# from scheduling.constants import EventCategory


# class BaseScheduleDetail(GenericModel):
#     name = models.CharField(max_length=50, **optional)
#     day_of_week = models.CharField(
#         choices=DayOfWeek.choices(), max_length=50, db_index=True, **optional
#     )
#     month = models.IntegerField(**optional)
#     day_of_month = models.IntegerField(**optional)
#     start_time = models.TimeField(**optional)
#     end_time = models.TimeField(**optional)
#     holiday = models.BooleanField(**optional, db_index=True)
#     active = models.BooleanField(default=True, db_index=True)

#     class Meta:
#         abstract = True


# class ScheduleTemplate(GenericModel):
#     name = models.CharField(max_length=50)
#     description = models.TextField(**optional)
#     template_category = models.CharField(
#         choices=ScheduleCategory.choices(), max_length=50, db_index=True
#     )
#     template_type = models.CharField(
#         choices=ScheduleType.choices(), max_length=50, db_index=True
#     )
#     active = models.BooleanField(default=True, db_index=True)

#     def __str__(self):
#         return self.name


# class ScheduleTemplateDetail(BaseScheduleDetail):
#     schedule_template = models.ForeignKey(ScheduleTemplate, on_delete=models.CASCADE)

#     class Meta:
#         unique_together = [
#             ("schedule_template", "day_of_week"),
#             ("schedule_template", "month", "day_of_month"),
#         ]


# class LocationSchedule(GenericModel):
#     practice_location = models.ForeignKey(
#         PracticeLocation, on_delete=models.CASCADE, **optional
#     )
#     name = models.CharField(max_length=50, **optional)
#     description = models.TextField(**optional)
#     schedule_type = models.CharField(
#         choices=ScheduleType.choices(), max_length=50, **optional
#     )
#     schedule_category = models.CharField(
#         choices=ScheduleCategory.choices(), max_length=50, db_index=True
#     )
#     applicable_start_date = models.DateField()
#     applicable_end_date = models.DateField(**optional)
#     active = models.BooleanField(default=True, db_index=True)

#     class Meta:
#         path_to_location = "practice_location"
#         index_together = [("practice_location", "schedule_category")]


# class LocationScheduleDetail(BaseScheduleDetail):
#     location_schedule = models.ForeignKey(LocationSchedule, on_delete=models.CASCADE)

#     class Meta:
#         path_to_location = "location_schedule__practice_location"
#         unique_together = [
#             ("location_schedule", "day_of_week"),
#             ("location_schedule", "month", "day_of_month"),
#         ]


# class StaffWorkingHour(GenericModel):
#     staff = models.ForeignKey(HelixStaff, on_delete=models.CASCADE)
#     practice_location = models.ForeignKey(PracticeLocation, on_delete=models.CASCADE)
#     name = models.CharField(max_length=50, **optional)
#     applicable_start_date = models.DateField()
#     applicable_end_date = models.DateField(**optional)
#     active = models.BooleanField(default=True, db_index=True)

#     def __str__(self):
#         return f"{self.staff.user.first_name} - {self.name}"

#     class Meta:
#         path_to_location = "practice_location"


# class StaffWorkingHourDetail(BaseScheduleDetail):
#     staff_workinghour = models.ForeignKey(StaffWorkingHour, on_delete=models.CASCADE)

#     class Meta:
#         unique_together = [("staff_workinghour", "day_of_week")]
#         path_to_location = "staff_workinghour__practice_location"


# class StaffEvent(GenericModel):
#     name = models.CharField(max_length=100)
#     short_description = models.CharField(max_length=512, **optional)
#     title = LookupField(
#         max_length=50,
#         lookup_name="EVENT_TITLE",
#         db_index=True,
#         **optional,
#     )
#     category = models.CharField(
#         choices=EventCategory.choices(),
#         default=EventCategory.APPOINTMENT_BLOCK.value,
#         max_length=200,
#     )
#     description = models.TextField(**optional)
#     staff = models.ForeignKey(HelixStaff, on_delete=models.CASCADE)
#     practice_location = models.ForeignKey(
#         PracticeLocation, on_delete=models.CASCADE, **optional
#     )
#     start_date = models.DateField()
#     end_date = models.DateField(**optional)
#     start_time = models.TimeField()
#     end_time = models.TimeField()
#     repeating = models.BooleanField(default=False, db_index=True)
#     repeat_interval = models.IntegerField(**optional)
#     repeat_frequency = models.CharField(
#         choices=EventRepeatFrequency.choices(), max_length=50, **optional
#     )
#     repeat_on_days_of_week = ArrayField(
#         models.CharField(choices=DayOfWeek.choices(), max_length=50), **optional
#     )
#     repeat_on_day_of_month = models.IntegerField(**optional)
#     visit_types = ArrayField(
#         LookupField(max_length=100, lookup_name="VISIT_TYPE", db_index=True), **optional
#     )
#     meeting = models.OneToOneField(
#         Meeting, on_delete=models.DO_NOTHING, related_name="scheduled_event", **optional
#     )
#     active = models.BooleanField(default=True, db_index=True)

#     def __str__(self):
#         return f"{self.staff.__str__()} - {self.title} - {self.category}"

#     class Meta:
#         path_to_location = "practice_location"

#     def save(self, *args, **kwargs):
#         return super(StaffEvent, self).save(*args, **kwargs)

#     @property
#     def schedule(self):
#         base_schedule = {
#             "host_name": self.staff.name,
#             "title": self.name,
#             "category": self.category,
#             "description": self.description,
#             "start_date": self.start_date.isoformat(),
#             "end_date": self.end_date.isoformat() if self.end_date else None,
#             "start_time": self.start_time.isoformat(),
#             "end_time": self.end_time.isoformat(),
#             "repeating": self.repeating,
#             "repeat_interval": self.repeat_interval,
#             "repeat_frequency": self.repeat_frequency,
#             "repeat_on_days_of_week": self.repeat_on_days_of_week,
#             "repeat_on_day_of_month": self.repeat_on_day_of_month,
#             "meeting_room": None,
#             "meeting_link": None,
#         }
#         if self.meeting is not None:
#             base_schedule["meeting_room"] = self.meeting.room_name
#             base_schedule["meeting_link"] = self.meeting.link
#         return base_schedule

#     @property
#     @lru_cache(maxsize=512)
#     def event_type(self):
#         from scheduling.managers.title_availability import TitleAvailabilityManager

#         event_title_availabilities = TitleAvailabilityManager.filter_by_title(
#             title=self.title
#         )
#         if not event_title_availabilities:
#             return

#         event_title_availability = event_title_availabilities[0]

#         return (
#             EventType.available.values
#             if (
#                 event_title_availability
#                 and event_title_availability["available_for_appointment"]
#             )
#             else EventType.unavailable.values
#         )


# class EventInstanceUpdate(GenericModel):
#     event = models.ForeignKey(StaffEvent, on_delete=models.CASCADE, db_index=True)
#     for_date = models.DateField(**optional, db_index=True)
#     new_start_time = models.TimeField(**optional)
#     new_end_time = models.TimeField(**optional)
#     cancelled = models.BooleanField(**optional, db_index=True)
#     all_future = models.BooleanField(**optional, db_index=True)

#     class Meta:
#         unique_together = ("event", "for_date")
#         path_to_location = "event__practice_location"
#         index_together = [("event", "for_date", "all_future")]


# class StaffVisitTypeConfiguration(GenericModel):
#     staff = models.ForeignKey(HelixStaff, **optional, on_delete=models.CASCADE)
#     visit_type = LookupField(max_length=100, lookup_name="VISIT_TYPE", db_index=True)
#     duration = models.IntegerField()
#     max_bookings = models.IntegerField()
#     active = models.BooleanField(default=True, db_index=True)

#     class Meta:
#         unique_together = ("staff", "visit_type")
#         path_to_location = "staff__locations"

#     def __str__(self):
#         return f"{self.staff.__str__()} - {self.visit_type}"


# class Slot(GenericModel):
#     event = models.ForeignKey(StaffEvent, on_delete=models.CASCADE)
#     slot_start_ts = models.DateTimeField(db_index=True)
#     slot_end_ts = models.DateTimeField(db_index=True)
#     visit_type = LookupField(
#         max_length=100, lookup_name="VISIT_TYPE", db_index=True, **optional
#     )
#     total_bookings = models.IntegerField(default=0, db_index=True)

#     class Meta:
#         path_to_location = "event__practice_location"

#     def __str__(self):
#         return f"{self.event.__str__()} - {self.slot_start_ts} - {self.slot_end_ts}"


# class EventTitleAvailability(GenericModel):
#     MODEL_ALL_DATA_CACHE_KEY = "EVENT_TITLE_AVAILABILITY"

#     event_title = LookupField(
#         max_length=50,
#         lookup_name="EVENT_TITLE",
#         db_index=True,
#         default="AVAILABLE",
#         unique=True,
#     )
#     available_for_appointment = models.BooleanField(default=False, db_index=True)


# class VisitTypeCategory(GenericModel):
#     visit_type = LookupField(max_length=100, lookup_name="VISIT_TYPE", db_index=True)
#     category = models.CharField(
#         choices=CategoryForVisitType.choices(), max_length=50, db_index=True, **optional
#     )
