from django.db import models, transaction
from django_celery_beat.models import PeriodicTask

from common.models import GenericModel, optional
from common.utils.logging import logger
from processflow.constants import ProcessType, ProcessStatus, ProcessTriggerType


class Process(GenericModel):
    periodic_task = models.ForeignKey(
        PeriodicTask, on_delete=models.CASCADE, **optional
    )
    request_id = models.UUIDField(unique=True)
    task_id = models.UUIDField(unique=True, **optional)
    object_id = models.UUIDField(**optional)
    object_name = models.CharField(max_length=512, **optional)
    process_type = models.CharField(choices=ProcessType.choices(), max_length=50)
    trigger_type = models.CharField(
        choices=ProcessTriggerType.choices(), max_length=100, **optional
    )
    status = models.CharField(
        choices=ProcessStatus.choices(),
        max_length=50,
        default=ProcessStatus.QUEUED.value,
        db_index=True,
    )
    raw_payload = models.JSONField(**optional)
    report = models.JSONField(**optional)
    error_code = models.IntegerField(**optional)
    error_body = models.JSONField(**optional)
    active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["object_id", "process_type", "status"]),
        ]

    def __str__(self):
        return f"{self.task_id} on {self.object_id} [ {self.process_type} ]"

    def set_task_id(self, task_id):
        self.task_id = task_id
        self.save()
        return self

    def update_status(self, new_status, error_body=None, error_code=None, report=None):
        if self.status == new_status:
            logger.info(
                f"Cannot update the status of the process with task_id {self.task_id}"
                f" current_status is {self.status} ; new_status is {new_status}"
            )
            return self

        old_status = self.status
        self.status = new_status
        self.error_body = error_body
        self.error_code = error_code
        self.report = report

        logger.info(
            f"Updating the status of the process with task_id {self.task_id} from {old_status} to {new_status} with "
            f"auto_commit as {transaction.get_autocommit()}"
        )
        self.save()
        logger.info(
            f"Updated the status of the process with task_id {self.task_id} from {old_status} to {new_status} ; "
            f"Additional data: error_code = {self.error_code}, error_body = {self.error_body}"
        )
        return self
