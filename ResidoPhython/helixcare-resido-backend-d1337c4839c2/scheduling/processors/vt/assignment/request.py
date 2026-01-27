import traceback

from celery import shared_task
from django.db import transaction
from django_tenants.utils import tenant_context

from customer_backend.managers.tenant import TenantManager
from common.utils.logging import logger

from processflow.managers.process.processor.base import BaseAsyncTaskProcessor
from scheduling.constants import (
    FROM_SOURCE_TEMPLATE,
    FROM_SOURCE_STAFF,
    FROM_SOURCE_COMPOSITION,
)
from scheduling.managers.vt.assignment.request import VisitTypeAssignmentRequestManager
from scheduling.models_v2 import (
    VisitTypeAssignmentRequest,
    VisitTypeTemplateComposition,
    VisitTypeAssignmentRequestTarget,
    StaffVisitType,
    VisitTypeAssignmentRequestComposition,
)
from scheduling.processors.vt.staff import StaffVisitTypeManager
from scheduling.serializers_v2 import (
    VisitTypeTemplateCompositionSerializer,
    StaffVisitTypeSerializer,
    VisitTypeAssignmentRequestCompositionSerializer,
)


class VisitTypeAssignmentRequestProcessor(BaseAsyncTaskProcessor):
    def __init__(self, process_id, request_id, process_type, **kwargs):
        super(VisitTypeAssignmentRequestProcessor, self).__init__(
            process_id=process_id,
            request_id=request_id,
            process_type=process_type,
            **kwargs,
        )
        self.assignment_request_id = kwargs.get("assignment_request_id")
        self.assignment_request_obj = kwargs.get("assignment_request_obj")
        self.method = kwargs.get("method")
        self.target_staff_objs = kwargs.get("target_staff_objs")

    def get_overridden_vt_configs_from_request_composition(self):
        vt_compositions_qs = VisitTypeAssignmentRequestComposition.objects.filter(
            assignment_request_id=self.assignment_request_id, overridden=True
        )
        if vt_compositions_qs is None:
            return None

        overridden_vt_configs = []
        vt_compositions_data = VisitTypeAssignmentRequestCompositionSerializer(
            vt_compositions_qs, many=True
        ).data
        for vt_config in vt_compositions_data:
            overridden_vt_config = {
                "assignment_request": self.assignment_request_id,
                "staff": vt_config["staff"],
                "visit_type": vt_config["visit_type"],
                "color_code": vt_config["color_code"],
                "duration": vt_config["duration"],
                "duration_unit": vt_config["duration_unit"],
                "frequency": vt_config["frequency"],
                "default": vt_config["default"],
            }
            overridden_vt_configs.append(overridden_vt_config)

        return overridden_vt_configs

    @classmethod
    def upsert_staff_visit_types(cls, all_vt_configs):
        if not all_vt_configs:
            return []

        staff_vt_objs = []
        for vt_config in all_vt_configs:
            vt_config["staff_id"] = str(vt_config.pop("staff"))
            vt_config["visit_type_id"] = str(vt_config.pop("visit_type"))
            vt_config["assignment_request_id"] = str(
                vt_config.pop("assignment_request")
            )

            manager = StaffVisitTypeManager()
            staff_vt_objs.append(manager.upsert(data=vt_config))

        return staff_vt_objs

    def get_all_vt_configs(self, vt_compositions_data):
        all_vt_configs, all_visit_type_ids, all_staff_ids = [], [], []
        for target_staff_obj in self.target_staff_objs:
            for existing_vt_config in vt_compositions_data:
                vt_config = {
                    "assignment_request": self.assignment_request_id,
                    "staff": str(target_staff_obj.staff.id),
                    "visit_type": existing_vt_config["visit_type"],
                    "color_code": existing_vt_config["color_code"],
                    "duration": existing_vt_config["duration"],
                    "duration_unit": existing_vt_config["duration_unit"],
                    "frequency": existing_vt_config["frequency"],
                    "default": existing_vt_config["default"],
                }
                all_vt_configs.append(vt_config)
                all_visit_type_ids.append(existing_vt_config["visit_type"])
                all_staff_ids.append(str(target_staff_obj.staff.id))

        return all_vt_configs, all_visit_type_ids, all_staff_ids

    def copy_from_source_template(self):
        source_template_obj = self.assignment_request_obj.source_template
        source_template_id = str(source_template_obj.id)
        template_composition_qs = VisitTypeTemplateComposition.objects.filter(
            template_id=source_template_id
        )
        template_compositions_data = VisitTypeTemplateCompositionSerializer(
            template_composition_qs, many=True
        ).data

        all_vt_configs, all_visit_type_ids, all_staff_ids = self.get_all_vt_configs(
            vt_compositions_data=template_compositions_data
        )

        staff_vt_configs = self.upsert_staff_visit_types(all_vt_configs=all_vt_configs)
        overridden_vt_configs = (
            self.get_overridden_vt_configs_from_request_composition()
        )
        if overridden_vt_configs:
            staff_vt_configs = self.upsert_staff_visit_types(
                all_vt_configs=overridden_vt_configs
            )

        return staff_vt_configs

    def copy_from_source_staff(self):
        source_staff_obj = self.assignment_request_obj.source_staff
        source_staff_id = str(source_staff_obj.id)
        source_speciality_obj = self.assignment_request_obj.source_speciality
        source_speciality_id = str(source_speciality_obj.id)

        vt_compositions_qs = StaffVisitType.objects.filter(
            staff_id=source_staff_id,
            visit_type__category__speciality_id=source_speciality_id,
        )
        source_vt_configs_data = StaffVisitTypeSerializer(
            vt_compositions_qs, many=True
        ).data

        all_vt_configs, all_visit_type_ids, all_staff_ids = self.get_all_vt_configs(
            vt_compositions_data=source_vt_configs_data
        )

        return self.upsert_staff_visit_types(all_vt_configs=all_vt_configs)

    def copy_from_source_composition(self):
        vt_compositions_qs = VisitTypeAssignmentRequestComposition.objects.filter(
            assignment_request_id=self.assignment_request_id, overridden=False
        )
        source_vt_configs_data = VisitTypeAssignmentRequestCompositionSerializer(
            vt_compositions_qs, many=True
        ).data

        all_vt_configs, all_visit_type_ids, all_staff_ids = self.get_all_vt_configs(
            vt_compositions_data=source_vt_configs_data
        )

        staff_vt_configs = self.upsert_staff_visit_types(all_vt_configs=all_vt_configs)
        overridden_vt_configs = (
            self.get_overridden_vt_configs_from_request_composition()
        )
        if overridden_vt_configs:
            staff_vt_configs = self.upsert_staff_visit_types(
                all_vt_configs=overridden_vt_configs
            )

        return staff_vt_configs

    def _process_request(self):
        if self.method == FROM_SOURCE_TEMPLATE:
            return self.copy_from_source_template()
        if self.method == FROM_SOURCE_STAFF:
            return self.copy_from_source_staff()
        if self.method == FROM_SOURCE_COMPOSITION:
            return self.copy_from_source_composition()
        return None

    def process_request(self):
        transaction.set_autocommit(False)
        try:
            self._process_request()
            transaction.commit()
            return True, None, None
        except Exception as e:
            logger.info(
                f"Exception occurred while processing assignment request: {str(e)}"
            )
            traceback.print_exc()
            transaction.rollback()
            transaction.set_autocommit(True)
            return False, e, 400

    @staticmethod
    @shared_task
    def process(**kwargs):
        kwargs[
            "task_id"
        ] = VisitTypeAssignmentRequestProcessor.process.request.id.__str__()
        with tenant_context(TenantManager.init(**kwargs).tenant_obj):
            VisitTypeAssignmentRequestProcessor._process(**kwargs)

    @classmethod
    def _run(cls, **kwargs):
        status, exception, error_body, error_code = True, None, None, None
        assignment_request_id = kwargs.get("assignment_request_id")
        assignment_request_obj = VisitTypeAssignmentRequest.objects.filter(
            id=assignment_request_id
        ).first()
        target_staff_objs = VisitTypeAssignmentRequestTarget.objects.filter(
            assignment_request_id=assignment_request_id
        )
        kwargs["assignment_request_id"] = assignment_request_id
        kwargs["assignment_request_obj"] = assignment_request_obj
        kwargs["target_staff_objs"] = target_staff_objs
        kwargs["method"] = assignment_request_obj.method
        request_manager = VisitTypeAssignmentRequestManager(**kwargs)
        request_processor = cls(**kwargs)
        request_manager.update_request_status_from_processing_status(
            processing_status=None
        )
        status, exception, error_code = request_processor.process_request()
        request_manager.update_request_status_from_processing_status(
            processing_status=status
        )

        if exception is not None:
            error_body = cls._process_exception(exception=exception)

        return status, error_body, error_code
