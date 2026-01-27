from datetime import date, timedelta
from typing import Iterable, Optional
from analytics.constants.dashboard import SIGNED_STATUSES, PENDING_STATUSES
from django.db import models
from django.db.models import Q


def _q_any_status(field: str, statuses: Iterable[str]) -> Q:
    q = Q()
    for s in statuses:
        q |= Q(**{f"{field}__iexact": s})
    return q


class LeaseQuerySet(models.QuerySet):
    def with_statuses(self, field: str, statuses: Iterable[str]) -> "LeaseQuerySet":
        return self.filter(_q_any_status(field, statuses))

    def in_date_window(self, field: str, start: date, end: date) -> "LeaseQuerySet":
        return self.filter(**{f"{field}__gte": start, f"{field}__lte": end})

    def scope_props_locs(
        self,
        *,
        property_ids: Optional[list[str]] = None,
        location_ids: Optional[list[str]] = None,
        property_field: Optional[str] = None,
        location_field: Optional[str] = None,
    ) -> "LeaseQuerySet":
        qs = self
        if property_ids:
            for f in [property_field, "unit__property_id", "property_id"]:
                if not f:
                    continue
                try:
                    qs = qs.filter(**{f"{f}__in": property_ids})
                    break
                except Exception:
                    continue
        if location_ids:
            for f in [location_field, "unit__location_id", "location_id"]:
                if not f:
                    continue
                try:
                    qs = qs.filter(**{f"{f}__in": location_ids})
                    break
                except Exception:
                    continue
        return qs

    def signed_count(self, date_field: str, start: date, end: date) -> int:
        return (
            self.in_date_window(date_field, start, end)
            .with_statuses("status", SIGNED_STATUSES)
            .count()
        )

    def pending_count(self) -> int:
        return self.with_statuses("status", PENDING_STATUSES).count()

    def expiring_count(self, today: date, days: int = 30) -> int:
        return self.filter(
            end_date__gte=today, end_date__lte=today + timedelta(days=days)
        ).count()


class LeaseAnalyticsManager(models.Manager.from_queryset(LeaseQuerySet)):
    """Attach as Lease.analytics; gives access to the queryset helpers."""

    pass
