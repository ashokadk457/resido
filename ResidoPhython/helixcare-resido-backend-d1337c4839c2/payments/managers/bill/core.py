from payments.managers.transaction.core import TransactionManager
from payments.payment_constants import (
    RefundRequestStatus,
    RefundType,
    TransactionStatus,
)
from common.utils.logging import logger


class BillManager:
    def __init__(self, **kwargs):
        self.bill_obj = kwargs.get("bill_obj")
        self.bill_id = kwargs.get("bill_id")

    def cancel_last_open_transaction(self):
        last_transaction = self.bill_obj.payments.filter(
            transaction_id__isnull=False
        ).latest("-created_on")

        if last_transaction is None:
            return {
                "status": False,
                "message": f"No open transaction found for bill_id: {self.bill_id}",
                "error": "no_open_transaction",
                "response_data": None,
            }

        txn_manager = TransactionManager(
            payment_obj=last_transaction, bill_obj=self.bill_obj
        )
        cancel_response = txn_manager.cancel(txn_id=last_transaction.transaction_id)
        if cancel_response.get("success"):
            self.bill_obj = self.update_bill_status_on_txn_recon()

        return cancel_response

    def update_bill_status_on_txn_recon(self):
        logger.info("Updating Bill status on txn_recon")
        already_paid_amount = self.bill_obj.already_paid_amount_val
        to_be_paid_amount = float(self.bill_obj.patient_amount.amount)

        if already_paid_amount is None or not already_paid_amount:
            self.bill_obj.status = TransactionStatus.PENDING.value
            self.bill_obj.payment_method = None
            self.bill_obj.save()
            return self.bill_obj

        if already_paid_amount < to_be_paid_amount:
            self.bill_obj.status = TransactionStatus.PARTIALLY_COMPLETED.value
            self.bill_obj.save()
            return self.bill_obj

        return self.bill_obj

    def _update_bill_status_on_total_refundable_amount(self):
        if float(self.bill_obj.total_refundable_amount) in [0, 0.0, 0.00]:
            logger.info(
                f"Bill refundable amount reduced to 0 for the bill {self.bill_id}"
            )
            self.bill_obj.status = TransactionStatus.REFUNDED.value
            self.bill_obj.save()

        return self.bill_obj

    def update_bill_upon_refund(self, bill_refund_obj):
        if bill_refund_obj.status == RefundRequestStatus.PENDING.value:
            self.bill_obj.status = (
                TransactionStatus.PARTIAL_REFUND_INITIATED.value
                if bill_refund_obj.refund_type == RefundType.PARTIAL_REFUND.value
                else TransactionStatus.REFUND_INITIATED.value
            )

        if bill_refund_obj.status == RefundRequestStatus.FAILED.value:
            self.bill_obj.status = (
                TransactionStatus.PARTIAL_REFUND_FAILED.value
                if self.bill_obj.status
                == TransactionStatus.PARTIAL_REFUND_INITIATED.value
                else TransactionStatus.REFUND_FAILED.value
            )

        if bill_refund_obj.status == RefundRequestStatus.COMPLETED.value:
            self.bill_obj.status = (
                TransactionStatus.PARTIALLY_REFUNDED.value
                if self.bill_obj.status
                == TransactionStatus.PARTIAL_REFUND_INITIATED.value
                else TransactionStatus.REFUNDED.value
            )

        if bill_refund_obj.status == RefundRequestStatus.PARTIAL_SUCCESS.value:
            self.bill_obj.status = TransactionStatus.PARTIALLY_REFUNDED.value

        self.bill_obj.save()
        return self._update_bill_status_on_total_refundable_amount()
