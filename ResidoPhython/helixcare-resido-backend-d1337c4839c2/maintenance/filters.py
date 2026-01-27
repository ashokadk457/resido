from django_filters import rest_framework as filters
from .models import ServiceProvider, ServiceProviderReview, Maintenance


class ServiceProviderFilter(filters.FilterSet):
    phone = filters.CharFilter(field_name="phone", lookup_expr="icontains")
    contact_name = filters.CharFilter(
        field_name="contact_name", lookup_expr="icontains"
    )

    class Meta:
        model = ServiceProvider
        fields = ["active", "service_type", "contact_name", "phone", "id"]


class ServiceProviderReviewFilter(filters.FilterSet):
    class Meta:
        model = ServiceProviderReview
        fields = ["service_provider", "rating"]


class MaintenanceFilter(filters.FilterSet):
    display_id = filters.CharFilter(field_name="display_id", lookup_expr="icontains")

    class Meta:
        model = Maintenance
        fields = [
            "unit",
            "resident",
            "created_on",
            "service_priority",
            "service_type",
            "assignee",
            "preferred_vendor",
            "preferred_contact_method",
            "recurring_issue",
        ]
