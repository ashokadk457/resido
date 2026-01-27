from dm.managers.dm.core import DataMigrationManager
from dm.tasks.dm.registry import DataMigrationTask


class DataMigrationRunner:
    @classmethod
    def run(cls):
        all_tasks = DataMigrationTask.values()

        for task_class in all_tasks:
            dm_manager = DataMigrationManager(task_class=task_class)
            dm_manager.run()
