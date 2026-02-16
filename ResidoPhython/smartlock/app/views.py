from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from app.common.mixins import StandardListCreateAPIMixin

from app.common.response import StandardAPIResponse
from app.serializers import LoginRequestSerializer, LoginResponseSerializer
from app.services.account_service import AccountService
from app.utils import Logger
from django.db.models import QuerySet
from django.contrib.auth import get_user_model
from app.auth.authentication import BearerTokenAuthentication
from drf_spectacular.utils import extend_schema, extend_schema_view


logger = Logger.get_logger(__name__)

@extend_schema_view(
    get=extend_schema(exclude=True)
)
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
class LoginView(StandardListCreateAPIMixin):
    """
    Controller for account-related operations.
    Handles user authentication and account management.
    """

    permission_classes = [AllowAny]
    authentication_classes = [BearerTokenAuthentication]
   
    def post(self, request):
        logger.info("Login View -  POST /api/v1/account/login")

        serializer = LoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = AccountService.login_with_ttlock(serializer.validated_data)

        response_serializer = LoginResponseSerializer(data=result)
        response_serializer.is_valid(raise_exception=True)

        return StandardAPIResponse(data=response_serializer.data, status=status.HTTP_200_OK)

__all__ = [
    "LoginView"
]

