import time
from datetime import datetime

import requests
import hashlib
from django.conf import settings
import uuid
from django.utils import timezone
from app.utils.logger import get_logger
from app.repositories.users_repository import UsersRepository
from app.repositories.access_refresh_tokens_repository import AccessRefreshTokensRepository

from app.serializers.ttlock_payload_serializer import TTLockPayloadSerializer

logger = get_logger(__name__)


class AccountService:

    @staticmethod
    def login_with_ttlock(validated_data: dict) -> dict:
        logger.info("Calling TTLock login API")

        encrypted_password = AccountService._generate_md5(
            validated_data["password"]
        )

        payload_serializer = TTLockPayloadSerializer(data={
            "client_id": settings.TTLOCK_CLIENT_ID,
            "client_secret": settings.TTLOCK_CLIENT_SECRET,
            "username": validated_data["contactOrEmail"],
            "password": encrypted_password,
            "grant_type": "password",
        #    "dialCode": validated_data.get("dialCode"),
        })

        payload_serializer.is_valid(raise_exception=True)
        payload = payload_serializer.validated_data

        logger.info(payload);

        response = requests.post(
            "https://euapi.ttlock.com/oauth2/token",
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
        try:
            now = timezone.now()
            contact = validated_data.get("contactOrEmail")
            # Resolve user: prefer email from response, else use contact
            user = None
            if data.get("email"):
                user = UsersRepository.find_by_email(contact)

            if not user:
                logger.info("User not found contact=%s",contact)
            else:
                UsersRepository.update_user(user.id, {
                    "ttlock_hash_password": encrypted_password,
                    "last_login": now,
                })
                logger.info("Updated user id=%s", user.id)

            # token_data = {
            #     "access_token": data.get("access_token"),
            #     "refresh_token": data.get("refresh_token"),
            #     "expires_in": data.get("expires_in"),
            #     "scope": data.get("scope")
            # }
            # AccessRefreshTokensRepository.update_token(token_data);
            # logger.info("Saved access token for user_id=%s", user.id)
        except Exception:
            logger.exception("Failed to persist login or token for contact=%s", validated_data.get("contactOrEmail"))

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
    def _generate_md5(plain_password: str) -> str:
        md5 = hashlib.md5()
        md5.update(plain_password.encode("utf-8"))
        return md5.hexdigest()

