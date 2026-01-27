import jwt
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import status
from common.utils.logging import logger
from helixauth.constants import AccessLevel
from helixauth.managers.token.user import HelixUserTokenManager
from staff.models import HelixUser


class CustomerOnboardingAuthentication(JWTAuthentication):
    def authenticate(self, request):
        from common.exception import StandardAPIException

        header = self.get_header(request)
        if header is None:
            raise StandardAPIException(
                code="authorization_header_missing",
                detail="Authorization header is missing.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            raise StandardAPIException(
                code="token_missing",
                detail="Bearer token is missing in the Authorization header.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            unverified_payload = jwt.decode(
                jwt=raw_token, options={"verify_signature": False}
            )
        except jwt.InvalidTokenError:
            raise StandardAPIException(
                code="invalid_token",
                detail="Invalid token provided.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        if not self.check_sub_token_type(unverified_payload):
            logger.info("Invalid token. sub_token_type is not customer_onboarding")
            raise StandardAPIException(
                code="invalid_token_type",
                detail="Invalid token type for care center admin.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            validated_token = HelixUserTokenManager.get_validated_token_from_raw(
                raw_token
            )
        except TokenError:
            raise StandardAPIException(
                code="invalid_token",
                detail="Invalid token provided.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        user = HelixUser(
            email=unverified_payload.get("user_id"),
            access_level=AccessLevel.Customer.value,
        )
        # set_current_user(user) When audit, Dummy user will raise error 404.
        request.user = user

        return user, validated_token

    @staticmethod
    def check_sub_token_type(unverified_payload):
        return unverified_payload.get("sub_token_type") == "customer_onboarding"
