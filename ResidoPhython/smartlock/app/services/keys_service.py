from app.repositories.keys_repository import KeyRepository
from app.utils.pagination_utils import get_offset_limit
from app.validators.key_query_validator import (
    validate_pagination,
    validate_sorting,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class KeyService:
    """
    Service layer :
    """

    # GET KEYS
    @staticmethod
    def get_keys(page, page_size, order_by, direction):
        logger.info(
            "get_keys called page=%s page_size=%s order_by=%s direction=%s",
            page, page_size, order_by, direction
        )

        page, page_size = validate_pagination(page, page_size)
        sort_field = validate_sorting(order_by, direction)

        offset, limit = get_offset_limit(page, page_size)

        keys = KeyRepository.find_all(
            offset=offset,
            limit=limit,
            order_by=sort_field,
        )

        total = KeyRepository.count_all()

        meta = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "order_by": order_by or "created_at",
            "direction": direction or "desc",
        }

        return keys, meta

    # LIST KEYS
    @staticmethod
    def list_ekeys(
        smart_lock_id=None,
        ekey_id=None,
        key_name=None,
        page=None,
        page_size=None,
        order_by=None,
        direction=None,
    ):
        logger.info(
            "list_keys called smart_lock_id=%s ekey_id=%s key_name=%s",
            smart_lock_id, ekey_id, key_name
        )

        page, page_size = validate_pagination(page, page_size)
        sort_field = validate_sorting(order_by, direction)

        offset, limit = get_offset_limit(page, page_size)

        keys = KeyRepository.list_keys(
            smart_lock_id=smart_lock_id,
            ekey_id=ekey_id,
            key_name=key_name,
            order_by=sort_field,
            offset=offset,
            limit=limit,
        )

        total = KeyRepository.count_keys(
            smart_lock_id=smart_lock_id,
            ekey_id=ekey_id,
            key_name=key_name,
        )

        meta = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "order_by": order_by or "created_at",
            "direction": direction or "desc",
        }

        return keys, meta

    # CREATE KEY
    @staticmethod
    def create_key(data):
        logger.info("create_key called")
        return KeyRepository.create_key(data)

    # DELETE KEY
    @staticmethod
    def delete_key(key_id):
        logger.info("delete_key called key_id=%s", key_id)
        return KeyRepository.delete_key(key_id)
