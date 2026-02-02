import hashlib
import requests
import uuid
from django.conf import settings
from django.utils import timezone

from app.serializers.ttlock_payload_serializer import TTLockPayloadSerializer
from app.utils.logger import get_logger
from app.repositories.users_repository import UsersRepository
from app.repositories.access_refresh_tokens_repository import AccessRefreshTokensRepository

logger = get_logger(__name__)


class TTLockService:
    """Service to interact with TTLock authentication endpoints and persist tokens/users."""

    @staticmethod
    def login(validated_data: dict) -> dict:
        """Exchange username/password for access token and persist user + token.

        Returns a dictionary with keys similar to the previous `AccountService.login_with_ttlock` response.
        """
        logger.info("Calling TTLock login API")

        encrypted_password = TTLockService.generate_md5(
            validated_data["password"]
        )

        payload_serializer = TTLockPayloadSerializer(data={
            "client_id": settings.TTLOCK['CLIENT_ID'],
            "client_secret": settings.TTLOCK['CLIENT_SECRET'],
            "username": validated_data["contactOrEmail"],
            "password": encrypted_password,
            "grant_type": "password",
        })

        payload_serializer.is_valid(raise_exception=True)
        payload = payload_serializer.validated_data

        logger.info(payload);

        response = requests.post(
            settings.TTLOCK['OAUTH_ENDPOINT'],
            data=payload,
            timeout=10,
        )

        logger.info("TTLock response: %s", response.text)

        data = response.json()

        if data.get("errcode"):
            return {
                "success": False,
                "message": data.get("errmsg", "Login failed"),
            }
        # Persist user record and access/refresh token
        TTLockService.saveUserAndTokenInfo(data, encrypted_password, validated_data)

        return {
            "success": True,
            "message": "Login successful",
            "accessToken": data.get("access_token"),
            "refreshToken": data.get("refresh_token"),
            "uid": data.get("uid"),
            "expiresIn": data.get("expires_in"),
            "scope": data.get("scope")
        }

    @staticmethod
    def saveUserAndTokenInfo(data, encrypted_password: str, validated_data: dict):
        try:
            now = timezone.now()
            contact = validated_data.get("contactOrEmail")
            # Resolve user: prefer email from response, else use contact
            user = None
            if contact:
                user = UsersRepository.find_by_email(contact)

            if not user:
                logger.info("User not found contact=%s", contact)
            else:
                UsersRepository.update_user(user.id, {
                    "ttlock_hash_password": encrypted_password,
                    "last_login": now,
                })
                logger.info("Updated user id=%s", user.id)

            token_data = {
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in"),
                "scope": data.get("scope")
            }
            AccessRefreshTokensRepository.update_token(user.id, token_data);
            logger.info("AccessRefreshTokens Saved access token for user_id=%s", user.id)
        except Exception:
            logger.exception("Failed to persist login or token for contact=%s", validated_data.get("contactOrEmail"))

    @staticmethod
    def generate_md5(plain_password: str) -> str:
        md5 = hashlib.md5()
        md5.update(plain_password.encode("utf-8"))
        return md5.hexdigest()
