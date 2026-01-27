from django.urls import re_path

from processflow.apiviews import ProcessListAPIView, ProcessRetrieveAPIView

urlpatterns = (
    re_path(
        r"^api/v1/processes$",
        ProcessListAPIView.as_view(),
        name="list_processes",
    ),
    re_path(
        r"^api/v1/processes/(?P<pk>[0-9a-zA-Z\-]+)$",
        ProcessRetrieveAPIView.as_view(),
        name="retrieve_process",
    ),
    re_path(
        r"^api/v1/processes/terminate$",
        ProcessListAPIView.as_view(),
        name="list_processes",
    ),
)
