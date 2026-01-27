from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate

from analytics.constants.common import MetricValueSystem
from analytics.managers.billing.base import BaseBillingAnalyticsManager
from payments.constants import ONLINE_PAYMENT_METHODS, OFFLINE_PAYMENT_METHODS
from payments.models import Payment


class PaymentAnalyticsManager(BaseBillingAnalyticsManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def _get_online_offline_payment_counts_by_status(cls, status, start_date, end_date):
        return Payment.objects.aggregate(
            online_success=Count(
                "id",
                filter=(
                    Q(payment_method__in=ONLINE_PAYMENT_METHODS)
                    & Q(status=status)
                    & Q(updated_on__range=[start_date, end_date])
                ),
            ),
            offline_success=Count(
                "id",
                filter=(
                    Q(payment_method__in=OFFLINE_PAYMENT_METHODS)
                    & Q(status=status)
                    & Q(updated_on__range=[start_date, end_date])
                ),
            ),
            total_online=Count(
                "id",
                filter=(
                    Q(payment_method__in=ONLINE_PAYMENT_METHODS)
                    & Q(updated_on__range=[start_date, end_date])
                ),
            ),
            total_offline=Count(
                "id",
                filter=(
                    Q(payment_method__in=OFFLINE_PAYMENT_METHODS)
                    & Q(updated_on__range=[start_date, end_date])
                ),
            ),
        )

    @classmethod
    def _get_success_payment_percentages(cls, payment_counts):
        total_payments = payment_counts.get("total_online", 0) + payment_counts.get(
            "total_offline", 0
        )

        if total_payments == 0:
            overall_success_rate = 0
            online_success_rate = 0
            offline_success_rate = 0
        else:
            overall_success = payment_counts.get(
                "online_success", 0
            ) + payment_counts.get("offline_success", 0)

            overall_success_rate = (overall_success / total_payments) * 100

            online_success_rate = (
                payment_counts.get("online_success", 0) / total_payments
            ) * 100
            offline_success_rate = (
                payment_counts.get("offline_success", 0) / total_payments
            ) * 100

        return {
            "value": overall_success_rate,
            "value_unit": MetricValueSystem.PERCENTAGE.value,
            "distribution": {
                "online": online_success_rate,
                "offline": offline_success_rate,
            },
        }

    def get_success_rate(self):
        success_payment_counts = self._get_online_offline_payment_counts_by_status(
            status="COMPLETED", start_date=self.start_date, end_date=self.end_date
        )

        return self._get_success_payment_percentages(
            payment_counts=success_payment_counts
        )

    def get_payment_rates(self, status):
        if status == "COMPLETED":
            return self.get_success_rate()

        return {}

    def _get_payment_distribution(self, payment_filter, start_date, end_date):
        payments = Payment.objects.filter(
            status="COMPLETED",
            updated_on__range=[start_date, end_date],
            updated_on__isnull=False,
        ).filter(payment_filter)

        if not payments.exists():
            return self.refill_missing_dates({})

        payments_per_day = (
            payments.annotate(payment_date=TruncDate("updated_on"))
            .values("payment_date")
            .annotate(total_amount=Sum("amount"))
            .order_by("payment_date")
        )

        base_distribution = {
            payment.get("payment_date").isoformat(): float(
                payment.get("total_amount") or 0
            )
            for payment in payments_per_day
        }

        return self.refill_missing_dates(base_distribution)

    def get_payment_trends(self):
        online_payments_current = self._get_payment_distribution(
            Q(payment_method__in=ONLINE_PAYMENT_METHODS), self.start_date, self.end_date
        )
        in_person_payments_current = self._get_payment_distribution(
            Q(payment_method__in=OFFLINE_PAYMENT_METHODS),
            self.start_date,
            self.end_date,
        )

        online_payments_previous = self._get_payment_distribution(
            Q(payment_method__in=ONLINE_PAYMENT_METHODS),
            self.comparative_start_date,
            self.comparative_end_date,
        )
        in_person_payments_previous = self._get_payment_distribution(
            Q(payment_method__in=OFFLINE_PAYMENT_METHODS),
            self.comparative_start_date,
            self.comparative_end_date,
        )

        online_comparative = self.compare(
            current_series=list(online_payments_current.values()),
            previous_series=list(online_payments_previous.values()),
        )
        in_person_comparative = self.compare(
            current_series=list(in_person_payments_current.values()),
            previous_series=list(in_person_payments_previous.values()),
        )

        return {
            "online_portal": {
                "comparative_analysis": online_comparative,
                "distribution": {
                    date: float(amount)
                    for date, amount in online_payments_current.items()
                },
            },
            "in_person": {
                "comparative_analysis": in_person_comparative,
                "distribution": {
                    date: float(amount)
                    for date, amount in in_person_payments_current.items()
                },
            },
        }
