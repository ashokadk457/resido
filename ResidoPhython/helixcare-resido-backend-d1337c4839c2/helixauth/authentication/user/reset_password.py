import jwt
from rest_framework_simplejwt.exceptions import TokenError

from common.utils.logging import logger
from common.thread_locals import set_current_user
from helixauth.authentication.user.base import BaseUserAuthentication
from helixauth.managers.token.user import HelixUserTokenManager


class UserResetPasswordAuthentication(BaseUserAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        unverified_payload = jwt.decode(
            jwt=raw_token, options={"verify_signature": False}
        )
        is_reset_password_token = self.check_sub_token_type(
            unverified_payload, required_sub_token_type="reset_password"
        )
        if not is_reset_password_token:
            logger.info("Invalid token. sub_token_type is not reset_password")
            return None

        try:
            validated_token = HelixUserTokenManager.get_validated_token_from_raw(
                raw_token
            )
        except TokenError:
            return None

        user = self.get_active_user(validated_token, request.tenant)
        request.is_helix_user = True
        set_current_user(user)
        return user, validated_token


class RentalApplicationAuthentication(BaseUserAuthentication):
    def authenticate(self, request):
        from residents.models import Resident
        from rest_framework_simplejwt.exceptions import AuthenticationFailed

        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        unverified_payload = jwt.decode(
            jwt=raw_token, options={"verify_signature": False}
        )
        is_rental_application_token = self.check_sub_token_type(
            unverified_payload, required_sub_token_type="rental_application_view"
        )
        if not is_rental_application_token:
            logger.info("Invalid token. sub_token_type is not rental_application_view")
            return None

        try:
            validated_token = HelixUserTokenManager.get_validated_token_from_raw(
                raw_token
            )
        except TokenError:
            return None

        user = self.get_active_user(validated_token, request.tenant)

        # Get the resident associated with this user
        try:
            resident = Resident.objects.get(user=user)
        except Resident.DoesNotExist:
            logger.error(f"No Resident found for user {user.id}")
            raise AuthenticationFailed("User not found", code="user_not_found")

        # Set request attributes for resident authentication
        request.is_resident = True
        request.patient = resident
        set_current_user(user)
        return user, validated_token
