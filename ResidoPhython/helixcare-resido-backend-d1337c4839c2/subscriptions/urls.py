from django.urls import re_path

from subscriptions.api.v1.plan import PlanListAPIView
from subscriptions.api.v1.subscription import TenantSubscriptionsListCreateAPIView
from subscriptions.api.v1.product_setting import ProductSubsSettingListAPIView

urlpatterns = [
    re_path(
        r"api/v1/tenant-subscriptions$",
        TenantSubscriptionsListCreateAPIView.as_view(),
        name="list_create_tenant_subscriptions",
    ),
    re_path(
        r"api/v1/plans$",
        PlanListAPIView.as_view(),
        name="list_plans",
    ),
    re_path(
        r"api/v1/subs-settings$",
        ProductSubsSettingListAPIView.as_view(),
        name="list_product_subs_settings",
    ),
]
