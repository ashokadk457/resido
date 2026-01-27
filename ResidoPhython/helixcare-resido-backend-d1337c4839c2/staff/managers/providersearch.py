from django.db.models import QuerySet

from common.constants import ALLOWED_PREFERRED_TIMES
from staff.models import HelixStaff


def get_empty_queryset():
    return HelixStaff.objects.none()


def get_default_provider_queryset():
    return (
        HelixStaff.objects.filter(user__is_active=True)
        .select_related("primary_location")
        .prefetch_related("locations")
        .prefetch_related("specialities")
        .prefetch_related("user")
        .prefetch_related("pcp")
    )


class ProviderSearchManager:
    # TODO eventually deprecate this class and move its functions and methods elsewhere
    @classmethod
    def filter_by_preferred_time(
        cls, providers_list: QuerySet, preferred_times: set
    ) -> list:
        if not preferred_times.issubset(set(ALLOWED_PREFERRED_TIMES)):
            return list(providers_list)

        preferred_times = list(preferred_times)

        return [
            obj
            for obj in providers_list
            if any(getattr(obj, pt) is True for pt in preferred_times)
        ]

    @staticmethod
    def format_filter_counts(filter_counts):
        formatted_counts = {}
        for key, values in filter_counts.items():
            formatted_values = {}
            for value, count in values:
                if isinstance(value, (list, tuple)):
                    formatted_values.update(
                        {str(sub_value): count for sub_value in value}
                    )
                else:
                    formatted_values[value] = count
            formatted_counts[key] = formatted_values

        for key in formatted_counts.keys():
            if not formatted_counts[key]:
                formatted_counts[key] = {}

        return formatted_counts
