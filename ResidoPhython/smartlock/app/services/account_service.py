from app.services.ttlock_service import TTLockService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AccountService:
    @staticmethod
    def login_with_ttlock(validated_data: dict) -> dict:
        """Delegate to TTLockService which contains the login and persistence logic."""
        return TTLockService.login(validated_data)