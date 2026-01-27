import django_filters
from .models import Lease, MoveRequest


class LeaseFilters(django_filters.FilterSet):
    unit = django_filters.UUIDFilter(
        field_name="application__unit_id", lookup_expr="exact"
    )
    property = django_filters.UUIDFilter(
        field_name="application__unit__floor__building__location__property_id",
        lookup_expr="exact",
    )
    location = django_filters.UUIDFilter(
        field_name="application__unit__floor__building__location_id",
        lookup_expr="exact",
    )
    building = django_filters.UUIDFilter(
        field_name="application__unit__floor__building_id", lookup_expr="exact"
    )
    floor = django_filters.UUIDFilter(
        field_name="application__unit__floor_id", lookup_expr="exact"
    )

    class Meta:
        model = Lease
        fields = [
            "resident",
            "unit",
            "application",
            "lease_term",
            "status",
            "due_date",
            "start_date",
            "end_date",
            "property",
            "location",
            "building",
            "floor",
        ]


class MoveRequestFilter(django_filters.FilterSet):
    location = django_filters.CharFilter(
        field_name="unit__floor__building__location_id", lookup_expr="iexact"
    )
    building = django_filters.CharFilter(
        field_name="unit__floor__building_id", lookup_expr="exact"
    )
    property = django_filters.CharFilter(
        field_name="unit__floor__building__location__property_id", lookup_expr="iexact"
    )

    class Meta:
        model = MoveRequest
        fields = [
            "property",
            "building",
            "location",
            "status",
        ]
