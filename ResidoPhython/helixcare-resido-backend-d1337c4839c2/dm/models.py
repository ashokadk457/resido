from django.db import models
from audit.models import GenericModel
from data.constants import DataMigrationStatus


class DataMigrationExecution(GenericModel):
    task = models.CharField(max_length=500)
    execution_version = models.IntegerField()
    status = models.CharField(
        choices=DataMigrationStatus.choices(),
        default=DataMigrationStatus.IN_PROGRESS,
        max_length=100,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["task", "execution_version"], name="unique_task_version"
            )
        ]
        indexes = [
            models.Index(fields=["task", "execution_version"]),
        ]

    def __str__(self):
        return f"{self.task} - v{self.execution_version}"
