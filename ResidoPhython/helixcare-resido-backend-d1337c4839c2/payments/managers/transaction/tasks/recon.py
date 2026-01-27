from datetime import datetime, timedelta

from django.db.models import Q

from common.constants import UTC_TIMEZONE
from common.managers.task import AsyncPeriodicTaskManager
from common.utils.logging import logger
from payments.gateway.easypay.constants import (
    EasyPayReconcileTxnQueryType,
)
from payments.gateway.easypay.core import EasyPay
from payments.managers.bill.core import BillManager
from payments.managers.transaction.core import TransactionManager
from payments.models import Payment
from payments.payment_constants import (
    TransactionStatus,
    TransactionMethod,
    CARD_BASED_TRANSACTION_METHODS,
)


class TransactionsReconciliationTask(AsyncPeriodicTaskManager):
    def __init__(self, **kwargs):
        super(TransactionsReconciliationTask, self).__init__(**kwargs)
        self.easypay = EasyPay()
        self.today_date_obj = datetime.now(tz=UTC_TIMEZONE).date()
        self.yesterday_date_obj = self.today_date_obj - timedelta(days=1)
        self.day_before_yday_date_obj = self.yesterday_date_obj - timedelta(days=1)
        self.day_before_yday_date_str = self.day_before_yday_date_obj.isoformat()
        self.today_date_str = self.today_date_obj.isoformat()
        self.yesterday_date_str = self.yesterday_date_obj.isoformat()
        self.report = {
            "start_date": self.day_before_yday_date_str,
            "end_date": self.yesterday_date_str,
            "total_hb_transactions": 0,
            EasyPayReconcileTxnQueryType.CARD.value: {},
            EasyPayReconcileTxnQueryType.ACH.value: {},
        }

    def transactions_exist_in_interval(self, start_date=None, end_date=None):
        if start_date is None:
            start_date = self.day_before_yday_date_str
        if end_date is None:
            end_date = self.yesterday_date_str

        transactions = Payment.objects.filter(
            created_on__date__range=(start_date, end_date)
        )
        total_hb_transactions = len(transactions)
        self.report["total_hb_transactions"] = total_hb_transactions

        return bool(total_hb_transactions)

    def _get_reconciled_transactions_from_easypay(
        self, query_type, start_date=None, end_date=None
    ):
        if start_date is None:
            start_date = self.day_before_yday_date_str
        if end_date is None:
            end_date = self.yesterday_date_str

        (
            success,
            transactions,
            error_code,
            error_message,
        ) = self.easypay.reconcile_transactions(
            start_date=start_date, end_date=end_date, query_type=query_type
        )
        if not success:
            logger.info(
                f"Reconciling {query_type} transactions from EasyPay for the dates "
                f"{start_date} to {end_date} failed - code: {error_code} ; message: {error_message}"
            )

        return success, transactions, error_code, error_message

    def get_ach_transactions_from_easypay(self, start_date=None, end_date=None):
        return self._get_reconciled_transactions_from_easypay(
            start_date=start_date,
            end_date=end_date,
            query_type=EasyPayReconcileTxnQueryType.ACH.value,
        )

    def get_card_transactions_from_easypay(self, start_date=None, end_date=None):
        return self._get_reconciled_transactions_from_easypay(
            start_date=start_date,
            end_date=end_date,
            query_type=EasyPayReconcileTxnQueryType.CARD.value,
        )

    def get_hb_transactions(self, txn_ids, txn_type, start_date=None, end_date=None):
        start_date = start_date or self.day_before_yday_date_str
        end_date = end_date or self.yesterday_date_str
        base_queries = Q(transaction_id__in=txn_ids) & Q(
            created_on__date__range=(start_date, end_date)
        )
        queries = base_queries
        if txn_type == EasyPayReconcileTxnQueryType.ACH.value:
            queries = queries & (
                Q(payment_method=TransactionMethod.BANK_TRANSFER.value)
                | Q(parent__payment_method=TransactionMethod.BANK_TRANSFER.value)
            )
        if txn_type == EasyPayReconcileTxnQueryType.CARD.value:
            queries = queries & (
                Q(payment_method__in=CARD_BASED_TRANSACTION_METHODS)
                | Q(parent__payment_method__in=CARD_BASED_TRANSACTION_METHODS)
            )

        return Payment.objects.filter(queries).distinct()

    def update_transactions(self, gateway_transactions, txn_type):
        if not gateway_transactions:
            logger.info("No gateway card transactions found")
            return

        total_gw_txns = len(gateway_transactions)
        self.report[txn_type]["total_gw_txns_fetched"] = total_gw_txns
        gw_txn_id_to_txn_recon_map = {
            str(txn.get("TxID")): txn for txn in gateway_transactions
        }
        gw_txn_ids = list(gw_txn_id_to_txn_recon_map.keys())

        transactions = self.get_hb_transactions(txn_ids=gw_txn_ids, txn_type=txn_type)
        total_txns_updated = 0
        for transaction_obj in transactions:
            gw_txn_id = transaction_obj.transaction_id
            if gw_txn_id not in gw_txn_id_to_txn_recon_map:
                continue
            recon_data = gw_txn_id_to_txn_recon_map.get(gw_txn_id, {})
            txn_manager = TransactionManager(payment_obj=transaction_obj)
            transaction_obj, _ = txn_manager.update_transaction_from_gateway_recon(
                gateway_recon_data=recon_data
            )
            if transaction_obj.status == TransactionStatus.FAILED.value:
                logger.info(
                    f"Transaction found to be failed at gateway ; "
                    f"id - {str(transaction_obj.id)} ; "
                    f"transaction_id: {transaction_obj.transaction_id} ; txn_type: {txn_type}"
                )
                bill_obj = transaction_obj.bill
                bill_manager = BillManager(bill_obj=bill_obj, bill_id=str(bill_obj.id))
                bill_manager.update_bill_status_on_txn_recon()

            total_txns_updated += 1

        self.report[txn_type]["total_hb_txns_updated"] = total_txns_updated

    def _run(self):
        if not self.transactions_exist_in_interval():
            logger.info(
                f"No Transactions found in the interval - {self.day_before_yday_date_str} to {self.yesterday_date_str}."
                f" Skipping recon."
            )
            return True

        (
            card_success,
            card_transactions,
            card_error_code,
            card_error_message,
        ) = self.get_card_transactions_from_easypay()
        (
            ach_success,
            ach_transactions,
            ach_error_code,
            ach_error_message,
        ) = self.get_ach_transactions_from_easypay()
        if card_success:
            self.update_transactions(
                gateway_transactions=card_transactions,
                txn_type=EasyPayReconcileTxnQueryType.CARD.value,
            )
        if ach_success:
            self.update_transactions(
                gateway_transactions=ach_transactions,
                txn_type=EasyPayReconcileTxnQueryType.ACH.value,
            )
        card_error_body = {
            "error_code": card_error_code,
            "error_message": card_error_message,
            "txn_type": EasyPayReconcileTxnQueryType.CARD.value,
        }
        ach_error_body = {
            "error_code": ach_error_code,
            "error_message": ach_error_message,
            "txn_type": EasyPayReconcileTxnQueryType.ACH.value,
        }
        self.error_body = [card_error_body, ach_error_body]
        return card_success or ach_success
