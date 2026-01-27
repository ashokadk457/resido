from payments.managers.transaction.core import TransactionManager
from payments.managers.transaction.log import TransactionLogManager


class BaseTransactionProcessor:
    def __init__(self, **kwargs):
        self.transaction_manager = TransactionManager(**kwargs)
        self.transaction_obj = kwargs.get("transaction_obj")
        self.transaction_id = (
            str(self.transaction_obj.id)
            if self.transaction_obj is not None
            else kwargs.get("transaction_id")
        )
        self.amount = (
            self.transaction_obj.amount if self.transaction_obj is not None else None
        )
        self.patient_obj = kwargs.get("patient_obj")
        self.method = self.transaction_obj.method
        self.parent_transaction = self.transaction_manager.parent_transaction
        self.txn_log_manager = TransactionLogManager(
            transaction_obj=self.transaction_obj
        )

    def process(self):
        raise NotImplementedError
