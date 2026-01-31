from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from app.services.account_service import AccountService
from app.serializers.login_request_serializer import LoginRequestSerializer
from app.serializers.login_response_serializer import LoginResponseSerializer
from app.utils.logger import get_logger

logger = get_logger(__name__)


@extend_schema(
    tags=["Account"],
    description="Login via TTLock username/password",
    auth=None,
    request=LoginRequestSerializer,
    responses={
        200: LoginResponseSerializer,
        401: LoginResponseSerializer,
    },
)
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def LoginUsernamePassword(request):
    logger.info("POST /api/Account/LoginUsernamePassword")

    serializer = LoginRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    result = AccountService.login_with_ttlock(serializer.validated_data)

    response_serializer = LoginResponseSerializer(data=result)
    response_serializer.is_valid(raise_exception=True)

    status_code = (
        status.HTTP_200_OK
        if result.get("success")
        else status.HTTP_401_UNAUTHORIZED
    )

    return Response(response_serializer.data, status=status_code)
