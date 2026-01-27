import django_filters

from common.filters import StandardAPIFilter
from scheduling.models_v2 import VisitType


class VisitTypeFilter(StandardAPIFilter):
    display_id = django_filters.CharFilter(lookup_expr="icontains")
    category_name = django_filters.CharFilter(
        field_name="category__name", lookup_expr="icontains"
    )
    speciality = django_filters.CharFilter(
        field_name="category__speciality__id", lookup_expr="icontains"
    )
    speciality_name = django_filters.CharFilter(
        field_name="category__speciality__specialization", lookup_expr="icontains"
    )
    category = django_filters.CharFilter(method="filter_by_category_csv")

    class Meta:
        model = VisitType
        fields = (
            "id",
            "display_id",
            "category_name",
            "speciality_name",
            "category",
            "speciality",
        )

    def filter_by_category_csv(self, queryset, name, value):
        return self._filter_csv(
            queryset=queryset, name=name, value=value, attr="category_id"
        )
