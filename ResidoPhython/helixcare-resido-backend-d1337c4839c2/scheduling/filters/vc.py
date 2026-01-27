import django_filters

from common.filters import StandardAPIFilter
from scheduling.models_v2 import VisitCategory


class VisitCategoryFilter(StandardAPIFilter):
    display_id = django_filters.CharFilter(lookup_expr="icontains")
    speciality_name = django_filters.CharFilter(
        field_name="speciality__specialization", lookup_expr="icontains"
    )

    class Meta:
        model = VisitCategory
        fields = (
            "id",
            "display_id",
            "name",
            "speciality",
            "speciality_name",
            "active",
            "seeded",
        )
