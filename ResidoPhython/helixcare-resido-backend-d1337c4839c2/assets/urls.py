from django.urls import re_path
import assets.apiviews


urlpatterns = (
    re_path(
        r"^api/v1/assets$",
        assets.apiviews.AssetListCreateAPIView.as_view(),
        name="asset_list_create",
    ),
    re_path(
        r"^api/v1/assets/(?P<pk>[0-9a-zA-Z\-]+)$",
        assets.apiviews.AssetDetailAPIView.as_view(),
        name="asset_detail",
    ),
)
