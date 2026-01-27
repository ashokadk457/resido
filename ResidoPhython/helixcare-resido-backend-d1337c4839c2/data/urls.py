from django.urls import re_path

import data.apiviews

urlpatterns = (
    re_path(
        r"^api/v1/reason-categories$",
        data.apiviews.ReasonCategoryListCreateAPIView.as_view(),
        name="reason_categories",
    ),
    re_path(
        r"^api/v1/reason-categories/(?P<pk>[0-9a-zA-Z\-]+)$",
        data.apiviews.ReasonCategoryDetail.as_view(),
        name="reason_categories",
    ),
    re_path(
        r"^api/v1/reasons$",
        data.apiviews.ReasonListCreateAPIView.as_view(),
        name="reasons",
    ),
    re_path(
        r"^api/v1/reasons/(?P<pk>[0-9a-zA-Z\-]+)$",
        data.apiviews.ReasonDetail.as_view(),
        name="reasons",
    ),
    re_path(
        r"^api/v1/reason-bulk-upload$",
        data.apiviews.ReasonBulkUploadAPIView.as_view(),
        name="reason_bulk_upload",
    ),
    re_path(
        r"^api/v1/reason-module-count$",
        data.apiviews.ReasonModuleCountAPIView.as_view(),
        name="reason_module_count",
    ),
)
