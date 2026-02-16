from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import gettext_lazy as _
from app import models
from app.utils import Logger


logger = Logger.get_logger(__name__)

class BearerTokenAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = None
        try:
            auth_header = request.headers.get("Authorization")
        except Exception:
            auth_header = request.META.get("HTTP_AUTHORIZATION")

        logger.debug("Authorization header: %s", auth_header)

        if not auth_header:
            # No header -> do not attempt authentication
            return None

        parts = auth_header.split()
        if len(parts) != 2:
            raise AuthenticationFailed(_("Invalid Authorization header. Expected 'Bearer <token>'"))

        prefix, token = parts
        if prefix.lower() != self.keyword.lower():
            # Not a Bearer token -> do not attempt authentication
            return None

        if not token:
            raise AuthenticationFailed(_("Invalid token"))

        # Lookup token in DB
        token_obj = models.AccessRefreshToken.objects.filter(access_token=token).first()
        
        if token_obj is None:
            logger.warning("Authentication failed: token not found")
            raise AuthenticationFailed(_("Invalid or unknown token"))

        # Check expiry
        if models.AccessRefreshToken.is_expired(token_obj):
            logger.info("Authentication failed: token expired for user_id=%s", token_obj.user_id)
            raise AuthenticationFailed(_("Token has expired"))

        # Resolve user
        user = models.User.objects.filter(id=token_obj.user_id).first()
        
        if not user:
            logger.warning("Authentication failed: user not found for token user_id=%s", token_obj.user_id)
            raise AuthenticationFailed(_("User not found"))

        logger.debug("Authentication successful for user_id=%s", token_obj.user_id)
        return (user, token_obj)

    def authenticate_header(self, request):
        return self.keyword

