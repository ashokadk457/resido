import requests
import hashlib
from django.conf import settings
from app.utils.logger import get_logger

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

        return {
            "success": True,
            "message": "Login successful",
            "accessToken": data.get("access_token"),
            "refreshToken": data.get("refresh_token"),
            "uid": data.get("uid"),
            "expiresIn": data.get("expires_in"),
            "scope": data.get("scope"),
            "expiresIn": data.get("expires_in"),
        }

    @staticmethod
    def _generate_md5(plain_password: str) -> str:
        md5 = hashlib.md5()
        md5.update(plain_password.encode("utf-8"))
        return md5.hexdigest()
