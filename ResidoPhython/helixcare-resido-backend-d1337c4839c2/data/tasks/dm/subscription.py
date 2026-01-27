from dm.tasks.dm.base import BaseDataMigrationTask
from subscriptions.managers.plan import PlanManager
from subscriptions.managers.product_setting.core import ProductSettingManager


class PlansDataMigrationTask(BaseDataMigrationTask):
    """DM task to seed subscription plans and product settings"""

    def __init__(self, **kwargs):
        super(PlansDataMigrationTask, self).__init__(**kwargs)
        self.version = 1

    def _run(self):
        PlanManager.seed_plans()
        ProductSettingManager.seed_all_possible_product_settings()


# Backward compatibility alias
SubscriptionPlansMigrationTask = PlansDataMigrationTask
