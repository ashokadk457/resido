# from rest_framework import serializers

# from lookup.fields import LookupModelSerializer
# from meetings.serializers.meeting import MeetingSerializer
# from scheduling.constants import EventCategory
# from scheduling.models import (
#     StaffWorkingHour,
#     StaffVisitTypeConfiguration,
#     StaffEvent,
#     EventInstanceUpdate,
#     Slot,
#     ScheduleTemplate,
#     ScheduleTemplateDetail,
#     LocationSchedule,
#     LocationScheduleDetail,
#     StaffWorkingHourDetail,
#     VisitTypeCategory,
# )


# class ScheduleTemplateDetailSerializer(serializers.ModelSerializer):
#     schedule_template = serializers.UUIDField(
#         required=False, allow_null=True, write_only=True
#     )
#     schedule_template_id = serializers.UUIDField(
#         required=False, source="schedule_template.id", read_only=True
#     )

#     class Meta:
#         model = ScheduleTemplateDetail
#         fields = '__all__'

#     def create(self, validated_data):
#         validated_data["schedule_template_id"] = validated_data.pop(
#             "schedule_template", None
#         )
#         return ScheduleTemplateDetail.objects.create(**validated_data)


# class BaseScheduleTemplateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ScheduleTemplate
#         fields = '__all__'


# class FullScheduleTemplateSerializer(BaseScheduleTemplateSerializer):
#     details = ScheduleTemplateDetailSerializer(
#         source="scheduletemplatedetail_set", many=True, required=False
#     )

#     def create(self, validated_data):
#         details = validated_data.pop("scheduletemplatedetail_set", None)
#         schedule_template = super().create(validated_data=validated_data)

#         detail_objs = []
#         for detail in details:
#             detail["schedule_template_id"] = schedule_template.id
#             detail_objs.append(ScheduleTemplateDetail(**detail))

#         ScheduleTemplateDetail.objects.bulk_create(detail_objs)

#         return schedule_template


# class LocationScheduleDetailSerializer(serializers.ModelSerializer):
#     location_schedule = serializers.UUIDField(
#         required=False, allow_null=True, write_only=True
#     )
#     location_schedule_id = serializers.UUIDField(
#         required=False, source="location_schedule.id", read_only=True
#     )

#     class Meta:
#         model = LocationScheduleDetail
#         fields = '__all__'

#     def create(self, validated_data):
#         validated_data["location_schedule_id"] = validated_data.pop(
#             "location_schedule", None
#         )
#         return LocationScheduleDetail.objects.create(**validated_data)


# class BaseLocationScheduleSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = LocationSchedule
#         fields = '__all__'


# class FullLocationScheduleSerializer(BaseLocationScheduleSerializer):
#     details = LocationScheduleDetailSerializer(
#         source="locationscheduledetail_set", many=True, required=False
#     )

#     def create(self, validated_data):
#         details = validated_data.pop("locationscheduledetail_set", None)
#         location_schedule = super().create(validated_data=validated_data)

#         detail_objs = []
#         for detail in details:
#             detail["location_schedule_id"] = location_schedule.id
#             detail_objs.append(LocationScheduleDetail(**detail))

#         LocationScheduleDetail.objects.bulk_create(detail_objs)

#         return location_schedule


# class StaffWorkingHourDetailSerializer(serializers.ModelSerializer):
#     staff_workinghour = serializers.UUIDField(
#         required=False, allow_null=True, write_only=True
#     )
#     staff_workinghour_id = serializers.UUIDField(
#         required=False, source="staff_workinghour.id", read_only=True
#     )

#     class Meta:
#         model = StaffWorkingHourDetail
#         fields = '__all__'

#     def create(self, validated_data):
#         validated_data["staff_workinghour_id"] = validated_data.pop(
#             "staff_workinghour", None
#         )
#         return StaffWorkingHourDetail.objects.create(**validated_data)


# class BaseStaffWorkingHourSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = StaffWorkingHour
#         fields = '__all__'


# class FullStaffWorkingHourSerializer(BaseStaffWorkingHourSerializer):
#     details = StaffWorkingHourDetailSerializer(
#         source="staffworkinghourdetail_set", many=True, required=False
#     )

#     def create(self, validated_data):
#         details = validated_data.pop("staffworkinghourdetail_set", None)
#         staff_workinghour = super().create(validated_data=validated_data)

#         detail_objs = []
#         for detail in details:
#             detail["staff_workinghour_id"] = staff_workinghour.id
#             detail_objs.append(StaffWorkingHourDetail(**detail))

#         StaffWorkingHourDetail.objects.bulk_create(detail_objs)

#         return staff_workinghour


# class StaffVisitTypeConfigurationSerializer(LookupModelSerializer):
#     class Meta:
#         model = StaffVisitTypeConfiguration
#         fields = "__all__"


# class EventInstanceSerializer(LookupModelSerializer):
#     practice_location_id = serializers.UUIDField(
#         source="practice_location.id", default=None
#     )
#     practice_location_name = serializers.CharField(
#         source="practice_location.name", default=None
#     )
#     practice_location_address = serializers.CharField(
#         source="practice_location.address", default=None
#     )
#     practice_location_address_1 = serializers.CharField(
#         source="practice_location.address_1", default=None
#     )
#     practice_location_city = serializers.CharField(
#         source="practice_location.city", default=None
#     )
#     practice_location_state = serializers.CharField(
#         source="practice_location.state", default=None
#     )
#     practice_location_zipcode = serializers.CharField(
#         source="practice_location.zipcode", default=None
#     )
#     practice_location_country = serializers.CharField(
#         source="practice_location.country", default=None
#     )
#     meeting = MeetingSerializer(required=False, default=None)

#     class Meta:
#         model = StaffEvent
#         fields = [
#             "id",
#             "short_description",
#             "description",
#             "name",
#             "title",
#             "start_date",
#             "end_date",
#             "practice_location_id",
#             "practice_location_name",
#             "practice_location_address",
#             "practice_location_address_1",
#             "practice_location_city",
#             "practice_location_state",
#             "practice_location_zipcode",
#             "practice_location_country",
#             "repeating",
#             "repeat_interval",
#             "repeat_frequency",
#             "repeat_on_days_of_week",
#             "repeat_on_day_of_month",
#             "start_time",
#             "end_time",
#             "event_type",
#             "visit_types",
#             "meeting",
#             "active",
#         ]


# class StaffEventSerializer(LookupModelSerializer):
#     practice_location_name = serializers.CharField(
#         source="practice_location.name", required=False, read_only=True
#     )
#     health_center_id = serializers.UUIDField(
#         source="practice_location.health_center.id", required=False, read_only=True
#     )
#     health_center_name = serializers.CharField(
#         source="practice_location.health_center.name", required=False, read_only=True
#     )
#     meeting = serializers.JSONField(required=False)

#     class Meta:
#         model = StaffEvent
#         fields = "__all__"

#     @staticmethod
#     def create_meeting(meeting_data):
#         if not meeting_data:
#             return
#         meeting_serializer = MeetingSerializer(data=meeting_data)
#         meeting_serializer.is_valid(raise_exception=True)
#         return meeting_serializer.save()

#     @staticmethod
#     def send_invites(event_obj):
#         from scheduling.managers.event import EventManager

#         if event_obj.category == EventCategory.APPOINTMENT_BLOCK.value:
#             return

#         event_manager = EventManager(
#             staff_id=str(event_obj.staff.id), event_obj=event_obj
#         )
#         event_manager.invite_all()

#     def create(self, validated_data):
#         meeting_data = validated_data.pop("meeting", {})
#         meeting_obj = self.create_meeting(meeting_data=meeting_data)
#         if meeting_obj is not None:
#             validated_data["meeting_id"] = str(meeting_obj.id)

#         event_obj = StaffEvent.objects.create(**validated_data)
#         self.send_invites(event_obj=event_obj)
#         return event_obj

#     def to_representation(self, instance):
#         event_representation = super().to_representation(instance=instance)
#         meeting_representation = MeetingSerializer(instance=instance.meeting).data
#         event_representation["meeting"] = meeting_representation

#         return event_representation


# class EventInstanceUpdateSerializer(serializers.ModelSerializer):
#     # event_detail = StaffEventSerializer(source="event", required=False)

#     class Meta:
#         model = EventInstanceUpdate
#         fields = "__all__"


# class StaffEventUpdateSerializer(LookupModelSerializer):
#     practice_location_name = serializers.CharField(
#         source="practice_location.name", required=False
#     )
#     health_center_id = serializers.UUIDField(
#         source="practice_location.health_center.id", required=False
#     )
#     health_center_name = serializers.CharField(
#         source="practice_location.health_center.name", required=False
#     )
#     event_instance_update = serializers.JSONField(required=False)

#     class Meta:
#         model = StaffEvent
#         fields = "__all__"

#     def update(self, instance, validated_data):
#         validated_data.pop("start_time", None)
#         validated_data.pop("end_time", None)
#         event_instance_update_data = validated_data.pop("event_instance_update", None)
#         if event_instance_update_data:
#             event_instance_update_id = event_instance_update_data.pop("id", None)
#             event_instance_update_obj, _ = EventInstanceUpdate.objects.update_or_create(
#                 id=event_instance_update_id, defaults=event_instance_update_data
#             )
#             self.context[
#                 "event_instance_update"
#             ] = EventInstanceUpdateSerializer().to_representation(
#                 instance=event_instance_update_obj
#             )
#         return super().update(instance, validated_data)

#     def to_representation(self, instance):
#         response = super().to_representation(instance=instance)
#         response["event_instance_update"] = self.context["event_instance_update"]
#         return response


# class SlotSerializer(LookupModelSerializer):
#     event_id = serializers.CharField(required=False)

#     class Meta:
#         model = Slot
#         fields = "__all__"

#     def get_event_id(self):
#         return self.instance.event.id


# class VisitTypeCategorySerializer(LookupModelSerializer):
#     class Meta:
#         model = VisitTypeCategory
#         fields = "__all__"
