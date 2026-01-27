import django_filters

from common.filters import StandardAPIFilter
from scheduling.models_v2 import VisitTypeAssignmentRequest


class VisitTypeAssignmentRequestFilter(StandardAPIFilter):
    display_id = django_filters.CharFilter(lookup_expr="icontains")
    method = django_filters.CharFilter(method="filter_by_method_csv")
    status = django_filters.CharFilter(method="filter_by_status_csv")

    class Meta:
        model = VisitTypeAssignmentRequest
        fields = (
            "id",
            "display_id",
            "method",
            "status",
        )

    def filter_by_status_csv(self, queryset, name, value):
        return self._filter_csv(
            queryset=queryset, name=name, value=value, attr="status"
        )

    def filter_by_method_csv(self, queryset, name, value):
        return self._filter_csv(
            queryset=queryset, name=name, value=value, attr="method"
        )
