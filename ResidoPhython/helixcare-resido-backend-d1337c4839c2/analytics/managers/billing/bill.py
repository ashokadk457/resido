from django.db.models import Q, Count

from analytics.constants.common import MetricValueSystem
from analytics.managers.billing.base import BaseBillingAnalyticsManager
from payments.models import Bill
from payments.payment_constants import BILL_PAID_STATUS, BILL_UNPAID_STATUS


class BillStatsAnalyticsManager(BaseBillingAnalyticsManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def _get_paid_unpaid_bill_counts(cls, start_date, end_date):
        return Bill.objects.aggregate(
            paid_bills=Count(
                "id",
                filter=(
                    Q(status__in=BILL_PAID_STATUS)
                    & Q(created_on__range=[start_date, end_date])
                ),
            ),
            unpaid_bills=Count(
                "id",
                filter=(
                    Q(status__in=BILL_UNPAID_STATUS)
                    & Q(created_on__range=[start_date, end_date])
                ),
            ),
        )

    @classmethod
    def _get_bill_status_percentages(cls, bill_counts):
        total_paid_or_unpaid_bills = bill_counts.get("paid_bills", 0) + bill_counts.get(
            "unpaid_bills", 0
        )
        paid_bills_percentage = 0
        unpaid_bills_percentage = 0

        if total_paid_or_unpaid_bills > 0:
            paid_bills_percentage = (
                bill_counts.get("paid_bills", 0) / total_paid_or_unpaid_bills
            ) * 100
            unpaid_bills_percentage = (
                bill_counts.get("unpaid_bills", 0) / total_paid_or_unpaid_bills
            ) * 100

        return {
            "value": total_paid_or_unpaid_bills,
            "value_unit": MetricValueSystem.ABSOLUTE.value,
            "distribution": {
                MetricValueSystem.PERCENTAGE.value: {
                    "unpaid_bills": unpaid_bills_percentage,
                    "paid_bills": paid_bills_percentage,
                },
                MetricValueSystem.ABSOLUTE.value: {
                    "unpaid_bills": bill_counts.get("unpaid_bills", 0),
                    "paid_bills": bill_counts.get("paid_bills", 0),
                },
            },
        }

    def get_paid_unpaid_bills_distribution(self):
        bill_counts = self._get_paid_unpaid_bill_counts(
            start_date=self.start_date, end_date=self.end_date
        )
        return self._get_bill_status_percentages(bill_counts=bill_counts)
