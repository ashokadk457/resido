# from django.contrib import admin

# from common.utils.admin import PULSEBaseAdmin
# from scheduling.models import (
#     StaffWorkingHour,
#     StaffEvent,
#     EventInstanceUpdate,
#     StaffVisitTypeConfiguration,
#     Slot,
#     ScheduleTemplate,
#     ScheduleTemplateDetail,
#     LocationSchedule,
#     LocationScheduleDetail,
#     StaffWorkingHourDetail,
#     EventTitleAvailability,
#     VisitTypeCategory,
# )
# from scheduling.models_v2 import (
#     VisitCategory,
#     VisitType,
#     VisitTypeTemplate,
#     VisitTypeTemplateComposition,
#     VisitTypeAssignmentRequest,
#     VisitTypeAssignmentRequestComposition,
#     VisitTypeAssignmentRequestTarget,
#     StaffVisitType,
# )


# # Register your models here.
# @admin.register(ScheduleTemplate)
# class ScheduleTemplateAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "name",
#         "description",
#         "template_category",
#         "template_type",
#         "active",
#     )


# @admin.register(ScheduleTemplateDetail)
# class ScheduleTemplateDetailAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "schedule_template",
#         "name",
#         "day_of_week",
#         "month",
#         "day_of_month",
#         "start_time",
#         "end_time",
#         "active",
#     )


# @admin.register(LocationSchedule)
# class LocationScheduleAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "practice_location",
#         "name",
#         "description",
#         "schedule_category",
#         "schedule_type",
#         "applicable_start_date",
#         "applicable_end_date",
#         "active",
#     )


# @admin.register(LocationScheduleDetail)
# class LocationScheduleDetailAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "location_schedule",
#         "name",
#         "day_of_week",
#         "month",
#         "day_of_month",
#         "start_time",
#         "end_time",
#         "active",
#     )


# @admin.register(StaffWorkingHour)
# class StaffWorkingHourAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "staff",
#         "practice_location",
#         "name",
#         "applicable_start_date",
#         "applicable_end_date",
#         "active",
#     )


# @admin.register(StaffWorkingHourDetail)
# class StaffWorkingHourDetailAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "staff_workinghour",
#         "name",
#         "day_of_week",
#         "month",
#         "day_of_month",
#         "start_time",
#         "end_time",
#         "active",
#     )


# @admin.register(StaffEvent)
# class StaffEventAdmin(PULSEBaseAdmin):
#     list_display = (
#         'id',
#         'staff',
#         "practice_location",
#         'name',
#         "title",
#         'start_date',
#         "end_date",
#         "start_time",
#         "end_time",
#         "repeating",
#         "repeat_frequency",
#         "repeat_interval",
#         "repeat_on_days_of_week",
#         "repeat_on_day_of_month",
#         "event_type",
#         "visit_types",
#         'active',
#         'created_on_ist',
#         'updated_on_ist',
#     )
#     list_filter = ("repeating", "active")
#     search_fields = ["id", "staff__id", "name", "title"]


# @admin.register(EventInstanceUpdate)
# class EventInstanceUpdateAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "event",
#         "for_date",
#         "all_future",
#         "new_start_time",
#         "new_end_time",
#         "cancelled",
#         "created_on",
#         "updated_on",
#     )


# @admin.register(StaffVisitTypeConfiguration)
# class StaffVisitTypeConfigurationAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "staff",
#         "visit_type",
#         "duration",
#         "max_bookings",
#         "active",
#         "created_on",
#         "updated_on",
#     )


# @admin.register(Slot)
# class SlotAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "event",
#         "slot_start_ts",
#         "slot_end_ts",
#         "visit_type",
#         "total_bookings",
#         "created_on",
#         "updated_on",
#     )


# @admin.register(EventTitleAvailability)
# class EventTitleAvailabilityAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "event_title",
#         "available_for_appointment",
#         "created_on",
#         "updated_on",
#     )
#     list_filter = ("event_title", "available_for_appointment")
#     search_fields = ["id"]


# @admin.register(VisitTypeCategory)
# class VisitTypeCategoryAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "visit_type",
#         "category",
#         "created_on",
#         "updated_on",
#     )
#     list_filter = ["category"]
#     search_fields = ["id"]


# @admin.register(VisitCategory)
# class VisitCategoryAdmin(PULSEBaseAdmin):
#     list_display = (
#         "id",
#         "display_id",
#         "speciality_name",
#         "name",
#         "active",
#         "seeded",
#         "created_on_ist",
#         "updated_on_ist",
#         "visit_types",
#     )
#     ordering = ["-created_on"]
#     list_per_page = 25
#     list_filter = (
#         "active",
#         "seeded",
#     )
#     search_fields = (
#         "id",
#         "display_id",
#         "name",
#         "speciality__id",
#     )

#     def speciality_name(self, obj):
#         if obj.speciality is None:
#             return None

#         speciality_id, link_text = str(obj.speciality.id), str(
#             obj.speciality.specialization
#         )

#         return self._get_admin_changelist_link(
#             app="symptoms",
#             model="nucctaxonomy",
#             obj_id=speciality_id,
#             link_text=link_text,
#         )

#     def visit_types(self, obj):
#         _obj_id, link_text = (
#             str(obj.id),
#             "View Visit Types",
#         )
#         if not _obj_id:
#             return _obj_id

#         return self._get_admin_changelist_link(
#             app="scheduling",
#             model="visittype",
#             obj_id=_obj_id,
#             link_text=link_text,
#         )


# @admin.register(VisitType)
# class VisitTypeAdmin(PULSEBaseAdmin):
#     list_display = (
#         "id",
#         "display_id",
#         "category_info",
#         "name",
#         "color_code",
#         "duration",
#         "duration_unit",
#         "frequency",
#         "default",
#         "seeded",
#         "active",
#         "created_on_ist",
#         "updated_on_ist",
#     )
#     ordering = ["-created_on"]
#     list_per_page = 25
#     list_filter = (
#         "default",
#         "active",
#         "seeded",
#     )
#     search_fields = (
#         "id",
#         "display_id",
#         "name",
#         "category__id",
#         "category__speciality__id",
#     )

#     def category_info(self, obj):
#         if obj.category is None:
#             return None

#         category_id, link_text = str(obj.category.id), str(obj.category.__str__())

#         return self._get_admin_changelist_link(
#             app="scheduling",
#             model="visitcategory",
#             obj_id=category_id,
#             link_text=link_text,
#         )


# @admin.register(VisitTypeTemplate)
# class VisitTypeTemplateAdmin(PULSEBaseAdmin):
#     list_display = (
#         "id",
#         "display_id",
#         "speciality_name",
#         "name",
#         "active",
#         "created_on_ist",
#         "updated_on_ist",
#         "composition",
#     )
#     ordering = ["-created_on"]
#     list_per_page = 25
#     list_filter = ("active",)
#     search_fields = (
#         "id",
#         "display_id",
#         "name",
#         "speciality__id",
#     )

#     def speciality_name(self, obj):
#         if obj.speciality is None:
#             return None

#         speciality_id, link_text = str(obj.speciality.id), str(
#             obj.speciality.specialization
#         )

#         return self._get_admin_changelist_link(
#             app="symptoms",
#             model="nucctaxonomy",
#             obj_id=speciality_id,
#             link_text=link_text,
#         )

#     def composition(self, obj):
#         _obj_id, link_text = (
#             str(obj.id),
#             "View Composition",
#         )
#         if not _obj_id:
#             return _obj_id

#         return self._get_admin_changelist_link(
#             app="scheduling",
#             model="visittypetemplatecomposition",
#             obj_id=_obj_id,
#             link_text=link_text,
#         )


# @admin.register(VisitTypeTemplateComposition)
# class VisitTypeTemplateCompositionAdmin(PULSEBaseAdmin):
#     list_display = (
#         "id",
#         "display_id",
#         "template_name",
#         "visit_type_name",
#         "color_code",
#         "duration",
#         "duration_unit",
#         "frequency",
#         "default",
#         "created_on_ist",
#         "updated_on_ist",
#     )
#     ordering = ["-created_on"]
#     list_per_page = 25
#     search_fields = (
#         "id",
#         "display_id",
#         "template__id",
#     )

#     def template_name(self, obj):
#         if obj.template is None:
#             return None

#         template_id, link_text = str(obj.template.id), str(obj.template.name)

#         return self._get_admin_changelist_link(
#             app="scheduling",
#             model="visittypetemplate",
#             obj_id=template_id,
#             link_text=link_text,
#         )

#     def visit_type_name(self, obj):
#         if obj.visit_type is None:
#             return None

#         template_id, link_text = str(obj.visit_type.id), str(obj.visit_type.name)

#         return self._get_admin_changelist_link(
#             app="scheduling",
#             model="visittype",
#             obj_id=template_id,
#             link_text=link_text,
#         )


# @admin.register(VisitTypeAssignmentRequest)
# class VisitTypeAssignmentRequestAdmin(PULSEBaseAdmin):
#     readonly_fields = (
#         "created_by",
#         "updated_by",
#         "deleted_by",
#         "source_template",
#         "process",
#         "source_staff",
#         "source_speciality",
#         "method",
#     )
#     list_display = (
#         "id",
#         "display_id",
#         "process_id",
#         "method",
#         "source_template",
#         "source_staff",
#         "source_speciality",
#         "status",
#         "created_on_ist",
#         "updated_on_ist",
#         "targets",
#         "composition",
#     )
#     ordering = ["-created_on"]
#     list_per_page = 25
#     list_filter = ("method", "status")
#     search_fields = ("id", "display_id")

#     def composition(self, obj):
#         _obj_id, link_text = (
#             str(obj.id),
#             "View Composition",
#         )
#         if not _obj_id:
#             return _obj_id

#         return self._get_admin_changelist_link(
#             app="scheduling",
#             model="visittypeassignmentrequestcomposition",
#             obj_id=_obj_id,
#             link_text=link_text,
#         )

#     def targets(self, obj):
#         _obj_id, link_text = (
#             str(obj.id),
#             "View Targets",
#         )
#         if not _obj_id:
#             return _obj_id

#         return self._get_admin_changelist_link(
#             app="scheduling",
#             model="visittypeassignmentrequesttarget",
#             obj_id=_obj_id,
#             link_text=link_text,
#         )

#     def process_id(self, obj):
#         _obj_id, link_text = str(obj.process_id), str(obj.process_id)
#         if not _obj_id:
#             return _obj_id

#         return self._get_admin_changelist_link(
#             app="processflow", model="process", obj_id=_obj_id, link_text=link_text
#         )


# @admin.register(VisitTypeAssignmentRequestComposition)
# class VisitTypeAssignmentRequestCompositionAdmin(PULSEBaseAdmin):
#     readonly_fields = ("created_by", "updated_by", "deleted_by", "staff")

#     list_display = (
#         "id",
#         "display_id",
#         "assignment_request_id",
#         "staff",
#         "visit_type_name",
#         "color_code",
#         "duration",
#         "duration_unit",
#         "frequency",
#         "default",
#         "overridden",
#         "created_on_ist",
#         "updated_on_ist",
#     )
#     ordering = ["-created_on"]
#     list_per_page = 25
#     search_fields = (
#         "id",
#         "display_id",
#         "assignment_request__id",
#     )
#     list_filter = ("default", "overridden")

#     def assignment_request_id(self, obj):
#         if obj.assignment_request is None:
#             return None

#         assignment_request_id, link_text = str(obj.assignment_request.id), str(
#             obj.assignment_request.display_id
#         )

#         return self._get_admin_changelist_link(
#             app="scheduling",
#             model="visittypeassignmentrequest",
#             obj_id=assignment_request_id,
#             link_text=link_text,
#         )

#     def visit_type_name(self, obj):
#         if obj.visit_type is None:
#             return None

#         template_id, link_text = str(obj.visit_type.id), str(obj.visit_type.name)

#         return self._get_admin_changelist_link(
#             app="scheduling",
#             model="visittype",
#             obj_id=template_id,
#             link_text=link_text,
#         )


# @admin.register(VisitTypeAssignmentRequestTarget)
# class VisitTypeAssignmentRequestTargetAdmin(PULSEBaseAdmin):
#     readonly_fields = (
#         "created_by",
#         "updated_by",
#         "deleted_by",
#         "assignment_request",
#         "staff",
#     )
#     list_display = (
#         "id",
#         "display_id",
#         "assignment_request_id",
#         "staff",
#         "created_on_ist",
#         "updated_on_ist",
#     )
#     ordering = ["-created_on"]
#     list_per_page = 25
#     search_fields = (
#         "id",
#         "display_id",
#         "assignment_request__id",
#     )

#     def assignment_request_id(self, obj):
#         if obj.assignment_request is None:
#             return None

#         template_id, link_text = str(obj.assignment_request.id), str(
#             obj.assignment_request.display_id
#         )

#         return self._get_admin_changelist_link(
#             app="scheduling",
#             model="visittypeassignmentrequest",
#             obj_id=template_id,
#             link_text=link_text,
#         )


# @admin.register(StaffVisitType)
# class StaffVisitTypeAdmin(PULSEBaseAdmin):
#     readonly_fields = (
#         "created_by",
#         "updated_by",
#         "deleted_by",
#         "staff",
#         "assignment_request",
#         "visit_type",
#     )
#     list_display = (
#         "id",
#         "display_id",
#         "assignment_request_id",
#         "staff",
#         "visit_type_name",
#         "color_code",
#         "duration",
#         "duration_unit",
#         "frequency",
#         "default",
#         "created_on_ist",
#         "updated_on_ist",
#     )
#     ordering = ["-created_on"]
#     list_per_page = 25
#     search_fields = (
#         "id",
#         "display_id",
#         "staff__id",
#         "assignment_request__id",
#     )

#     def assignment_request_id(self, obj):
#         if obj.assignment_request is None:
#             return None

#         template_id, link_text = str(obj.assignment_request.id), str(
#             obj.assignment_request.display_id
#         )

#         return self._get_admin_changelist_link(
#             app="scheduling",
#             model="visittypeassignmentrequest",
#             obj_id=template_id,
#             link_text=link_text,
#         )

#     def visit_type_name(self, obj):
#         if obj.visit_type is None:
#             return None

#         template_id, link_text = str(obj.visit_type.id), str(obj.visit_type.name)

#         return self._get_admin_changelist_link(
#             app="scheduling",
#             model="visittype",
#             obj_id=template_id,
#             link_text=link_text,
#         )
