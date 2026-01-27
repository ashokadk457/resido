from datetime import timedelta
from django.db.models import (
    Sum,
    F,
    Case,
    When,
    Value,
    DecimalField,
    Count,
    OuterRef,
    Subquery,
)
from django.db.models.functions import TruncDate, Coalesce
from django.db.models.expressions import CombinedExpression

from analytics.constants.billing import (
    FinancialSummaryMetric,
    BillProcess,
)
from analytics.managers.billing.base import BaseBillingAnalyticsManager
from common.utils.datetime import DateTimeUtils
from lookup.models import Lookup
from payments.models import (
    BillRefundRequest,
    Payment,
    Bill,
    BillDiscount,
    BillAdjustment,
    BillWriteoff,
)
from payments.payment_constants import TransactionStatus


class FinancialSummaryManager(BaseBillingAnalyticsManager):
    def __init__(self, **kwargs):
        super(FinancialSummaryManager, self).__init__(**kwargs)
        self.comparative_dates_available = (
            self.comparative_start_date and self.comparative_end_date
        )

    def _query_aggregated_payments(self, status, start_date, end_date):
        payments_per_day = (
            Payment.objects.filter(
                status=status,
                updated_on__range=[start_date, end_date],
            )
            .annotate(payment_date=TruncDate("updated_on"))
            .values("payment_date")
            .annotate(
                total_amount=Sum(
                    "amount", output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )
            .order_by("payment_date")
        )

        base_distribution = {
            payment.get("payment_date").isoformat(): float(payment.get("total_amount"))
            for payment in payments_per_day
        }

        return self.refill_missing_dates(base_distribution=base_distribution)

    def _query_aggregated_bills(self, status, start_date, end_date):
        bills_per_day = (
            Bill.objects.filter(
                status=status,
                paid_date__range=[start_date, end_date],
            )
            .annotate(bill_completed_date=TruncDate("paid_date"))
            .values("bill_completed_date")
            .annotate(
                revenue=Sum(
                    CombinedExpression(
                        F("total_charges"),
                        "+",
                        F("insurance_paid"),
                        output_field=DecimalField(max_digits=14, decimal_places=2),
                    ),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                )
            )
            .order_by("bill_completed_date")
        )

        base_distribution = {
            bill.get("bill_completed_date").isoformat(): float(bill.get("revenue"))
            for bill in bills_per_day
        }

        return self.refill_missing_dates(base_distribution=base_distribution)

    def _query_aggregated_outstanding_balance(self, start_date, end_date):
        PENDING = TransactionStatus.PENDING.value
        PARTIAL = TransactionStatus.PARTIALLY_COMPLETED.value
        ON_PP = TransactionStatus.ON_PP.value
        COMPLETED = TransactionStatus.COMPLETED.value

        if isinstance(start_date, str):
            start_date = DateTimeUtils.custom_date_parser(start_date)
        if isinstance(end_date, str):
            end_date = DateTimeUtils.custom_date_parser(end_date)

        date_dict = {}
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.isoformat()
            date_dict[date_str] = 0
            current_date += timedelta(days=1)

        pending_query = (
            Bill.objects.filter(
                status=PENDING,
                created_on__range=[start_date, end_date],
            )
            .annotate(bill_date=TruncDate("created_on"))
            .values("bill_date")
            .annotate(daily_total=Sum("total_charges"))
        )

        for item in pending_query:
            bill_date = item["bill_date"]
            date_str = (
                bill_date.isoformat() if hasattr(bill_date, "isoformat") else bill_date
            )
            date_dict[date_str] = date_dict.get(date_str, 0) + float(
                item["daily_total"] or 0
            )

        partial_query = (
            Bill.objects.filter(
                status__in=[PARTIAL, ON_PP],
                created_on__range=[start_date, end_date],
            )
            .annotate(bill_date=TruncDate("created_on"))
            .values("bill_date")
            .annotate(
                total_charges=Sum("total_charges"),
                completed_payments=Sum(
                    Case(
                        When(payments__status=COMPLETED, then="payments__amount"),
                        default=Value(0),
                        output_field=DecimalField(max_digits=10, decimal_places=2),
                    )
                ),
            )
        )

        for item in partial_query:
            bill_date = item["bill_date"]
            date_str = (
                bill_date.isoformat() if hasattr(bill_date, "isoformat") else bill_date
            )
            partial_total = (item["total_charges"] or 0) - (
                item["completed_payments"] or 0
            )
            date_dict[date_str] = date_dict.get(date_str, 0) + float(partial_total)

        final_distribution = self.refill_missing_dates(date_dict)

        current_outstanding = sum(final_distribution.values())

        return {"distribution": final_distribution, "total": current_outstanding}

    def _query_discounts_data(self, start_date, end_date):
        discounts = (
            BillDiscount.objects.filter(
                created_on__range=[start_date, end_date],
            )
            .annotate(date=TruncDate("created_on"))
            .values("date")
            .annotate(
                total_amount=Sum(
                    "amount", output_field=DecimalField(max_digits=14, decimal_places=2)
                ),
                count=Count("id"),
            )
            .order_by("date")
        )

        base_distribution = {
            item["date"].isoformat(): {
                "amount": float(item["total_amount"] or 0),
                "count": item["count"],
            }
            for item in discounts
        }

        total_amount = sum(item["total_amount"] or 0 for item in discounts)
        total_count = sum(item["count"] for item in discounts)

        return {
            "distribution": self.refill_missing_dates(
                {k: v["amount"] for k, v in base_distribution.items()}
            ),
            "total_amount": float(total_amount),
            "total_count": total_count,
            "counts_distribution": {
                k: v["count"] for k, v in base_distribution.items()
            },
        }

    def _query_adjustments_data(self, start_date, end_date):
        adjustments = (
            BillAdjustment.objects.filter(
                created_on__range=[start_date, end_date],
            )
            .annotate(date=TruncDate("created_on"))
            .values("date")
            .annotate(
                total_amount=Sum(
                    "amount", output_field=DecimalField(max_digits=14, decimal_places=2)
                ),
                count=Count("id"),
            )
            .order_by("date")
        )

        base_distribution = {
            item["date"].isoformat(): {
                "amount": float(item["total_amount"] or 0),
                "count": item["count"],
            }
            for item in adjustments
        }

        total_amount = sum(item["total_amount"] or 0 for item in adjustments)
        total_count = sum(item["count"] for item in adjustments)

        return {
            "distribution": self.refill_missing_dates(
                {k: v["amount"] for k, v in base_distribution.items()}
            ),
            "total_amount": float(total_amount),
            "total_count": total_count,
            "counts_distribution": {
                k: v["count"] for k, v in base_distribution.items()
            },
        }

    def _query_writeoffs_data(self, start_date, end_date):
        writeoffs = (
            BillWriteoff.objects.filter(
                created_on__range=[start_date, end_date],
            )
            .annotate(date=TruncDate("created_on"))
            .values("date")
            .annotate(
                total_amount=Sum(
                    "amount", output_field=DecimalField(max_digits=14, decimal_places=2)
                ),
                count=Count("id"),
            )
            .order_by("date")
        )

        base_distribution = {
            item["date"].isoformat(): {
                "amount": float(item["total_amount"] or 0),
                "count": item["count"],
            }
            for item in writeoffs
        }

        total_amount = sum(item["total_amount"] or 0 for item in writeoffs)
        total_count = sum(item["count"] for item in writeoffs)

        return {
            "distribution": self.refill_missing_dates(
                {k: v["amount"] for k, v in base_distribution.items()}
            ),
            "total_amount": float(total_amount),
            "total_count": total_count,
            "counts_distribution": {
                k: v["count"] for k, v in base_distribution.items()
            },
        }

    def _query_past_due_data(self, start_date, end_date):
        COMPLETED = TransactionStatus.COMPLETED.value
        payments_subquery = (
            Payment.objects.filter(
                bill=OuterRef("pk"), status=COMPLETED, updated_on__lte=end_date
            )
            .values("bill")
            .annotate(
                total_paid=Sum(
                    "amount", output_field=DecimalField(max_digits=14, decimal_places=2)
                )
            )
            .values("total_paid")
        )

        bills = (
            Bill.objects.filter(
                due_date__range=[start_date, end_date],
                status__in=[
                    TransactionStatus.PENDING.value,
                    TransactionStatus.PARTIALLY_COMPLETED.value,
                    TransactionStatus.ON_PP.value,
                ],
            )
            .annotate(
                total_paid=Coalesce(
                    Subquery(
                        payments_subquery,
                        output_field=DecimalField(max_digits=14, decimal_places=2),
                    ),
                    Value(
                        0.0, output_field=DecimalField(max_digits=14, decimal_places=2)
                    ),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
                outstanding=CombinedExpression(
                    F("patient_amount"),
                    "-",
                    F("total_paid"),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
            )
            .filter(outstanding__gt=0)
            .annotate(date=TruncDate("due_date"))
            .values("date")
            .annotate(
                total_amount=Sum(
                    "outstanding",  # Changed from 'amount' to 'outstanding'
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
                count=Count("id"),
            )
            .order_by("date")
        )

        base_distribution = {
            item["date"].isoformat(): {
                "amount": float(item["total_amount"] or 0),
                "count": item["count"],
            }
            for item in bills
        }

        total_amount = sum(item["total_amount"] or 0 for item in bills)
        total_count = sum(item["count"] for item in bills)

        return {
            "distribution": self.refill_missing_dates(
                {k: v["amount"] for k, v in base_distribution.items()}
            ),
            "total_amount": float(total_amount),
            "total_count": total_count,
            "counts_distribution": {
                k: v["count"] for k, v in base_distribution.items()
            },
        }

    def _query_customer_paid_data(self, start_date, end_date):
        COMPLETED = TransactionStatus.COMPLETED.value
        payments = (
            Payment.objects.filter(
                status=COMPLETED,
                updated_on__range=[start_date, end_date],
            )
            .annotate(date=TruncDate("updated_on"))
            .values("date")
            .annotate(
                total_amount=Sum(
                    "amount", output_field=DecimalField(max_digits=14, decimal_places=2)
                ),
                count=Count("id"),
            )
            .order_by("date")
        )

        base_distribution = {
            item["date"].isoformat(): {
                "amount": float(item["total_amount"] or 0),
                "count": item["count"],
            }
            for item in payments
        }

        total_amount = sum(item["total_amount"] or 0 for item in payments)
        total_count = sum(item["count"] for item in payments)

        return {
            "distribution": self.refill_missing_dates(
                {k: v["amount"] for k, v in base_distribution.items()}
            ),
            "total_amount": float(total_amount),
            "total_count": total_count,
            "counts_distribution": {
                k: v["count"] for k, v in base_distribution.items()
            },
        }

    def _get_metric_with_comparison(
        self, query_func, start_date, end_date, comp_start_date=None, comp_end_date=None
    ):
        current_data = query_func(start_date, end_date)
        previous_data = None
        comparative_analysis = None

        if self.comparative_dates_available and comp_start_date and comp_end_date:
            previous_data = query_func(comp_start_date, comp_end_date)
            comparative_analysis = self.compare(
                current_series=list(current_data["distribution"].values()),
                previous_series=list(previous_data["distribution"].values()),
            )

        return {
            "current_total": current_data["total_amount"],
            "current_count": current_data["total_count"],
            "current_distribution": current_data["distribution"],
            "current_counts_distribution": current_data["counts_distribution"],
            "previous_total": previous_data["total_amount"] if previous_data else 0,
            "previous_count": previous_data["total_count"] if previous_data else 0,
            "previous_distribution": (
                previous_data["distribution"] if previous_data else {}
            ),
            "previous_counts_distribution": (
                previous_data["counts_distribution"] if previous_data else {}
            ),
            "comparative_analysis": comparative_analysis,
        }

    def get_outstanding_analytics(self):
        metrics = {
            "outstanding_balance": self.outstanding_balance_comparative_analysis(),
            "discounts_applied": self._get_metric_with_comparison(
                self._query_discounts_data,
                self.start_date,
                self.end_date,
                self.comparative_start_date,
                self.comparative_end_date,
            ),
            "invoice_adjustments": self._get_metric_with_comparison(
                self._query_adjustments_data,
                self.start_date,
                self.end_date,
                self.comparative_start_date,
                self.comparative_end_date,
            ),
            "invoice_write_off": self._get_metric_with_comparison(
                self._query_writeoffs_data,
                self.start_date,
                self.end_date,
                self.comparative_start_date,
                self.comparative_end_date,
            ),
            "invoices_past_due": self._get_metric_with_comparison(
                self._query_past_due_data,
                self.start_date,
                self.end_date,
                self.comparative_start_date,
                self.comparative_end_date,
            ),
            "customer_paid": self._get_metric_with_comparison(
                self._query_customer_paid_data,
                self.start_date,
                self.end_date,
                self.comparative_start_date,
                self.comparative_end_date,
            ),
        }

        return metrics

    def _query_aggregated_reason(
        self, start_date, end_date, lookup_name, lookup_field, model
    ):
        reason = list(
            Lookup.objects.filter(name=lookup_name).values_list("code", flat=True)
        )
        reason_query = (
            model.objects.filter(
                **{
                    f"{lookup_field}__in": reason,
                    "created_on__range": [start_date, end_date],
                }
            )
            .annotate(date=TruncDate("created_on"), reason_name=F(lookup_field))
            .values("date", "reason_name")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        datewise_counts = {}
        groupby_reason_in_abs = {}
        overall_total = 0

        for data in reason_query:
            date_str = data.get("date", "").isoformat()
            reason = data.get("reason_name")
            count = data.get("count", 0)

            datewise_counts[date_str] = datewise_counts.get(date_str, 0) + count

            groupby_reason_in_abs[reason] = groupby_reason_in_abs.get(reason, 0) + count

            overall_total += count

        groupby_reason_in_percentage = (
            self._get_percentage_distribution_from_abs_distribution(
                groupby_reason_in_abs
            )
        )

        datewise = self.refill_missing_dates(datewise_counts)

        return {
            "datewise": datewise,
            "reason_in_abs": groupby_reason_in_abs,
            "reason_in_percentage": groupby_reason_in_percentage,
            "overall_total": overall_total,
        }

    def summarize_payments_collected(self):
        current_payments_collected_datewise_map = self._query_aggregated_payments(
            status="COMPLETED", start_date=self.start_date, end_date=self.end_date
        )
        previous_payments_collected_datewise_map, comparative_analysis = {}, None
        if self.comparative_dates_available:
            previous_payments_collected_datewise_map = self._query_aggregated_payments(
                status="COMPLETED",
                start_date=self.comparative_start_date,
                end_date=self.comparative_end_date,
            )
            comparative_analysis = self.compare(
                current_series=list(current_payments_collected_datewise_map.values()),
                previous_series=list(previous_payments_collected_datewise_map.values()),
            )

        return {
            "total": sum(list(current_payments_collected_datewise_map.values())),
            "comparative_analysis": comparative_analysis,
            "distribution": current_payments_collected_datewise_map,
        }

    def summarize_bills_revenue(self):
        current_revenue_datewise_map = self._query_aggregated_bills(
            status="COMPLETED", start_date=self.start_date, end_date=self.end_date
        )
        previous_revenue_datewise_map, comparative_analysis = {}, None
        if self.comparative_dates_available:
            previous_revenue_datewise_map = self._query_aggregated_bills(
                status="COMPLETED",
                start_date=self.comparative_start_date,
                end_date=self.comparative_end_date,
            )
            comparative_analysis = self.compare(
                current_series=list(current_revenue_datewise_map.values()),
                previous_series=list(previous_revenue_datewise_map.values()),
            )

        return {
            "total": sum(list(current_revenue_datewise_map.values())),
            "comparative_analysis": comparative_analysis,
            "distribution": current_revenue_datewise_map,
        }

    def get_reason_comparative_analysis(self, **kwargs):
        current_reason = self._query_aggregated_reason(
            start_date=self.start_date, end_date=self.end_date, **kwargs
        )
        previous_reason, comparative_analysis = {}, None
        if self.comparative_dates_available:
            previous_reason = self._query_aggregated_reason(
                start_date=self.comparative_start_date,
                end_date=self.comparative_end_date,
                **kwargs,
            )
            comparative_analysis = self.compare(
                current_series=list(current_reason["datewise"].values()),
                previous_series=list(previous_reason["datewise"].values()),
            )

        return {
            "total": current_reason["overall_total"],
            "comparative_analysis": comparative_analysis,
            "ABSOLUTE": current_reason["reason_in_abs"],
            "PERCENTAGE": current_reason["reason_in_percentage"],
        }

    def summarize(self, metric):
        if metric == FinancialSummaryMetric.PAYMENTS_COLLECTED.value:
            return self.summarize_payments_collected()

        if metric == FinancialSummaryMetric.REVENUE.value:
            return self.summarize_bills_revenue()

        if metric == BillProcess.REFUNDS.value:
            return self.get_reason_comparative_analysis(
                lookup_name="BILL_REFUND_REASON",
                lookup_field="refund_reason",
                model=BillRefundRequest,
            )

        if metric == BillProcess.CANCELLATION.value:
            return self.get_reason_comparative_analysis(
                lookup_name="BILL_CANCELLATION_REASON",
                lookup_field="cancellation_reason",
                model=Bill,
            )

        return {}

    def outstanding_balance_comparative_analysis(self):
        current_outstanding = self._query_aggregated_outstanding_balance(
            start_date=self.start_date, end_date=self.end_date
        )
        previous_outstanding, comparative_analysis = {}, None
        if self.comparative_dates_available:
            previous_outstanding = self._query_aggregated_outstanding_balance(
                start_date=self.comparative_start_date,
                end_date=self.comparative_end_date,
            )
            comparative_analysis = self.compare(
                current_series=list(current_outstanding["distribution"].values()),
                previous_series=list(previous_outstanding["distribution"].values()),
            )

        return {
            "current_total": current_outstanding["total"],
            "current_distribution": current_outstanding["distribution"],
            "previous_total": previous_outstanding.get("total", 0),
            "previous_distribution": previous_outstanding.get("distribution", {}),
            "comparative_analysis": comparative_analysis,
        }

    def _query_payments(
        self, model, amount_field, start_date, end_date, filter_conditions
    ):
        date_field = "updated_on" if model == Payment else "paid_date"
        payments = (
            model.objects.filter(
                **filter_conditions, **{f"{date_field}__isnull": False}
            )
            .annotate(payment_date=TruncDate(date_field))
            .values("payment_date")
            .annotate(
                total_amount=Sum(
                    amount_field,
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                )
            )
            .order_by("payment_date")
        )

        base_distribution = {
            payment.get("payment_date").isoformat(): float(
                payment.get("total_amount") or 0
            )
            for payment in payments
        }

        return self.refill_missing_dates(base_distribution)

    def get_payment_comparison(self, model, amount_field, filter_conditions):
        current_payments = self._query_payments(
            model, amount_field, self.start_date, self.end_date, filter_conditions
        )
        comparative_payments = {}
        if self.comparative_dates_available:
            comparative_payments = self._query_payments(
                model,
                amount_field,
                self.comparative_start_date,
                self.comparative_end_date,
                filter_conditions,
            )

        comparative_analysis = (
            self.compare(
                current_series=list(current_payments.values()),
                previous_series=list(comparative_payments.values()),
            )
            if self.comparative_dates_available
            else None
        )

        total_amount = sum(current_payments.values()) or 1
        distribution = [
            {
                "x": f"{amount / total_amount * 100:.1f}%",
                "y": date,
                "amount": float(amount),
            }
            for date, amount in current_payments.items()
        ]

        return {
            "comparative_analysis": comparative_analysis,
            "distribution": distribution,
        }

    def get_insurance_comparison(self):
        return self.get_payment_comparison(
            Bill,
            "insurance_paid",
            {"insurance_paid__gt": 0, "status": TransactionStatus.COMPLETED.value},
        )

    def get_selfpay_comparison(self):
        return self.get_payment_comparison(
            Payment,
            "amount",
            {
                "bill__insurance_paid__isnull": True,
                "status": TransactionStatus.COMPLETED.value,
            },
        )
