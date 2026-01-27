from dm.tasks.dm.base import BaseDataMigrationTask
from helixauth.managers.module import ModuleManager


class ModulesMigrationTask(BaseDataMigrationTask):
    def __init__(self, **kwargs):
        super(ModulesMigrationTask, self).__init__(**kwargs)
        self.version = 1

    def _run(self):
        ModuleManager.seed_modules()
