import csv

from django_tenants.utils import tenant_context
from hb_core.utils.logging import logger
from customer_backend.managers.model.module import ModuleManager
from subscriptions.constants import PLANS_FILE_PATH
from subscriptions.models.plan import Plan, PlanModuleComposition


class PlanManager:
    @classmethod
    def init(cls, **kwargs):
        plan_name = kwargs.get("plan_name")
        plan_obj = kwargs.get("plan_obj")
        if plan_obj is None and plan_name is not None:
            plan_obj = Plan.objects.filter(name=plan_name).first()
        if plan_obj is None:
            return None

        return cls(plan_obj=plan_obj, plan_name=plan_name)

    def __init__(self, **kwargs):
        self.plan_obj = kwargs.get("plan_obj")
        self.plan_name = kwargs.get("plan_name")

    def _get_plan_module_ids(self):
        module_ids = list(
            self.plan_obj.planmodulecomposition_set.filter(active=True).values_list(
                "module_id", flat=True
            )
        )
        return set([str(_id) for _id in module_ids])

    def _get_plan_module_ids_from_cache(self):
        module_ids = []
        all_plan_module_compositions = (
            PlanModuleComposition.objects.get_all_from_cache()
        )
        plan_id = str(self.plan_obj.id)
        for plan_module_composition_data in all_plan_module_compositions:
            plan_id_in_comp = str(plan_module_composition_data.get("plan_id"))
            is_active = plan_module_composition_data.get("active")
            if plan_id_in_comp == plan_id and is_active:
                module_ids.append(str(plan_module_composition_data.get("module_id")))

        return set([str(_id) for _id in module_ids])

    @classmethod
    def serialized_modules_for_plan(cls):
        # Import here to avoid circular dependency
        from customer_backend.managers.tenant import TenantManager

        with tenant_context(TenantManager.init(schema_name="public").tenant_obj):
            module_manager = ModuleManager()
            all_serialized_modules = module_manager.get_serialized_modules()
            return all_serialized_modules

    def get_module_composition(self):
        plan_module_ids = self._get_plan_module_ids_from_cache()
        all_serialized_modules = self.serialized_modules_for_plan()
        final_module_composition = []
        for module in all_serialized_modules:
            _id = module.get("id")
            module["subscribed"] = _id in plan_module_ids
            final_module_composition.append(module)

        return final_module_composition

    @classmethod
    def seed_plans(cls):
        logger.info("Loading plans...")
        plans = list(csv.DictReader(open(PLANS_FILE_PATH)))
        for plan in plans:
            Plan.objects.update_or_create(id=plan["id"], defaults=plan)
        logger.info("Loaded plans.")
