from dm.tasks.dm.base import BaseDataMigrationTask
from subscriptions.managers.pcomp import PlanCompositionManager


class PlanModuleCompositionDataMigrationTask(BaseDataMigrationTask):
    def __init__(self, **kwargs):
        super(PlanModuleCompositionDataMigrationTask, self).__init__(**kwargs)
        self.version = 1

    def _run(self):
        PlanCompositionManager.seed_plan_composition()
