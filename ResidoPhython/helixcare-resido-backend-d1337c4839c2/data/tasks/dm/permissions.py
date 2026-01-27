from dm.tasks.dm.base import BaseDataMigrationTask
from data.management.commands.populate_permissions import Command


class PermissionsMigrationTask(BaseDataMigrationTask):
    def __init__(self, **kwargs):
        super(PermissionsMigrationTask, self).__init__(**kwargs)
        self.version = 8

    def _run(self):
        Command().handle()
