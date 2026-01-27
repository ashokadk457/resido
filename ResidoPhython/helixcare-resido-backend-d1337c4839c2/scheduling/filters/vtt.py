import django_filters

from common.filters import StandardAPIFilter
from scheduling.models_v2 import VisitTypeTemplate


class VisitTypeTemplateFilter(StandardAPIFilter):
    display_id = django_filters.CharFilter(lookup_expr="icontains")
    speciality = django_filters.CharFilter(
        field_name="speciality__id", lookup_expr="icontains"
    )
    speciality_name = django_filters.CharFilter(
        field_name="speciality__specialization", lookup_expr="icontains"
    )

    class Meta:
        model = VisitTypeTemplate
        fields = ("id", "display_id", "speciality_name", "speciality", "active")
