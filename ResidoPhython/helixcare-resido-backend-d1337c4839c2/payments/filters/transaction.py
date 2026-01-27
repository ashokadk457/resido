import django_filters

from common.filters import StandardAPIFilter
from payments.models import Payment


class TransactionFilter(StandardAPIFilter):
    display_id = django_filters.CharFilter(lookup_expr="icontains")
    order_id = django_filters.CharFilter(lookup_expr="icontains")
    bill_display_id = django_filters.CharFilter(
        field_name="bill__display_id", lookup_expr="icontains"
    )
    patient_id = django_filters.CharFilter(
        field_name="bill__patient__patient_id", lookup_expr="exact"
    )
    bill_patient_id = django_filters.CharFilter(
        field_name="bill__patient_id", lookup_expr="exact"
    )
    status = django_filters.CharFilter(method="filter_by_status_csv")
    transaction_type = django_filters.CharFilter(lookup_expr="exact")
    payment_method = django_filters.CharFilter(lookup_expr="exact")
    gateway_status = django_filters.CharFilter(lookup_expr="exact")
    gateway_recon_last_request_id = django_filters.CharFilter(lookup_expr="exact")
    patient_first_name = django_filters.CharFilter(
        field_name="bill__patient__first_name", lookup_expr="icontains"
    )
    patient_last_name = django_filters.CharFilter(
        field_name="bill__patient__last_name", lookup_expr="icontains"
    )
    practice_location_id = django_filters.UUIDFilter(
        field_name="bill__practice_location_id", lookup_expr="exact"
    )
    provider_first_name = django_filters.CharFilter(
        field_name="bill__encounter__created_by__first_name", lookup_expr="icontains"
    )
    provider_last_name = django_filters.CharFilter(
        field_name="bill__encounter__created_by__last_name", lookup_expr="icontains"
    )
    service_start_date = django_filters.DateFilter(
        field_name="bill__service_start_date", lookup_expr="exact"
    )
    service_end_date = django_filters.DateFilter(
        field_name="bill__service_end_date", lookup_expr="exact"
    )
    service_category = django_filters.CharFilter(
        field_name="bill__breakdown__category__id", lookup_expr="exact"
    )
    service_name = django_filters.CharFilter(
        field_name="bill__breakdown__type_of_service__id", lookup_expr="exact"
    )
    patient_dob = django_filters.DateFilter(
        field_name="bill__patient__dob", lookup_expr="exact"
    )
    patient_gender = django_filters.CharFilter(
        field_name="bill__patient__gender", lookup_expr="iexact"
    )
    plan_type = django_filters.CharFilter(
        field_name="payment_plan__type_of_interest", lookup_expr="exact"
    )
    plan_start_date = django_filters.DateFilter(
        field_name="payment_plan__start_date", lookup_expr="gte"
    )
    plan_end_date = django_filters.DateFilter(
        field_name="payment_plan__end_date", lookup_expr="lte"
    )

    class Meta:
        model = Payment
        fields = (
            "id",
            "display_id",
            "order_id",
            "bill_display_id",
            "patient_id",
            "bill_patient_id",
            "status",
            "transaction_type",
            "payment_method",
            "gateway_status",
            "gateway_recon_last_request_id",
            "patient_first_name",
            "patient_last_name",
            "practice_location_id",
            "provider_first_name",
            "provider_last_name",
            "service_start_date",
            "service_end_date",
            "service_category",
            "service_name",
            "patient_dob",
            "patient_gender",
            "plan_type",
        )

    def filter_by_status_csv(self, queryset, name, value):
        return self._filter_csv(
            queryset=queryset, name=name, value=value, attr="status"
        )
