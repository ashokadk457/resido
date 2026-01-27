from calendar import month_abbr
from django.db.models import Q, Count, Avg, F
from django.db.models.functions import Coalesce, TruncMonth
from datetime import datetime, date
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from lease.models import Lease
from locations.models import Unit
from maintenance.models import Maintenance

from common.response import StandardAPIResponse
from django.core.exceptions import FieldDoesNotExist

from analytics.mixins import (
    DashboardQueryMixin,
    standard_api_exception_guard,
)
from common.utils.currency import get_currency_codes


class OutstandingBalanceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        currency_symbol = get_currency_codes("USD")
        data = {
            "title": "Outstanding Balance",
            "summary": {
                "value": 22000.00,
                "currency": currency_symbol,
                "delta": {"value": 1.3, "direction": "up", "text": "VS Last week"},
            },
            "quick_stats": [
                {"label": "Completed", "value": 1279},
                {"label": "Overdue", "value": 800},
            ],
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class NewLeasesSignedAPIView(DashboardQueryMixin, APIView):
    permission_classes = [IsAuthenticated]

    PROPERTY_PATH = "unit__floor__building__location__property_id"
    LOCATION_PATH = "unit__floor__building__location_id"

    @standard_api_exception_guard
    def get(self, request):
        f = self.parse_filters(request, allow_defaults=True)

        date_field = f["date_field"] or "start_date"
        self.ensure_model_has_field(Lease, date_field)

        qs = self.scope_for_current_user(Lease.objects.all(), request.user)
        qs = self.apply_property_location_filters(
            qs,
            property_ids=f["property_ids"],
            location_ids=f["location_ids"],
        )

        current_q = self.q_for_range(Lease, date_field, f["start"], f["end"])
        previous_q = self.q_for_range(Lease, date_field, f["prev_start"], f["prev_end"])

        expiring_to = f["end"] + (f["end"] - f["start"])
        expiring_q = self.q_for_after_until(Lease, "end_date", f["end"], expiring_to)

        agg = qs.aggregate(
            current=Count("id", filter=current_q & Q(status__in=self.SIGNED_STATUSES)),
            previous=Count(
                "id", filter=previous_q & Q(status__in=self.SIGNED_STATUSES)
            ),
            pending=Count("id", filter=Q(status__in=self.PENDING_STATUSES)),
            expiring=Count("id", filter=expiring_q),
        )

        current = int(agg.get("current") or 0)
        previous = int(agg.get("previous") or 0)
        delta, direction = self.compute_delta_percent(current, previous)

        data = {
            "title": "New Leases Signed",
            "meta": self.build_meta(
                start=f["start"],
                end=f["end"],
                prev_start=f["prev_start"],
                prev_end=f["prev_end"],
                extra={
                    "filters": {
                        "property_ids": f["property_ids"],
                        "location_ids": f["location_ids"],
                    },
                    "date_field": date_field,
                    "defaults_applied": f["defaults_applied"],
                },
            ),
            "summary": {
                "value": current,
                "delta": {
                    "value": delta,
                    "direction": direction,
                    "text": "VS Last week",
                },
            },
            "quick_stats": [
                {"label": "Lease Expiration", "value": int(agg.get("expiring") or 0)},
                {"label": "Pending Leases", "value": int(agg.get("pending") or 0)},
            ],
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class OpenWorkOrdersCardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Open Work Orders",
            "summary": {
                "value": 199,
                "delta": {"value": -1.3, "direction": "down", "text": "VS Last week"},
            },
            "quick_stats": [
                {"label": "In Progress", "value": 149},
                {"label": "Assigned", "value": 99},
            ],
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class SupportTicketsRaisedAPIView(DashboardQueryMixin, APIView):
    permission_classes = [IsAuthenticated]

    PROPERTY_PATH = "unit__floor__building__location__property_id"
    LOCATION_PATH = "unit__floor__building__location_id"

    @standard_api_exception_guard
    def get(self, request):
        f = self.parse_filters(request, allow_defaults=True)
        date_field = f["date_field"] or "reported_date"
        self.ensure_model_has_field(Maintenance, date_field)

        qs = self.scope_for_current_user(Maintenance.objects.all(), request.user)
        qs = self.apply_property_location_filters(
            qs,
            property_ids=f["property_ids"],
            location_ids=f["location_ids"],
        )

        current_q = self.q_for_range(Maintenance, date_field, f["start"], f["end"])
        previous_q = self.q_for_range(
            Maintenance, date_field, f["prev_start"], f["prev_end"]
        )

        agg = qs.aggregate(
            current=Count("id", filter=current_q),
            previous=Count("id", filter=previous_q),
            in_progress=Count(
                "id", filter=self.any_status_q("status", self.IN_PROGRESS_STATUSES)
            ),
            resolved=Count(
                "id", filter=self.any_status_q("status", self.RESOLVED_STATUSES)
            ),
        )

        delta, direction = self.compute_delta_percent(
            agg["current"] or 0, agg["previous"] or 0
        )

        data = {
            "title": "Support Tickets Raised",
            "meta": self.build_meta(
                start=f["start"],
                end=f["end"],
                prev_start=f["prev_start"],
                prev_end=f["prev_end"],
                extra={
                    "filters": {
                        "property_ids": f["property_ids"],
                        "location_ids": f["location_ids"],
                    },
                    "date_field": date_field,
                    "defaults_applied": f["defaults_applied"],
                },
            ),
            "summary": {
                "value": agg["current"] or 0,
                "delta": {
                    "value": delta,
                    "direction": direction,
                    "text": "VS Last week",
                },
            },
            "quick_stats": [
                {"label": "In Progress", "value": agg["in_progress"] or 0},
                {"label": "Resolved", "value": agg["resolved"] or 0},
            ],
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class VacancyRateAPIView(DashboardQueryMixin, APIView):
    permission_classes = [IsAuthenticated]

    PROPERTY_PATH = "floor__building__location__property_id"
    LOCATION_PATH = "floor__building__location_id"

    def get(self, request):
        active_view = request.query_params.get("active_view") or "by_property"
        f = self.parse_filters(request, allow_defaults=True)
        date_field = f["date_field"] or "created_on"
        self.ensure_model_has_field(Unit, date_field)

        qs = self.scope_for_current_user(Unit.objects.all(), request.user)
        qs = self.apply_property_location_filters(
            qs,
            property_ids=f["property_ids"],
            location_ids=f["location_ids"],
        )

        current_q = self.q_for_range(Unit, date_field, f["start"], f["end"])
        previous_q = self.q_for_range(Unit, date_field, f["prev_start"], f["prev_end"])
        agg = qs.aggregate(
            current=Count("id", filter=current_q),
            previous=Count("id", filter=previous_q),
            vacant_units=Count(
                "id",
                filter=current_q & self.any_status_q("status", self.VACANT_STATUSES),
            ),
        )
        delta, direction = self.compute_delta_percent(
            agg["current"] or 0, agg["previous"] or 0
        )
        unit_names, unit_counts = self.get_unit_chart_data(qs, current_q, active_view)
        data = {
            "title": "Vacancy Rate",
            "summary": {
                "value": agg["vacant_units"] or 0,
                "delta": {
                    "value": delta,
                    "direction": direction,
                    "text": "VS Last week",
                },
            },
            "active_view": active_view,
            "available_views": ["by_property", "by_buildings", "by_unit_type"],
            "chart": {
                "type": "line",
                "categories": unit_names,
                "series": [{"name": "Vacancies", "data": unit_counts}],
                "tooltips": True,
            },
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class OccupancyRateAPIView(DashboardQueryMixin, APIView):
    permission_classes = [IsAuthenticated]

    PROPERTY_PATH = "floor__building__location__property_id"
    LOCATION_PATH = "floor__building__location_id"

    def get(self, request):
        f = self.parse_filters(request, allow_defaults=True)
        date_field = f["date_field"] or "created_on"
        self.ensure_model_has_field(Unit, date_field)

        qs = self.scope_for_current_user(Unit.objects.all(), request.user)
        qs = self.apply_property_location_filters(
            qs,
            property_ids=f["property_ids"],
            location_ids=f["location_ids"],
        )

        current_q = self.q_for_range(Unit, date_field, f["start"], f["end"])
        previous_q = self.q_for_range(Unit, date_field, f["prev_start"], f["prev_end"])
        agg = qs.aggregate(
            current=Count("id", filter=current_q),
            previous=Count("id", filter=previous_q),
            occupied_units=Count(
                "id",
                filter=current_q & self.any_status_q("status", self.OCCUPIED_STATUSES),
            ),
            vacant_units=Count(
                "id",
                filter=current_q & self.any_status_q("status", self.VACANT_STATUSES),
            ),
        )
        delta, direction = self.compute_delta_percent(
            agg["current"] or 0, agg["previous"] or 0
        )

        current = agg["current"] or 0
        occupied = agg["occupied_units"] or 0
        vacant = agg["vacant_units"] or 0

        if current > 0:
            occupied_pct = round((occupied / current) * 100.0, 1)
            available_pct = round((vacant / current) * 100.0, 1)
        else:
            occupied_pct = 0
            available_pct = 0
        data = {
            "title": "Occupancy Rate",
            "summary": {
                "rate_pct": occupied_pct,
                "delta": {
                    "value": delta,
                    "direction": direction,
                    "text": "VS Last week",
                },
            },
            "total_units": agg["current"] or 0,
            "slices": [
                {
                    "label": "Occupied Units",
                    "value": agg["occupied_units"] or 0,
                    "pct": occupied_pct,
                },
                {
                    "label": "Available Units",
                    "value": agg["vacant_units"] or 0,
                    "pct": available_pct,
                },
            ],
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class RevenueLeakageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        currency_symbol = get_currency_codes("USD")
        data = {
            "title": "Revenue Leakage",
            "summary": {
                "value": 129000,
                "currency": currency_symbol,
                "delta": {"value": 1.3, "direction": "up", "text": "VS Last week"},
            },
            "kpis": [
                {"label": "PMR", "value": 1250000, "currency": currency_symbol},
                {
                    "label": "Cash Collected",
                    "value": 1121000,
                    "currency": currency_symbol,
                },
            ],
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class LeaseRenewalRateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Leases Renewal Rate",
            "summary": {
                "value": 220,
                "delta": {"value": 1.3, "direction": "up", "text": "VS Last week"},
            },
            "pie": {
                "slices": [
                    {"label": "Renewed", "pct": 70},
                    {"label": "Expiring", "pct": 30},
                ]
            },
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class LeaseDocumentStatusAPIView(DashboardQueryMixin, APIView):
    permission_classes = [IsAuthenticated]
    PROPERTY_PATH = "unit__floor__building__location__property_id"
    LOCATION_PATH = "unit__floor__building__location_id"

    def get(self, request):
        f = self.parse_filters(request, allow_defaults=True)

        date_field = f["date_field"] or "start_date"
        self.ensure_model_has_field(Lease, date_field)

        qs = self.scope_for_current_user(Lease.objects.all(), request.user)
        qs = self.apply_property_location_filters(
            qs,
            property_ids=f["property_ids"],
            location_ids=f["location_ids"],
        )

        current_q = self.q_for_range(Lease, date_field, f["start"], f["end"])
        previous_q = self.q_for_range(Lease, date_field, f["prev_start"], f["prev_end"])

        expiring_to = f["end"] + (f["end"] - f["start"])
        expiring_q = self.q_for_after_until(Lease, "end_date", f["end"], expiring_to)

        agg = qs.aggregate(
            current=Count("id", filter=current_q & Q(status__in=self.SIGNED_STATUSES)),
            previous=Count(
                "id", filter=previous_q & Q(status__in=self.SIGNED_STATUSES)
            ),
            pending=Count("id", filter=Q(status__in=self.PENDING_STATUSES)),
            previous_for_pending=Count(
                "id", filter=previous_q & Q(status__in=self.PENDING_STATUSES)
            ),
            expired=Count("id", filter=expiring_q),
            previous_for_expired=Count("id", filter=previous_q & expiring_q),
        )
        current = int(agg.get("current") or 0)
        previous = int(agg.get("previous") or 0)
        pending = int(agg.get("pending") or 0)
        previous_for_pending = int(agg.get("previous_for_pending") or 0)
        expired = int(agg.get("expired") or 0)
        previous_for_expiring = int(agg.get("previous_for_expired") or 0)
        new_delta, new_direction = self.compute_delta_percent(current, previous)
        pending_delta, pending_direction = self.compute_delta_percent(
            pending, previous_for_pending
        )
        expired_delta, expired_direction = self.compute_delta_percent(
            expired, previous_for_expiring
        )
        anno = (
            qs.annotate(month=TruncMonth("created_on"))
            .values("month")
            .annotate(
                new_count=Count(
                    "id", filter=current_q & Q(status__in=self.SIGNED_STATUSES)
                ),
                pending_count=Count("id", filter=Q(status__in=self.PENDING_STATUSES)),
                expired_count=Count("id", filter=expiring_q),
            )
            .order_by("month")
        )
        months = [month_abbr[item["month"].month] for item in anno]

        # Extract each status as a data series
        new_leases_data = [item["new_count"] for item in anno]
        pending_leases_data = [item["pending_count"] for item in anno]
        expired_leases_data = [item["expired_count"] for item in anno]
        data = {
            "title": "Lease Document Status",
            "kpis": [
                {
                    "label": "Lease Expiration",
                    "value": expired,
                    "delta": {
                        "value": expired_delta,
                        "direction": expired_direction,
                        "text": "VS Last week",
                    },
                },
                {
                    "label": "New Leases Signed",
                    "value": current,
                    "delta": {
                        "value": new_delta,
                        "direction": new_direction,
                        "text": "VS Last week",
                    },
                },
                {
                    "label": "Pending Leases",
                    "value": pending,
                    "delta": {
                        "value": pending_delta,
                        "direction": pending_direction,
                        "text": "VS Last week",
                    },
                },
            ],
            "chart": {
                "type": "line",
                "x": months,
                "series": [
                    {
                        "name": "Lease Expiration",
                        "data": expired_leases_data,
                    },
                    {
                        "name": "New Leases Signed",
                        "data": new_leases_data,
                    },
                    {
                        "name": "Pending Leases",
                        "data": pending_leases_data,
                    },
                ],
            },
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class PaymentsCollectedAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Total Payments Collected",
            "summary": {
                "value": 150000,
                "currency": "USD",
                "delta": {"value": 13, "direction": "up", "text": "VS Last month"},
            },
            "chart": {
                "type": "line",
                "x": [
                    "Mar 20",
                    "Mar 23",
                    "Mar 26",
                    "Mar 29",
                    "Apr 1",
                    "Apr 4",
                    "Apr 7",
                    "Apr 10",
                    "Apr 13",
                    "Apr 16",
                    "Apr 19",
                ],
                "series": [
                    {
                        "name": "Collections",
                        "data": [250, 400, 300, 260, 200, 230, 260, 220, 210, 240, 300],
                    }
                ],
                "y_unit": "K",
            },
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class PaymentSuccessRateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Payment Success Rate",
            "summary": {
                "value_pct": 95.5,
                "delta": {"value": 1.3, "direction": "up", "text": "VS Last week"},
            },
            "breakdown": [
                {"label": "Online Portal", "value_pct": 60.0},
                {"label": "In-Person", "value_pct": 35.5},
            ],
            "gauge": {"min": 0, "max": 100, "value": 95.5},
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class RentCollectionRateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Rent Collection Rate",
            "summary": {"value_pct": 65},
            "pie": {
                "slices": [
                    {"label": "On-Time", "pct": 60},
                    {"label": "Late", "pct": 35},
                    {"label": "Unpaid", "pct": 5},
                ]
            },
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class AgedReceivablesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Outstanding Balances Aged Receivables",
            "summary": {"value": 200000, "currency": "USD"},
            "chart": {
                "type": "bar-stacked",
                "categories": ["0–30", "31–60", "61–90", "90+ days"],
                "series": [
                    {"name": "Property", "data": [100, 150, 200, 250]},
                    {"name": "Renter", "data": [80, 120, 160, 210]},
                ],
            },
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class ExpenseBreakdownAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Expense Breakdown",
            "slices": [
                {"label": "Utilities", "pct": 30},
                {"label": "Maintenance", "pct": 30},
                {"label": "Payroll", "pct": 25},
                {"label": "Taxes", "pct": 15},
            ],
            "legend": [
                {"label": "Utilities", "value": 100000},
                {"label": "Maintenance", "value": 50000},
                {"label": "Payroll", "value": 120000},
                {"label": "Taxes", "value": 100000},
            ],
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class WorkOrdersStatsAPIView(DashboardQueryMixin, APIView):
    permission_classes = [IsAuthenticated]
    PROPERTY_PATH = "unit__floor__building__location__property_id"
    LOCATION_PATH = "unit__floor__building__location_id"
    OPEN_STATUSES = ("open",)
    IN_PROGRESS_STATUSES = ("in_progress", "approved")
    RESOLVED_STATUSES = ("completed", "rejected")

    def get(self, request):
        f = self.parse_filters(request, allow_defaults=True)
        date_field = f["date_field"] or "reported_date"
        self.ensure_model_has_field(Maintenance, date_field)

        qs = self.scope_for_current_user(Maintenance.objects.all(), request.user)
        qs = self.apply_property_location_filters(
            qs,
            property_ids=f["property_ids"],
            location_ids=f["location_ids"],
        )
        current_q = self.q_for_range(Maintenance, date_field, f["start"], f["end"])
        previous_q = self.q_for_range(
            Maintenance, date_field, f["prev_start"], f["prev_end"]
        )

        agg = qs.aggregate(
            current=Count("id", filter=current_q),
            previous=Count("id", filter=previous_q),
            opened=Count(
                "id", filter=current_q & self.any_status_q("status", self.OPEN_STATUSES)
            ),
            in_progress=Count(
                "id",
                filter=current_q
                & self.any_status_q("status", self.IN_PROGRESS_STATUSES),
            ),
            resolved=Count(
                "id",
                filter=current_q & self.any_status_q("status", self.RESOLVED_STATUSES),
            ),
        )

        delta, direction = self.compute_delta_percent(
            agg["current"] or 0, agg["previous"] or 0
        )

        current = agg.get("current", 0) or 0
        opened = agg.get("opened", 0) or 0
        in_progress = agg.get("in_progress", 0) or 0
        resolved = agg.get("resolved", 0) or 0

        opened_pct = self.percent(opened, current)
        in_progress_pct = self.percent(in_progress, current)
        resolved_pct = self.percent(resolved, current)
        data = {
            "title": "Work Orders",
            "summary": {
                "total": agg["current"] or 0,
                "delta": {
                    "value": delta,
                    "direction": direction,
                    "text": "VS Last week",
                },
            },
            "status_bars": [
                {"label": "Open", "value": agg["opened"] or 0},
                {"label": "In Progress", "value": agg["in_progress"] or 0},
                {"label": "Closed", "value": agg["resolved"] or 0},
                {"label": "Assigned", "value": agg["in_progress"] or 0},
            ],
            "pie": {
                "slices": [
                    {"label": "Open", "pct": opened_pct},
                    {"label": "In Progress", "pct": in_progress_pct},
                    {"label": "Closed", "pct": resolved_pct},
                    {"label": "Assigned", "pct": in_progress_pct},
                ]
            },
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class RecurringMaintenanceTasksAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Recurring Maintenance Tasks",
            "summary": {
                "total": 658,
                "delta": {"value": -1.3, "direction": "down", "text": "VS Last week"},
            },
            "chart": {
                "type": "bar",
                "categories": [
                    "HVAC",
                    "Pest Control",
                    "Plumbing",
                    "Electrical",
                    "Cleaning",
                ],
                "data": [160, 100, 180, 170, 80],
            },
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class MaintenanceCostTrendsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Maintenance Cost Trends",
            "subtitle": "Most Vulnerable & High-Expense Units by Property",
            "filter": {"properties": ["Vertex Luxury Flats", "… +2 more"]},
            "chart": {
                "type": "line",
                "x": [
                    "Mar 20",
                    "Mar 23",
                    "Mar 26",
                    "Mar 29",
                    "Apr 1",
                    "Apr 4",
                    "Apr 7",
                    "Apr 10",
                    "Apr 13",
                    "Apr 16",
                    "Apr 19",
                ],
                "series": [
                    {
                        "name": "Vertex Luxury Flats",
                        "data": [
                            15000,
                            18000,
                            16000,
                            14000,
                            13000,
                            12000,
                            11000,
                            15000,
                            17000,
                            16000,
                            22000,
                        ],
                    },
                    {
                        "name": "Benchmark",
                        "data": [
                            12000,
                            13000,
                            14000,
                            13500,
                            14500,
                            15000,
                            14000,
                            14500,
                            15000,
                            14800,
                            16000,
                        ],
                    },
                ],
                "y_unit": "K",
            },
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class RenterSatisfactionScoreAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Renter Satisfaction Score",
            "summary": {
                "value": 4.5,
                "scale": 5,
                "delta": {"value": -1.3, "direction": "down", "text": "VS Last week"},
            },
            "bars": [
                {"label": "Very Satisfied", "value": 320},
                {"label": "Satisfied", "value": 260},
                {"label": "Neutral", "value": 180},
                {"label": "Unsatisfied", "value": 110},
                {"label": "Very Unsatisfied", "value": 70},
            ],
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class TopComplaintsLoggedAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Top Complaints Logged",
            "summary": {
                "delta": {"value": -1.3, "direction": "down", "text": "VS Last week"}
            },
            "bars": [
                {"label": "Delayed Response", "value": 520},
                {"label": "Poor Communications", "value": 460},
                {"label": "Maintenance Delay", "value": 350},
                {"label": "Billing Issues", "value": 240},
            ],
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class InsuranceExpiryAlertsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Insurance Expiry Alerts by Property and Renters",
            "summary": {
                "total": 998,
                "delta": {"value": 1.3, "direction": "up", "text": "VS Last week"},
            },
            "chart": {
                "type": "bar-stacked",
                "categories": [
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                ],
                "series": [
                    {
                        "name": "Property",
                        "data": [
                            50,
                            80,
                            110,
                            60,
                            250,
                            140,
                            110,
                            90,
                            120,
                            140,
                            160,
                            180,
                        ],
                    },
                    {
                        "name": "Renter",
                        "data": [
                            120,
                            40,
                            60,
                            50,
                            180,
                            120,
                            150,
                            210,
                            180,
                            160,
                            200,
                            220,
                        ],
                    },
                ],
            },
            "legend": [{"label": "Property"}, {"label": "Renter"}],
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class InspectionReportsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Inspection Reports",
            "summary": {
                "value": 1879,
                "delta": {"value": 1.3, "direction": "up", "text": "VS Last week"},
            },
            "slices": [
                {"label": "Completed", "value": 420, "pct": 48},
                {"label": "Overdue", "value": 100, "pct": 12},
                {"label": "Remaining", "value": 359, "pct": 40},
            ],
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class UnitTypeDistributionAPIView(DashboardQueryMixin, APIView):
    permission_classes = [IsAuthenticated]

    PROPERTY_PATH = "floor__building__location__property_id"
    LOCATION_PATH = "floor__building__location_id"

    def get(self, request):
        f = self.parse_filters(request)

        qs = self.scope_for_current_user(Unit.objects.all(), request.user)
        qs = self.apply_property_location_filters(
            qs,
            property_ids=f["property_ids"],
            location_ids=f["location_ids"],
        )

        rows = list(
            qs.values("floor_plan").annotate(total=Count("id")).order_by("floor_plan")
        )
        # choices = dict(getattr(Unit._meta.get_field("unit_type"), "choices", []) or [])
        total_units = sum(int(r["total"]) for r in rows) or 0

        slices = []
        for r in rows:
            code = r["floor_plan"]
            cnt = int(r["total"] or 0)
            pct = round((cnt / total_units) * 100.0, 1) if total_units else 0.0
            slices.append(
                {
                    "label": code,
                    "value": cnt,
                    "pct": pct,
                    "code": code,
                }
            )

        data = {
            "title": "Unit Types Distribution",
            "meta": self.build_meta(
                start=f["start"],
                end=f["end"],
                prev_start=f["prev_start"],
                prev_end=f["prev_end"],
                extra={
                    "filters": {
                        "property_ids": f["property_ids"],
                        "location_ids": f["location_ids"],
                    }
                },
            ),
            "summary": {"total_units": total_units},
            "slices": slices,
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class TotalUnitsByPropertyAPIView(DashboardQueryMixin, APIView):
    permission_classes = [IsAuthenticated]
    PROPERTY_PATH = "floor__building__location__property_id"
    LOCATION_PATH = "floor__building__location_id"

    def _first_ok(self, qs, candidates: tuple[str, ...]) -> str | None:
        """
        Return the first field path that works with qs.values(). This safely
        detects valid relation paths across heterogeneous schemas.
        """
        for path in candidates:
            try:
                qs.values(path)[:1]
                return path
            except Exception:
                continue
        return None

    @standard_api_exception_guard
    def get(self, request):
        f = self.parse_filters(request, allow_defaults=True)

        qs = self.scope_for_current_user(Unit.objects.all(), request.user)
        qs = self.apply_property_location_filters(
            qs,
            property_ids=f["property_ids"],
            location_ids=f["location_ids"],
        )

        prop_id_path = (
            self._first_ok(
                qs,
                (
                    "floor__building__location__property_id",
                    "floor__building__location__property__id",
                    "property_id",
                    "property__id",
                ),
            )
            or "id"
        )

        prop_name_path = self._first_ok(
            qs,
            (
                "floor__building__location__property__name",
                "property__name",
                "floor__building__name",
                "building__name",
            ),
        )

        values_fields = (
            (prop_id_path,) if not prop_name_path else (prop_id_path, prop_name_path)
        )
        rows = list(
            qs.values(*values_fields)
            .annotate(total=Count("id"))
            .order_by(*values_fields)
        )

        categories, data_vals = [], []
        for r in rows:
            label = r.get(prop_name_path) if prop_name_path else None
            if label in (None, ""):
                label = str(r.get(prop_id_path) or "Unknown")
            categories.append(label)
            data_vals.append(int(r.get("total") or 0))

        total_units = sum(data_vals) or 0

        current_new = previous_new = 0
        try:
            Unit._meta.get_field("created_at")
            current_new = qs.filter(
                self.q_for_range(Unit, "created_at", f["start"], f["end"])
            ).count()
            previous_new = qs.filter(
                self.q_for_range(Unit, "created_at", f["prev_start"], f["prev_end"])
            ).count()
        except FieldDoesNotExist:
            pass

        delta, direction = self.compute_delta_percent(current_new, previous_new)

        data = {
            "title": "Total Units by Property",
            "meta": self.build_meta(
                start=f["start"],
                end=f["end"],
                prev_start=f["prev_start"],
                prev_end=f["prev_end"],
                extra={
                    "filters": {
                        "property_ids": f["property_ids"],
                        "location_ids": f["location_ids"],
                    },
                    "group_by": {
                        "id_field": prop_id_path,
                        "name_field": prop_name_path,
                    },
                    "defaults_applied": f["defaults_applied"],
                },
            ),
            "summary": {
                "total_units": total_units,
                "delta": {
                    "value": delta,
                    "direction": direction,
                    "text": "VS Last week",
                },
            },
            "chart": {"type": "bar", "categories": categories, "data": data_vals},
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class AverageRentPerUnitTypeAPIView(DashboardQueryMixin, APIView):
    permission_classes = [IsAuthenticated]

    def _q_any_status(self, field: str, statuses: tuple[str, ...]) -> Q:
        q = Q()
        for s in statuses:
            q |= Q(**{f"{field}__iexact": s})
        return q

    def _scope_props_locs(
        self, qs, *, property_ids: list[str] | None, location_ids: list[str] | None
    ):
        """
        Scope Units by property/location, trying common relationship paths so
        it survives minor schema differences.
        """
        if property_ids:
            for path in (
                "floor__building__property_id",
                "floor__building__property__id",
                "property_id",
                "property__id",
            ):
                try:
                    qs = qs.filter(**{f"{path}__in": property_ids})
                    break
                except Exception:
                    continue

        if location_ids:
            for path in (
                "floor__building__location_id",
                "floor__building__location__id",
                "location_id",
                "location__id",
            ):
                try:
                    qs = qs.filter(**{f"{path}__in": location_ids})
                    break
                except Exception:
                    continue

        return qs

    def get(self, request):
        prop_ids = [
            p.strip()
            for p in (request.query_params.get("property_ids") or "").split(",")
            if p.strip()
        ]
        loc_ids = [
            l_data.strip()
            for l_data in (request.query_params.get("location_ids") or "").split(",")
            if l_data.strip()
        ]
        statuses = [
            s.strip()
            for s in (request.query_params.get("status") or "").split(",")
            if s.strip()
        ]
        unit_types = [
            u.strip()
            for u in (request.query_params.get("unit_types") or "").split(",")
            if u.strip()
        ]
        furnished = (request.query_params.get("furnished") or "").strip().lower()
        currency = (request.query_params.get("currency") or "USD").strip().upper()

        # Read date range from query params (start/end or from/to)
        date_from_str = request.query_params.get("start") or request.query_params.get(
            "from"
        )
        date_to_str = request.query_params.get("end") or request.query_params.get("to")

        qs = Unit.objects.all()
        qs = self._scope_props_locs(
            qs, property_ids=prop_ids or None, location_ids=loc_ids or None
        )

        if statuses:
            qs = qs.filter(self._q_any_status("status", tuple(statuses)))

        if unit_types:
            qs = qs.filter(unit_type__in=unit_types)

        if furnished == "true":
            price_expr = F("furnished_price")
            qs = qs.filter(furnished_price_currency=currency)
        elif furnished == "false":
            price_expr = F("unfurnished_price")
            qs = qs.filter(unfurnished_price_currency=currency)
        else:
            price_expr = Coalesce(F("furnished_price"), F("unfurnished_price"))
            qs = qs.filter(
                Q(furnished_price_currency=currency)
                | Q(unfurnished_price_currency=currency)
            )

        try:
            today = date.today()
            start_of_year = date(today.year, 1, 1)

            # Parse dates if provided, otherwise use defaults
            if date_from_str:
                try:
                    filter_start = datetime.strptime(date_from_str, "%m/%d/%Y").date()
                except (ValueError, TypeError):
                    filter_start = start_of_year
            else:
                filter_start = start_of_year

            if date_to_str:
                try:
                    filter_end = datetime.strptime(date_to_str, "%m/%d/%Y").date()
                except (ValueError, TypeError):
                    filter_end = today
            else:
                filter_end = today

            rows = (
                qs.filter(created_on__range=(filter_start, filter_end))
                .values("floor_plan")
                .annotate(avg_rent=Avg(price_expr))
                .order_by("floor_plan")
            )
        except Exception:
            rows = []
            filter_start = start_of_year
            filter_end = today

        choices_map = dict(
            getattr(Unit._meta.get_field("floor_plan"), "choices", []) or []
        )

        categories: list[str] = []
        data: list[float] = []

        for r in rows:
            code = r.get("floor_plan")
            label = choices_map.get(code, code) or "Unknown"
            avg_val = r.get("avg_rent") or 0
            try:
                avg_num = (
                    float(avg_val.amount)
                    if hasattr(avg_val, "amount")
                    else float(avg_val)
                )
            except Exception:
                avg_num = 0.0
            categories.append(str(label))
            data.append(round(avg_num, 2))

        # Convert currency code to symbol
        currency_symbol = get_currency_codes(currency)

        payload = {
            "title": "Average Rent per Unit Type",
            "chart": {
                "type": "bar",
                "categories": categories,
                "data": data,
                "date": [filter_start, filter_end],
                "currency": currency_symbol,
            },
        }

        return StandardAPIResponse(data=payload, status=status.HTTP_200_OK)


class UpcomingVacanciesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Upcoming Vacancies",
            "summary": {
                "value": 263,
                "delta": {"value": 1.3, "direction": "up", "text": "VS Last week"},
            },
            "filter": {"properties": ["Vertex Luxury Flats", "+2 more"]},
            "chart": {
                "type": "line",
                "x": [
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                ],
                "series": [
                    {
                        "name": "Vacancies",
                        "data": [
                            90,
                            110,
                            130,
                            150,
                            140,
                            120,
                            100,
                            110,
                            130,
                            150,
                            170,
                            210,
                        ],
                    },
                    {
                        "name": "VacanciesA",
                        "data": [
                            210,
                            170,
                            150,
                            150,
                            140,
                            130,
                            130,
                            120,
                            110,
                            110,
                            100,
                            90,
                        ],
                    },
                    {
                        "name": "VacanciesB",
                        "data": [
                            90,
                            100,
                            110,
                            120,
                            130,
                            150,
                            210,
                            170,
                            150,
                            140,
                            130,
                            110,
                        ],
                    },
                ],
            },
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class PMRvsCashCollectedAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "PMR vs Cash Collected",
            "kpis": [
                {"label": "PMR", "value": 1250000, "currency": "USD"},
                {"label": "Cash Collected", "value": 1121000, "currency": "USD"},
            ],
            "delta": {"value": 1.3, "direction": "up", "text": "VS Last week"},
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class MoveInsVsMoveOutsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Move-ins vs Move-outs",
            "summary": {"period": "Last 12 months"},
            "chart": {
                "type": "bar-grouped",
                "categories": [
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                ],
                "series": [
                    {
                        "name": "Move-ins",
                        "data": [45, 50, 60, 70, 65, 75, 80, 78, 70, 68, 62, 71],
                    },
                    {
                        "name": "Move-outs",
                        "data": [30, 35, 40, 45, 44, 50, 52, 55, 48, 46, 45, 49],
                    },
                ],
            },
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class DelinquencyRateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Delinquency Rate",
            "summary": {
                "rate_pct": 4.2,
                "delta": {"value": -0.4, "direction": "down", "text": "VS Last week"},
            },
            "by_property": [
                {"label": "Vertex Luxury Flats", "rate_pct": 3.1},
                {"label": "Vertex Condos", "rate_pct": 4.6},
                {"label": "Vertex Family", "rate_pct": 5.0},
            ],
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class UnitTurnoverTimeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Average Unit Turnover Time",
            "summary": {
                "value_days": 12.4,
                "delta": {"value": -0.8, "direction": "down", "text": "VS Last week"},
            },
            "trend": {
                "type": "line",
                "x": ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"],
                "series": [
                    {
                        "name": "Days",
                        "data": [14.2, 13.9, 13.6, 13.1, 12.9, 12.7, 12.5, 12.4],
                    }
                ],
            },
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class TicketsByCategoryTrendAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Tickets by Category (Trend)",
            "summary": {"period": "Last 8 weeks"},
            "chart": {
                "type": "line",
                "x": ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"],
                "series": [
                    {
                        "name": "Maintenance",
                        "data": [120, 110, 130, 125, 140, 135, 128, 132],
                    },
                    {"name": "Billing", "data": [60, 58, 62, 59, 65, 63, 61, 60]},
                    {"name": "Other", "data": [40, 38, 41, 39, 42, 40, 39, 38]},
                ],
            },
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class AvgTicketResolutionTimeAPIView(DashboardQueryMixin, APIView):
    permission_classes = [IsAuthenticated]
    PROPERTY_PATH = "unit__floor__building__location__property_id"
    LOCATION_PATH = "unit__floor__building__location_id"

    def get(self, request):
        f = self.parse_filters(request, allow_defaults=True)
        date_field = f["date_field"] or "reported_date"
        self.ensure_model_has_field(Maintenance, date_field)

        qs = self.scope_for_current_user(Maintenance.objects.all(), request.user)
        qs = self.apply_property_location_filters(
            qs,
            property_ids=f["property_ids"],
            location_ids=f["location_ids"],
        )
        current_q = self.q_for_range(Maintenance, date_field, f["start"], f["end"])
        previous_q = self.q_for_range(
            Maintenance, date_field, f["prev_start"], f["prev_end"]
        )

        agg = qs.aggregate(
            current=Count("id", filter=current_q),
            previous=Count("id", filter=previous_q),
            avg_time=Avg(F("resolved_date") - F("reported_date"), filter=current_q),
        )

        delta, direction = self.compute_delta_percent(
            agg["current"] or 0, agg["previous"] or 0
        )

        if agg["avg_time"] is None:
            total_seconds = 0
            formatted = "0.00 hrs"
        else:
            total_seconds = agg["avg_time"].total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) / 60)
            formatted = f"{hours}.{int(minutes / 60 * 100):02d} hrs"
        data = {
            "title": "Average Time to Resolve Tickets",
            "summary": {
                "value_hours": agg["avg_time"],
                "formatted": formatted,
                "delta": {
                    "value": delta,
                    "direction": direction,
                    "text": "VS Last week",
                },
            },
            "gauge": {
                "min": 0,
                "max": 100,
                "thresholds": [
                    {"to": 25, "label": "good"},
                    {"to": 50, "label": "warning"},
                    {"to": 100, "label": "bad"},
                ],
            },
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class SupportTicketsRaisedLineChartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Support Tickets Raised",
            "summary": {
                "value": 872,
                "delta": {
                    "value": -0.8,
                    "direction": "down",
                    "text": "VS Last week",
                },
            },
            "trend": {
                "type": "line",
                "date": [
                    "Mon",
                    "Tue",
                    "Wed",
                    "Thu",
                    "Fri",
                    "Sat",
                    "Sun",
                ],
                "series": [
                    {
                        "name": "Days",
                        "data": [
                            150,
                            30,
                            75,
                            25,
                            75,
                            50,
                            100,
                        ],
                    }
                ],
            },
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class SLAComplaintsByMonthAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "SLA Compliance By Month",
            "summary": {
                "value": 872,
                "delta": {
                    "value": -0.8,
                    "direction": "down",
                    "text": "VS Last week",
                },
            },
            "chart": {
                "type": "bar",
                "stacked": True,
                "categories": [
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                ],
                "series": [
                    {
                        "name": "Met",
                        "data": [
                            180,
                            210,
                            230,
                            160,
                            190,
                            200,
                            170,
                            220,
                            210,
                            150,
                            130,
                            140,
                        ],
                    },
                    {
                        "name": "Breached",
                        "data": [50, 45, 60, 40, 70, 65, 55, 60, 80, 50, 40, 45],
                    },
                ],
                "tooltips": True,
            },
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class TicketResolutionSLAComplaintsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = {
            "title": "Ticket Resolution SLA Compliance",
            "summary": {
                "value": 872,
                "compliance_pct": 66.5,
                "delta": {
                    "value": -0.8,
                    "direction": "down",
                    "text": "VS Last week",
                },
            },
            "chart": {
                "type": "gauge",
                "value": 66.5,
                "max": 100,
                "label": "Resolved within SLA",
                "colors": {"good": "#00B050", "average": "#FFC000", "bad": "#C00000"},
                "show_label": True,
            },
        }
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)
