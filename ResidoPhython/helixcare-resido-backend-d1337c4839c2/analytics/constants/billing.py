from common.utils.enum import EnumWithValueConverter


class FinancialSummaryMetric(EnumWithValueConverter):
    PAYMENTS_COLLECTED = "PAYMENTS_COLLECTED"
    REVENUE = "REVENUE"
    NET_PROFIT = "NET_PROFIT"


class BillProcess(EnumWithValueConverter):
    REFUNDS = "REFUNDS"
    CANCELLATION = "CANCELLATION"
