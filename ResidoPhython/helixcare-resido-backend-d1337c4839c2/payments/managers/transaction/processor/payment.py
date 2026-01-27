from payments.managers.transaction.processor.base import BaseTransactionProcessor


class PaymentTransactionProcessor(BaseTransactionProcessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def process(self):
        pass
