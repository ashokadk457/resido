from dm.tasks.dm.base import BaseDataMigrationTask
from lookup.managers.lookup import LookupManager


class LookupsMigrationTask(BaseDataMigrationTask):
    def __init__(self, **kwargs):
        super(LookupsMigrationTask, self).__init__(**kwargs)
        self.version = 26

    def _run(self):
        LookupManager().populate_lookup()
