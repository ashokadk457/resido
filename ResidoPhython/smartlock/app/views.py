"""
API Views Module - View layer that imports from controllers

This module serves as the API layer that imports controller classes
and re-exports them for URL routing. It acts as the bridge between
URLs and the modular controllers.

Architecture:
URLs → Views (imports) → Controllers (APIView classes) → Services → Repositories
"""

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from app.common.mixins import StandardListCreateAPIMixin

from app.serializers import LoginRequestSerializer, LoginResponseSerializer
from app.services.account_service import AccountService
from app.utils.logger import get_logger
from django.db.models import QuerySet
from django.contrib.auth import get_user_model
from app.auth.authentication import BearerTokenAuthentication
from drf_spectacular.utils import extend_schema, extend_schema_view




logger = get_logger(__name__)
# Account Views - imported from controllers



# @extend_schema(
#         tags=["Account"],
#         summary="Login via TTLock username/password",
#         description="Authenticate user using TTLock credentials and get access token",
#         request=LoginRequestSerializer,
#         responses={
#             200: LoginResponseSerializer,
#             401: LoginResponseSerializer,
#             400: {"type": "object", "properties": {"detail": {"type": "string"}}},
#         },
#     )
@extend_schema_view(
    get=extend_schema(exclude=True)  # 👈 hides GET
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
        """
        Handle login request with TTLock credentials.
        
        Args:
            request: HTTP request with username and password
            
        Returns:
            Response with access token or error message
        """
        logger.info("POST /api/v1/account/login")

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

__all__ = [
    "LoginView"
]

