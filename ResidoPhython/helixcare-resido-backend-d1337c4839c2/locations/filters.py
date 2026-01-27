from django_filters import rest_framework as filters
from .models import Unit, Amenity, Location, ParkingLevel, ParkingSlot


class LocationFilter(filters.FilterSet):
    customer = filters.UUIDFilter(field_name="property__customer_id")

    class Meta:
        model = Location
        fields = [
            "name",
            "short_name",
            "display_id",
            "property",
            "property__customer",
            "city",
            "state",
            "zipcode",
            "is_active",
            "customer",
        ]


class UnitFilter(filters.FilterSet):
    location = filters.CharFilter(
        field_name="floor__building__location_id", lookup_expr="exact"
    )
    tenant = filters.CharFilter(
        field_name="application__lease__resident_id", lookup_expr="exact"
    )
    building = filters.CharFilter(field_name="floor__building_id", lookup_expr="exact")

    class Meta:
        model = Unit
        fields = [
            "floor",
            "is_furnished",
            "is_furnished",
            "status",
            "unit_type",
            "display_id",
            "is_pet_allowed",
            "is_service_animal_allowed",
            "location",
            "building",
            "tenant",
        ]


class AmenityFilter(filters.FilterSet):
    location = filters.CharFilter(
        field_name="building__location_id", lookup_expr="iexact"
    )
    property = filters.CharFilter(
        field_name="building__location__property_id", lookup_expr="iexact"
    )

    class Meta:
        model = Amenity
        fields = [
            "active",
            "building",
            "location",
            "property",
        ]


class ParkingLevelFilter(filters.FilterSet):
    location = filters.UUIDFilter(field_name="building__location_id")
    property = filters.UUIDFilter(field_name="building__location__property_id")
    building = filters.UUIDFilter(field_name="building__id")

    class Meta:
        model = ParkingLevel
        fields = [
            "is_active",
            "building",
            "location",
            "property",
        ]


class ParkingSlotFilter(filters.FilterSet):
    location = filters.UUIDFilter(
        field_name="zone__parking_level__building__location_id"
    )
    property = filters.UUIDFilter(
        field_name="zone__parking_level__building__location__property_id"
    )
    building = filters.UUIDFilter(field_name="zone__parking_level__building__id")

    class Meta:
        model = ParkingSlot
        fields = [
            "is_active",
            "building",
            "location",
            "property",
        ]


class MyUnitFilter(filters.FilterSet):
    property = filters.UUIDFilter(field_name="floor__building__location__property_id")
    location = filters.UUIDFilter(field_name="floor__building__location_id")
    building = filters.UUIDFilter(field_name="floor__building__id")
    status = filters.CharFilter(field_name="lease__status", lookup_expr="iexact")

    class Meta:
        model = Unit
        fields = [
            "property",
            "location",
            "building",
            "status",
        ]
