# from django_filters.rest_framework.backends import DjangoFilterBackend
# from rest_framework import generics, status
# from rest_framework.permissions import AllowAny

# from common.errors import ERROR_DETAILS
# from common.exception import StandardAPIException
# from common.mixins import (
#     StandardRetrieveUpdateAPIMixin,
#     StandardListBulkCreateAPIMixin,
#     StandardListCreateAPIMixin,
# )
# from common.permissions import HelixUserBasePermission
# from common.response import StandardAPIResponse
# from helixauth.authentication.composite.guest import GuestCompositeAuthentication
# from scheduling.managers.schedule.staff import StaffScheduleManager
# from scheduling.managers.slots import SlotsManager
# from scheduling.models import (
#     StaffWorkingHour,
#     StaffVisitTypeConfiguration,
#     StaffEvent,
#     EventInstanceUpdate,
#     ScheduleTemplate,
#     ScheduleTemplateDetail,
#     LocationSchedule,
#     LocationScheduleDetail,
#     StaffWorkingHourDetail,
#     VisitTypeCategory,
# )
# from scheduling.serializers import (
#     StaffVisitTypeConfigurationSerializer,
#     StaffEventSerializer,
#     EventInstanceUpdateSerializer,
#     FullScheduleTemplateSerializer,
#     ScheduleTemplateDetailSerializer,
#     FullLocationScheduleSerializer,
#     BaseScheduleTemplateSerializer,
#     BaseLocationScheduleSerializer,
#     LocationScheduleDetailSerializer,
#     FullStaffWorkingHourSerializer,
#     BaseStaffWorkingHourSerializer,
#     StaffWorkingHourDetailSerializer,
#     VisitTypeCategorySerializer,
#     StaffEventUpdateSerializer,
# )


# class ScheduleTemplatesListCreateAPIView(StandardListCreateAPIMixin):
#     permission_classes = [HelixUserBasePermission]
#     queryset = ScheduleTemplate.objects.all()
#     entity = "ScheduleTemplate"
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ["active", "template_type", "template_category"]

#     def get_serializer_class(self):
#         if (
#             self.request.query_params.get("details") in ["True", "true"]
#             or "details" in self.request.data
#         ):
#             return FullScheduleTemplateSerializer

#         return BaseScheduleTemplateSerializer


# class ScheduleTemplatesRetrieveUpdateAPIView(StandardRetrieveUpdateAPIMixin):
#     permission_classes = [HelixUserBasePermission]
#     queryset = ScheduleTemplate.objects.all()
#     entity = "ScheduleTemplate"

#     def get_serializer_class(self):
#         if self.request.query_params.get("details") in ["True", "true"]:
#             return FullScheduleTemplateSerializer

#         return BaseScheduleTemplateSerializer


# class ScheduleTemplateDetailsListCreateAPIView(StandardListBulkCreateAPIMixin):
#     permission_classes = [HelixUserBasePermission]
#     queryset = ScheduleTemplateDetail.objects.all()
#     serializer_class = ScheduleTemplateDetailSerializer
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ["active"]
#     entity = "ScheduleTemplateDetail"

#     @staticmethod
#     def filter_by_schedule_template(queryset, schedule_template_id):
#         return queryset.filter(schedule_template_id=schedule_template_id)

#     def filter_queryset(self, queryset):
#         qs = super(ScheduleTemplateDetailsListCreateAPIView, self).filter_queryset(
#             queryset
#         )
#         schedule_template_id = self.request.query_params.get("schedule_template")
#         if schedule_template_id:
#             qs = self.filter_by_schedule_template(queryset, schedule_template_id)

#         return qs


# class ScheduleTemplateDetailsRetrieveUpdateAPIView(StandardRetrieveUpdateAPIMixin):
#     permission_classes = [HelixUserBasePermission]  # permission
#     serializer_class = ScheduleTemplateDetailSerializer
#     queryset = ScheduleTemplateDetail.objects.all()
#     entity = "ScheduleTemplateDetail"


# class LocationScheduleListCreateAPIView(StandardListBulkCreateAPIMixin):
#     permission_classes = [HelixUserBasePermission]
#     queryset = LocationSchedule.objects.for_current_user()
#     entity = "LocationSchedule"
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ["active", "schedule_category", "schedule_type"]

#     def get_serializer_class(self):
#         if (
#             self.request.query_params.get("details") in ["True", "true"]
#             or "details" in self.request.data
#         ):
#             return FullLocationScheduleSerializer

#         return BaseLocationScheduleSerializer

#     @staticmethod
#     def filter_by_practice_location_id(queryset, practice_location_id):
#         return queryset.filter(practice_location_id=practice_location_id)

#     def filter_queryset(self, queryset):
#         qs = super().filter_queryset(queryset)
#         practice_location_id = self.request.query_params.get("practice_location")
#         if practice_location_id:
#             qs = self.filter_by_practice_location_id(qs, practice_location_id)

#         return qs


# class LocationScheduleRetrieveUpdateAPIView(StandardRetrieveUpdateAPIMixin):
#     permission_classes = [HelixUserBasePermission]  # permission
#     queryset = LocationSchedule.objects.for_current_user()
#     entity = "LocationSchedule"

#     def get_serializer_class(self):
#         if self.request.query_params.get("details") in ["True", "true"]:
#             return FullLocationScheduleSerializer

#         return BaseLocationScheduleSerializer


# class LocationScheduleDetailsListCreateAPIView(StandardListBulkCreateAPIMixin):
#     permission_classes = [HelixUserBasePermission]  # permission
#     queryset = LocationScheduleDetail.objects.for_current_user()
#     serializer_class = LocationScheduleDetailSerializer
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ["active"]
#     entity = "LocationScheduleDetail"

#     @staticmethod
#     def filter_by_location_schedule(queryset, location_schedule_id):
#         return queryset.filter(location_schedule_id=location_schedule_id)

#     def filter_queryset(self, queryset):
#         qs = super().filter_queryset(queryset)
#         location_schedule_id = self.request.query_params.get("location_schedule")
#         if location_schedule_id:
#             qs = self.filter_by_location_schedule(queryset, location_schedule_id)

#         return qs


# class LocationScheduleDetailsRetrieveUpdateAPIView(StandardRetrieveUpdateAPIMixin):
#     permission_classes = [HelixUserBasePermission]  # permission
#     serializer_class = LocationScheduleDetailSerializer
#     queryset = LocationScheduleDetail.objects.for_current_user()
#     entity = "LocationScheduleDetail"


# class StaffWorkingHourListCreateAPIView(StandardListCreateAPIMixin):
#     permission_classes = [HelixUserBasePermission]  # permission
#     queryset = StaffWorkingHour.objects.for_current_user()
#     entity = "StaffWorkingHour"

#     def get_serializer_class(self):
#         if (
#             self.request.query_params.get("details") in ["True", "true"]
#             or "details" in self.request.data
#         ):
#             return FullStaffWorkingHourSerializer

#         return BaseStaffWorkingHourSerializer

#     @staticmethod
#     def filter_by_staff_id(queryset, staff_id):
#         return queryset.filter(staff_id=staff_id)

#     @staticmethod
#     def filter_by_practice_location_id(queryset, practice_location_id):
#         return queryset.filter(practice_location_id=practice_location_id)

#     def filter_queryset(self, queryset):
#         qs = super().filter_queryset(queryset)
#         staff_id = self.request.query_params.get("staff")
#         practice_location_id = self.request.query_params.get("practice_location")
#         if staff_id:
#             qs = self.filter_by_staff_id(qs, staff_id)
#         if practice_location_id:
#             qs = self.filter_by_practice_location_id(qs, practice_location_id)

#         return qs


# class StaffWorkingHourDetailListCreateAPIView(StandardListBulkCreateAPIMixin):
#     permission_classes = [HelixUserBasePermission]  # permission
#     queryset = StaffWorkingHourDetail.objects.for_current_user()
#     serializer_class = StaffWorkingHourDetailSerializer
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ["active"]
#     entity = "StaffWorkingHourDetail"

#     @staticmethod
#     def filter_by_staff_workinghour(queryset, staff_workinghour_id):
#         return queryset.filter(staff_workinghour_id=staff_workinghour_id)

#     def filter_queryset(self, queryset):
#         qs = super().filter_queryset(queryset)
#         staff_workinghour_id = self.request.query_params.get("staff_workinghour")
#         if staff_workinghour_id:
#             qs = self.filter_by_staff_workinghour(queryset, staff_workinghour_id)

#         return qs


# class StaffWorkingHourDetailRetrieveUpdateAPIView(StandardRetrieveUpdateAPIMixin):
#     permission_classes = [HelixUserBasePermission]  # permission
#     serializer_class = StaffWorkingHourDetailSerializer
#     queryset = StaffWorkingHourDetail.objects.for_current_user()
#     entity = "StaffWorkingHourDetail"


# class StaffVisitTypeConfigurationListCreate(StandardListBulkCreateAPIMixin):
#     permission_classes = [HelixUserBasePermission]  # permission
#     queryset = StaffVisitTypeConfiguration.objects.for_current_user()
#     serializer_class = StaffVisitTypeConfigurationSerializer
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ["staff", "visit_type", "active"]
#     entity = "StaffVisitTypeConfiguration"


# class StaffScheduleAPIView(generics.GenericAPIView):
#     permission_classes = [HelixUserBasePermission]  # permission
#     entity = "StaffEvent"

#     @staticmethod
#     def get(request, *args, **kwargs):
#         staff_id = kwargs.get("staff_id")
#         from_date = request.query_params.get("from_date")
#         to_date = request.query_params.get("to_date")
#         event_type = request.query_params.get("event_type")
#         practice_location_id = request.query_params.get("practice_location")
#         category = request.query_params.get("category")
#         schedule_manager = StaffScheduleManager(
#             staff_id=staff_id,
#             from_date=from_date,
#             to_date=to_date,
#             practice_location_id=practice_location_id,
#             category=category,
#         )
#         data = schedule_manager.build_schedule(event_type=event_type)
#         return StandardAPIResponse(
#             data={"staff_id": staff_id, "schedule": data},
#             status=status.HTTP_200_OK,
#         )


# class StaffSlotsPIView(generics.GenericAPIView):
#     permission_classes = [AllowAny]  # public

#     @staticmethod
#     def get(request, *args, **kwargs):
#         staff_id = kwargs.get("staff_id")
#         from_date = request.query_params.get("from_date")
#         to_date = request.query_params.get("to_date")
#         visit_type = request.query_params.get("visit_type", None)
#         get_all_vt_configs = visit_type is None
#         practice_location_id = request.query_params.get("practice_location")
#         slots_manager = SlotsManager(
#             staff_id=staff_id,
#             from_date=from_date,
#             to_date=to_date,
#             visit_type=visit_type,
#             get_all_vt_configs=get_all_vt_configs,
#             practice_location_id=practice_location_id,
#         )
#         if not get_all_vt_configs:
#             slots, error_code = slots_manager.get_slots()
#         else:
#             slots, error_code = slots_manager.get_min_slot_counts_map()
#         if error_code:
#             raise StandardAPIException(
#                 code=error_code,
#                 detail=ERROR_DETAILS[error_code],
#                 status_code=status.HTTP_400_BAD_REQUEST,
#             )
#         response_data = {
#             "staff_id": staff_id,
#             "from_date": from_date,
#             "to_date": to_date,
#             "visit_type": visit_type,
#             "slots": slots,
#         }
#         return StandardAPIResponse(data=response_data, status=status.HTTP_200_OK)


# class StaffEventsListCreateAPIView(StandardListBulkCreateAPIMixin):
#     permission_classes = [HelixUserBasePermission]  # permission
#     queryset = StaffEvent.objects.for_current_user()
#     serializer_class = StaffEventSerializer
#     entity = "StaffEvent"

#     @staticmethod
#     def filter_by_staff_id(queryset, staff_id):
#         return queryset.filter(staff_id=staff_id)

#     def filter_queryset(self, queryset):
#         qs = super(StaffEventsListCreateAPIView, self).filter_queryset(queryset)
#         staff_id = self.request.query_params.get("staff")
#         if staff_id:
#             qs = self.filter_by_staff_id(queryset, staff_id)

#         return qs


# class StaffEventRetrieveUpdateAPIView(StandardRetrieveUpdateAPIMixin):
#     permission_classes = [HelixUserBasePermission]  # permission
#     queryset = StaffEvent.objects.for_current_user()
#     entity = "StaffEvent"

#     def get_serializer_class(self):
#         if self.request.method in ["PUT", "PATCH"]:
#             return StaffEventUpdateSerializer

#         return StaffEventSerializer

#     def put(self, request, *args, **kwargs):
#         raise StandardAPIException(
#             code="method_not_allowed",
#             detail=ERROR_DETAILS["method_not_allowed"],
#             status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
#         )


# class EventOccurrenceUpdatesListCreateAPIView(StandardListCreateAPIMixin):
#     permission_classes = [HelixUserBasePermission]  # permission
#     queryset = EventInstanceUpdate.objects.for_current_user().select_related("event")
#     serializer_class = EventInstanceUpdateSerializer
#     entity = "EventInstanceUpdate"


# class EventOccurrenceUpdatesRetrieveUpdateAPIView(StandardRetrieveUpdateAPIMixin):
#     permission_classes = [HelixUserBasePermission]  # permission
#     queryset = EventInstanceUpdate.objects.for_current_user()
#     serializer_class = EventInstanceUpdateSerializer
#     entity = "EventInstanceUpdate"


# class VisitTypeCategoriesAPIView(StandardListCreateAPIMixin):
#     authentication_classes = [GuestCompositeAuthentication]
#     permission_classes = [AllowAny]  # public
#     queryset = VisitTypeCategory.objects.all()
#     serializer_class = VisitTypeCategorySerializer

#     def post(self, request, *args, **kwargs):
#         raise StandardAPIException(
#             code="method_not_allowed",
#             detail=ERROR_DETAILS["method_not_allowed"],
#             status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
#         )
