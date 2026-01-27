import statistics
from datetime import timedelta

from analytics.constants.common import MetricValueSystem, Trend
from common.utils.datetime import DateTimeUtils


class BaseBillingAnalyticsManager:
    def __init__(self, **kwargs):
        self.start_date = kwargs.get("start_date")
        self.end_date = kwargs.get("end_date")
        self.comparative_start_date = kwargs.get("comparative_start_date")
        self.comparative_end_date = kwargs.get("comparative_end_date")

    @classmethod
    def compare(cls, current_series, previous_series):
        current_series_mean = (
            statistics.mean(current_series) if len(current_series) else 0
        )
        previous_series_mean = (
            statistics.mean(previous_series) if len(previous_series) else 0
        )

        percentage_change = 100
        if not current_series_mean and not previous_series_mean:
            percentage_change = 0
        if previous_series_mean:
            percentage_change = (
                (current_series_mean - previous_series_mean) / previous_series_mean
            ) * 100

        trend = Trend.UP.value
        if percentage_change < 0:
            trend = Trend.DOWN.value
        elif percentage_change == 0:
            trend = Trend.UNCHANGED.value

        return {
            "delta": abs(percentage_change),
            "delta_unit": MetricValueSystem.PERCENTAGE.value,
            "trend": trend,
        }

    def refill_missing_dates(self, base_distribution):
        final_distribution = {}
        start_date_obj = DateTimeUtils.custom_date_parser(self.start_date)
        end_date_obj = DateTimeUtils.custom_date_parser(self.end_date)
        current_date_obj = start_date_obj
        while current_date_obj <= end_date_obj:
            current_date_str = current_date_obj.isoformat()
            final_distribution[current_date_str] = base_distribution.get(
                current_date_str, 0
            )
            current_date_obj += timedelta(days=1)

        return final_distribution

    @classmethod
    def _get_percentage_distribution_from_abs_distribution(cls, abs_distribution):
        total = sum(abs_distribution.values())

        return {
            key: (abs_val / total) * 100 for key, abs_val in abs_distribution.items()
        }
