from common.managers.task import AsyncPeriodicTaskManager
from dm.tasks.dm.base import BaseDataMigrationTask


class AsyncPeriodicTasksDataMigration(BaseDataMigrationTask):
    def __init__(self, **kwargs):
        super(AsyncPeriodicTasksDataMigration, self).__init__(**kwargs)
        self.version = 2

    def _run(self):
        AsyncPeriodicTaskManager.seed_tenant_tasks()
