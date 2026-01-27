import traceback

from common.utils.logging import logger
from residents.managers.patient import ResidentManager
from payments.managers.transaction.adjustment import TransactionAdjustmentManager
from payments.managers.transaction.processor.base import BaseTransactionProcessor
from payments.managers.transaction.writeoff import TransactionWriteOffManager
from payments.payment_constants import TransactionMethod, TransactionStatus


class RefundTransactionProcessor(BaseTransactionProcessor):
    def __init__(self, **kwargs):
        super(RefundTransactionProcessor, self).__init__(**kwargs)

    def process_cash_refund_txn(self):
        """
            self.transaction_obj is the refund transaction
            self.transaction_obj.parent is the actual payment that needs to be refunded
        :return:
        """
        refund_status, refund_response_data = True, None

        logger.info(
            f"refund_status and refund_response_data for refund_transaction {self.transaction_id}: "
            f"{refund_status}, {refund_response_data}"
        )

        self.transaction_manager.update_refund_status_and_amount_for_parent_transaction(
            refund_status=refund_status,
            refund_methodology=TransactionMethod.CASH.value,
        )
        self.transaction_obj = self.transaction_manager.update_txn_from_parent()

        return self.transaction_obj

    def process_writeoff_refund_txn(self):
        transaction_writeoff_manager = TransactionWriteOffManager(
            transaction_obj=self.transaction_obj,
            writeoff_obj=self.transaction_obj.write_off,
        )
        transaction_writeoff_manager.create_transaction_writeoff()
        self.transaction_obj = self.transaction_manager.update_txn_status(
            status=TransactionStatus.COMPLETED.value
        )
        return self.transaction_obj

    def process_adjustment_refund_txn(self):
        transaction_adjustment_manager = TransactionAdjustmentManager(
            transaction_obj=self.transaction_obj,
            adjustment_obj=self.transaction_obj.adjustment,
        )
        transaction_adjustment_manager.create_transaction_adjustment()
        self.transaction_obj = self.transaction_manager.update_txn_status(
            status=TransactionStatus.COMPLETED.value
        )
        return self.transaction_obj

    def process_wallet_refund_txn(self):
        # update the patient wallet
        patient_manager = ResidentManager(patient_obj=self.patient_obj)
        patient_manager.credit_wallet_balance(amount=self.amount)

        # mark the refund status as complete
        self.transaction_obj = self.transaction_manager.update_txn_status(
            status=TransactionStatus.COMPLETED.value
        )
        return self.transaction_obj

    def process_back_to_source_refund_txn(self):
        """
            self.transaction_obj is the refund transaction
            self.transaction_obj.parent is the actual payment that needs to be refunded
        :return:
        """
        (
            refund_status,
            refund_response_data_from_gateway,
            refund_methodology,
        ) = self.transaction_manager.easy_pay.refund_transaction(
            parent_id=str(self.parent_transaction.id),
            txn_id=self.parent_transaction.transaction_id,
            amount=self.transaction_manager.amount_value,
            payment_method=self.parent_transaction.payment_method,
        )

        logger.info(
            f"refund_status and refund_response_data_from_gateway for refund_transaction {self.transaction_id}: "
            f"{refund_status}, {refund_response_data_from_gateway}"
        )

        (
            self.parent_transaction,
            parent_updated,
        ) = self.transaction_manager.update_refund_status_and_amount_for_parent_transaction(
            refund_status=refund_status,
            refund_methodology=refund_methodology,
        )
        self.transaction_obj = self.transaction_manager.update_txn_from_parent(
            extra_data=refund_response_data_from_gateway
        )

        return self.transaction_obj

    def _process(self):
        if self.method == TransactionMethod.WRITE_OFF.value:
            return self.process_writeoff_refund_txn()

        if self.method == TransactionMethod.ADJUSTMENT.value:
            return self.process_adjustment_refund_txn()

        if self.method == TransactionMethod.WALLET.value:
            return self.process_wallet_refund_txn()

        if self.method == TransactionMethod.BACK_TO_SOURCE.value:
            return self.process_back_to_source_refund_txn()

        if self.method == TransactionMethod.CASH.value:
            return self.process_cash_refund_txn()

        return self.transaction_obj

    def process(self):
        # TODO MUST -- this should be marked as atomic
        try:
            return self._process()
        except Exception as e:
            logger.info(
                f"Exception occurred while processing transaction {self.transaction_id}: {str(e)}"
            )
            traceback.print_exc()
            return self.transaction_manager.update_txn_status(
                status=TransactionStatus.REFUND_FAILED.value,
                extra_data={"error": str(e)},
            )
