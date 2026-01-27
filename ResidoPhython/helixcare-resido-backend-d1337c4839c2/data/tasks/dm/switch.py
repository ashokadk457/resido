from common.managers.feature.switch import FeatureSwitchManager
from dm.tasks.dm.base import BaseDataMigrationTask


class FeatureSwitchMigrationTask(BaseDataMigrationTask):
    def __init__(self, **kwargs):
        super(FeatureSwitchMigrationTask, self).__init__(**kwargs)
        self.version = 1

    def _run(self):
        FeatureSwitchManager.seed_feature_switches()
