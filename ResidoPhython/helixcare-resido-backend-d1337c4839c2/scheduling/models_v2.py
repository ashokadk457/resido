# from django.db import models
# from rest_framework.exceptions import ValidationError

# from common.constants import DurationUnit
# from common.errors import ERROR_DETAILS
# from common.models import GenericDisplayModel, optional
# from processflow.models import Process
# from staff.models import HelixStaff
# from scheduling.constants import (
#     VisitTypeAssignmentRequestStatus,
#     VisitTypeAssignmentRequestMethod,
# )


# class BaseVisitTypeConfiguration(GenericDisplayModel):
#     color_code = models.CharField(max_length=256, **optional)
#     duration = models.IntegerField()
#     duration_unit = models.CharField(
#         max_length=256,
#         choices=DurationUnit.choices(),
#         default=DurationUnit.MINUTES.value,
#     )
#     frequency = models.IntegerField()
#     default = models.BooleanField(default=False)

#     class Meta:
#         abstract = True


# class VisitCategory(GenericDisplayModel):
#     name = models.CharField(max_length=256)
#     active = models.BooleanField(default=True)
#     seeded = models.BooleanField(default=True)

#     class Meta:
#         unique_together = (("speciality", "name"),)

#     def __str__(self):
#         return f"{self.speciality.__str__()} - {self.name}"


# class VisitType(BaseVisitTypeConfiguration):
#     category = models.ForeignKey(VisitCategory, on_delete=models.CASCADE)
#     name = models.CharField(max_length=256)
#     seeded = models.BooleanField(default=True)
#     active = models.BooleanField(default=True)

#     class Meta:
#         unique_together = (("category", "name"),)

#     def __str__(self):
#         return f"{self.category.__str__()} - {self.name}"

#     def _check_for_current_default_while_updating(self, current_default):
#         if str(self.id) == str(current_default.id):
#             return

#         current_default.default = False
#         current_default.save()
#         return

#     def check_for_current_default(self):
#         if not self.default:
#             return

#         current_default = VisitType.objects.filter(
#             category__speciality__id=str(self.category.speciality.id), default=True
#         ).first()
#         if current_default is None:
#             return

#         if self._state.adding:
#             raise ValidationError(
#                 code="default_visit_type_exists",
#                 detail=ERROR_DETAILS["default_visit_type_exists"].format(
#                     speciality_name=str(self.category.speciality.specialization)
#                 ),
#             )

#         return self._check_for_current_default_while_updating(
#             current_default=current_default
#         )

#     def save(self, *args, **kwargs):
#         self.check_for_current_default()
#         return super(VisitType, self).save(*args, **kwargs)


# class VisitTypeTemplate(GenericDisplayModel):
#     name = models.CharField(max_length=256)
#     description = models.TextField(**optional)
#     active = models.BooleanField(default=True)

#     class Meta:
#         unique_together = (("speciality", "name"),)

#     def __str__(self):
#         return f"{self.speciality.__str__()} - {self.name}"


# class VisitTypeTemplateComposition(BaseVisitTypeConfiguration):
#     template = models.ForeignKey(VisitTypeTemplate, on_delete=models.CASCADE)
#     visit_type = models.ForeignKey(VisitType, on_delete=models.CASCADE)

#     class Meta:
#         unique_together = (("template", "visit_type"),)

#     def __str__(self):
#         return f"{self.template.__str__()} : {self.visit_type.__str__()}"


# class VisitTypeAssignmentRequest(GenericDisplayModel):
#     process = models.ForeignKey(to=Process, on_delete=models.DO_NOTHING, **optional)
#     method = models.CharField(
#         max_length=256, choices=VisitTypeAssignmentRequestMethod.choices()
#     )
#     source_template = models.ForeignKey(
#         VisitTypeTemplate, on_delete=models.CASCADE, **optional
#     )
#     source_staff = models.ForeignKey(HelixStaff, on_delete=models.CASCADE, **optional)
#     status = models.CharField(
#         max_length=100,
#         choices=VisitTypeAssignmentRequestStatus.choices(),
#         default=VisitTypeAssignmentRequestStatus.PENDING.value,
#     )

#     class Meta:
#         unique_together = (("process", "method"),)


# class VisitTypeAssignmentRequestComposition(BaseVisitTypeConfiguration):
#     assignment_request = models.ForeignKey(
#         to=VisitTypeAssignmentRequest, on_delete=models.CASCADE
#     )
#     visit_type = models.ForeignKey(VisitType, on_delete=models.CASCADE)
#     staff = models.ForeignKey(HelixStaff, on_delete=models.CASCADE, **optional)
#     overridden = models.BooleanField(default=False)

#     class Meta:
#         unique_together = (("assignment_request", "visit_type", "overridden"),)


# class VisitTypeAssignmentRequestTarget(GenericDisplayModel):
#     assignment_request = models.ForeignKey(
#         to=VisitTypeAssignmentRequest, on_delete=models.CASCADE
#     )
#     staff = models.ForeignKey(HelixStaff, on_delete=models.CASCADE)

#     class Meta:
#         unique_together = (("assignment_request", "staff"),)


# class StaffVisitType(BaseVisitTypeConfiguration):
#     assignment_request = models.ForeignKey(
#         to=VisitTypeAssignmentRequest, on_delete=models.CASCADE, **optional
#     )
#     staff = models.ForeignKey(HelixStaff, on_delete=models.CASCADE)
#     visit_type = models.ForeignKey(VisitType, on_delete=models.CASCADE)

#     class Meta:
#         unique_together = (("staff", "visit_type", "assignment_request"),)
