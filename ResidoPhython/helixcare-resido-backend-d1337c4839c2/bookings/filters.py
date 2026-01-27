from django_filters import FilterSet, filters
from django_filters.filters import UUIDFilter
from .models import AmenitySlot, AmenityBlackoutPeriod, AmenityBooking


class AmenitySlotFilter(FilterSet):
    amenity = filters.UUIDFilter(field_name="amenity_id")
    date_from = filters.DateFilter(field_name="slot_date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="slot_date", lookup_expr="lte")

    class Meta:
        model = AmenitySlot
        fields = {
            "slot_date": ["exact", "gte", "lte"],
            "is_available": ["exact"],
            "active": ["exact"],
        }


class BlackoutPeriodFilter(FilterSet):
    property = UUIDFilter(field_name="amenity__building__location__property")
    location = UUIDFilter(field_name="amenity__building__location")
    building = UUIDFilter(field_name="amenity__building")
    amenity = filters.UUIDFilter(field_name="amenity_id")

    class Meta:
        model = AmenityBlackoutPeriod
        fields = {
            "amenity": ["exact"],
            "active": ["exact"],
            "start_date": ["gte", "lte"],
            "end_date": ["gte", "lte"],
        }


class BookingFilter(FilterSet):
    property = UUIDFilter(field_name="amenity__building__location__property")
    location = UUIDFilter(field_name="amenity__building__location")
    building = UUIDFilter(field_name="amenity__building")
    amenity = filters.UUIDFilter(field_name="amenity_id")
    tenant = filters.UUIDFilter(field_name="tenant_id")
    date_from = filters.DateFilter(field_name="booking_date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="booking_date", lookup_expr="lte")

    class Meta:
        model = AmenityBooking
        fields = {
            "amenity": ["exact"],
            "tenant": ["exact"],
            "status": ["exact"],
            "booking_date": ["exact", "gte", "lte"],
        }
