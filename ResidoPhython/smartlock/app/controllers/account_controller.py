"""
Account Controller Module - Handles authentication and account operations
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from app.services.account_service import AccountService
from app.serializers.login_request_serializer import LoginRequestSerializer
from app.serializers.login_response_serializer import LoginResponseSerializer
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AccountController(APIView):
    """
    Controller for account-related operations.
    Handles user authentication and account management.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Account"],
        summary="Login via TTLock username/password",
        description="Authenticate user using TTLock credentials and get access token",
        request=LoginRequestSerializer,
        responses={
            200: LoginResponseSerializer,
            401: LoginResponseSerializer,
            400: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
    )
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
