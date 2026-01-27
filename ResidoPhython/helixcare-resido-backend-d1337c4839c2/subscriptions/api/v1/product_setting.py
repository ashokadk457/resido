from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from hb_core.exception import StandardAPIException
from hb_core.mixins import StandardListCreateAPIMixin
from s2s_auth.authentication.s2s import S2SAuthentication

from common.errors import ERROR_DETAILS
from subscriptions.filters.product_setting import ProductSettingFilter
from subscriptions.models.product_setting import ProductSetting
from subscriptions.serializers.product_setting import ProductSettingSerializer


class ProductSubsSettingListAPIView(StandardListCreateAPIMixin):
    authentication_classes = [S2SAuthentication]
    permission_classes = (IsAuthenticated,)
    filterset_class = ProductSettingFilter
    search_fields = (
        "name",
        "visible_name",
    )

    def get_serializer_class(self):
        return ProductSettingSerializer

    def get_queryset(self):
        return ProductSetting.objects.all()

    def post(self, request, *args, **kwargs):
        raise StandardAPIException(
            code="method_not_allowed",
            detail=ERROR_DETAILS["method_not_allowed"],
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
