from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from hb_core.exception import StandardAPIException
from hb_core.mixins import StandardListCreateAPIMixin
from s2s_auth.authentication.s2s import S2SAuthentication

from common.errors import ERROR_DETAILS
from subscriptions.filters.plan import PlanFilter
from subscriptions.models.plan import Plan
from subscriptions.serializers.plan import (
    PlanSerializer,
    PlanMiniSerializerV2,
)


class PlanListAPIView(StandardListCreateAPIMixin):
    authentication_classes = [S2SAuthentication]
    permission_classes = (IsAuthenticated,)
    filterset_class = PlanFilter
    search_fields = (
        "name",
        "code",
    )

    def get_serializer_class(self):
        if self.request.user.is_authenticated:
            return PlanSerializer
        return PlanMiniSerializerV2

    def get_queryset(self):
        return Plan.objects.all()

    def post(self, request, *args, **kwargs):
        raise StandardAPIException(
            code="method_not_allowed",
            detail=ERROR_DETAILS["method_not_allowed"],
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
