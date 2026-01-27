from django.db.models import Sum

from analytics.constants.common import MetricValueSystem
from analytics.managers.billing.base import BaseBillingAnalyticsManager
from payments.models import BillBreakDown


class AmountDistributionManager(BaseBillingAnalyticsManager):
    def __init__(self, **kwargs):
        super(AmountDistributionManager, self).__init__(**kwargs)

    @classmethod
    def _get_absolute_distribution_for_service_types(cls, start_date, end_date):
        total_charges_per_service_type = (
            BillBreakDown.objects.filter(date__range=[start_date, end_date])
            .values("type_of_service__name")
            .annotate(total_charges=Sum("total_amount"))
            .order_by("category__name")
        )

        base_distribution = {
            charge.get("type_of_service__name"): float(charge.get("total_charges"))
            for charge in total_charges_per_service_type
            if charge.get("total_charges") is not None
        }

        return base_distribution

    @classmethod
    def _get_absolute_distribution_for_categories(cls, start_date, end_date):
        total_charges_per_category = (
            BillBreakDown.objects.filter(date__range=[start_date, end_date])
            .values("category__name")
            .annotate(total_charges=Sum("total_amount"))
            .order_by("category__name")
        )

        base_distribution = {
            charge.get("category__name"): float(charge.get("total_charges"))
            for charge in total_charges_per_category
            if charge.get("total_charges") is not None
        }

        return base_distribution

    def _get_distribution_for_service_types(self):
        absolute_distribution_for_service_types = (
            self._get_absolute_distribution_for_service_types(
                start_date=self.start_date, end_date=self.end_date
            )
        )
        percentage_distribution_for_service_types = (
            self._get_percentage_distribution_from_abs_distribution(
                abs_distribution=absolute_distribution_for_service_types
            )
        )
        return {
            MetricValueSystem.ABSOLUTE.value: absolute_distribution_for_service_types,
            MetricValueSystem.PERCENTAGE.value: percentage_distribution_for_service_types,
        }

    def _get_distribution_for_service_categories(self):
        absolute_distribution_for_categories = (
            self._get_absolute_distribution_for_categories(
                start_date=self.start_date, end_date=self.end_date
            )
        )
        percentage_distribution_for_categories = (
            self._get_percentage_distribution_from_abs_distribution(
                abs_distribution=absolute_distribution_for_categories
            )
        )
        return {
            MetricValueSystem.ABSOLUTE.value: absolute_distribution_for_categories,
            MetricValueSystem.PERCENTAGE.value: percentage_distribution_for_categories,
        }

    def get_distributions(self, attribute="service_category"):
        if attribute == "service_category":
            return self._get_distribution_for_service_categories()

        if attribute == "service_type":
            return self._get_distribution_for_service_types()

        return {}
