from common.utils.logging import get_request_id
from payments.models_v2 import TransactionLog


class TransactionLogManager:
    def __init__(self, **kwargs):
        self.transaction_obj = kwargs.get("transaction_obj")
        self.transaction_id = (
            str(self.transaction_obj.id)
            if self.transaction_obj is not None
            else kwargs.get("transaction_id")
        )
        self.log_obj = kwargs.get("log_obj")

    def log(self, event, source, data, call_log=None):
        self.log_obj = TransactionLog.objects.create(
            request_id=get_request_id(),
            transaction=self.transaction_obj,
            source=source,
            event=event,
            data=data,
            call_log=call_log,
        )
        return self.log_obj
