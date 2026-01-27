from customer_backend.managers.tenant import TenantManager
from common.utils.logging import logger
from payments.managers.transaction.processor.refund import RefundTransactionProcessor
from payments.models import BillRefundRequest
from payments.payment_constants import RefundRequestStatus, TransactionStatus
from processflow.constants import ProcessType
from processflow.managers.process.core import ProcessManager


class BillRefundRequestManager:
    def __init__(self, **kwargs):
        self.tenant_id = (
            kwargs.get("tenant_id")
            if kwargs.get("tenant_id")
            else str(TenantManager().tenant_id)
        )
        self.bill_refund_obj = kwargs.get("bill_refund_obj")
        self.bill_refund_id = (
            str(self.bill_refund_obj.id)
            if self.bill_refund_obj is not None
            else kwargs.get("bill_refund_id")
        )
        self.bill_obj = kwargs.get("bill_obj")
        self.bill_id = (
            str(self.bill_obj.id)
            if self.bill_obj is not None
            else kwargs.get("bill_id")
        )
        self.refund_transactions_qs = None
        self.patient_obj = None

    def get_refund_and_related_objects(self):
        if self.bill_refund_id is not None and self.bill_refund_obj is None:
            self.bill_refund_obj = BillRefundRequest.objects.filter(
                id=self.bill_refund_id
            ).first()
        if self.bill_refund_obj is not None:
            self.bill_obj = self.bill_refund_obj.bill
            self.refund_transactions_qs = self.bill_refund_obj.payment_set.all()
            self.patient_obj = self.bill_obj.patient

        return self.bill_refund_obj, self.bill_obj, self.patient_obj

    def _init_async_process(self, process_type):
        pm = ProcessManager(process_type=process_type)
        kwargs = {
            "tenant_id": self.tenant_id,
            "bill_id": self.bill_id,
            "bill_refund_id": str(self.bill_refund_id),
        }
        object_name = self.bill_refund_obj.display_id
        return pm.init_and_enqueue_adhoc_aysnc_process(
            object_id=self.bill_refund_id, object_name=object_name, **kwargs
        )

    def init_adhoc_refund_process(self):
        return self._init_async_process(
            process_type=ProcessType.PROCESS_BILL_REFUND_REQUEST.value
        )

    def _update_status_and_total_refund_processed(
        self, status, total_refund_processed=None
    ):
        self.bill_refund_obj.status = status
        if total_refund_processed is not None:
            self.bill_refund_obj.total_refund_processed = total_refund_processed

        logger.info(
            f"Updating refund request details: {self.bill_refund_obj.status} "
            f"and {self.bill_refund_obj.total_refund_processed}"
        )
        self.bill_refund_obj.save()
        return self.bill_refund_obj

    def _update_status_as_per_refund_report(
        self, total_count, success_count, total_refund_processed
    ):
        if success_count == 0:
            return self._update_status_and_total_refund_processed(
                status=RefundRequestStatus.FAILED.value,
                total_refund_processed=total_refund_processed,
            )

        if success_count == total_count:
            return self._update_status_and_total_refund_processed(
                status=RefundRequestStatus.COMPLETED.value,
                total_refund_processed=total_refund_processed,
            )

        return self._update_status_and_total_refund_processed(
            status=RefundRequestStatus.PARTIAL_SUCCESS.value,
            total_refund_processed=total_refund_processed,
        )

    def refund(self):
        if self.refund_transactions_qs is None:
            logger.info("Refund transactions qs is None")
            return False, self.bill_refund_obj

        refund_transactions = list(self.refund_transactions_qs)
        success_count, total_count, total_refund_processed = (
            0,
            len(refund_transactions),
            0,
        )
        refund_report = {
            "success_count": success_count,
            "total_count": total_count,
            "total_refund_processed": total_refund_processed,
        }
        logger.info(f"Starting refund process: {refund_report}")
        for i, refund_transaction in enumerate(refund_transactions):
            refund_txn_processor = RefundTransactionProcessor(
                payment_obj=refund_transaction,
                transaction_obj=refund_transaction,
                patient_obj=self.patient_obj,
            )
            refund_txn = refund_txn_processor.process()
            if refund_txn is None:
                logger.info("Refund txn is None post processing")
                continue
            logger.info(
                f"Completed refund transaction processing for refund transaction {str(refund_txn.id)} "
                f"with status {str(refund_txn.status)} ; {i+1} out of {total_count} done"
            )
            if refund_txn.status == TransactionStatus.COMPLETED.value:
                success_count += 1
                total_refund_processed += refund_txn.amount.amount

        refund_report = {
            "success_count": success_count,
            "total_count": total_count,
            "total_refund_processed": total_refund_processed,
        }
        logger.info(f"Refund Request Processing report: {refund_report}")
        self.bill_refund_obj = self._update_status_as_per_refund_report(
            total_count=total_count,
            success_count=success_count,
            total_refund_processed=total_refund_processed,
        )
        return True, self.bill_refund_obj
