import traceback
from common.utils.logging import logger
from data.constants import DataMigrationStatus
from dm.models import DataMigrationExecution


class DataMigrationManager:
    def __init__(self, **kwargs):
        self.dm_exec_obj = kwargs.get("dm_exec_obj")
        self.task_class = kwargs.get("task_class")
        self.task_class_name = self.task_class.__name__ if self.task_class else None

    def _get_existing_dm_exec_obj(self, execution_version):
        return DataMigrationExecution.objects.filter(
            task=self.task_class_name, execution_version=execution_version
        ).first()

    def init_dm(self, execution_version):
        existing_dm_exec_obj = self._get_existing_dm_exec_obj(
            execution_version=execution_version
        )
        self.dm_exec_obj = existing_dm_exec_obj
        if existing_dm_exec_obj is None:
            self.dm_exec_obj = DataMigrationExecution.objects.create(
                task=self.task_class_name, execution_version=execution_version
            )
            return self.dm_exec_obj, "new_obj"

        if existing_dm_exec_obj.status == DataMigrationStatus.COMPLETED.value:
            return None, "already_completed"

        if existing_dm_exec_obj.status == DataMigrationStatus.FAILED.value:
            return self.dm_exec_obj, DataMigrationStatus.FAILED.value

        return self.dm_exec_obj, "existing_obj"

    def _update_dm_status(self, dm_status):
        self.dm_exec_obj.status = dm_status
        self.dm_exec_obj.save()
        return self.dm_exec_obj

    def mark_dm_as_failed(self):
        return self._update_dm_status(dm_status=DataMigrationStatus.FAILED.value)

    def mark_dm_as_completed(self):
        return self._update_dm_status(dm_status=DataMigrationStatus.COMPLETED.value)

    def run(self):
        if not self.task_class:
            logger.info("No Data Migration task class specified")
            return

        task_obj = self.task_class()
        self.dm_exec_obj, message = self.init_dm(execution_version=task_obj.version)

        if self.dm_exec_obj is None and message:
            if message != "already_completed":
                logger.info(
                    f"Cannot execute task {self.task_class_name} v{task_obj.version}. Reason: {message}"
                )
            return

        logger.info(f"Running {self.dm_exec_obj.__str__()}")
        try:
            status, error_message = task_obj.run()
        except Exception as e:
            logger.info(
                f"Exception occurred while running {self.dm_exec_obj.__str__()}: {str(e)}"
            )
            traceback.print_exc()
            return self.mark_dm_as_failed()

        if status is False:
            logger.info(
                f"Data Migration task {self.dm_exec_obj.__str__()} failed: {error_message}"
            )
            return self.mark_dm_as_failed()

        return self.mark_dm_as_completed()
