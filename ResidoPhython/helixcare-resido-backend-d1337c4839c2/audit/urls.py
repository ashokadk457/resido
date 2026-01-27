from django.urls import re_path

from .apiviews import AuditEventListView

urlpatterns = [
    re_path(
        r"^api/v1/audit/events$",
        AuditEventListView.as_view(),
        name="list-audit-events",
    ),
]
