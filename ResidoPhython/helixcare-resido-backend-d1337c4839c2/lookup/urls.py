from django.urls import re_path
import lookup.apiviews

urlpatterns = (
    re_path(
        r"^api/v1/lookups$",
        lookup.apiviews.LookupListCreateAPIView.as_view(),
        name="lookup_list",
    ),
    re_path(
        r"^api/v1/lookups/(?P<pk>[0-9a-zA-Z\-]+)$",
        lookup.apiviews.LookupUpdateView.as_view(),
        name="update_lookup",
    ),
    re_path(
        r"^api/v1/cpt_codes$", lookup.apiviews.CPTCodeList.as_view(), name="cpt_list"
    ),
    re_path(
        r"^api/v1/cpt_code_detail/(?P<pk>[0-9a-zA-Z\-]+)$",
        lookup.apiviews.CPTCodesDetail.as_view(),
        name="cpt_code_detail",
    ),
    re_path(
        r"^api/v1/ui_metadata$",
        lookup.apiviews.UIMetadataList.as_view(),
        name="ui_metdata_list",
    ),
)
