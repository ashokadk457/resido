from payments.managers.transaction.processor.payment import PaymentTransactionProcessor
from payments.managers.transaction.processor.refund import RefundTransactionProcessor
from payments.payment_constants import TransactionType


class TransactionProcessorFactory:
    TRANSACTION_TYPE_TO_PROCESSOR_FACTORY = {
        TransactionType.PAYMENT.value: PaymentTransactionProcessor,
        TransactionType.REFUND.value: RefundTransactionProcessor,
    }

    def __init__(self, transaction_type=None):
        self.transaction_type = transaction_type

    def get_processor(self, transaction_type=None):
        transaction_type = self.transaction_type or transaction_type
        return self.TRANSACTION_TYPE_TO_PROCESSOR_FACTORY.get(transaction_type)
