from app.services.ttlock_service import TTLockService
from app.utils import Logger

logger = Logger.get_logger(__name__)


class AccountService:
    @staticmethod
    def login_with_ttlock(validated_data: dict) -> dict:
        return TTLockService.login(validated_data)