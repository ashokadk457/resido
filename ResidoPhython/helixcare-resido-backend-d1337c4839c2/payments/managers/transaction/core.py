import json
from datetime import datetime

from common.constants import UTC_TIMEZONE
from payments.gateway.easypay.core import EasyPay
from payments.gateway.easypay.constants import (
    EASY_PAY_TRANSACTION_STATUS_TO_PAYMENTS_STATUS,
    EASYPAY_VERIFONE_EVENT_TO_TRANSACTION_STATUS_MAP,
    EasyPayRefundMethodology,
    EasyPayTxnStatus,
)
from common.utils.logging import logger, get_request_id
from payments.helix_payment_processor import HelixPaymentProcessor

from payments.payment_constants import (
    TransactionStatus,
    REFUNDED_TRANSACTION_STATUSES,
    TransactionType,
    TransactionEvent,
)


class TransactionManager:
    """
    AKA PaymentManager
    """

    def __init__(self, **kwargs):
        self.payment_obj = kwargs.get("payment_obj")
        self.transaction_obj = kwargs.get("transaction_obj") or self.payment_obj
        self.payment_id = (
            str(self.payment_obj.id)
            if self.payment_obj is not None
            else kwargs.get("payment_id")
        )
        self.transaction_id = self.payment_id or str(self.transaction_obj.id)
        self.bill_obj = self.payment_obj.bill if self.payment_obj is not None else None
        self.transaction_type = (
            self.payment_obj.transaction_type
            if self.payment_obj is not None
            else kwargs.get("transaction_type")
        )
        self.method = (
            self.payment_obj.payment_method
            if self.payment_obj is not None
            else kwargs.get("method")
        )
        self.amount = self.payment_obj.amount if self.payment_obj is not None else None
        self.amount_value = (
            float(self.amount.amount) if self.amount is not None else None
        )
        self.patient_obj = kwargs.get("patient_obj")
        self.parent_transaction = (
            self.payment_obj.parent
            if self.payment_obj is not None
            else kwargs.get("parent_transaction")
        )
        self.transaction_for_gateway = (
            self.transaction_obj
            if self.transaction_obj.transaction_type == TransactionType.PAYMENT.value
            else self.parent_transaction
        )
        self.easy_pay = kwargs.get("easy_pay") or EasyPay(
            bill=self.bill_obj, transaction_obj=self.transaction_for_gateway
        )

    def update_txn_from_parent(self, extra_data=None):
        self.payment_obj.extra_data = extra_data
        self.payment_obj.status = TransactionStatus.FAILED.value
        if self.parent_transaction.status in REFUNDED_TRANSACTION_STATUSES:
            self.payment_obj.status = TransactionStatus.COMPLETED.value

        logger.info(f"Updating refund transaction status as {self.payment_obj.status}")
        self.payment_obj.save()
        return self.payment_obj

    def update_txn_status(self, status, extra_data=None):
        self.payment_obj.status = status
        self.payment_obj.extra_data = extra_data
        self.payment_obj.save()
        return self.payment_obj

    def cancel(self, txn_id):
        cancel_response = self.easy_pay.cancel_payment(
            txn_id=txn_id, payment_method=self.method
        )
        if cancel_response.get("success"):
            self.payment_obj = self.update_txn_status(
                status=TransactionStatus.CANCELLED.value,
                extra_data=cancel_response.get("response_data"),
            )

        return cancel_response

    def get_payment_status_from_gateway(self, txn_id):
        if self.payment_obj is None:
            return None, "no_payment_obj"

        return self.easy_pay.get_transaction_status(
            txn_id=txn_id,
            payment_id=self.payment_id,
            transaction_method=self.method,
        )

    def verify_payment_status(self, payment_status_from_client, txn_id):
        (
            payment_status_from_server,
            error_message,
        ) = self.get_payment_status_from_gateway(txn_id=txn_id)
        if error_message:
            return False, error_message, payment_status_from_server

        payment_status_as_per_client_event = (
            EASYPAY_VERIFONE_EVENT_TO_TRANSACTION_STATUS_MAP.get(
                payment_status_from_client
            )
        )
        matching = payment_status_from_server == payment_status_as_per_client_event
        return matching, None, payment_status_from_server

    def update_transaction_status(
        self, payment_status_from_client, client_payment_response, txn_id
    ):
        (
            payment_status_matching,
            error_message,
            payment_status_from_server,
        ) = self.verify_payment_status(
            payment_status_from_client=payment_status_from_client, txn_id=txn_id
        )
        if error_message:
            return self.payment_obj, False, error_message

        payment_status_as_per_client_event = (
            EASYPAY_VERIFONE_EVENT_TO_TRANSACTION_STATUS_MAP.get(
                payment_status_from_client
            )
        )

        if not payment_status_matching:
            logger.info(
                f"Payment status not matching - {payment_status_as_per_client_event} "
                f"from client vs {payment_status_from_server} from server"
            )

        payment_status = EASY_PAY_TRANSACTION_STATUS_TO_PAYMENTS_STATUS.get(
            payment_status_from_server
        )
        notes = json.dumps(client_payment_response)
        self.payment_obj = HelixPaymentProcessor.update_transaction_post_processing(
            payment=self.payment_obj,
            status=payment_status,
            notes=notes,
            transaction_id=txn_id,
        )

        return self.payment_obj, True, "payment_status_matched"

    def update_refund_status_and_amount_for_parent_transaction(
        self, refund_status, refund_methodology
    ):
        if not refund_status:
            return self.parent_transaction, False

        refund_amount = self.amount_value
        current_refund_money_obj = self.parent_transaction.refund_amount
        current_refund_amount_val = float(current_refund_money_obj.amount)
        current_refund_amount_val += refund_amount

        self.parent_transaction.status = TransactionStatus.PARTIALLY_REFUNDED.value
        if float(self.parent_transaction.amount.amount) == float(
            current_refund_amount_val
        ):
            self.parent_transaction.status = TransactionStatus.REFUNDED.value

        self.parent_transaction.refund_amount = current_refund_amount_val
        if refund_methodology == EasyPayRefundMethodology.VOID.value:
            # In case the methodology was VOID, EasyPay Voids the whole transaction
            self.parent_transaction.status = TransactionStatus.REFUNDED.value
            self.parent_transaction.refund_amount = float(
                self.parent_transaction.amount.amount
            )

        logger.info(
            f"Updating status for parent transaction {str(self.parent_transaction.id)} "
            f"as {self.parent_transaction.status}"
        )
        self.parent_transaction.save()
        return self.parent_transaction, True

    def update_transaction_from_gateway_recon(self, gateway_recon_data):
        self.transaction_obj.log(
            event=TransactionEvent.RECONCILE_GATEWAY.value, data=gateway_recon_data
        )
        gateway_status = gateway_recon_data.get("TxStatus")
        if not gateway_status:
            return self.transaction_obj, False

        self.transaction_obj.gateway_status = gateway_status
        if gateway_status == EasyPayTxnStatus.FAILED.value:
            self.transaction_obj.status = TransactionStatus.FAILED.value

        self.transaction_obj.gateway_status_last_updated_on = datetime.now(
            tz=UTC_TIMEZONE
        )
        self.transaction_obj.gateway_recon_last_request_id = get_request_id()
        self.transaction_obj.save()
        return self.transaction_obj, True
