from common.utils.enum import EnumWithValueConverter


class PlaceOfTax(EnumWithValueConverter):
    PRIMARY = "primary"
    SECONDARY = "secondary"


ONLINE_PAYMENT_METHODS = [
    "CREDIT_CARD",
    "DEBIT_CARD",
    "BANK_TRANSFER",
    "PAYPAL",
    "GOOGLE_PAY",
]
OFFLINE_PAYMENT_METHODS = ["POS_PAYMENT", "CASH"]
CANCELLATION_CODE_COMPOSITIONS_FILE_PATH = (
    "./data/bill_cancellation_code_composition/composition.csv"
)


class DiscountFrequencyType(EnumWithValueConverter):
    ONE_TIME = "One_Time"
    RECURRING = "Recurring"


class DiscountApplicableType(EnumWithValueConverter):
    RENT = "Rent"
    MAINTENANCE = "Maintenance"
    DEPOSIT = "Deposit"
    APPLICATION_FEE = "Application_Fee"
