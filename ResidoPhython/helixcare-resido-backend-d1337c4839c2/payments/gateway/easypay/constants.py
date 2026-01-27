import os
from common.utils.enum import EnumWithValueConverter
from payments.payment_constants import TransactionStatus

EASY_PAY_URL = os.getenv("EASY_PAY_URL", "https://easypay5.com")
EASY_PAY_ACC_CODE = os.getenv("EASY_PAY_ACC_CODE", "EP1155389")
EASY_PAY_ACC_TOKEN = os.getenv("EASY_PAY_ACC_TOKEN", "")

AUTHENTICATION = "/APIcardProcRESTstaging/v1.0.0/Authenticate"
CC_SALE = "/APIcardProcRESTstaging/v1.0.0/CardSale/Manual"
ACC_SALE = "/APIcardProcRESTstaging/v1.0.0/ACH/Sale"
CC_SALE_RECUR = "/APIcardProcRESTstaging/v1.0.0/ConsentRecurring/Create"
QUERY_CARD_TRANSACTION_PATH = "/APIcardProcREST/v1.0.0/Query/Transaction"
QUERY_ACH_TRANSACTION_PATH = "/APIcardProcREST/v1.0.0/Query/ACHTransaction"
CC_CONSENT_CREATE = "/APIcardProcREST/v1.0.0/ConsentAnnual/Create_MAN"
CC_CONSENT_PAY = "/APIcardProcREST/v1.0.0/ConsentAnnual/Create_MAN"
ACC_CONSENT_CREATE = "/APIcardProcREST/v1.0.0/ACH/Combo"
ACC_CONSENT_PAY = "/APIcardProcREST/v1.0.0/ACH/Combo"
APPLY_CREDIT_AKA_REFUND_PATH = "/APIcardProcREST/v1.0.0/CardSale/ApplyCredit"
ACC_VOID_CANCEL_TRANSACTION = "/APIcardProcREST/v1.0.0/ACH/Void"
CARD_VOID_CANCEL_TRANSACTION = "/APIcardProcREST/v1.0.0/CardSale/Void"
RECONCILE_TRANSACTIONS_API_PATH = "/APIcardProcREST/v1.0.0/Query/Reconcile"


class EasyPayReconcileTxnQueryType(EnumWithValueConverter):
    CARD = "CARD"
    ACH = "ACH"


class EasyPayRefundMethodology(EnumWithValueConverter):
    VOID = "VOID"
    APPLY_CREDIT = "APPLY_CREDIT"


class EasyPayTransactionType(EnumWithValueConverter):
    CC = "CC"
    ACH = "ACH"


class EasyPayQueryTransactionResponseKey(EnumWithValueConverter):
    CC_TRANSACTION_QUERY_RESPONSE_KEY = "Transaction_QueryResult"
    ACH_TRANSACTION_QUERY_RESPONSE_KEY = "ACHTransaction_QueryResult"


class EasyPayVoidResponseKey(EnumWithValueConverter):
    ACC_VOID_RESPONSE_KEY = "ACHTransaction_VoidResult"
    CARD_VOID_RESPONSE_KEY = "Transaction_VoidResult"


class EasyPayTxnStatus(EnumWithValueConverter):
    OPEN = "OPEN"
    SETTLED = "SETTLED"
    FAILED = "FAILED"
    LOCKED = "LOCKED"
    VOID = "VOID"
    AUTHOK = "AUTHOK"


class EasyPayVerifoneTxnEvent(EnumWithValueConverter):
    TX_APPROVED = "TxApproved"
    TX_DECLINE = "TxDecline"
    TX_REVERSED = "TxReversed"  # TODO mapped to what??
    PRE_SALE_DEVICE_CODE = "PreSaleDeviceCode"  # TODO mapped to what??
    POST_SALE_DEVICE_CODE = "PostSaleDeviceCode"  # TODO mapped to what??
    TIMEOUT = "Timeout"  # TODO mapped to what??
    ASPEN_ERROR = "AspenError"
    AUTH_FAIL = "AuthFail"
    FUNCTION_FAIL = "FunctionFail"
    EXCEPTION = "Exception"


EASYPAY_VERIFONE_EVENT_TO_TRANSACTION_STATUS_MAP = {
    EasyPayVerifoneTxnEvent.TX_APPROVED.value: EasyPayTxnStatus.OPEN.value,
    EasyPayVerifoneTxnEvent.TX_DECLINE.value: EasyPayTxnStatus.FAILED.value,
    EasyPayVerifoneTxnEvent.ASPEN_ERROR.value: EasyPayTxnStatus.FAILED.value,
    EasyPayVerifoneTxnEvent.AUTH_FAIL.value: EasyPayTxnStatus.FAILED.value,
    EasyPayVerifoneTxnEvent.FUNCTION_FAIL.value: EasyPayTxnStatus.FAILED.value,
    EasyPayVerifoneTxnEvent.EXCEPTION.value: EasyPayTxnStatus.FAILED.value,
}

EASY_PAY_TRANSACTION_STATUS_TO_PAYMENTS_STATUS = {
    EasyPayTxnStatus.OPEN.value: TransactionStatus.COMPLETED.value,
    EasyPayTxnStatus.SETTLED.value: TransactionStatus.COMPLETED.value,  # TODO Should we track SETTLED as COMPLETED or anything beyond that
    EasyPayTxnStatus.FAILED.value: TransactionStatus.FAILED.value,
    EasyPayTxnStatus.VOID.value: TransactionStatus.CANCELLED.value,
}

EASY_PAY_TRANSACTION_TYPE_TO_QUERY_TRANSACTION_API_PATH_MAP = {
    EasyPayTransactionType.CC.value: QUERY_CARD_TRANSACTION_PATH,
    EasyPayTransactionType.ACH.value: QUERY_ACH_TRANSACTION_PATH,
}

EASY_PAY_TRANSACTION_TYPE_TO_QUERY_RESPONSE_KEY_MAP = {
    EasyPayTransactionType.CC.value: EasyPayQueryTransactionResponseKey.CC_TRANSACTION_QUERY_RESPONSE_KEY.value,
    EasyPayTransactionType.ACH.value: EasyPayQueryTransactionResponseKey.ACH_TRANSACTION_QUERY_RESPONSE_KEY.value,
}
