# analytics/mixins.py
from datetime import datetime, time, timedelta
from functools import wraps
from typing import Iterable, Callable

from django.core.exceptions import FieldDoesNotExist
from django.db.models import (
    Q,
    Count,
    QuerySet,
    DateField as DJDateField,
    DateTimeField as DJDateTimeField,
)
from django.utils import timezone
from django.utils.dateparse import parse_date as django_parse_date

from rest_framework import status

from common.exception import StandardAPIException
from common.errors import ERROR_DETAILS
from analytics.constants.dashboard import DEFAULT_WINDOW_DAYS


def _parse_date_flexible(date_str: str):
    if not date_str:
        return None

    result = django_parse_date(date_str)
    if result:
        return result

    try:
        return datetime.strptime(date_str, "%m/%d/%Y").date()
    except ValueError:
        pass

    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except ValueError:
        pass

    return None


def standard_api_exception_guard(fn: Callable):
    @wraps(fn)
    def _wrapped(self, request, *args, **kwargs):
        try:
            return fn(self, request, *args, **kwargs)
        except StandardAPIException:
            raise
        except Exception:
            raise StandardAPIException(
                code="internal_error",
                detail=ERROR_DETAILS.get("server_error", "Internal server error."),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return _wrapped


class DashboardQueryMixin:
    PROPERTY_PATH = "property_id"
    LOCATION_PATH = "property__location_id"

    SIGNED_STATUSES: tuple[str, ...] = ("executed", "active")
    PENDING_STATUSES: tuple[str, ...] = ("pending",)
    IN_PROGRESS_STATUSES: tuple[str, ...] = ("in_progress", "assigned")
    RESOLVED_STATUSES: tuple[str, ...] = ("completed", "closed")
    OPEN_STATUSES: tuple[str, ...] = ("open",)
    OCCUPIED_STATUSES: tuple[str, ...] = ("occupied",)
    VACANT_STATUSES: tuple[str, ...] = ("vacant",)

    def parse_filters(self, request, *, allow_defaults: bool = True) -> dict:
        start_s = (request.query_params.get("start") or "").strip()
        end_s = (request.query_params.get("end") or "").strip()

        start = _parse_date_flexible(start_s) if start_s else None
        end = _parse_date_flexible(end_s) if end_s else None

        defaults_applied = None
        if allow_defaults:
            today = timezone.localdate()
            if not start and not end:
                end = today
                start = end - timedelta(days=DEFAULT_WINDOW_DAYS - 1)
                defaults_applied = {"start": True, "end": True}
            elif start and not end:
                end = start + timedelta(days=DEFAULT_WINDOW_DAYS - 1)
                defaults_applied = {"end": True}
            elif end and not start:
                start = end - timedelta(days=DEFAULT_WINDOW_DAYS - 1)
                defaults_applied = {"start": True}

        if not start or not end:
            raise StandardAPIException(
                code="missing_required_param",
                detail=ERROR_DETAILS["missing_required_param"].format(
                    param="start,end"
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if start > end:
            if allow_defaults:
                start, end = end, start
                defaults_applied = (defaults_applied or {}) | {"swapped": True}
            else:
                raise StandardAPIException(
                    code="invalid_input_value",
                    detail=ERROR_DETAILS["invalid_input_value"].format(
                        param="start,end"
                    ),
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        span_days = (end - start).days + 1
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=span_days - 1)

        def _csv(key: str) -> list[str]:
            # Handle both comma-separated values and multiple parameters with same name
            values = request.query_params.getlist(key)
            if not values:
                return []
            # If multiple parameters, combine them
            # If single parameter, split by comma
            result = []
            for val in values:
                result.extend([v.strip() for v in val.split(",") if v.strip()])
            return result

        return {
            "start": start,
            "end": end,
            "prev_start": prev_start,
            "prev_end": prev_end,
            "property_ids": _csv("property_ids"),
            "location_ids": _csv("location_ids"),
            "date_field": (request.query_params.get("date_field") or "").strip(),
            "defaults_applied": defaults_applied,
        }

    def scope_for_current_user(self, qs: QuerySet, user):
        manager = qs.model.objects
        fn = getattr(manager, "for_current_user", None)
        return fn() if callable(fn) else qs

    def apply_property_location_filters(
        self,
        qs: QuerySet,
        *,
        property_ids: list[str],
        location_ids: list[str],
        property_path: str | None = None,
        location_path: str | None = None,
    ) -> QuerySet:
        if property_ids:
            qs = qs.filter(
                **{f"{property_path or self.PROPERTY_PATH}__in": property_ids}
            )
        if location_ids:
            qs = qs.filter(
                **{f"{location_path or self.LOCATION_PATH}__in": location_ids}
            )
        return qs

    def any_status_q(self, field: str, statuses: Iterable[str]) -> Q:
        statuses = tuple(s for s in statuses if s)
        if not statuses:
            return Q()
        q = Q()
        for s in statuses:
            q |= Q(**{f"{field}__iexact": s})
        return q

    def compute_delta_percent(
        self, current: int | float, previous: int | float
    ) -> tuple[float, str]:
        if not previous:
            return (0.0, "flat" if not current else "up")
        pct = round(((current - previous) / previous) * 100.0, 2)
        return (abs(pct), "up" if current >= previous else "down")

    def build_meta(
        self, *, start, end, prev_start, prev_end, extra: dict | None = None
    ) -> dict:
        base = {
            "period": {"from": str(start), "to": str(end)},
            "previous_period": {"from": str(prev_start), "to": str(prev_end)},
        }
        if extra:
            base.update(extra)
        return base

    def ensure_model_has_field(self, model, field_name: str) -> str:
        if not field_name:
            return ""
        try:
            model._meta.get_field(field_name)
            return field_name
        except FieldDoesNotExist:
            raise StandardAPIException(
                code="invalid_input_value",
                detail=ERROR_DETAILS["invalid_input_value"].format(param="date_field"),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    def _is_datetime_field(self, model, field_name: str) -> bool:
        field = model._meta.get_field(field_name)
        return isinstance(field, DJDateTimeField)

    def _is_date_field(self, model, field_name: str) -> bool:
        field = model._meta.get_field(field_name)
        return isinstance(field, DJDateField)

    def q_for_range(self, model, field_name: str, start_date, end_date) -> Q:
        if self._is_datetime_field(model, field_name):
            tz = timezone.get_current_timezone()
            start_dt = timezone.make_aware(datetime.combine(start_date, time.min), tz)
            end_dt_excl = timezone.make_aware(
                datetime.combine(end_date + timedelta(days=1), time.min), tz
            )
            return Q(
                **{f"{field_name}__gte": start_dt, f"{field_name}__lt": end_dt_excl}
            )
        return Q(**{f"{field_name}__gte": start_date, f"{field_name}__lte": end_date})

    def q_for_after_until(self, model, field_name: str, after_date, until_date) -> Q:
        if self._is_datetime_field(model, field_name):
            tz = timezone.get_current_timezone()
            gte_dt = timezone.make_aware(
                datetime.combine(after_date + timedelta(days=1), time.min), tz
            )
            lt_dt = timezone.make_aware(
                datetime.combine(until_date + timedelta(days=1), time.min), tz
            )
            return Q(**{f"{field_name}__gte": gte_dt, f"{field_name}__lt": lt_dt})
        return Q(**{f"{field_name}__gt": after_date, f"{field_name}__lte": until_date})

    def get_unit_chart_data(self, qs, current_q, view_type):
        field_map = {
            "by_unit_type": {"field": "unit_type"},
            "by_buildings": {
                "field": "floor__building__name",
            },
            "by_properties": {
                "field": "floor__building__location__property__name",
            },
        }

        config = field_map.get(view_type, field_map["by_properties"])
        group_field = config["field"]

        unit_data = (
            qs.filter(current_q & self.any_status_q("status", self.VACANT_STATUSES))
            .values(group_field)
            .annotate(count=Count("id"))
            .order_by(group_field)
        )

        # Extract data
        unit_names = [item[group_field] or "Unknown" for item in unit_data]
        unit_counts = [item["count"] for item in unit_data]

        return unit_names, unit_counts

    def percent(self, value, total):
        return round((value / total) * 100, 2) if total else 0.0
