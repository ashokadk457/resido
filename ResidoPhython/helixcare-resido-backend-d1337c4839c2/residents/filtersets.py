from django.db.models import Q
from django_filters import rest_framework as filters
from .models import Resident, ResidentDocument, ResidentEviction


class ResidentFilter(filters.FilterSet):
    first_name = filters.CharFilter(
        field_name="user__first_name", lookup_expr="icontains"
    )
    last_name = filters.CharFilter(
        field_name="user__last_name", lookup_expr="icontains"
    )
    date_of_birth = filters.CharFilter(
        field_name="user__date_of_birth", lookup_expr="icontains"
    )
    phone = filters.CharFilter(field_name="user__phone", lookup_expr="icontains")
    email = filters.CharFilter(field_name="user__email", lookup_expr="icontains")
    city = filters.CharFilter(field_name="user__city", lookup_expr="icontains")
    state = filters.CharFilter(field_name="user__state", lookup_expr="icontains")
    zipcode = filters.CharFilter(field_name="user__zipcode", lookup_expr="icontains")
    user_status = filters.CharFilter(field_name="user__status", lookup_expr="icontains")
    lease_status = filters.CharFilter(field_name="leases__status", lookup_expr="iexact")
    invitation_pending = filters.BooleanFilter(method="filter_invitation_pending")
    active = filters.BooleanFilter(method="filter_active")

    class Meta:
        model = Resident
        fields = [
            "resident_id",
            "first_name",
            "last_name",
            "date_of_birth",
            "phone",
            "email",
            "city",
            "state",
            "zipcode",
            "user_status",
            "lease_status",
        ]

    def filter_invitation_pending(self, queryset, name, value):
        """
        If invitation_pending=True, return only residents who haven't set their password yet.
        Residents with user.status='PENDING' are considered invitation pending.
        Once they set their password, status changes to 'APPROVED' and they move to Active.
        """
        if value:
            return queryset.filter(user__status="PENDING")
        return queryset

    def filter_active(self, queryset, name, value):
        """
        If active=True, return residents who either:
        - Have an active lease (leases__status='active'), OR
        - Have completed account activation by setting their password (user__status='APPROVED') - even with zero leases
        """
        if value:
            return queryset.filter(
                Q(leases__status="active") | Q(user__status="APPROVED")
            ).distinct()
        return queryset


class PatientChartsFilter(filters.FilterSet):
    first_name = filters.CharFilter(lookup_expr="icontains")
    last_name = filters.CharFilter(lookup_expr="icontains")
    dob = filters.DateFilter()
    encounter_id = filters.UUIDFilter(method="filter_by_encounter_id")
    encounter_start = filters.DateTimeFilter(method="filter_by_encounter_start")
    encounter_end = filters.DateTimeFilter(method="filter_by_encounter_end")
    conditions = filters.CharFilter(method="filter_by_conditions")
    procedures = filters.CharFilter(method="filter_by_procedures")

    class Meta:
        model = Resident
        fields = [
            "first_name",
            "last_name",
            "dob",
            "encounter_id",
            "encounter_start",
            "encounter_end",
            "conditions",
            "procedures",
        ]

    def filter_by_encounter_id(self, queryset, name, value):
        return queryset.filter(encounters__id=value)

    def filter_by_encounter_start(self, queryset, name, value):
        return queryset.filter(encounters__encounter_date__gte=value)

    def filter_by_encounter_end(self, queryset, name, value):
        return queryset.filter(encounters__encounter_date__lte=value)

    def filter_by_conditions(self, queryset, name, value):
        value = value.split(",")
        return queryset.filter(conditions__condition__icd_code__in=value)

    def filter_by_procedures(self, queryset, name, value):
        # this needs to be implemented when relation b/w patient & procedures is established
        return queryset


class ResidentDocumentFilter(filters.FilterSet):
    resident_name = filters.CharFilter(method="filter_resident_name")
    created_on = filters.DateFilter(field_name="created_on", lookup_expr="date")
    resident_id = filters.CharFilter(field_name="resident_id", lookup_expr="exact")

    class Meta:
        model = ResidentDocument
        fields = [
            "created_on",
            "document_type",
            "resident_id",
        ]

    def filter_resident_name(self, queryset, name, value):
        return queryset.filter(
            Q(resident__user__first_name__icontains=value)
            | Q(resident__user__last_name__icontains=value)
        )


class ResidentEvictionFilter(filters.FilterSet):
    resident_name = filters.CharFilter(method="filter_resident_name")
    notice_date = filters.DateFilter(field_name="notice_date", lookup_expr="date")
    status = filters.CharFilter(field_name="status", lookup_expr="icontains")
    notice_id = filters.CharFilter(field_name="notice_id", lookup_expr="icontains")
    select_reason = filters.CharFilter(method="filter_select_reason")

    class Meta:
        model = ResidentEviction
        fields = [
            "resident_name",
            "notice_date",
            "status",
            "notice_id",
            "select_reason",
        ]

    def filter_resident_name(self, queryset, name, value):
        return queryset.filter(
            Q(resident__user__first_name__icontains=value)
            | Q(resident__user__last_name__icontains=value)
        )

    def filter_select_reason(self, queryset, name, value):
        """
        Since select_reason is an ArrayField, use icontains to match any value inside it.
        """
        return queryset.filter(select_reason__icontains=value)
