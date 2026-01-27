import django_filters

from common.filters import StandardAPIFilter
from payments.models import Bill


class BillFilter(StandardAPIFilter):
    service = django_filters.CharFilter(lookup_expr="icontains")
    claim_id = django_filters.CharFilter(
        field_name="display_id", lookup_expr="icontains"
    )
    due_date = django_filters.DateFilter(
        field_name="due_date__date", lookup_expr="exact"
    )
    service_date = django_filters.DateFilter(
        field_name="service_date__date", lookup_expr="exact"
    )
    statement_date = django_filters.DateFilter(
        field_name="statement_date__date", lookup_expr="exact"
    )
    patient = django_filters.CharFilter(
        field_name="patient__patient_id", lookup_expr="exact"
    )
    patient_id = django_filters.CharFilter(
        field_name="patient__patient_id", lookup_expr="exact"
    )
    patient_first_name = django_filters.CharFilter(
        field_name="patient__first_name", lookup_expr="icontains"
    )
    patient_last_name = django_filters.CharFilter(
        field_name="patient__last_name", lookup_expr="icontains"
    )
    patient_gender = django_filters.CharFilter(
        field_name="patient__gender", lookup_expr="iexact"
    )
    patient_dob = django_filters.DateFilter(
        field_name="patient__dob", lookup_expr="exact"
    )
    ssn = django_filters.CharFilter(field_name="patient__ssn", lookup_expr="exact")
    type_of_service_category = django_filters.CharFilter(
        field_name="breakdown__category__name", lookup_expr="icontains"
    )
    type_of_service_sub_category = django_filters.CharFilter(
        field_name="breakdown__type_of_service__sub_category__name",
        lookup_expr="icontains",
    )
    status = django_filters.CharFilter(method="filter_by_status_csv")
    practice_location_id = django_filters.UUIDFilter(
        field_name="practice_location_id", lookup_expr="exact"
    )
    provider_first_name = django_filters.CharFilter(
        field_name="provider__user__first_name", lookup_expr="icontains"
    )
    provider_last_name = django_filters.CharFilter(
        field_name="provider__user__last_name", lookup_expr="icontains"
    )
    encounter_display_id = django_filters.CharFilter(
        field_name="encounter__display_id", lookup_expr="icontains"
    )
    service_start_date = django_filters.DateFilter(
        field_name="service_start_date__date", lookup_expr="exact"
    )
    service_end_date = django_filters.DateFilter(
        field_name="service_end_date__date", lookup_expr="exact"
    )
    payment_method = django_filters.CharFilter(
        field_name="payment_method", lookup_expr="iexact"
    )
    cancellation_reason = django_filters.CharFilter(
        field_name="cancellation_reason", lookup_expr="iexact"
    )
    statement_date__from = django_filters.DateFilter(
        field_name="statement_date", lookup_expr="gte"
    )
    statement_date__to = django_filters.DateFilter(
        field_name="statement_date", lookup_expr="lte"
    )
    paid_date = django_filters.DateFilter(
        field_name="paid_date__date", lookup_expr="exact"
    )
    service_category = django_filters.CharFilter(
        field_name="breakdown__category__id", lookup_expr="exact"
    )
    service_name = django_filters.CharFilter(
        field_name="breakdown__type_of_service__id", lookup_expr="exact"
    )
    plan_type = django_filters.CharFilter(
        field_name="pp__payment_plan__type_of_interest", lookup_expr="exact"
    )
    plan_start_date = django_filters.DateFilter(
        field_name="pp__payment_plan__start_date", lookup_expr="gte"
    )
    plan_end_date = django_filters.DateFilter(
        field_name="pp__payment_plan__end_date", lookup_expr="lte"
    )
    refund_date = django_filters.DateFilter(
        field_name="billrefundrequest__created_on", lookup_expr="date"
    )
    refund_reason = django_filters.CharFilter(
        field_name="billrefundrequest__refund_reason", lookup_expr="exact"
    )

    def filter_by_status_csv(self, queryset, name, value):
        return self._filter_csv(
            queryset=queryset, name=name, value=value, attr="status"
        )

    class Meta:
        model = Bill
        fields = (
            "id",
            "display_id",
            "service",
            "service_date",
            "statement_date",
            "due_date",
            "status",
            "patient",
            "patient_id",
            "patient_first_name",
            "patient_last_name",
            "patient_gender",
            "patient_dob",
            "ssn",
            "type_of_service_category",
            "type_of_service_sub_category",
            "service_category",
            "service_name",
            "practice_location_id",
            "provider_first_name",
            "provider_last_name",
            "encounter_display_id",
            "statement_date__from",
            "statement_date__to",
            "service_start_date",
            "service_end_date",
            "payment_method",
            "paid_date",
            "refund_date",
            "refund_reason",
            "cancellation_reason",
            "plan_type",
            "plan_start_date",
            "plan_end_date",
        )
