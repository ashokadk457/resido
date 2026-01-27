# from rest_framework import serializers

# from common.constants import TRUE_QUERY_PARAMS
# from common.errors import ERROR_DETAILS
# from common.serializers import StandardModelSerializer
# from scheduling.constants import (
#     FROM_SOURCE_STAFF,
#     FROM_SOURCE_TEMPLATE,
#     FROM_SOURCE_COMPOSITION,
#     ASSIGNMENT_REQUEST_METHODS,
# )
# from scheduling.managers.vt.assignment.request import VisitTypeAssignmentRequestManager
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


# class VisitCategorySerializer(StandardModelSerializer):
#     display_id = serializers.CharField(read_only=True)

#     class Meta:
#         model = VisitCategory
#         fields = "__all__"

#     def to_representation(self, instance):
#         representation = super(VisitCategorySerializer, self).to_representation(
#             instance=instance
#         )
#         return representation

#     def update(self, instance, validated_data):
#         if validated_data.get("speciality") or "seeded" in validated_data:
#             raise serializers.ValidationError(
#                 code="cannot_update_speciality_or_seeded",
#                 detail=ERROR_DETAILS["cannot_update_speciality_or_seeded"],
#             )

#         return super(VisitCategorySerializer, self).update(
#             instance=instance, validated_data=validated_data
#         )


# class VisitTypeSerializer(StandardModelSerializer):
#     display_id = serializers.CharField(read_only=True)

#     class Meta:
#         model = VisitType
#         fields = "__all__"

#     def to_representation(self, instance):
#         representation = super(VisitTypeSerializer, self).to_representation(
#             instance=instance
#         )
#         category_serializer = VisitCategorySerializer(instance=instance.category)
#         representation["category"] = category_serializer.data
#         return representation

#     def update(self, instance, validated_data):
#         if validated_data.get("category") or "seeded" in validated_data:
#             raise serializers.ValidationError(
#                 code="cannot_update_category_or_seeded",
#                 detail=ERROR_DETAILS["cannot_update_category_or_seeded"],
#             )

#         return super(VisitTypeSerializer, self).update(
#             instance=instance, validated_data=validated_data
#         )


# class VisitTypeTemplateCompositionSerializer(StandardModelSerializer):
#     display_id = serializers.CharField(read_only=True)

#     class Meta:
#         model = VisitTypeTemplateComposition
#         fields = "__all__"


# class VisitTypeTemplateCompositionDisplaySerializer(
#     VisitTypeTemplateCompositionSerializer
# ):
#     visit_type = VisitTypeSerializer()


# class VisitTypeTemplateSerializer(StandardModelSerializer):
#     display_id = serializers.CharField(read_only=True)
#     composition = serializers.JSONField(
#         required=False, allow_null=True, write_only=True
#     )

#     class Meta:
#         model = VisitTypeTemplate
#         fields = "__all__"

#     def is_composition_required(self):
#         request_obj = self.context.get("request")
#         return (
#             request_obj is not None
#             and request_obj.query_params.get("composition_required")
#             in TRUE_QUERY_PARAMS
#         ) or (self.context.get("composition_required"))

#     def to_representation(self, instance):
#         representation = super(VisitTypeTemplateSerializer, self).to_representation(
#             instance=instance
#         )
#         representation["composition"] = None
#         if self.is_composition_required():
#             composition_serializer = VisitTypeTemplateCompositionDisplaySerializer(
#                 instance.visittypetemplatecomposition_set.all(), many=True
#             )
#             representation["composition"] = composition_serializer.data
#         return representation

#     @staticmethod
#     def append_template_id_in_composition(template_id, composition_data):
#         for composition in composition_data:
#             composition["template"] = template_id
#         return composition_data

#     @classmethod
#     def validate_only_one_default_in_composition(cls, composition_data):
#         default_count = 0
#         for composition in composition_data:
#             if composition.get("default"):
#                 default_count += 1
#             if default_count > 1:
#                 raise serializers.ValidationError(
#                     code="only_one_default_allowed",
#                     detail=ERROR_DETAILS["only_one_default_allowed"],
#                 )

#     def validate_and_create_template_composition(self, template_obj, composition_data):
#         if not composition_data:
#             return None

#         composition_data = self.append_template_id_in_composition(
#             template_id=str(template_obj.id), composition_data=composition_data
#         )
#         self.validate_only_one_default_in_composition(composition_data=composition_data)
#         composition_serializer = VisitTypeTemplateCompositionSerializer(
#             data=composition_data, many=True
#         )
#         composition_serializer.is_valid(raise_exception=True)
#         return composition_serializer.save()

#     def validate_and_update_template_composition(self, template_obj, composition_data):
#         if not composition_data:
#             return None

#         template_obj.visittypetemplatecomposition_set.all().delete()
#         return self.validate_and_create_template_composition(
#             template_obj=template_obj, composition_data=composition_data
#         )

#     def create(self, validated_data):
#         composition_data = validated_data.pop("composition", None)
#         template_obj = super().create(validated_data=validated_data)
#         self.validate_and_create_template_composition(
#             template_obj=template_obj, composition_data=composition_data
#         )
#         return template_obj

#     def update(self, instance, validated_data):
#         composition_data = validated_data.pop("composition", None)
#         template_obj = super().update(instance=instance, validated_data=validated_data)
#         if composition_data is not None:
#             self.validate_and_update_template_composition(
#                 template_obj=instance, composition_data=composition_data
#             )
#         return template_obj


# class StaffVisitTypeSerializer(StandardModelSerializer):
#     display_id = serializers.CharField(read_only=True)

#     class Meta:
#         model = StaffVisitType
#         fields = "__all__"

#     def create(self, validated_data):
#         if not self.context.get("upsert"):
#             return super().create(validated_data)

#         staff_visit_type, _ = StaffVisitType.objects.update_or_create(
#             staff_id=str(validated_data["staff"].id),
#             visit_type_id=str(validated_data["visit_type"].id),
#             defaults=validated_data,
#         )
#         return staff_visit_type


# class VisitTypeAssignmentRequestCompositionSerializer(StandardModelSerializer):
#     display_id = serializers.CharField(read_only=True)

#     class Meta:
#         model = VisitTypeAssignmentRequestComposition
#         fields = "__all__"


# class VisitTypeAssignmentRequestTargetSerializer(StandardModelSerializer):
#     display_id = serializers.CharField(read_only=True)

#     class Meta:
#         model = VisitTypeAssignmentRequestTarget
#         fields = "__all__"


# class VisitTypeAssignmentRequestSerializer(StandardModelSerializer):
#     display_id = serializers.CharField(read_only=True)
#     composition = serializers.JSONField(
#         required=False, allow_null=True, write_only=True
#     )
#     target = serializers.JSONField(required=False, allow_null=True, write_only=True)

#     class Meta:
#         model = VisitTypeAssignmentRequest
#         fields = "__all__"

#     @staticmethod
#     def append_assignment_request_id_in_target(assignment_request_id, target_data):
#         for target in target_data:
#             target["assignment_request"] = assignment_request_id
#         return target_data

#     def validate_and_create_request_target(self, assignment_request_obj, target_data):
#         if not target_data:
#             return None

#         target_data = self.append_assignment_request_id_in_target(
#             assignment_request_id=str(assignment_request_obj.id),
#             target_data=target_data,
#         )
#         target_serializer = VisitTypeAssignmentRequestTargetSerializer(
#             data=target_data, many=True
#         )
#         target_serializer.is_valid(raise_exception=True)
#         return target_serializer.save()

#     @staticmethod
#     def append_assignment_request_id_in_composition(
#         assignment_request_id, composition_data
#     ):
#         for composition in composition_data:
#             composition["assignment_request"] = assignment_request_id
#         return composition_data

#     @staticmethod
#     def validate_staff_exists_for_overridden_configs(composition_data):
#         for composition in composition_data:
#             if composition.get("overridden"):
#                 staff = composition.get("staff")
#                 if not staff:
#                     raise serializers.ValidationError(
#                         code="staff_required_for_overridden_config",
#                         detail=ERROR_DETAILS["staff_required_for_overridden_config"],
#                     )

#     def validate_and_create_request_composition(
#         self, assignment_request_obj, composition_data
#     ):
#         if not composition_data:
#             return None

#         self.validate_staff_exists_for_overridden_configs(
#             composition_data=composition_data
#         )
#         composition_data = self.append_assignment_request_id_in_composition(
#             assignment_request_id=str(assignment_request_obj.id),
#             composition_data=composition_data,
#         )
#         composition_serializer = VisitTypeAssignmentRequestCompositionSerializer(
#             data=composition_data, many=True
#         )
#         composition_serializer.is_valid(raise_exception=True)
#         return composition_serializer.save()

#     @staticmethod
#     def init_vt_assignment_process(assignment_request_obj):
#         assignment_request_manager = VisitTypeAssignmentRequestManager(
#             assignment_request_obj=assignment_request_obj
#         )
#         assignment_request_obj.process_id = (
#             assignment_request_manager.init_adhoc_vt_assignment_process()
#         )
#         assignment_request_obj.save()
#         return assignment_request_obj

#     @staticmethod
#     def validate_for_copy_from_source_staff(validated_data):
#         if validated_data.get("method") != FROM_SOURCE_STAFF:
#             return None

#         if not validated_data.get("source_staff") or not validated_data.get(
#             "source_speciality"
#         ):
#             raise serializers.ValidationError(
#                 code="source_staff_and_speciality_required",
#                 detail=ERROR_DETAILS["source_staff_and_speciality_required"],
#             )

#         source_staff_id = str(validated_data.get("source_staff").id)
#         targets = validated_data.get("target", [])
#         if targets:
#             for target in targets:
#                 if str(target.get("staff")) == source_staff_id:
#                     raise serializers.ValidationError(
#                         code="source_staff_and_target_staff_cannot_be_same",
#                         detail=ERROR_DETAILS[
#                             "source_staff_and_target_staff_cannot_be_same"
#                         ],
#                     )

#         return None

#     @staticmethod
#     def validate_for_copy_from_template(validated_data):
#         if validated_data.get("method") != FROM_SOURCE_TEMPLATE:
#             return None

#         if not validated_data.get("source_template"):
#             raise serializers.ValidationError(
#                 code="source_template_required",
#                 detail=ERROR_DETAILS["source_template_required"],
#             )

#         if validated_data.get("composition"):
#             VisitTypeTemplateSerializer.validate_only_one_default_in_composition(
#                 composition_data=validated_data.get("composition")
#             )

#         return None

#     @staticmethod
#     def validate_for_copy_from_source_composition(validated_data):
#         if validated_data.get("method") != FROM_SOURCE_COMPOSITION:
#             return None

#         if not validated_data.get("composition"):
#             raise serializers.ValidationError(
#                 code="composition_required",
#                 detail=ERROR_DETAILS["composition_required"],
#             )

#         if validated_data.get("composition"):
#             VisitTypeTemplateSerializer.validate_only_one_default_in_composition(
#                 composition_data=validated_data.get("composition")
#             )

#         return None

#     @staticmethod
#     def validate_targets(validated_data):
#         # TODO MUST validate the speciality of the targets must match with the speciality of the source staff or templ
#         if not validated_data.get("target"):
#             raise serializers.ValidationError(
#                 code="target_required", detail=ERROR_DETAILS["target_required"]
#             )

#         return None

#     @staticmethod
#     def validate_methods(validated_data):
#         if validated_data.get("method") not in ASSIGNMENT_REQUEST_METHODS:
#             raise serializers.ValidationError(
#                 code="invalid_assignment_request_method",
#                 detail=ERROR_DETAILS["invalid_assignment_request_method"],
#             )

#         return None

#     def run_initial_validations(self, validated_data):
#         self.validate_methods(validated_data=validated_data)
#         self.validate_for_copy_from_source_staff(validated_data=validated_data)
#         self.validate_for_copy_from_template(validated_data=validated_data)
#         self.validate_for_copy_from_source_composition(validated_data=validated_data)
#         self.validate_targets(validated_data=validated_data)

#     def create(self, validated_data):
#         self.run_initial_validations(validated_data=validated_data)
#         composition_data = validated_data.pop("composition", None)
#         target_data = validated_data.pop("target", None)
#         assignment_request_obj = super().create(validated_data=validated_data)
#         self.validate_and_create_request_target(
#             assignment_request_obj=assignment_request_obj,
#             target_data=target_data,
#         )
#         self.validate_and_create_request_composition(
#             assignment_request_obj=assignment_request_obj,
#             composition_data=composition_data,
#         )
#         return self.init_vt_assignment_process(
#             assignment_request_obj=assignment_request_obj
#         )
