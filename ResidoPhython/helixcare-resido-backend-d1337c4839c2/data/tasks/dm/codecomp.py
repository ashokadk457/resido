from dm.tasks.dm.base import BaseDataMigrationTask
from payments.managers.bill.cancellation.code.composition import (
    BillCancellationCodeCompositionManager,
)


class BillCancellationCodeCompositionMigrationTask(BaseDataMigrationTask):
    def __init__(self, **kwargs):
        super(BillCancellationCodeCompositionMigrationTask, self).__init__(**kwargs)
        self.version = 2

    def _run(self):
        BillCancellationCodeCompositionManager.seed_cancellation_code_composition()
