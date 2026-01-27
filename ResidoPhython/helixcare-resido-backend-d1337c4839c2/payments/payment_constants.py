from common.utils.enum import EnumWithValueConverter


class TransactionMethod(EnumWithValueConverter):
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    PAYPAL = "PAYPAL"
    CASH = "CASH"
    GOOGLE_PAY = "GOOGLE_PAY"
    BANK_TRANSFER = "BANK_TRANSFER"
    POS_PAYMENT = "POS_PAYMENT"
    BACK_TO_SOURCE = "BACK_TO_SOURCE"
    WALLET = "WALLET"
    WRITE_OFF = "WRITE_OFF"
    ADJUSTMENT = "ADJUSTMENT"


REFUND_TRANSACTION_METHODS = [
    TransactionMethod.BACK_TO_SOURCE.value,
    TransactionMethod.WALLET.value,
    TransactionMethod.WRITE_OFF.value,
    TransactionMethod.ADJUSTMENT.value,
    TransactionMethod.CASH.value,
]

CARD_BASED_TRANSACTION_METHODS = [
    TransactionMethod.CREDIT_CARD.value,
    TransactionMethod.DEBIT_CARD.value,
    TransactionMethod.POS_PAYMENT.value,
]

PARENT_MANDATED_REFUND_METHODS = [
    TransactionMethod.BACK_TO_SOURCE.value,
    TransactionMethod.CASH.value,
]


class TransactionStatus(EnumWithValueConverter):
    PENDING = "PENDING"
    ON_PP = "ON_PP"
    DRAFT = "DRAFT"
    IN_PROCESS = "IN_PROCESS"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    REFUND_INITIATED = "REFUND_INITIATED"
    PARTIAL_REFUND_INITIATED = "PARTIAL_REFUND_INITIATED"
    PARTIAL_REFUND_FAILED = "PARTIAL_REFUND_FAILED"
    REFUND_FAILED = "REFUND_FAILED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    CANCELLED = "CANCELLED"


class RefundType(EnumWithValueConverter):
    FULL_REFUND = "FULL_REFUND"
    PARTIAL_REFUND = "PARTIAL_REFUND"


class TransactionType(EnumWithValueConverter):
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"


class TransactionEventSource(EnumWithValueConverter):
    SYSTEM = "SYSTEM"
    GATEWAY = "GATEWAY"


class TransactionEvent(EnumWithValueConverter):
    SALE_GATEWAY = "SALE_GATEWAY"
    QUERY_GATEWAY = "QUERY_GATEWAY"
    VOID_GATEWAY = "VOID_GATEWAY"
    CREDIT_GATEWAY = "CREDIT_GATEWAY"
    RECONCILE_GATEWAY = "RECONCILE_GATEWAY"


PAYMENT_ORIGINALLY_DONE_STATUSES = [
    TransactionStatus.COMPLETED.value,
    TransactionStatus.REFUNDED.value,
    TransactionStatus.PARTIALLY_REFUNDED.value,
    TransactionStatus.REFUND_FAILED.value,
    TransactionStatus.PARTIAL_REFUND_FAILED.value,
]

REFUNDABLE_BILL_STATUSES = [
    TransactionStatus.PARTIALLY_COMPLETED.value,
    TransactionStatus.COMPLETED.value,
    TransactionStatus.PARTIALLY_REFUNDED.value,
    TransactionStatus.REFUND_FAILED.value,
    TransactionStatus.PARTIAL_REFUND_FAILED.value,
]

REFUNDED_TRANSACTION_STATUSES = [
    TransactionStatus.PARTIALLY_REFUNDED.value,
    TransactionStatus.REFUNDED.value,
]


class RefundRequestStatus(EnumWithValueConverter):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    FAILED = "FAILED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    COMPLETED = "COMPLETED"


SUCCESSFUL_REFUND_REQUEST_STATUSES = [
    RefundRequestStatus.COMPLETED.value,
    RefundRequestStatus.PARTIAL_SUCCESS.value,
]

PAYMENT_LINK_TEMPLATE_URL = "{domain}/#/billing-history-detail-view?uid={uid}&bill-id={bill_id}&module=billing-history-details"

PAYMENT_LINK_MAIL_SUBJECT = "Payment Invoice"

PAYMENT_LINK_MAIL_BODY = """Your invoice is now ready for payment.\n
Please proceed with the payment using the following link. : {PAYMENT_LINK_TEMPLATE_URL}"""

BILL_PAID_STATUS = ["COMPLETED"]
BILL_UNPAID_STATUS = ["PENDING", "PARTIALLY_COMPLETED"]
