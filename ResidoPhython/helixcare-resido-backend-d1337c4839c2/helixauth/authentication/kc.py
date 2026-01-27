from django.contrib.auth.models import AnonymousUser
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from common.thread_locals import set_current_user
from external.kc.core import KeyCloak
from helixauth.managers.user.generic import HelixUserManager
from helixauth.models import HelixUser


class KeyCloakAuthentication(JWTAuthentication):
    def __init__(self, *args, **kwargs):
        super(KeyCloakAuthentication, self).__init__(*args, **kwargs)
        self.kc = KeyCloak.init(init_admin=False)

    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return AnonymousUser(), None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return AnonymousUser(), None

        info = self.validate_token(raw_token=raw_token)
        if not info:
            return None

        return self.get_user_obj(validated_token=raw_token, request=request), raw_token

    def get_raw_token(self, header):
        raw_token = super().get_raw_token(header)
        if raw_token is None:
            return raw_token

        return raw_token.decode(encoding="utf-8")

    def validate_token(self, raw_token):
        try:
            token_info = self.kc.openid.introspect(token=raw_token)
        except Exception:
            return None
            # raise AuthenticationFailed(f"Failed to authenticate: {str(e)}")

        if not token_info.get("active"):
            return None
            # raise InvalidToken(_("Token is not active"))

        return token_info

    def get_user_obj(self, validated_token, request):
        try:
            user_info = self.kc.openid.userinfo(token=validated_token)
            auth_user_id = user_info.get("sub")
            if not auth_user_id:
                raise AuthenticationFailed(_("Invalid token"))
            user = HelixUser.objects.get(auth_user_id=auth_user_id)
        except HelixUser.DoesNotExist:
            raise AuthenticationFailed(_("User not found"), code="user_not_found")

        if not user.is_active:
            raise AuthenticationFailed(_("User is inactive"), code="user_inactive")

        set_current_user(user=user)

        if user is not None:
            user_manager = HelixUserManager(user_obj=user)
            if user.is_staff:
                request.is_helix_user = True
                request.staff, c = user_manager.get_associated_patient_or_provider()
            else:
                request.is_resident = True
                request.patient, c = user_manager.get_associated_patient_or_provider()

        return user
