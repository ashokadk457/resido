from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import gettext_lazy as _
from app import models
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BearerTokenAuthentication(BaseAuthentication):
    """Authenticate requests using a Bearer access token from the Authorization header.

    - Accepts header in format: "Authorization: Bearer <token>"
    - Returns (User, AccessRefreshToken) on success
    - Returns None if no Authorization header (so other auth classes or anonymous access can proceed)
    - Raises AuthenticationFailed for malformed / invalid / expired tokens
    """

    keyword = "Bearer"

    def authenticate(self, request):
        # Prefer DRF's case-insensitive header access
        auth_header = None
        try:
            # request.headers is provided by DRF and is case-insensitive
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
            # Optionally purge token from DB
            # try:
            #      AccessRefreshTokensRepository.delete_token(token_obj.id)
            # except Exception:
            #     logger.exception("Failed to delete expired token %s", token_obj.id)
            # raise AuthenticationFailed(_("Token has expired"))
            raise AuthenticationFailed(_("Token has expired"))

        # Resolve user
        # user = UsersRepository.get_by_id(token_obj.user_id)
        user = models.User.objects.filter(id=token_obj.user_id).first()
        
        if not user:
            logger.warning("Authentication failed: user not found for token user_id=%s", token_obj.user_id)
            raise AuthenticationFailed(_("User not found"))

        # Success: DRF will set request.user and request.auth to these values
        logger.debug("Authentication successful for user_id=%s", token_obj.user_id)
        return (user, token_obj)

    def authenticate_header(self, request):
        return self.keyword

