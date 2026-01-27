from dm.tasks.dm.base import BaseDataMigrationTask
from common.managers.seed_countries_states import CountryStateMigrationManager


class CountryStateMigrationTask(BaseDataMigrationTask):
    def __init__(self, **kwargs):
        super(CountryStateMigrationTask, self).__init__(**kwargs)
        self.version = 2

    def _run(self):
        CountryStateMigrationManager.seed_countries_and_states()
