"""
API views for RESIDO subscription management

Provides endpoints for:
- /api/v1/plans - List available subscription plans
- /api/v1/subs-settings - List global subscription settings

These endpoints are consumed by GENIUS during customer onboarding
to display available plans.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from hb_core.exception import StandardAPIException
from hb_core.mixins import StandardListCreateAPIMixin
from s2s_auth.authentication.s2s import S2SAuthentication

from common.errors import ERROR_DETAILS
from subscriptions.models.plan import Plan
from subscriptions.models.product_setting import ProductSetting
from common.subscription_serializers import (
    PlanSerializer,
    PlanMiniSerializer,
    ProductSettingSerializer,
)


class PlanListAPIView(StandardListCreateAPIMixin):
    """
    GET /api/v1/plans

    List all subscription plans available in RESIDO.

    Authentication: S2S (service-to-service) authentication required
    Permissions: Authenticated users only

    Query params:
    - search: Filter by name or code
    - active: Filter by active status (true/false)

    Returns: List of Plan objects
    """

    authentication_classes = [S2SAuthentication]
    permission_classes = (IsAuthenticated,)
    search_fields = ("name", "code")

    def get_serializer_class(self):
        if self.request.user.is_authenticated:
            return PlanSerializer
        return PlanMiniSerializer

    def get_queryset(self):
        queryset = Plan.objects.all()

        # Filter by active status if provided
        active = self.request.query_params.get("active")
        if active is not None:
            is_active = active.lower() in ("true", "1", "yes")
            queryset = queryset.filter(active=is_active)

        return queryset.order_by("name")

    def post(self, request, *args, **kwargs):
        """
        POST not allowed - plans are managed via admin/fixtures
        """
        raise StandardAPIException(
            code="method_not_allowed",
            detail=ERROR_DETAILS["method_not_allowed"],
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        )


class ProductSubsSettingListAPIView(StandardListCreateAPIMixin):
    """
    GET /api/v1/subs-settings

    List global subscription settings for RESIDO.

    Authentication: S2S (service-to-service) authentication required
    Permissions: Authenticated users only

    Query params:
    - search: Filter by name or visible_name
    - active: Filter by active status (true/false)

    Returns: List of ProductSetting objects
    """

    authentication_classes = [S2SAuthentication]
    permission_classes = (IsAuthenticated,)
    search_fields = ("name", "visible_name")

    def get_serializer_class(self):
        return ProductSettingSerializer

    def get_queryset(self):
        queryset = ProductSetting.objects.all()

        # Filter by active status if provided
        active = self.request.query_params.get("active")
        if active is not None:
            is_active = active.lower() in ("true", "1", "yes")
            queryset = queryset.filter(active=is_active)

        return queryset.order_by("name")

    def post(self, request, *args, **kwargs):
        """
        POST not allowed - settings are managed via admin/fixtures
        """
        raise StandardAPIException(
            code="method_not_allowed",
            detail=ERROR_DETAILS["method_not_allowed"],
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
