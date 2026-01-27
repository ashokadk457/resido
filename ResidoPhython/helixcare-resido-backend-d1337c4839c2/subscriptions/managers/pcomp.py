import csv
from django.contrib import admin
from hb_core.utils.logging import logger
from customer_backend.models.rla import Module
from subscriptions.constants import PLANS_COMPOSITIONS_FILE_PATH
from subscriptions.models.plan import Plan, PlanModuleComposition


class PlanCompositionManager:
    @classmethod
    def modify_plan_mod_composition(cls):
        """
        Modify plan module compositions for RESIDO-specific requirements

        This method can be used to:
        - Remove incompatible module combinations
        - Enforce module dependencies
        - Apply business rules for plan compositions

        Currently no modifications are needed for RESIDO plans.
        """
        # No modifications required at this time
        pass

    @classmethod
    def seed_plan_composition(cls, plan_obj=None, plan_module_compositions=None):
        logger.info("Loading plans compositions...")
        if not plan_module_compositions:
            plan_module_compositions = list(
                csv.DictReader(open(PLANS_COMPOSITIONS_FILE_PATH))
            )
        plans, modules = {}, {}
        if plan_obj:
            plans[plan_obj.code] = plan_obj
        for plan_composition in plan_module_compositions:
            plan_name = plan_composition["plan"]
            plan_obj = plans.get(plan_name)
            if plan_obj is None:
                plan_obj = Plan.objects.get(name=plan_name)
                plans[plan_name] = plan_obj

            module_name = plan_composition["module"]
            module_obj = modules.get(module_name)
            try:
                if module_obj is None:
                    module_obj = Module.objects.get(name=module_name)
                    modules[module_name] = module_obj
            except Exception as e:
                logger.error(
                    f"No Module found with name {module_name}, skipping it to seed. Exception: {e}"
                )
                continue

            _id = plan_composition.get("id")
            _defaults = {"id": _id, "plan": plan_obj, "module": module_obj}
            PlanModuleComposition.objects.update_or_create(id=_id, defaults=_defaults)

        logger.info("Loaded plan compositions")

    @classmethod
    @admin.action(description="Unsubscribe from the selected modules")
    def unsubscribe(cls, modeladmin, request, queryset):
        queryset.update(active=False)

    @classmethod
    @admin.action(description="Subscribe to the selected modules")
    def subscribe(cls, modeladmin, request, queryset):
        queryset.update(active=True)
