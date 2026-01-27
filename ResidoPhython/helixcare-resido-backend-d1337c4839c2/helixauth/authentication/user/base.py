from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from helixauth.utils import get_user


class BaseUserAuthentication(JWTAuthentication):
    @staticmethod
    def get_active_user(validated_token, tenant):
        try:
            user_id = validated_token["user_id"]
            tenant_id = validated_token["tenant_id"]
        except KeyError:
            raise InvalidToken(_("Token contained no recognizable user identification"))

        if str(tenant.id) != tenant_id:
            raise AuthenticationFailed(_("User not found"), code="user_not_found")

        return get_user(user_id)

    @staticmethod
    def check_sub_token_type(unverified_payload, required_sub_token_type):
        return unverified_payload.get("sub_token_type") == required_sub_token_type
