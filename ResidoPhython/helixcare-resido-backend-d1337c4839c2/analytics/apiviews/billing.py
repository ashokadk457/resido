from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Count

from analytics.constants.billing import FinancialSummaryMetric, BillProcess
from analytics.managers.billing.amount import AmountDistributionManager
from analytics.managers.billing.bill import BillStatsAnalyticsManager
from analytics.managers.billing.fs import FinancialSummaryManager
from analytics.managers.billing.payment import PaymentAnalyticsManager
from analytics.utils import get_metrics_requested
from common.errors import ERROR_DETAILS
from common.exception import StandardAPIException
from common.response import StandardAPIResponse
from payments.models import Payment


class FinancialSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        comparative_start_date = self.request.query_params.get("comparative_start_date")
        comparative_end_date = self.request.query_params.get("comparative_end_date")

        metrics_requested = get_metrics_requested(
            metrics=FinancialSummaryMetric.values(),
            query_params=self.request.query_params,
        )

        final_response_data = {}
        fs_manager = FinancialSummaryManager(
            start_date=start_date,
            end_date=end_date,
            comparative_start_date=comparative_start_date,
            comparative_end_date=comparative_end_date,
        )
        for financial_summary_metric in metrics_requested:
            metric_summary = fs_manager.summarize(metric=financial_summary_metric)
            final_response_data[financial_summary_metric.lower()] = metric_summary

        return StandardAPIResponse(data=final_response_data, status=status.HTTP_200_OK)


class ServiceCategoryAmountDistributionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        charges_manager = AmountDistributionManager(
            start_date=start_date, end_date=end_date
        )
        distribution = charges_manager.get_distributions(attribute="service_category")

        return StandardAPIResponse(data=distribution, status=status.HTTP_200_OK)


class ServiceTypeAmountDistributionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        charges_manager = AmountDistributionManager(
            start_date=start_date, end_date=end_date
        )
        distribution = charges_manager.get_distributions(attribute="service_type")

        return StandardAPIResponse(data=distribution, status=status.HTTP_200_OK)


class PaymentStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        payment_status = self.request.query_params.get("status")
        if not payment_status:
            raise StandardAPIException(
                code="payment_status_missing",
                detail=ERROR_DETAILS["payment_status_missing"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        payment_analytics_manager = PaymentAnalyticsManager(
            start_date=start_date, end_date=end_date
        )
        payment_stats = payment_analytics_manager.get_payment_rates(
            status=payment_status
        )

        return StandardAPIResponse(data=payment_stats, status=status.HTTP_200_OK)


class BillStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        bill_analytics_manager = BillStatsAnalyticsManager(
            start_date=start_date, end_date=end_date
        )
        bill_stats = bill_analytics_manager.get_paid_unpaid_bills_distribution()

        return StandardAPIResponse(data=bill_stats, status=status.HTTP_200_OK)


class CombinedFinancialMetricsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        comparative_start_date = self.request.query_params.get("comparative_start_date")
        comparative_end_date = self.request.query_params.get("comparative_end_date")

        fs_manager = FinancialSummaryManager(
            start_date=start_date,
            end_date=end_date,
            comparative_start_date=comparative_start_date,
            comparative_end_date=comparative_end_date,
        )

        final_response_data = fs_manager.get_outstanding_analytics()

        return StandardAPIResponse(data=final_response_data, status=status.HTTP_200_OK)


class BillProcessStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        comparative_start_date = self.request.query_params.get("comparative_start_date")
        comparative_end_date = self.request.query_params.get("comparative_end_date")

        metrics_requested = get_metrics_requested(
            metrics=BillProcess.values(), query_params=self.request.query_params
        )

        if not metrics_requested:
            metrics_requested = BillProcess.values()

        final_response_data = {}
        fs_manager = FinancialSummaryManager(
            start_date=start_date,
            end_date=end_date,
            comparative_start_date=comparative_start_date,
            comparative_end_date=comparative_end_date,
        )
        for payment_reason_metric in metrics_requested:
            metric_summary = fs_manager.summarize(metric=payment_reason_metric)
            final_response_data[payment_reason_metric.lower()] = metric_summary

        return StandardAPIResponse(data=final_response_data, status=status.HTTP_200_OK)


class PaymentMethodStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        fs_manager = FinancialSummaryManager(
            start_date=start_date,
            end_date=end_date,
        )

        payment_methods = (
            Payment.objects.filter(created_on__range=[start_date, end_date])
            .values("payment_method")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        method_distribution_in_abs = {
            item["payment_method"]: item["count"] for item in payment_methods
        }

        method_distribution_in_percentage = (
            fs_manager._get_percentage_distribution_from_abs_distribution(
                method_distribution_in_abs
            )
        )

        final_response_data = {
            "ABSOLUTE": method_distribution_in_abs,
            "PERCENTAGE": method_distribution_in_percentage,
            "total": sum(method_distribution_in_abs.values()),
        }
        return StandardAPIResponse(data=final_response_data, status=status.HTTP_200_OK)


class InsuranceSelfpayComparisonAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        comparative_start_date = self.request.query_params.get("comparative_start_date")
        comparative_end_date = self.request.query_params.get("comparative_end_date")

        fs_manager = FinancialSummaryManager(
            start_date=start_date,
            end_date=end_date,
            comparative_start_date=comparative_start_date,
            comparative_end_date=comparative_end_date,
        )

        insurance_data = fs_manager.get_insurance_comparison()
        selfpay_data = fs_manager.get_selfpay_comparison()

        response_data = {"insurance": insurance_data, "self_pay": selfpay_data}

        return StandardAPIResponse(data=response_data, status=status.HTTP_200_OK)


class PaymentTrendAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        comparative_start_date = request.query_params.get("comparative_start_date")
        comparative_end_date = request.query_params.get("comparative_end_date")

        payment_manager = PaymentAnalyticsManager(
            start_date=start_date,
            end_date=end_date,
            comparative_start_date=comparative_start_date,
            comparative_end_date=comparative_end_date,
        )

        response_data = payment_manager.get_payment_trends()

        return StandardAPIResponse(data=response_data, status=status.HTTP_200_OK)
