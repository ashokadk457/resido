from django_filters import rest_framework as filters

from data.models import Reason


class ReasonFilter(filters.FilterSet):
    display_id = filters.CharFilter(field_name="display_id", lookup_expr="icontains")
    category = filters.UUIDFilter(field_name="category__id")

    class Meta:
        model = Reason
        fields = [
            "display_id",
            "status",
            "category",
        ]
