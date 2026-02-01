from datetime import timedelta
from django.utils import timezone
from app.models.access_refresh_token_model import AccessRefreshToken
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AccessRefreshTokensRepository:
    """Repository layer for AccessRefreshTokens table."""

    @staticmethod
    def _base_queryset(user_id=None, access_token=None, refresh_token=None, uid=None):
        qs = AccessRefreshToken.objects.all()

        if user_id:
            qs = qs.filter(user_id=user_id)

        if access_token:
            qs = qs.filter(access_token=access_token)

        if refresh_token:
            qs = qs.filter(refresh_token=refresh_token)

        if uid is not None:
            qs = qs.filter(uid=uid)

        return qs

    @staticmethod
    def get_by_id(token_id):
        logger.debug("get_by_id token_id=%s", token_id)
        try:
            return AccessRefreshToken.objects.get(id=token_id)
        except AccessRefreshToken.DoesNotExist:
            return None

    @staticmethod
    def find_by_access_token(access_token):
        logger.debug("find_by_access_token access_token=%s", access_token)
        try:
            return AccessRefreshToken.objects.get(access_token=access_token)
        except AccessRefreshToken.DoesNotExist:
            return None

    @staticmethod
    def find_by_refresh_token(refresh_token):
        logger.debug("find_by_refresh_token refresh_token=%s", refresh_token)
        try:
            return AccessRefreshToken.objects.get(refresh_token=refresh_token)
        except AccessRefreshToken.DoesNotExist:
            return None

    @staticmethod
    def list_tokens_for_user(user_id, offset=0, limit=20, order_by="issued_at_utc"):
        logger.debug("list_tokens_for_user user_id=%s offset=%s limit=%s", user_id, offset, limit)
        qs = AccessRefreshTokensRepository._base_queryset(user_id=user_id)
        return qs.order_by(order_by)[offset: offset + limit]

    @staticmethod
    def count_tokens_for_user(user_id):
        logger.debug("count_tokens_for_user user_id=%s", user_id)
        return AccessRefreshTokensRepository._base_queryset(user_id=user_id).count()

    @staticmethod
    def create_token(data):
        logger.info("create_token called")
        return AccessRefreshToken.objects.create(**data)

    @staticmethod
    def update_token(token_id, data):
        logger.info("update_token called token_id=%s", token_id)
        updated = AccessRefreshToken.objects.filter(id=token_id).update(**data)
        return updated > 0

    @staticmethod
    def delete_token(token_id):
        logger.warning("delete_token called token_id=%s", token_id)
        deleted, _ = AccessRefreshToken.objects.filter(id=token_id).delete()
        return deleted > 0

    @staticmethod
    def delete_by_refresh_token(refresh_token):
        logger.warning("delete_by_refresh_token refresh_token=%s", refresh_token)
        deleted, _ = AccessRefreshToken.objects.filter(refresh_token=refresh_token).delete()
        return deleted > 0

    @staticmethod
    def is_expired(token: AccessRefreshToken) -> bool:
        if not token.issued_at_utc or not token.expires_in:
            return False
        expiry = token.issued_at_utc + timedelta(seconds=int(token.expires_in))
        return timezone.now() >= expiry

    @staticmethod
    def purge_expired():
        """Delete tokens that are expired. Implementation uses Python-side check to keep DB compatibility."""
        logger.info("purge_expired called")
        now = timezone.now()
        expired_ids = []
        for t in AccessRefreshToken.objects.all():
            if t.issued_at_utc and t.expires_in is not None:
                expiry = t.issued_at_utc + timedelta(seconds=int(t.expires_in))
                if now >= expiry:
                    expired_ids.append(t.id)

        if not expired_ids:
            return 0

        deleted, _ = AccessRefreshToken.objects.filter(id__in=expired_ids).delete()
        return deleted
